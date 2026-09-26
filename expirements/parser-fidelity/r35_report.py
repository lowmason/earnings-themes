"""R3.5's text-fidelity report, plan A's leg (Stage 3 spec: R3.5 fidelity check).

    uv run --locked --all-packages python expirements/parser-fidelity/r35_report.py

Writes docs/verification/R3.5-text-fidelity.md. The references are the committed gold,
marked from the browser rendering (anchors and table header texts), and the <sup> runs
html.parser reads from each source.html; never lxml or the walker. Comparisons run in
NFC with whitespace runs collapsed (earnings_ingestion.canonical.fidelity). The report
counts and lists, and sets no threshold (R13.1). Plan B adds the second leg: full
browser captures and the user's rendered copies.
"""

from __future__ import annotations

import unicodedata
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from earnings_core import DocumentElement, ElementType
from earnings_ingestion.canonical import Canonicalized
from earnings_ingestion.canonical.fidelity import (
    SCALE_PHRASES,
    SUP_CLASSES,
    classify_run,
    comparison_space,
    joined_to_text,
    locate_run,
    non_ascii,
    read_source,
    scale_counts,
    signed_figures,
)
from pf_decode import decode_html_bytes
from pf_paths import FIXTURES, REPO_ROOT
from pf_space import primary_space
from score import CandidateText, match_block, scored_blocks
from validate_gold import SourceText
from walker1_report import Fixture, load_fixtures, project

REPORT = REPO_ROOT / "docs" / "verification" / "R3.5-text-fidelity.md"
CATEGORIES = (
    "Unicode",
    "Numeric signs",
    "Scale",
    "Superscripts",
    "Footnotes",
    "Table headings",
)
NO_INSTANCES = "no instances in sample"


def references(gold: dict) -> tuple[list[str], list[str]]:
    """The gold's anchors (start, end, after, and table cell texts) and its table
    header texts, from anchorable blocks only."""
    anchors: list[str] = []
    headers: list[str] = []
    for block in gold["blocks"]:
        if block.get("unanchorable"):
            continue
        anchors += [block[key] for key in ("start", "end", "after") if key in block]
        anchors += [cell["text"] for cell in block.get("cells", [])]
        headers += block.get("headers", [])
    return anchors, headers


@dataclass
class Counts:
    """One fixture's counts in every category."""

    fixture: str
    non_ascii: Counter
    non_ascii_found: Counter
    replacement_characters: int
    signed: int
    signed_found: int
    signed_missing: list[str]
    scale_references: Counter
    scale_canonical: Counter
    sup_classes: Counter
    sup_other: list[str]
    sup_located: int
    sup_unlocatable: list[str]
    sup_hazards: list[str]
    footnotes: int
    footnotes_found: int
    footnotes_typed: int
    footnotes_merged: int
    gold_tables: int
    tables_located: int
    headers: int
    headers_lost: int
    headers_in_header_cell: int
    headers_in_other_cell: int
    headers_in_no_cell: int


def count(fixture: Fixture) -> Counts:
    raw = (FIXTURES / fixture.fixture / "source.html").read_bytes()
    canonical = comparison_space(fixture.result.document.canonical_text)
    anchors, headers = references(fixture.gold)

    characters, found = Counter(), Counter()
    for reference in (comparison_space(text) for text in anchors + headers):
        chars = non_ascii(reference)
        characters.update(chars)
        if chars and reference in canonical:
            found.update(chars)

    figures = [f for a in anchors for f in signed_figures(comparison_space(a))]
    missing = [figure for figure in figures if figure not in canonical]

    scale_references = Counter()
    for reference in anchors + headers:
        scale_references.update(scale_counts(comparison_space(reference)))

    source = read_source(decode_html_bytes(raw).text)
    classes, other, unlocatable, hazards, located = Counter(), [], [], [], 0
    for start, end in source.sup_runs:
        run = source.text[start:end]
        run_class = classify_run(run)
        classes[run_class] += 1
        if run_class == "other":
            other.append(run)
        if run_class == "empty":
            continue
        position = locate_run(canonical, source, start, end)
        if position is None:
            unlocatable.append(run)
            continue
        located += 1
        if run_class == "bare_digits" and joined_to_text(canonical, position):
            hazards.append(canonical[max(0, position - 20) : position + len(run)])

    dump, sources = project(
        fixture.result.document.canonical_text, fixture.result.elements
    )
    text = CandidateText(dump)
    gold_source = SourceText(raw)
    blocks = scored_blocks(fixture.gold)
    footnote_results = [
        match_block(block, text, gold_source)
        for block in blocks
        if block["type"] == "footnote"
    ]
    typed = sum(
        1
        for result in footnote_results
        if result.found and dump[result.start.position[0]].type == "footnote"
    )
    table_results = [
        match_block(block, text, gold_source)
        for block in blocks
        if block["type"] == "table"
    ]
    placement = Counter()
    for result in table_results:
        if not result.found:
            continue
        tables = [
            sources[i] for i in sorted(result.elements) if dump[i].type == "table"
        ]
        for header in result.block["headers"]:
            placement[header_placement(header, tables, fixture.result)] += 1

    merged, footnotes_found = fixture.walker1.counts["footnote_merging"]
    headers_lost, header_total = fixture.walker1.counts["header_table"]
    return Counts(
        fixture=fixture.fixture,
        non_ascii=characters,
        non_ascii_found=found,
        replacement_characters=fixture.result.manifest.replacement_characters,
        signed=len(figures),
        signed_found=len(figures) - len(missing),
        signed_missing=missing,
        scale_references=scale_references,
        scale_canonical=Counter(scale_counts(canonical)),
        sup_classes=classes,
        sup_other=other,
        sup_located=located,
        sup_unlocatable=unlocatable,
        sup_hazards=hazards,
        footnotes=sum(1 for b in fixture.gold["blocks"] if b["type"] == "footnote"),
        footnotes_found=footnotes_found,
        footnotes_typed=typed,
        footnotes_merged=merged,
        gold_tables=sum(1 for b in fixture.gold["blocks"] if b["type"] == "table"),
        tables_located=sum(1 for result in table_results if result.found),
        headers=header_total,
        headers_lost=headers_lost,
        headers_in_header_cell=placement["header cell"],
        headers_in_other_cell=placement["other cell"],
        headers_in_no_cell=placement["no cell"],
    )


def header_placement(
    header: str, tables: Sequence[DocumentElement], result: Canonicalized
) -> str:
    """Where a found table's header text sits: in a header cell, in another cell, or in
    no cell (a C1 table has none)."""
    text = result.document.canonical_text
    ids = {table.element_id for table in tables}
    key = primary_space(header)
    cells = [
        e
        for e in result.elements
        if e.type is ElementType.TABLE_CELL
        and e.parent_id in ids
        and key in primary_space(e.span.slice_of(text))
    ]
    if any(cell.table_cell and cell.table_cell.is_header for cell in cells):
        return "header cell"
    return "other cell" if cells else "no cell"


def instances(value: int) -> str:
    return f"**Instances:** {value if value else NO_INSTANCES}"


def render(counts: Sequence[Counts]) -> str:
    total = Counter()
    for c in counts:
        total.update(
            non_ascii=sum(c.non_ascii.values()),
            non_ascii_found=sum(c.non_ascii_found.values()),
            replacement=c.replacement_characters,
            signed=c.signed,
            signed_found=c.signed_found,
            sup=sum(c.sup_classes.values()),
            sup_located=c.sup_located,
            footnotes=c.footnotes,
            footnotes_found=c.footnotes_found,
            footnotes_typed=c.footnotes_typed,
            footnotes_merged=c.footnotes_merged,
            gold_tables=c.gold_tables,
            tables_located=c.tables_located,
            headers=c.headers,
            headers_lost=c.headers_lost,
            header_cell=c.headers_in_header_cell,
            other_cell=c.headers_in_other_cell,
            no_cell=c.headers_in_no_cell,
        )
    characters = Counter()
    characters_found = Counter()
    for c in counts:
        characters.update(c.non_ascii)
        characters_found.update(c.non_ascii_found)
    lines = [
        "# R3.5 text fidelity: plan A's leg",
        "",
        "Generated by `expirements/parser-fidelity/r35_report.py`; do not edit. Plan B",
        "adds the second leg, from full browser captures and the user's rendered copies,",
        "and the report is final only then (Stage 3 spec: R3.5 fidelity check).",
        "",
        "- **References.** The committed gold, marked from the browser rendering: its",
        "  anchors (start, end, after, and table cell texts) and table header texts,",
        "  from anchorable blocks; and the `<sup>` runs `html.parser` reads from each",
        "  `source.html`. Never lxml or the walker.",
        "- **Comparison space.** NFC with whitespace runs collapsed, never NFKC.",
        "- **No thresholds.** The report counts and lists (R13.1). These are",
        "  development-set numbers: the fixtures were Stage 1's test set.",
        "",
        "## Unicode",
        "",
        instances(total["non_ascii"]),
        "",
        f"- Non-ASCII characters in the references: {total['non_ascii']}.",
        (
            "- Of those, in references the canonical text contains verbatim:"
            f" {total['non_ascii_found']}."
        ),
        (
            "- U+FFFD characters in the canonical text, from the manifests:"
            f" {total['replacement']}."
        ),
        "",
        "The spec expected no instances, because the fixtures' bytes are ASCII. Their",
        "character references decode to non-ASCII characters, so the gold has real",
        "instances. V9's synthetic cases, in",
        "`packages/earnings-ingestion/tests/test_normalize.py`, still cover what the",
        "sample lacks.",
    ]
    if characters:
        lines += [
            "",
            "| Character | Name | In references | Found |",
            "| --- | --- | --- | --- |",
        ]
        for char, number in sorted(characters.items()):
            name = unicodedata.name(char, "UNNAMED")
            lines.append(
                f"| U+{ord(char):04X} | {name} | {number} | {characters_found[char]} |"
            )
    lines += [
        "",
        "## Numeric signs",
        "",
        instances(total["signed"]),
        "",
        f"- Signed figures in the gold anchors: {total['signed']}.",
        f"- Found with the sign intact: {total['signed_found']}.",
    ]
    missing = [(c.fixture, figure) for c in counts for figure in c.signed_missing]
    if missing:
        lines += ["", "| Fixture | Figure not found |", "| --- | --- |"]
        lines += [f"| `{fixture}` | {figure} |" for fixture, figure in missing]
    scale_total = sum(sum(c.scale_references.values()) for c in counts)
    lines += [
        "",
        "## Scale",
        "",
        instances(scale_total),
        "",
        "| Phrase | In references | In canonical text |",
        "| --- | --- | --- |",
    ]
    for phrase in SCALE_PHRASES:
        in_references = sum(c.scale_references[phrase] for c in counts)
        in_canonical = sum(c.scale_canonical[phrase] for c in counts)
        lines.append(f"| {phrase} | {in_references} | {in_canonical} |")
    hazards = [(c.fixture, h) for c in counts for h in c.sup_hazards]
    unlocatable = [(c.fixture, run) for c in counts for run in c.sup_unlocatable]
    lines += [
        "",
        "## Superscripts",
        "",
        instances(total["sup"]),
        "",
        f"- `<sup>` runs: {total['sup']}.",
        f"- Located: {total['sup_located']}. Empty runs have nothing to locate.",
        f"- Unlocatable: {len(unlocatable)}.",
        f"- Bare-digit runs joined to text, the fidelity hazard: {len(hazards)}.",
        "",
        "The hazard is tested synthetically, in",
        "`packages/earnings-ingestion/tests/test_fidelity.py`, and watched on Stage 5's",
        "pilot releases.",
        "",
        "| Class | Runs |",
        "| --- | --- |",
    ]
    for run_class in SUP_CLASSES:
        lines.append(
            f"| {run_class} | {sum(c.sup_classes[run_class] for c in counts)} |"
        )
    other = [(c.fixture, run) for c in counts for run in c.sup_other]
    if other:
        lines += ["", "| Fixture | Run classed other |", "| --- | --- |"]
        lines += [f"| `{fixture}` | {run!r} |" for fixture, run in other]
    if unlocatable:
        lines += ["", "| Fixture | Unlocatable run |", "| --- | --- |"]
        lines += [f"| `{fixture}` | {run!r} |" for fixture, run in unlocatable]
    if hazards:
        lines += ["", "| Fixture | Hazard |", "| --- | --- |"]
        lines += [f"| `{fixture}` | {text!r} |" for fixture, text in hazards]
    lines += [
        "",
        "## Footnotes",
        "",
        instances(total["footnotes"]),
        "",
        f"- Gold footnote blocks: {total['footnotes']}.",
        (
            "- Found by the frozen scorer on the re-score's projection:"
            f" {total['footnotes_found']}."
        ),
        f"- Typed `footnote`: {total['footnotes_typed']}.",
        (
            "- Merged into another element, the scorer's footnote-merging count:"
            f" {total['footnotes_merged']}."
        ),
        "",
        "## Table headings",
        "",
        instances(total["headers"]),
        "",
        f"- Gold tables: {total['gold_tables']}.",
        f"- Located by their anchors: {total['tables_located']}. The rest are",
        "  unlocated, as in V2.",
        f"- Header texts of located tables: {total['headers']}.",
        f"  - In a header cell: {total['header_cell']}.",
        f"  - In another cell: {total['other_cell']}.",
        f"  - In no cell of its table: {total['no_cell']}. Every header text of a C1",
        "    table lands here, since a C1 table has no cells.",
        f"- Lost, the scorer's table-header count: {total['headers_lost']}.",
        "",
        "## By fixture",
        "",
        "Each entry is a count out of a total:",
        "",
        "- **Non-ASCII:** characters found identically, out of those in the",
        "  references.",
        "- **Signed:** figures found with the sign intact.",
        "- **Sup runs:** runs located.",
        "- **Footnotes:** gold footnotes typed `footnote`.",
        "- **Header texts:** header texts of located tables that sit in a header cell.",
        "",
        "| Fixture | Non-ASCII | Signed | Sup runs | Footnotes | Header texts |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for c in counts:
        lines.append(
            f"| `{c.fixture}` | {sum(c.non_ascii_found.values())}/"
            f"{sum(c.non_ascii.values())} | {c.signed_found}/{c.signed}"
            f" | {c.sup_located}/{sum(c.sup_classes.values())}"
            f" | {c.footnotes_typed}/{c.footnotes}"
            f" | {c.headers_in_header_cell}/{c.headers} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    counts = [count(fixture) for fixture in load_fixtures()]
    REPORT.write_text(render(counts), encoding="utf-8", newline="\n")
    print(f"wrote {REPORT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
