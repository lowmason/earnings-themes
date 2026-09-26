"""``LayoutExtractor``: layout-1's element stream over walker-1's canonical text (B5).

``extract(capture)`` works offline from the capture's saved layout metadata and
returns layout-1's blocks, after C1-C5. ``map_onto(capture, document)`` places them
on one canonical document under ``anchored-1`` and returns the elements with every
alignment failure. Canonical text that no element covers becomes ``other``, one
element per line (the spec's "text with no visible counterpart"). layout-1 emits no
sentences and no list containers: nothing downstream of the comparison reads them.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    TableCellContext,
    TextSpan,
    validate_elements,
)

from earnings_ingestion.browser.records import CaptureStatus, RenderedCapture
from earnings_ingestion.canonical.blocks import Block
from earnings_ingestion.canonical.compensate import compensate
from earnings_ingestion.layout.align import MAPPING_POLICY, CollapsedText, align
from earnings_ingestion.layout.blocks import LAYOUT_VERSION, SOURCE, LayoutBlocks
from earnings_ingestion.layout.records import AlignmentFailure, LayoutExtraction

USABLE = frozenset({CaptureStatus.COMPLETED, CaptureStatus.PARTIAL})


class LayoutExtractor:
    """layout-1 (B5): candidate elements from a capture's layout metadata."""

    version = LAYOUT_VERSION
    mapping_policy = MAPPING_POLICY

    def extract(self, capture: RenderedCapture) -> tuple[list[Block], dict[str, int]]:
        """layout-1's blocks after C1-C5, and C1-C5's retype counts.

        A failed or unavailable capture has no layout to read: ``ValueError``.
        """
        if capture.status not in USABLE:
            raise ValueError(f"capture {capture.capture_id} is {capture.status.value}")
        return compensate(LayoutBlocks(capture.layout).blocks)

    def map_onto(
        self, capture: RenderedCapture, document: CanonicalDocument
    ) -> LayoutExtraction:
        """The capture's blocks placed on ``document``, with every alignment failure."""
        blocks, retypes = self.extract(capture)
        return place(capture, document, blocks, retypes)


@dataclass(frozen=True)
class _Unit:
    block: int
    cell: int | None
    text: str


def place(
    capture: RenderedCapture,
    document: CanonicalDocument,
    blocks: Sequence[Block],
    retypes: dict[str, int],
) -> LayoutExtraction:
    units = [
        _Unit(index, None, block.text)
        if block.cells is None
        else _Unit(index, position, cell.text)
        for index, block in enumerate(blocks)
        for position, cell in (
            [(None, None)] if block.cells is None else enumerate(block.cells)
        )
    ]
    collapsed = CollapsedText.of(document.canonical_text)
    placements = align(collapsed, [unit.text for unit in units])
    failures: list[AlignmentFailure] = []
    spans: dict[tuple[int, int | None], TextSpan] = {}
    for unit, placement in zip(units, placements, strict=True):
        if placement.start is None:
            failures.append(
                AlignmentFailure(
                    reason=placement.reason,
                    unit_type="table_cell"
                    if unit.cell is not None
                    else blocks[unit.block].type,
                    text=unit.text,
                    detail=placement.detail,
                )
            )
        else:
            spans[unit.block, unit.cell] = collapsed.span(
                placement.start, placement.start + len(unit.text)
            )
    elements: list[DocumentElement] = []
    for index, block in enumerate(blocks):
        if block.cells is None:
            if (index, None) in spans:
                elements.append(
                    DocumentElement.create(
                        document,
                        ElementType(block.type),
                        spans[index, None],
                        level=block.level,
                        source_type=block.source_type,
                    )
                )
        else:
            elements.extend(_table(document, block, index, spans))
    elements = _with_uncovered(document, elements)
    rejections = validate_elements(document, elements)
    if rejections:
        raise AssertionError(f"layout-1 built an invalid element set: {rejections}")
    return LayoutExtraction(
        layout_version=LAYOUT_VERSION,
        mapping_policy=MAPPING_POLICY,
        capture_id=capture.capture_id,
        doc_id=document.doc_id,
        units=len(units),
        retypes=retypes,
        elements=tuple(elements),
        failures=tuple(failures),
    )


def _table(
    document: CanonicalDocument,
    block: Block,
    index: int,
    spans: dict[tuple[int, int | None], TextSpan],
) -> list[DocumentElement]:
    placed = [
        (cell, spans[index, position])
        for position, cell in enumerate(block.cells)
        if (index, position) in spans
    ]
    if not placed:
        return []
    table = DocumentElement.create(
        document,
        ElementType.TABLE,
        TextSpan(start=placed[0][1].start, end=placed[-1][1].end),
        source_type=block.source_type,
    )
    out = [table]
    headers: list[tuple[int, int, int, str]] = []  # row, first column, end column, id
    for cell, span in placed:
        references = (
            ()
            if cell.is_header
            else tuple(
                element_id
                for row, start, end, element_id in headers
                if row < cell.row
                and start < cell.column + cell.column_span
                and end > cell.column
            )
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
                header_cell_ids=references,
            ),
            source_type=f"{SOURCE}:cell",
        )
        if cell.is_header:
            headers.append(
                (
                    cell.row,
                    cell.column,
                    cell.column + cell.column_span,
                    element.element_id,
                )
            )
        out.append(element)
    return out


def _with_uncovered(
    document: CanonicalDocument, elements: Sequence[DocumentElement]
) -> list[DocumentElement]:
    """Every element, plus one ``other`` per line of canonical text none covers."""
    text = document.canonical_text
    tops = sorted(
        (e for e in elements if e.parent_id is None), key=lambda e: e.span.start
    )
    gaps: list[tuple[int, int]] = []
    cursor = 0
    for element in tops:
        if element.span.start > cursor:
            gaps.append((cursor, element.span.start))
        cursor = max(cursor, element.span.end)
    if cursor < len(text):
        gaps.append((cursor, len(text)))
    others: list[DocumentElement] = []
    for low, high in gaps:
        line_start = low
        for position in range(low, high + 1):
            if position == high or text[position] == "\n":
                start, end = line_start, position
                while start < end and text[start].isspace():
                    start += 1
                while end > start and text[end - 1].isspace():
                    end -= 1
                if start < end:
                    others.append(
                        DocumentElement.create(
                            document,
                            ElementType.OTHER,
                            TextSpan(start=start, end=end),
                            source_type=f"{SOURCE}:uncovered",
                        )
                    )
                line_start = position + 1
    order = {id(e): n for n, e in enumerate(elements)}
    merged = sorted(
        [*elements, *others],
        key=lambda e: (e.span.start, -e.span.end, order.get(id(e), -1)),
    )
    return _parents_first(merged)


def _parents_first(elements: list[DocumentElement]) -> list[DocumentElement]:
    """Document order with each table directly before its cells."""
    cells: dict[str, list[DocumentElement]] = {}
    for element in elements:
        if element.parent_id is not None:
            cells.setdefault(element.parent_id, []).append(element)
    out: list[DocumentElement] = []
    for element in elements:
        if element.parent_id is None:
            out.append(element)
            out.extend(cells.get(element.element_id, []))
    return out
