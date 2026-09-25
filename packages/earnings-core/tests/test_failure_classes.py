"""Stage 2 exit evidence: each failure class is rejected with a recorded reason.

One row per failure class, named for the requirement or V9 case it closes. Every row
starts from a candidate that verifies and changes one thing about it.
"""

import unicodedata

import pytest
from earnings_core import (
    VALIDATOR_VERSION,
    CanonicalDocument,
    ElementType,
    Rejection,
    RejectionReason,
    SpanLocator,
    TextChunk,
    TextSpan,
    VerifiedSpan,
    hash_canonical_text,
    parse_span_candidate,
    resolve_locator,
    resolve_pointer,
    validate_span,
)

R = RejectionReason
MARGINS = "Margins held at last year's level."
RESULTS = "Results are preliminary."
QUESTION = "How did the caf\u00e9 segment do?"


def check(sample, raw: object) -> VerifiedSpan | Rejection:
    """Parse, then verify: the path every candidate takes."""
    parsed = parse_span_candidate(raw)
    if isinstance(parsed, Rejection):
        return parsed
    return validate_span(sample.document, sample.elements, parsed)


def utf8_offsets(sample):
    data = sample.text.encode("utf-8")
    start = data.index(RESULTS.encode("utf-8"))
    return check(sample, sample.raw(RESULTS, start=start, end=start + len(RESULTS)))


def utf16_offsets(sample):
    units = sample.text.encode("utf-16-le")
    start = units.index(RESULTS.encode("utf-16-le")) // 2
    return check(sample, sample.raw(RESULTS, start=start, end=start + len(RESULTS)))


def newer_version(sample) -> CanonicalDocument:
    return CanonicalDocument.create(
        source_document_id=sample.document.source_document_id,
        canonicalization_version=sample.document.canonicalization_version,
        canonical_text=sample.text.replace("5%", "6%"),
    )


def span_from_previous_version(sample):
    return validate_span(
        newer_version(sample), sample.elements, sample.candidate(MARGINS)
    )


def text_changed_beneath_spans(sample):
    edited = sample.document.model_copy(
        update={"canonical_text": sample.text.replace("5%", "6%")}
    )
    return validate_span(edited, sample.elements, sample.candidate(MARGINS))


def stitched(sample, joiner: str):
    turn = sample.element(ElementType.SPEAKER_TURN, "CEO:")
    return check(
        sample,
        sample.raw(
            "Revenue rose 5%",
            end=sample.span_of(RESULTS).end,
            quote_text=f"Revenue rose 5%{joiner}{RESULTS}",
            element_id=turn.element_id,
        ),
    )


def two_ranges(sample):
    first, second = sample.span_of(RESULTS), sample.span_of(MARGINS)
    return check(
        sample,
        sample.raw(
            RESULTS, ranges=[[first.start, first.end], [second.start, second.end]]
        ),
    )


def end_past_the_text(sample):
    length = len(sample.text)
    return check(
        sample,
        sample.raw(
            MARGINS, start=length - 3, end=length + 5, quote_text=sample.text[-3:]
        ),
    )


def same_text_in_another_document(sample):
    other = CanonicalDocument.create(
        source_document_id="another-call",
        canonicalization_version=sample.document.canonicalization_version,
        canonical_text=sample.text,
    )
    return validate_span(other, sample.elements, sample.candidate(MARGINS))


def attributed_to(sample, needle: str, occurrence: int, element_type, holder: str):
    element = sample.element(element_type, holder)
    return check(sample, sample.raw(needle, occurrence, element_id=element.element_id))


def crossing_speaker_turns(sample):
    start = sample.span_of("Welcome to the call.").start
    end = sample.span_of("CEO: Revenue").end
    section = sample.element(ElementType.SECTION, "Prepared remarks")
    return check(
        sample,
        sample.raw(
            "Welcome to the call.",
            end=end,
            quote_text=sample.text[start:end],
            element_id=section.element_id,
        ),
    )


def chunk_offsets_stored_unconverted(sample):
    turn = sample.element(ElementType.SPEAKER_TURN, "CFO:")
    chunk = TextChunk.of(sample.document, turn.span)
    local = chunk.text.index(MARGINS)
    return check(sample, sample.raw(MARGINS, start=local, end=local + len(MARGINS)))


def local_span_past_its_chunk(sample):
    chunk = TextChunk.of(sample.document, sample.span_of(MARGINS))
    return chunk.to_document_span(TextSpan(start=0, end=len(MARGINS) + 1))


CASES = [
    # R3.2: offsets are strict integers counting code points.
    (
        "R3.2-offset-is-a-bool",
        lambda s: check(s, s.raw(MARGINS, start=True)),
        R.MALFORMED_RECORD,
    ),
    (
        "R3.2-offset-is-a-float",
        lambda s: check(s, s.raw(MARGINS, end=9.0)),
        R.MALFORMED_RECORD,
    ),
    (
        "R3.2-offset-is-a-string",
        lambda s: check(s, s.raw(MARGINS, start="3")),
        R.MALFORMED_RECORD,
    ),
    ("R3.2-utf8-byte-offsets", utf8_offsets, R.QUOTE_TEXT_MISMATCH),
    ("R3.2-utf16-code-unit-offsets", utf16_offsets, R.QUOTE_TEXT_MISMATCH),
    # R3.3 and V9 canonical version changes: changed text is a new version.
    (
        "R3.3-span-from-the-previous-version",
        span_from_previous_version,
        R.WRONG_DOCUMENT,
    ),
    (
        "R3.3-text-changed-beneath-spans",
        text_changed_beneath_spans,
        R.DOCUMENT_INTEGRITY,
    ),
    # R5.4 and V9 duplicated passages: context singles out one occurrence.
    (
        "R5.4-repeated-text-without-context",
        lambda s: check(s, s.raw(RESULTS, 1, prefix="", suffix="")),
        R.AMBIGUOUS_OCCURRENCE,
    ),
    (
        "R5.4-context-not-around-the-span",
        lambda s: check(s, s.raw(RESULTS, 1, prefix="CEO: ")),
        R.LOCATOR_MISMATCH,
    ),
    (
        "R5.4-locating-repeated-text-without-context",
        lambda s: resolve_locator(s.document, SpanLocator(exact=RESULTS)),
        R.AMBIGUOUS_OCCURRENCE,
    ),
    (
        "R5.4-locator-matching-nothing",
        lambda s: resolve_locator(s.document, SpanLocator(exact="Results were final.")),
        R.LOCATOR_NOT_FOUND,
    ),
    # R5.5 and V9 stitched spans: one record is one contiguous range.
    (
        "R5.5-stitched-with-an-ellipsis",
        lambda s: stitched(s, " \u2026 "),
        R.QUOTE_TEXT_MISMATCH,
    ),
    (
        "R5.5-joined-without-an-ellipsis",
        lambda s: stitched(s, " "),
        R.QUOTE_TEXT_MISMATCH,
    ),
    ("R5.5-two-ranges-in-one-record", two_ranges, R.MALFORMED_RECORD),
    # R6.1: bounds, identity, hash, text, and attribution.
    ("R6.1-end-past-the-text", end_past_the_text, R.SPAN_OUT_OF_BOUNDS),
    (
        "R6.1-empty-span",
        lambda s: check(s, s.raw(MARGINS, end=s.span_of(MARGINS).start)),
        R.MALFORMED_RECORD,
    ),
    (
        "R6.1-negative-start",
        lambda s: check(s, s.raw(MARGINS, start=-1)),
        R.MALFORMED_RECORD,
    ),
    (
        "R6.1-same-text-in-another-document",
        same_text_in_another_document,
        R.WRONG_DOCUMENT,
    ),
    (
        "R6.1-stale-hash",
        lambda s: check(
            s, s.raw(MARGINS, canonical_hash=hash_canonical_text(s.text + " "))
        ),
        R.CANONICAL_HASH_MISMATCH,
    ),
    (
        "R6.1-wrong-section",
        lambda s: attributed_to(s, MARGINS, 0, ElementType.SECTION, "Prepared remarks"),
        R.OUTSIDE_ELEMENT,
    ),
    (
        "R6.1-wrong-speaker-turn",
        lambda s: attributed_to(s, RESULTS, 1, ElementType.SPEAKER_TURN, "CEO:"),
        R.OUTSIDE_ELEMENT,
    ),
    # V9 speaker boundaries, invalid pointers, and chunk coordinates.
    ("V9-span-crossing-speaker-turns", crossing_speaker_turns, R.CROSSES_SPEAKER_TURN),
    (
        "V9-attribution-to-no-element",
        lambda s: check(s, s.raw(MARGINS, element_id="sentence-0-5")),
        R.UNKNOWN_ELEMENT,
    ),
    (
        "V9-pointer-to-no-element",
        lambda s: resolve_pointer(s.document, s.elements, "paragraph-0-16"),
        R.UNKNOWN_ELEMENT,
    ),
    (
        "V9-pointer-into-another-version",
        lambda s: resolve_pointer(
            newer_version(s), s.elements, s.elements[0].element_id
        ),
        R.WRONG_DOCUMENT,
    ),
    (
        "V9-chunk-offsets-stored-unconverted",
        chunk_offsets_stored_unconverted,
        R.QUOTE_TEXT_MISMATCH,
    ),
    ("V9-local-span-past-its-chunk", local_span_past_its_chunk, R.OUTSIDE_CHUNK),
    # R13.2: exactness has no tolerance; a near miss is a miss.
    (
        "R13.2-decomposed-accent",
        lambda s: check(
            s, s.raw(QUESTION, quote_text=unicodedata.normalize("NFD", QUESTION))
        ),
        R.QUOTE_TEXT_MISMATCH,
    ),
    (
        "R13.2-curly-apostrophe",
        lambda s: check(s, s.raw(MARGINS, quote_text=MARGINS.replace("'", "\u2019"))),
        R.QUOTE_TEXT_MISMATCH,
    ),
    (
        "R13.2-doubled-space",
        lambda s: check(
            s, s.raw(MARGINS, quote_text=MARGINS.replace(" held", "  held"))
        ),
        R.QUOTE_TEXT_MISMATCH,
    ),
    (
        "R13.2-changed-case",
        lambda s: check(s, s.raw(MARGINS, quote_text=MARGINS.lower())),
        R.QUOTE_TEXT_MISMATCH,
    ),
    (
        "R13.2-trailing-space",
        lambda s: check(s, s.raw(MARGINS, quote_text=MARGINS + " ")),
        R.QUOTE_TEXT_MISMATCH,
    ),
]


@pytest.mark.parametrize(
    ("case", "expected"),
    [pytest.param(case, expected, id=name) for name, case, expected in CASES],
)
def test_the_failure_class_is_rejected_with_its_reason(sample, case, expected) -> None:
    outcome = case(sample)
    assert isinstance(outcome, Rejection), outcome
    assert outcome.reason is expected, outcome.detail
    assert outcome.detail
    assert outcome.validator_version == VALIDATOR_VERSION


@pytest.mark.parametrize(
    ("needle", "occurrence"),
    [
        (MARGINS, 0),
        (RESULTS, 0),
        (RESULTS, 1),
        ("Welcome to the call.", 0),
        ("Revenue rose 5%", 0),
        (QUESTION, 0),
    ],
)
def test_every_row_starts_from_a_candidate_that_verifies(
    sample, needle: str, occurrence: int
) -> None:
    assert isinstance(check(sample, sample.raw(needle, occurrence)), VerifiedSpan)
