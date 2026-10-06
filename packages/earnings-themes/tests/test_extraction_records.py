"""Stage 7's records (the Stage 7 spec, §Records; ES6, ES21, ES22): their
invariants, and a refusal printed as its reason and IDs, never its text (GS13)."""

from datetime import UTC, datetime

import pytest
from earnings_core import Rejection, RejectionReason, VerifiedSpan
from earnings_themes.extraction.records import (
    AdapterIdentity,
    Ceilings,
    ExtractionPolicy,
    ExtractionProblem,
    ExtractionRejection,
    Quote,
    RunConfiguration,
    RunRecord,
    Visit,
    WindowOutcome,
)
from pydantic import ValidationError

SENTINEL = "Sentinel words a refusal must never print."
HASH = "a" * 64


def span(start: int = 0, end: int = 5) -> VerifiedSpan:
    return VerifiedSpan(
        doc_id="doc@walker-1#0123456789abcdef",
        canonical_hash=HASH,
        start=start,
        end=end,
        quote_text="x" * (end - start),
        element_id=f"sentence-{start}-{end}",
        validator_version="3",
    )


@pytest.mark.parametrize(
    ("reason", "expected"),
    [
        (
            {
                "rejection": Rejection(
                    reason=RejectionReason.QUOTE_TEXT_MISMATCH, detail=SENTINEL
                )
            },
            "doc w-0-90 attempt 2 candidate 1 sentence-0-5: quote_text_mismatch",
        ),
        (
            {"problem": ExtractionProblem.UNKNOWN_LABEL, "detail": SENTINEL},
            "doc w-0-90 attempt 2 candidate 1 sentence-0-5: unknown_label",
        ),
    ],
    ids=["core", "problem"],
)
def test_a_refusal_prints_its_ids_and_reason_never_its_text(reason, expected) -> None:
    """Plan 11's GS13 item: a refusal over pilot text prints only its reason and IDs.
    Its detail and the reply's labels may quote the document, so neither prints."""
    refused = ExtractionRejection(
        doc_id="doc",
        window_id="w-0-90",
        attempt=2,
        candidate_index=1,
        labels=(SENTINEL,),
        element_ids=("sentence-0-5",),
        **reason,
    )
    assert (str(refused), f"{refused}") == (expected, expected)
    assert SENTINEL not in str(refused)
    shown = repr(refused)
    listed = str([refused])
    assert SENTINEL not in shown
    assert SENTINEL not in listed
    assert refused.reason in shown


def test_a_document_refusal_prints_the_document_and_reason() -> None:
    refused = ExtractionRejection(
        doc_id="doc",
        rejection=Rejection(reason=RejectionReason.WRONG_DOCUMENT, detail=SENTINEL),
    )
    assert str(refused) == "doc: wrong_document"
    shown = repr(refused)
    listed = str([refused])
    assert SENTINEL not in shown
    assert SENTINEL not in listed
    assert refused.reason in shown


@pytest.mark.parametrize(
    "reasons",
    [
        {},
        {
            "rejection": Rejection(reason=RejectionReason.UNKNOWN_ELEMENT, detail=""),
            "problem": ExtractionProblem.UNKNOWN_LABEL,
        },
    ],
    ids=["neither", "both"],
)
def test_a_refusal_holds_exactly_one_reason(reasons) -> None:
    with pytest.raises(ValidationError):
        ExtractionRejection(doc_id="doc", **reasons)


def test_a_quote_s_id_is_its_span() -> None:
    assert Quote(quote_id="q-0-5", span=span()).quote_id == "q-0-5"
    with pytest.raises(ValidationError):
        Quote(quote_id="q-0-6", span=span())


@pytest.mark.parametrize(
    ("outcome", "reason"),
    [
        (WindowOutcome.FAILED, None),
        (WindowOutcome.COMPLETED, ExtractionProblem.TRANSPORT_ERROR),
    ],
)
def test_a_visit_has_a_reason_exactly_when_it_failed(outcome, reason) -> None:
    with pytest.raises(ValidationError):
        Visit(
            doc_id="doc",
            element_id="sentence-0-5",
            window_id="w-0-5",
            outcome=outcome,
            reason=reason,
        )


def test_ceilings_have_no_default() -> None:
    """ES21: every run passes its ceilings explicitly."""
    with pytest.raises(ValidationError):
        Ceilings()


def run_record(**changes) -> RunRecord:
    configuration = RunConfiguration(
        identity=AdapterIdentity(adapter_kind="scripted", model_id="scripted"),
        policy=ExtractionPolicy(),
        ceilings=Ceilings(
            requests_per_document=4, requests_per_run=8, tokens_per_run=1000
        ),
        prompt_sha256=HASH,
        reply_schema_sha256=HASH,
        extractor_version="pointer-traversal/1",
        validator_version="3",
    )
    fields = {
        "run_id": "run-1",
        "started_at": datetime(2026, 10, 4, tzinfo=UTC),
        "configuration": configuration,
        "configuration_hash": HASH,
        "documents": {"doc": HASH},
        "units": 3,
        "windows": 1,
        "candidates": 0,
        "quotes": 0,
        "claims": 0,
        "rejections_by_reason": {},
        "requests": 1,
        "cache_hits": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "unreported": 1,
        "exhausted": False,
        "software": {"earnings-themes": "0.1.0"},
        "exactness_rate": None,
    }
    return RunRecord(**{**fields, **changes})


def test_no_quote_retained_means_no_exactness_rate() -> None:
    """R6.2, R12.8: zero retained quotes has no defined exactness rate."""
    assert run_record().exactness_rate is None
    assert run_record(quotes=2, exactness_rate=1.0).exactness_rate == 1.0
    assert run_record().billable_cost == "none, self-hosted"
    for changes in (
        {"exactness_rate": 1.0},
        {"quotes": 2},
        {"rejections_by_reason": {"not_a_reason": 1}},
    ):
        with pytest.raises(ValidationError):
            run_record(**changes)


def test_a_run_starts_at_an_aware_time() -> None:
    naive = datetime(2026, 10, 4, tzinfo=UTC).replace(tzinfo=None)
    with pytest.raises(ValidationError):
        run_record(started_at=naive)


def window_fields():
    return {
        "doc_id": "invented-doc",
        "window_id": "w-0-10",
        "start": 0,
        "end": 10,
        "unit_ids": ("paragraph-0-10",),
        "attempts": 1,
        "outcome": WindowOutcome.COMPLETED,
        "reason": None,
        "requests": 1,
        "cache_hits": 0,
        "prompt_tokens": 3,
        "completion_tokens": 2,
        "unreported": 0,
        "latency_ms": 0,
        "exhausted": False,
    }


@pytest.mark.parametrize(
    "change",
    [
        {"end": 0},
        {"start": 11},
        {"window_id": "w-1-10"},
        {"requests": 2},
        {"cache_hits": 1},
        {"unreported": 2},
        {"attempts": 3},
        {"reason": ExtractionProblem.TRANSPORT_ERROR},
        {"outcome": WindowOutcome.FAILED},
        {"reason": "unknown"},
        {"unit_ids": ("paragraph-0-10", "paragraph-0-10")},
        {"unit_ids": ()},
        {"attempts": True},
        {"requests": 1.0},
        {"prompt_tokens": "3"},
    ],
    ids=[
        "empty",
        "reversed",
        "wrong-id",
        "requests",
        "hits",
        "unreported",
        "third-attempt",
        "completed-reason",
        "failed-no-reason",
        "unknown-reason",
        "duplicate-unit",
        "empty-units",
        "bool",
        "float",
        "string",
    ],
)
def test_window_refuses_impossible_record(change):
    from earnings_themes.extraction.records import WindowRecord

    with pytest.raises(ValidationError):
        WindowRecord.model_validate(window_fields() | change)


@pytest.mark.parametrize(
    "changes",
    [
        {"claim_id": "malformed"},
        {"claim_id": "c-1-10-1-0"},
        {"claim_id": "c-0-10-2-0"},
        {"claim_id": "c-0-10-1--1"},
        {"attempt": 3, "claim_id": "c-0-10-3-0"},
        {"quote_ids": ("q-0-5", "q-0-5")},
        {"quote_ids": ()},
        {"attempt": True},
        {"window_id": "w-0-0", "claim_id": "c-0-0-1-0"},
    ],
    ids=[
        "malformed",
        "window",
        "attempt",
        "index",
        "third-attempt",
        "duplicate-links",
        "empty-links",
        "bool",
        "empty-window",
    ],
)
def test_claim_refuses_invalid_identity_and_links(changes):
    from earnings_themes.extraction.records import Claim

    fields = {
        "claim_id": "c-0-10-1-0",
        "doc_id": "doc",
        "window_id": "w-0-10",
        "attempt": 1,
        "claim": "Invented claim.",
        "quote_ids": ("q-0-5",),
    }
    with pytest.raises(ValidationError):
        Claim.model_validate(fields | changes)


def test_document_failed_windows_are_bounded():
    from earnings_themes.extraction.records import DocumentOutcome, DocumentRecord

    with pytest.raises(ValidationError):
        DocumentRecord(
            doc_id="doc",
            canonical_hash=HASH,
            outcome=DocumentOutcome.FAILED,
            units=1,
            windows=1,
            windows_failed=2,
            candidates=0,
            quotes=0,
            claims=0,
            rejections=0,
        )


def test_replay_misses_and_budget_stopped_unsent_windows_remain_valid():
    from earnings_themes.extraction.records import WindowRecord

    base = window_fields() | {"requests": 0, "outcome": WindowOutcome.FAILED}
    assert (
        WindowRecord.model_validate(
            base | {"attempts": 2, "reason": ExtractionProblem.REPLAY_MISS}
        ).attempts
        == 2
    )
    assert (
        WindowRecord.model_validate(
            base
            | {
                "attempts": 0,
                "reason": ExtractionProblem.BUDGET_EXHAUSTED,
                "exhausted": True,
            }
        ).attempts
        == 0
    )


def test_run_refuses_unreported_over_requests():
    with pytest.raises(ValidationError):
        run_record(unreported=2)
