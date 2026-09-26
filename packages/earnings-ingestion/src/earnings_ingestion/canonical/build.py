"""Layout L1: the canonical text, and a span for every block, table, and cell.

Blocks appear in the walker's order, one per line. A table is its rows, one per line,
each row its non-empty cells separated by one tab. Separators belong to no leaf
element. A list container spans its items and contributes no text; a container with
no item text is dropped, and a nested container that spans exactly what its parent
spans is merged into the parent, since the two would share one derived ID.
"""

from collections.abc import Sequence

from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    TableCellContext,
    TextSpan,
)

from earnings_ingestion.canonical.blocks import Block, GridCell


class _Text:
    """Canonical text under construction, with the span of each unit appended."""

    def __init__(self) -> None:
        self.pieces: list[str] = []
        self.length = 0

    def append(self, unit: str, separator: str) -> TextSpan:
        if self.length:
            self.pieces.append(separator)
            self.length += len(separator)
        start = self.length
        self.pieces.append(unit)
        self.length += len(unit)
        return TextSpan(start=start, end=self.length)


def build(
    blocks: Sequence[Block], *, source_document_id: str, canonicalization_version: str
) -> tuple[CanonicalDocument, list[DocumentElement]]:
    """The document and its block, table, and cell elements, in document order.

    Each table is followed by its cells in row-major order. ``DocumentElement``
    construction refuses an inconsistent element, and that error is raised: it is a
    canonicalizer defect, never a property of the input.
    """
    text = _Text()
    spans: dict[int, TextSpan] = {}
    cell_spans: dict[int, list[TextSpan]] = {}
    for index, block in enumerate(blocks):
        if block.container:
            continue
        if block.cells is None:
            spans[index] = text.append(block.text, "\n")
        else:
            cell_spans[index] = _lay_out_table(text, block.cells)
            spans[index] = TextSpan(
                start=cell_spans[index][0].start, end=cell_spans[index][-1].end
            )
    _span_containers(blocks, spans)
    merged = _merged_containers(blocks, spans)

    document = CanonicalDocument.create(
        source_document_id=source_document_id,
        canonicalization_version=canonicalization_version,
        canonical_text="".join(text.pieces),
    )
    ids: dict[int, str] = {}
    elements: list[DocumentElement] = []
    for index, block in enumerate(blocks):
        if index not in spans or index in merged:
            continue
        parent = (
            None if block.parent is None else merged.get(block.parent, block.parent)
        )
        element = DocumentElement.create(
            document,
            ElementType(block.type),
            spans[index],
            parent_id=None if parent is None else ids[parent],
            level=block.level,
            source_type=block.source_type,
        )
        ids[index] = element.element_id
        elements.append(element)
        if block.cells is not None:
            elements.extend(
                _cell_elements(document, element, block.cells, cell_spans[index])
            )
    return document, elements


def _lay_out_table(text: _Text, cells: Sequence[GridCell]) -> list[TextSpan]:
    spans: list[TextSpan] = []
    row: int | None = None
    for cell in cells:
        spans.append(text.append(cell.text, "\t" if cell.row == row else "\n"))
        row = cell.row
    return spans


def _span_containers(blocks: Sequence[Block], spans: dict[int, TextSpan]) -> None:
    """A container spans its first item's start to its last item's end.

    A nested container follows its parent in the walker's order, so walking backwards
    spans every nested container before the container that holds it.
    """
    children: dict[int, list[int]] = {}
    for index, block in enumerate(blocks):
        if block.parent is not None:
            children.setdefault(block.parent, []).append(index)
    for index in reversed(range(len(blocks))):
        if not blocks[index].container:
            continue
        held = [spans[child] for child in children.get(index, []) if child in spans]
        if held:
            spans[index] = TextSpan(
                start=min(span.start for span in held),
                end=max(span.end for span in held),
            )


def _merged_containers(
    blocks: Sequence[Block], spans: dict[int, TextSpan]
) -> dict[int, int]:
    """Each container merged into the container that holds it, by index."""
    merged: dict[int, int] = {}
    for index, block in enumerate(blocks):
        if not block.container or index not in spans or block.parent is None:
            continue
        parent = merged.get(block.parent, block.parent)
        if spans[parent] == spans[index]:
            merged[index] = parent
    return merged


def _cell_elements(
    document: CanonicalDocument,
    table: DocumentElement,
    cells: Sequence[GridCell],
    spans: Sequence[TextSpan],
) -> list[DocumentElement]:
    """A table's cells; a non-header cell lists the header cells above it that overlap
    its columns, in row order."""
    headers: list[tuple[GridCell, str]] = []
    elements: list[DocumentElement] = []
    for cell, span in zip(cells, spans, strict=True):
        labels = ()
        if not cell.is_header:
            labels = tuple(
                element_id
                for header, element_id in headers
                if header.row < cell.row
                and header.column < cell.column + cell.column_span
                and cell.column < header.column + header.column_span
            )
        element = DocumentElement.create(
            document,
            ElementType.TABLE_CELL,
            span,
            parent_id=table.element_id,
            table_cell=TableCellContext(
                row=cell.row,
                column=cell.column,
                row_span=cell.row_span,
                column_span=cell.column_span,
                is_header=cell.is_header,
                header_cell_ids=labels,
            ),
            source_type="cell",
        )
        if cell.is_header:
            headers.append((cell, element.element_id))
        elements.append(element)
    return elements
