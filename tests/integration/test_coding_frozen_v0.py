"""Frozen-v0 plumbing against invented evidence; no semantic-quality claim."""

from datetime import UTC, datetime
from pathlib import Path

from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    TextSpan,
    digest,
    sha256_hex,
)
from earnings_themes import codebook as codebook_module
from earnings_themes.anchoring import Bundle
from earnings_themes.codebook import codebook_hash, load_codebook
from earnings_themes.coding.adapters import ScriptedClassifier
from earnings_themes.coding.cache import CodingCache
from earnings_themes.coding.records import CodingCeilings, CodingPolicy
from earnings_themes.coding.run import propose_run
from earnings_themes.extraction.adapters import ModelReply, ScriptedAdapter
from earnings_themes.extraction.prompt import parse_template
from earnings_themes.extraction.records import Ceilings, ExtractionPolicy, Parameters
from earnings_themes.extraction.run import extract_run
from earnings_themes.extraction.store import StoredRun
from earnings_themes.support.records import (
    JudgeIdentity,
    RuntimeIdentity,
    SupportSources,
)

REPO = Path(__file__).resolve().parents[2]
PINNED_HASH = "635975d1ec952cf5719ea3b473870f96e7e3a52bc3015cc1ac5725aa80ec1e79"


def test_frozen_v0_fake_proposals_and_zero_inference_replay(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("protected_resolution_or_discovery_forbidden")

    monkeypatch.setattr(codebook_module, "_example", forbidden)
    monkeypatch.setattr(codebook_module, "validate_codebook", forbidden)
    monkeypatch.setattr(Path, "glob", forbidden)
    monkeypatch.setattr(Path, "rglob", forbidden)
    book = load_codebook(REPO / "codebooks/djia-pilot/codebook-v0.toml")
    assert (
        book.codebook_id,
        book.codebook_version,
        book.content_hash,
        len(book.themes),
    ) == ("djia-pilot", 0, PINNED_HASH, 22)
    assert sum(theme.parent_id is not None for theme in book.themes) == 4
    assert (
        book.rules.multi_label
        == "A claim takes every theme it fits, each as its own assignment row; where a sub-theme fits, code the sub-theme instead of its parent."
    )
    text = "Vela added equipment and received more orders."
    document = CanonicalDocument.create(
        source_document_id="invented-v0-plumbing",
        canonicalization_version="invented-1",
        canonical_text=text,
    )
    element = DocumentElement.create(
        document, ElementType.PARAGRAPH, TextSpan(start=0, end=len(text))
    )
    bundle = Bundle("invented-v0-plumbing", document, (element,), ())
    template = parse_template((REPO / "prompts/extraction/pointer-1.md").read_text())
    extraction = extract_run(
        (bundle,),
        ScriptedAdapter(
            lambda request: ModelReply(
                model="scripted",
                text='{"candidates":[{"quote_labels":["U1"],"claim":"An invented operating change."}]}',
            )
        ),
        ExtractionPolicy(),
        template,
        Ceilings(requests_per_document=2, requests_per_run=2, tokens_per_run=10000),
        run_id="invented-v0-extraction",
        started_at=datetime(2026, 10, 5, tzinfo=UTC),
        software={"fixture": "1"},
    )
    sources = SupportSources(
        StoredRun.of(extraction), (bundle,), book, digest("invented v0 provenance")
    )
    identity = JudgeIdentity(
        family="invented-v0-classifier",
        hosting="scripted",
        weight_license=None,
        input_limit=100000,
        output_limit=2048,
        runtime=RuntimeIdentity(
            model_id="scripted",
            revision="fixture-1",
            files=(),
            runtime="scripted",
            runtime_version="1",
            device="cpu",
            precision="float32",
            encoding_version="fixture-1",
        ),
    )
    prompt = (REPO / "prompts/coding/deductive-1.md").read_text()
    policy = CodingPolicy(
        prompt_text=prompt,
        prompt_hash=sha256_hex(prompt.encode()),
        parameters=Parameters(max_tokens=64),
    )
    roots = tuple(
        sorted(theme.theme_id for theme in book.themes if theme.parent_id is None)
    )[:2]
    import json

    classifier = ScriptedClassifier(
        lambda request: ModelReply(
            model="scripted", text=json.dumps({"theme_ids": roots, "attributes": {}})
        ),
        lambda request: 5,
        identity,
    )
    ceilings = CodingCeilings(
        requests_per_claim=2,
        requests_per_document=20,
        requests_per_run=40,
        tokens_per_document=100000,
        tokens_per_run=200000,
    )
    order = tuple((claim.doc_id, claim.claim_id) for claim in sources.stored_run.claims)

    def run(classifier, mode):
        return propose_run(
            "invented-v0-coding",
            sources,
            order,
            classifier,
            policy,
            ceilings,
            cache=CodingCache(tmp_path / "raw", mode),
            started_at=datetime(2026, 10, 5, tzinfo=UTC),
            software={"lock_hash": digest("invented lock")},
        )

    live = run(classifier, "live")
    assert len(classifier.requests) == len(live.attempts) == 1
    assert tuple(target.theme_id for target in live.targets) == roots
    assert all(target.codebook == live.record.codebook for target in live.targets)
    assert live.record.codebook.content_hash == codebook_hash(book) == PINNED_HASH
    replay_classifier = ScriptedClassifier(forbidden, forbidden, identity)
    replay = run(replay_classifier, "replay")
    assert replay.proposals == live.proposals
    assert replay.attributes == live.attributes and replay.novelty == live.novelty
    assert replay_classifier.requests == []
    assert replay.record.requests == replay.record.charged_tokens == 0
    assert replay.record.cache_hits == 1
    assert replay.record.codebook.content_hash == PINNED_HASH
