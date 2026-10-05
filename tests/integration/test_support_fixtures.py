"""Permitted curated inputs: contract translation, never extractor output."""

import importlib
import json
from collections import Counter
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

import pytest
from earnings_core import (
    VALIDATOR_VERSION,
    TextSpan,
    VerifiedSpan,
    digest,
    make_locator,
    parse_span_candidate,
    sha256_hex,
    validate_span,
)
from earnings_themes.anchoring import Bundle, check_pointer
from earnings_themes.codebook import Codebook, load_codebook
from earnings_themes.extraction.records import Quote
from earnings_themes.extraction.store import read_run, write_run
from earnings_themes.gold import load_hard_negatives
from earnings_themes.support.cache import SupportCache
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import ResolvedInput, SupportSources, Target
from earnings_themes.support.resolve import resolve_target
from earnings_themes.support.store import (
    read_support_run,
    reverify_support_run,
    write_support_run,
)

REPO = Path(__file__).resolve().parents[2]
CURATED = REPO / "tests/fixtures/gold/hard-negatives.toml"
# Reuse invented adapters and Stage 1 loaders, never the pilot/gold loaders.
shared = importlib.import_module("packages.earnings-themes.tests.conftest")
support = importlib.import_module("packages.earnings-themes.tests.support.conftest")
cases = importlib.import_module("packages.earnings-themes.tests.support.cases")
runner = importlib.import_module("packages.earnings-themes.tests.support.test_run")
prompts = importlib.import_module("packages.earnings-themes.tests.support.test_prompt")
codebook = shared.codebook
no_network = shared.no_network
scorer_identity = support.scorer_identity
scorer = support.scorer
panel = support.panel
allowance = support.allowance
case = support.case
policy = prompts.policy


def curated_cases(
    path: Path, bundles: Mapping[str, Bundle], codebook: Codebook
) -> tuple[tuple[SupportSources, Target, str], ...]:
    """Translate original permitted pointers with explicit fixture provenance."""
    negatives = load_hard_negatives(path)
    book_binding = (
        codebook.codebook_id,
        codebook.codebook_version,
        codebook.content_hash,
    )
    expected_binding = (
        negatives.codebook.codebook_id,
        negatives.codebook.codebook_version,
        negatives.codebook.content_hash,
    )
    if book_binding != expected_binding or codebook.status.value != "approved":
        raise ValueError("curated_codebook_mismatch")
    file_hash = sha256_hex(path.read_bytes())
    translated = []
    for document in negatives.documents:
        matched = tuple(
            b
            for b in bundles.values()
            if (b.document.doc_id, b.document.canonical_hash)
            == (document.doc_id, document.canonical_hash)
        )
        if len(matched) != 1:
            raise ValueError("curated_bundle_mismatch")
        bundle = matched[0]
        pointer_map = {p.quote_id: p for p in document.quotes}
        id_map = {p.quote_id: f"q-{p.start}-{p.end}" for p in document.quotes}
        for negative in document.hard_negatives:
            quotes = []
            for original_id in negative.quote_ids:
                pointer = pointer_map[original_id]
                if check_pointer(bundle, pointer):
                    raise ValueError("curated_pointer_refused")
                locator = make_locator(
                    bundle.document, TextSpan(start=pointer.start, end=pointer.end)
                )
                candidate = parse_span_candidate(
                    {
                        "doc_id": bundle.document.doc_id,
                        "canonical_hash": bundle.document.canonical_hash,
                        "start": pointer.start,
                        "end": pointer.end,
                        "quote_text": bundle.document.canonical_text[
                            pointer.start : pointer.end
                        ],
                        "element_id": pointer.element_id,
                        "prefix": locator.prefix,
                        "suffix": locator.suffix,
                    }
                )
                span = validate_span(bundle.document, bundle.elements, candidate)
                if not isinstance(span, VerifiedSpan):
                    raise TypeError("curated_span_refused")
                quotes.append(
                    Quote(
                        quote_id=id_map[original_id],
                        span=span,
                        mask_ids=pointer.mask_ids,
                    )
                )
            sources, target = cases.stored_case(
                bundle,
                codebook,
                negative.claim,
                tuple((q.span.start, q.span.end, q.span.element_id) for q in quotes),
            )
            config = sources.stored_run.record.configuration
            config = config.model_copy(
                update={
                    "identity": config.identity.model_copy(
                        update={
                            "adapter_kind": "curated-fixture",
                            "model_id": document.fixture_id,
                        }
                    )
                }
            )
            record = sources.stored_run.record.model_copy(
                update={
                    "run_id": f"curated-{document.fixture_id}-{negative.claim_id}",
                    "configuration": config,
                    "configuration_hash": digest(config.model_dump(mode="json")),
                    "software": {
                        "fixture_sha256": file_hash,
                        "fixture_id": document.fixture_id,
                        "fixture_quote_id_map": json.dumps(id_map, sort_keys=True),
                    },
                }
            )
            claim = sources.stored_run.claims[0].model_copy(
                update={
                    "claim_id": negative.claim_id,
                    "quote_ids": tuple(id_map[q] for q in negative.quote_ids),
                }
            )
            stored = replace(
                sources.stored_run, record=record, quotes=tuple(quotes), claims=(claim,)
            )
            provenance = digest(
                {
                    "curated_sha256": file_hash,
                    "fixture_id": document.fixture_id,
                    "quote_id_map": id_map,
                }
            )
            sources = replace(sources, stored_run=stored, provenance_hash=provenance)
            target = target.model_copy(
                update={
                    "source_run_id": record.run_id,
                    "claim_id": claim.claim_id,
                    "theme_id": negative.theme_id,
                }
            )
            translated.append((sources, target, negative.negative_kind.value))
    return tuple(translated)


@pytest.fixture
def curated(no_network):
    negatives = load_hard_negatives(CURATED)
    bundles = {
        d.fixture_id: shared.fixture_bundle(d.fixture_id) for d in negatives.documents
    }
    frozen = load_codebook(REPO / "codebooks/djia-pilot/codebook-v0.toml")
    yield curated_cases(CURATED, bundles, frozen)
    assert no_network == []


def test_curated_claims_preserve_partial_evidence(curated):
    counts = Counter(kind for _, _, kind in curated)
    assert (len(curated), counts) == (29, {"issuer": 4, "period": 13, "section": 12})
    original = load_hard_negatives(CURATED)
    by_claim = {
        n.claim_id: (d, n) for d in original.documents for n in d.hard_negatives
    }
    partial = 0
    for sources, target, _ in curated:
        document, negative = by_claim[target.claim_id]
        pointers = {p.quote_id: p for p in document.quotes}
        resolved = resolve_target(
            sources.stored_run,
            sources.bundles,
            sources.codebook,
            target,
            provenance_hash=sources.provenance_hash,
        )
        assert isinstance(resolved, ResolvedInput)
        expected = tuple(
            (p.start, p.end, p.element_id, p.quote_sha256, p.mask_ids)
            for q in negative.quote_ids
            for p in (pointers[q],)
        )
        actual = tuple(
            (
                q.span.start,
                q.span.end,
                q.span.element_id,
                sha256_hex(q.span.quote_text.encode()),
                q.mask_ids,
            )
            for q in sources.stored_run.quotes
        )
        claim_unchanged = sources.stored_run.claims[0].claim == negative.claim
        assert (actual, claim_unchanged) == (expected, True)
        assert all(
            ref.validator_version == VALIDATOR_VERSION for ref in resolved.evidence
        )
        assert (
            sources.stored_run.record.configuration.identity.adapter_kind
            == "curated-fixture"
        )
        assert sources.stored_run.record.software["fixture_sha256"] == sha256_hex(
            CURATED.read_bytes()
        )
        elements = {e.element_id: e for e in sources.bundles[0].elements}
        partial += sum(
            (q.span.start, q.span.end)
            != (
                elements[q.span.element_id].span.start,
                elements[q.span.element_id].span.end,
            )
            for q in sources.stored_run.quotes
        )
    assert partial > 0


def test_all_curated_objections_keep_raw_scores(
    curated, scorer, panel, policy, allowance, tmp_path
):
    from earnings_themes.support.allowance import Allowance
    from earnings_themes.support.assess import assess_target

    reasons = {
        "issuer": "wrong_attribution",
        "period": "wrong_period",
        "section": "scope_mismatch",
    }
    for index, (sources, target, kind) in enumerate(curated):
        resolved = cases.resolved_case(sources, target)
        for judge in panel:
            judge.script = cases.negative_reply(reasons[kind])
        result = assess_target(
            resolved,
            scorer,
            panel,
            policy,
            Allowance(allowance.ceilings),
            cache=SupportCache(tmp_path / str(index), "live"),
            extractor_family="invented-extractor",
        )
        diagnostic = (
            result.outcome.status,
            reasons[kind] in result.outcome.flags,
            tuple(s.score for s in result.entailment),
            tuple(a.answer.joint_support_score for a in result.attempts),
        )
        assert diagnostic == ("flagged", True, (0.99, 0.99), (0.9,) * 4)


def test_saved_extraction_support_replay_and_tamper(
    case, scorer, panel, policy, allowance, tmp_path, no_network
):
    sources, target = case
    saved = write_run(tmp_path / "extraction", sources.stored_run, sources.bundles)
    sources = replace(sources, stored_run=read_run(saved))
    first = runner.run(
        (sources, target), scorer, panel, policy, allowance.ceilings, tmp_path / "cache"
    )
    path = write_support_run(tmp_path / "support", first, sources)
    stored = read_support_run(path)
    assert reverify_support_run(stored, sources) == stored.outcomes
    replay = runner.run(
        (sources, target),
        scorer,
        panel,
        policy,
        allowance.ceilings,
        tmp_path / "cache",
        cache=SupportCache(tmp_path / "cache", "replay"),
    )
    assert replay.assessments[0].outcome == first.assessments[0].outcome
    assert (
        replay.record.requests,
        replay.record.evaluations,
        len(scorer.requests),
        tuple(len(j.requests) for j in panel),
    ) == (0, 0, 3, (2, 2))
    quote = sources.stored_run.quotes[0]
    bad = quote.model_copy(
        update={"span": quote.span.model_copy(update={"start": quote.span.start + 1})}
    )
    changed = replace(
        sources,
        stored_run=replace(
            sources.stored_run, quotes=(bad, *sources.stored_run.quotes[1:])
        ),
    )
    refused = runner.run(
        (changed, target),
        scorer,
        panel,
        policy,
        allowance.ceilings,
        tmp_path / "cache",
        cache=SupportCache(tmp_path / "cache", "replay"),
    )
    assert (
        refused.assessments[0].outcome.status,
        refused.record.requests,
        refused.record.evaluations,
    ) == ("refused", 0, 0)
    with pytest.raises(SupportError):
        reverify_support_run(stored, changed)
    assert no_network == []


@pytest.mark.parametrize(
    "lines,claim,reply_options,expected",
    [
        (("Orion reduced delays.",), "Orion reduced delays.", {}, "assessed"),
        (
            ("Orion did not reduce delays.",),
            "Orion reduced delays.",
            {"claim_support": "unsupported", "reasons": ("negation",)},
            "flagged",
        ),
        (
            ("Competitor Lyra reduced delays.",),
            "Orion reduced delays.",
            {"claim_support": "unsupported", "reasons": ("wrong_attribution",)},
            "flagged",
        ),
        (
            ("Last year Orion reduced delays.",),
            "This quarter Orion reduced delays.",
            {"claim_support": "unsupported", "reasons": ("wrong_period",)},
            "flagged",
        ),
        (
            ("Orion reduced delays.",),
            "Orion reduced delays.",
            {"theme_fit": "does_not_fit", "reasons": ("theme_mismatch",)},
            "flagged",
        ),
        (
            ("Orion scheduled a review.",),
            "Orion reduced delays.",
            {
                "claim_support": "unsupported",
                "contribution": "contextual",
                "reasons": ("context_only_support",),
            },
            "flagged",
        ),
        (
            ("Orion scheduled a review.", "Orion reduced delays."),
            "Orion reduced delays.",
            {"contribution": "contextual"},
            "assessed",
        ),
        (
            ("Orion added tooling.", "The tooling reduced delays."),
            "Orion tooling reduced delays.",
            {},
            "assessed",
        ),
        (
            ("Orion added tooling.",),
            "Orion added tooling and doubled output.",
            {
                "claim_support": "unsupported",
                "reasons": ("compound_claim", "partial_support"),
            },
            "flagged",
        ),
    ],
    ids=[
        "positive",
        "negation",
        "competitor",
        "prior-period",
        "wrong-theme-positive",
        "context-only",
        "contextual-quote",
        "distributed",
        "compound-partial",
    ],
)
def test_invented_processing_distinctions(
    codebook,
    scorer,
    panel,
    policy,
    allowance,
    tmp_path,
    no_network,
    lines,
    claim,
    reply_options,
    expected,
):
    source_case = cases.invented_case(codebook, lines, claim)
    for judge in panel:
        judge.script = cases.judge_reply(**reply_options)
    result = runner.run(
        source_case, scorer, panel, policy, allowance.ceilings, tmp_path
    )
    row = result.assessments[0]
    diagnostic = (
        row.outcome.status,
        tuple(s.score for s in row.entailment),
        len(row.attempts),
    )
    assert diagnostic == (expected, (0.99,) * (len(lines) + 1), 4)
    assert no_network == []


def test_partial_panel_and_ceiling_remain_incomplete(
    case, scorer, panel, policy, allowance, tmp_path
):
    panel[0].script = cases.negative_reply("theme_mismatch")
    ceilings = allowance.ceilings.model_copy(update={"judge_per_run": 1})
    result = runner.run(case, scorer, panel, policy, ceilings, tmp_path)
    outcome = result.assessments[0].outcome
    assert outcome.status == "incomplete"
    assert "judge_exhausted" in outcome.missing and "theme_mismatch" in outcome.flags
    assert result.record.counts_by_status == (("incomplete", 1),)
