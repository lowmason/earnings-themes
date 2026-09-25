# /// script
# requires-python = ">=3.14"
# dependencies = ["packaging==26.3"]
# ///
"""The lock gate (spec: Selection rule, step 1; decision F7).

    uv run --locked --script expirements/parser-fidelity/lock_gate.py edgartools
    uv run --locked --script expirements/parser-fidelity/lock_gate.py secparser
    uv run --locked --script expirements/parser-fidelity/lock_gate.py walker

For a library candidate: extract HEAD into a scratch directory with ``git archive``, add
the pinned requirement to earnings-ingestion's runtime dependencies there, and run
``uv lock``. The gate passes when the lock resolves, lowers no locked version, and the
adapter imports and parses every fixture under Python 3.14 in the scratch workspace.
The repository itself is never modified. The walker adds no dependency: the gate checks
that its imports are already earnings-ingestion runtime dependencies and that it parses
every fixture in the workspace environment. Run only after the freeze and gold completion.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import tomllib
from packaging.requirements import Requirement
from packaging.version import Version
from pf_paths import FIXTURES, HARNESS, REPO_ROOT, RUNS
from run_candidates import fixture_preconditions

INGESTION = "earnings-ingestion"
INGESTION_PYPROJECT = Path("packages") / "earnings-ingestion" / "pyproject.toml"
LIBRARY_CANDIDATES = {
    "edgartools": ("edgartools==5.58.0", "adapter_edgartools.py"),
    "secparser": ("sec-parser==0.58.1", "adapter_secparser.py"),
}
WALKER_IMPORTS = ("lxml", "beautifulsoup4")


def add_dependency(pyproject_text: str, requirement: str) -> str:
    marker = "dependencies = [\n"
    at = pyproject_text.index(marker) + len(marker)
    return pyproject_text[:at] + f'    "{requirement}",\n' + pyproject_text[at:]


def locked_versions(lock: dict) -> dict[str, str]:
    return {p["name"]: p["version"] for p in lock["package"] if "version" in p}


def lowered_versions(old: dict[str, str], new: dict[str, str]) -> list[str]:
    return sorted(
        f"{n} {old[n]} -> {new[n]}"
        for n in old
        if n in new and Version(new[n]) < Version(old[n])
    )


def runtime_closure(lock: dict, root: str = INGESTION) -> set[str]:
    """Distributions ``root`` needs at run time, following requested extras (markers ignored: an upper bound)."""
    packages = {p["name"]: p for p in lock["package"]}
    visited: set[tuple[str, tuple[str, ...]]] = set()
    stack: list[tuple[str, tuple[str, ...]]] = [(root, ())]
    while stack:
        item = stack.pop()
        if item in visited:
            continue
        visited.add(item)
        name, extras = item
        entry = packages.get(name, {})
        deps = list(entry.get("dependencies", []))
        for extra in extras:
            deps += entry.get("optional-dependencies", {}).get(extra, [])
        stack.extend((dep["name"], tuple(dep.get("extra", ()))) for dep in deps)
    return {name for name, _ in visited} - {root}


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


def parse_fixtures(
    workspace: Path, adapter: str, python_prefix: str = "3.14"
) -> tuple[bool, list[str]]:
    problems = []
    with tempfile.TemporaryDirectory() as out:
        for source in sorted(FIXTURES.glob("*/source.html")):
            dump, sidecar = Path(out) / "d.json", Path(out) / "s.json"
            command = ["uv", "run", "--directory", str(workspace), "--locked", "--all-packages", "python",
                       str(HARNESS / adapter), "--input", str(source), "--output", str(dump), "--sidecar", str(sidecar)]  # fmt: skip
            completed = _run(command, REPO_ROOT)
            status = (
                json.loads(sidecar.read_text())["status"]
                if sidecar.exists()
                else "no sidecar"
            )
            python = (
                json.loads(sidecar.read_text()).get("python", "")
                if sidecar.exists()
                else ""
            )
            if (
                completed.returncode != 0
                or status != "ok"
                or not python.startswith(python_prefix)
            ):
                problems.append(
                    f"{source.parent.name}: exit {completed.returncode}, status {status}, python {python}"
                )
    return not problems, problems


def library_gate(name: str) -> dict:
    requirement, adapter = LIBRARY_CANDIDATES[name]
    result: dict = {"candidate": name, "requirement": requirement}
    with tempfile.TemporaryDirectory() as scratch_dir:
        scratch = Path(scratch_dir)
        archive = subprocess.run(
            ["git", "archive", "--format=tar", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
        )
        with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
            tar.extractall(scratch, filter="data")
        pyproject = scratch / INGESTION_PYPROJECT
        pyproject.write_text(
            add_dependency(pyproject.read_text(encoding="utf-8"), requirement),
            encoding="utf-8",
        )
        old = tomllib.loads((REPO_ROOT / "uv.lock").read_text(encoding="utf-8"))
        locked = _run(["uv", "lock"], scratch)
        result["resolved"] = locked.returncode == 0
        result["uv_lock_output"] = (locked.stdout + locked.stderr)[-4000:]
        if not result["resolved"]:
            result.update(
                lowered=[],
                added_runtime=[],
                pandas_added=False,
                parse_ok=False,
                parse_problems=["not run: uv lock failed"],
            )
            return result
        new = tomllib.loads((scratch / "uv.lock").read_text(encoding="utf-8"))
        result["lowered"] = lowered_versions(locked_versions(old), locked_versions(new))
        added = sorted(runtime_closure(new) - runtime_closure(old))
        result["added_runtime"] = added
        result["pandas_added"] = "pandas" in added
        if result["lowered"]:
            result.update(
                parse_ok=False,
                parse_problems=["not run: the lock lowers a locked version"],
            )
            return result
        synced = _run(["uv", "sync", "--locked", "--all-packages"], scratch)
        if synced.returncode != 0:
            result.update(
                parse_ok=False,
                parse_problems=[f"uv sync failed: {synced.stderr[-2000:]}"],
            )
            return result
        result["parse_ok"], result["parse_problems"] = parse_fixtures(scratch, adapter)
    return result


def walker_gate() -> dict:
    ingestion = tomllib.loads(
        (REPO_ROOT / INGESTION_PYPROJECT).read_text(encoding="utf-8")
    )
    declared = {Requirement(dep).name for dep in ingestion["project"]["dependencies"]}
    missing = [name for name in WALKER_IMPORTS if name not in declared]
    result: dict = {
        "candidate": "walker",
        "requirement": None,
        "resolved": not missing,
        "lowered": [],
        "added_runtime": missing,
    }
    result["pandas_added"] = False
    result["parse_ok"], result["parse_problems"] = parse_fixtures(
        REPO_ROOT, "walker.py"
    )
    return result


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1 or args[0] not in (*LIBRARY_CANDIDATES, "walker"):
        print(
            f"usage: lock_gate.py {{{','.join((*LIBRARY_CANDIDATES, 'walker'))}}}",
            file=sys.stderr,
        )
        return 2
    name = args[0]
    problems = fixture_preconditions()  # P11: every gate parses every fixture
    if problems:
        print(
            "refusing to run the lock gate on fixtures:\n" + "\n".join(problems),
            file=sys.stderr,
        )
        return 1
    result = walker_gate() if name == "walker" else library_gate(name)
    result["passed"] = (
        bool(result["resolved"]) and not result["lowered"] and bool(result["parse_ok"])
    )
    out = RUNS / "gates" / f"lock-{name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {k: v for k, v in result.items() if k != "uv_lock_output"},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
