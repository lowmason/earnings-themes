"""Captures on disk under ``data/runs/``: written atomically, never overwritten (B2).

- A usable capture, ``completed`` or ``partial``, is stored by its cache key and
  reused for that key: a new run either reuses an exact key or writes a new capture.
- A failed or unavailable capture is kept for the record, under its key and time, and
  never reused.
- Screenshots are stored by content hash, so writing one twice is harmless.

Every write goes to a temporary file first. A hard link then puts it in place, which
fails rather than replace an existing file: writing the same bytes again is a no-op,
and different bytes raise ``FileExistsError``.
"""

import os
import tempfile
from pathlib import Path

from earnings_core import ArtifactRef, RightsStatus, sha256_hex

from earnings_ingestion.browser.policy import CapturePolicy
from earnings_ingestion.browser.records import CaptureStatus, RenderedCapture
from earnings_ingestion.browser.renderer import BrowserRenderer, cache_key

USABLE = frozenset({CaptureStatus.COMPLETED, CaptureStatus.PARTIAL})
SCREENSHOT_RIGHTS = "a rendering of a saved filing, kept local under data/runs/"


class CaptureStore:
    """``root`` lies under ``repo``'s ``data/runs/``; references are repo-relative."""

    def __init__(self, root: Path, repo: Path) -> None:
        self.root = root
        self.repo = repo

    def reuse(self, key: str) -> RenderedCapture | None:
        path = self.root / "captures" / f"{key}.json"
        if not path.is_file():
            return None
        return RenderedCapture.model_validate_json(path.read_text(encoding="utf-8"))

    def put(self, capture: RenderedCapture) -> Path:
        """Write ``capture``; ``FileExistsError`` if another record holds its file."""
        if capture.status in USABLE:
            path = self.root / "captures" / f"{capture.cache_key}.json"
        else:
            stamp = capture.captured_at.strftime("%Y%m%dT%H%M%S%fZ")
            path = self.root / "failures" / capture.cache_key / f"{stamp}.json"
        _write_new(path, capture.model_dump_json().encode("utf-8"))
        return path

    def screenshot(self, png: bytes) -> ArtifactRef:
        """Store one screenshot tile by its hash and return its reference."""
        digest = sha256_hex(png)
        path = self.root / "screenshots" / f"{digest}.png"
        _write_new(path, png)
        return ArtifactRef.for_bytes(
            png,
            media_type="image/png",
            storage_ref=path.relative_to(self.repo).as_posix(),
            rights_status=RightsStatus.LOCAL_ONLY,
            rights_basis=SCREENSHOT_RIGHTS,
        )


def capture_once(
    renderer: BrowserRenderer,
    store: CaptureStore,
    saved_html: bytes,
    policy: CapturePolicy,
    *,
    source_document_id: str,
) -> RenderedCapture:
    """The stored capture for this exact cache key, or a new one, stored."""
    key = cache_key(sha256_hex(saved_html), policy, renderer.environment)
    found = store.reuse(key)
    if found is not None:
        return found
    capture = renderer.capture(
        saved_html, policy, source_document_id=source_document_id
    )
    store.put(capture)
    return capture


def _write_new(path: Path, data: bytes) -> None:
    if path.exists():
        if path.read_bytes() == data:
            return
        raise FileExistsError(f"{path} holds another record")
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(handle, "wb") as out:
            out.write(data)
        os.link(temporary, path)
    finally:
        os.unlink(temporary)
