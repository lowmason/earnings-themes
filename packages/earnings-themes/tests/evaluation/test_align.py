"""Alignment: spans to pointer units by character overlap, and character Jaccard's
counts (the Stage 11 spec, A3; FP13)."""

from earnings_themes.evaluation.align import (
    char_overlap,
    covered,
    difference,
    intersection,
    merged,
    unit_index,
    units_over,
)

from .cases import bundle, unit_ids


def test_each_paragraph_is_one_unit_in_document_order() -> None:
    source = bundle()
    index = unit_index(source)
    assert index.doc_id == source.document.doc_id
    assert [(s, e) for _, s, e in index.spans] == [
        (0, 20),
        (21, 37),
        (38, 56),
        (57, 73),
    ]


def test_a_span_maps_to_every_unit_it_shares_a_character_with() -> None:
    source = bundle()
    p0, p1, p2, p3 = unit_ids(source)
    index = unit_index(source)
    assert units_over(index, [(0, 5)]) == {p0}
    assert units_over(index, [(30, 45)]) == {p1, p2}
    assert units_over(index, [(20, 21)]) == set()
    assert units_over(index, [(19, 22)]) == {p0, p1}
    assert units_over(index, [(0, 5), (57, 73)]) == {p0, p3}


def test_spans_merge_and_count_each_character_once() -> None:
    assert merged([(5, 9), (0, 3), (2, 6), (12, 14)]) == ((0, 9), (12, 14))
    assert covered([(0, 5), (3, 8), (8, 10)]) == 10
    assert char_overlap([(0, 5), (57, 73)], [(0, 20)]) == (5, 36)
    assert char_overlap([(30, 45)], [(21, 37)]) == (7, 24)
    assert char_overlap([], []) == (0, 0)


def test_the_characters_both_cover_as_disjoint_spans() -> None:
    """[0, 9) and [12, 14) (merged from four) against [3, 13) share [3, 9) and
    [12, 13); adjacent spans share nothing; either side empty shares nothing."""
    assert intersection([(5, 9), (0, 3), (2, 6), (12, 14)], [(3, 13)]) == (
        (3, 9),
        (12, 13),
    )
    assert intersection([(0, 20), (57, 73)], [(21, 37), (60, 65), (70, 80)]) == (
        (60, 65),
        (70, 73),
    )
    assert intersection([(0, 5)], [(5, 9)]) == ()
    assert intersection([(0, 5)], []) == intersection([], [(0, 5)]) == ()


def test_the_characters_one_covers_and_the_other_does_not() -> None:
    """[0, 20) less a hole at its start [0, 3), in its middle [8, 10) and at its
    end [18, 25): [3, 8) and [10, 18). Adjacent holes [8, 10) and [10, 12) leave
    [0, 8) and [12, 20). A hole covering everything leaves nothing; no hole leaves
    the merged spans; several spans each lose their own part."""
    assert difference([(0, 20)], [(0, 3), (8, 10), (18, 25)]) == ((3, 8), (10, 18))
    assert difference([(0, 20)], [(10, 12), (8, 10)]) == ((0, 8), (12, 20))
    assert difference([(21, 37)], [(0, 73)]) == ()
    assert difference([(5, 9), (0, 6)], []) == ((0, 9),)
    assert difference([(0, 20), (57, 73)], [(15, 60)]) == ((0, 15), (60, 73))
    assert difference([], [(0, 5)]) == ()
