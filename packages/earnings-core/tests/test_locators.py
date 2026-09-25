import pytest
from earnings_core.documents import CanonicalDocument
from earnings_core.locators import (
    SpanLocator,
    make_locator,
    occurrences,
    resolve_locator,
)
from earnings_core.rejections import Rejection, RejectionReason
from earnings_core.spans import TextSpan
from pydantic import ValidationError


def document(text: str) -> CanonicalDocument:
    return CanonicalDocument.create(
        source_document_id="locator-test",
        canonicalization_version="test-1",
        canonical_text=text,
    )


def span_at(text: str, needle: str, occurrence: int) -> TextSpan:
    start = -1
    for _ in range(occurrence + 1):
        start = text.index(needle, start + 1)
    return TextSpan(start=start, end=start + len(needle))


def test_unique_text_needs_no_context(sample) -> None:
    span = sample.span_of("Margins held")
    assert make_locator(sample.document, span) == SpanLocator(exact="Margins held")


def test_a_repeated_sentence_gets_one_word_each_side(sample) -> None:
    first = make_locator(sample.document, sample.span_of("Results are preliminary."))
    second = make_locator(
        sample.document, sample.span_of("Results are preliminary.", 1)
    )
    assert (first.prefix, first.suffix) == ("\U0001f4c8. ", "\nQuestions")
    assert (second.prefix, second.suffix) == ("CFO: ", " Margins")


def test_context_grows_until_the_occurrence_is_unique() -> None:
    text = "x a b TARGET c y and z a b TARGET c w"
    locator = make_locator(document(text), span_at(text, "TARGET", 1))
    # One word each side ("b ", " c") still matches both; two words do not.
    assert (locator.prefix, locator.suffix) == ("a b ", " c w")


def test_a_word_cut_by_the_span_edge_counts_as_one_word() -> None:
    text = "prerevenue and revenue"
    locator = make_locator(document(text), span_at(text, "revenue", 0))
    assert (locator.prefix, locator.suffix) == ("pre", " and")


def test_context_stops_at_the_document_edges() -> None:
    # "abab" is one word, so each side's context is the rest of that word.
    text = "abab"
    assert make_locator(document(text), TextSpan(start=0, end=2)) == SpanLocator(
        exact="ab", prefix="", suffix="ab"
    )
    assert make_locator(document(text), TextSpan(start=2, end=4)) == SpanLocator(
        exact="ab", prefix="ab", suffix=""
    )


def test_every_span_round_trips_through_its_locator(sample) -> None:
    for element in sample.elements:
        locator = make_locator(sample.document, element.span)
        assert resolve_locator(sample.document, locator) == element.span


def test_overlapping_occurrences_count() -> None:
    assert occurrences("aaa", SpanLocator(exact="aa")) == [0, 1]


def test_a_repeated_text_without_context_is_ambiguous_never_first_match(
    sample,
) -> None:
    outcome = resolve_locator(
        sample.document, SpanLocator(exact="Results are preliminary.")
    )
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.AMBIGUOUS_OCCURRENCE


@pytest.mark.parametrize(
    "locator",
    [
        SpanLocator(exact="Results were final."),
        SpanLocator(exact="Results are preliminary.", prefix="CTO: "),
    ],
    ids=["absent-text", "absent-context"],
)
def test_a_locator_that_matches_nothing_is_rejected(sample, locator) -> None:
    outcome = resolve_locator(sample.document, locator)
    assert isinstance(outcome, Rejection)
    assert outcome.reason is RejectionReason.LOCATOR_NOT_FOUND


def test_exact_text_may_not_be_empty() -> None:
    with pytest.raises(ValidationError):
        SpanLocator(exact="")
