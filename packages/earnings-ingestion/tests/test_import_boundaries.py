"""earnings-ingestion imports neither earnings-themes nor the application, and no
browser: browser capture stays behind an optional extra (A §173; B3)."""

import json
import subprocess
import sys

FORBIDDEN = {
    "earnings_themes",
    "earnings_pipeline",
    "selenium",
    "playwright",
    "pyppeteer",
}


def modules_loaded_by(module: str) -> set[str]:
    """Top-level modules a fresh interpreter holds after importing ``module``."""
    code = f"import json, sys, {module}; print(json.dumps(sorted(sys.modules)))"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    return {name.partition(".")[0] for name in json.loads(result.stdout)}


def test_importing_earnings_ingestion_loads_nothing_forbidden() -> None:
    assert modules_loaded_by("earnings_ingestion") & FORBIDDEN == set()
