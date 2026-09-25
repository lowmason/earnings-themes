"""Deterministic class tests for release exhibits (spec: Fixture corpus > Classes).

These values only sort fixtures into classes; they are not quality thresholds (R13.1
is untouched). The walker imports the data-table helpers, so this module is frozen
with it. Characters are counted in the primary matching space.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import asdict, dataclass

import lxml.html
from lxml.html import HtmlElement
from pf_decode import decode_html_bytes
from pf_space import primary_space

SHARE_THRESHOLD = 0.5
LAYOUT_PROSE_WORDS = 40
HIDDEN_TAGS = frozenset({"script", "style", "head", "title", "noscript", "template"})
BLOCK_TAGS = frozenset(
    {"p", "div", "center", "td", "th", "li", "h1", "h2", "h3", "h4", "h5", "h6"}
)

_DISPLAY_NONE = re.compile(r"display\s*:\s*none", re.IGNORECASE)
_POSITIONED = re.compile(r"position\s*:\s*(?:absolute|fixed)", re.IGNORECASE)
_PAGE_BREAK = re.compile(
    r"page-break-(?:before|after)\s*:\s*(?:always|left|right)|(?<![-\w])break-(?:before|after)\s*:\s*page",
    re.IGNORECASE,
)
BARE_PAGE_NUMBER = re.compile(
    r"(?:page\s*)?[-\u2013\u2014\s]*\d{1,4}[-\u2013\u2014\s]*", re.IGNORECASE
)


@dataclass(frozen=True)
class ClassTests:
    visible_chars: int
    data_tables: int
    data_table_chars: int
    data_table_share: float
    pre_chars: int
    pre_share: float
    positioned_text: bool
    layout_table_prose: bool
    max_layout_cell_words: int
    page_break_styling: bool
    bare_page_number_blocks: int
    page_break_debris: bool
    preformatted_text: bool
    table_heavy: bool
    narrative_only: bool
    malformed_layout: bool
    clean_html: bool

    def as_dict(self) -> dict[str, int | float | bool]:
        return asdict(self)


def parse_document(text: str) -> HtmlElement:
    """Parse decoded text with libxml2's HTML parser; the explicit encoding overrides declarations."""
    parser = lxml.html.HTMLParser(encoding="utf-8")
    return lxml.html.document_fromstring(text.encode("utf-8"), parser=parser)


def body_of(root: HtmlElement) -> HtmlElement:
    body = root.find("body")
    return body if body is not None else root


def is_hidden(el: HtmlElement) -> bool:
    """Comments, processing instructions, hidden tags, and inline ``display: none``."""
    if not isinstance(el.tag, str):
        return True
    return el.tag.lower() in HIDDEN_TAGS or bool(
        _DISPLAY_NONE.search(el.get("style") or "")
    )


def visible_elements(root: HtmlElement) -> Iterator[HtmlElement]:
    stack = [root]
    while stack:
        el = stack.pop()
        if is_hidden(el):
            continue
        yield el
        stack.extend(reversed(list(el)))


def visible_text(el: HtmlElement, *, skip_tables: bool = False) -> str:
    """Visible text of ``el``; with ``skip_tables``, text of nested tables is left out."""
    parts: list[str] = []
    stack: list[HtmlElement | str] = [el]
    while stack:
        item = stack.pop()
        if isinstance(item, str):
            parts.append(item)
            continue
        if is_hidden(item) or (skip_tables and item is not el and item.tag == "table"):
            continue
        pending: list[HtmlElement | str] = [item.text] if item.text else []
        for child in item:
            pending.append(child)
            if child.tail:
                pending.append(child.tail)
        stack.extend(reversed(pending))
    return "".join(parts)


def _nearest(el: HtmlElement, tag: str) -> HtmlElement | None:
    parent = el.getparent()
    while parent is not None and parent.tag != tag:
        parent = parent.getparent()
    return parent


def own_rows(table: HtmlElement) -> list[HtmlElement]:
    """The table's own visible rows, not those of nested tables."""
    return [
        tr
        for tr in table.iter("tr")
        if _nearest(tr, "table") is table and not is_hidden(tr)
    ]


def own_cells(row: HtmlElement) -> list[HtmlElement]:
    return [
        cell
        for cell in row.iter("td", "th")
        if _nearest(cell, "tr") is row and not is_hidden(cell)
    ]


def cell_text(cell: HtmlElement) -> str:
    return visible_text(cell, skip_tables=True)


def is_data_table(table: HtmlElement) -> bool:
    """At least two rows with text and one row with two or more non-empty cells (own rows and cells)."""
    rows_with_text = 0
    has_multi_cell_row = False
    for row in own_rows(table):
        filled = sum(1 for cell in own_cells(row) if primary_space(cell_text(cell)))
        rows_with_text += filled > 0
        has_multi_cell_row = has_multi_cell_row or filled >= 2
    return rows_with_text >= 2 and has_multi_cell_row


def _text_segments(
    body: HtmlElement, data_tables: set[HtmlElement]
) -> list[tuple[str, bool, bool]]:
    """Visible text segments with (inside a data table, inside <pre>) flags."""
    out: list[tuple[str, bool, bool]] = []
    stack: list[tuple[HtmlElement | str, bool, bool]] = [(body, False, False)]
    while stack:
        item, in_data, in_pre = stack.pop()
        if isinstance(item, str):
            out.append((item, in_data, in_pre))
            continue
        if is_hidden(item):
            continue
        in_data = in_data or item in data_tables
        in_pre = in_pre or item.tag == "pre"
        pending: list[tuple[HtmlElement | str, bool, bool]] = []
        if item.text:
            pending.append((item.text, in_data, in_pre))
        for child in item:
            pending.append((child, in_data, in_pre))
            if child.tail:
                pending.append((child.tail, in_data, in_pre))
        stack.extend(reversed(pending))
    return out


def _style_sources(root: HtmlElement) -> list[str]:
    inline = [el.get("style") or "" for el in root.iter() if isinstance(el.tag, str)]
    sheets = [el.text or "" for el in root.iter("style")]
    return inline + sheets


def run_class_tests(raw: bytes) -> ClassTests:
    root = parse_document(decode_html_bytes(raw).text)
    body = body_of(root)
    elements = list(visible_elements(body))
    tables = [el for el in elements if el.tag == "table"]
    data_tables = {table for table in tables if is_data_table(table)}

    segments = _text_segments(body, data_tables)
    visible_chars = sum(len(primary_space(text)) for text, _, _ in segments)
    data_chars = sum(
        len(primary_space(text)) for text, in_data, _ in segments if in_data
    )
    pre_chars = sum(len(primary_space(text)) for text, _, in_pre in segments if in_pre)
    data_share = data_chars / visible_chars if visible_chars else 0.0
    pre_share = pre_chars / visible_chars if visible_chars else 0.0

    styles = _style_sources(root)
    positioned = any(_POSITIONED.search(style) for style in styles)
    page_break_styling = any(_PAGE_BREAK.search(style) for style in styles)

    layout_words = [
        len(cell_text(cell).split())
        for table in tables
        if table not in data_tables
        for row in own_rows(table)
        for cell in own_cells(row)
    ]
    max_layout_words = max(layout_words, default=0)

    bare_page_numbers = sum(
        1
        for el in elements
        if el.tag in BLOCK_TAGS
        and not any(ancestor in data_tables for ancestor in el.iterancestors("table"))
        and BARE_PAGE_NUMBER.fullmatch(visible_text(el).strip())
    )

    layout_table_prose = max_layout_words >= LAYOUT_PROSE_WORDS
    page_break_debris = page_break_styling and bare_page_numbers > 0
    preformatted = pre_share >= SHARE_THRESHOLD
    malformed = positioned or layout_table_prose or page_break_debris or preformatted
    return ClassTests(
        visible_chars=visible_chars,
        data_tables=len(data_tables),
        data_table_chars=data_chars,
        data_table_share=round(data_share, 4),
        pre_chars=pre_chars,
        pre_share=round(pre_share, 4),
        positioned_text=positioned,
        layout_table_prose=layout_table_prose,
        max_layout_cell_words=max_layout_words,
        page_break_styling=page_break_styling,
        bare_page_number_blocks=bare_page_numbers,
        page_break_debris=page_break_debris,
        preformatted_text=preformatted,
        table_heavy=data_share >= SHARE_THRESHOLD,
        narrative_only=not data_tables,
        malformed_layout=malformed,
        clean_html=not malformed,
    )
