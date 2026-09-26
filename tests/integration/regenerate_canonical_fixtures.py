"""Regenerate tests/fixtures/canonical/ from the Stage 1 fixtures (Stage 3, plan A).

    uv run --locked --all-packages python tests/integration/regenerate_canonical_fixtures.py

Writes ``<fixture_id>.json`` for each release in tests/fixtures/releases/. Run it only
when test_canonical_golden.py says the environment changed and the canonical output did
not; a change to canonical text or elements needs a new canonicalization version
instead. pytest never collects this file.
"""

from pathlib import Path

from earnings_ingestion.canonical import Canonicalized, canonicalize
from earnings_ingestion.canonical.serialize import to_fixture_json

REPO = Path(__file__).resolve().parents[2]
RELEASES = REPO / "tests" / "fixtures" / "releases"
CANONICAL = REPO / "tests" / "fixtures" / "canonical"


def main() -> int:
    CANONICAL.mkdir(exist_ok=True)
    for source in sorted(RELEASES.glob("*/source.html")):
        fixture = source.parent.name
        result = canonicalize(
            source.read_bytes(), source_document_id=fixture, media_type="text/html"
        )
        if not isinstance(result, Canonicalized):
            raise SystemExit(f"{fixture}: {result.reason.value}: {result.detail}")
        target = CANONICAL / f"{fixture}.json"
        target.write_text(to_fixture_json(result), encoding="utf-8", newline="\n")
        print(f"wrote {target.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
