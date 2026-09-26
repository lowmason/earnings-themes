"""layout-1's blocks: the walker's rules read from the rendering (Stage 3, plan B).

Each L-rule is the walker rule of the same number with a rendered signal in place of
a tag or an inline style (plan 5, PB-9):

- **L1.** Hidden content is what the capture did not render: computed
  ``display: none``, ``noscript``, and runs whose computed visibility is not
  ``visible``.
- **L2, L3.** A block is what the capture recorded as one: the runs one element with a
  block display holds directly. Two or more ``<br>`` in a row, with only whitespace
  between them, end it.
- **L5.** A ``<pre>`` block splits at blank lines; each piece keeps its lines for C1.
- **L6, L7.** A heading or list item by its nearest ``h1``-``h6`` or ``li``, as the
  capture recorded; a list item's level is its list depth.
- **L8-L12.** The walker's ``classify``, over runs styled by computed weight,
  decoration, vertical alignment, and font family. W11 gains one clause: a block of at
  most 12 words whose every visible character is larger than the body size is a
  heading.
- **L13-L16.** The walker's marker-table, data-table, header-row, and layout-table
  tests, over each rendered table's own rows and cells, with their texts built as the
  walker builds them.
- **L17.** In a data table, a row whose only non-empty cell spans every column and
  holds a letter leaves the table: it is a block typed by L8-L12, and the table
  splits around it.

The blocks are the walker's ``Block`` records, so C1-C5 apply to them unchanged.
"""

import re
from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field

from earnings_ingestion.browser.records import (
    LayoutBlock,
    LayoutMetadata,
    LayoutRun,
    LayoutTable,
)
from earnings_ingestion.canonical.blocks import Block, GridCell, grid_columns
from earnings_ingestion.canonical.dom import primary_space
from earnings_ingestion.canonical.normalize import normalize
from earnings_ingestion.canonical.walker import (
    _FOOTNOTE_CELL,
    _LIST_CELL,
    _NUMERIC_CELL,
    _YEAR,
    MAX_HEADING_WORDS,
    MAX_MARKER_CHARS,
    Cell,
    Row,
    Run,
    Style,
    classify,
    collapse,
)

LAYOUT_VERSION = "layout-1"
SOURCE = "layout"
"""The prefix of every layout-1 ``source_type``: ``layout:<tag>``."""

_BLANK_LINE = re.compile(r"\n[ \t\r\f\v]*\n")


def body_size(layout: LayoutMetadata) -> float | None:
    """The font size that carries the most visible non-whitespace characters.

    A tie goes to the smaller size; ``None`` when nothing visible has text.
    """
    counts: Counter[float] = Counter()
    for block in layout.blocks:
        for run in block.runs:
            if run.visible and not run.br:
                counts[run.font_size] += sum(not char.isspace() for char in run.text)
    counts = Counter({size: count for size, count in counts.items() if count})
    if not counts:
        return None
    return min(counts, key=lambda size: (-counts[size], size))


def counts(run: LayoutRun) -> bool:
    """L1: a run's text counts when it rendered. Whitespace always counts: it
    separates words whether or not it drew a box, as the walker's text keeps it."""
    return run.visible or (not run.br and not run.text.strip())


def _style(run: LayoutRun) -> Style:
    return Style(
        bold=run.bold,
        underline=run.underline,
        sup=run.superscript,
        symbol_font=run.symbol_font,
    )


def _walker_runs(runs: Sequence[LayoutRun]) -> list[Run]:
    """Visible runs as the walker's runs; a ``<br>`` is a newline (W3)."""
    return [
        Run("\n" if run.br else run.text, _style(run)) for run in runs if counts(run)
    ]


def split_breaks(runs: Sequence[LayoutRun]) -> list[list[LayoutRun]]:
    """L3: two or more ``<br>`` in a row, with only whitespace between, end a block."""
    pieces: list[list[LayoutRun]] = []
    segment: list[LayoutRun] = []
    breaks = 0
    for run in runs:
        if run.br and run.visible:
            breaks += 1
            if breaks >= 2:
                pieces.append(segment)
                segment = []
                continue
        elif run.visible and run.text.strip():
            breaks = 0
        segment.append(run)
    pieces.append(segment)
    return pieces


def split_pre(runs: Sequence[LayoutRun]) -> list[list[LayoutRun]]:
    """L5: a ``<pre>`` block's visible runs, split at blank lines."""
    visible = [run for run in runs if counts(run)]
    text = "".join(run.text for run in visible)
    gaps = [(gap.start(), gap.end()) for gap in _BLANK_LINE.finditer(text)]
    starts = [0] + [end for _, end in gaps]
    ends = [start for start, _ in gaps] + [len(text)]
    pieces = []
    for start, end in zip(starts, ends, strict=True):
        piece, offset = [], 0
        for run in visible:
            low, high = max(start, offset), min(end, offset + len(run.text))
            if low < high:
                piece.append(
                    run.model_copy(
                        update={"text": run.text[low - offset : high - offset]}
                    )
                )
            offset += len(run.text)
        pieces.append(piece)
    return pieces


def type_block(
    runs: Sequence[LayoutRun], text: str, block: LayoutBlock, body: float | None
) -> tuple[str, int | None]:
    """L6-L12: the type and level of one block's text."""
    if block.heading_level is not None:
        return "heading", block.heading_level
    if block.list_item:
        return "list_item", block.list_depth or None
    kind = classify(_walker_runs(runs), text)
    if (
        kind == "paragraph"
        and larger(runs, body)
        and len(text.split()) <= MAX_HEADING_WORDS
    ):
        return "heading", None
    return kind, None


def larger(runs: Sequence[LayoutRun], body: float | None) -> bool:
    """Every visible non-whitespace character is set larger than the body size."""
    sizes = [
        run.font_size for run in runs if run.visible and not run.br and run.text.strip()
    ]
    return body is not None and bool(sizes) and all(size > body for size in sizes)


@dataclass
class _Cell:
    items: list["LayoutBlock | _Table"] = field(default_factory=list)


@dataclass
class _Table:
    index: int
    table: LayoutTable
    cells: list[list[_Cell]]


def _tree(layout: LayoutMetadata) -> list["LayoutBlock | _Table"]:
    """The blocks in document order, each table in place as a tree of its cells."""
    top: list[LayoutBlock | _Table] = []
    made: dict[int, _Table] = {}

    def table_node(index: int) -> _Table:
        if index not in made:
            table = layout.tables[index]
            made[index] = _Table(
                index, table, [[_Cell() for _ in row.cells] for row in table.rows]
            )
            if table.parent_table is None:
                top.append(made[index])
            else:
                parent = table_node(table.parent_table)
                parent.cells[table.parent_row][table.parent_cell].items.append(
                    made[index]
                )
        return made[index]

    for block in layout.blocks:
        if block.table is None:
            top.append(block)
        else:
            table_node(block.table).cells[block.row][block.cell].items.append(block)
    return top


def _text_runs(item: "LayoutBlock | _Table", nested: bool) -> Iterator[LayoutRun]:
    """A cell item's visible text runs in document order, as ``visible_text`` reads
    them: a ``<br>`` adds nothing, and nested tables only when ``nested``."""
    if isinstance(item, _Table):
        if nested:
            for row in item.cells:
                for cell in row:
                    for inner in cell.items:
                        yield from _text_runs(inner, nested)
        return
    for run in item.runs:
        if counts(run) and not run.br:
            yield run


def _cell_text(cell: _Cell, *, nested: bool) -> str:
    return collapse(
        "".join(run.text for item in cell.items for run in _text_runs(item, nested))
    )


class LayoutBlocks:
    """layout-1 over one capture: its blocks, in document order, before C1-C5."""

    def __init__(self, layout: LayoutMetadata) -> None:
        self.body = body_size(layout)
        self.blocks: list[Block] = []
        for item in _tree(layout):
            self._item(item)

    # -- blocks -----------------------------------------------------------------
    def _item(self, item: "LayoutBlock | _Table") -> None:
        if isinstance(item, _Table):
            self._table(item)
        else:
            self._block(item)

    def _block(self, block: LayoutBlock) -> None:
        if block.tag == "pre":
            for piece in split_pre(block.runs):
                self._emit(piece, block, pre=True)
            return
        for piece in split_breaks(block.runs):
            self._emit(piece, block, pre=False)

    def _emit(
        self, runs: Sequence[LayoutRun], block: LayoutBlock, *, pre: bool
    ) -> None:
        raw = "".join("\n" if run.br else run.text for run in runs if counts(run))
        text = normalize(collapse(raw))
        if not text:
            return
        kind, level = type_block(runs, text, block, self.body)
        self.blocks.append(
            Block(
                type=kind,
                text=text,
                source_type=f"{SOURCE}:{block.tag}",
                level=level,
                pre_lines=tuple(raw.split("\n")) if pre else None,
            )
        )

    # -- tables -----------------------------------------------------------------
    def _table(self, table: _Table) -> None:
        rows = [
            index
            for index, cells in enumerate(table.cells)
            if any(_cell_text(cell, nested=True) for cell in cells)
        ]
        markers = [self._marker_row(table.cells[index]) for index in rows]
        if rows and all(markers):
            for kind, text in markers:
                if text := normalize(text):
                    self.blocks.append(
                        Block(
                            type=kind, text=text, source_type=f"{SOURCE}:marker-table"
                        )
                    )
            return
        if _is_data_table(table):
            self._data_table(table, rows)
            return
        for cells in table.cells:
            for cell in cells:
                for item in cell.items:
                    self._item(item)

    def _marker_row(self, cells: Sequence[_Cell]) -> tuple[str, str] | None:
        """L13: (type, text) when the row's first non-empty cell holds only a marker."""
        texts = [_cell_text(cell, nested=True) for cell in cells]
        filled = [(cell, text) for cell, text in zip(cells, texts, strict=True) if text]
        if len(filled) < 2 or len(filled[0][1]) > MAX_MARKER_CHARS:
            return None
        (marker_cell, marker), rest = (
            filled[0],
            " ".join(text for _, text in filled[1:]),
        )
        first = next(
            (
                run
                for item in marker_cell.items
                for run in _text_runs(item, nested=False)
                if run.text.strip()
            ),
            None,
        )
        if _FOOTNOTE_CELL.match(marker) or (first is not None and first.superscript):
            return "footnote", rest
        if _LIST_CELL.match(marker) or (first is not None and first.symbol_font):
            return "list_item", rest
        return None

    def _data_table(self, table: _Table, rows: Sequence[int]) -> None:
        """L14, L15 and L17: the grid, its header rows, and the rows that leave it."""
        grid: list[Row] = []
        numeric_seen = False
        for index in rows:
            own = table.table.rows[index]
            texts = [_cell_text(cell, nested=True) for cell in table.cells[index]]
            numeric = any(
                _NUMERIC_CELL.match(text) and not _YEAR.match(text)
                for text in texts[1:]
                if text
            )
            numeric_seen = numeric_seen or numeric
            all_th = bool(own.cells) and all(cell.header for cell in own.cells)
            header = own.head or all_th or not numeric_seen
            grid.append(
                Row(
                    header,
                    tuple(
                        Cell(text, cell.colspan, cell.rowspan)
                        for cell, text in zip(own.cells, texts, strict=True)
                    ),
                )
            )
        starts = grid_columns(grid)
        width = max(
            (
                start + cell.colspan
                for row, row_starts in zip(grid, starts, strict=True)
                for cell, start in zip(row.cells, row_starts, strict=True)
            ),
            default=0,
        )
        piece: list[GridCell] = []
        piece_row = 0
        for index, row, row_starts in zip(rows, grid, starts, strict=True):
            filled = [
                (k, cell) for k, cell in enumerate(row.cells) if normalize(cell.text)
            ]
            spanning = (
                len(filled) == 1
                and row_starts[filled[0][0]] == 0
                and filled[0][1].colspan >= width
                and any(char.isalpha() for char in filled[0][1].text)
            )
            if spanning:
                self._close(piece)
                piece, piece_row = [], 0
                self._lift(table.cells[index][filled[0][0]])
                continue
            for cell, start in zip(row.cells, row_starts, strict=True):
                if text := normalize(cell.text):
                    piece.append(
                        GridCell(
                            text,
                            piece_row,
                            start,
                            cell.rowspan,
                            cell.colspan,
                            row.header,
                        )
                    )
            piece_row += 1
        self._close(piece)

    def _close(self, cells: Sequence[GridCell]) -> None:
        if cells:
            self.blocks.append(
                Block(
                    type="table",
                    text="",
                    source_type=f"{SOURCE}:table",
                    cells=tuple(cells),
                )
            )

    def _lift(self, cell: _Cell) -> None:
        """L17: the spanning cell's text as one block, typed by L8-L12."""
        runs = [run for item in cell.items for run in _text_runs(item, nested=True)]
        text = normalize(collapse("".join(run.text for run in runs)))
        if not text:
            return
        kind = classify(_walker_runs(runs), text)
        if (
            kind == "paragraph"
            and larger(runs, self.body)
            and len(text.split()) <= MAX_HEADING_WORDS
        ):
            kind = "heading"
        self.blocks.append(Block(type=kind, text=text, source_type=f"{SOURCE}:row"))


def _is_data_table(table: _Table) -> bool:
    """L14: at least two rows with text and one row with two or more non-empty cells,
    counting the table's own cells' text without nested tables."""
    rows_with_text = 0
    has_multi_cell_row = False
    for cells in table.cells:
        filled = sum(
            1 for cell in cells if primary_space(_cell_text(cell, nested=False))
        )
        rows_with_text += filled > 0
        has_multi_cell_row = has_multi_cell_row or filled >= 2
    return rows_with_text >= 2 and has_multi_cell_row
