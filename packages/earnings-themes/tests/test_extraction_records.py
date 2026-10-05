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
