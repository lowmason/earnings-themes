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
    book: Codebook, bundle: Bundle, template: PromptTemplate, *, other_bundles=()
) -> SupportSources:
    adapter = ScriptedAdapter(
        lambda request: ModelReply(
            text='{"candidates":[{"quote_labels":["U1"],"claim":"An invented operating claim."}]}',
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
