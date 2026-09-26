"""The canonical fixtures regenerate byte for byte (Stage 3 spec: Canonical fixtures,
Verification (plan A), item 3).

A difference in the document, elements, masks, or any other manifest field is a change
to canonical output: it needs a new canonicalization version, never a regenerated
walker-1 file. A difference only in the manifest's lxml, libxml2, or Python version is
the environment: regenerate.
"""

import json
from pathlib import Path

import pytest
from earnings_ingestion.canonical import Canonicalized, canonicalize
from earnings_ingestion.canonical.serialize import to_fixture_json

REPO = Path(__file__).resolve().parents[2]
RELEASES = REPO / "tests" / "fixtures" / "releases"
CANONICAL = REPO / "tests" / "fixtures" / "canonical"
FIXTURE_IDS = sorted(path.parent.name for path in RELEASES.glob("*/source.html"))
REGENERATE = (
    "uv run --locked --all-packages python"
    " tests/integration/regenerate_canonical_fixtures.py"
)
ENVIRONMENT = frozenset({"lxml_version", "libxml2_version", "python_version"})


def test_every_release_has_exactly_one_canonical_fixture() -> None:
    assert sorted(path.stem for path in CANONICAL.glob("*.json")) == FIXTURE_IDS


@pytest.mark.parametrize("fixture", FIXTURE_IDS)
def test_the_canonical_fixture_regenerates_byte_for_byte(fixture: str) -> None:
    raw = (RELEASES / fixture / "source.html").read_bytes()
    result = canonicalize(raw, source_document_id=fixture, media_type="text/html")
    assert isinstance(result, Canonicalized), result
    regenerated = to_fixture_json(result)
    committed = (CANONICAL / f"{fixture}.json").read_bytes().decode("utf-8")
    if regenerated == committed:
        return
    old, new = json.loads(committed), json.loads(regenerated)
    manifest = sorted(
        key
        for key in old["manifest"].keys() | new["manifest"].keys()
        if old["manifest"].get(key) != new["manifest"].get(key)
    )
    changed = [key for key in ("document", "elements", "masks") if old[key] != new[key]]
    if changed or not set(manifest) <= ENVIRONMENT:
        pytest.fail(
            f"{fixture}: canonical output changed ({', '.join(changed + manifest)})."
            " That needs a new canonicalization version (walker-2) with its own"
            " fixtures; never regenerate walker-1's."
        )
    pytest.fail(
        f"{fixture}: only the environment differs ({', '.join(manifest)}), and the"
        f" canonical output does not. Regenerate with {REGENERATE}."
    )
