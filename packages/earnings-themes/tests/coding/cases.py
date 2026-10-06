"""In-memory invented coding inputs produced by the real extraction seam."""

import json
from collections import deque
from datetime import UTC, date, datetime
from types import SimpleNamespace

from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    TextSpan,
    digest,
)
from earnings_themes.anchoring import Bundle
from earnings_themes.codebook import (
    Approval,
    Codebook,
    CodebookRules,
    CodebookStatus,
    DraftingAid,
    Example,
    Theme,
    codebook_hash,
)
from earnings_themes.extraction.adapters import ModelReply, ScriptedAdapter
from earnings_themes.extraction.prompt import PromptTemplate
from earnings_themes.extraction.records import Ceilings, ExtractionPolicy
from earnings_themes.extraction.run import extract_run
from earnings_themes.extraction.store import StoredRun
from earnings_themes.support.records import SupportSources


def invented_bundle(source_id: str = "invented-coding") -> Bundle:
    text = "Lumen added a press and served more orders."
    document = CanonicalDocument.create(
        source_document_id=source_id,
        canonicalization_version="invented-1",
        canonical_text=text,
    )
    element = DocumentElement.create(
        document, ElementType.PARAGRAPH, TextSpan(start=0, end=len(text))
    )
    return Bundle(source_id, document, (element,), ())


def invented_codebook(base: Codebook) -> Codebook:
    themes = tuple(
        Theme(
            theme_id=theme_id,
            label=label,
            definition=definition,
            inclusion_rules=(inclusion,),
            exclusion_rules=(exclusion,),
            positive_examples=(
                Example(synthetic=True, text="An invented positive illustration."),
            ),
            hard_negatives=(
                Example(synthetic=True, text="An invented unrelated illustration."),
            ),
            sector_applicability="all",
        )
        for theme_id, label, definition, inclusion, exclusion in (
            (
                "capacity",
                "Capacity",
                "Changes to productive equipment or facilities.",
                "Explicit equipment or facility expansion.",
                "Orders without equipment changes.",
            ),
            (
                "demand",
                "Demand",
                "Changes to customer orders.",
                "Explicit customer order changes.",
                "Equipment without order changes.",
            ),
        )
    )
    book = Codebook(
        codebook_id="invented-coding",
        codebook_version=0,
        status=CodebookStatus.APPROVED,
        content_hash="0" * 64,
        discovery_corpus=base.discovery_corpus,
        rules=CodebookRules(
            multi_label="Allow each independently fitting theme.",
            boilerplate="Retain masks for later analysis.",
        ),
        approval=Approval(
            approver="fixture",
            approved_on=date(2026, 10, 5),
            adr="docs/adr/invented-fixture.md",
        ),
        drafting_aid=DraftingAid(model_id="scripted", drafted_on=date(2026, 10, 5)),
        themes=themes,
    )
    return book.model_copy(update={"content_hash": codebook_hash(book)})


def make_sources(
    book: Codebook,
    bundle: Bundle,
    template: PromptTemplate,
    *,
    other_bundles=(),
    quote_labels=("U1",),
    claim_texts=("An invented operating claim.",),
) -> SupportSources:
    adapter = ScriptedAdapter(
        lambda request: ModelReply(
            text=json.dumps(
                {
                    "candidates": [
                        {
                            "quote_labels": quote_labels,
                            "claim": claim,
                        }
                        for claim in claim_texts
                    ]
                }
            ),
            model="scripted",
        )
    )
    result = extract_run(
        (bundle, *other_bundles),
        adapter,
        ExtractionPolicy(),
        template,
        Ceilings(requests_per_document=2, requests_per_run=2, tokens_per_run=10000),
        run_id="invented-extraction",
        started_at=datetime(2026, 10, 5, tzinfo=UTC),
        software={"fixture": "1"},
    )
    return SupportSources(
        StoredRun.of(result),
        (bundle, *other_bundles),
        book,
        digest("invented provenance"),
    )


def make_proposal_job(sources, policy, identity, root):
    """Use only the public runner; callbacks and token counts are invented."""

    def run(replies, cache_mode="live", *, ceilings=None, claim_order=None):
        from earnings_themes.coding.adapters import ScriptedClassifier
        from earnings_themes.coding.cache import CodingCache
        from earnings_themes.coding.records import CodingCeilings
        from earnings_themes.coding.run import propose_run

        queue = deque(replies)

        def script(request):
            value = queue.popleft()
            if isinstance(value, ModelReply):
                return value
            if isinstance(value, Exception):
                raise value
            return ModelReply(
                model=identity.runtime.model_id,
                text=value if isinstance(value, str) else json.dumps(value),
            )

        classifier = ScriptedClassifier(script, lambda request: 5, identity)
        result = propose_run(
            "invented-coding-run",
            sources,
            tuple((c.doc_id, c.claim_id) for c in sources.stored_run.claims)
            if claim_order is None
            else claim_order,
            classifier,
            policy,
            ceilings
            or CodingCeilings(
                requests_per_claim=2,
                requests_per_document=20,
                requests_per_run=40,
                tokens_per_document=100000,
                tokens_per_run=200000,
            ),
            cache=CodingCache(root / "classifier-cache", cache_mode),
            started_at=datetime(2026, 10, 5, tzinfo=UTC),
            software={"fixture": "1", "lock_hash": digest("invented lock")},
        )
        return result, len(classifier.requests)

    return SimpleNamespace(run=run, sources=sources, root=root)


def make_support_parts(contribution="supporting", *, score=0.25):
    """Scripted Stage 8 inputs; no fabricated processing outcome."""
    from earnings_themes.support.judges import ScriptedJudge
    from earnings_themes.support.records import (
        JudgeIdentity,
        RuntimeIdentity,
        ScorerIdentity,
    )
    from earnings_themes.support.scorers import ScoreReply, ScriptedScorer

    runtime = RuntimeIdentity(
        model_id="invented-support",
        revision="fixture-1",
        files=(),
        runtime="scripted",
        runtime_version="1",
        device="cpu",
        precision="float32",
        encoding_version="fixture-1",
    )
    scorer_id = ScorerIdentity(kind="scripted", runtime=runtime, input_limit=100000)
    scorer = ScriptedScorer(
        lambda request: ScoreReply(
            score=score,
            reason=None,
            input_tokens=5,
            latency_ms=1,
            identity=scorer_id,
            input_hash=request.input_hash,
        ),
        lambda request: 5,
        scorer_id,
    )

    def answer(request):
        blocks = json.loads(request.messages[1].content)
        evidence = next(b["quoted_evidence"] for b in blocks if "quoted_evidence" in b)
        return ModelReply(
            model=runtime.model_id,
            text=json.dumps(
                {
                    "claim_support": "supported",
                    "theme_fit": "fits",
                    "joint_support_score": 0.25,
                    "quote_assessments": [
                        {
                            "quote_id": q["quote_id"],
                            "contribution": contribution.get(
                                q["quote_id"], "supporting"
                            )
                            if isinstance(contribution, dict)
                            else contribution,
                        }
                        for q in evidence
                    ],
                    "reason_codes": [],
                    "summary": "Invented fixture assessment.",
                }
            ),
        )

    panel = tuple(
        ScriptedJudge(
            answer,
            lambda request: 5,
            JudgeIdentity(
                family=f"invented-family-{i}",
                runtime=runtime,
                input_limit=100000,
                output_limit=2048,
                hosting="scripted",
                weight_license=None,
            ),
        )
        for i in range(2)
    )
    return scorer, panel


def make_assessed_case(
    proposals,
    sources,
    root,
    *,
    contribution="supporting",
    parts=None,
    ceilings=None,
    targets=None,
):
    from pathlib import Path

    from earnings_core import sha256_hex
    from earnings_themes.extraction.records import Parameters
    from earnings_themes.support import assess_run, read_support_run, write_support_run
    from earnings_themes.support.cache import SupportCache
    from earnings_themes.support.records import SupportCeilings, SupportPolicy

    scorer, panel = parts or make_support_parts(contribution)
    prompt = (
        Path(__file__).resolve().parents[4] / "prompts/support/judge-1.md"
    ).read_text(encoding="utf-8")
    policy = SupportPolicy(
        support_version="semantic-support/1",
        prompt_text=prompt,
        prompt_hash=sha256_hex(prompt.encode("utf-8")),
        parameters=Parameters(max_tokens=64),
    )
    result = assess_run(
        "invented-support-run",
        sources,
        proposals.targets if targets is None else targets,
        scorer,
        panel,
        policy,
        ceilings
        or SupportCeilings(
            scorer_per_target=40,
            scorer_per_document=40,
            scorer_per_run=40,
            judge_per_target=40,
            judge_per_document=40,
            judge_per_run=40,
            tokens_per_document=200000,
            tokens_per_run=200000,
        ),
        extractor_family="invented-extractor",
        cache=SupportCache(root / "support-cache", "live"),
        started_at=datetime(2026, 10, 5, tzinfo=UTC),
        software={"fixture": "1", "lock_hash": digest("invented lock")},
    )
    write_support_run(root / "support", result, sources)
    stored = read_support_run(root / "support")
    case = SimpleNamespace(
        proposals=proposals,
        sources=sources,
        support=stored,
        result=result,
        scorer=scorer,
        panel=panel,
        context_quote_ids=tuple(e.quote_id for e in stored.evidence)
        if contribution == "contextual"
        else (),
    )

    def decide(policy=None):
        from earnings_themes.coding.decide import decide_assignments

        return decide_assignments(case.proposals, case.support, case.sources, policy)

    case.decide = decide
    return case


class FixturePolicy:
    """Explicit fixture-only acceptance, never a package default."""

    def __init__(self, proposals, support):
        from earnings_themes.coding.records import PolicyReference

        self.reference = PolicyReference(
            policy_id="fixture-only",
            policy_hash=digest("fixture-only/1"),
            kind="fixture",
            codebook=support.record.codebook,
            classifier_configuration_hash=proposals.record.configuration_hash,
            support_configuration_hash=support.record.configuration_hash,
            calibration_reference=None,
        )
        self.vote_quote_ids = None

    def evaluate(self, view):
        from earnings_themes.coding.records import PolicyVote

        ids = (
            view.eligible_quote_ids
            if self.vote_quote_ids is None
            else self.vote_quote_ids
        )
        return PolicyVote(action="accept", supporting_quote_ids=ids)


def make_coding_run(case, policy):
    """Assemble actual Task 6/7 outputs without mutating the proposal manifest."""
    from collections import Counter

    from earnings_themes.coding.assignments import project_assignments
    from earnings_themes.coding.records import CodingRun, CodingRunRecord

    decisions = case.decide(policy)
    assignments, links = project_assignments(decisions, case.support)
    proposal = case.proposals
    record = CodingRunRecord(
        **proposal.record.model_dump(),
        proposal_hash=decisions.proposal_hash,
        support_run_id=case.support.record.run_id,
        support_run_hash=decisions.support_run_hash,
        support_configuration_hash=case.support.record.configuration_hash,
        policy=decisions.policy,
        counts_by_decision=tuple(
            sorted(Counter(r.status for r in decisions.decisions).items())
        ),
        counts_by_decision_reason=tuple(
            sorted(Counter(r.reason for r in decisions.decisions).items())
        ),
    )
    return CodingRun(
        record,
        proposal.classifications,
        proposal.attempts,
        proposal.proposals,
        proposal.attributes,
        decisions.decisions,
        assignments,
        links,
        proposal.novelty,
    )
