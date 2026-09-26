"""layout-1's blocks from synthetic layout metadata: the L-rules, one by one."""

import pytest
from earnings_ingestion.browser.metadata import parse_metadata
from earnings_ingestion.browser.records import LayoutMetadata
from earnings_ingestion.layout.blocks import LayoutBlocks, body_size

BULLET = chr(0x2022)


def layout(blocks: list[dict], tables: list[dict] = ()) -> LayoutMetadata:
    return parse_metadata({"blocks": blocks, "tables": list(tables)})


def typed(metadata: LayoutMetadata) -> list[tuple[str, str, int | None]]:
    return [(b.type, b.text, b.level) for b in LayoutBlocks(metadata).blocks]


def body(parts, *extra: dict) -> list[dict]:
    """Enough body-size text that the body size is 16."""
    sentence = "The quarter's results were in line with the outlook we gave."
    return [parts.block(parts.run(sentence)), *extra]


def test_two_breaks_end_a_block_and_one_is_a_space(parts) -> None:
    blocks = [
        parts.block(
            parts.run("One"),
            parts.br(),
            parts.run("two"),
            parts.br(),
            parts.run(" "),
            parts.br(),
            parts.run("Three"),
        )
    ]
    assert typed(layout(blocks)) == [
        ("paragraph", "One two", None),
        ("paragraph", "Three", None),
    ]


@pytest.mark.parametrize("style", [{"bold": True}, {"underline": True}])
def test_a_short_emphasized_block_is_a_heading(style: dict, parts) -> None:
    blocks = body(parts, parts.block(parts.run("Outlook", **style)))
    assert typed(layout(blocks))[-1] == ("heading", "Outlook", None)


def test_a_long_emphasized_block_is_a_paragraph(parts) -> None:
    words = " ".join(["word"] * 13)
    blocks = body(parts, parts.block(parts.run(words, bold=True)))
    assert typed(layout(blocks))[-1][0] == "paragraph"


def test_a_short_block_set_larger_than_the_body_is_a_heading(parts) -> None:
    blocks = body(parts, parts.block(parts.run("Third Quarter Results", font_size=20)))
    assert typed(layout(blocks))[-1] == ("heading", "Third Quarter Results", None)


def test_a_block_partly_at_the_body_size_is_a_paragraph(parts) -> None:
    blocks = body(
        parts,
        parts.block(parts.run("Third Quarter", font_size=20), parts.run(" Results")),
    )
    assert typed(layout(blocks))[-1][0] == "paragraph"


def test_the_body_size_carries_the_most_visible_characters(parts) -> None:
    metadata = layout(
        [
            parts.block(parts.run("abcd", font_size=12)),
            parts.block(parts.run("abcd", font_size=14)),
            parts.block(
                parts.run("ab", font_size=20), parts.run("      ", font_size=30)
            ),
            parts.block(parts.run("hidden text here", font_size=40, visible=False)),
        ]
    )
    assert body_size(metadata) == 12


def test_tags_decide_headings_and_list_items(parts) -> None:
    blocks = body(
        parts,
        parts.block(parts.run("Results"), tag="h2", heading_level=2),
        parts.block(parts.run("Nested point"), tag="li", list_item=True, list_depth=2),
        parts.block(parts.run("Loose item"), tag="li", list_item=True, list_depth=0),
    )
    assert typed(layout(blocks))[1:] == [
        ("heading", "Results", 2),
        ("list_item", "Nested point", 2),
        ("list_item", "Loose item", None),
    ]


def test_the_walker_markers_type_page_numbers_bullets_and_footnotes(parts) -> None:
    blocks = body(
        parts,
        parts.block(parts.run("- 3 -")),
        parts.block(parts.run(f"{BULLET} Revenue grew")),
        parts.block(parts.run("l", symbol_font=True), parts.run(" Margins held")),
        parts.block(parts.run("(1) Excludes charges")),
        parts.block(parts.run("2", superscript=True), parts.run("Adjusted figure")),
    )
    assert [kind for kind, _, _ in typed(layout(blocks))[1:]] == [
        "other",
        "list_item",
        "list_item",
        "footnote",
        "footnote",
    ]


def test_hidden_runs_add_nothing_but_whitespace_always_separates(parts) -> None:
    blocks = body(
        parts,
        parts.block(
            parts.run("Visible"),
            parts.run(" secret", visible=False),
            parts.run(" text"),
        ),
        parts.block(
            parts.run("4,579;"),
            parts.run("\n    ", visible=False),
            parts.run("no shares"),
        ),
    )
    assert [text for _, text, _ in typed(layout(blocks))[1:]] == [
        "Visible text",
        "4,579; no shares",
    ]


def test_a_pre_block_splits_at_blank_lines_and_keeps_its_lines(parts) -> None:
    blocks = body(
        parts,
        parts.block(
            parts.run("Revenue     9.8\nCost        7.1\n\nNote text"), tag="pre"
        ),
    )
    produced = LayoutBlocks(layout(blocks)).blocks[1:]
    assert [(b.text, b.pre_lines) for b in produced] == [
        ("Revenue 9.8 Cost 7.1", ("Revenue     9.8", "Cost        7.1")),
        ("Note text", ("Note text",)),
    ]


def test_a_marker_table_makes_list_items_and_footnotes(parts) -> None:
    rows = [[BULLET, "First point"], ["(1)", "A note"]]
    metadata = layout(body(parts, *parts.cells(rows)), [parts.table([1, 1], [1, 1])])
    assert typed(metadata)[1:] == [
        ("list_item", "First point", None),
        ("footnote", "A note", None),
    ]


def test_a_data_table_is_one_block_with_header_rows(parts) -> None:
    rows = [["", "2026", "2025"], ["Revenue", "$9.8", "$9.1"], ["Cost", "7.1", "6.9"]]
    metadata = layout(
        body(parts, *parts.cells(rows)), [parts.table([1, 1, 1], [1, 1, 1], [1, 1, 1])]
    )
    (grid,) = LayoutBlocks(metadata).blocks[1:]
    assert grid.type == "table"
    assert [(c.text, c.row, c.column, c.is_header) for c in grid.cells] == [
        ("2026", 0, 1, True),
        ("2025", 0, 2, True),
        ("Revenue", 1, 0, False),
        ("$9.8", 1, 1, False),
        ("$9.1", 1, 2, False),
        ("Cost", 2, 0, False),
        ("7.1", 2, 1, False),
        ("6.9", 2, 2, False),
    ]


def test_thead_and_all_th_rows_are_header_rows(parts) -> None:
    rows = [["Metric", "Value"], ["Revenue", "9.8"], ["Cost", "7.1"]]
    metadata = layout(
        body(parts, *parts.cells(rows)), [parts.table([1, 1], [1, 1], [1, 1], head=3)]
    )
    (grid,) = LayoutBlocks(metadata).blocks[1:]
    assert all(c.is_header for c in grid.cells)


def test_a_spanning_prose_row_leaves_the_table(parts) -> None:
    rows = [
        ["Consolidated Statements of Income"],
        ["", "2026", "2025"],
        ["Revenue", "9.8", "9.1"],
        ["Amounts in millions, except where noted otherwise below."],
        ["Cost", "7.1", "6.9"],
    ]
    blocks = body(parts, *parts.cells(rows))
    blocks[1]["runs"][0]["bold"] = True
    metadata = layout(blocks, [parts.table([3], [1, 1, 1], [1, 1, 1], [3], [1, 1, 1])])
    produced = LayoutBlocks(metadata).blocks[1:]
    assert [(b.type, b.text) for b in produced if b.cells is None] == [
        ("heading", "Consolidated Statements of Income"),
        ("paragraph", "Amounts in millions, except where noted otherwise below."),
    ]
    assert [b.type for b in produced] == ["heading", "table", "paragraph", "table"]
    first, second = produced[1], produced[3]
    assert [(c.text, c.row) for c in first.cells] == [
        ("2026", 0),
        ("2025", 0),
        ("Revenue", 1),
        ("9.8", 1),
        ("9.1", 1),
    ]
    assert [(c.text, c.row) for c in second.cells] == [
        ("Cost", 0),
        ("7.1", 0),
        ("6.9", 0),
    ]


@pytest.mark.parametrize(
    ("row", "spans"),
    [(["Costs and expenses:", "", ""], [1, 1, 1]), (["12.5"], [3])],
)
def test_other_single_cell_rows_stay_in_the_table(
    row: list[str], spans: list[int], parts
) -> None:
    rows = [["", "2026", "2025"], ["Revenue", "9.8", "9.1"], row]
    metadata = layout(
        body(parts, *parts.cells(rows)), [parts.table([1, 1, 1], [1, 1, 1], spans)]
    )
    assert [b.type for b in LayoutBlocks(metadata).blocks[1:]] == ["table"]


def test_a_layout_table_is_walked_as_ordinary_blocks(parts) -> None:
    rows = [["Media contact", "Investor contact"]]
    metadata = layout(body(parts, *parts.cells(rows)), [parts.table([1, 1])])
    assert [text for _, text, _ in typed(metadata)[1:]] == [
        "Media contact",
        "Investor contact",
    ]


def test_a_nested_data_table_is_read_in_place(parts) -> None:
    outer = [parts.block(parts.run("Before"), tag="td", cell=(0, 0, 0))]
    inner = parts.cells([["", "2026"], ["Revenue", "9.8"]], table_index=1)
    after = [parts.block(parts.run("After"), tag="td", cell=(0, 0, 0))]
    metadata = layout(
        body(parts, *outer, *inner, *after),
        [parts.table([1]), parts.table([1, 1], [1, 1], parent=(0, 0, 0))],
    )
    assert [b.type for b in LayoutBlocks(metadata).blocks[1:]] == [
        "paragraph",
        "table",
        "paragraph",
    ]
