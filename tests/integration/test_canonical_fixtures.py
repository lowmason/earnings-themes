"""Stage 3's exit tests on the eight Stage 1 fixtures (Stage 3 spec: Verification
(plan A), items 4-6): R3.1, R4.1, R4.2, and R4.3."""

import socket
from pathlib import Path

import pytest
from earnings_core import (
    DocumentElement,
    ElementType,
    SpanCandidate,
    TextOrigin,
    VerifiedSpan,
    document_integrity_problem,
    hash_canonical_text,
    make_locator,
    validate_elements,
    validate_span,
)
from earnings_ingestion.canonical import Canonicalized, canonicalize

REPO = Path(__file__).resolve().parents[2]
RELEASES = REPO / "tests" / "fixtures" / "releases"
FIXTURE_IDS = sorted(path.parent.name for path in RELEASES.glob("*/source.html"))
PHARMACYCLICS = "0000949699-08-000023_ex-99-1"
NARRATIVE = frozenset(
    {
        ElementType.HEADING,
        ElementType.PARAGRAPH,
        ElementType.LIST_ITEM,
        ElementType.FOOTNOTE,
        ElementType.SENTENCE,
    }
)


@pytest.fixture
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: object, **kwargs: object) -> object:
        raise AssertionError("canonicalization reached for the network")

    for owner, name in (
        (socket.socket, "connect"),
        (socket.socket, "connect_ex"),
        (socket, "create_connection"),
        (socket, "getaddrinfo"),
    ):
        monkeypatch.setattr(owner, name, refuse)


def canonical(fixture: str) -> Canonicalized:
    raw = (RELEASES / fixture / "source.html").read_bytes()
    result = canonicalize(raw, source_document_id=fixture, media_type="text/html")
    assert isinstance(result, Canonicalized), result
    return result


def test_there_are_eight_fixtures() -> None:
    assert len(FIXTURE_IDS) == 8


@pytest.mark.usefixtures("no_network")
@pytest.mark.parametrize("fixture", FIXTURE_IDS)
def test_r3_1_and_r4_1_every_fixture_is_a_valid_canonical_document(
    fixture: str,
) -> None:
    result = canonical(fixture)
    document, text = result.document, result.document.canonical_text
    assert document_integrity_problem(document) is None
    assert document.canonical_hash == hash_canonical_text(text)
    assert validate_elements(document, result.elements) == ()
    for element in result.elements:
        unit = element.span.slice_of(text)
        assert unit == unit.strip(), element.element_id
        if element.type is ElementType.TABLE:
            continue
        if element.type is ElementType.OTHER and element.source_type in ("ul", "ol"):
            continue
        assert "\n" not in unit and "\t" not in unit, element.element_id


@pytest.mark.parametrize("fixture", FIXTURE_IDS)
def test_r4_1_every_sentence_round_trips_through_validate_span(fixture: str) -> None:
    result = canonical(fixture)
    document = result.document
    sentences = [e for e in result.elements if e.type is ElementType.SENTENCE]
    assert sentences
    for sentence in sentences:
        locator = make_locator(document, sentence.span)
        candidate = SpanCandidate(
            doc_id=document.doc_id,
            canonical_hash=document.canonical_hash,
            start=sentence.span.start,
            end=sentence.span.end,
            quote_text=sentence.span.slice_of(document.canonical_text),
            element_id=sentence.element_id,
            prefix=locator.prefix,
            suffix=locator.suffix,
        )
        verified = validate_span(document, result.elements, candidate)
        assert isinstance(verified, VerifiedSpan), verified


def overlaps_a_table(element: DocumentElement, tables: list[DocumentElement]) -> bool:
    return any(table.span.overlaps(element.span) for table in tables)


@pytest.mark.parametrize("fixture", FIXTURE_IDS)
def test_r4_2_no_narrative_element_overlaps_a_table(fixture: str) -> None:
    elements = canonical(fixture).elements
    tables = [e for e in elements if e.type is ElementType.TABLE]
    assert not [
        e.element_id
        for e in elements
        if e.type in NARRATIVE and overlaps_a_table(e, tables)
    ]


def test_r4_2_positive_control_the_fixtures_yield_cells() -> None:
    cells = sum(
        element.type is ElementType.TABLE_CELL
        for fixture in FIXTURE_IDS
        for element in canonical(fixture).elements
    )
    assert cells > 0


def test_r4_2_positive_control_pharmacyclics_pre_statements_are_tables() -> None:
    pieces = [e for e in canonical(PHARMACYCLICS).elements if e.source_type == "pre"]
    assert len(pieces) == 12
    assert {piece.type for piece in pieces} == {ElementType.TABLE}


def test_r4_2_positive_control_a_prose_pre_piece_stays_a_paragraph() -> None:
    raw = b"<pre>Revenue rose in every region.\nMargins widened.</pre>"
    result = canonicalize(raw, source_document_id="prose-pre", media_type="text/html")
    assert isinstance(result, Canonicalized)
    assert result.elements[0].type is ElementType.PARAGRAPH


@pytest.mark.parametrize("fixture", FIXTURE_IDS)
def test_r4_3_every_fixture_element_is_native(fixture: str) -> None:
    origins = {element.text_origin for element in canonical(fixture).elements}
    assert origins == {TextOrigin.NATIVE}
