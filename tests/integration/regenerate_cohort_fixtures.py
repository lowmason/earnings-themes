"""Regenerate tests/fixtures/cohort/, the synthetic cohort (Stage 4, plan 6).

    uv run --locked --all-packages python tests/integration/regenerate_cohort_fixtures.py

Replaces the whole directory with ``earnings_ingestion.cohort.synthetic``'s output:
registers, saved artifacts, curated files, overrides, and the frozen manifest. Run it
only when test_cohort_fixtures.py reports that the committed fixture no longer matches
the generator, and commit the generator change with it. pytest never collects this
file.
"""

import shutil
from pathlib import Path

from earnings_ingestion.cohort.synthetic import FIXTURE_DIR, write_synthetic_cohort

REPO = Path(__file__).resolve().parents[2]


def main() -> int:
    shutil.rmtree(REPO / FIXTURE_DIR, ignore_errors=True)
    manifest = write_synthetic_cohort(REPO, FIXTURE_DIR)
    print(f"wrote {manifest.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
