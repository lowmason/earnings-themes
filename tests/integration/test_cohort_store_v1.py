"""The real cohort's frozen v1 against the local store, which only this machine holds:
the test skips without it, so each gate runs it and reads "passed" (plan 26, Task 10).

The saved evidence rebuilds the cohort to the operative hash of its latest frozen
manifest, with no blocking finding. The content hash is not compared: plan 7,
Task 16 changed the source register, so the content hash no longer reproduces, and
Stage 5's records key on the operative hash, which still does. A failure prints
hashes, counts, and IDs only, and cuts a problem line short, since a line can quote
saved text and the log is public.
"""

from collections.abc import Sequence
from pathlib import Path

import pytest
from earnings_ingestion.cohort.build import (
    COHORT_STORE,
    CohortBuild,
    CohortError,
    build,
)
from earnings_ingestion.cohort.config import UNIVERSE_DIR
from earnings_ingestion.cohort.freeze import frozen_manifests
from earnings_ingestion.cohort.identity import operative_hash

REPO = Path(__file__).resolve().parents[2]
SHOWN = 10
"""How many problem lines a failure prints."""
WIDTH = 100
"""How many characters of each problem line a failure prints."""


def described(problems: Sequence[str]) -> str:
    """The count, then each of the first ``SHOWN`` problems cut to ``WIDTH``
    characters. A problem line can quote saved text, so it is never printed whole."""
    lines = "".join(f"\n  {problem[:WIDTH]}" for problem in problems[:SHOWN])
    return f"{len(problems)} problems, the first {min(len(problems), SHOWN)}:{lines}"


def rebuilt() -> CohortBuild:
    """The cohort that the committed files and the saved store support. The failure is
    raised outside the ``except`` block, so that pytest chains no ``CohortError``,
    whose message holds every problem line whole."""
    try:
        return build(REPO)
    except CohortError as error:
        problems = error.problems
    pytest.fail(
        f"the saved store no longer builds the cohort: {described(problems)}\n"
        "run `earnings-pipeline cohort build` for the full lines"
    )


def test_cohort_v1_rebuilds_to_its_operative_hash() -> None:
    if not (REPO / COHORT_STORE).is_dir():
        pytest.skip("data/raw/cohort is not saved here: each gate runs this test")
    built = rebuilt()
    if built.report.blocking:
        pytest.fail(
            "the build has blocking findings: "
            f"{[f.finding_id for f in built.report.blocking]}"
        )
    latest = frozen_manifests(
        REPO / UNIVERSE_DIR / "manifests", built.config.universe.universe_id
    )[-1]
    rebuilt_hash = built.operative_hash  # not in the assert: pytest prints ``built``
    assert rebuilt_hash == operative_hash(latest)
