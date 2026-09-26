"""The renderer interface without a browser: cache keys, identifiers, and the fake."""

import dataclasses

from earnings_core import sha256_hex
from earnings_ingestion.browser import renderer
from earnings_ingestion.browser.policy import ISOLATED_1
from earnings_ingestion.browser.records import CaptureReason, CaptureStatus
from earnings_ingestion.browser.renderer import (
    CaptureEnvironment,
    FakeRenderer,
    cache_key,
    capture_id,
    unrendered,
)

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


def test_the_cache_key_is_stable_and_has_no_timestamp() -> None:
    key = cache_key(sha256_hex(RAW), ISOLATED_1, ENVIRONMENT)
    assert key == cache_key(sha256_hex(RAW), ISOLATED_1, ENVIRONMENT)
    assert len(key) == 64


def test_every_input_that_can_change_a_capture_changes_the_key() -> None:
    key = cache_key(sha256_hex(RAW), ISOLATED_1, ENVIRONMENT)
    changed = [
        cache_key(sha256_hex(b"<p>Other.</p>"), ISOLATED_1, ENVIRONMENT),
        cache_key(
            sha256_hex(RAW), dataclasses.replace(ISOLATED_1, version="2"), ENVIRONMENT
        ),
        cache_key(
            sha256_hex(RAW),
            dataclasses.replace(ISOLATED_1, viewport_width=800),
            ENVIRONMENT,
        ),
        cache_key(
            sha256_hex(RAW),
            ISOLATED_1,
            dataclasses.replace(ENVIRONMENT, browser_version="155.0.0.0"),
        ),
        cache_key(
            sha256_hex(RAW),
            ISOLATED_1,
            dataclasses.replace(ENVIRONMENT, os_version="27.0"),
        ),
    ]
    assert key not in changed
    assert len(set(changed)) == len(changed)


def test_the_metadata_scripts_text_is_part_of_the_key(monkeypatch) -> None:
    key = cache_key(sha256_hex(RAW), ISOLATED_1, ENVIRONMENT)
    monkeypatch.setattr(renderer, "METADATA_SCRIPT", renderer.METADATA_SCRIPT + "\n")
    assert cache_key(sha256_hex(RAW), ISOLATED_1, ENVIRONMENT) != key


def test_the_capture_id_names_the_source_the_policy_and_the_key() -> None:
    key = cache_key(sha256_hex(RAW), ISOLATED_1, ENVIRONMENT)
    assert capture_id("release", ISOLATED_1, key) == f"release@isolated-1#{key[:16]}"


def test_the_font_set_is_the_platform_release() -> None:
    assert ENVIRONMENT.font_set == "Darwin 26.6.2 system fonts"


def test_an_unrendered_capture_records_its_reason_and_nothing_else() -> None:
    record = unrendered(
        RAW,
        ISOLATED_1,
        ENVIRONMENT,
        source_document_id="release",
        status=CaptureStatus.FAILED,
        reason=CaptureReason.TIMEOUT,
        detail="navigation ran past 30 s",
    )
    assert record.status is CaptureStatus.FAILED
    assert record.reason is CaptureReason.TIMEOUT
    assert (record.rendered_text, record.layout.blocks, record.screenshots) == (
        "",
        (),
        (),
    )
    assert record.raw_sha256 == sha256_hex(RAW)


def test_the_fake_returns_saved_captures_by_raw_hash() -> None:
    saved = unrendered(
        RAW,
        ISOLATED_1,
        ENVIRONMENT,
        source_document_id="release",
        status=CaptureStatus.FAILED,
        reason=CaptureReason.CAPTURE_FAILURE,
        detail="saved",
    )
    fake = FakeRenderer({sha256_hex(RAW): saved}, ENVIRONMENT)
    assert fake.capture(RAW, ISOLATED_1, source_document_id="release") is saved


def test_the_fake_is_unavailable_for_anything_else() -> None:
    fake = FakeRenderer({}, ENVIRONMENT)
    record = fake.capture(b"<p>New.</p>", ISOLATED_1, source_document_id="other")
    assert record.status is CaptureStatus.UNAVAILABLE
    assert record.reason is CaptureReason.BROWSER_UNAVAILABLE
    assert fake.environment is ENVIRONMENT
