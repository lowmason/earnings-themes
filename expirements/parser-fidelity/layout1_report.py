"""layout-1's pre-registered comparison (Stage 3 spec, Pre-registered comparison).

    uv run --locked --all-packages python expirements/parser-fidelity/layout1_report.py

Writes docs/verification/layout-1-comparison.md from the gold, walker-1's output, the
committed fixture captures in tests/fixtures/browser/, and layout1-units.toml. Three
configurations are projected to the dump format by walker1_report.project and scored
by the frozen score.py:

1. ``walker-1``: walker-1, with C1-C5;
2. ``layout-1``: layout-1's element stream, mapped onto walker-1's text, for every
   document;
3. ``fallback``: layout-1's stream for exactly the documents where walker-1's output
   fires a trigger (canonical/triggers.py), and walker-1's elsewhere.

The rules were fixed before any release was captured (plan 5, PB-14), and every
comparison is an exact count or an exact fraction:

- A targeted class is repaired when a configuration loses strictly fewer of its units
  than walker-1. A heading unit is lost when it is missed or in the scorer's
  header_lost; a prose unit, when it is missed or any element it matches is a table.
- A regression is a metric worse than walker-1's by more than 1/n in a fixture class,
  n being walker-1's denominator there. A metric whose denominator is zero on one side
  only is not comparable, and counts as a regression.
- The promotion rule allows a configuration only when it repairs a targeted class
  with no regression.

These are development-set numbers: the fixtures were Stage 1's test set (SC2).
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction

import tomllib
from earnings_core import DocumentElement, ElementType
from earnings_ingestion.browser.records import RenderedCapture
from earnings_ingestion.browser.serialize import from_capture_json
from earnings_ingestion.canonical import Canonicalized, canonicalize
from earnings_ingestion.canonical.triggers import fired
from earnings_ingestion.layout import LayoutExtraction, LayoutExtractor
from layout1_units import CLASSES, Unit, load_units
from pf_dump import Element
from pf_paths import FIXTURES, HARNESS, MANIFEST, REPO_ROOT
from score import CandidateText, FixtureScore, match_block, score_fixture
from validate_gold import SourceText, load_gold
from walker1_report import excerpt, project

REPORT = REPO_ROOT / "docs" / "verification" / "layout-1-comparison.md"
CAPTURES = REPO_ROOT / "tests" / "fixtures" / "browser"
PREREGISTERED = HARNESS / "layout1-preregistered.toml"
CONFIGURATIONS = ("walker-1", "layout-1", "fallback")
CANDIDATES = CONFIGURATIONS[1:]
METRICS = (
    ("block coverage", "coverage"),
    ("reading order", "reading_order"),
    ("heading loss", "header_section"),
    ("footnote merging", "footnote_merging"),
    ("table-header retention", "header_table"),
    ("cell association", "cell_association"),
    ("altered anchors", "altered"),
    ("alignment failures", "alignment"),
)
"""The spec's eight metrics: its name, and the count it reads. Table-header retention
counts header texts lost; altered anchors count over the scored gold blocks;
alignment failures count over layout-1's units, and walker-1 aligns nothing."""
HIGHER_BETTER = frozenset({"coverage", "cell_association"})
CLASS_NAMES = {
    "styled_headings": "1. headings typed paragraph by W12",
    "prose_in_tables": "2. prose inside data tables",
    "stylesheet_hidden": "3. content hidden by stylesheets",
}


@dataclass(frozen=True)
class Probe:
    """One of plan 4's open review-gate findings, found by its elements' text."""

    finding: str
    fixture: str | None
    """``None``: every fixture."""
    pattern: str
    """Matched against a whole element's text."""


PROBES = (
    Probe(
        "NHI's headline",
        "0000877860-13-000100_ex-99-1",
        r"NHI Reports 17\.2% Increase in Third Quarter Normalized FFO",
    ),
    Probe(
        "Becton Dickinson's statement titles",
        "0000010795-22-000014_ex-99-1",
        r"BECTON DICKINSON AND COMPANY",
    ),
    Probe("End marks", None, r"[#*]+(?: [#*]+)*"),
    Probe(
        "Ball's numbered running heads",
        "0000009389-10-000004_ex-99-1",
        r"Ball Corp - \d+",
    ),
    Probe(
        "FMC's numbered running heads",
        "0000037785-14-000003_ex-99-1",
        r"Page \d+/ FMC Corporation Announces Fourth Quarter Results",
    ),
    Probe(
        "Becton Dickinson's non-GAAP footnotes",
        "0000010795-22-000014_ex-99-1",
        r"1 ?Represents a non-GAAP financial measure.*",
    ),
    Probe(
        "Southwestern Energy's forward-looking-statements continuation",
        "0000007332-09-000032_ex-99",
        r"rates and the ability of the company.s lenders.*",
    ),
)


@dataclass
class Fixture:
    """One release under the three configurations."""

    fixture: str
    klass: str
    gold: dict
    source: SourceText
    result: Canonicalized
    capture: RenderedCapture
    extraction: LayoutExtraction
    triggers: tuple[str, ...]
    elements: dict[str, tuple[DocumentElement, ...]]
    projections: dict[str, list[Element]]
    scores: dict[str, FixtureScore]


def load_fixture(fixture: str, klass: str) -> Fixture:
    directory = FIXTURES / fixture
    raw = (directory / "source.html").read_bytes()
    result = canonicalize(raw, source_document_id=fixture, media_type="text/html")
    if not isinstance(result, Canonicalized):
        raise SystemExit(f"{fixture}: {result.reason.value}: {result.detail}")
    path = CAPTURES / f"{fixture}.capture.json"
    if not path.is_file():
        raise SystemExit(f"{path.relative_to(REPO_ROOT)} is missing: capture first")
    capture = from_capture_json(path.read_text(encoding="utf-8"))
    extraction = LayoutExtractor().map_onto(capture, result.document)
    triggers = fired(result.document, result.elements)
    elements = {
        "walker-1": result.elements,
        "layout-1": extraction.elements,
        "fallback": extraction.elements if triggers else result.elements,
    }
    text = result.document.canonical_text
    projections = {name: project(text, elements[name])[0] for name in CONFIGURATIONS}
    gold, source = load_gold(directory), SourceText(raw)
    return Fixture(
        fixture=fixture,
        klass=klass,
        gold=gold,
        source=source,
        result=result,
        capture=capture,
        extraction=extraction,
        triggers=triggers,
        elements=elements,
        projections=projections,
        scores={
            name: score_fixture(gold, source, projections[name])
            for name in CONFIGURATIONS
        },
    )


def load_fixtures() -> list[Fixture]:
    manifest = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))
    return [
        load_fixture(entry["fixture_id"], entry["primary_class"])
        for entry in sorted(manifest["fixtures"], key=lambda e: e["fixture_id"])
    ]


def metric_pairs(fixture: Fixture) -> dict[str, dict[str, tuple[int, int]]]:
    """Each configuration's (numerator, denominator) for each metric."""
    units = fixture.extraction.units
    failures = {
        "walker-1": 0,
        "layout-1": len(fixture.extraction.failures),
        "fallback": len(fixture.extraction.failures) if fixture.triggers else 0,
    }
    out: dict[str, dict[str, tuple[int, int]]] = {}
    for name in CONFIGURATIONS:
        score = fixture.scores[name]
        pairs = {
            metric: (score.counts[metric][0], score.counts[metric][1])
            for _, metric in METRICS
            if metric in score.counts
        }
        pairs["altered"] = (len(score.altered), score.counts["coverage"][1])
        pairs["alignment"] = (failures[name], units)
        out[name] = pairs
    return out


def pooled(fixtures: Sequence[Fixture], name: str, metric: str) -> tuple[int, int]:
    pairs = [metric_pairs(fixture)[name][metric] for fixture in fixtures]
    return sum(pair[0] for pair in pairs), sum(pair[1] for pair in pairs)


def regression(
    metric: str, baseline: tuple[int, int], other: tuple[int, int]
) -> str | None:
    """Why ``other`` regresses from walker-1's ``baseline``, or ``None``: worse by more
    than 1/n, n being walker-1's denominator, as exact fractions."""
    (a, n), (b, m) = baseline, other
    if n == 0 and m == 0:
        return None
    if n == 0 or m == 0:
        return "not comparable: one denominator is zero"
    worse = Fraction(a, n) - Fraction(b, m)
    if metric not in HIGHER_BETTER:
        worse = -worse
    if worse > Fraction(1, n):
        return f"worse by {worse}, more than 1/{n}"
    return None


def unit_lost(fixture: Fixture, name: str, unit: Unit, blocks: dict) -> bool:
    """The pre-registered loss of one targeted unit under one configuration."""
    score = fixture.scores[name]
    if unit.block in score.residual["missed"]:
        return True
    if unit.klass == CLASSES[0]:
        return unit.block in score.residual["header_lost"]
    projection = fixture.projections[name]
    result = match_block(blocks[unit.block], CandidateText(projection), fixture.source)
    return any(projection[index].type == "table" for index in result.elements)


def class_losses(
    fixtures: Sequence[Fixture], units: Sequence[Unit]
) -> dict[str, dict[str, list[Unit]]]:
    """For each class and configuration, the units lost."""
    by_id = {fixture.fixture: fixture for fixture in fixtures}
    blocks = {
        fixture.fixture: {block["id"]: block for block in fixture.gold["blocks"]}
        for fixture in fixtures
    }
    return {
        klass: {
            name: [
                unit
                for unit in units
                if unit.klass == klass
                and unit_lost(by_id[unit.fixture], name, unit, blocks[unit.fixture])
            ]
            for name in CONFIGURATIONS
        }
        for klass in CLASSES
    }


def repaired(losses: dict[str, list[Unit]], name: str) -> bool:
    return len(losses[name]) < len(losses["walker-1"])


def regressions(fixtures: Sequence[Fixture], name: str) -> list[str]:
    """Every regression of one configuration, as ``class, metric: why``."""
    found = []
    for klass in sorted({fixture.klass for fixture in fixtures}):
        members = [fixture for fixture in fixtures if fixture.klass == klass]
        for label, metric in METRICS:
            why = regression(
                metric,
                pooled(members, "walker-1", metric),
                pooled(members, name, metric),
            )
            if why is not None:
                found.append(f"{klass}, {label}: {why}")
    return found


def probe_types(fixture: Fixture, probe: Probe, name: str) -> Counter[str]:
    """The types of the elements whose whole text the probe matches."""
    pattern = re.compile(probe.pattern, re.DOTALL)
    text = fixture.result.document.canonical_text
    return Counter(
        element.type.value
        for element in fixture.elements[name]
        if element.type not in (ElementType.SENTENCE, ElementType.TABLE_CELL)
        and pattern.fullmatch(element.span.slice_of(text))
    )


def render(fixtures: Sequence[Fixture], units: Sequence[Unit]) -> str:
    losses = class_losses(fixtures, units)
    lines = [
        "# layout-1: the pre-registered comparison",
        "",
        "Generated by `expirements/parser-fidelity/layout1_report.py`; do not edit.",
        "Development-set numbers: the fixtures were Stage 1's test set (SC2).",
        "",
        *_preregistration(),
        "",
        "## Versions",
        "",
        *_versions(fixtures),
        "",
        "## Captures",
        "",
        (
            "| Fixture | Class | Status | Blocked (required) | Units"
            " | Alignment failures | Triggers | layout-1 retypes |"
        ),
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for fixture in fixtures:
        capture, extraction = fixture.capture, fixture.extraction
        required = sum(request.required for request in capture.blocked_requests)
        retypes = ", ".join(
            f"{rule} {count}" for rule, count in extraction.retypes.items() if count
        )
        lines.append(
            f"| `{fixture.fixture}` | {fixture.klass} | {capture.status.value}"
            f" | {len(capture.blocked_requests)} ({required}) | {extraction.units}"
            f" | {len(extraction.failures)} | {', '.join(fixture.triggers) or 'none'}"
            f" | {retypes or 'none'} |"
        )
    lines += [
        "",
        "## Targeted classes",
        "",
        "Units lost out of each class's pre-registered units (layout1-units.toml).",
        "",
        "| Class | Units | walker-1 | layout-1 | fallback | Repaired by |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for klass in CLASSES:
        total = sum(unit.klass == klass for unit in units)
        by = [name for name in CANDIDATES if repaired(losses[klass], name)]
        lines.append(
            f"| {CLASS_NAMES[klass]} | {total}"
            + "".join(f" | {len(losses[klass][name])}" for name in CONFIGURATIONS)
            + f" | {', '.join(by) or 'none'} |"
        )
    lines += [
        "",
        "## Metrics by fixture class",
        "",
        "Exact counts pooled over each class's fixtures, as numerator/denominator.",
        "Block coverage and cell association count successes; every other metric",
        "counts losses. A mark is the pre-registered regression rule's finding.",
        "",
        "| Class | Metric | walker-1 | layout-1 | fallback |",
        "| --- | --- | --- | --- | --- |",
    ]
    for klass in sorted({fixture.klass for fixture in fixtures}):
        members = [fixture for fixture in fixtures if fixture.klass == klass]
        for label, metric in METRICS:
            baseline = pooled(members, "walker-1", metric)
            cells = [_pair(baseline)]
            for name in CANDIDATES:
                pair = pooled(members, name, metric)
                why = regression(metric, baseline, pair)
                cells.append(_pair(pair) + (" (regression)" if why else ""))
            lines.append(f"| {klass} | {label} | " + " | ".join(cells) + " |")
    lines += ["", "## Verdict", ""]
    allowed = ["1 (diagnostic-only capture)"]
    for name, outcome in zip(
        CANDIDATES,
        ("3 (layout-1 for every document)", "2 (the fallback, as walker-2)"),
        strict=True,
    ):
        fixed = [CLASS_NAMES[k] for k in CLASSES if repaired(losses[k], name)]
        worse = regressions(fixtures, name)
        eligible = bool(fixed) and not worse
        lines += [
            f"### {name}",
            "",
            f"- Repaired classes: {'; '.join(fixed) or 'none'}.",
            f"- Regressions: {len(worse)}.",
            *(f"  - {why}" for why in worse),
            (
                f"- The promotion rule {'allows' if eligible else 'does not allow'}"
                f" outcome {outcome}."
            ),
            "",
        ]
        if eligible:
            allowed.append(outcome)
    lines.append(
        "ADR 0002 chooses among the outcomes the rule allows: "
        + "; ".join(sorted(allowed))
        + "."
    )
    lines += ["", "## Units", ""]
    for klass in CLASSES:
        members = [unit for unit in units if unit.klass == klass]
        lines += [f"### {CLASS_NAMES[klass]}", ""]
        if not members:
            empty = "No units."
            if klass == CLASSES[2]:
                empty = "No units: no fixture carries a stylesheet."
            lines += [empty, ""]
            continue
        lines += [
            "| Fixture | Block | Type | walker-1 | layout-1 | fallback |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for unit in members:
            marks = [
                "lost" if unit in losses[klass][name] else "kept"
                for name in CONFIGURATIONS
            ]
            lines.append(
                f"| `{unit.fixture}` | {unit.block} | {unit.type} | "
                + " | ".join(marks)
                + " |"
            )
        lines.append("")
    lines += ["## Alignment failures", ""]
    failures = [
        (fixture.fixture, failure)
        for fixture in fixtures
        for failure in fixture.extraction.failures
    ]
    if not failures:
        lines.append("None.")
    else:
        lines += ["| Fixture | Reason | Unit | Text |", "| --- | --- | --- | --- |"]
        lines += [
            f"| `{fixture}` | {failure.reason.value} | {failure.unit_type}"
            f" | {excerpt(failure.text)} |"
            for fixture, failure in failures
        ]
    lines += [
        "",
        "## Review-gate findings",
        "",
        "Plan 4's open findings (docs/verification/walker-1.md, The review gate): the",
        "elements whose whole text each finding's pattern matches, by type.",
        "",
        "| Finding | Fixture | walker-1 | layout-1 | fallback |",
        "| --- | --- | --- | --- | --- |",
    ]
    for probe in PROBES:
        for fixture in fixtures:
            if probe.fixture not in (None, fixture.fixture):
                continue
            counts = [probe_types(fixture, probe, name) for name in CONFIGURATIONS]
            if not any(counts):
                continue
            lines.append(
                f"| {probe.finding} | `{fixture.fixture}` | "
                + " | ".join(_types(count) for count in counts)
                + " |"
            )
    return "\n".join(lines) + "\n"


def _preregistration() -> list[str]:
    record = tomllib.loads(PREREGISTERED.read_text(encoding="utf-8"))
    changes = record.get("changes", [])
    lines = [
        (
            f"Pre-registered on {record['frozen_on']} at commit"
            f" `{record['commit'][:12]}`, before any release was captured;"
            f" {len(changes)} recorded post-freeze fixes."
        )
    ]
    lines += [
        f"- {change['date']}: `{change['file']}`, {change['reason']}: {change['note']}"
        for change in changes
    ]
    return lines


def _versions(fixtures: Sequence[Fixture]) -> list[str]:
    environments = Counter(
        (
            c.browser_engine,
            c.browser_version,
            c.driver_version,
            c.selenium_version,
            c.os_name,
            c.os_version,
            c.architecture,
            c.capture_policy,
            c.capture_policy_version,
            c.metadata_version,
        )
        for c in (fixture.capture for fixture in fixtures)
    )
    lines = [
        (
            f"- walker-1 (C1-C5); {fixtures[0].extraction.layout_version}, mapped by"
            f" {fixtures[0].extraction.mapping_policy}."
        ),
    ]
    for environment, count in sorted(environments.items()):
        engine, browser, driver, selenium, os_name, os_version, arch = environment[:7]
        policy, policy_version, metadata = environment[7:]
        lines.append(
            f"- {count} captures: {engine} {browser}, chromedriver {driver},"
            f" Selenium {selenium}, {os_name} {os_version} {arch};"
            f" capture policy {policy}/{policy_version}, {metadata}."
        )
    return lines


def _pair(pair: tuple[int, int]) -> str:
    return f"{pair[0]}/{pair[1]}"


def _types(counts: Counter[str]) -> str:
    return ", ".join(f"{kind} {n}" for kind, n in sorted(counts.items())) or "none"


def main() -> int:
    REPORT.write_text(
        render(load_fixtures(), load_units()), encoding="utf-8", newline="\n"
    )
    print(f"wrote {REPORT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
