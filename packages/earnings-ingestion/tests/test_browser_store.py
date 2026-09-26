"""Captures on disk: atomic, never overwritten, and reused only by an exact key."""

from pathlib import Path

import pytest
from earnings_core import RightsStatus, sha256_hex
from earnings_ingestion.browser.policy import ISOLATED_1
from earnings_ingestion.browser.records import CaptureReason, CaptureStatus
from earnings_ingestion.browser.renderer import (
    CaptureEnvironment,
    FakeRenderer,
    unrendered,
)
from earnings_ingestion.browser.store import CaptureStore, capture_once

ENVIRONMENT = CaptureEnvironment(
    browser_engine="Chrome for Testing",
    browser_version="154.0.8037.57",
    driver_version="154.0.8037.57",
    selenium_version="4.49.0",
    os_name="Darwin",
    os_version="26.6.2",
    architecture="arm64",
)
RAW = b"<p>Revenue rose.</p>"


def store_in(tmp_path: Path) -> CaptureStore:
    return CaptureStore(tmp_path / "data" / "runs" / "browser-capture", tmp_path)


def failed(status: CaptureStatus = CaptureStatus.FAILED):
    return unrendered(
        RAW,
        ISOLATED_1,
        ENVIRONMENT,
        source_document_id="release",
        status=status,
        reason=CaptureReason.TIMEOUT,
        detail="navigation ran past 30 s",
    )


class Counting(FakeRenderer):
    def __init__(self, record) -> None:
        super().__init__({sha256_hex(RAW): record}, ENVIRONMENT)
        self.calls = 0

    def capture(self, saved_html, capture_policy, *, source_document_id):
        self.calls += 1
        return super().capture(
            saved_html, capture_policy, source_document_id=source_document_id
        )


def test_a_failed_capture_is_kept_but_never_reused(tmp_path: Path) -> None:
    store = store_in(tmp_path)
    record = failed()
    path = store.put(record)
    assert path.parent == store.root / "failures" / record.cache_key
    assert store.reuse(record.cache_key) is None


def test_a_usable_capture_is_reused_by_its_key(tmp_path: Path) -> None:
    store = store_in(tmp_path)
    record = failed().model_copy(
        update={"status": CaptureStatus.COMPLETED, "reason": None, "detail": ""}
    )
    path = store.put(record)
    assert path == store.root / "captures" / f"{record.cache_key}.json"
    assert store.reuse(record.cache_key) == record


def test_a_stored_capture_is_never_overwritten(tmp_path: Path) -> None:
    store = store_in(tmp_path)
    record = failed().model_copy(
        update={"status": CaptureStatus.COMPLETED, "reason": None, "detail": ""}
    )
    path = store.put(record)
    before = path.read_bytes()
    assert store.put(record) == path
    later = record.model_copy(update={"duration_seconds": 9.0})
    with pytest.raises(FileExistsError, match="holds another record"):
        store.put(later)
    assert path.read_bytes() == before
    assert not list(path.parent.glob(".tmp-*"))


def test_screenshots_are_stored_by_content_hash(tmp_path: Path) -> None:
    store = store_in(tmp_path)
    png = b"\x89PNG\r\n\x1a\n not really"
    reference = store.screenshot(png)
    assert reference == store.screenshot(png)
    assert reference.storage_ref == (
        f"data/runs/browser-capture/screenshots/{sha256_hex(png)}.png"
    )
    assert reference.rights_status is RightsStatus.LOCAL_ONLY
    assert (tmp_path / reference.storage_ref).read_bytes() == png


def test_capture_once_reuses_an_exact_key_without_rendering(tmp_path: Path) -> None:
    store = store_in(tmp_path)
    record = failed().model_copy(
        update={"status": CaptureStatus.COMPLETED, "reason": None, "detail": ""}
    )
    renderer = Counting(record)
    first = capture_once(renderer, store, RAW, ISOLATED_1, source_document_id="release")
    second = capture_once(
        renderer, store, RAW, ISOLATED_1, source_document_id="release"
    )
    assert first == second == record
    assert renderer.calls == 1


def test_capture_once_renders_again_after_a_failure(tmp_path: Path) -> None:
    store = store_in(tmp_path)
    renderer = Counting(failed())
    capture_once(renderer, store, RAW, ISOLATED_1, source_document_id="release")
    capture_once(renderer, store, RAW, ISOLATED_1, source_document_id="release")
    assert renderer.calls == 2
