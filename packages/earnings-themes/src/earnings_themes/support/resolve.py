"""Resolve explicit frozen targets through current exact-span consuming gates.

No source lookup, example dereference, model dispatch, or filesystem operation.
Refusals retain only identities, digests, and fixed reasons.
"""

from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import get_origin

from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    OverlayMask,
    Rejection,
    VerifiedSpan,
    canonical_json,
    digest,
    reverify_span,
    sha256_hex,
)
from pydantic import BaseModel, ValidationError

from earnings_themes.anchoring import Bundle, bundle_problems, mask_id
from earnings_themes.codebook import Codebook, CodebookStatus, codebook_hash
from earnings_themes.extraction.records import Claim, DocumentRecord, Quote, RunRecord
from earnings_themes.extraction.store import StoredRun
from earnings_themes.support.context import context_elements
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import (
    CodebookReference,
    ContextReference,
    EvidenceReference,
    RefusedTarget,
    ResolvedInput,
    ReviewOutcome,
    ReviewStatus,
    SupportSources,
    Target,
    TargetRecord,
    ThemeSnapshot,
)


def _dump(record: BaseModel) -> dict:
    return record.model_dump(mode="json", warnings=False)


def _check_raw(value: object) -> None:
    """JSON serialization must not erase unknown fields or coerce map keys."""
    if isinstance(value, BaseModel):
        if (
            set(value.__dict__) - set(type(value).model_fields)
            or value.__pydantic_extra__
        ):
            raise SupportError("malformed_record")
        if (
            "schema_version" in type(value).model_fields
            and type(value.schema_version) is not int
        ):
            raise SupportError("malformed_record")
        for field, definition in type(value).model_fields.items():
            item = getattr(value, field)
            if definition.annotation is int and type(item) is not int:
                raise SupportError("malformed_record")
            if get_origin(definition.annotation) is tuple and type(item) is not tuple:
                raise SupportError("malformed_record")
            _check_raw(item)
    elif isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise SupportError("malformed_record")
            _check_raw(item)
    elif isinstance(value, tuple | list):
        for item in value:
            _check_raw(item)


def _validated[M: BaseModel](record: M, model: type[M]) -> M:
    try:
        _check_raw(record)
        fields = _dump(record)
        if "schema_version" in fields and type(fields["schema_version"]) is not int:
            raise SupportError("malformed_record")
        return model.model_validate_json(canonical_json(fields))
    except (ValidationError, ValueError, TypeError, AttributeError, OverflowError):
        raise SupportError("malformed_record") from None


def _one(rows: Sequence, missing: str, duplicate: str):
    if not rows:
        raise SupportError(missing)
    if len(rows) != 1:
        raise SupportError(duplicate)
    return rows[0]


def exact_quote(bundle: Bundle, quote: Quote) -> VerifiedSpan:
    """Every link is checked anew, with exact offsets and current mask bindings."""
    again = reverify_span(bundle.document, bundle.elements, quote.span)
    if isinstance(again, Rejection):
        raise SupportError(again.reason.value)
    if quote.quote_id != f"q-{again.start}-{again.end}":
        raise SupportError("invalid_quote")
    masks = tuple(
        sorted(
            mask_id(m)
            for m in bundle.masks
            if m.span.start < again.end and again.start < m.span.end
        )
    )
    if quote.mask_ids != masks:
        raise SupportError("masks_mismatch")
    _validated(quote, Quote)
    return again


def check_theme_graph(codebook: Codebook) -> None:
    """Reject duplicate/reserved themes and dangling or cyclic ancestry."""
    ids = [t.theme_id for t in codebook.themes]
    if len(ids) != len(set(ids)) or "unmatched" in ids:
        raise SupportError("duplicate_theme")
    parents = {t.theme_id: t.parent_id for t in codebook.themes}
    if any(p is not None and p not in parents for p in parents.values()):
        raise SupportError("unknown_parent")
    for first in parents:
        seen, current = set(), first
        while current is not None:
            if current in seen:
                raise SupportError("parent_cycle")
            seen.add(current)
            current = parents[current]


def _frozen_theme(book: Codebook, target: Target) -> ThemeSnapshot:
    book = _validated(book, Codebook)
    expected = target.codebook
    if (book.codebook_id, book.codebook_version, book.content_hash) != (
        expected.codebook_id,
        expected.codebook_version,
        expected.content_hash,
    ) or codebook_hash(book) != book.content_hash:
        raise SupportError("wrong_codebook")
    if book.status != CodebookStatus.APPROVED or book.approval is None:
        raise SupportError("codebook_not_approved")
    check_theme_graph(book)
    if target.theme_id == "unmatched":
        raise SupportError("unknown_theme")
    theme = _one(
        [t for t in book.themes if t.theme_id == target.theme_id],
        "unknown_theme",
        "duplicate_theme",
    )
    return ThemeSnapshot(
        codebook=expected,
        theme_id=theme.theme_id,
        label=theme.label,
        definition=theme.definition,
        parent_id=theme.parent_id,
        inclusion_rules=theme.inclusion_rules,
        exclusion_rules=theme.exclusion_rules,
    )


def _refused(
    target: Target, source_hash: str, reason: str | Sequence[str]
) -> RefusedTarget:
    identity = digest({"target": _dump(target), "source_run_hash": source_hash})
    target_id = "support-" + identity
    record = TargetRecord(
        target_id=target_id,
        target=target,
        source_run_hash=source_hash,
        claim_hash=digest(None),
        input_hash=identity,
        original_quote_ids=(),
        evidence_ids=(),
        theme=None,
    )
    outcome = ReviewOutcome(
        target_id=target_id,
        status=ReviewStatus.REFUSED,
        flags=(),
        missing=(reason,) if isinstance(reason, str) else tuple(dict.fromkeys(reason)),
        signal_ids=(),
        trial_ids=(),
    )
    return RefusedTarget(record, outcome)


def _source_hash(stored_run: StoredRun, provenance_hash: str) -> str:
    try:
        return digest(
            {"record": _dump(stored_run.record), "provenance_hash": provenance_hash}
        )
    except (AttributeError, ValueError, TypeError, OverflowError):
        return digest("malformed_source")


def _redacted_target() -> Target:
    reference = CodebookReference(
        codebook_id="redacted", codebook_version=0, content_hash=digest(None)
    )
    return Target(
        source_run_id="redacted",
        doc_id="redacted",
        claim_id="redacted",
        theme_id="redacted",
        codebook=reference,
    )


def resolve_target(
    stored_run: StoredRun,
    bundles: Sequence[Bundle],
    codebook: Codebook,
    target: Target,
    *,
    provenance_hash: str,
) -> ResolvedInput | RefusedTarget:
    """Resolve all original quote links or refuse the entire requested target."""
    source_hash = _source_hash(stored_run, provenance_hash)
    try:
        target = _validated(target, Target)
    except SupportError:
        safe = _redacted_target()
        return _refused(safe, source_hash, "malformed_record")
    try:
        if (
            not isinstance(provenance_hash, str)
            or len(provenance_hash) != 64
            or any(c not in "0123456789abcdef" for c in provenance_hash)
        ):
            raise SupportError("malformed_record")
        run = _validated(stored_run.record, RunRecord)
        if (
            target.source_run_id != run.run_id
            or digest(_dump(run.configuration)) != run.configuration_hash
        ):
            raise SupportError("wrong_source_run")
        bundle = _one(
            [b for b in bundles if b.document.doc_id == target.doc_id],
            "wrong_document",
            "wrong_document",
        )
        row = _one(
            [r for r in stored_run.documents if r.doc_id == target.doc_id],
            "wrong_document",
            "wrong_document",
        )
        row = _validated(row, DocumentRecord)
        if (
            run.documents.get(target.doc_id) != bundle.document.canonical_hash
            or row.canonical_hash != bundle.document.canonical_hash
        ):
            raise SupportError("wrong_document")
        document = _validated(bundle.document, CanonicalDocument)
        elements = tuple(_validated(e, DocumentElement) for e in bundle.elements)
        masks = tuple(_validated(m, OverlayMask) for m in bundle.masks)
        checked_bundle = replace(
            bundle, document=document, elements=elements, masks=masks
        )
        problems = bundle_problems(checked_bundle)
        if problems:
            raise SupportError(problems[0])
        claim = _one(
            [
                c
                for c in stored_run.claims
                if (c.doc_id, c.claim_id) == (target.doc_id, target.claim_id)
            ],
            "unknown_claim",
            "duplicate_claim",
        )
        claim = _validated(claim, Claim)
        if len(set(claim.quote_ids)) != len(claim.quote_ids):
            raise SupportError("duplicate_quote")
        verified, quote_problems = [], []
        for quote_id in claim.quote_ids:
            try:
                quote = _one(
                    [
                        q
                        for q in stored_run.quotes
                        if (q.span.doc_id, q.quote_id) == (target.doc_id, quote_id)
                    ],
                    "unknown_quote",
                    "duplicate_quote",
                )
                span = exact_quote(checked_bundle, quote)
                verified.append((quote, span))
            except SupportError as error:
                quote_problems.append(str(error))
        if quote_problems:
            return _refused(target, source_hash, quote_problems)
        theme = _frozen_theme(codebook, target)
        evidence = tuple(
            EvidenceReference(
                target_id="pending",
                quote_id=q.quote_id,
                doc_id=span.doc_id,
                canonical_hash=span.canonical_hash,
                element_id=span.element_id,
                start=span.start,
                end=span.end,
                text_hash=sha256_hex(
                    document.canonical_text[span.start : span.end].encode("utf-8")
                ),
                validator_version=span.validator_version,
                mask_ids=q.mask_ids,
            )
            for q, span in sorted(
                verified,
                key=lambda item: (item[1].start, item[1].end, item[0].quote_id),
            )
        )
        context_refs = {}
        for ref in evidence:
            selected = context_elements(checked_bundle, ref.element_id)
            for index, element in enumerate(selected):
                kind = "block" if index == len(selected) - 1 else "heading"
                context = ContextReference(
                    target_id="pending",
                    doc_id=document.doc_id,
                    canonical_hash=document.canonical_hash,
                    element_id=element.element_id,
                    start=element.span.start,
                    end=element.span.end,
                    text_hash=sha256_hex(
                        document.canonical_text[
                            element.span.start : element.span.end
                        ].encode("utf-8")
                    ),
                    kind=kind,
                )
                key = (
                    context.doc_id,
                    context.element_id,
                    context.start,
                    context.end,
                    kind,
                )
                context_refs[key] = context
        contexts = tuple(
            sorted(
                context_refs.values(),
                key=lambda c: (c.doc_id, c.start, c.end, c.element_id, c.kind),
            )
        )
        claim_hash = digest(_dump(claim))
        input_hash = digest(
            {
                "target": _dump(target),
                "source_run_hash": source_hash,
                "claim": _dump(claim),
                "bundle": {
                    "document": _dump(document),
                    "elements": [_dump(e) for e in elements],
                    "masks": [_dump(m) for m in masks],
                },
                "theme": _dump(theme),
                "evidence": [_dump(e) for e in evidence],
                "contexts": [_dump(c) for c in contexts],
            }
        )
        target_id = "support-" + digest(
            {"target": _dump(target), "input_hash": input_hash}
        )
        evidence = tuple(
            e.model_copy(update={"target_id": target_id}) for e in evidence
        )
        contexts = tuple(
            c.model_copy(update={"target_id": target_id}) for c in contexts
        )
        record = TargetRecord(
            target_id=target_id,
            target=target,
            source_run_hash=source_hash,
            claim_hash=claim_hash,
            input_hash=input_hash,
            original_quote_ids=claim.quote_ids,
            evidence_ids=tuple(e.quote_id for e in evidence),
            theme=theme,
        )
        sources = SupportSources(stored_run, tuple(bundles), codebook, provenance_hash)
        return ResolvedInput(record, evidence, contexts, claim.claim, sources)
    except SupportError as error:
        return _refused(target, source_hash, str(error))
    except (AttributeError, ValueError, TypeError, OverflowError):
        return _refused(target, source_hash, "malformed_record")


def reverify_input(input: ResolvedInput) -> ResolvedInput | RefusedTarget:
    """Strictly validate retained input, then repeat the current source gate."""
    sources = getattr(input, "sources", None)
    source_hash = _source_hash(
        getattr(sources, "stored_run", None), getattr(sources, "provenance_hash", None)
    )
    try:
        target = _validated(input.record.target, Target)
    except (SupportError, AttributeError):
        target = _redacted_target()
    try:
        if (
            type(input) is not ResolvedInput
            or type(sources) is not SupportSources
            or type(sources.stored_run) is not StoredRun
            or type(sources.bundles) is not tuple
            or type(input.evidence) is not tuple
            or type(input.contexts) is not tuple
            or type(input.claim) is not str
            or not input.claim.strip()
        ):
            raise SupportError("malformed_record")
        record = _validated(input.record, TargetRecord)
        evidence = tuple(_validated(e, EvidenceReference) for e in input.evidence)
        contexts = tuple(_validated(c, ContextReference) for c in input.contexts)
    except (SupportError, AttributeError, TypeError, ValueError):
        return _refused(target, source_hash, "malformed_record")
    again = resolve_target(
        sources.stored_run,
        sources.bundles,
        sources.codebook,
        record.target,
        provenance_hash=sources.provenance_hash,
    )
    if isinstance(again, RefusedTarget):
        return again
    if (
        again.record != record
        or again.evidence != evidence
        or again.contexts != contexts
        or again.claim != input.claim
    ):
        return _refused(
            again.record.target, again.record.source_run_hash, "input_changed"
        )
    return again
