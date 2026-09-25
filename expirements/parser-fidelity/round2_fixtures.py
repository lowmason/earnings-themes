"""Round-2 fixture selection, fixed at gate D before the round-2 discovery run.

At gate D (2026-09-24) the user replaced all eight round-1 fixtures. Round 1's results
were known by then, so the user chose a fixed rule over a hand pick: discover.py's
suggest(), unchanged since 050beea and called exactly as written (three per class), over
every discovery candidate except

- round 1's fixtures and its development set, and
- every other release from those eleven issuers, matched on CIK (never on the accession
  prefix, which names the filer agent).

In each class the first two picks, in pick order, are the fixtures. The third is the
spare that replaces a fixture of its class rejected at gate B.

This file was committed before the round-2 discovery run and before the rule ran on any
candidate. Run once, in this order:

    uv run --locked --script expirements/parser-fidelity/discover.py run --live --years 2007 2010 2013 2016 2019 2022
    uv run --locked --all-packages python expirements/parser-fidelity/round2_fixtures.py [--write]

--write replaces approval.toml with the rendered approval, unsigned; the user signs it
with approved_by. A class with fewer than two picks stops the script, and the user
decides.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime

from discover import Candidate, eligible_for_shortlist, load_candidates, suggest
from pf_paths import HARNESS

ROUND1_FIXTURES = (
    "0000315449-18-000009_ex-99-1",  # UQM Technologies, 2018
    "0000859163-17-000071_ex-99-1",  # AVX Corp, 2017
    "0000003370-05-000209_ex-99",  # IKON Office Solutions, 2005
    "0000004904-24-000080_ex-99",  # American Electric Power, 2024
    "0000049071-06-000012_ex-99",  # Humana, 2006
    "0000068270-05-000104_ex-99",  # Ruby Tuesday, 2005
    "0001104659-23-049001_ex-99-1",  # Establishment Labs Holdings, 2023
    "0001572910-14-000003_ex-99-1",  # Phillips 66 Partners, 2014
)
DEVSET = (
    "0000079958-12-000020_ex-99-1",  # Precision Castparts, 2012
    "0000019149-11-000022_ex-99-1",  # Champion Industries, 2011
    "0001045150-09-000060_ex-99-1",  # Tier Technologies, 2009
)
APPROVAL_ORDER = ("clean_html", "malformed_layout", "table_heavy", "narrative_only")
FIXTURES_PER_CLASS = 2
APPROVAL_FILE = HARNESS / "approval.toml"

Selection = dict[str, tuple[list[Candidate], list[Candidate]]]


def round2_pool(candidates: list[Candidate], excluded: set[str]) -> list[Candidate]:
    """Every candidate except the excluded releases and any release from their issuers."""
    by_id = {c.fixture_id: c for c in candidates}
    missing = sorted(excluded - by_id.keys())
    if missing:
        raise ValueError(
            f"excluded releases not among the candidates: {', '.join(missing)}"
        )
    ciks = {by_id[fid].cik for fid in excluded}
    return [c for c in candidates if c.cik not in ciks]


def round2_selection(candidates: list[Candidate], excluded: set[str]) -> Selection:
    """suggest() over the round-2 pool: per class, (fixtures, spares) in pick order."""
    chosen = suggest(round2_pool(candidates, excluded))
    return {
        cls: (picks[:FIXTURES_PER_CLASS], picks[FIXTURES_PER_CLASS:])
        for cls, picks in chosen.items()
    }


def short_classes(selection: Selection) -> list[str]:
    return [
        cls for cls in APPROVAL_ORDER if len(selection[cls][0]) < FIXTURES_PER_CLASS
    ]


def _label(candidate: Candidate) -> str:
    return f"{candidate.issuer_name}, {candidate.year}"


def render_approval(
    selection: Selection, devset: list[Candidate], approved_on: str
) -> str:
    lines = [
        "# Stage 1 fixture approval, round 2 (specs/release-parser-fidelity.md: Selection;",
        "# decisions F3, F4). Written by round2_fixtures.py from discover.suggest() over the",
        "# round-2 pool, a rule fixed before the round-2 discovery run; the user signs it with",
        "# approved_by. promote_fixtures.py enforces two fixtures per class, a class-test match",
        "# for each primary_class, at most two fixtures per issuer, the 1 MiB cap, and a",
        "# development set of two or three releases disjoint from the fixtures.",
        'approved_by = ""',
        f"approved_on = {approved_on}",
        "short_classes = []",
    ]
    for cls in APPROVAL_ORDER:
        for c in selection[cls][0]:
            lines += [
                "",
                "[[fixtures]]",
                f'fixture_id = "{c.fixture_id}"  # {_label(c)}',
                f'primary_class = "{cls}"',
            ]
    for c in devset:
        lines += ["", "[[devset]]", f'fixture_id = "{c.fixture_id}"  # {_label(c)}']
    lines += [
        "",
        "# Spares, fixed with the fixtures: each replaces a fixture of its class rejected at",
        "# gate B.",
    ]
    for cls in APPROVAL_ORDER:
        lines += [
            f'# spare, {cls}: "{c.fixture_id}"  # {_label(c)}'
            for c in selection[cls][1]
        ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="replace approval.toml with the rendered approval, unsigned",
    )
    args = parser.parse_args(argv)

    candidates = load_candidates()
    by_id = {c.fixture_id: c for c in candidates}
    excluded = set(ROUND1_FIXTURES) | set(DEVSET)
    pool = round2_pool(candidates, excluded)
    selection = round2_selection(candidates, excluded)
    print(
        f"{len(candidates)} candidates; {len(pool)} left in the round-2 pool after "
        f"excluding {len(excluded)} releases and every release from their issuers"
    )
    for cls in APPROVAL_ORDER:
        eligible = sum(c.class_tests[cls] and eligible_for_shortlist(c) for c in pool)
        print(f"{cls} ({eligible} eligible in the pool):")
        fixtures, spares = selection[cls]
        for role, group in (("fixture", fixtures), ("spare", spares)):
            for c in group:
                malformed = "yes" if c.class_tests["malformed_layout"] else "no"
                print(
                    f"  {role:8} {c.fixture_id}  {_label(c)}  agent {c.agent}  "
                    f"{c.exhibit_type}  malformed {malformed}"
                )
    short = short_classes(selection)
    if short:
        print(
            f"STOP: fewer than two picks in {', '.join(short)}; the user decides "
            "(the plan's short-class contingency)"
        )
        return 1
    chosen = [c for cls in APPROVAL_ORDER for c in selection[cls][0]]
    other = [c for c in chosen if c.exhibit_type.strip().upper() != "EX-99.1"]
    if other:
        print(
            f"exhibit numbering: {len(other)} of {len(chosen)} fixtures are filed "
            "under an exhibit other than EX-99.1"
        )
    else:
        print(
            "limitation: no fixture is filed under an exhibit other than EX-99.1 "
            "(nothing substituted)"
        )
    text = render_approval(
        selection, [by_id[fid] for fid in DEVSET], datetime.now(UTC).date().isoformat()
    )
    if args.write:
        APPROVAL_FILE.write_text(text, encoding="utf-8")
        print(f"wrote {APPROVAL_FILE} (unsigned)")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
