"""Mapping policy anchored-1: exact, reversible, never a first match (SC13)."""

import pytest
from earnings_core import RejectionReason, TextSpan
from earnings_ingestion.layout.align import CollapsedText, align

NOT_FOUND = RejectionReason.LOCATOR_NOT_FOUND
AMBIGUOUS = RejectionReason.AMBIGUOUS_OCCURRENCE


def places(text: str, units: list[str]) -> list[int | RejectionReason]:
    collapsed = CollapsedText.of(text)
    return [
        placed.start if placed.start is not None else placed.reason
        for placed in align(collapsed, units)
    ]


def test_the_collapsed_text_maps_back_to_exact_canonical_spans() -> None:
    canonical = "Net sales\t$\t9.8\nCost  of sales\n"
    collapsed = CollapsedText.of(canonical)
    assert collapsed.text == "Net sales $ 9.8 Cost of sales"
    start = collapsed.text.index("9.8 Cost")
    span = collapsed.span(start, start + len("9.8 Cost"))
    assert span == TextSpan(start=12, end=20)
    assert canonical[span.start : span.end] == "9.8\nCost"


def test_occurrences_are_token_bounded_and_may_overlap() -> None:
    collapsed = CollapsedText.of("2019 1 a a a")
    assert collapsed.occurrences("1") == [5]
    assert collapsed.occurrences("a a") == [7, 9]
    assert collapsed.occurrences("") == []


def test_unique_units_map_and_missing_ones_are_not_found() -> None:
    assert places(
        "Revenue rose. Margins held.", ["Revenue rose.", "Guidance", "Margins held."]
    ) == [
        0,
        NOT_FOUND,
        14,
    ]


def test_neighbours_settle_repeated_cells() -> None:
    text = "Net sales $ 9.8 Cost $ 7.1"
    assert places(text, ["Net sales", "$", "9.8", "Cost", "$", "7.1"]) == [
        0,
        10,
        12,
        16,
        21,
        23,
    ]


def test_equal_counts_between_neighbours_map_in_order() -> None:
    text = "Shares 9,988 9,988 9,988 Total 9,988"
    units = ["Shares", "9,988", "9,988", "9,988", "Total", "9,988"]
    assert places(text, units) == [0, 7, 13, 19, 25, 31]


def test_a_repeat_the_neighbours_cannot_settle_stays_ambiguous() -> None:
    assert places("x y x", ["x"]) == [AMBIGUOUS]
    assert places("A x x B", ["A", "x", "B"]) == [0, AMBIGUOUS, 6]


def test_one_unit_far_out_of_place_costs_only_itself() -> None:
    text = "Intro Middle End Late"
    assert places(text, ["Intro", "Late", "Middle", "End"]) == [0, AMBIGUOUS, 6, 13]


def test_neither_unit_of_a_swapped_pair_is_kept() -> None:
    assert places("A B C", ["B", "A", "C"]) == [AMBIGUOUS, AMBIGUOUS, 4]


def test_overlapping_places_are_both_refused() -> None:
    assert places("A B C", ["A B", "B C"]) == [AMBIGUOUS, AMBIGUOUS]


def test_every_unit_inside_a_longer_one_is_refused_with_it() -> None:
    assert places("A B C D", ["A B C", "A", "C", "D"]) == [
        AMBIGUOUS,
        AMBIGUOUS,
        AMBIGUOUS,
        6,
    ]


@pytest.mark.parametrize("text", ["", "   \n\t "])
def test_an_empty_text_holds_nothing(text: str) -> None:
    assert CollapsedText.of(text).text == ""
    assert places(text, ["A"]) == [NOT_FOUND]
