"""Run every candidate twice per release, in separate processes (spec: Candidate harness).

    uv run --locked --all-packages python expirements/parser-fidelity/run_candidates.py dev
    uv run --locked --all-packages python expirements/parser-fidelity/run_candidates.py fixtures [--candidates walker ...]

Each run is ``uv run --locked --script <adapter>`` in a fresh process with default hash
randomization (PYTHONHASHSEED is removed from the child environment). The two dumps are
compared byte for byte (determinism gate); any network-guard trip voids the run (network
gate). Fixture runs refuse to start until the freeze verifies and every gold file passes
the validator, so no candidate output exists before the gold is complete.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from freeze import FREEZE_FILE, verify
from pf_paths import DEVSET, EDGAR_HOME, FIXTURES, HARNESS, REPO_ROOT, RUNS
from validate_gold import validate_fixture

RUN_TIMEOUT_SECONDS = 900


@dataclass(frozen=True)
class Candidate:
    script: str
    selectable: bool


CANDIDATES = {
    "edgartools": Candidate("adapter_edgartools.py", True),
    "secparser": Candidate("adapter_secparser.py", True),
    "walker": Candidate("walker.py", True),
    "control": Candidate("control.py", False),
}


def release_inputs(
    set_name: str, fixtures: Path = FIXTURES, devset: Path = DEVSET
) -> dict[str, Path]:
    root = fixtures if set_name == "fixtures" else devset
    return {path.parent.name: path for path in sorted(root.glob("*/source.html"))}


def fixture_preconditions(fixtures: Path = FIXTURES) -> list[str]:
    problems = verify(HARNESS, FREEZE_FILE)
    for folder in sorted(path.parent for path in fixtures.glob("*/source.html")):
        report = validate_fixture(folder)
        problems += [f"{folder.name}: gold: {error}" for error in report.errors]
    return problems


# PYTHONHASHSEED is dropped so each run gets default hash randomization. EDGAR_IDENTITY
# is dropped because parsing needs no identity and candidate output lands in run logs.
DROPPED_ENV = frozenset({"PYTHONHASHSEED", "EDGAR_IDENTITY"})


def child_env() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key not in DROPPED_ENV}
    env["EDGAR_LOCAL_DATA_DIR"] = str(EDGAR_HOME)
    return env


def run_once(
    candidate: Candidate,
    source: Path,
    out_dir: Path,
    number: int,
    runner: Callable = subprocess.run,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    dump, sidecar = out_dir / f"run{number}.json", out_dir / f"run{number}.sidecar.json"
    for stale in (dump, sidecar):
        stale.unlink(missing_ok=True)
    command = [
        "uv", "run", "--locked", "--script", str(HARNESS / candidate.script),
        "--input", str(source), "--output", str(dump), "--sidecar", str(sidecar),
    ]  # fmt: skip
    try:
        completed = runner(
            command,
            cwd=REPO_ROOT,
            env=child_env(),
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT_SECONDS,
        )
        log = f"exit {completed.returncode}\n--- stdout\n{completed.stdout}\n--- stderr\n{completed.stderr}"
    except subprocess.TimeoutExpired:
        log = f"timed out after {RUN_TIMEOUT_SECONDS}s"
    (out_dir / f"run{number}.log").write_text(log, encoding="utf-8")
    if not sidecar.exists():
        return {"status": "no_sidecar", "dump": None}
    data = json.loads(sidecar.read_text(encoding="utf-8"))
    data["dump"] = str(dump) if dump.exists() else None
    return data


def run_pair(
    candidate: Candidate, source: Path, out_dir: Path, runner: Callable = subprocess.run
) -> dict:
    first = run_once(candidate, source, out_dir, 1, runner)
    second = run_once(candidate, source, out_dir, 2, runner)
    both_ok = first["status"] == second["status"] == "ok"
    deterministic = (
        both_ok
        and Path(first["dump"]).read_bytes() == Path(second["dump"]).read_bytes()
    )
    return {
        "status": [first["status"], second["status"]],
        "deterministic": deterministic,
        "guard_trips": first.get("guard_trips", []) + second.get("guard_trips", []),
        "python": first.get("python"),
        "library_version": first.get("library_version"),
        "parse_seconds": [first.get("parse_seconds"), second.get("parse_seconds")],
        "error": first.get("error") or second.get("error"),
    }


def run_set(set_name: str, names: list[str], runner: Callable = subprocess.run) -> dict:
    results: dict = {}
    gates_path = RUNS / set_name / "gates.json"
    if gates_path.exists():
        results = json.loads(gates_path.read_text(encoding="utf-8"))
    for name in names:
        results[name] = {}
        for fid, source in release_inputs(set_name).items():
            outcome = run_pair(
                CANDIDATES[name], source, RUNS / set_name / name / fid, runner
            )
            results[name][fid] = outcome
            print(
                f"{name:10} {fid}  status={outcome['status']}  deterministic={outcome['deterministic']}"
            )
    gates_path.parent.mkdir(parents=True, exist_ok=True)
    gates_path.write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("set", choices=("dev", "fixtures"))
    parser.add_argument(
        "--candidates", nargs="+", choices=sorted(CANDIDATES), default=list(CANDIDATES)
    )
    args = parser.parse_args(argv)
    if args.set == "fixtures":
        problems = fixture_preconditions()
        if problems:
            print(
                "refusing to run candidates on fixtures:\n" + "\n".join(problems),
                file=sys.stderr,
            )
            return 1
    if not release_inputs(args.set):
        print(f"no releases found for the {args.set} set", file=sys.stderr)
        return 1
    run_set(args.set, args.candidates)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
