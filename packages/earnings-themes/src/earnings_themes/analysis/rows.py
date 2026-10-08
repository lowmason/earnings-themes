"""Current, document-qualified analytical projection without aggregation or I/O."""

from collections.abc import Sequence
from dataclasses import fields

import polars as pl
from earnings_core import TextSpan, digest, sha256_hex

from earnings_themes.anchoring import mask_id
from earnings_themes.coding.records import CodingRun

from .consume import reverify_analysis_inputs
from .problems import AnalysisError
from .records import (
    TABLE_SCHEMAS,
    AnalysisTables,
    BoundAnalysis,
    ClaimAudit,
    ClaimEvidence,
    ClassificationAudit,
    CopyRow,
    DecisionAudit,
    Observation,
    QuoteAudit,
    RejectionAudit,
)


def _run_hash(run: CodingRun) -> str:
    return digest(
        {
            field.name: getattr(run, field.name).model_dump(mode="json")
            if field.name == "record"
            else [row.model_dump(mode="json") for row in getattr(run, field.name)]
            for field in fields(run)
        }
    )


def _processing_fingerprint(bound: BoundAnalysis, doc_id: str) -> str:
    """Compare outcomes/evidence, excluding document-specific IDs and cache counts.

    Raw scores and wording of model rationales are not acceptance outcomes.
    Multiplicity of claims and actual span occurrences remains significant.
    """
    inputs = bound.inputs
    source = inputs.sources.stored_run
    coding = inputs.coding
    bundle = next(b for b in inputs.sources.bundles if b.document.doc_id == doc_id)
    quotes = {q.quote_id: q for q in source.quotes if q.span.doc_id == doc_id}

    def spans(quote_ids: Sequence[str]) -> list[tuple[int, int]]:
        return sorted((quotes[q].span.start, quotes[q].span.end) for q in quote_ids)

    claims = {c.claim_id: c for c in source.claims if c.doc_id == doc_id}
    claim_keys = {
        key: (sha256_hex(claim.claim.encode("utf-8")), spans(claim.quote_ids))
        for key, claim in claims.items()
    }
    documents = [d for d in source.documents if d.doc_id == doc_id]
    states = [
        (a.state, a.missing_reason, a.failure_reason)
        for a in bound.acquisition
        if a.doc_id == doc_id
    ]
    material = {
        "states": states,
        "documents": [
            d.model_dump(mode="json", exclude={"doc_id", "canonical_hash"})
            for d in documents
        ],
        "windows": sorted(
            (w.start, w.end, w.outcome.value, w.reason.value if w.reason else None)
            for w in source.windows
            if w.doc_id == doc_id
        ),
        "quotes": sorted(
            (
                q.span.start,
                q.span.end,
                sha256_hex(
                    bundle.document.canonical_text[q.span.start : q.span.end].encode(
                        "utf-8"
                    )
                ),
            )
            for q in quotes.values()
        ),
        "masks": sorted(
            (m.span.start, m.span.end, m.category.value, m.policy_id, m.policy_version)
            for m in bundle.masks
        ),
        "claims": sorted(digest(key) for key in claim_keys.values()),
        "classifications": sorted(
            digest((claim_keys[c.claim_id], c.status, c.reason, c.theme_ids))
            for c in coding.classifications
            if c.doc_id == doc_id
        ),
        "decisions": sorted(
            digest(
                (
                    claim_keys[d.claim_id],
                    d.theme_id,
                    d.status,
                    d.reason,
                    d.support_status,
                    d.flags,
                    d.missing,
                    spans(d.supporting_quote_ids),
                )
            )
            for d in bound.decisions.decisions
            if d.doc_id == doc_id
        ),
        "rejections": sorted(
            digest((r.window_id, r.attempt, r.candidate_index, r.reason))
            for r in source.rejections
            if r.doc_id == doc_id
        ),
    }
    return digest(material)


def _copy_rows(bound: BoundAnalysis) -> tuple[CopyRow, ...]:
    metadata = {row.doc_id: row for row in bound.metadata}
    parents = {doc_id: doc_id for doc_id in metadata}

    def root(doc_id: str) -> str:
        while parents[doc_id] != doc_id:
            doc_id = parents[doc_id]
        return doc_id

    def join(doc_ids: Sequence[str]) -> None:
        roots = sorted({root(doc_id) for doc_id in doc_ids})
        for member in roots:
            parents[member] = roots[0]

    exact = {}
    for row in bound.metadata:
        key = (
            row.event_id,
            row.entity_id,
            row.period_end,
            row.doc_type,
            row.canonical_hash,
        )
        exact.setdefault(key, []).append(row.doc_id)
    for members in exact.values():
        join(members)
    assertions_by_doc = {doc_id: [] for doc_id in metadata}
    for assertion in sorted(bound.copies, key=lambda row: row.copy_id):
        subjects = {
            (
                metadata[d].event_id,
                metadata[d].entity_id,
                metadata[d].period_end,
                metadata[d].doc_type,
            )
            for d in assertion.doc_ids
        }
        if len(subjects) != 1:
            raise AnalysisError("input_changed")
        join(assertion.doc_ids)
        for doc_id in assertion.doc_ids:
            assertions_by_doc[doc_id].append(assertion)
    groups = {}
    for doc_id in sorted(metadata):
        groups.setdefault(root(doc_id), []).append(doc_id)
    rows = []
    for members in groups.values():
        assertions = {a.copy_id: a for d in members for a in assertions_by_doc[d]}
        group = "disclosure-" + digest(
            {
                "rule": bound.inputs.analysis_policy.dedup_rule,
                "documents": [metadata[d].model_dump(mode="json") for d in members],
                "assertions": [
                    assertions[key].model_dump(mode="json")
                    for key in sorted(assertions)
                ],
            }
        )
        conflict = len({_processing_fingerprint(bound, d) for d in members}) > 1
        for doc_id in members:
            assertion = next(iter(assertions_by_doc[doc_id]), None)
            rows.append(
                CopyRow(
                    doc_id=doc_id,
                    event_id=metadata[doc_id].event_id,
                    disclosure_group=group,
                    representative_doc_id=members[0],
                    canonical_hash=metadata[doc_id].canonical_hash,
                    copy_assertion_id=assertion.copy_id if assertion else None,
                    copy_assertion_hash=digest(assertion.model_dump(mode="json"))
                    if assertion
                    else None,
                    rule_version=bound.inputs.analysis_policy.dedup_rule,
                    status="copy_processing_conflict" if conflict else "consistent",
                )
            )
    return tuple(rows)


def _quote_rows(bound: BoundAnalysis) -> tuple[QuoteAudit, ...]:
    source = bound.inputs.sources.stored_run
    bundles = {b.document.doc_id: b for b in bound.inputs.sources.bundles}
    metadata = {m.doc_id: m for m in bound.metadata}
    rows = []
    for quote in source.quotes:
        span = quote.span
        bundle = bundles[span.doc_id]
        meta = metadata[span.doc_id]
        current_masks = tuple(
            sorted(
                mask_id(m)
                for m in bundle.masks
                if m.span.overlaps(TextSpan(start=span.start, end=span.end))
            )
        )
        rows.append(
            QuoteAudit(
                doc_id=span.doc_id,
                quote_id=quote.quote_id,
                canonical_hash=span.canonical_hash,
                start=span.start,
                end=span.end,
                element_id=span.element_id,
                validator_version=span.validator_version,
                mask_ids=current_masks,
                source_run_id=source.record.run_id,
                source_run_hash=bound.decisions.source_run_hash,
                metadata_ref=digest(meta.model_dump(mode="json")),
                quote_text=bundle.document.canonical_text[span.start : span.end]
                if meta.retain_text
                else None,
            )
        )
    return tuple(rows)


def _original_rows(bound: BoundAnalysis) -> dict[str, tuple]:
    inputs = bound.inputs
    source = inputs.sources.stored_run
    coding = inputs.coding
    metadata = {m.doc_id: m for m in bound.metadata}
    claims = {(c.doc_id, c.claim_id): c for c in source.claims}
    elements = {
        b.document.doc_id: {e.element_id for e in b.elements}
        for b in inputs.sources.bundles
    }
    return {
        "claims": tuple(
            ClaimAudit(
                doc_id=c.doc_id,
                claim_id=c.claim_id,
                window_id=c.window_id,
                attempt_id=f"a-{c.window_id}-{c.attempt}",
                interpretation_hash=sha256_hex(c.claim.encode("utf-8")),
                interpretation=c.claim if metadata[c.doc_id].retain_text else None,
                original_quote_ids=c.quote_ids,
                source_run_id=source.record.run_id,
                source_run_hash=bound.decisions.source_run_hash,
            )
            for c in source.claims
        ),
        "claim_evidence": tuple(
            ClaimEvidence(doc_id=c.doc_id, claim_id=c.claim_id, quote_id=q)
            for c in source.claims
            for q in c.quote_ids
        ),
        "assignment_claims": coding.assignment_claims,
        "classifications": tuple(
            ClassificationAudit(
                **c.model_dump(exclude={"theme_ids"}),
                proposed_theme_ids=c.theme_ids,
            )
            for c in coding.classifications
        ),
        "decisions": tuple(
            DecisionAudit(
                **d.model_dump(exclude={"supporting_quote_ids"}),
                original_quote_ids=claims[(d.doc_id, d.claim_id)].quote_ids,
                supported_quote_ids=d.supporting_quote_ids,
            )
            for d in bound.decisions.decisions
        ),
        "novelty": coding.novelty,
        "rejections": tuple(
            RejectionAudit(
                source_run_id=source.record.run_id,
                doc_id=r.doc_id,
                window_id=r.window_id,
                attempt_id=f"a-{r.window_id}-{r.attempt}"
                if r.attempt is not None
                else None,
                candidate_index=r.candidate_index,
                reason=r.reason,
                element_ids=tuple(e for e in r.element_ids if e in elements[r.doc_id]),
            )
            for r in source.rejections
        ),
    }


def _observations(
    bound: BoundAnalysis, quotes: tuple[QuoteAudit, ...], copies: tuple[CopyRow, ...]
) -> tuple[Observation, ...]:
    inputs = bound.inputs
    quote_lookup = {(q.doc_id, q.quote_id): q for q in quotes}
    metadata = {m.doc_id: m for m in bound.metadata}
    events = {e.event_id: e for e in bound.expected}
    copy_lookup = {c.doc_id: c for c in copies}
    coding_hash = _run_hash(inputs.coding)
    source = inputs.sources.stored_run
    rows = []
    for assignment in inputs.coding.assignments:
        quote = quote_lookup[(assignment.doc_id, assignment.quote_id)]
        meta = metadata[assignment.doc_id]
        event = events[meta.event_id]
        rows.append(
            Observation(
                **quote.model_dump(),
                event_id=event.event_id,
                entity_id=event.entity_id,
                cik=event.cik,
                period_end=event.period_end,
                fiscal_year=event.fiscal_year,
                fiscal_quarter=event.fiscal_quarter,
                doc_type=meta.doc_type,
                speaker_role="not_applicable",
                theme_id=assignment.theme_id,
                assignment_id=assignment.assignment_id,
                codebook_id=assignment.codebook.codebook_id,
                codebook_version=assignment.codebook.codebook_version,
                codebook_hash=assignment.codebook.content_hash,
                headline_eligible=not quote.mask_ids,
                disclosure_group=copy_lookup[assignment.doc_id].disclosure_group,
                policy_kind=assignment.policy_kind,
                policy_hash=assignment.policy_hash,
                policy_scope=inputs.analysis_policy.scope,
                coding_run_id=inputs.coding.record.run_id,
                coding_run_hash=coding_hash,
                support_run_id=inputs.support.record.run_id,
                support_run_hash=bound.decisions.support_run_hash,
                evidence_id="evidence-"
                + digest(
                    (
                        quote.doc_id,
                        quote.quote_id,
                        quote.canonical_hash,
                        quote.start,
                        quote.end,
                        quote.validator_version,
                    )
                ),
                published_at=meta.published_at,
                retrieved_at=meta.retrieved_at,
                extracted_at=source.record.started_at,
            )
        )
    return tuple(rows)


def build_observations(bound: BoundAnalysis) -> AnalysisTables:
    """Rebind current inputs, then project originals and unique accepted spans.

    Completion, coverage, prevalence and publication evidence retain empty typed
    schemas. No empty result is an adjudication of theme absence.
    """
    try:
        if type(bound) is not BoundAnalysis:
            raise AnalysisError("malformed_record")
        current = reverify_analysis_inputs(bound.inputs)
        if current.binding_hash != bound.binding_hash:
            raise AnalysisError("input_changed")
        quotes = _quote_rows(current)
        copies = _copy_rows(current)
        rows = _original_rows(current) | {
            "quotes": quotes,
            "copies": copies,
            "observations": _observations(current, quotes, copies),
        }
        frames = {
            name: pl.DataFrame(
                [row.model_dump(mode="python") for row in rows.get(name, ())],
                schema=schema,
            )
            for name, schema in TABLE_SCHEMAS.items()
        }
        return AnalysisTables(frames)
    except AnalysisError:
        raise
    except Exception:  # noqa: BLE001 - source/policy/model diagnostics remain private
        raise AnalysisError("input_changed") from None
