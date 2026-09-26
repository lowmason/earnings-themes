"""walker-1's re-score and the review gate's reports (Stage 3, plan A).

    uv run --locked --all-packages python expirements/parser-fidelity/walker1_report.py

Writes docs/verification/walker-1-report.md from the committed fixtures and gold:

- the re-score (Stage 3 spec: Verification (plan A), item 2): walker-1's elements
  projected back to the dump format and scored by the frozen score.py beside the frozen
  walker, pooled by class, with C1's effect separated from C2-C5's;
- every change, by fixture and block;
- the page-artifact report, against the gold's page_artifact blocks;
- the mask report, flagging every unmasked narrative block that mentions
  forward-looking statements or non-GAAP measures.

These are development-set numbers: the fixtures were Stage 1's test set.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

import tomllib
import walker as frozen
from earnings_core import DocumentElement, ElementType
from earnings_ingestion.canonical import (
    CANONICALIZATION_VERSION,
    Canonicalized,
    canonicalize,
)
from earnings_ingestion.canonical.blocks import Block, to_blocks
from earnings_ingestion.canonical.build import build
from earnings_ingestion.canonical.compensate import compensate
from earnings_ingestion.canonical.decode import decode_html_bytes
from earnings_ingestion.canonical.walker import walk
from pf_decode import decode_html_bytes as frozen_decode
from pf_dump import Cell, Element, Row, grid_text
from pf_paths import FIXTURES, MANIFEST, REPO_ROOT
from pf_space import primary_space
from score import FixtureScore, score_fixture
from validate_gold import SourceText, load_gold

REPORT = REPO_ROOT / "docs" / "verification" / "walker-1-report.md"
COMPARED = (
    "coverage",
    "footnote_merging",
    "reading_order",
    "header_section",
    "header_table",
)
"""The ranked metrics' exact counts; header_loss is header_section plus header_table,
compared separately so neither can hide the other."""
RESIDUALS = ("missed", "split", "merged", "misordered", "header_lost")
NARRATIVE = frozenset(
    {
        ElementType.HEADING,
        ElementType.PARAGRAPH,
        ElementType.LIST_ITEM,
        ElementType.FOOTNOTE,
    }
)
FLAG = re.compile(r"forward\W?looking|non\W?gaap", re.IGNORECASE)
EXCERPT = 80


def project(
    document_text: str, elements: Sequence[DocumentElement]
) -> tuple[list[Element], list[DocumentElement]]:
    """walker-1's elements in the dump format, and the element each came from.

    ``page_artifact`` becomes ``other``; sentences fold back into their blocks; cells
    fold back into their grids, rebuilt from their positions with an empty cell for
    each column no cell occupies. A list container keeps the walker's empty text.
    """
    cells: dict[str, list[DocumentElement]] = defaultdict(list)
    parents: set[str] = set()
    for element in elements:
        if element.type is ElementType.TABLE_CELL:
            cells[element.parent_id or ""].append(element)
        elif element.parent_id is not None and element.type is not ElementType.SENTENCE:
            parents.add(element.parent_id)
    dump: list[Element] = []
    sources: list[DocumentElement] = []
    index: dict[str, int] = {}
    for element in elements:
        if element.type in (ElementType.SENTENCE, ElementType.TABLE_CELL):
            continue
        kind = element.type.value
        if element.type is ElementType.PAGE_ARTIFACT:
            kind = "other"
        rows = None
        if element.element_id in cells:
            rows = rebuild_grid(document_text, cells[element.element_id])
            text = grid_text(rows)
        elif element.type is ElementType.OTHER and element.element_id in parents:
            text = ""
        else:
            text = element.span.slice_of(document_text)
        parent = None if element.parent_id is None else index[element.parent_id]
        index[element.element_id] = len(dump)
        dump.append(
            Element(kind, text, parent, element.level, element.source_type, rows)
        )
        sources.append(element)
    return dump, sources


def rebuild_grid(
    document_text: str, cells: Sequence[DocumentElement]
) -> tuple[Row, ...]:
    """A W14 grid from its cells' positions, row by row in the walker's order."""
    by_row: dict[int, list[DocumentElement]] = defaultdict(list)
    for cell in cells:
        assert cell.table_cell is not None
        by_row[cell.table_cell.row].append(cell)
    claimed: dict[int, list[tuple[int, int]]] = defaultdict(list)
    rows = []
    for row in sorted(by_row):
        placed: list[Cell] = []
        column = 0
        for cell in sorted(by_row[row], key=lambda c: c.table_cell.column):
            context = cell.table_cell
            while column < context.column:
                if not any(start <= column < end for start, end in claimed[row]):
                    placed.append(Cell(""))
                column += 1
            placed.append(
                Cell(
                    cell.span.slice_of(document_text),
                    context.column_span,
                    context.row_span,
                )
            )
            for below in range(row + 1, row + context.row_span):
                claimed[below].append(
                    (context.column, context.column + context.column_span)
                )
            column = context.column + context.column_span
        rows.append(Row(by_row[row][0].table_cell.is_header, tuple(placed)))
    return tuple(rows)


def c1_only(text: str, fixture: str) -> list[Element]:
    """The projection with C1 alone: C1 runs first, so this isolates its effect."""
    blocks, _ = compensate(to_blocks(*walk(text)), rules=("C1",))
    document, elements = build(
        blocks,
        source_document_id=fixture,
        canonicalization_version=CANONICALIZATION_VERSION,
    )
    return project(document.canonical_text, elements)[0]


@dataclass
class Fixture:
    fixture: str
    klass: str
    gold: dict
    result: Canonicalized
    blocks: list[Block]
    frozen: FixtureScore
    c1_only: FixtureScore
    walker1: FixtureScore


def load_fixture(fixture: str, klass: str) -> Fixture:
    directory = FIXTURES / fixture
    raw = (directory / "source.html").read_bytes()
    gold, source = load_gold(directory), SourceText(raw)
    result = canonicalize(raw, source_document_id=fixture, media_type="text/html")
    if not isinstance(result, Canonicalized):
        raise SystemExit(f"{fixture}: {result.reason.value}: {result.detail}")
    text = decode_html_bytes(raw).text
    blocks, _ = compensate(to_blocks(*walk(text)))
    projection, _ = project(result.document.canonical_text, result.elements)
    return Fixture(
        fixture=fixture,
        klass=klass,
        gold=gold,
        result=result,
        blocks=blocks,
        frozen=score_fixture(gold, source, frozen.parse(frozen_decode(raw).text)),
        c1_only=score_fixture(gold, source, c1_only(text, fixture)),
        walker1=score_fixture(gold, source, projection),
    )


def load_fixtures() -> list[Fixture]:
    manifest = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))
    return [
        load_fixture(entry["fixture_id"], entry["primary_class"])
        for entry in sorted(manifest["fixtures"], key=lambda e: e["fixture_id"])
    ]


def pooled(fixtures: Sequence[Fixture], stage: str, metric: str) -> tuple[int, int]:
    counts = [getattr(f, stage).counts[metric] for f in fixtures]
    return sum(c[0] for c in counts), sum(c[1] for c in counts)


def verdict(metric: str, before: tuple[int, int], after: tuple[int, int]) -> str:
    """``same``, ``better``, ``worse``, or ``denominator`` when the counts are not
    comparable."""
    if before[1] != after[1]:
        return "denominator"
    if before[0] == after[0]:
        return "same"
    better = after[0] > before[0] if metric == "coverage" else after[0] < before[0]
    return "better" if better else "worse"


def regression_rows(fixtures: Sequence[Fixture]) -> list[dict]:
    """One row per class and metric, with C1's and C2-C5's verdicts."""
    classes = sorted({f.klass for f in fixtures})
    rows = []
    for klass in classes:
        members = [f for f in fixtures if f.klass == klass]
        for metric in COMPARED:
            before = pooled(members, "frozen", metric)
            middle = pooled(members, "c1_only", metric)
            after = pooled(members, "walker1", metric)
            rows.append(
                {
                    "class": klass,
                    "metric": metric,
                    "frozen": before,
                    "c1_only": middle,
                    "walker1": after,
                    "c1": verdict(metric, before, middle),
                    "c2_c5": verdict(metric, middle, after),
                }
            )
    return rows


def excerpt(text: str) -> str:
    text = " ".join(text.split()).replace("|", "\\|")
    return text if len(text) <= EXCERPT else text[: EXCERPT - 3] + "..."


def page_artifact_rows(fixture: Fixture) -> tuple[list[dict], list[dict]]:
    """Per distinct gold anchor, and the page artifacts that match no gold anchor.

    Gold anchors need not be unique, so they are counted as a multiset; no gold block
    is ever placed at a first match.
    """
    anchors = Counter(
        block["start"]
        for block in fixture.gold["blocks"]
        if block["type"] == "page_artifact"
    )
    text = fixture.result.document.canonical_text
    parents = {e.parent_id for e in fixture.result.elements if e.parent_id}
    blocks = [
        (element, primary_space(element.span.slice_of(text)))
        for element in fixture.result.elements
        if element.type not in (ElementType.SENTENCE, ElementType.TABLE_CELL)
        and not (element.type is ElementType.OTHER and element.element_id in parents)
    ]
    rules = defaultdict(set)
    for block in fixture.blocks:
        if block.retyped_by and block.type == "page_artifact":
            rules[block.text].add(block.retyped_by)
    rows, matched = [], set()
    for anchor, gold_count in sorted(anchors.items()):
        key = primary_space(anchor)
        starting = [element for element, space in blocks if space.startswith(key)]
        typed = [e for e in starting if e.type is ElementType.PAGE_ARTIFACT]
        matched.update(e.element_id for e in typed)
        rows.append(
            {
                "anchor": anchor,
                "gold": gold_count,
                "canonical": len(starting),
                "page_artifact": len(typed),
            }
        )
    unmatched = []
    for element, _ in blocks:
        if (
            element.type is ElementType.PAGE_ARTIFACT
            and element.element_id not in matched
        ):
            unit = element.span.slice_of(text)
            unmatched.append(
                {
                    "element_id": element.element_id,
                    "text": unit,
                    "rules": ", ".join(sorted(rules.get(unit, set()))),
                }
            )
    return rows, unmatched


def mask_rows(fixture: Fixture) -> tuple[list[dict], list[dict]]:
    """The fixture's masks, and every unmasked narrative block the gate flags."""
    text = fixture.result.document.canonical_text
    types = {e.span: e.type for e in fixture.result.elements if e.type in NARRATIVE}
    masks = [
        {
            "category": mask.category.value,
            "type": types[mask.span].value,
            "text": mask.span.slice_of(text),
        }
        for mask in fixture.result.masked.masks
    ]
    masked = {mask.span for mask in fixture.result.masked.masks}
    flagged = [
        {"type": element.type.value, "text": element.span.slice_of(text)}
        for element in fixture.result.elements
        if element.type in NARRATIVE
        and element.span not in masked
        and FLAG.search(element.span.slice_of(text))
    ]
    return masks, flagged


def render(fixtures: Sequence[Fixture]) -> str:
    lines = [
        "# walker-1: re-score, page artifacts, and masks",
        "",
        "Generated by `expirements/parser-fidelity/walker1_report.py`; do not edit.",
        "Development-set numbers: the fixtures were Stage 1's test set (SC2).",
        "",
        "## Re-score by class",
        "",
        "Exact counts, pooled over each class's fixtures, as numerator/denominator:",
        "coverage counts found blocks, and every other metric counts losses. The C1",
        "column scores the projection with C1 alone, which isolates C1's effect,",
        "because C1 runs first; the last column scores the whole of walker-1.",
        "",
        "| Class | Metric | Frozen walker | C1 only | walker-1 | C1 | C2-C5 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    rows = regression_rows(fixtures)
    for row in rows:
        lines.append(
            f"| {row['class']} | {row['metric']} | {_pair(row['frozen'])}"
            f" | {_pair(row['c1_only'])} | {_pair(row['walker1'])}"
            f" | {row['c1']} | {row['c2_c5']} |"
        )
    c1_worse = [r for r in rows if r["c1"] in ("worse", "denominator")]
    gate = [r for r in rows if r["c2_c5"] in ("worse", "denominator")]
    lines += ["", "### Verdict", ""]
    lines.append(
        "- C1 regressions, accepted because R4.2 requires C1 and outranks a ranked"
        f" metric: {_list(c1_worse)}."
    )
    lines.append(f"- C2-C5 regressions, for the review gate: {_list(gate)}.")
    lines += ["", "## Changes by fixture and block", ""]
    for fixture in fixtures:
        changes = []
        for kind in RESIDUALS:
            before = set(fixture.frozen.residual.get(kind, []))
            after = set(fixture.walker1.residual.get(kind, []))
            for block in sorted(after - before):
                changes.append(f"  - {kind}: now {block}")
            for block in sorted(before - after):
                changes.append(f"  - {kind}: no longer {block}")
        lines.append(f"- `{fixture.fixture}` ({fixture.klass}): {len(changes)} changes")
        lines += changes
    lines += [
        "",
        "## Page artifacts",
        "",
        "For each distinct gold `page_artifact` anchor: the gold blocks with it, the",
        "canonical blocks whose text begins with it (primary space), and how many of",
        "those are typed `page_artifact`. Then the page artifacts no anchor matches.",
    ]
    totals = Counter()
    for fixture in fixtures:
        anchors, unmatched = page_artifact_rows(fixture)
        lines += ["", f"### `{fixture.fixture}`", ""]
        if anchors:
            lines += [
                "| Gold anchor | Gold | Canonical | Typed |",
                "| --- | --- | --- | --- |",
            ]
        for row in anchors:
            totals.update(
                gold=row["gold"],
                canonical=row["canonical"],
                page_artifact=row["page_artifact"],
            )
            lines.append(
                f"| {excerpt(row['anchor'])} | {row['gold']} | {row['canonical']}"
                f" | {row['page_artifact']} |"
            )
        if not anchors:
            lines.append("No gold page artifacts.")
        lines += ["", f"Page artifacts matching no gold anchor: {len(unmatched)}."]
        if unmatched:
            lines += ["", "| Element | Rule | Text |", "| --- | --- | --- |"]
            lines += [
                f"| `{row['element_id']}` | {row['rules']} | {excerpt(row['text'])} |"
                for row in unmatched
            ]
    lines += [
        "",
        (
            f"Totals: {totals['gold']} gold page-artifact blocks;"
            f" {totals['canonical']} canonical blocks begin with their anchors;"
            f" {totals['page_artifact']} of those are typed `page_artifact`."
        ),
        "",
        "## Masks (policy boilerplate/1)",
        "",
        "Each fixture's masks, then every unmasked heading, paragraph, list item, or",
        "footnote matching `forward\\W?looking` or `non\\W?gaap`, case-insensitively.",
    ]
    for fixture in fixtures:
        masks, flagged = mask_rows(fixture)
        lines += ["", f"### `{fixture.fixture}`", ""]
        if masks:
            lines += ["| Category | Type | Text |", "| --- | --- | --- |"]
            lines += [
                f"| {m['category']} | {m['type']} | {excerpt(m['text'])} |"
                for m in masks
            ]
        else:
            lines.append("No masks.")
        lines += ["", f"Flagged unmasked blocks: {len(flagged)}."]
        if flagged:
            lines += ["", "| Type | Text |", "| --- | --- |"]
            lines += [f"| {f['type']} | {excerpt(f['text'])} |" for f in flagged]
    return "\n".join(lines) + "\n"


def _pair(pair: tuple[int, int]) -> str:
    return f"{pair[0]}/{pair[1]}"


def _list(rows: Sequence[dict]) -> str:
    if not rows:
        return "none"
    return "; ".join(f"{row['class']} {row['metric']}" for row in rows)


def main() -> int:
    REPORT.write_text(render(load_fixtures()), encoding="utf-8", newline="\n")
    print(f"wrote {REPORT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
