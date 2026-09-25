"""DocumentElement: a typed structural unit with a stable ID and a code-point span."""

from enum import StrEnum
from typing import Self

from pydantic import NonNegativeInt, PositiveInt, model_validator

from earnings_core._model import ContractModel, VersionedRecord
from earnings_core.documents import CanonicalDocument
from earnings_core.spans import TextSpan


class ElementType(StrEnum):
    """R4.1's structural units, plus the types Stage 1's gold and parsers use.

    ``page_artifact`` and the six block types come from the Stage 1 gold
    (docs/verification/V2-parser-fidelity.md, "Element types and nesting observed in
    the gold"); ``other`` is the parsers' catch-all. Adding a type is a schema change.
    """

    SECTION = "section"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    SENTENCE = "sentence"
    FOOTNOTE = "footnote"
    TABLE = "table"
    TABLE_CELL = "table_cell"
    SPEAKER_TURN = "speaker_turn"
    PAGE_ARTIFACT = "page_artifact"
    OTHER = "other"


LEVELED_TYPES = frozenset(
    {ElementType.SECTION, ElementType.HEADING, ElementType.LIST_ITEM}
)
"""Types that may carry a level: an outline depth, or a list's nesting depth."""


class TableCellContext(ContractModel):
    """A cell's grid position and the header cells that label it (R4.1, R4.2).

    ``row`` and ``column`` count every cell of the table's grid, empty ones included,
    although an empty cell is never an element: every element span holds text.
    """

    row: NonNegativeInt
    column: NonNegativeInt
    row_span: PositiveInt = 1
    column_span: PositiveInt = 1
    is_header: bool
    header_cell_ids: tuple[str, ...] = ()


def derive_element_id(element_type: ElementType, span: TextSpan) -> str:
    """An element's ID: its type and span, e.g. ``paragraph-120-450``.

    Plan decision, 2026-09-25: derived, so two parsers that agree on an element's type
    and span give it the same ID. The ID is unique within one document version; the
    pair ``(doc_id, element_id)`` is unique across versions.
    """
    return f"{element_type.value}-{span.start}-{span.end}"


class DocumentElement(VersionedRecord):
    """One structural unit of one canonical document version (R4.1).

    ``source_type`` records the producing parser's own name for the unit, so each
    producer can publish its type mapping, as Stage 1's dumps did.
    """

    element_id: str
    doc_id: str
    type: ElementType
    span: TextSpan
    parent_id: str | None = None
    level: PositiveInt | None = None
    table_cell: TableCellContext | None = None
    source_type: str = ""

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        expected = derive_element_id(self.type, self.span)
        if self.element_id != expected:
            raise ValueError(
                f"element_id {self.element_id!r} is not the derived {expected!r}"
            )
        if self.parent_id == self.element_id:
            raise ValueError(f"element {self.element_id} is its own parent")
        if self.level is not None and self.type not in LEVELED_TYPES:
            raise ValueError(f"a {self.type.value} element carries no level")
        if (self.type is ElementType.TABLE_CELL) != (self.table_cell is not None):
            raise ValueError(
                "table_cell context is required on table cells and forbidden elsewhere"
            )
        return self

    @classmethod
    def create(
        cls,
        document: CanonicalDocument,
        element_type: ElementType,
        span: TextSpan,
        *,
        parent_id: str | None = None,
        level: int | None = None,
        table_cell: TableCellContext | None = None,
        source_type: str = "",
    ) -> Self:
        """An element of ``document``, with its ID derived from type and span."""
        return cls(
            element_id=derive_element_id(element_type, span),
            doc_id=document.doc_id,
            type=element_type,
            span=span,
            parent_id=parent_id,
            level=level,
            table_cell=table_cell,
            source_type=source_type,
        )
