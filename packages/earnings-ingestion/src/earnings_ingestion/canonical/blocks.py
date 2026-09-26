"""The walker's elements after N1: the blocks compensation retypes and L1 lays out."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from earnings_ingestion.canonical.normalize import normalize
from earnings_ingestion.canonical.walker import Element, Row


@dataclass(frozen=True)
class GridCell:
    """A non-empty cell of a W14 grid, after N1 (Stage 3 spec: Tables and cells).

    ``row`` indexes the walker's emitted rows. ``column`` is found by occupancy: the
    first column no ``rowspan`` from an earlier row still covers. The spans are the
    walker's own ``rowspan`` and ``colspan``.
    """

    text: str
    row: int
    column: int
    row_span: int
    column_span: int
    is_header: bool


@dataclass(frozen=True)
class Block:
    """One walker element after N1.

    ``parent`` is the index, in the block list, of the enclosing W7 list container.
    ``pre_lines`` holds a W5 piece's lines as they were before W4 collapsed them.
    ``cells`` holds a W14 grid's non-empty cells in row-major order; L1 lays a table
    out from them, not from ``text``. ``retyped_by`` names the compensation rule that
    set ``type``, if any.
    """

    type: str
    text: str
    source_type: str
    container: bool = False
    parent: int | None = None
    level: int | None = None
    pre_lines: tuple[str, ...] | None = None
    cells: tuple[GridCell, ...] | None = None
    retyped_by: str | None = None


def grid_columns(rows: Sequence[Row]) -> list[list[int]]:
    """Each cell's first grid column, by occupancy, row by row.

    Occupancy is kept as column ranges per row, so no ``colspan`` or ``rowspan`` value
    costs memory in proportion to its size; a ``rowspan`` past the last row is clipped.
    """
    claimed: list[list[tuple[int, int]]] = [[] for _ in rows]
    columns: list[list[int]] = []
    for index, row in enumerate(rows):
        column, starts = 0, []
        for cell in row.cells:
            column = _first_free(claimed[index], column)
            starts.append(column)
            for below in range(index + 1, min(index + cell.rowspan, len(rows))):
                claimed[below].append((column, column + cell.colspan))
            column += cell.colspan
        columns.append(starts)
    return columns


def _first_free(claimed: Sequence[tuple[int, int]], column: int) -> int:
    moved = True
    while moved:
        moved = False
        for start, end in claimed:
            if start <= column < end:
                column, moved = end, True
    return column


def to_blocks(
    elements: Sequence[Element], pre_lines: Mapping[int, tuple[str, ...]]
) -> list[Block]:
    """N1 over every block and cell text; a unit left empty is dropped (N1 step 4).

    W7's list containers carry no text and are kept here; L1 drops a container none of
    whose items has text.
    """
    blocks: list[Block] = []
    moved: dict[int, int] = {}  # walker index -> block index
    for index, element in enumerate(elements):
        container = element.type == "other" and not element.text
        cells = None if element.rows is None else _cells(element.rows)
        text = normalize(element.text)
        if not container and not (text if cells is None else cells):
            continue
        moved[index] = len(blocks)
        blocks.append(
            Block(
                type=element.type,
                text=text,
                source_type=element.source_type,
                container=container,
                parent=None if element.parent is None else moved[element.parent],
                level=element.level,
                pre_lines=pre_lines.get(index),
                cells=cells,
            )
        )
    return blocks


def _cells(rows: Sequence[Row]) -> tuple[GridCell, ...]:
    return tuple(
        GridCell(text, index, column, cell.rowspan, cell.colspan, row.header)
        for index, (row, starts) in enumerate(
            zip(rows, grid_columns(rows), strict=True)
        )
        for cell, column in zip(row.cells, starts, strict=True)
        if (text := normalize(cell.text))
    )
