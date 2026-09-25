"""Repository paths and fixture identifiers for the Stage 1 parser-fidelity harness.

Nothing here touches the filesystem at import time; the constants are plain paths.
"""

from __future__ import annotations

import re
from pathlib import Path

HARNESS = Path(__file__).resolve().parent
REPO_ROOT = HARNESS.parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "releases"
MANIFEST = FIXTURES / "manifest.toml"
REGISTER = REPO_ROOT / "docs" / "source-register.toml"
DATA_RAW = REPO_ROOT / "data" / "raw"
DISCOVERY = DATA_RAW / "discovery"
DEVSET = DATA_RAW / "devset"
RUNS = REPO_ROOT / "data" / "runs" / "parser-fidelity"
EDGAR_HOME = RUNS / "edgar-home"
LIVE_LOCK = RUNS / "live.lock"

MAX_FIXTURE_BYTES = 1024 * 1024  # F1: each fixture is at most 1 MiB

_ACCESSION = re.compile(r"^\d{10}-\d{2}-\d{6}$")
_FIXTURE_ID = re.compile(r"^\d{10}-\d{2}-\d{6}_[a-z0-9-]+$")


def fixture_id(accession: str, exhibit_type: str) -> str:
    """Accession plus the exhibit type as filed, lowercased, dots replaced by hyphens."""
    if not _ACCESSION.match(accession):
        raise ValueError(f"not an accession number: {accession!r}")
    candidate = f"{accession}_{exhibit_type.strip().lower().replace('.', '-')}"
    if not _FIXTURE_ID.match(candidate):
        raise ValueError(
            f"exhibit type {exhibit_type!r} does not give a valid fixture id"
        )
    return candidate
