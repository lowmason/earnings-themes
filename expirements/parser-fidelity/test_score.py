"""Scorer behaviour on hand-built gold and dumps, with hand-computed expectations."""

from pf_dump import Cell, Element, Row, grid_text
from score import cell_headers, gold_structure, pool, score_fixture
from validate_gold import SourceText

SOURCE = SourceText(
    b"<html><body>"
    b"<p><b>Acme Reports Record Third Quarter</b></p>"
    b"<p>Acme Corp. today reported net sales of $4.3 billion, up 5 percent.</p>"
    b"<p>Outlook</p><p>The company expects growth to continue next year.</p>"
    b"<table><tr><td></td><td>2025</td><td>2024</td></tr>"
    b"<tr><td>Net sales</td><td>4,321</td><td>3,210</td></tr>"
    b"<tr><td>Cost of sales</td><td>2,109</td><td>1,987</td></tr></table>"
    b"<p>(1) Excludes the impact of the divestiture completed in May.</p>"
    b"<p>Outlook</p>"
    b"</body></html>"
)

GOLD = {
    "blocks": [
        {"id": "h1", "type": "heading", "start": "Acme Reports Record Third Quarter"},
        {
            "id": "p1",
            "type": "paragraph",
            "start": "Acme Corp. today reported",
            "end": "billion, up 5 percent.",
        },
        {
            "id": "h2",
            "type": "heading",
            "start": "Outlook",
            "after": "The company expects",
        },
        {
            "id": "p2",
            "type": "paragraph",
            "start": "The company expects growth",
            "end": "to continue next year.",
        },
        {
            "id": "t1",
            "type": "table",
            "headers": ["2025", "2024"],
            "cells": [
                {
                    "role": "corner",
                    "text": "4,321",
                    "row_header": "Net sales",
                    "col_header": "2025",
                },
                {
                    "role": "right",
                    "text": "3,210",
                    "row_header": "Net sales",
                    "col_header": "2024",
                },
                {
                    "role": "below",
                    "text": "2,109",
                    "row_header": "Cost of sales",
                    "col_header": "2025",
                },
            ],
        },
        {
            "id": "f1",
            "type": "footnote",
            "start": "Excludes the impact of the",
            "end": "divestiture completed in May.",
        },
        {"id": "x1", "type": "page_artifact", "start": "- 2 -"},
        {"id": "u1", "type": "heading", "start": "Outlook", "unanchorable": True},
    ]
}

ROWS = (
    Row(True, (Cell(""), Cell("2025"), Cell("2024"))),
    Row(False, (Cell("Net sales"), Cell("4,321"), Cell("3,210"))),
    Row(False, (Cell("Cost of sales"), Cell("2,109"), Cell("1,987"))),
)
PERFECT = [
    Element("heading", "Acme Reports Record Third Quarter"),
    Element(
        "paragraph",
        "Acme Corp. today reported net sales of $4.3 billion, up 5 percent.",
    ),
    Element("heading", "Outlook"),
    Element("paragraph", "The company expects growth to continue next year."),
    Element("table", grid_text(ROWS), rows=ROWS),
    Element("footnote", "(1) Excludes the impact of the divestiture completed in May."),
]


def counts(elements):
    return score_fixture(GOLD, SOURCE, elements).counts


def test_a_perfect_dump_scores_perfectly():
    score = score_fixture(GOLD, SOURCE, PERFECT)
    assert score.counts["coverage"] == [6, 6]
    assert score.counts["footnote_merging"] == [0, 1]
    assert score.counts["reading_order"] == [
        0,
        7,
    ]  # h1 p1 h2 p2 corner right below f1 -> 8 items
    assert score.counts["header_section"] == [0, 2]
    assert score.counts["header_table"] == [0, 2]
    assert score.counts["cell_association"] == [3, 3]
    assert score.unanchorable == 1
    assert score.residual["missed"] == []


def test_missing_output_scores_zero_coverage():
    score = score_fixture(GOLD, SOURCE, None)
    assert score.counts["coverage"] == [0, 6]
    assert score.residual["missed"] == ["h1", "p1", "h2", "p2", "t1", "f1"]


def test_footnote_merged_into_a_paragraph():
    merged = PERFECT[:3] + [
        Element("paragraph", PERFECT[3].text + " " + PERFECT[5].text),
        PERFECT[4],
    ]
    result = counts(merged)
    assert result["footnote_merging"] == [1, 1]
    assert result["coverage"] == [6, 6]


def test_tables_appended_at_the_end_corrupt_reading_order():
    moved = PERFECT[:4] + [PERFECT[5], PERFECT[4]]
    score = score_fixture(GOLD, SOURCE, moved)
    assert score.counts["reading_order"] == [1, 7]
    assert score.residual["misordered"] == ["t1:below>f1"]


def test_heading_typed_as_paragraph_or_merged_is_header_loss():
    untyped = [Element("paragraph", PERFECT[0].text)] + PERFECT[1:]
    assert counts(untyped)["header_section"] == [1, 2]
    merged = [Element("paragraph", PERFECT[0].text + " " + PERFECT[1].text)] + PERFECT[
        2:
    ]
    assert counts(merged)["header_section"] == [1, 2]


def test_table_headers_outside_table_elements_are_lost():
    flat = PERFECT[:4] + [
        Element("paragraph", "2025 2024"),
        Element("paragraph", "Net sales 4,321 3,210 Cost of sales 2,109 1,987"),
        PERFECT[5],
    ]
    result = counts(flat)
    assert result["header_table"] == [2, 2]
    assert result["cell_association"] == [0, 0]


def test_folded_typography_is_found_and_marked_altered():
    folded = [
        Element("heading", "Acme Reports Record Third Quarter"),
        Element(
            "paragraph",
            "Acme Corp. today reported net sales of $4.3 billion, up 5 percent",
        ),
    ] + PERFECT[2:]
    score = score_fixture(GOLD, SOURCE, folded)
    assert score.counts["coverage"] == [6, 6]
    assert score.altered == ["p1:end"]


def test_split_blocks_and_duplicates_are_diagnosed():
    split = (
        [
            PERFECT[0],
            Element("paragraph", "Acme Corp. today reported net sales"),
            Element("paragraph", "of $4.3 billion, up 5 percent."),
        ]
        + PERFECT[2:]
        + [PERFECT[0]]
    )
    score = score_fixture(GOLD, SOURCE, split)
    assert score.counts["split"][0] == 1
    assert score.residual["split"] == ["p1"]
    assert score.counts["duplication"][0] == 1


def test_cell_headers_follow_grid_geometry_with_spans():
    rows = (
        Row(True, (Cell(""), Cell("Three Months Ended", 2))),
        Row(True, (Cell(""), Cell("2025"), Cell("2024"))),
        Row(False, (Cell("Net sales"), Cell("4,321"), Cell("3,210"))),
    )
    assert cell_headers(rows, "3,210") == ("Net sales", "Three Months Ended 2024")
    assert cell_headers(rows, "9,999") is None


def test_pool_sums_numerators_and_denominators_and_means_header_subrates():
    first = score_fixture(GOLD, SOURCE, PERFECT)
    second = score_fixture(
        GOLD, SOURCE, [Element("paragraph", PERFECT[0].text)] + PERFECT[1:]
    )
    pooled = pool([first, second])
    assert pooled["counts"]["coverage"] == [12, 12]
    assert pooled["counts"]["header_section"] == [1, 4]
    assert pooled["rates"]["header_loss"] == (0.25 + 0.0) / 2
    assert pooled["rates"]["header_loss_n"] == 8


def test_gold_structure_reports_levels_and_footnote_placement():
    structure = gold_structure(GOLD)
    assert structure["types"]["heading"] == 3
    assert structure["footnote_placement"] == {"after table": 1}
