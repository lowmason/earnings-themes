"""The opt-in live verification of the real cohort (P-VL); run with ``-m live``.

It needs EDGAR_IDENTITY and SOURCE_IDENTITY, the curated files under
config/universe/djia/, and the saved artifacts under data/raw/cohort/, and it sends
live requests under both clients' access policies. It never runs by default.
"""

import os
from pathlib import Path

import pytest
from earnings_ingestion.cohort.live import run_live

pytestmark = pytest.mark.live
REPO = Path(__file__).resolve().parents[2]
LIVE_REQUESTS = 60
"""Each client's cap: every terms page, curated page, and robots.txt, with room."""


def test_the_real_cohort_verifies_live() -> None:
    missing = [
        v for v in ("EDGAR_IDENTITY", "SOURCE_IDENTITY") if not os.environ.get(v)
    ]
    if missing:
        pytest.skip(f"set {' and '.join(missing)} outside Git to run this check")
    if not (REPO / "config" / "universe" / "djia" / "evidence.toml").exists():
        pytest.skip("the real cohort is not curated yet")
    result, path = run_live(REPO, max_requests=LIVE_REQUESTS)
    assert path.is_file()
    assert result.build_problems == ()
    assert [c.url for c in result.checks if c.outcome == "failed"] == []
    assert result.blocking_finding_ids == ()
    assert result.rebuilt_content_hash == result.frozen_content_hash
