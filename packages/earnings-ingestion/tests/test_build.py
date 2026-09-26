"""Layout L1: canonical text, spans, tables and cells, and list containers."""

from earnings_core import ElementType, validate_elements
from earnings_ingestion.canonical.blocks import Block, GridCell
from earnings_ingestion.canonical.build import build


def built(blocks: list[Block]):
    return build(blocks, source_document_id="doc-1", canonicalization_version="test-1")


def paragraph(text: str) -> Block:
    return Block(type="paragraph", text=text, source_type="p")


def container(parent: int | None = None) -> Block:
    return Block(type="other", text="", source_type="ul", container=True, parent=parent)


def item(text: str, parent: int, level: int = 1) -> Block:
    return Block(
        type="list_item", text=text, source_type="li", parent=parent, level=level
    )


def summary(document, elements) -> list[tuple]:
    text = document.canonical_text
    return [
        (
            element.type.value,
            element.span.slice_of(text),
            element.parent_id,
            element.level,
        )
        for element in elements
    ]


def test_blocks_are_one_per_line_with_no_edge_separators() -> None:
    document, elements = built(
        [
            Block(type="heading", text="Outlook", source_type="h2", level=2),
            paragraph("Revenue rose."),
        ]
    )
    assert document.canonical_text == "Outlook\nRevenue rose."
    assert document.canonicalization_version == "test-1"
    assert summary(document, elements) == [
        ("heading", "Outlook", None, 2),
        ("paragraph", "Revenue rose.", None, None),
    ]
    assert validate_elements(document, elements) == ()


def test_a_table_is_rows_of_tab_separated_non_empty_cells() -> None:
    cells = (
        GridCell("Item", 0, 0, 1, 1, True),
        GridCell("2024", 0, 2, 1, 1, True),
        GridCell("Net sales", 1, 0, 1, 1, False),
        GridCell("1,234", 1, 2, 1, 1, False),
    )
    table = Block(type="table", text="unused", source_type="table", cells=cells)
    document, elements = built([paragraph("Results"), table, paragraph("After.")])
    assert document.canonical_text == "Results\nItem\t2024\nNet sales\t1,234\nAfter."
    assert [element.type for element in elements] == [
        ElementType.PARAGRAPH,
        ElementType.TABLE,
        ElementType.TABLE_CELL,
        ElementType.TABLE_CELL,
        ElementType.TABLE_CELL,
        ElementType.TABLE_CELL,
        ElementType.PARAGRAPH,
    ]
    table_element = elements[1]
    assert table_element.span.slice_of(document.canonical_text) == (
        "Item\t2024\nNet sales\t1,234"
    )
    assert validate_elements(document, elements) == ()


def test_cells_carry_their_grid_position_and_column_headers() -> None:
    cells = (
        GridCell("Item", 0, 0, 1, 1, True),
        GridCell("Year", 0, 1, 1, 2, True),
        GridCell("2024", 1, 1, 1, 1, True),
        GridCell("2023", 1, 2, 1, 1, True),
        GridCell("Net sales", 2, 0, 1, 1, False),
        GridCell("1,234", 2, 1, 1, 1, False),
        GridCell("1,100", 2, 2, 1, 1, False),
    )
    table = Block(type="table", text="unused", source_type="table", cells=cells)
    document, elements = built([table])
    by_text = {
        element.span.slice_of(document.canonical_text): element
        for element in elements[1:]
    }
    item, year, current, prior = (
        by_text["Item"],
        by_text["Year"],
        by_text["2024"],
        by_text["2023"],
    )
    assert by_text["Net sales"].table_cell.header_cell_ids == (item.element_id,)
    assert by_text["1,234"].table_cell.header_cell_ids == (
        year.element_id,
        current.element_id,
    )
    assert by_text["1,100"].table_cell.header_cell_ids == (
        year.element_id,
        prior.element_id,
    )
    assert year.table_cell.header_cell_ids == ()
    assert (year.table_cell.column, year.table_cell.column_span) == (1, 2)
    assert {element.source_type for element in elements[1:]} == {"cell"}
    assert validate_elements(document, elements) == ()


def test_a_list_container_spans_its_items_and_adds_no_text() -> None:
    document, elements = built(
        [paragraph("Intro."), container(), item("One", 1), item("Two", 1)]
    )
    assert document.canonical_text == "Intro.\nOne\nTwo"
    container_id = elements[1].element_id
    assert summary(document, elements) == [
        ("paragraph", "Intro.", None, None),
        ("other", "One\nTwo", None, None),
        ("list_item", "One", container_id, 1),
        ("list_item", "Two", container_id, 1),
    ]
    assert validate_elements(document, elements) == ()


def test_a_container_without_item_text_is_dropped() -> None:
    document, elements = built([paragraph("Intro."), container(), container(1)])
    assert summary(document, elements) == [("paragraph", "Intro.", None, None)]


def test_nested_lists_nest_their_containers() -> None:
    blocks = [
        container(),
        item("One", 0),
        container(0),
        item("Nested", 2, level=2),
        item("Two", 0),
    ]
    document, elements = built(blocks)
    outer, _one, inner, nested, two = elements
    assert (inner.parent_id, nested.parent_id, two.parent_id) == (
        outer.element_id,
        inner.element_id,
        outer.element_id,
    )
    assert inner.span.slice_of(document.canonical_text) == "Nested"
    assert validate_elements(document, elements) == ()


def test_a_container_spanning_exactly_its_parent_is_merged_into_it() -> None:
    blocks = [container(), container(0), item("Only", 1, level=2)]
    document, elements = built(blocks)
    outer, only = elements
    assert (outer.type, only.parent_id, only.level) == (
        ElementType.OTHER,
        outer.element_id,
        2,
    )
    assert validate_elements(document, elements) == ()


def test_a_retyped_item_keeps_its_container() -> None:
    artifact = Block(
        type="page_artifact", text="Repeat", source_type="li", parent=0, retyped_by="C5"
    )
    document, elements = built([container(), artifact, item("Real", 0)])
    assert summary(document, elements)[1] == (
        "page_artifact",
        "Repeat",
        elements[0].element_id,
        None,
    )
    assert validate_elements(document, elements) == ()
