"""The Selenium adapter in the pinned browser: opt-in with ``-m browser`` (Stage 3 spec,
Checks; plan B exit criteria 3, 4, and 10).

Every test here skips visibly without the ``browser-capture`` extra or the pinned
Chrome for Testing. The adapter is imported by a fixture, not at collection, so the
default suite deselects these tests whether or not the extra is installed. The guard
pages point at a local HTTP server that counts every connection it accepts: none may
arrive.
"""

import dataclasses
import http.server
import socketserver
import subprocess
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from earnings_ingestion.browser.install import installed
from earnings_ingestion.browser.policy import ISOLATED_1
from earnings_ingestion.browser.records import CaptureReason, CaptureStatus
from earnings_ingestion.browser.store import CaptureStore

pytestmark = pytest.mark.browser
BINARIES = installed()
pinned = pytest.mark.skipif(
    BINARIES is None,
    reason="the pinned Chrome for Testing is not installed: run"
    " uv run --locked --all-packages earnings-pipeline browser setup",
)
WITHOUT_DEFENCE = dataclasses.replace(
    ISOLATED_1,
    arguments=tuple(
        argument
        for argument in ISOLATED_1.arguments
        if not argument.startswith(("--proxy", "--host-resolver"))
    ),
)


class _Counter(socketserver.ThreadingTCPServer):
    daemon_threads = True
    connections = 0

    def verify_request(self, request, client_address) -> bool:
        type(self).connections += 1
        return True


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture
def adapter():
    """The adapter module, which imports Selenium; skips without the extra."""
    return pytest.importorskip(
        "earnings_ingestion.browser.selenium_capture",
        reason="needs the browser-capture extra: uv sync --locked --all-packages"
        " --extra browser-capture",
    )


@pytest.fixture
def server() -> Iterator[str]:
    """A local origin standing in for the network; yields its base URL."""
    _Counter.connections = 0
    counter = _Counter(("127.0.0.1", 0), _Handler)
    threading.Thread(target=counter.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{counter.server_address[1]}"
    finally:
        counter.shutdown()
        counter.server_close()


def guard_page(origin: str) -> bytes:
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="{origin}/sheet.css">
<script src="{origin}/external.js"></script>
</head><body>
<p id="target">ORIGINAL TEXT</p>
<script>document.getElementById("target").textContent = "REWRITTEN BY SCRIPT";</script>
<img src="{origin}/logo.png" alt="logo">
<iframe src="{origin}/frame.html"></iframe>
</body></html>""".encode()


def renderer(adapter, **options: object):
    return adapter.SeleniumRenderer(BINARIES, **options)


@pinned
@pytest.mark.parametrize(
    "policy", [ISOLATED_1, WITHOUT_DEFENCE], ids=["isolated-1", "fetch-alone"]
)
def test_every_request_is_blocked_recorded_and_never_made(
    adapter, server: str, policy
) -> None:
    """The stylesheet, image, and frame are refused and recorded. With document
    JavaScript disabled, Chrome never asks for the external script at all (PB-4)."""
    capture = renderer(adapter).capture(
        guard_page(server), policy, source_document_id="guard"
    )
    blocked = {
        (request.url, request.resource_type) for request in capture.blocked_requests
    }
    assert blocked == {
        (f"{server}/sheet.css", "Stylesheet"),
        (f"{server}/logo.png", "Image"),
        (f"{server}/frame.html", "Document"),
    }
    time.sleep(0.5)
    assert _Counter.connections == 0


@pinned
def test_document_javascript_never_runs(adapter, server: str) -> None:
    capture = renderer(adapter).capture(
        guard_page(server), ISOLATED_1, source_document_id="guard"
    )
    assert "ORIGINAL TEXT" in capture.rendered_text
    assert "REWRITTEN" not in capture.rendered_text


@pinned
def test_a_blocked_stylesheet_or_frame_makes_the_capture_partial(
    adapter, server: str
) -> None:
    capture = renderer(adapter).capture(
        guard_page(server), ISOLATED_1, source_document_id="guard"
    )
    assert capture.status is CaptureStatus.PARTIAL
    assert capture.reason is CaptureReason.BLOCKED_REQUIRED_RESOURCE
    required = {r.resource_type for r in capture.blocked_requests if r.required}
    assert required == {"Stylesheet", "Document"}


@pinned
def test_a_missing_image_does_not_downgrade_the_capture(adapter, server: str) -> None:
    page = f'<p>Logo below.</p><img src="{server}/logo.png" alt="logo">'.encode()
    capture = renderer(adapter).capture(page, ISOLATED_1, source_document_id="logo")
    assert capture.status is CaptureStatus.COMPLETED
    assert [r.resource_type for r in capture.blocked_requests] == ["Image"]


@pinned
def test_two_captures_have_the_same_text_and_layout_hashes(
    adapter, server: str
) -> None:
    page = guard_page(server)
    first = renderer(adapter).capture(page, ISOLATED_1, source_document_id="guard")
    second = renderer(adapter).capture(page, ISOLATED_1, source_document_id="guard")
    assert first.rendered_text_sha256 == second.rendered_text_sha256
    assert first.layout_sha256 == second.layout_sha256
    assert first.cache_key == second.cache_key


@pinned
def test_the_capture_records_the_pinned_environment(adapter) -> None:
    capture = renderer(adapter).capture(
        b"<p>Hello</p>", ISOLATED_1, source_document_id="hello"
    )
    assert (capture.browser_version, capture.driver_version) == (
        BINARIES.version,
        BINARIES.version,
    )
    assert capture.browser_engine == "Chrome for Testing"
    assert capture.os_name and capture.os_version and capture.architecture
    print(
        f"environment: {capture.browser_engine} {capture.browser_version},"
        f" chromedriver {capture.driver_version}, Selenium {capture.selenium_version},"
        f" {capture.os_name} {capture.os_version} {capture.architecture}"
    )


@pinned
def test_a_tall_page_is_screenshotted_in_tiles(adapter, tmp_path: Path) -> None:
    store = CaptureStore(tmp_path / "data" / "runs" / "browser-capture", tmp_path)
    page = ("<html><body>" + "<p>line</p>" * 400 + "</body></html>").encode()
    capture = renderer(adapter, screenshots=store.screenshot).capture(
        page, ISOLATED_1, source_document_id="tall"
    )
    assert len(capture.screenshots) > 1
    for reference in capture.screenshots:
        assert reference.matches((tmp_path / reference.storage_ref).read_bytes())


@pinned
def test_a_capture_never_runs_selenium_manager(adapter, monkeypatch) -> None:
    """Selenium Manager would download a driver; the explicit paths never call it."""
    monkeypatch.setenv("SE_MANAGER_PATH", "/nonexistent/selenium-manager")
    capture = renderer(adapter).capture(
        b"<p>Hello</p>", ISOLATED_1, source_document_id="hello"
    )
    assert capture.status is CaptureStatus.COMPLETED


@pinned
def test_a_browser_that_is_not_the_pinned_one_fails_at_startup(adapter) -> None:
    wrong = dataclasses.replace(BINARIES, version="1.0.0.0")
    capture = adapter.SeleniumRenderer(wrong).capture(
        b"<p>Hello</p>", ISOLATED_1, source_document_id="hello"
    )
    assert capture.status is CaptureStatus.FAILED
    assert capture.reason is CaptureReason.STARTUP_FAILURE


@pinned
def test_a_navigation_past_its_bound_is_a_timeout(adapter) -> None:
    policy = dataclasses.replace(ISOLATED_1, navigation_seconds=0.001)
    capture = renderer(adapter).capture(
        b"<p>Hello</p>", policy, source_document_id="hello"
    )
    assert capture.status is CaptureStatus.FAILED
    assert capture.reason is CaptureReason.TIMEOUT


@pinned
def test_no_browser_process_outlives_a_capture(adapter) -> None:
    renderer(adapter).capture(b"<p>Hello</p>", ISOLATED_1, source_document_id="hello")
    install_root = str(BINARIES.browser.parents[4])
    for _ in range(50):
        listing = subprocess.run(
            ["ps", "-A", "-o", "command="], capture_output=True, text=True, check=True
        ).stdout
        left = [line for line in listing.splitlines() if install_root in line]
        if not left:
            break
        time.sleep(0.1)
    assert left == []


def test_without_binaries_every_capture_is_unavailable(adapter) -> None:
    capture = adapter.SeleniumRenderer(None).capture(
        b"<p>Hello</p>", ISOLATED_1, source_document_id="hello"
    )
    assert capture.status is CaptureStatus.UNAVAILABLE
    assert capture.reason is CaptureReason.BROWSER_UNAVAILABLE
