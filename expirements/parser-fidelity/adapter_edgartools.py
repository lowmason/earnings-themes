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
# A leaf whose children hold one of these is split around it rather than flattened.
STRUCTURAL_NODE_TYPES = frozenset({"LIST", "TABLE"})


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


def holds_structure(node: object) -> bool:
    """True when the node is, or contains, a list or table the library exposes as nodes."""
    stack = [node]
    while stack:
        current = stack.pop()
        if current.type.name in STRUCTURAL_NODE_TYPES:
            return True
        stack.extend(current.children)
    return False


def split_children(children: list[object]) -> list[object]:
    """[text, block, text, ..., text]: each nested list or table between the texts around it.

    A text joins its nodes' non-empty text() with spaces, as ListItemNode.text() does.
    """
    pieces: list[object] = []
    run: list[str] = []
    for child in children:
        if holds_structure(child):
            pieces += [" ".join(run), child]
            run = []
        else:
            text = child.text()
            if text:
                run.append(text)
    return [*pieces, " ".join(run)]


def flatten(root: object) -> list[Element]:
    """Pre-order walk: containers become text-less parents; every other node is a leaf.

    A leaf's text() would flatten a nested list or table (ListItemNode.text() joins every
    child), so a leaf that holds one is split: its text before the first nested block is its
    element, the nested blocks are that element's children, and any later text is a further
    element of the leaf's type.
    """
    elements: list[Element] = []
    stack: list[tuple[object, int | None]] = [(root, None)]
    while stack:
        node, parent = stack.pop()
        # A split leaf's text after one of its nested blocks, already typed.
        if isinstance(node, Element):
            elements.append(node)
            continue
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
            kind = leaf_type(node)
            level = getattr(node, "level", None) if name == "HEADING" else None
            if not any(holds_structure(child) for child in node.children):
                elements.append(
                    Element(kind, node.text() or "", parent, level, source_type)
                )
                continue
            first, *rest = split_children(node.children)
            elements.append(Element(kind, first, parent, level, source_type))
            index = len(elements) - 1
            pending: list[tuple[object, int | None]] = []
            for piece in rest:
                if not isinstance(piece, str):
                    pending.append((piece, index))
                elif piece:
                    pending.append(
                        (Element(kind, piece, parent, level, source_type), None)
                    )
            stack.extend(reversed(pending))
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
