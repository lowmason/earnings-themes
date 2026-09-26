"""The committed release captures: usable, exact, and mapped (Stage 3 spec, plan B
exit criteria 4 and 5).

Each Stage 1 release has a capture made by the pinned browser under ``isolated/1``
(tests/integration/capture_browser_fixtures.py). These tests read the captures
offline. The last, opt-in with ``-m browser``, recaptures each release and checks
that the pinned environment still renders the same text and layout.
"""

from pathlib import Path

import pytest
from earnings_core import sha256_hex, validate_elements
from earnings_ingestion.browser import ISOLATED_1, CaptureStatus
from earnings_ingestion.browser.install import installed
from earnings_ingestion.browser.serialize import from_capture_json, to_capture_json
from earnings_ingestion.canonical import Canonicalized, canonicalize
from earnings_ingestion.layout import LayoutExtractor

ROOT = Path(__file__).resolve().parents[2]
RELEASES = ROOT / "tests" / "fixtures" / "releases"
CAPTURES = ROOT / "tests" / "fixtures" / "browser"
FIXTURES = sorted(path.parent.name for path in RELEASES.glob("*/source.html"))


def source(fixture: str) -> bytes:
    return (RELEASES / fixture / "source.html").read_bytes()


def capture_text(fixture: str) -> str:
    return (CAPTURES / f"{fixture}.capture.json").read_text(encoding="utf-8")


@pytest.mark.parametrize("fixture", FIXTURES)
def test_each_release_has_a_usable_capture_of_its_own_bytes(fixture: str) -> None:
    capture = from_capture_json(capture_text(fixture))
    assert capture.raw_sha256 == sha256_hex(source(fixture))
    assert capture.source_document_id == fixture
    assert capture.status in (CaptureStatus.COMPLETED, CaptureStatus.PARTIAL)
    assert (capture.capture_policy, capture.capture_policy_version) == ("isolated", "1")
    assert capture.screenshots == ()


@pytest.mark.parametrize("fixture", FIXTURES)
def test_each_capture_round_trips_byte_for_byte(fixture: str) -> None:
    text = capture_text(fixture)
    assert to_capture_json(from_capture_json(text)) == text


def test_every_capture_shares_one_pinned_environment() -> None:
    captures = [from_capture_json(capture_text(fixture)) for fixture in FIXTURES]
    environments = {
        (
            capture.browser_version,
            capture.driver_version,
            capture.selenium_version,
            capture.os_name,
            capture.os_version,
            capture.architecture,
            capture.metadata_version,
        )
        for capture in captures
    }
    assert len(environments) == 1


@pytest.mark.parametrize("fixture", FIXTURES)
def test_every_layout1_unit_is_an_exact_span_or_an_alignment_failure(
    fixture: str,
) -> None:
    result = canonicalize(
        source(fixture), source_document_id=fixture, media_type="text/html"
    )
    assert isinstance(result, Canonicalized)
    extraction = LayoutExtractor().map_onto(
        from_capture_json(capture_text(fixture)), result.document
    )
    assert extraction.doc_id == result.document.doc_id
    assert validate_elements(result.document, extraction.elements) == ()
    parents = {
        element.parent_id
        for element in extraction.elements
        if element.parent_id is not None
    }
    placed = [
        element
        for element in extraction.elements
        if element.element_id not in parents
        and element.source_type != "layout:uncovered"
    ]
    assert len(placed) + len(extraction.failures) == extraction.units


@pytest.mark.browser
@pytest.mark.parametrize("fixture", FIXTURES)
def test_the_pinned_browser_still_renders_each_committed_capture(fixture: str) -> None:
    selenium_capture = pytest.importorskip(
        "earnings_ingestion.browser.selenium_capture",
        reason="needs the browser-capture extra",
    )
    binaries = installed()
    if binaries is None:
        pytest.skip("the pinned Chrome for Testing is not installed")
    committed = from_capture_json(capture_text(fixture))
    fresh = selenium_capture.SeleniumRenderer(binaries).capture(
        source(fixture), ISOLATED_1, source_document_id=fixture
    )
    assert (fresh.rendered_text_sha256, fresh.layout_sha256) == (
        committed.rendered_text_sha256,
        committed.layout_sha256,
    )
