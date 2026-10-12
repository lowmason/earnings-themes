"""Alignment: spans to pointer units by character overlap, and character Jaccard's
counts (the Stage 11 spec, A3; FP13)."""

from earnings_themes.evaluation.align import (
    char_overlap,
    covered,
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
