"""Shared inputs for earnings-themes' tests: Stage 1's committed canonical fixtures,
read through earnings-core's contracts, the synthetic document, and the synthetic
codebook; and for the extractor, the prompt template. Tests hold only synthetic text
and Stage 1's fixtures (GS13)."""

import json
from datetime import date
from pathlib import Path

import pytest
from earnings_core import CanonicalDocument, DocumentElement, OverlayMask
from earnings_themes.anchoring import Bundle
from earnings_themes.codebook import Approval, Codebook, CodebookDraft, freeze_codebook
from earnings_themes.extraction.prompt import PromptTemplate, parse_template
from earnings_themes.records import parse
from earnings_themes.synthetic import (
    DEV,
    LATER,
    PIN,
    TEST,
    TRAIN,
    Synthetic,
    build_synthetic,
    codebook_draft,
    synthetic_split,
)

REPO = Path(__file__).resolve().parents[3]
CANONICAL = REPO / "tests" / "fixtures" / "canonical"
TEMPLATE = REPO / "prompts" / "extraction" / "pointer-1.md"
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


@pytest.fixture(scope="module")
def codebook() -> Codebook:
    """``codebook_draft``, frozen over the synthetic pilot's bundles and approved."""
    approval = Approval(
        approver="Lowell Mason",
        approved_on=date(2026, 10, 2),
        adr="docs/adr/0003-approve-pilot-codebook-v0.md",
    )
    made = freeze_codebook(
        parse(codebook_draft(), CodebookDraft, "draft"),
        pin=PIN,
        split=synthetic_split(),
        bundles={e: build_synthetic(e).bundle for e in (TRAIN, DEV, TEST, LATER)},
        approval=approval,
    )
    assert isinstance(made, Codebook)
    return made


@pytest.fixture(scope="session")
def template() -> PromptTemplate:
    """The committed prompt, read by the caller and passed in (ES17)."""
    return parse_template(TEMPLATE.read_text(encoding="utf-8"))
