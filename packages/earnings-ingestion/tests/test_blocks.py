"""The walker's elements after N1: dropped units, containers, and grid positions."""

from earnings_ingestion.canonical.blocks import Block, GridCell, grid_columns, to_blocks
from earnings_ingestion.canonical.walker import Cell, Element, Row, walk

SOFT_HYPHEN = chr(0x00AD)


def blocks_of(body: str) -> list[Block]:
    return to_blocks(*walk(f"<html><body>{body}</body></html>"))


def test_blocks_keep_the_walkers_type_source_and_level() -> None:
    assert blocks_of("<h2>Outlook</h2><p>Revenue  rose.</p>") == [
        Block(type="heading", text="Outlook", source_type="h2", level=2),
        Block(type="paragraph", text="Revenue rose.", source_type="p"),
    ]


def test_a_block_left_empty_by_n1_is_dropped() -> None:
    assert blocks_of(f"<p>{SOFT_HYPHEN}</p><p>Kept.</p>") == [
        Block(type="paragraph", text="Kept.", source_type="p")
    ]


def test_list_containers_are_kept_and_parents_follow_dropped_blocks() -> None:
    blocks = blocks_of(f"<p>{SOFT_HYPHEN}</p><ul><li>One</li><li>Two</li></ul>")
    assert [(b.type, b.text, b.container, b.parent, b.level) for b in blocks] == [
        ("other", "", True, None, None),
        ("list_item", "One", False, 0, 1),
        ("list_item", "Two", False, 0, 1),
    ]


def test_a_bare_page_number_is_other_but_not_a_container() -> None:
    [block] = blocks_of("<p>- 12 -</p>")
    assert (block.type, block.text, block.container) == ("other", "- 12 -", False)


def test_pre_pieces_carry_their_original_lines() -> None:
    [block] = blocks_of("<pre>Net sales    1,234\n  Cost    (56)</pre>")
    assert block.pre_lines == ("Net sales    1,234", "  Cost    (56)")
    assert block.text == "Net sales 1,234 Cost (56)"


def test_grid_cells_are_the_non_empty_cells_after_n1() -> None:
    [table] = blocks_of(
        "<table><tr><th>Item</th><th></th><th>2024</th></tr>"
        f"<tr><td>Net sales</td><td>{SOFT_HYPHEN}</td><td>1,234</td></tr></table>"
    )
    assert table.cells == (
        GridCell("Item", 0, 0, 1, 1, True),
        GridCell("2024", 0, 2, 1, 1, True),
        GridCell("Net sales", 1, 0, 1, 1, False),
        GridCell("1,234", 1, 2, 1, 1, False),
    )


def test_a_grid_left_without_text_is_dropped() -> None:
    rows = (
        Row(False, (Cell(SOFT_HYPHEN), Cell(SOFT_HYPHEN))),
        Row(False, (Cell(SOFT_HYPHEN), Cell(SOFT_HYPHEN))),
    )
    table = Element("table", SOFT_HYPHEN, None, None, "table", rows)
    assert to_blocks([table], {}) == []


def test_rowspans_push_later_cells_right() -> None:
    rows = (
        Row(True, (Cell("A", rowspan=2), Cell("B", colspan=2))),
        Row(False, (Cell("C"), Cell("D"))),
        Row(False, (Cell("E", colspan=3),)),
    )
    assert grid_columns(rows) == [[0, 1], [1, 2], [0]]


def test_huge_spans_cost_nothing() -> None:
    rows = (
        Row(False, (Cell("A", colspan=10**9, rowspan=10**9), Cell("B"))),
        Row(False, (Cell("C"),)),
    )
    assert grid_columns(rows) == [[0, 10**9], [10**9]]
