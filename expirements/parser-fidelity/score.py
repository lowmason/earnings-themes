"""Score candidate dumps against the gold (spec: Metrics). Standard library only.

    uv run --locked --all-packages python expirements/parser-fidelity/score.py

Reads each candidate's first fixture dump (data/runs/parser-fidelity/fixtures/), the gold,
and the manifest; writes data/runs/parser-fidelity/scores/scores.json and metrics.md.
All matching is exact substring search in the primary space, or, for text-block anchors
only, the fallback space when the anchor's fallback form occurs exactly once in the
document and exactly once in the candidate's text.
"""

from __future__ import annotations

import itertools
import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import tomllib
from pf_dump import Element, Row, read_dump
from pf_paths import FIXTURES, RUNS
from pf_space import fallback_space, find_all, primary_space
from pf_text import SpaceText, build_space_text
from run_candidates import CANDIDATES
from validate_gold import TEXT_TYPES, SourceText, load_gold

RANKED = ("coverage", "footnote_merging", "reading_order", "header_loss")
COUNTED = ("coverage", "footnote_merging", "reading_order", "header_section", "header_table", "split", "other_merges",
           "duplication", "footnotes_in_tables", "cell_association")  # fmt: skip
BODY_TYPES = frozenset({"heading", "paragraph", "list_item"})
ROLES = ("corner", "right", "below")


@dataclass(frozen=True)
class Match:
    found: bool
    altered: bool = False
    duplicated: bool = False
    position: tuple[int, int] | None = (
        None  # (element index, offset in element) of the first character
    )
    elements: frozenset[int] = (
        frozenset()
    )  # elements the block's own portion of the match overlaps


NOT_FOUND = Match(False)


class CandidateText:
    def __init__(self, elements: list[Element]) -> None:
        pieces = [element.text for element in elements]
        self.elements = elements
        self.primary: SpaceText = build_space_text(pieces, "primary")
        self.fallback: SpaceText = build_space_text(pieces, "fallback")


def _located(
    space: SpaceText, start: int, length: int, own: int, **flags: bool
) -> Match:
    covered = space.origins[start : start + (own or length)]
    return Match(
        True,
        position=space.origins[start],
        elements=frozenset(o[0] for o in covered),
        **flags,
    )


def match_anchor(
    text: CandidateText,
    source: SourceText,
    anchor: str,
    own: str | None = None,
    fallback: bool = True,
) -> Match:
    """Find ``anchor``; ``own`` is the leading part that belongs to the block (for ``after`` blocks)."""
    form = primary_space(anchor)
    if not form:
        return NOT_FOUND
    hits = find_all(text.primary.text, form)
    if hits:
        own_length = len(primary_space(own)) if own is not None else len(form)
        return _located(
            text.primary, hits[0], len(form), own_length, duplicated=len(hits) > 1
        )
    if not fallback:
        return NOT_FOUND
    form2 = fallback_space(anchor)
    if not form2 or source.count_fallback(form2) != 1:
        return NOT_FOUND
    hits2 = find_all(text.fallback.text, form2)
    if len(hits2) != 1:
        return NOT_FOUND
    own_length = len(fallback_space(own)) if own is not None else len(form2)
    return _located(text.fallback, hits2[0], len(form2), own_length, altered=True)


@dataclass
class BlockResult:
    block: dict
    anchors: dict[
        str, Match
    ]  # the block's own anchors: start[, end] or start+after; roles for tables

    @property
    def id(self) -> str:
        return self.block["id"]

    @property
    def start(self) -> Match:
        return (
            self.anchors["start"]
            if "start" in self.anchors
            else self.anchors["start+after"]
        )

    @property
    def kind(self) -> str:
        return self.block["type"]

    @property
    def found(self) -> bool:
        return all(match.found for match in self.anchors.values())

    @property
    def elements(self) -> frozenset[int]:
        return frozenset().union(
            *(m.elements for m in self.anchors.values() if m.found)
        )


def match_block(block: dict, text: CandidateText, source: SourceText) -> BlockResult:
    if block["type"] == "table":
        cells = {cell["role"]: cell["text"] for cell in block["cells"]}
        return BlockResult(
            block,
            {
                role: match_anchor(text, source, cells[role], fallback=False)
                for role in ROLES
            },
        )
    if "after" in block:
        combined = match_anchor(
            text, source, block["start"] + block["after"], own=block["start"]
        )
        return BlockResult(block, {"start+after": combined})  # its end is its start
    anchors = {"start": match_anchor(text, source, block["start"])}
    if "end" in block:
        anchors["end"] = match_anchor(text, source, block["end"])
    return BlockResult(block, anchors)


def scored_blocks(gold: dict) -> list[dict]:
    return [
        b
        for b in gold["blocks"]
        if b["type"] != "page_artifact" and not b.get("unanchorable")
    ]


@dataclass
class FixtureScore:
    counts: dict[str, list[int]] = field(
        default_factory=dict
    )  # metric -> [numerator, denominator]
    altered: list[str] = field(default_factory=list)
    residual: dict[str, list[str]] = field(default_factory=dict)
    unanchorable: int = 0
    exposes_cells: bool = False


def _grid_positions(rows: tuple[Row, ...]) -> list[list[tuple[int, int]]]:
    """Column span [start, end) of every cell, with colspan and rowspan expanded."""
    occupied: set[tuple[int, int]] = set()
    positions = []
    for r, row in enumerate(rows):
        column, spans = 0, []
        for cell in row.cells:
            while (r, column) in occupied:
                column += 1
            spans.append((column, column + cell.colspan))
            occupied.update(
                (r + dr, column + dc)
                for dr in range(cell.rowspan)
                for dc in range(cell.colspan)
            )
            column += cell.colspan
        positions.append(spans)
    return positions


def cell_headers(rows: tuple[Row, ...], cell_text: str) -> tuple[str, str] | None:
    """(row header, column header path) of the grid cell holding ``cell_text``, by grid geometry.

    The row header is the first non-empty cell to its left in its row; the column header path
    joins, top to bottom, the non-empty header-row cells whose columns overlap the cell's.
    """
    target = primary_space(cell_text)
    positions = _grid_positions(rows)
    located = [
        (r, k)
        for r, row in enumerate(rows)
        for k, cell in enumerate(row.cells)
        if primary_space(cell.text) == target
    ]
    located = located or [
        (r, k)
        for r, row in enumerate(rows)
        for k, cell in enumerate(row.cells)
        if target in primary_space(cell.text)
    ]
    if not located:
        return None
    r, k = located[0]
    start, end = positions[r][k]
    row_header = next(
        (
            c.text
            for c, (s, _) in zip(rows[r].cells, positions[r], strict=True)
            if s < start and c.text.strip()
        ),
        "",
    )
    path = [
        cell.text
        for rr, row in enumerate(rows)
        if row.header and rr != r
        for cell, (s, e) in zip(row.cells, positions[rr], strict=True)
        if s < end and e > start and cell.text.strip()
    ]
    return row_header, " ".join(path)


def _count(score: FixtureScore, metric: str, numerator: int, denominator: int) -> None:
    score.counts[metric] = [numerator, denominator]


def score_fixture(
    gold: dict, source: SourceText, elements: list[Element] | None
) -> FixtureScore:
    elements = elements or []
    text = CandidateText(elements)
    results = [match_block(block, text, source) for block in scored_blocks(gold)]
    score = FixtureScore(
        unanchorable=sum(1 for b in gold["blocks"] if b.get("unanchorable"))
    )
    score.exposes_cells = any(e.rows is not None for e in elements)
    text_results = [r for r in results if r.kind in TEXT_TYPES]
    found = [r for r in results if r.found]

    _count(score, "coverage", len(found), len(results))
    score.residual["missed"] = [r.id for r in results if not r.found]

    body_elements = frozenset().union(
        *(r.elements for r in results if r.kind in BODY_TYPES)
    )
    footnotes = [r for r in found if r.kind == "footnote"]
    merged_notes = [r for r in footnotes if r.elements & body_elements]
    _count(score, "footnote_merging", len(merged_notes), len(footnotes))
    in_tables = [
        r for r in footnotes if any(elements[i].type == "table" for i in r.elements)
    ]
    _count(score, "footnotes_in_tables", len(in_tables), len(footnotes))

    sequence: list[tuple[str, tuple[int, int]]] = []
    for r in results:
        if r.kind == "table":
            sequence += [
                (f"{r.id}:{role}", r.anchors[role].position)
                for role in ROLES
                if r.anchors[role].found
            ]
        elif r.start.found:
            sequence.append((r.id, r.start.position))
    reversed_pairs = [
        f"{a}>{b}" for (a, pa), (b, pb) in itertools.pairwise(sequence) if pa > pb
    ]
    _count(score, "reading_order", len(reversed_pairs), max(len(sequence) - 1, 0))
    score.residual["misordered"] = reversed_pairs

    headings = [r for r in found if r.kind == "heading"]
    lost_headings = []
    for r in headings:
        home = r.start.position[0]
        shared = any(home in other.elements for other in results if other is not r)
        if elements[home].type != "heading" or shared:
            lost_headings.append(r.id)
    _count(score, "header_section", len(lost_headings), len(headings))
    lost_headers, header_total = [], 0
    for r in (r for r in found if r.kind == "table"):
        table_elements = sorted(i for i in r.elements if elements[i].type == "table")
        table_text = primary_space("".join(elements[i].text for i in table_elements))
        for header in r.block["headers"]:
            header_total += 1
            if not table_elements or primary_space(header) not in table_text:
                lost_headers.append(f"{r.id}:{header}")
    _count(score, "header_table", len(lost_headers), header_total)
    score.residual["header_lost"] = lost_headings + lost_headers

    found_text = [r for r in text_results if r.found]
    split = [r.id for r in found_text if len(r.elements) > 1]
    _count(score, "split", len(split), len(found_text))
    score.residual["split"] = split

    holders: dict[int, set[str]] = {}
    for r in results:
        if r.kind != "footnote":
            for index in r.elements:
                holders.setdefault(index, set()).add(r.id)
    merged_blocks = sorted(
        {block for ids in holders.values() if len(ids) > 1 for block in ids}
    )
    non_footnote_found = [r for r in found if r.kind != "footnote"]
    _count(score, "other_merges", len(merged_blocks), len(non_footnote_found))
    score.residual["merged"] = sorted({r.id for r in merged_notes} | set(merged_blocks))

    anchors = [m for r in results for m in r.anchors.values() if m.found]
    _count(score, "duplication", sum(m.duplicated for m in anchors), len(anchors))
    score.altered = sorted(
        f"{r.id}:{label}"
        for r in text_results
        for label, m in r.anchors.items()
        if m.found and m.altered
    )

    matched, cells_seen = 0, 0
    for r in (r for r in found if r.kind == "table"):
        for cell in r.block["cells"]:
            grids = [
                elements[i]
                for i in sorted(r.anchors[cell["role"]].elements)
                if elements[i].rows is not None
            ]
            if not grids:
                continue
            cells_seen += 1
            headers = cell_headers(grids[0].rows, cell["text"])
            if (
                headers
                and primary_space(cell["row_header"]) in primary_space(headers[0])
                and primary_space(cell["col_header"]) in primary_space(headers[1])
            ):
                matched += 1
    _count(score, "cell_association", matched, cells_seen)
    return score


def pool(scores: Iterable[FixtureScore]) -> dict:
    scores = list(scores)
    counts = {
        metric: [sum(s.counts[metric][i] for s in scores) for i in (0, 1)]
        for metric in COUNTED
    }
    pooled: dict = {"counts": counts, "altered": sum(len(s.altered) for s in scores)}
    pooled["unanchorable"] = sum(s.unanchorable for s in scores)
    pooled["exposes_cells"] = any(s.exposes_cells for s in scores)
    pooled["rates"] = rates(counts)
    return pooled


def _rate(pair: list[int]) -> float | None:
    return pair[0] / pair[1] if pair[1] else None


def rates(counts: dict[str, list[int]]) -> dict:
    out = {metric: _rate(counts[metric]) for metric in COUNTED}
    subrates = [
        out[m] for m in ("header_section", "header_table") if out[m] is not None
    ]
    out["header_loss"] = sum(subrates) / len(subrates) if subrates else None
    out["header_loss_n"] = counts["header_section"][1] + counts["header_table"][1]
    return out


def gold_structure(gold: dict) -> dict:
    """Element types and nesting observed in the gold (for Stage 2)."""
    blocks = gold["blocks"]
    placement = Counter()
    for index, block in enumerate(blocks):
        if block["type"] == "footnote":
            previous = next(
                (
                    b["type"]
                    for b in reversed(blocks[:index])
                    if b["type"] not in ("footnote", "page_artifact")
                ),
                "start",
            )
            placement[f"after {previous}"] += 1
    return {
        "types": dict(Counter(b["type"] for b in blocks)),
        "heading_levels": dict(
            Counter(
                str(b.get("level", "none")) for b in blocks if b["type"] == "heading"
            )
        ),
        "list_levels": dict(
            Counter(
                str(b.get("level", "none")) for b in blocks if b["type"] == "list_item"
            )
        ),
        "footnote_placement": dict(placement),
    }


def score_all(fixtures: Path = FIXTURES, runs: Path = RUNS) -> dict:
    manifest = tomllib.loads((fixtures / "manifest.toml").read_text(encoding="utf-8"))
    classes = {
        entry["fixture_id"]: entry["primary_class"] for entry in manifest["fixtures"]
    }
    report: dict = {"fixtures": {}, "classes": {}, "gold": {}}
    per_class: dict[str, dict[str, list[FixtureScore]]] = {}
    for fid, cls in sorted(classes.items()):
        gold = load_gold(fixtures / fid)
        source = SourceText((fixtures / fid / "source.html").read_bytes())
        report["gold"][fid] = gold_structure(gold)
        for name in CANDIDATES:
            dump = runs / "fixtures" / name / fid / "run1.json"
            score = score_fixture(
                gold, source, read_dump(dump) if dump.exists() else None
            )
            sidecar = dump.with_name("run1.sidecar.json")
            runtime = (
                json.loads(sidecar.read_text())["parse_seconds"]
                if sidecar.exists()
                else None
            )
            report["fixtures"].setdefault(fid, {})[name] = {
                "class": cls,
                "dump_present": dump.exists(),
                "counts": score.counts,
                "rates": rates(score.counts),
                "altered": score.altered,
                "residual": score.residual,
                "unanchorable": score.unanchorable,
                "exposes_cells": score.exposes_cells,
                "parse_seconds": runtime,
            }
            per_class.setdefault(cls, {}).setdefault(name, []).append(score)
    for cls, by_candidate in per_class.items():
        report["classes"][cls] = {
            name: pool(scores) for name, scores in by_candidate.items()
        }
    return report


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def render_markdown(report: dict) -> str:
    lines = ["# V2 metric tables (generated by score.py)", ""]
    for title, metric in (
        ("Block coverage (higher is better)", "coverage"),
        ("Footnote merging (lower is better)", "footnote_merging"),
        ("Reading-order corruption (lower is better)", "reading_order"),
        ("Header loss (lower is better)", "header_loss"),
    ):
        names = list(CANDIDATES)
        lines += [
            f"## {title}",
            "",
            "| class | " + " | ".join(names) + " |",
            "|---" * (len(names) + 1) + "|",
        ]
        for cls, by_candidate in sorted(report["classes"].items()):
            cells = []
            for name in names:
                pooled = by_candidate[name]
                if metric == "header_loss":
                    cells.append(
                        f"{_pct(pooled['rates']['header_loss'])} (n={pooled['rates']['header_loss_n']})"
                    )
                else:
                    num, den = pooled["counts"][metric]
                    cells.append(f"{_pct(pooled['rates'][metric])} ({num}/{den})")
            lines.append(f"| {cls} | " + " | ".join(cells) + " |")
        lines.append("")
    lines += ["## Diagnostics by class", ""]
    for cls, by_candidate in sorted(report["classes"].items()):
        lines += [
            f"### {cls}",
            "",
            "| candidate | altered | split | other merges | duplication | footnotes in tables | cell association | unanchorable |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for name, pooled in by_candidate.items():
            c = pooled["counts"]
            association = (
                f"{c['cell_association'][0]}/{c['cell_association'][1]}"
                if pooled["exposes_cells"]
                else "no cells exposed"
            )
            lines.append(
                f"| {name} | {pooled['altered']} | {c['split'][0]}/{c['split'][1]} | {c['other_merges'][0]}/{c['other_merges'][1]} "
                f"| {c['duplication'][0]}/{c['duplication'][1]} | {c['footnotes_in_tables'][0]}/{c['footnotes_in_tables'][1]} "
                f"| {association} | {pooled['unanchorable']} |"
            )
        lines.append("")
    lines += ["## Per-fixture detail", ""]
    for fid, by_candidate in sorted(report["fixtures"].items()):
        lines += [f"### `{fid}` ({next(iter(by_candidate.values()))['class']})", ""]
        lines += [
            "| candidate | coverage | footnote merging | reading order | header section | header table | runtime (s) | altered |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for name, result in by_candidate.items():
            c = result["counts"]
            cells = [
                f"{c[m][0]}/{c[m][1]}"
                for m in (
                    "coverage",
                    "footnote_merging",
                    "reading_order",
                    "header_section",
                    "header_table",
                )
            ]
            lines.append(
                f"| {name} | "
                + " | ".join(cells)
                + f" | {result['parse_seconds']} | {', '.join(result['altered']) or '-'} |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = score_all()
    out = RUNS / "scores"
    out.mkdir(parents=True, exist_ok=True)
    (out / "scores.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "metrics.md").write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"wrote {out / 'scores.json'} and {out / 'metrics.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
