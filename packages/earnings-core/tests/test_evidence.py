import inspect
import json

import pytest
from earnings_core.elements import ElementType
from earnings_core.evidence import (
    SpanCandidate,
    VerifiedSpan,
    parse_span_candidate,
    validate_span,
)
from earnings_core.locators import SpanLocator, make_locator, resolve_locator
from earnings_core.rejections import VALIDATOR_VERSION, Rejection, RejectionReason
from earnings_core.structure import resolve_pointer
from pydantic import ValidationError


def test_a_valid_candidate_is_verified(sample) -> None:
    candidate = sample.candidate("Margins held at last year's level.")
    verified = validate_span(sample.document, sample.elements, candidate)
    assert isinstance(verified, VerifiedSpan)
    assert verified.quote_text == sample.text[verified.start : verified.end]
    assert verified.validator_version == VALIDATOR_VERSION
    assert verified.span == sample.span_of("Margins held at last year's level.")


def test_each_occurrence_of_repeated_text_verifies_with_its_own_context(
    sample,
) -> None:
    for occurrence in (0, 1):
        candidate = sample.candidate("Results are preliminary.", occurrence)
        verified = validate_span(sample.document, sample.elements, candidate)
        assert isinstance(verified, VerifiedSpan)
        assert (
            verified.start
            == sample.span_of("Results are preliminary.", occurrence).start
        )


def test_a_span_may_be_attributed_to_any_element_that_contains_it(sample) -> None:
    turn = sample.element(ElementType.SPEAKER_TURN, "CFO:")
    candidate = sample.candidate("Margins held", element_id=turn.element_id)
    verified = validate_span(sample.document, sample.elements, candidate)
    assert isinstance(verified, VerifiedSpan)
    assert verified.element_id == turn.element_id


def test_a_pointer_resolves_to_a_span_that_verifies(sample) -> None:
    sentence = sample.element(ElementType.SENTENCE, "Revenue rose")
    span = resolve_pointer(sample.document, sample.elements, sentence.element_id)
    text = span.slice_of(sample.text)
    locator = make_locator(sample.document, span)
    candidate = SpanCandidate(
        doc_id=sample.document.doc_id,
        canonical_hash=sample.document.canonical_hash,
        start=span.start,
        end=span.end,
        quote_text=text,
        element_id=sentence.element_id,
        prefix=locator.prefix,
        suffix=locator.suffix,
    )
    assert isinstance(
        validate_span(sample.document, sample.elements, candidate), VerifiedSpan
    )


def test_a_located_span_verifies(sample) -> None:
    proposed = SpanLocator(exact="Welcome to the call.")
    span = resolve_locator(sample.document, proposed)
    candidate = sample.candidate("Welcome to the call.")
    assert candidate.span == span
    assert isinstance(
        validate_span(sample.document, sample.elements, candidate), VerifiedSpan
    )


def test_the_first_failing_check_is_the_recorded_reason(sample) -> None:
    candidate = sample.candidate(
        "Margins held", doc_id="another@test-1#0000000000000000", quote_text="x"
    )
    outcome = validate_span(sample.document, sample.elements, candidate)
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.WRONG_DOCUMENT


def test_the_validator_takes_no_tolerance() -> None:
    assert list(inspect.signature(validate_span).parameters) == [
        "document",
        "elements",
        "candidate",
    ]


def test_candidate_fields_are_closed_and_strict(sample) -> None:
    with pytest.raises(ValidationError):
        sample.candidate("Margins held", start=True)
    with pytest.raises(ValidationError):
        sample.candidate("Margins held", ranges=[(0, 3)])


def test_json_text_bytes_and_mappings_parse_the_same(sample) -> None:
    raw = sample.raw("Margins held")
    expected = SpanCandidate(**raw)
    assert parse_span_candidate(raw) == expected
    assert parse_span_candidate(json.dumps(raw)) == expected
    assert parse_span_candidate(json.dumps(raw).encode()) == expected


@pytest.mark.parametrize(
    "raw",
    ["{not json", "[1, 2]", 42, None, ["doc_id"]],
    ids=["broken-json", "json-array", "int", "none", "list"],
)
def test_anything_but_a_candidate_object_is_malformed(raw: object) -> None:
    outcome = parse_span_candidate(raw)
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.MALFORMED_RECORD
    assert outcome.detail


def test_a_malformed_record_names_the_offending_field(sample) -> None:
    outcome = parse_span_candidate(sample.raw("Margins held", start=1.5))
    assert isinstance(outcome, Rejection)
    assert outcome.detail.startswith("start:")
