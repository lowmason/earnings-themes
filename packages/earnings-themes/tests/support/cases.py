"""Invented inputs with exact original spans, including partial spans."""

from datetime import UTC, datetime

from earnings_core import (
    SpanCandidate,
    TextSpan,
    VerifiedSpan,
    digest,
    make_locator,
    validate_span,
)
from earnings_themes.anchoring import mask_id
from earnings_themes.extraction.records import (
    AdapterIdentity,
    Ceilings,
    Claim,
    DocumentOutcome,
    DocumentRecord,
    ExtractionPolicy,
    Quote,
    RunConfiguration,
    RunRecord,
)
from earnings_themes.extraction.store import StoredRun
from earnings_themes.support.records import CodebookReference, SupportSources, Target


def stored_case(bundle, codebook, claim, spans):
    quotes = []
    for start, end, element_id in spans:
        locator = make_locator(bundle.document, TextSpan(start=start, end=end))
        checked = validate_span(
            bundle.document,
            bundle.elements,
            SpanCandidate(
                doc_id=bundle.document.doc_id,
                canonical_hash=bundle.document.canonical_hash,
                start=start,
                end=end,
                element_id=element_id,
                quote_text=bundle.document.canonical_text[start:end],
                prefix=locator.prefix,
                suffix=locator.suffix,
            ),
        )
        assert isinstance(checked, VerifiedSpan)
        masks = tuple(
            sorted(
                mask_id(m)
                for m in bundle.masks
                if m.span.start < end and start < m.span.end
            )
        )
        quotes.append(Quote(quote_id=f"q-{start}-{end}", span=checked, mask_ids=masks))
    config = RunConfiguration(
        identity=AdapterIdentity(adapter_kind="fixture", model_id="invented"),
        policy=ExtractionPolicy(),
        ceilings=Ceilings(
            requests_per_document=1, requests_per_run=1, tokens_per_run=100
        ),
        prompt_sha256=digest("invented"),
        reply_schema_sha256=digest("schema"),
        extractor_version="pointer-traversal/1",
        validator_version=quotes[0].span.validator_version,
    )
    doc = bundle.document
    record = RunRecord(
        run_id="fixture-run",
        started_at=datetime(2026, 10, 5, tzinfo=UTC),
        configuration=config,
        configuration_hash=digest(config.model_dump(mode="json")),
        documents={doc.doc_id: doc.canonical_hash},
        units=len(spans),
        windows=0,
        candidates=1,
        quotes=len(quotes),
        claims=1,
        rejections_by_reason={},
        requests=0,
        cache_hits=0,
        prompt_tokens=0,
        completion_tokens=0,
        unreported=0,
        exhausted=False,
        software={"fixture": "1"},
        exactness_rate=1.0,
    )
    row = DocumentRecord(
        doc_id=doc.doc_id,
        canonical_hash=doc.canonical_hash,
        outcome=DocumentOutcome.COMPLETED,
        units=len(spans),
        windows=0,
        windows_failed=0,
        candidates=1,
        quotes=len(quotes),
        claims=1,
        rejections=0,
    )
    row = DocumentRecord.model_validate_json(row.model_dump_json())
    claim_row = Claim(
        claim_id="claim-1",
        doc_id=doc.doc_id,
        window_id="fixture-window",
        attempt=1,
        claim=claim,
        quote_ids=tuple(q.quote_id for q in quotes),
    )
    run = StoredRun(
        record=record,
        documents=(row,),
        windows=(),
        visits=(),
        quotes=tuple(quotes),
        claims=(claim_row,),
        rejections=(),
    )
    sources = SupportSources(
        run, (bundle,), codebook, digest("invented fixture provenance")
    )
    target = Target(
        source_run_id=record.run_id,
        doc_id=doc.doc_id,
        claim_id=claim_row.claim_id,
        theme_id=codebook.themes[0].theme_id,
        codebook=CodebookReference(
            codebook_id=codebook.codebook_id,
            codebook_version=codebook.codebook_version,
            content_hash=codebook.content_hash,
        ),
    )
    return sources, target


def context_bundle():
    """Invented nested narrative with attribution-only words and repeated evidence."""
    from earnings_core import CanonicalDocument, DocumentElement, ElementType, TextSpan
    from earnings_themes.anchoring import Bundle

    text = "OUTER HEADING\nINNER HEADING\nINVENTED_CONTEXT_ONLY_ASSERTION. Orion improved output. Orion improved output."
    doc = CanonicalDocument.create(
        source_document_id="invented-context",
        canonicalization_version="test-1",
        canonical_text=text,
    )
    elements = []

    def add(kind, start, end, parent=None):
        element = DocumentElement.create(
            doc,
            ElementType(kind),
            TextSpan(start=start, end=end),
            parent_id=None if parent is None else parent.element_id,
        )
        elements.append(element)
        return element

    outer = add("section", 0, len(text))
    add("heading", 0, text.index("\n"), outer)
    inner_start = text.index("INNER HEADING")
    inner = add("section", inner_start, len(text), outer)
    add("heading", inner_start, text.index("\n", inner_start), inner)
    paragraph = add(
        "paragraph", text.index("INVENTED_CONTEXT_ONLY_ASSERTION"), len(text), inner
    )
    first = text.index("Orion")
    sentence = add("sentence", first, first + len("Orion improved output."), paragraph)
    add("sentence", text.index("Orion", first + 1), len(text), paragraph)
    return Bundle("invented-context", doc, tuple(elements), ()), sentence
