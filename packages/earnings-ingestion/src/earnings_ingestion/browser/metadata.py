"""The layout-metadata script: the capture's own extractor (metadata version 1).

The script runs in the page through WebDriver while document JavaScript stays
disabled; it only reads the DOM and computed style. It emits one block for the runs a
block element holds directly, flushing where a nested block starts, as the walker
does (W2). A ``<pre>`` element's whole content is one block, tables left out, as the
walker's W5 reads it. Each run is one text node's raw DOM text with its computed
style, so text-transform never alters it; a ``<br>`` is a run of its own. A block
outside every table cell whose runs hold only whitespace is not emitted: it has no
text for layout-1. Inside a cell such a block stays, because it separates the words
of the cell's other blocks.

Content with computed ``display: none`` is skipped, and so is ``noscript``: it
renders only because the capture disables scripts, and a reader's browser hides it.
Each table records its own rendered rows (whether each sits in ``thead``), their
rendered cells (whether each is a ``th``, and its spans), and the cell of another
table that holds it, if any.

Any change to the script, or to how ``parse_metadata`` reads it, is a new
``METADATA_VERSION``: captures made by different scripts never share a cache key.
"""

from collections.abc import Mapping
from typing import Any

from earnings_ingestion.browser.records import (
    LayoutBlock,
    LayoutCell,
    LayoutMetadata,
    LayoutRow,
    LayoutRun,
    LayoutTable,
)

METADATA_VERSION = "layout-metadata-1"

METADATA_SCRIPT = r"""
const BLOCK_DISPLAYS = new Set([
  "block", "list-item", "table", "table-row-group", "table-header-group",
  "table-footer-group", "table-row", "table-cell", "table-caption", "flex", "grid",
  "flow-root",
]);
const RESETS = new Set(["td", "th", "caption", "table", "ul", "ol", "pre"]);
const styles = new Map();
function style(el) {
  let s = styles.get(el);
  if (s === undefined) {
    s = getComputedStyle(el);
    styles.set(el, s);
  }
  return s;
}
function rendered(el) {
  return el.getClientRects().length > 0;
}
const tables = [];
const cells = new Map();
function enclosing(node) {
  for (let up = node.parentElement; up !== null; up = up.parentElement) {
    if (cells.has(up)) return cells.get(up);
    if (up === document.body) break;
  }
  return null;
}
for (const table of document.body.querySelectorAll("table")) {
  if (!rendered(table)) continue;
  const index = tables.length;
  const parent = enclosing(table);
  const rows = [];
  for (const tr of table.querySelectorAll("tr")) {
    if (tr.closest("table") !== table || !rendered(tr)) continue;
    const row = [];
    for (const cell of tr.cells) {
      if (!rendered(cell)) continue;
      cells.set(cell, [index, rows.length, row.length]);
      row.push({
        header: cell.tagName === "TH",
        colspan: Math.max(1, cell.colSpan),
        rowspan: Math.max(1, cell.rowSpan),
      });
    }
    const head = tr.parentElement !== null && tr.parentElement.tagName === "THEAD";
    rows.push({head: head, cells: row});
  }
  tables.push({
    parent_table: parent === null ? null : parent[0],
    parent_row: parent === null ? null : parent[1],
    parent_cell: parent === null ? null : parent[2],
    rows: rows,
  });
}
function context(owner) {
  let heading = null;
  let listItem = false;
  let decided = false;
  let depth = 0;
  let cell = null;
  for (let node = owner; node !== null; node = node.parentElement) {
    const tag = node.tagName.toLowerCase();
    if (!decided) {
      if (/^h[1-6]$/.test(tag)) {
        heading = Number(tag[1]);
        decided = true;
      } else if (tag === "li") {
        listItem = true;
        decided = true;
      } else if (RESETS.has(tag)) {
        decided = true;
      }
    }
    if (tag === "ul" || tag === "ol") depth += 1;
    if (cell === null && cells.has(node)) cell = cells.get(node);
    if (node === document.body) break;
  }
  return {heading, listItem, depth, cell};
}
function underlined(el) {
  for (let node = el; node !== null; node = node.parentElement) {
    if (style(node).textDecorationLine.includes("underline")) return true;
    if (node === document.body) break;
  }
  return false;
}
function raised(el, owner) {
  for (let node = el; node !== null; node = node.parentElement) {
    if (style(node).verticalAlign === "super") return true;
    if (node === owner || node === document.body) break;
  }
  return false;
}
function textRun(node, owner) {
  const el = node.parentElement;
  const s = style(el);
  const range = document.createRange();
  range.selectNodeContents(node);
  return {
    text: node.data,
    br: false,
    visible: s.visibility === "visible" && range.getClientRects().length > 0,
    bold: Number.parseInt(s.fontWeight, 10) >= 600,
    underline: underlined(el),
    superscript: raised(el, owner),
    symbol_font: /wingdings|symbol/i.test(s.fontFamily),
    font_size: Number.parseFloat(s.fontSize),
  };
}
function breakRun(el) {
  const s = style(el);
  return {
    text: "\n", br: true, visible: rendered(el), bold: false, underline: false,
    superscript: false, symbol_font: false, font_size: Number.parseFloat(s.fontSize),
  };
}
const blocks = [];
function flush(owner, runs) {
  if (runs.length === 0) return;
  const ctx = context(owner);
  if (ctx.cell === null && runs.every((run) => !/\S/.test(run.text))) {
    runs.length = 0;
    return;
  }
  const box = owner.getBoundingClientRect();
  blocks.push({
    tag: owner.tagName.toLowerCase(),
    display: style(owner).display,
    heading_level: ctx.heading,
    list_item: ctx.listItem,
    list_depth: ctx.depth,
    table: ctx.cell === null ? null : ctx.cell[0],
    row: ctx.cell === null ? null : ctx.cell[1],
    cell: ctx.cell === null ? null : ctx.cell[2],
    x: Math.round(box.x + window.scrollX),
    y: Math.round(box.y + window.scrollY),
    width: Math.round(box.width),
    height: Math.round(box.height),
    runs: runs.splice(0),
  });
}
function preRuns(el, owner, runs) {
  for (const child of el.childNodes) {
    if (child.nodeType === Node.TEXT_NODE) {
      if (child.data) runs.push(textRun(child, owner));
    } else if (child.nodeType === Node.ELEMENT_NODE) {
      const tag = child.tagName.toLowerCase();
      if (tag === "br") {
        const run = breakRun(child);
        run.br = false;
        runs.push(run);
      } else if (tag !== "table" && style(child).display !== "none") {
        preRuns(child, owner, runs);
      }
    }
  }
}
function walkBlock(el) {
  const runs = [];
  if (el.tagName.toLowerCase() === "pre") {
    preRuns(el, el, runs);
    flush(el, runs);
    return;
  }
  walkContent(el, el, runs);
  flush(el, runs);
}
function walkContent(el, owner, runs) {
  for (const child of el.childNodes) {
    if (child.nodeType === Node.TEXT_NODE) {
      if (child.data) runs.push(textRun(child, owner));
      continue;
    }
    if (child.nodeType !== Node.ELEMENT_NODE) continue;
    const tag = child.tagName.toLowerCase();
    if (tag === "br") {
      runs.push(breakRun(child));
      continue;
    }
    const display = style(child).display;
    if (display === "none" || tag === "noscript") continue;
    if (BLOCK_DISPLAYS.has(display) || tag === "pre") {
      flush(owner, runs);
      walkBlock(child);
      continue;
    }
    walkContent(child, owner, runs);
  }
}
walkBlock(document.body);
return {blocks: blocks, tables: tables};
"""
"""Returns ``{"blocks": [...], "tables": [...]}`` for ``parse_metadata``."""


def parse_metadata(payload: Mapping[str, Any]) -> LayoutMetadata:
    """The script's result as records; malformed output raises ``ValueError``."""
    try:
        blocks = tuple(
            LayoutBlock(
                **{key: value for key, value in block.items() if key != "runs"},
                runs=tuple(LayoutRun(**run) for run in block["runs"]),
            )
            for block in payload["blocks"]
        )
        tables = tuple(
            LayoutTable(
                **{key: value for key, value in table.items() if key != "rows"},
                rows=tuple(
                    LayoutRow(
                        head=row["head"],
                        cells=tuple(LayoutCell(**cell) for cell in row["cells"]),
                    )
                    for row in table["rows"]
                ),
            )
            for table in payload["tables"]
        )
    except (KeyError, TypeError) as error:
        raise ValueError(f"malformed layout metadata: {error!r}") from error
    return LayoutMetadata(blocks=blocks, tables=tables)
