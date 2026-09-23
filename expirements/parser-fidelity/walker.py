# /// script
# requires-python = ">=3.14"
# dependencies = ["lxml==6.1.3", "beautifulsoup4==4.15.0"]
# ///
"""Candidate: the bespoke lxml walker. Its rules are in walker-rules.md (W0-W16).

Developed only on the development set; frozen before its first fixture run.

    uv run --locked --script expirements/parser-fidelity/walker.py --input S --output D --sidecar C
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass

from lxml.html import HtmlElement
from pf_classes import (
    BARE_PAGE_NUMBER,
    body_of,
    is_data_table,
    is_hidden,
    own_cells,
    own_rows,
    parse_document,
    visible_text,
)
from pf_dump import Cell, Element, Row, grid_text, run_adapter

BLOCK_TAGS = frozenset(
    {
        "address",
        "article",
        "blockquote",
        "center",
        "dd",
        "div",
        "dl",
        "dt",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "ul",
    }
)
HEADING_TAGS = {f"h{n}": n for n in range(1, 7)}
MAX_HEADING_WORDS = 12
MAX_MARKER_CHARS = 4
BULLETS = "\u2022\u25cf\u25e6\u25aa\u25a0\u2023\u2043\xb7\u2219"
_BULLET_START = re.compile(rf"^(?:[{BULLETS}]|[-\u2013\u2014]\s)")
_FOOTNOTE_MARKER = (
    r"\(\d{1,2}\)|\([a-z]\)|\*{1,3}|[\u2020\u2021]|[\xb9\xb2\xb3\u2070-\u2079]+"
)
_FOOTNOTE_START = re.compile(rf"^(?:{_FOOTNOTE_MARKER})\s*\S")
_FOOTNOTE_CELL = re.compile(rf"^(?:{_FOOTNOTE_MARKER})$")
_LIST_CELL = re.compile(
    rf"^(?:[{BULLETS}\u2013\u2014-]|\d{{1,2}}\.|[a-z]\.|[ivx]{{1,4}}\.)$", re.IGNORECASE
)
_NUMERIC_CELL = re.compile(r"^[\$\(\-\u2013\u2014]*\s*[\d.,]*\d[\d.,]*\s*%?\)?$")
_YEAR = re.compile(r"^(?:19|20)\d{2}$")
_FONT_WEIGHT = re.compile(r"font-weight\s*:\s*([a-z0-9]+)", re.IGNORECASE)
_DECORATION = re.compile(
    r"text-decoration(?:-line)?\s*:\s*[^;]*underline", re.IGNORECASE
)
_SYMBOL_FONT = re.compile(r"wingdings|symbol", re.IGNORECASE)
_WHITESPACE = re.compile(r"\s+")
_BLANK_LINE = re.compile(r"\n[ \t\r\f\v]*\n")  # W5 splits pre text here


@dataclass(frozen=True)
class Style:
    bold: bool = False
    underline: bool = False
    sup: bool = False
    symbol_font: bool = False


@dataclass(frozen=True)
class Run:
    text: str
    style: Style


BREAK = Run("\n", Style())  # a <br>; two in a row end the block (W3)


def child_style(el: HtmlElement, style: Style) -> Style:
    tag = el.tag
    css = el.get("style") or ""
    bold = style.bold or tag in ("b", "strong")
    weight = _FONT_WEIGHT.search(css)
    if weight:
        value = weight.group(1).lower()
        bold = value in ("bold", "bolder") or (value.isdigit() and int(value) >= 600)
    underline = style.underline or tag in ("u", "ins") or bool(_DECORATION.search(css))
    face = f"{el.get('face') or ''} {css}"
    symbol = style.symbol_font or bool(_SYMBOL_FONT.search(face))
    return Style(bold, underline, style.sup or tag == "sup", symbol)


def cell_style(table: HtmlElement, cell: HtmlElement, style: Style) -> Style:
    """W11: a cell inherits the styles of the rows and row groups between it and its table."""
    chain = []
    node = cell
    while node is not None and node is not table:
        chain.append(node)
        node = node.getparent()
    for el in reversed(chain):
        style = child_style(el, style)
    return style


def collapse(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip()


class Walker:
    def __init__(self) -> None:
        self.elements: list[Element] = []
        self.lists: list[int] = []  # indices of the open ul/ol containers (W7)

    def emit(
        self,
        kind: str,
        text: str,
        *,
        parent: int | None = None,
        level: int | None = None,
        source: str,
    ) -> None:
        self.elements.append(Element(kind, text, parent, level, source))

    # -- blocks ---------------------------------------------------------------
    def walk_block(self, el: HtmlElement, style: Style, kind: str) -> None:
        runs: list[Run] = []
        self.walk_content(el, style, runs, kind)
        self.flush(runs, kind, el.tag)

    def walk_content(
        self, el: HtmlElement, style: Style, runs: list[Run], kind: str
    ) -> None:
        if el.text:
            runs.append(Run(el.text, style))
        for child in el:
            self.walk_node(child, style, runs, kind, el.tag)
            if child.tail:
                runs.append(Run(child.tail, style))

    def walk_node(
        self, el: HtmlElement, style: Style, runs: list[Run], kind: str, owner: str
    ) -> None:
        if is_hidden(el):
            return
        tag = el.tag
        if tag == "br":
            runs.append(BREAK)
        elif tag in BLOCK_TAGS:
            self.flush(runs, kind, owner)
            runs.clear()
            self.walk_block_element(el, child_style(el, style), kind)
        else:
            self.walk_content(el, child_style(el, style), runs, kind)

    def walk_block_element(self, el: HtmlElement, style: Style, kind: str) -> None:
        """A nested block: a plain one keeps the enclosing heading or list-item kind (W6, W7)."""
        tag = el.tag
        if tag in HEADING_TAGS:
            self.walk_block(el, style, f"heading{HEADING_TAGS[tag]}")
        elif tag in ("ul", "ol"):
            self.walk_list(el, style)
        elif tag == "li":
            self.walk_block(el, style, "list_item")
        elif tag == "table":
            self.walk_table(el, style)
        elif tag == "pre":
            self.walk_pre(el, style)
        elif tag != "hr":
            self.walk_block(el, style, kind)

    def walk_list(self, el: HtmlElement, style: Style) -> None:
        parent = self.lists[-1] if self.lists else None
        self.emit("other", "", parent=parent, source=el.tag)
        self.lists.append(len(self.elements) - 1)
        self.walk_block(el, style, "block")
        self.lists.pop()

    def walk_pre(self, el: HtmlElement, style: Style) -> None:
        """W5: split at blank lines; each piece keeps its styled runs for W8-W12."""
        runs = styled_runs(el, style)
        text = "".join(run.text for run in runs)
        gaps = [(gap.start(), gap.end()) for gap in _BLANK_LINE.finditer(text)]
        starts = [0] + [end for _, end in gaps]
        ends = [start for start, _ in gaps] + [len(text)]
        for start, end in zip(starts, ends, strict=True):
            self.flush(slice_runs(runs, start, end), "block", "pre")

    # -- typing ---------------------------------------------------------------
    def flush(self, runs: list[Run], kind: str, source: str) -> None:
        segment: list[Run] = []
        breaks = 0
        for run in runs:
            if run is BREAK:
                breaks += 1
                if breaks >= 2:
                    self.emit_block(segment, kind, source)
                    segment = []
                    continue
            elif run.text.strip():
                breaks = 0
            segment.append(run)
        self.emit_block(segment, kind, source)

    def emit_block(self, runs: list[Run], kind: str, source: str) -> None:
        text = collapse("".join(run.text for run in runs))
        if not text:
            return
        if kind.startswith("heading"):
            self.emit(
                "heading", text, level=int(kind.removeprefix("heading")), source=source
            )
        elif kind == "list_item":
            parent = self.lists[-1] if self.lists else None
            self.emit(
                "list_item",
                text,
                parent=parent,
                level=len(self.lists) or None,
                source=source,
            )
        else:
            self.emit(classify(runs, text), text, source=source)

    # -- tables ---------------------------------------------------------------
    def walk_table(self, table: HtmlElement, style: Style) -> None:
        caption = table.find("caption")
        if caption is not None and not is_hidden(caption):
            self.walk_block(caption, child_style(caption, style), "block")
        rows = [
            row
            for row in own_rows(table)
            if any(collapse(visible_text(c)) for c in own_cells(row))
        ]
        marker_rows = [marker_row(row, table, style) for row in rows]
        if rows and all(marker_rows):
            for kind, text in marker_rows:
                self.emit(kind, text, source="marker-table")
        elif is_data_table(table):
            grid = data_grid(table, rows)
            self.emit_table(grid)
        else:
            for row in own_rows(table):
                for cell in own_cells(row):
                    self.walk_block(cell, cell_style(table, cell, style), "block")

    def emit_table(self, grid: tuple[Row, ...]) -> None:
        self.elements.append(
            Element("table", grid_text(grid), None, None, "table", grid)
        )


def classify(runs: list[Run], text: str) -> str:
    """W8-W12 for a block that is not a heading or list item by tag."""
    if BARE_PAGE_NUMBER.fullmatch(text):
        return "other"
    first = next((run for run in runs if run.text.strip()), None)
    if _BULLET_START.match(text) or (
        first
        and first.style.symbol_font
        and len(first.text.strip()) <= MAX_MARKER_CHARS
    ):
        return "list_item"
    if _FOOTNOTE_START.match(text) or (
        first
        and first.style.sup
        and len(first.text.strip()) <= MAX_MARKER_CHARS
        and len(text) > len(first.text.strip())
    ):
        return "footnote"
    styled = all(
        run.style.bold or run.style.underline for run in runs if run.text.strip()
    )
    if styled and len(text.split()) <= MAX_HEADING_WORDS:
        return "heading"
    return "paragraph"


def styled_runs(el: HtmlElement, style: Style) -> list[Run]:
    """The visible text of ``el`` as styled runs in document order (W1).

    A <br> is a newline, and nested tables are left out, as in ``pf_classes.cell_text``.
    """
    runs = [Run(el.text, style)] if el.text else []
    for child in el:
        if child.tag == "br":
            runs.append(Run("\n", style))
        elif not is_hidden(child) and child.tag != "table":
            runs.extend(styled_runs(child, child_style(child, style)))
        if child.tail:
            runs.append(Run(child.tail, style))
    return runs


def slice_runs(runs: list[Run], start: int, end: int) -> list[Run]:
    """The runs covering characters [start, end) of their joined text, cut at both ends."""
    out, offset = [], 0
    for run in runs:
        low, high = max(start, offset), min(end, offset + len(run.text))
        if low < high:
            out.append(Run(run.text[low - offset : high - offset], run.style))
        offset += len(run.text)
    return out


def marker_row(
    row: HtmlElement, table: HtmlElement, style: Style
) -> tuple[str, str] | None:
    """W13: (type, text) when the row's first non-empty cell holds only a marker.

    ``style`` is the table's. A W9 symbol-font run or a W10 leading ``sup`` in the marker
    cell counts, as well as the marker's text.
    """
    cells = own_cells(row)
    texts = [collapse(visible_text(cell)) for cell in cells]
    filled = [(cell, text) for cell, text in zip(cells, texts, strict=True) if text]
    if len(filled) < 2 or len(filled[0][1]) > MAX_MARKER_CHARS:
        return None
    (marker_cell, marker), rest = filled[0], " ".join(text for _, text in filled[1:])
    runs = styled_runs(marker_cell, cell_style(table, marker_cell, style))
    first = next((run for run in runs if run.text.strip()), None)
    if _FOOTNOTE_CELL.match(marker) or (first is not None and first.style.sup):
        return "footnote", rest
    if _LIST_CELL.match(marker) or (first is not None and first.style.symbol_font):
        return "list_item", rest
    return None


def data_grid(table: HtmlElement, rows: list[HtmlElement]) -> tuple[Row, ...]:
    """W14-W15: the grid with header flags."""
    cells = [own_cells(row) for row in rows]
    numeric_seen = False
    grid = []
    for row, row_cells in zip(rows, cells, strict=True):
        texts = [collapse(visible_text(cell)) for cell in row_cells]
        numeric = any(
            _NUMERIC_CELL.match(text) and not _YEAR.match(text)
            for text in texts[1:]
            if text
        )
        numeric_seen = numeric_seen or numeric
        all_th = bool(row_cells) and all(cell.tag == "th" for cell in row_cells)
        header = _in_thead(row, table) or all_th or not numeric_seen
        spans = [
            Cell(text, _span(cell, "colspan"), _span(cell, "rowspan"))
            for cell, text in zip(row_cells, texts, strict=True)
        ]
        grid.append(Row(header, tuple(spans)))
    return tuple(grid)


def _in_thead(row: HtmlElement, table: HtmlElement) -> bool:
    parent = row.getparent()
    while parent is not None and parent is not table:
        if parent.tag == "thead":
            return True
        parent = parent.getparent()
    return False


def _span(cell: HtmlElement, name: str) -> int:
    value = (cell.get(name) or "1").strip()
    return max(1, int(value)) if value.isdigit() else 1


def parse(html: str) -> list[Element]:
    sys.setrecursionlimit(
        max(sys.getrecursionlimit(), 20000)
    )  # deeply nested font soup
    walker = Walker()
    walker.walk_block(body_of(parse_document(html)), Style(), "block")
    return walker.elements


if __name__ == "__main__":
    raise SystemExit(run_adapter(parse, library="lxml"))
