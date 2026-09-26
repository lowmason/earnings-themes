"""Two parser implementations emit one browser-neutral element schema (D-15, B5).

The real pair (Stage 3 spec, Layout extractor): walker-1 canonicalizes the contract
release, and layout-1 maps a real capture of the same bytes onto walker-1's document,
the sole coordinate system. The capture is committed
(tests/fixtures/browser/contract-release.capture.json), so the default suite runs the
pair with no browser; the last test, opt-in with ``-m browser``, checks that the
pinned browser still renders exactly that capture.
"""

import json
from pathlib import Path

import pytest
from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    RejectionReason,
    sha256_hex,
    validate_elements,
)
from earnings_ingestion.browser import ISOLATED_1, CaptureStatus
from earnings_ingestion.browser.install import installed
from earnings_ingestion.browser.serialize import from_capture_json
from earnings_ingestion.canonical import Canonicalized, canonicalize
from earnings_ingestion.layout import LayoutExtraction, LayoutExtractor

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "browser"
SOURCE = (FIXTURES / "contract-release.html").read_bytes()
CAPTURE = from_capture_json(
    (FIXTURES / "contract-release.capture.json").read_text(encoding="utf-8")
)
REPEATED = "Results are preliminary."


def walker1(source: bytes = SOURCE) -> Canonicalized:
    result = canonicalize(
        source, source_document_id="contract-release", media_type="text/html"
    )
    assert isinstance(result, Canonicalized)
    return result


def layout1(document: CanonicalDocument) -> LayoutExtraction:
    return LayoutExtractor().map_onto(CAPTURE, document)


def comparable(element: DocumentElement) -> dict:
    """Everything but provenance; layout-1 emits no list containers, so a list item's
    parent is left out too."""
    exclude = {"source_type"}
    if element.type is ElementType.LIST_ITEM:
        exclude.add("parent_id")
    return element.model_dump(exclude=exclude)


def test_the_committed_capture_is_of_the_contract_release() -> None:
    assert CAPTURE.raw_sha256 == sha256_hex(SOURCE)
    assert CAPTURE.status is CaptureStatus.COMPLETED
    assert (CAPTURE.capture_policy, CAPTURE.capture_policy_version) == ("isolated", "1")


def test_walker1_emits_a_valid_element_set() -> None:
    result = walker1()
    assert validate_elements(result.document, result.elements) == ()
    assert not any(e.source_type.startswith("layout:") for e in result.elements)


def test_layout1_maps_valid_elements_onto_the_same_document() -> None:
    document = walker1().document
    extraction = layout1(document)
    assert extraction.doc_id == document.doc_id
    assert extraction.failures == ()
    assert validate_elements(document, extraction.elements) == ()
    assert all(e.source_type.startswith("layout:") for e in extraction.elements)


def test_elements_both_readers_place_agree_in_everything_but_provenance() -> None:
    result = walker1()
    containers = {
        e.parent_id for e in result.elements if e.type is ElementType.LIST_ITEM
    }
    expected = [
        comparable(e)
        for e in result.elements
        if e.type is not ElementType.SENTENCE and e.element_id not in containers
    ]
    assert [comparable(e) for e in layout1(result.document).elements] == expected


def test_repeated_text_is_placed_by_its_neighbours_never_by_a_first_match() -> None:
    result = walker1()
    text = result.document.canonical_text
    assert text.count(REPEATED) == 2

    def placed(elements) -> list[tuple[ElementType, int]]:
        return [
            (e.type, e.span.start)
            for e in elements
            if e.span.slice_of(text) == REPEATED and e.type is not ElementType.SENTENCE
        ]

    expected = [(ElementType.PARAGRAPH, 68), (ElementType.LIST_ITEM, 111)]
    assert placed(result.elements) == expected
    assert placed(layout1(result.document).elements) == expected


def test_text_the_document_lacks_is_not_found_and_stays_uncovered() -> None:
    changed = walker1(SOURCE.replace(b"rose 5%", b"rose 6%")).document
    extraction = layout1(changed)
    assert [(f.reason, f.unit_type, f.text) for f in extraction.failures] == [
        (
            RejectionReason.LOCATOR_NOT_FOUND,
            "paragraph",
            "Revenue rose 5% to $2.1 billion.",
        )
    ]
    uncovered = [
        e.span.slice_of(changed.canonical_text)
        for e in extraction.elements
        if e.source_type == "layout:uncovered"
    ]
    assert uncovered == ["Revenue rose 6% to $2.1 billion."]


def test_a_repeat_its_neighbours_cannot_settle_is_ambiguous() -> None:
    doubled = walker1(
        SOURCE.replace(b"<ul>", b"<p>Margins expanded.</p><ul>", 1)
    ).document
    extraction = layout1(doubled)
    assert [(f.reason, f.text) for f in extraction.failures] == [
        (RejectionReason.AMBIGUOUS_OCCURRENCE, "Margins expanded.")
    ]
    uncovered = [
        e.span.slice_of(doubled.canonical_text)
        for e in extraction.elements
        if e.source_type == "layout:uncovered"
    ]
    assert uncovered == ["Margins expanded.", "Margins expanded."]


def test_both_readers_emit_records_of_the_one_schema() -> None:
    result = walker1()
    fields = set(DocumentElement.model_fields)
    for element in [*result.elements, *layout1(result.document).elements]:
        payload = element.model_dump_json()
        assert set(json.loads(payload)) == fields
        assert DocumentElement.model_validate_json(payload) == element


@pytest.mark.browser
def test_the_pinned_browser_still_renders_the_committed_capture() -> None:
    selenium_capture = pytest.importorskip(
        "earnings_ingestion.browser.selenium_capture",
        reason="needs the browser-capture extra",
    )
    binaries = installed()
    if binaries is None:
        pytest.skip("the pinned Chrome for Testing is not installed")
    fresh = selenium_capture.SeleniumRenderer(binaries).capture(
        SOURCE, ISOLATED_1, source_document_id="contract-release"
    )
    assert (fresh.rendered_text_sha256, fresh.layout_sha256) == (
        CAPTURE.rendered_text_sha256,
        CAPTURE.layout_sha256,
    )
