"""earnings-ingestion imports neither earnings-themes nor the application, and no
browser: browser capture stays behind an optional extra (A §173; B3).

Only ``earnings_ingestion.browser.selenium_capture`` may load a browser library, and
only when something imports it; tests/contracts/test_import_scan.py checks the source
statically as well.
"""

import json
import subprocess
import sys

import pytest

FORBIDDEN = {
    "earnings_themes",
    "earnings_pipeline",
    "selenium",
    "websocket",
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


@pytest.mark.parametrize(
    "module",
    [
        "earnings_ingestion",
        "earnings_ingestion.browser",
        "earnings_ingestion.browser.install",
        "earnings_ingestion.browser.renderer",
        "earnings_ingestion.browser.serialize",
        "earnings_ingestion.browser.store",
        "earnings_ingestion.layout",
        "earnings_ingestion.layout.extract",
    ],
)
def test_importing_ingestion_loads_nothing_forbidden(module: str) -> None:
    assert modules_loaded_by(module) & FORBIDDEN == set()
