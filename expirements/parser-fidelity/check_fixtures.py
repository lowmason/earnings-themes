"""Stage 1 harness check (spec: Exit criteria 4). Standard library plus the git CLI.

    uv run --locked --all-packages python expirements/parser-fidelity/check_fixtures.py

Confirms that each fixture directory holds exactly source.html and gold.toml and has a
manifest entry (and the reverse); each source.html matches its sha256 and is at most
1 MiB; .gitattributes marks source.html -text; every source_id resolves to a register
entry with a recorded redistribution status; every gold.toml passes the validator; and
every harness script that declares dependencies has a committed lock.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

import tomllib
from pf_paths import FIXTURES, HARNESS, MAX_FIXTURE_BYTES, REGISTER, REPO_ROOT
from validate_gold import validate_fixture

FIXTURE_FILES = {"gold.toml", "source.html"}
_SCRIPT_BLOCK = re.compile(
    r"^# /// script\s*$(.*?)^# ///\s*$", re.MULTILINE | re.DOTALL
)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=False
    )


def declared_dependencies(script: Path) -> list[str]:
    match = _SCRIPT_BLOCK.search(script.read_text(encoding="utf-8"))
    if match is None:
        return []
    body = "\n".join(
        line.removeprefix("#").removeprefix(" ") for line in match.group(1).splitlines()
    )
    return list(tomllib.loads(body).get("dependencies", []))


def committable_files(repo: Path, folder: Path) -> set[str]:
    """Files under ``folder`` that Git tracks or would add; ignored files such as .DS_Store drop out."""
    relative = folder.relative_to(repo).as_posix()
    listed = _git(
        repo, "ls-files", "--cached", "--others", "--exclude-standard", "--", relative
    )
    return {
        line.removeprefix(relative + "/") for line in listed.stdout.splitlines() if line
    }


def check_fixtures(fixtures: Path, register: Path, repo: Path) -> list[str]:
    problems: list[str] = []
    manifest = tomllib.loads((fixtures / "manifest.toml").read_text(encoding="utf-8"))
    entries = {entry["fixture_id"]: entry for entry in manifest.get("fixtures", [])}
    directories = {path.name for path in fixtures.iterdir() if path.is_dir()}
    problems += [
        f"{fid}: directory has no manifest entry"
        for fid in sorted(directories - set(entries))
    ]
    problems += [
        f"{fid}: manifest entry has no directory"
        for fid in sorted(set(entries) - directories)
    ]
    sources = tomllib.loads(register.read_text(encoding="utf-8")).get("sources", {})
    for fid in sorted(directories & set(entries)):
        folder, entry = fixtures / fid, entries[fid]
        files = committable_files(repo, folder)
        if files != FIXTURE_FILES:
            problems.append(
                f"{fid}: holds {sorted(files)}, expected exactly {sorted(FIXTURE_FILES)}"
            )
        source = folder / "source.html"
        if source.exists():
            raw = source.read_bytes()
            if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
                problems.append(
                    f"{fid}: source.html does not match its manifest sha256"
                )
            if len(raw) > MAX_FIXTURE_BYTES:
                problems.append(f"{fid}: source.html is {len(raw)} bytes, over 1 MiB")
            attribute = _git(
                repo, "check-attr", "text", "--", str(source.relative_to(repo))
            ).stdout.strip()
            if not attribute.endswith(": text: unset"):
                problems.append(
                    f"{fid}: .gitattributes does not mark source.html -text ({attribute or 'no output'})"
                )
        status = sources.get(entry.get("source_id"), {}).get(
            "redistribution_status", ""
        )
        if not status.strip():
            problems.append(
                f"{fid}: source_id {entry.get('source_id')!r} has no register entry with a redistribution status"
            )
        if (folder / "gold.toml").exists():
            report = validate_fixture(folder)
            problems += [f"{fid}: gold: {error}" for error in report.errors]
    return problems


def check_locks(harness: Path, repo: Path) -> list[str]:
    problems = []
    for script in sorted(harness.glob("*.py")):
        if not declared_dependencies(script):
            continue
        lock = script.with_name(script.name + ".lock")
        tracked = (
            _git(
                repo, "ls-files", "--error-unmatch", str(lock.relative_to(repo))
            ).returncode
            == 0
        )
        if not tracked:
            problems.append(
                f"{script.name}: declares dependencies but {lock.name} is not committed"
            )
    return problems


def main() -> int:
    problems = check_fixtures(FIXTURES, REGISTER, REPO_ROOT) + check_locks(
        HARNESS, REPO_ROOT
    )
    for problem in problems:
        print(problem)
    print(
        "fixture check passed"
        if not problems
        else f"fixture check failed: {len(problems)} problem(s)"
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
