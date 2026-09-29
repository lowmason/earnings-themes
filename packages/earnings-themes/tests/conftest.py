"""Shared inputs for earnings-themes' tests: Stage 1's committed canonical fixtures,
read through earnings-core's contracts, and the synthetic document. Tests hold only
synthetic text and Stage 1's fixtures (GS13)."""

import json
from pathlib import Path

import pytest
from earnings_core import CanonicalDocument, DocumentElement, OverlayMask
from earnings_themes.anchoring import Bundle
from earnings_themes.synthetic import Synthetic, build_synthetic

REPO = Path(__file__).resolve().parents[3]
CANONICAL = REPO / "tests" / "fixtures" / "canonical"
FIXTURE_IDS = sorted(path.stem for path in CANONICAL.glob("*.json"))


def fixture_bundle(fixture_id: str) -> Bundle:
    """A Stage 1 canonical fixture, read record by record through the contracts."""
    data = json.loads((CANONICAL / f"{fixture_id}.json").read_text(encoding="utf-8"))

    def read(model, record):
        return model.model_validate_json(json.dumps(record))

    return Bundle(
        name=fixture_id,
        document=read(CanonicalDocument, data["document"]),
        elements=tuple(read(DocumentElement, r) for r in data["elements"]),
        masks=tuple(read(OverlayMask, r) for r in data["masks"]),
    )


@pytest.fixture
def synthetic() -> Synthetic:
    return build_synthetic()


@pytest.fixture(scope="session")
def fixtures() -> dict[str, Bundle]:
    return {fixture_id: fixture_bundle(fixture_id) for fixture_id in FIXTURE_IDS}
