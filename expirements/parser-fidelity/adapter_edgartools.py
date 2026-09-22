# /// script
# requires-python = ">=3.14"
# dependencies = ["edgartools==5.58.0"]
# ///
"""Candidate adapter: edgartools 5.58.0's HTML document parser (edgar.documents).

The parse path is ``edgar.documents.parse_html(html)`` with the default ParserConfig,
the call edgartools' own ``PressRelease.text()`` makes. The legacy ``edgar.files.html``
parser is deprecated (removed in edgartools 6.0) and is not measured.

    uv run --locked --script expirements/parser-fidelity/adapter_edgartools.py --input S --output D --sidecar C
    uv run --locked --script expirements/parser-fidelity/adapter_edgartools.py --self-check

Type mapping (NodeType name -> common type). Containers carry no text.
"""

from __future__ import annotations

import os
import sys

from pf_dump import Cell, Element, Row, grid_text, run_adapter
from pf_paths import EDGAR_HOME

CONTAINER_NODE_TYPES = frozenset({"DOCUMENT", "SECTION", "CONTAINER", "LIST"})
LEAF_NODE_TYPES = {
    "HEADING": "heading",
    "PARAGRAPH": "paragraph",
    "LIST_ITEM": "list_item",
    "TABLE": "table",
    "TEXT": "other",
    "LINK": "other",
    "IMAGE": "other",
    "XBRL_FACT": "other",
}
FOOTNOTE_SEMANTIC_TYPE = (
    "FOOTNOTE"  # a paragraph carrying SemanticType.FOOTNOTE is a footnote
)


def table_rows(table: object) -> tuple[Row, ...]:
    """Header rows first, then body rows, then footer rows, as TableNode holds them."""
    rows = [Row(True, tuple(_cell(c) for c in header)) for header in table.headers]
    for row in [*table.rows, *table.footer]:
        rows.append(Row(bool(row.is_header), tuple(_cell(c) for c in row.cells)))
    return tuple(rows)


def _cell(cell: object) -> Cell:
    return Cell(
        cell.text() or "",
        max(1, int(cell.colspan or 1)),
        max(1, int(cell.rowspan or 1)),
    )


def leaf_type(node: object) -> str:
    name = node.type.name
    semantic = getattr(node, "semantic_type", None)
    if (
        name == "PARAGRAPH"
        and getattr(semantic, "name", None) == FOOTNOTE_SEMANTIC_TYPE
    ):
        return "footnote"
    return LEAF_NODE_TYPES[name]


def flatten(root: object) -> list[Element]:
    """Pre-order walk: containers become text-less parents; every other node is a leaf."""
    elements: list[Element] = []
    stack: list[tuple[object, int | None]] = [(root, None)]
    while stack:
        node, parent = stack.pop()
        name = node.type.name
        source_type = type(node).__name__
        if name in CONTAINER_NODE_TYPES:
            elements.append(Element("other", "", parent, None, source_type))
            index = len(elements) - 1
            stack.extend((child, index) for child in reversed(node.children))
        elif name == "TABLE":
            if getattr(node, "caption", None):
                elements.append(
                    Element("other", node.caption, parent, None, "TableNode.caption")
                )
            rows = table_rows(node)
            elements.append(
                Element("table", grid_text(rows), parent, None, source_type, rows)
            )
        else:
            level = getattr(node, "level", None) if name == "HEADING" else None
            elements.append(
                Element(leaf_type(node), node.text() or "", parent, level, source_type)
            )
    return elements


def parse(html: str) -> list[Element]:
    os.environ.setdefault("EDGAR_LOCAL_DATA_DIR", str(EDGAR_HOME))
    from edgar.documents import (
        parse_html,
    )  # imported after the network guard is installed

    return flatten(parse_html(html).root)


def self_check() -> int:
    """Every public NodeType must be mapped; run before the freeze."""
    os.environ.setdefault("EDGAR_LOCAL_DATA_DIR", str(EDGAR_HOME))
    from edgar.documents.types import NodeType, SemanticType

    unmapped = set(NodeType.__members__) - CONTAINER_NODE_TYPES - set(LEAF_NODE_TYPES)
    stale = (CONTAINER_NODE_TYPES | set(LEAF_NODE_TYPES)) - set(NodeType.__members__)
    missing_semantic = FOOTNOTE_SEMANTIC_TYPE not in SemanticType.__members__
    print(f"NodeType members: {sorted(NodeType.__members__)}")
    print(
        f"unmapped: {sorted(unmapped)}; stale: {sorted(stale)}; FOOTNOTE missing: {missing_semantic}"
    )
    return 1 if unmapped or stale or missing_semantic else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-check"]:
        raise SystemExit(self_check())
    raise SystemExit(run_adapter(parse, library="edgartools"))
