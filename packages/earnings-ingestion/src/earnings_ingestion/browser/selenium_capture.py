"""The Selenium adapter: captures a saved page in the pinned Chrome for Testing (B1, B7).

Only this module imports Selenium or websocket-client (the import scan in
tests/contracts/test_import_scan.py holds every other module to that), and only the
``browser-capture`` extra installs them.

Every capture starts its own browser, in a fresh profile, and kills it afterwards:
chromedriver runs in a process group of its own, which Chrome and every helper it
starts share, so one signal reaches them all even when shutdown hangs. Chrome's crash
handler alone detaches, and exits with the browser. Requests are intercepted with CDP
Fetch over the page's DevTools socket, which Selenium's bundled CDP bindings do not
cover for this Chrome, and the interceptor outlives the browser: Chrome would let a
paused request through once its client had gone.
"""

import base64
import contextlib
import json
import os
import signal
import subprocess
import tempfile
import threading
import time
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import selenium
import websocket
from earnings_core import ArtifactRef, sha256_hex
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service

from earnings_ingestion.browser.install import Binaries
from earnings_ingestion.browser.metadata import (
    METADATA_SCRIPT,
    METADATA_VERSION,
    parse_metadata,
)
from earnings_ingestion.browser.policy import SAVED_NAME, CapturePolicy
from earnings_ingestion.browser.records import (
    BlockedRequest,
    CaptureReason,
    CaptureStatus,
    RenderedCapture,
    layout_hash,
)
from earnings_ingestion.browser.renderer import (
    CaptureEnvironment,
    cache_key,
    capture_id,
    this_platform,
    unrendered,
)

BROWSER_ENGINE = "Chrome for Testing"
TILE_HEIGHT = 4096
"""The tallest screenshot tile, in CSS pixels: long releases are captured in tiles."""


class _Failure(Exception):
    """A capture that cannot complete, with the reason it records."""

    def __init__(self, reason: CaptureReason, detail: str) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


class _Watchdog:
    """Kills the browser when a bounded phase runs over, and remembers which one."""

    def __init__(self, kill: Callable[[], None]) -> None:
        self._kill = kill
        self._timer: threading.Timer | None = None
        self.expired: str | None = None

    def arm(self, phase: str, seconds: float) -> None:
        self.disarm()
        self._timer = threading.Timer(seconds, self._fire, args=(phase, seconds))
        self._timer.daemon = True
        self._timer.start()

    def disarm(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def _fire(self, phase: str, seconds: float) -> None:
        self.expired = f"{phase} ran past {seconds:g} s"
        self._kill()


class _Interceptor:
    """Pauses every request of the page and lets through only the saved file.

    It speaks CDP over the page target's own DevTools socket, on a thread of its own.
    A required resource is a stylesheet or font (the policy's types) or a subframe's
    document; the main frame's own navigations away are refused and kept on the page.
    """

    def __init__(
        self, debugger_address: str, allowed_url: str, required: frozenset[str]
    ):
        with urllib.request.urlopen(
            f"http://{debugger_address}/json", timeout=10
        ) as reply:
            targets = json.load(reply)
        page = next(target for target in targets if target["type"] == "page")
        self._socket = websocket.create_connection(
            page["webSocketDebuggerUrl"], suppress_origin=True, timeout=10
        )
        self._allowed = allowed_url
        self._required = required
        self._next_id = 0
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self.blocked: list[BlockedRequest] = []
        self.error: str | None = None
        self._main_frame = self._call("Page.getFrameTree", {})["frameTree"]["frame"][
            "id"
        ]
        self._call(
            "Fetch.enable",
            {"patterns": [{"urlPattern": "*", "requestStage": "Request"}]},
        )
        self._socket.settimeout(0.2)
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    @property
    def alive(self) -> bool:
        return self._thread.is_alive() and self.error is None

    def _send(self, method: str, params: dict) -> int:
        self._next_id += 1
        self._socket.send(
            json.dumps({"id": self._next_id, "method": method, "params": params})
        )
        return self._next_id

    def _call(self, method: str, params: dict) -> dict:
        wanted = self._send(method, params)
        while True:
            message = json.loads(self._socket.recv())
            if message.get("id") == wanted:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message["result"]

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                message = json.loads(self._socket.recv())
            except websocket.WebSocketTimeoutException:
                continue
            except Exception as error:  # noqa: BLE001 - any loss of the socket fails closed
                if not self._stop.is_set():
                    self.error = f"request interception stopped: {error!r}"
                return
            if message.get("method") != "Fetch.requestPaused":
                continue
            params = message["params"]
            url = params["request"]["url"]
            if url == self._allowed:
                self._send("Fetch.continueRequest", {"requestId": params["requestId"]})
                continue
            kind = params.get("resourceType", "Other")
            subframe = kind == "Document" and params.get("frameId") != self._main_frame
            with self._lock:
                self.blocked.append(
                    BlockedRequest(
                        url=url,
                        resource_type=kind,
                        required=kind in self._required or subframe,
                    )
                )
            reason = "Aborted" if kind == "Document" else "BlockedByClient"
            self._send(
                "Fetch.failRequest",
                {"requestId": params["requestId"], "errorReason": reason},
            )

    def recorded(self) -> tuple[BlockedRequest, ...]:
        """Each distinct blocked request once, sorted, so records compare stably."""
        with self._lock:
            unique = set(self.blocked)
        return tuple(sorted(unique, key=lambda item: (item.url, item.resource_type)))

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2)
        self._socket.close()


class _Browser:
    """One chromedriver session in a process group of its own."""

    def __init__(
        self, binaries: Binaries, policy: CapturePolicy, scratch: Path
    ) -> None:
        options = webdriver.ChromeOptions()
        options.binary_location = str(binaries.browser)
        for argument in policy.arguments:
            options.add_argument(argument)
        options.add_argument(f"--user-data-dir={scratch / 'profile'}")
        options.add_experimental_option("prefs", dict(policy.preferences))
        self._service = Service(
            executable_path=str(binaries.driver),
            log_output=subprocess.DEVNULL,
            env={
                "HOME": str(scratch),
                "LANG": "en_US.UTF-8",
                "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                "TZ": policy.timezone,
            },
            popen_kw={"start_new_session": True},
        )
        self._options = options
        self.driver: webdriver.Chrome | None = None

    def start(self) -> webdriver.Chrome:
        self.driver = webdriver.Chrome(options=self._options, service=self._service)
        return self.driver

    def kill(self) -> None:
        """SIGKILL chromedriver's whole process group; safe to repeat."""
        process = getattr(self._service, "process", None)
        if process is None:
            return
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass  # the group is gone, or only unreaped processes are left in it
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass

    def close(self, seconds: float) -> None:
        """Quit within ``seconds``, then kill whatever is left. A driver the watchdog
        already killed is not asked to quit: nothing would answer."""
        process = getattr(self._service, "process", None)
        running = process is not None and process.poll() is None
        if self.driver is not None and running:
            closer = threading.Thread(target=self._quit, daemon=True)
            closer.start()
            closer.join(seconds)
        self.kill()

    def _quit(self) -> None:
        # Any error is moot: the kill that follows cleans up regardless.
        with contextlib.suppress(Exception):
            self.driver.quit()


class SeleniumRenderer:
    """``BrowserRenderer`` over the pinned Chrome for Testing and chromedriver.

    ``binaries`` is ``None`` where none are installed: every capture is then
    ``unavailable``. ``screenshots`` stores each screenshot tile and returns its
    reference, as ``CaptureStore.screenshot`` does; without it a capture takes none.
    """

    def __init__(
        self,
        binaries: Binaries | None,
        screenshots: Callable[[bytes], ArtifactRef] | None = None,
    ) -> None:
        self._binaries = binaries
        self._store_screenshot = screenshots
        name, version, architecture = this_platform()
        pinned = binaries.version if binaries is not None else "none"
        self.environment = CaptureEnvironment(
            browser_engine=BROWSER_ENGINE,
            browser_version=pinned,
            driver_version=pinned,
            selenium_version=selenium.__version__,
            os_name=name,
            os_version=version,
            architecture=architecture,
        )

    def capture(
        self,
        saved_html: bytes,
        capture_policy: CapturePolicy,
        *,
        source_document_id: str,
    ) -> RenderedCapture:
        captured_at = datetime.now(UTC)
        started = time.monotonic()
        if self._binaries is None or not self._binaries.present():
            return self._unrendered(
                saved_html,
                capture_policy,
                source_document_id,
                CaptureStatus.UNAVAILABLE,
                CaptureReason.BROWSER_UNAVAILABLE,
                "the pinned browser and driver are not installed; run the browser setup",
                captured_at,
                started,
            )
        with tempfile.TemporaryDirectory(
            prefix="earnings-capture-", ignore_cleanup_errors=True
        ) as scratch_name:
            scratch = Path(scratch_name).resolve()
            try:
                return self._render(
                    saved_html,
                    capture_policy,
                    source_document_id,
                    scratch,
                    captured_at,
                    started,
                )
            except _Failure as failure:
                return self._unrendered(
                    saved_html,
                    capture_policy,
                    source_document_id,
                    CaptureStatus.FAILED,
                    failure.reason,
                    failure.detail,
                    captured_at,
                    started,
                )

    def _render(
        self,
        saved_html: bytes,
        policy: CapturePolicy,
        source_document_id: str,
        scratch: Path,
        captured_at: datetime,
        started: float,
    ) -> RenderedCapture:
        page = scratch / "page"
        page.mkdir()
        saved = page / SAVED_NAME
        saved.write_bytes(saved_html)
        url = saved.as_uri()
        browser = _Browser(self._binaries, policy, scratch)
        watchdog = _Watchdog(browser.kill)
        interceptor: _Interceptor | None = None
        try:
            watchdog.arm("startup", policy.startup_seconds)
            driver = _step(watchdog, CaptureReason.STARTUP_FAILURE, browser.start)
            self._check_versions(driver.capabilities)
            interceptor = _step(
                watchdog,
                CaptureReason.STARTUP_FAILURE,
                lambda: _Interceptor(
                    driver.capabilities["goog:chromeOptions"]["debuggerAddress"],
                    url,
                    policy.required_resource_types,
                ),
            )

            def configure() -> None:
                driver.execute_cdp_cmd(
                    "Emulation.setScriptExecutionDisabled", {"value": True}
                )
                driver.execute_cdp_cmd(
                    "Emulation.setTimezoneOverride", {"timezoneId": policy.timezone}
                )
                driver.set_page_load_timeout(policy.navigation_seconds)
                driver.set_script_timeout(policy.capture_seconds)

            _step(watchdog, CaptureReason.STARTUP_FAILURE, configure)
            watchdog.arm("navigation", policy.navigation_seconds)
            _step(
                watchdog, CaptureReason.DOCUMENT_LOAD_FAILURE, lambda: driver.get(url)
            )
            if driver.current_url.partition("#")[0] != url:
                raise _Failure(
                    CaptureReason.DOCUMENT_LOAD_FAILURE,
                    "the browser did not stay on the saved file",
                )
            watchdog.arm("capture", policy.capture_seconds)
            text, payload, charset = _step(
                watchdog,
                CaptureReason.CAPTURE_FAILURE,
                lambda: (
                    driver.execute_script("return document.body.innerText"),
                    driver.execute_script(METADATA_SCRIPT),
                    driver.execute_script("return document.characterSet"),
                ),
            )
            try:
                layout = parse_metadata(payload)
            except ValueError as error:
                raise _Failure(CaptureReason.CAPTURE_FAILURE, str(error)) from error
            screenshots = _step(
                watchdog,
                CaptureReason.CAPTURE_FAILURE,
                lambda: self._screenshots(driver),
            )
            watchdog.disarm()
            if not interceptor.alive:
                raise _Failure(
                    CaptureReason.CAPTURE_FAILURE,
                    interceptor.error or "request interception stopped",
                )
            blocked = interceptor.recorded()
        finally:
            watchdog.disarm()
            browser.close(policy.shutdown_seconds)
            if interceptor is not None:
                interceptor.close()
        required = [request for request in blocked if request.required]
        status = CaptureStatus.PARTIAL if required else CaptureStatus.COMPLETED
        raw_sha256 = sha256_hex(saved_html)
        key = cache_key(raw_sha256, policy, self.environment)
        return RenderedCapture(
            capture_id=capture_id(source_document_id, policy, key),
            cache_key=key,
            source_document_id=source_document_id,
            raw_sha256=raw_sha256,
            capture_policy=policy.name,
            capture_policy_version=policy.version,
            metadata_version=METADATA_VERSION,
            browser_engine=self.environment.browser_engine,
            browser_version=self.environment.browser_version,
            driver_version=self.environment.driver_version,
            selenium_version=self.environment.selenium_version,
            os_name=self.environment.os_name,
            os_version=self.environment.os_version,
            architecture=self.environment.architecture,
            viewport_width=policy.viewport_width,
            viewport_height=policy.viewport_height,
            device_scale_factor=policy.device_scale_factor,
            locale=policy.locale,
            timezone=policy.timezone,
            font_set=self.environment.font_set,
            document_charset=charset,
            script_policy="disabled",
            network_policy="blocked",
            image_policy="blocked",
            missing_resource_policy="recorded",
            rendered_text=text,
            rendered_text_sha256=sha256_hex(text.encode("utf-8")),
            layout=layout,
            layout_sha256=layout_hash(layout),
            screenshots=screenshots,
            blocked_requests=blocked,
            captured_at=captured_at,
            duration_seconds=round(time.monotonic() - started, 3),
            status=status,
            reason=None if not required else CaptureReason.BLOCKED_REQUIRED_RESOURCE,
            detail=(
                ""
                if not required
                else f"{len(required)} required resource(s) blocked: "
                + ", ".join(sorted({request.resource_type for request in required}))
            ),
        )

    def _check_versions(self, capabilities: dict) -> None:
        browser = capabilities.get("browserVersion", "")
        driver = (
            capabilities.get("chrome", {}).get("chromedriverVersion", "").split(" ")[0]
        )
        pinned = self._binaries.version
        if browser != pinned or driver != pinned:
            raise _Failure(
                CaptureReason.STARTUP_FAILURE,
                f"browser {browser!r} and driver {driver!r} are not the pinned {pinned!r}",
            )

    def _screenshots(self, driver: webdriver.Chrome) -> tuple[ArtifactRef, ...]:
        if self._store_screenshot is None:
            return ()
        size = driver.execute_cdp_cmd("Page.getLayoutMetrics", {})["cssContentSize"]
        width = max(1, int(size["width"]))
        height = max(1, int(size["height"]))
        tiles = []
        for top in range(0, height, TILE_HEIGHT):
            shot = driver.execute_cdp_cmd(
                "Page.captureScreenshot",
                {
                    "format": "png",
                    "captureBeyondViewport": True,
                    "clip": {
                        "x": 0,
                        "y": top,
                        "width": width,
                        "height": min(TILE_HEIGHT, height - top),
                        "scale": 1,
                    },
                },
            )
            tiles.append(self._store_screenshot(base64.b64decode(shot["data"])))
        return tuple(tiles)

    def _unrendered(
        self,
        saved_html: bytes,
        policy: CapturePolicy,
        source_document_id: str,
        status: CaptureStatus,
        reason: CaptureReason,
        detail: str,
        captured_at: datetime,
        started: float,
    ) -> RenderedCapture:
        return unrendered(
            saved_html,
            policy,
            self.environment,
            source_document_id=source_document_id,
            status=status,
            reason=reason,
            detail=detail,
            captured_at=captured_at,
            duration_seconds=round(time.monotonic() - started, 3),
        )


def _step[T](watchdog: _Watchdog, reason: CaptureReason, action: Callable[[], T]) -> T:
    """Run one step; a timeout or any error becomes a ``_Failure``."""
    try:
        return action()
    except _Failure:
        raise
    except TimeoutException as error:
        raise _Failure(CaptureReason.TIMEOUT, _first_line(error)) from error
    except Exception as error:
        if watchdog.expired is not None:
            raise _Failure(CaptureReason.TIMEOUT, watchdog.expired) from error
        raise _Failure(reason, _first_line(error)) from error


def _first_line(error: Exception) -> str:
    text = str(error).strip().splitlines()
    return f"{type(error).__name__}: {text[0] if text else ''}"[:300]
