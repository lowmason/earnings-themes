"""R4.3: text recognized from an image is flagged and never verified as a quotation."""

from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    Rejection,
    RejectionReason,
    SpanCandidate,
    TextOrigin,
    TextSpan,
    VerifiedSpan,
    make_locator,
    validate_span,
)

NATIVE = "Revenue rose 5% to $2.1 billion."
RECOGNIZED = "Net sales grew in every region."
TEXT = f"{NATIVE}\n{RECOGNIZED}"
RECOGNIZED_START = len(NATIVE) + 1
DOCUMENT = CanonicalDocument.create(
    source_document_id="ocr-test",
    canonicalization_version="test-1",
    canonical_text=TEXT,
)
WHOLE = DocumentElement.create(
    DOCUMENT, ElementType.OTHER, TextSpan(start=0, end=len(TEXT))
)
PARAGRAPH = DocumentElement.create(
    DOCUMENT, ElementType.PARAGRAPH, TextSpan(start=0, end=len(NATIVE))
)
FROM_IMAGE = DocumentElement.create(
    DOCUMENT,
    ElementType.PARAGRAPH,
    TextSpan(start=RECOGNIZED_START, end=len(TEXT)),
    text_origin=TextOrigin.OCR,
)
ELEMENTS = (WHOLE, PARAGRAPH, FROM_IMAGE)


def candidate(start: int, end: int, element: DocumentElement) -> SpanCandidate:
    locator = make_locator(DOCUMENT, TextSpan(start=start, end=end))
    return SpanCandidate(
        doc_id=DOCUMENT.doc_id,
        canonical_hash=DOCUMENT.canonical_hash,
        start=start,
        end=end,
        quote_text=TEXT[start:end],
        element_id=element.element_id,
        prefix=locator.prefix,
        suffix=locator.suffix,
    )


def test_native_text_verifies() -> None:
    outcome = validate_span(DOCUMENT, ELEMENTS, candidate(0, len(NATIVE), PARAGRAPH))
    assert isinstance(outcome, VerifiedSpan)


def test_an_exact_quote_of_ocr_text_is_refused() -> None:
    outcome = validate_span(
        DOCUMENT, ELEMENTS, candidate(RECOGNIZED_START, len(TEXT), FROM_IMAGE)
    )
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.OCR_DERIVED_TEXT
    assert FROM_IMAGE.element_id in outcome.detail


def test_a_span_that_partly_overlaps_ocr_text_is_refused() -> None:
    start = TEXT.index("billion")
    outcome = validate_span(
        DOCUMENT, ELEMENTS, candidate(start, RECOGNIZED_START + 3, WHOLE)
    )
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.OCR_DERIVED_TEXT


def test_an_ocr_element_of_another_version_does_not_count() -> None:
    other = CanonicalDocument.create(
        source_document_id="ocr-test",
        canonicalization_version="test-2",
        canonical_text=TEXT,
    )
    stale = DocumentElement.create(
        other, ElementType.PARAGRAPH, FROM_IMAGE.span, text_origin=TextOrigin.OCR
    )
    native = DocumentElement.create(DOCUMENT, ElementType.PARAGRAPH, FROM_IMAGE.span)
    outcome = validate_span(
        DOCUMENT,
        (WHOLE, PARAGRAPH, native, stale),
        candidate(RECOGNIZED_START, len(TEXT), native),
    )
    assert isinstance(outcome, VerifiedSpan)


def test_the_speaker_turn_check_runs_first() -> None:
    turn = DocumentElement.create(
        DOCUMENT, ElementType.SPEAKER_TURN, TextSpan(start=0, end=len(NATIVE))
    )
    start = TEXT.index("billion")
    outcome = validate_span(
        DOCUMENT,
        (WHOLE, turn, FROM_IMAGE),
        candidate(start, RECOGNIZED_START + 3, WHOLE),
    )
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.CROSSES_SPEAKER_TURN
