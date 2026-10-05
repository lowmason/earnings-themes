"""In-memory invented coding inputs produced by the real extraction seam."""

from datetime import UTC, date, datetime

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
    book: Codebook, bundle: Bundle, template: PromptTemplate
) -> SupportSources:
    adapter = ScriptedAdapter(
        lambda request: ModelReply(
            text='{"candidates":[{"quote_labels":["U1"],"claim":"An invented operating claim."}]}',
            model="scripted",
        )
    )
    result = extract_run(
        (bundle,),
        adapter,
        ExtractionPolicy(),
        template,
        Ceilings(requests_per_document=2, requests_per_run=2, tokens_per_run=10000),
        run_id="invented-extraction",
        started_at=datetime(2026, 10, 5, tzinfo=UTC),
        software={"fixture": "1"},
    )
    return SupportSources(
        StoredRun.of(result), (bundle,), book, digest("invented provenance")
    )
