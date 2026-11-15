"""The parser-fidelity harness's freezes hold in the default suite.

Stage 1's freeze (``FROZEN.toml``) and layout-1's pre-registration
(``layout1-preregistered.toml``, plan 5, PB-13) each record the SHA-256 of the files
they freeze, and each script's ``verify`` fails on a change that its record does not
name:

    python expirements/parser-fidelity/freeze.py verify
    python expirements/parser-fidelity/preregister.py verify

A permitted ``preregister.py amend`` adds a ``[[changes]]`` entry, which ``verify``
accepts but which the committed layout-1 comparison renders in its header, so the
comparison must also be regenerated.

The harness's own tests check these, but the root ``testpaths`` leave ``expirements/``
out, so a change passed the default suite unseen. The checks here run in
subprocesses: the harness imports its modules by bare name and needs pytest's prepend
import mode, which the root suite does not use.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "expirements" / "parser-fidelity"

# Each script prints its line and exits 0 when its record holds.
VERIFIED = {
    "freeze.py": "freeze verified",
    "preregister.py": "pre-registration verified",
}
LAYOUT1_COMPARISON = (
    "expirements/parser-fidelity/test_layout1_report_current.py"
    "::test_the_committed_comparison_is_current"
)


def run_python(*args: str) -> subprocess.CompletedProcess[str]:
    # No -I: it implies -P, which takes the script's directory off sys.path, and the
    # harness imports its sibling modules by bare name.
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("script", VERIFIED)
def test_the_committed_freeze_record_verifies(script: str) -> None:
    result = run_python(str(HARNESS / script), "verify")
    assert result.returncode == 0 and VERIFIED[script] in result.stdout, (
        f"{script} verify exited {result.returncode}:\n"
        f"{result.stdout}{result.stderr}"
        f"restore the frozen bytes, or record a permitted fix with `{script} amend`"
    )


def test_the_committed_layout1_comparison_is_current() -> None:
    result = run_python(
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "--import-mode=prepend",
        "-m",
        "not live and not browser",
        "-q",
        LAYOUT1_COMPARISON,
    )
    # A skip also exits 0, so the one test must have passed.
    assert result.returncode == 0 and re.search(r"\b1 passed\b", result.stdout), (
        f"{LAYOUT1_COMPARISON} exited {result.returncode}:\n"
        f"{result.stdout}{result.stderr}"
    )
