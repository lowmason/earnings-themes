"""Expected release slots and explicit transcript-not-in-scope coverage."""

import polars as pl
from earnings_core import digest

from .completion import checked_bound, document_completions
from .problems import AnalysisError
from .records import (
    TABLE_SCHEMAS,
    BoundAnalysis,
    CopyRow,
    CoverageRow,
    DocumentCompletion,
    ExpectedEvent,
)
from .rows import _copy_rows

COUNT_FIELDS = (
    "accepted_count",
    "masked_count",
    "review_count",
    "rejected_count",
    "refused_count",
    "flagged_count",
    "incomplete_count",
    "unmatched_count",
)
STATE_ORDER = ("failed", "partial", "completed", "completed-no-theme")


def _release(
    bound: BoundAnalysis,
    event: ExpectedEvent,
    completions: tuple[DocumentCompletion, ...],
    copies: tuple[CopyRow, ...],
) -> CoverageRow:
    acquisition = sorted(
        (a for a in bound.acquisition if a.event_id == event.event_id),
        key=lambda a: a.document_id,
    )
    metadata = tuple(m for m in bound.metadata if m.event_id == event.event_id)
    doc_ids = tuple(sorted(m.doc_id for m in metadata))
    selected = tuple(c for c in completions if c.doc_id in doc_ids)
    copy_rows = tuple(c for c in copies if c.doc_id in doc_ids)
    # Count one processing result per disclosure group; audit retains every copy.
    representatives = {c.representative_doc_id for c in copy_rows}
    distinct = tuple(c for c in selected if c.doc_id in representatives)
    by_doc = {c.doc_id: c for c in selected}
    completion_states = {}
    for copy in copy_rows:
        completion = by_doc[copy.doc_id]
        completion_states.setdefault(copy.disclosure_group, set()).add(
            (completion.processing_state, completion.observable, completion.reasons)
        )
    conflicts = any(c.status == "copy_processing_conflict" for c in copy_rows) or any(
        len(states) > 1 for states in completion_states.values()
    )
    reasons = tuple(dict.fromkeys(reason for c in distinct for reason in c.reasons))
    state = next(
        (s for s in STATE_ORDER if any(c.processing_state == s for c in selected)), None
    )
    for a in acquisition:
        if a.state == "failed":
            state = "failed"
        reasons += tuple(
            r for r in (a.missing_reason, a.failure_reason) if r and r not in reasons
        )
    if state is None:
        state = acquisition[0].state if acquisition else "expected"
    if not distinct and state in (
        "expected",
        "acquired",
        "parsed",
        "partial",
        "completed",
        "completed-no-theme",
    ):
        reasons += ("not_processed",)
    if conflicts and "copy_processing_conflict" not in reasons:
        reasons += ("copy_processing_conflict",)
    if event.eligibility_status != "eligible":
        reasons += (event.eligibility_reason,)
    available = bool(metadata) or any(a.state == "acquired" for a in acquisition)
    parsed = bool(metadata) and all(a.doc_id is not None for a in acquisition)
    observable = (
        parsed
        and bool(distinct)
        and all(c.observable for c in selected)
        and not conflicts
        and state in ("completed", "completed-no-theme")
        and event.eligibility_status == "eligible"
    )
    # Publication restrictions are acquisition outcomes, not evidence of absence.
    if any(a.state in ("restricted", "unavailable") for a in acquisition):
        observable = False
    availability = (
        "available"
        if available
        else "restricted"
        if any(a.state == "restricted" for a in acquisition)
        else "unavailable"
        if acquisition and state != "expected"
        else "not_yet_checked"
    )
    return CoverageRow(
        event_id=event.event_id,
        entity_id=event.entity_id,
        cik=event.cik,
        period_end=event.period_end,
        fiscal_year=event.fiscal_year,
        fiscal_quarter=event.fiscal_quarter,
        doc_type="release",
        speaker_role="not_applicable",
        eligibility_status=event.eligibility_status,
        eligibility_reason=event.eligibility_reason,
        membership_assertion_id=event.membership_assertion_id,
        expected=True,
        available=available,
        parsed=parsed,
        observable=observable,
        availability=availability,
        document_id=acquisition[0].document_id if acquisition else None,
        doc_ids=doc_ids,
        latest_state=state,
        state_run_id=acquisition[0].state_run_id if acquisition else None,
        state_schema_version=acquisition[0].state_schema_version
        if acquisition
        else None,
        missing_reasons=tuple(dict.fromkeys(reasons)),
        policy_scope=bound.inputs.analysis_policy.scope,
        **{name: sum(getattr(c, name) for c in distinct) for name in COUNT_FIELDS},
        copy_refs=tuple(sorted(digest(c.model_dump(mode="json")) for c in copy_rows)),
        metadata_refs=tuple(
            sorted(digest(m.model_dump(mode="json")) for m in metadata)
        ),
        completion_refs=tuple(
            sorted(digest(c.model_dump(mode="json")) for c in selected)
        ),
    )


def build_coverage(
    bound: BoundAnalysis, completions: tuple[DocumentCompletion, ...]
) -> pl.DataFrame:
    """Retain every expected event, with current independently rederived completions."""
    try:
        current = checked_bound(bound)
        actual = document_completions(current)
        if type(completions) is not tuple or completions != actual:
            raise AnalysisError("input_changed")
        copies = _copy_rows(current)
        rows = []
        for event in current.expected:
            release = _release(current, event, actual, copies)
            rows.append(release)
            fields = release.model_dump()
            fields.update(
                doc_type="transcript",
                speaker_role="unknown",
                available=False,
                parsed=False,
                observable=False,
                availability="not_yet_checked",
                document_id=None,
                doc_ids=(),
                latest_state="expected",
                state_run_id=None,
                state_schema_version=None,
                missing_reasons=("transcript_not_in_scope",),
                copy_refs=(),
                metadata_refs=(),
                completion_refs=(),
                **dict.fromkeys(COUNT_FIELDS, 0),
            )
            rows.append(CoverageRow.model_validate(fields))
        return pl.DataFrame(
            [r.model_dump(mode="python") for r in rows],
            schema=TABLE_SCHEMAS["coverage"],
        )
    except AnalysisError:
        raise
    except Exception:  # noqa: BLE001 - never echo arbitrary caller values
        raise AnalysisError("input_changed") from None
