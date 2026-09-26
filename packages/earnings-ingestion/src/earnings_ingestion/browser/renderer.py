"""The public capture interface (B1), with no browser import.

``BrowserRenderer.capture(saved_html, capture_policy, *, source_document_id)``
returns a ``RenderedCapture``. The Selenium adapter in ``selenium_capture``
implements it behind the ``browser-capture`` extra; ``FakeRenderer`` serves default
tests. The cache key covers the raw hash, the policy, the browser, driver, and
Selenium, the platform and render configuration, and the metadata script's version
and text, and never a timestamp, so an exact key can be reused without starting a
browser, and a changed script can never reuse an old capture.
"""

import json
import platform
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Protocol

from earnings_core import sha256_hex

from earnings_ingestion.browser.metadata import METADATA_SCRIPT, METADATA_VERSION
from earnings_ingestion.browser.policy import CapturePolicy
from earnings_ingestion.browser.records import (
    CaptureReason,
    CaptureStatus,
    LayoutMetadata,
    RenderedCapture,
    layout_hash,
)

EMPTY_LAYOUT = LayoutMetadata(blocks=(), tables=())


@dataclass(frozen=True)
class CaptureEnvironment:
    """The browser, driver, library, and platform a capture runs under."""

    browser_engine: str
    browser_version: str
    driver_version: str
    selenium_version: str
    os_name: str
    os_version: str
    architecture: str

    @property
    def font_set(self) -> str:
        """Fonts are the platform's own; its release identifies them."""
        return f"{self.os_name} {self.os_version} system fonts"


def this_platform() -> tuple[str, str, str]:
    """(os_name, os_version, architecture) of the running machine."""
    name = platform.system()
    version = platform.mac_ver()[0] if name == "Darwin" else platform.release()
    return name, version, platform.machine()


def cache_key(
    raw_sha256: str, policy: CapturePolicy, environment: CaptureEnvironment
) -> str:
    """SHA-256 of every input that can change a capture; never a timestamp."""
    fields = {
        "raw_sha256": raw_sha256,
        "capture_policy": policy.name,
        "capture_policy_version": policy.version,
        "metadata_version": METADATA_VERSION,
        "metadata_script_sha256": sha256_hex(METADATA_SCRIPT.encode("utf-8")),
        "viewport_width": policy.viewport_width,
        "viewport_height": policy.viewport_height,
        "device_scale_factor": policy.device_scale_factor,
        "locale": policy.locale,
        "timezone": policy.timezone,
        **asdict(environment),
    }
    payload = json.dumps(fields, sort_keys=True, separators=(",", ":"))
    return sha256_hex(payload.encode("ascii"))


def capture_id(source_document_id: str, policy: CapturePolicy, key: str) -> str:
    """A readable, stable identifier: ``<source>@<policy>-<version>#<key prefix>``."""
    return f"{source_document_id}@{policy.name}-{policy.version}#{key[:16]}"


class BrowserRenderer(Protocol):
    """Renders a saved source under a capture policy (B1).

    ``environment`` is known before any capture, so a cache key can be looked up
    without starting a browser.
    """

    environment: CaptureEnvironment

    def capture(
        self,
        saved_html: bytes,
        capture_policy: CapturePolicy,
        *,
        source_document_id: str,
    ) -> RenderedCapture: ...


def unrendered(
    saved_html: bytes,
    capture_policy: CapturePolicy,
    environment: CaptureEnvironment,
    *,
    source_document_id: str,
    status: CaptureStatus,
    reason: CaptureReason,
    detail: str,
    captured_at: datetime | None = None,
    duration_seconds: float = 0.0,
) -> RenderedCapture:
    """A failed or unavailable capture: it holds no text, layout, or screenshot."""
    raw_sha256 = sha256_hex(saved_html)
    key = cache_key(raw_sha256, capture_policy, environment)
    return RenderedCapture(
        capture_id=capture_id(source_document_id, capture_policy, key),
        cache_key=key,
        source_document_id=source_document_id,
        raw_sha256=raw_sha256,
        capture_policy=capture_policy.name,
        capture_policy_version=capture_policy.version,
        metadata_version=METADATA_VERSION,
        browser_engine=environment.browser_engine,
        browser_version=environment.browser_version,
        driver_version=environment.driver_version,
        selenium_version=environment.selenium_version,
        os_name=environment.os_name,
        os_version=environment.os_version,
        architecture=environment.architecture,
        viewport_width=capture_policy.viewport_width,
        viewport_height=capture_policy.viewport_height,
        device_scale_factor=capture_policy.device_scale_factor,
        locale=capture_policy.locale,
        timezone=capture_policy.timezone,
        font_set=environment.font_set,
        document_charset="",
        script_policy="disabled",
        network_policy="blocked",
        image_policy="blocked",
        missing_resource_policy="recorded",
        rendered_text="",
        rendered_text_sha256=sha256_hex(b""),
        layout=EMPTY_LAYOUT,
        layout_sha256=layout_hash(EMPTY_LAYOUT),
        screenshots=(),
        blocked_requests=(),
        captured_at=captured_at or datetime.now(UTC),
        duration_seconds=duration_seconds,
        status=status,
        reason=reason,
        detail=detail,
    )


class FakeRenderer:
    """Returns saved captures by raw hash, and ``unavailable`` for anything else.

    It starts no browser and touches no network: default tests use it wherever code
    takes a ``BrowserRenderer``.
    """

    def __init__(
        self, captures: Mapping[str, RenderedCapture], environment: CaptureEnvironment
    ) -> None:
        self._captures = dict(captures)
        self.environment = environment

    def capture(
        self,
        saved_html: bytes,
        capture_policy: CapturePolicy,
        *,
        source_document_id: str,
    ) -> RenderedCapture:
        found = self._captures.get(sha256_hex(saved_html))
        if found is not None:
            return found
        return unrendered(
            saved_html,
            capture_policy,
            self.environment,
            source_document_id=source_document_id,
            status=CaptureStatus.UNAVAILABLE,
            reason=CaptureReason.BROWSER_UNAVAILABLE,
            detail="the fake renderer holds no capture of these bytes",
        )
