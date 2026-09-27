"""Regenerate tests/fixtures/events/, the synthetic event corpus (Stage 5, plan 7).

    uv run --locked --all-packages python tests/integration/regenerate_event_fixtures.py

Replaces the whole directory with ``earnings_ingestion.events.fixture``'s output: the
event layer's saved responses, the reviewer's overrides, and the frozen event
manifest, evidence record, and pilot. It reads the synthetic cohort's committed
manifest and writes nothing under tests/fixtures/cohort/. Run it only when
test_event_fixtures.py reports that the committed fixture no longer matches the
generator, and commit the generator change with it. pytest never collects this file.
"""

import shutil
from pathlib import Path

from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.events.fixture import (
    COHORT_MANIFEST,
    FIXTURE_DIR,
    write_fixture,
)

REPO = Path(__file__).resolve().parents[2]


def main() -> int:
    shutil.rmtree(REPO / FIXTURE_DIR, ignore_errors=True)
    frozen = write_fixture(REPO, load_manifest(REPO / COHORT_MANIFEST))
    print(f"wrote {frozen.path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
