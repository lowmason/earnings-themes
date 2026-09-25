import pytest
from earnings_core.documents import CanonicalDocument
from earnings_core.elements import (
    DocumentElement,
    ElementType,
    TableCellContext,
    derive_element_id,
)
from earnings_core.spans import TextSpan
from pydantic import ValidationError

DOCUMENT = CanonicalDocument.create(
    source_document_id="elements-test",
    canonicalization_version="test-1",
    canonical_text="Results\nRevenue rose.\nMetric\tQ3",
)
HEADING = TextSpan(start=0, end=7)
CELL = TextSpan(start=22, end=28)


def test_the_id_is_derived_from_type_and_span() -> None:
    element = DocumentElement.create(DOCUMENT, ElementType.HEADING, HEADING, level=1)
    assert element.element_id == "heading-0-7"
    assert element.element_id == derive_element_id(ElementType.HEADING, HEADING)
    assert element.doc_id == DOCUMENT.doc_id


def test_the_same_type_and_span_give_the_same_id_from_any_producer() -> None:
    first = DocumentElement.create(
        DOCUMENT, ElementType.HEADING, HEADING, source_type="lxml:h1"
    )
    second = DocumentElement.create(
        DOCUMENT, ElementType.HEADING, HEADING, source_type="html.parser:h1"
    )
    assert first.element_id == second.element_id
    assert first.source_type != second.source_type


def test_an_id_that_is_not_derived_is_refused() -> None:
    with pytest.raises(ValidationError, match="is not the derived"):
        DocumentElement(
            element_id="h1",
            doc_id=DOCUMENT.doc_id,
            type=ElementType.HEADING,
            span=HEADING,
        )


@pytest.mark.parametrize(
    "element_type", [ElementType.PARAGRAPH, ElementType.TABLE, ElementType.FOOTNOTE]
)
def test_only_sections_headings_and_list_items_carry_a_level(
    element_type: ElementType,
) -> None:
    with pytest.raises(ValidationError, match="carries no level"):
        DocumentElement.create(DOCUMENT, element_type, HEADING, level=1)


def test_a_heading_may_have_no_level() -> None:
    element = DocumentElement.create(DOCUMENT, ElementType.HEADING, HEADING)
    assert element.level is None


def test_a_table_cell_requires_its_context() -> None:
    with pytest.raises(ValidationError, match="required on table cells"):
        DocumentElement.create(DOCUMENT, ElementType.TABLE_CELL, CELL)


def test_only_a_table_cell_takes_table_context() -> None:
    context = TableCellContext(row=0, column=0, is_header=True)
    with pytest.raises(ValidationError, match="forbidden elsewhere"):
        DocumentElement.create(
            DOCUMENT, ElementType.PARAGRAPH, CELL, table_cell=context
        )


def test_a_table_cell_records_its_grid_position_and_headers() -> None:
    context = TableCellContext(
        row=1, column=2, is_header=False, header_cell_ids=("table_cell-22-28",)
    )
    cell = DocumentElement.create(
        DOCUMENT, ElementType.TABLE_CELL, TextSpan(start=29, end=31), table_cell=context
    )
    assert cell.table_cell == context
    assert (context.row_span, context.column_span) == (1, 1)


@pytest.mark.parametrize(
    "changes",
    [{"row": -1}, {"column_span": 0}, {"is_header": 1}, {"header_cell_ids": ["x"]}],
    ids=["negative-row", "zero-span", "int-flag", "list-not-tuple"],
)
def test_table_context_is_strictly_typed(changes: dict[str, object]) -> None:
    fields: dict[str, object] = {"row": 0, "column": 0, "is_header": False}
    fields.update(changes)
    with pytest.raises(ValidationError):
        TableCellContext(**fields)


def test_an_element_is_not_its_own_parent() -> None:
    with pytest.raises(ValidationError, match="its own parent"):
        DocumentElement.create(
            DOCUMENT, ElementType.HEADING, HEADING, parent_id="heading-0-7"
        )


def test_an_element_round_trips_through_json() -> None:
    context = TableCellContext(row=0, column=0, is_header=True)
    cell = DocumentElement.create(
        DOCUMENT,
        ElementType.TABLE_CELL,
        CELL,
        parent_id="table-22-31",
        table_cell=context,
        source_type="lxml:th",
    )
    assert DocumentElement.model_validate_json(cell.model_dump_json()) == cell
