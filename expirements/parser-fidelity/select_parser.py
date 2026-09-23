"""Apply the fixed selection rule (spec: Selection rule; decisions F6 and F7). Standard library only.

    uv run --locked --all-packages python expirements/parser-fidelity/select_parser.py

Reads scores.json, the fixture run gates, and the lock-gate results; writes
data/runs/parser-fidelity/selection.json and selection.md with the rule applied step by
step. The rule was fixed before any fixture was scored and this script must not change
after scoring begins.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import tomllib
from pf_paths import HARNESS, RUNS
from run_candidates import CANDIDATES
from score import RANKED

WORST = {
    "coverage": min,
    "footnote_merging": max,
    "reading_order": max,
    "header_loss": max,
}
BEST = {
    "coverage": max,
    "footnote_merging": min,
    "reading_order": min,
    "header_loss": min,
}


@dataclass(frozen=True)
class Meta:
    license: str
    permissive: bool
    package: str | None  # distribution name in the adapter's script lock
    lock: str | None


# Licenses read from the wheels' METADATA on 2026-09-22 (edgartools: License-Expression MIT;
# sec-parser: License MIT, OSI classifier). The walker is this project's own code.
META = {
    "edgartools": Meta("MIT", True, "edgartools", "adapter_edgartools.py.lock"),
    "secparser": Meta("MIT", True, "sec-parser", "adapter_secparser.py.lock"),
    "walker": Meta("project code", True, None, None),
}


def release_date(meta: Meta, harness: Path = HARNESS) -> str | None:
    if meta.lock is None:
        return None
    lock = tomllib.loads((harness / meta.lock).read_text(encoding="utf-8"))
    package = next(p for p in lock["package"] if p["name"] == meta.package)
    upload = (
        package.get("sdist", {}).get("upload-time")
        or package["wheels"][0]["upload-time"]
    )
    return str(upload)[:10]


def worst_class(
    classes: dict, candidate: str, metric: str
) -> tuple[float, int, str] | None:
    """(value, denominator, class) of the candidate's worst class; classes without a denominator are skipped."""
    values = []
    for cls, by_candidate in classes.items():
        rates = by_candidate[candidate]["rates"]
        if metric == "header_loss":
            if rates["header_loss"] is not None:
                values.append((rates["header_loss"], rates["header_loss_n"], cls))
        elif by_candidate[candidate]["counts"][metric][1]:
            values.append(
                (rates[metric], by_candidate[candidate]["counts"][metric][1], cls)
            )
    if not values:
        return None
    # Classes tied at the worst value: the smallest n, the spec's "smaller of the denominators".
    worst = WORST[metric](value for value, _, _ in values)
    return min((v for v in values if v[0] == worst), key=lambda v: (v[1], v[2]))


def tie(a: tuple[float, int, str], b: tuple[float, int, str]) -> bool:
    return abs(a[0] - b[0]) <= 1 / min(a[1], b[1])


def priority_comparison(
    classes: dict, candidates: list[str]
) -> tuple[list[str], list[str]]:
    remaining, trace = list(candidates), []
    for metric in RANKED:
        if len(remaining) <= 1:
            break
        values = {c: worst_class(classes, c, metric) for c in remaining}
        defined = {c: v for c, v in values.items() if v is not None}
        if not defined:
            trace.append(f"{metric}: no candidate has a denominator; all remain")
            continue
        best = BEST[metric](defined.values(), key=lambda v: v[0])
        remaining = [c for c in remaining if values[c] is None or tie(values[c], best)]
        shown = ", ".join(
            f"{c}={v[0]:.3f} (n={v[1]}, worst class {v[2]})" if v else f"{c}=n/a"
            for c, v in values.items()
        )
        trace.append(
            f"{metric}: {shown}; best {best[0]:.3f}; within 1/n of best: {', '.join(remaining)}"
        )
    return remaining, trace


def tie_breaks(remaining: list[str], lock_gates: dict) -> tuple[list[str], list[str]]:
    trace = []
    if len(remaining) > 1:
        cost = {
            c: (lock_gates[c]["pandas_added"], len(lock_gates[c]["added_runtime"]))
            for c in remaining
        }
        low = min(cost.values())
        remaining = [c for c in remaining if cost[c] == low]
        trace.append(
            f"dependencies (pandas added, count added): {cost}; kept {remaining}"
        )
    if len(remaining) > 1:
        remaining = [c for c in remaining if META[c].permissive] or remaining
        trace.append(f"license: kept {remaining}")
    if len(remaining) > 1:
        dates = {c: release_date(META[c]) or "0000-00-00" for c in remaining}
        latest = max(dates.values())
        remaining = [c for c in remaining if dates[c] == latest]
        trace.append(f"most recent release: {dates}; kept {remaining}")
    return remaining, trace


def gate_results(run_gates: dict, lock_gates: dict) -> dict[str, dict[str, bool]]:
    results = {}
    for name in META:
        runs = run_gates.get(name, {})
        lock = lock_gates.get(name, {})
        results[name] = {
            "lock": bool(lock.get("resolved"))
            and not lock.get("lowered")
            and bool(lock.get("parse_ok")),
            "determinism": bool(runs)
            and all(r["deterministic"] for r in runs.values()),
            "network": bool(runs) and not any(r["guard_trips"] for r in runs.values()),
        }
    return results


def control_check(classes: dict, selected: str) -> tuple[dict[str, bool], bool]:
    beats = {}
    for cls, by_candidate in classes.items():
        wins = []
        for metric in ("coverage", "footnote_merging", "reading_order"):
            sel, ctl = (
                by_candidate[selected]["counts"][metric],
                by_candidate["control"]["counts"][metric],
            )
            if not sel[1] or not ctl[1]:
                continue
            diff = sel[0] / sel[1] - ctl[0] / ctl[1]
            margin = 1 / min(sel[1], ctl[1])
            wins.append(diff > margin if metric == "coverage" else -diff > margin)
        beats[cls] = any(wins)
    return beats, any(beats.values())


def select(scores: dict, run_gates: dict, lock_gates: dict) -> dict:
    classes = scores["classes"]
    gates = gate_results(run_gates, lock_gates)
    eligible = [name for name in META if all(gates[name].values())]
    trace = [f"eligibility: {gates}; eligible: {eligible or 'none'}"]
    outcome: dict = {
        "gates": gates,
        "eligible": eligible,
        "selected": None,
        "trace": trace,
    }
    if not eligible:
        outcome["status"] = "no eligible candidate: the decision returns to the user"
        return outcome
    remaining, steps = priority_comparison(classes, eligible)
    trace += steps
    remaining, steps = tie_breaks(remaining, lock_gates)
    trace += steps
    if len(remaining) == 1:
        outcome["selected"] = remaining[0]
        outcome["status"] = "selected"
    else:
        outcome["status"] = (
            f"tie after every tie-break ({', '.join(remaining)}): the decision returns to the user"
        )
        return outcome
    unrestricted, _ = priority_comparison(classes, list(META))
    outcome["ineligible_would_have_won"] = [
        c for c in unrestricted if c not in eligible
    ]
    outcome["ineligible_gains"] = {
        c: {
            metric: {
                "ineligible": worst_class(classes, c, metric),
                "selected": worst_class(classes, outcome["selected"], metric),
            }
            for metric in RANKED
        }
        for c in outcome["ineligible_would_have_won"]
    }
    beats, discriminates = control_check(classes, outcome["selected"])
    outcome["control_check"] = {
        "beats_control_by_class": beats,
        "fixtures_discriminate": discriminates,
    }
    return outcome


def render(outcome: dict) -> str:
    lines = ["# Selection rule applied (generated by select_parser.py)", ""]
    lines += [
        f"{number}. {step}" for number, step in enumerate(outcome["trace"], start=1)
    ]
    lines += [
        "",
        f"**Outcome:** {outcome['status']}"
        + (f" -- **{outcome['selected']}**" if outcome["selected"] else ""),
    ]
    for name, gains in outcome.get("ineligible_gains", {}).items():
        lines.append(
            f"**{name} is ineligible but would have survived step 3.** Worst-class values:"
        )
        for metric, pair in gains.items():
            ours, theirs = pair["selected"], pair["ineligible"]
            shown = [
                f"{v[0]:.3f} (n={v[1]}, {v[2]})" if v else "n/a" for v in (theirs, ours)
            ]
            lines.append(
                f"- {metric}: {name} {shown[0]} vs {outcome['selected']} {shown[1]}"
            )
    if "control_check" in outcome:
        check = outcome["control_check"]
        lines.append(
            f"**Control check:** beats the control by more than the tie margin in: {check['beats_control_by_class']}"
        )
        if not check["fixtures_discriminate"]:
            lines.append(
                "**Flag:** the fixtures cannot discriminate between parsers; the user decides whether to replace any."
            )
    return "\n".join(lines)


def main() -> int:
    scores = json.loads((RUNS / "scores" / "scores.json").read_text(encoding="utf-8"))
    run_gates = json.loads(
        (RUNS / "fixtures" / "gates.json").read_text(encoding="utf-8")
    )
    lock_gates = {
        name: json.loads(path.read_text(encoding="utf-8"))
        for name in META
        if (path := RUNS / "gates" / f"lock-{name}.json").exists()
    }
    missing = [name for name in META if name not in lock_gates]
    if missing:
        print(f"lock gate results missing for {missing}; run lock_gate.py first")
        return 1
    outcome = select(scores, run_gates, lock_gates)
    (RUNS / "selection.json").write_text(
        json.dumps(outcome, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (RUNS / "selection.md").write_text(render(outcome) + "\n", encoding="utf-8")
    print(render(outcome))
    return 0


if __name__ == "__main__":
    assert set(META) | {"control"} == set(CANDIDATES)
    raise SystemExit(main())
