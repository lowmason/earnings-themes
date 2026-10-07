"""Document completeness from expected structural and downstream work, without I/O."""

from collections import Counter

from earnings_core import digest

from earnings_themes.anchoring import Bundle
from earnings_themes.coding.decide import REQUIRED_TRIALS
from earnings_themes.extraction.records import DocumentOutcome, WindowOutcome
from earnings_themes.extraction.windows import plan_windows

from .consume import reverify_analysis_inputs
from .problems import AnalysisError
from .records import BoundAnalysis, DocumentCompletion, QuoteAudit
from .rows import _copy_rows, _quote_rows, _run_hash


def checked_bound(bound: BoundAnalysis) -> BoundAnalysis:
    """A prior binding never substitutes for current consuming gates."""
    if type(bound) is not BoundAnalysis:
        raise AnalysisError("malformed_record")
    current = reverify_analysis_inputs(bound.inputs)
    if current.binding_hash != bound.binding_hash:
        raise AnalysisError("input_changed")
    return current


def _traversal(bound: BoundAnalysis, bundle: Bundle) -> tuple[bool, int, int, int]:
    source = bound.inputs.sources.stored_run
    doc_id = bundle.document.doc_id
    plans = plan_windows(bundle, source.record.configuration.policy.window_budget)
    windows = tuple(w for w in source.windows if w.doc_id == doc_id)
    visits = tuple(v for v in source.visits if v.doc_id == doc_id)
    expected_units = tuple(unit for w in plans for unit in w.unit_ids)
    planned = tuple(
        (w.window_id, w.start, w.end, w.unit_ids, w.context_id) for w in plans
    )
    actual = tuple(
        (w.window_id, w.start, w.end, w.unit_ids, w.context_id) for w in windows
    )
    identity_complete = planned == actual and Counter(
        v.element_id for v in visits
    ) == Counter(expected_units)
    # The extraction gate checks stored accounting; this independently checks the plan.
    outcomes_complete = all(
        w.outcome == WindowOutcome.COMPLETED and not w.exhausted for w in windows
    ) and all(v.outcome == WindowOutcome.COMPLETED for v in visits)
    rejected_candidates = any(r.doc_id == doc_id for r in source.rejections)
    complete = (
        bool(expected_units)
        and identity_complete
        and outcomes_complete
        and not rejected_candidates
    )
    return (
        complete,
        len(expected_units),
        sum(w.outcome == WindowOutcome.COMPLETED for w in windows),
        sum(w.outcome == WindowOutcome.FAILED for w in windows),
    )


def _layers(bound: BoundAnalysis, doc_id: str):
    inputs = bound.inputs
    claims = tuple(c for c in inputs.sources.stored_run.claims if c.doc_id == doc_id)
    order = tuple((c.doc_id, c.claim_id) for c in claims)
    requested = tuple(
        key for key in inputs.coding.record.requested_claim_order if key[0] == doc_id
    )
    classifications = tuple(
        c for c in inputs.coding.classifications if c.doc_id == doc_id
    )
    classification_complete = (
        requested == order
        and Counter((c.doc_id, c.claim_id) for c in classifications) == Counter(order)
        and all(c.status == "completed" for c in classifications)
    )
    proposed = {
        (c.claim_id, theme)
        for c in classifications
        if c.status == "completed"
        for theme in c.theme_ids
    }
    proposals = tuple(p for p in inputs.coding.proposals if p.target.doc_id == doc_id)
    targets = tuple(t for t in inputs.support.targets if t.target.doc_id == doc_id)
    target_pairs = {(t.target.claim_id, t.target.theme_id) for t in targets}
    assessment_complete = proposed == {
        (p.target.claim_id, p.target.theme_id) for p in proposals
    } == target_pairs and len(targets) == len(proposed)
    outcomes = tuple(
        o
        for o in inputs.support.outcomes
        if o.target_id in {t.target_id for t in targets}
    )
    assessment_complete = (
        assessment_complete
        and len(outcomes) == len(targets)
        and all(o.status == "assessed" for o in outcomes)
    )
    # Four trial slots, per-quote and joint signals/answers are reverified by the
    # shipped support gate even on a rejected/empty assignment inventory.
    for target in targets:
        trials = tuple(
            t for t in inputs.support.trials if t.target_id == target.target_id
        )
        expected_slots = {
            (identity.family, presentation)
            for identity in inputs.support.record.judge_identities
            for presentation in ("evidence_first", "claim_theme_first")
        }
        slots = {(t.identity.family, t.presentation.value) for t in trials}
        signals = tuple(
            s for s in inputs.support.entailment if s.target_id == target.target_id
        )
        quotes = {
            e.quote_id
            for e in inputs.support.evidence
            if e.target_id == target.target_id
        }
        assessment_complete = (
            assessment_complete
            and len(trials) == REQUIRED_TRIALS
            and slots == expected_slots
            and all(
                t.answer is not None
                and {q.quote_id for q in t.answer.quote_assessments} == quotes
                for t in trials
            )
            and {(s.scope, s.quote_id) for s in signals}
            == {("joint", None)} | {("quote", q) for q in quotes}
            and all(s.status == "available" for s in signals)
        )
    decisions = tuple(d for d in bound.decisions.decisions if d.doc_id == doc_id)
    decision_complete = (
        {(d.claim_id, d.theme_id) for d in decisions} == proposed
        and len(decisions) == len(proposed)
        and all(d.status in ("accepted", "rejected") for d in decisions)
    )
    return (
        classification_complete,
        assessment_complete,
        decision_complete,
        classifications,
        outcomes,
        decisions,
    )


def _document_completion(
    bound: BoundAnalysis,
    bundle: Bundle,
    quotes: dict[tuple[str, str], QuoteAudit],
    conflicts: set[str],
) -> DocumentCompletion:
    inputs = bound.inputs
    doc_id = bundle.document.doc_id
    meta = next(m for m in bound.metadata if m.doc_id == doc_id)
    doc = next(d for d in inputs.sources.stored_run.documents if d.doc_id == doc_id)
    traversal, eligible, completed, failed = _traversal(bound, bundle)
    classification, assessment, decision, classifications, outcomes, decisions = (
        _layers(bound, doc_id)
    )
    assignments = tuple(a for a in inputs.coding.assignments if a.doc_id == doc_id)
    counts = Counter(d.status for d in decisions)
    support_counts = Counter(o.status for o in outcomes)
    unmatched = sum(
        c.status == "completed" and not c.theme_ids for c in classifications
    )
    masked = sum(bool(quotes[(a.doc_id, a.quote_id)].mask_ids) for a in assignments)
    reasons = []
    state = "partial"
    if doc.outcome == DocumentOutcome.FAILED:
        state = "failed"
        reasons.append("processing_failed")
    if not eligible:
        reasons.append("no_eligible_units")
    if not traversal and eligible:
        reasons.append("extraction_partial")
    reasons.extend(
        dict.fromkeys(
            w.reason.value
            for w in inputs.sources.stored_run.windows
            if w.doc_id == doc_id and w.reason is not None
        )
    )
    reasons.extend(
        dict.fromkeys(
            r.reason
            for r in inputs.sources.stored_run.rejections
            if r.doc_id == doc_id and r.reason not in reasons
        )
    )
    if not classification:
        reasons.append("classification_incomplete")
    for status in ("refused", "incomplete", "flagged"):
        if support_counts[status]:
            reasons.append("assessment_" + status)
    if not assessment and not any(
        support_counts[s] for s in ("refused", "incomplete", "flagged")
    ):
        reasons.append("assessment_incomplete")
    if inputs.assignment_policy is None:
        reasons.append("calibration_required")
    elif counts["review"]:
        reasons.append("policy_review")
    if counts["refused"] and not support_counts["refused"]:
        reasons.append("assessment_refused")
    if not decision and not counts["review"] and not counts["refused"]:
        reasons.append("policy_review")
    if doc_id in conflicts:
        reasons.append("copy_processing_conflict")
    prerequisites = (
        all((traversal, classification, assessment, decision))
        and inputs.assignment_policy is not None
        and not reasons
    )
    declaration = next((d for d in inputs.no_theme if d.doc_id == doc_id), None)
    if declaration is not None and (not prerequisites or assignments):
        raise AnalysisError("input_changed")
    observable = False
    if declaration is not None:
        state, observable = "completed-no-theme", True
        reasons.append("explicit_no_theme")
    elif unmatched:
        reasons.append("valid_unmatched")
    elif prerequisites and assignments:
        state, observable = "completed", True
    elif not assignments:
        reasons.append("no_theme_unconfirmed")
    return DocumentCompletion(
        doc_id=doc_id,
        event_id=meta.event_id,
        canonical_hash=meta.canonical_hash,
        source_run_hash=inputs.coding.record.source_run_hash,
        coding_run_hash=_run_hash(inputs.coding),
        support_run_hash=bound.decisions.support_run_hash,
        codebook=inputs.coding.record.codebook,
        assignment_policy=inputs.coding.record.policy,
        analysis_policy_hash=inputs.analysis_policy.content_hash,
        traversal_complete=traversal,
        classification_complete=classification,
        assessment_complete=assessment,
        decision_complete=decision,
        eligible_units=eligible,
        completed_windows=completed,
        failed_windows=failed,
        accepted_count=len(assignments),
        masked_count=masked,
        rejected_count=counts["rejected"],
        review_count=counts["review"],
        refused_count=counts["refused"]
        + sum(c.status == "refused" for c in classifications),
        flagged_count=support_counts["flagged"],
        incomplete_count=support_counts["incomplete"]
        + sum(c.status == "incomplete" for c in classifications),
        unmatched_count=unmatched,
        processing_state=state,
        reasons=tuple(dict.fromkeys(reasons)),
        declaration_hash=digest(declaration.model_dump(mode="json"))
        if declaration
        else None,
        observable=observable,
        policy_scope=inputs.analysis_policy.scope,
    )


def document_completions(bound: BoundAnalysis) -> tuple[DocumentCompletion, ...]:
    """Prove each selected document's work inventory; never infer an empty negative."""
    try:
        current = checked_bound(bound)
        quotes = {(q.doc_id, q.quote_id): q for q in _quote_rows(current)}
        conflicts = {
            c.doc_id
            for c in _copy_rows(current)
            if c.status == "copy_processing_conflict"
        }
        return tuple(
            _document_completion(current, b, quotes, conflicts)
            for b in sorted(
                current.inputs.sources.bundles, key=lambda b: b.document.doc_id
            )
        )
    except AnalysisError:
        raise
    except Exception:  # noqa: BLE001 - no source-bearing diagnostics escape
        raise AnalysisError("input_changed") from None
