"""earnings-ingestion imports neither earnings-themes nor the application, and no
browser: browser capture stays behind an optional extra (A §173; B3).

Only ``earnings_ingestion.browser.selenium_capture`` may load a browser library, and
only when something imports it; tests/contracts/test_import_scan.py checks the source
statically as well. The cohort's offline path, from saved artifacts to a frozen
manifest, loads no network client (A §410), and neither does pdftext-1's PDF reader.

Stage 5 loads no acquisition library (R14.5): its readers are the package's own, so
no edgartools, pandas, or pyarrow object reaches the ingestion boundary, and there is
nothing to cast. Its offline path, from saved responses to the frozen pilot, loads no
network client; only discovery, which takes the shared client's ``fetch``, does.
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
        "earnings_ingestion.fetch.client",
        "earnings_ingestion.fetch.robots",
        "earnings_ingestion.sec.client",
        "earnings_ingestion.cohort.build",
        "earnings_ingestion.cohort.pdftext",
        "earnings_ingestion.cohort.web",
    ],
)
def test_importing_ingestion_loads_nothing_forbidden(module: str) -> None:
    assert modules_loaded_by(module) & FORBIDDEN == set()


NETWORK = {
    "httpx",
    "earnings_ingestion.fetch.client",
    "earnings_ingestion.sec.client",
    "earnings_ingestion.cohort.web",
}


def full_modules_loaded_by(module: str) -> set[str]:
    code = f"import json, sys, {module}; print(json.dumps(sorted(sys.modules)))"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    return set(json.loads(result.stdout))


@pytest.mark.parametrize(
    "module",
    [
        "earnings_ingestion.cohort.build",
        "earnings_ingestion.cohort.freeze",
        "earnings_ingestion.cohort.locators",
        "earnings_ingestion.cohort.pdftext",
        "earnings_ingestion.cohort.synthetic",
        "earnings_ingestion.sec.data",
        "earnings_ingestion.sec.urls",
        "earnings_ingestion.fetch.store",
    ],
)
def test_the_offline_cohort_path_loads_no_network_client(module: str) -> None:
    """Building and freezing read saved bytes; they cannot reach the network (A §410)."""
    assert full_modules_loaded_by(module) & NETWORK == set()


ACQUISITION = {"edgar", "pandas", "pyarrow"}
EVENTS = [
    "earnings_ingestion.events.acceptance",
    "earnings_ingestion.events.build",
    "earnings_ingestion.events.discover",
    "earnings_ingestion.events.eligibility",
    "earnings_ingestion.events.evidence",
    "earnings_ingestion.events.filings",
    "earnings_ingestion.events.fixture",
    "earnings_ingestion.events.freeze",
    "earnings_ingestion.events.layer",
    "earnings_ingestion.events.pilot",
    "earnings_ingestion.events.records",
    "earnings_ingestion.events.release",
    "earnings_ingestion.events.saved",
    "earnings_ingestion.events.slots",
    "earnings_ingestion.events.synthetic",
    "earnings_ingestion.sec.companyfacts",
    "earnings_ingestion.sec.filing_index",
    "earnings_ingestion.cohort.identity",
]


@pytest.mark.parametrize("module", EVENTS)
def test_stage_5_loads_no_acquisition_library(module: str) -> None:
    """R14.5: no edgartools, pandas, or pyarrow output crosses the boundary."""
    assert modules_loaded_by(module) & (ACQUISITION | FORBIDDEN) == set()


@pytest.mark.parametrize("module", EVENTS)
def test_the_offline_event_path_loads_no_network_client(module: str) -> None:
    """Building, freezing, and selecting read saved responses (A §410), and
    discovery takes a fetch callable, so it loads no client; only the CLI opens one
    (P6-22; plan 8, P8-12)."""
    assert full_modules_loaded_by(module) & NETWORK == set()
