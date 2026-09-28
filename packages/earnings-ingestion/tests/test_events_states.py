"""The processing states (the Stage 5 spec, §Processing states; R1.4): the records,
the transitions R1.4 allows, and each document's current state under a pilot."""

from datetime import UTC, datetime, timedelta

import pytest
from earnings_ingestion.canonical.records import FailureReason
from earnings_ingestion.events.states import (
    AttemptOutcome,
    DocumentState,
    ExhibitAttempt,
    ExhibitChoice,
    MissingReason,
    StateTransition,
    check_histories,
    current_states,
)
from pydantic import ValidationError

PILOT = "a" * 64
OTHER_PILOT = "b" * 64
SHA = "c" * 64
AT = datetime(2026, 9, 29, 14, 0, tzinfo=UTC)
FROZEN = "0009990001-25-000012"
EXHIBIT = ExhibitAttempt(
    accession=FROZEN,
    filename="acme-20250925-ex992.htm",
    exhibit_type="EX-99.2",
    choice=ExhibitChoice.NAMED,
    outcome=AttemptOutcome.CONFIRMED,
    artifact_sha256=SHA,
)
DOC_ID = f"{FROZEN}_acme-20250925-ex992.htm@walker-1#0123456789abcdef"


def step(
    state: DocumentState,
    before: DocumentState | None,
    *,
    event: str = "cik-0009990001:2025-08-31",
    run: str = "run-1",
    sequence: int = 0,
    pilot: str = PILOT,
    **fields,
) -> StateTransition:
    details = {
        DocumentState.EXPECTED: {"missing_reason": MissingReason.NOT_YET_CHECKED},
        DocumentState.ACQUIRED: {
            "accession": FROZEN,
            "exhibit": EXHIBIT.filename,
            "artifact_sha256": SHA,
            "retrieved_at": AT,
        },
        DocumentState.PARSED: {
            "accession": FROZEN,
            "exhibit": EXHIBIT.filename,
            "artifact_sha256": SHA,
            "retrieved_at": AT,
            "doc_id": DOC_ID,
            "attempts": (EXHIBIT,),
        },
        DocumentState.FAILED: {
            "missing_reason": MissingReason.PARSE_FAILED,
            "failure_reason": FailureReason.NO_NATIVE_TEXT,
        },
        DocumentState.UNAVAILABLE: {"missing_reason": MissingReason.NOT_FOUND},
        DocumentState.RESTRICTED: {"missing_reason": MissingReason.RIGHTS_RESTRICTED},
    }.get(state, {})
    values = {
        "document_id": f"{event}:release",
        "event_id": event,
        "run_id": run,
        "sequence": sequence,
        "recorded_at": AT + timedelta(minutes=sequence),
        "from_state": before,
        "to_state": state,
        "pilot_id": "djia-synthetic-pilot",
        "pilot_version": 1,
        "pilot_hash": pilot,
        "frozen_accession": FROZEN,
        **details,
    }
    return StateTransition(**{**values, **fields})


E, A, P, F, U, R = (
    DocumentState.EXPECTED,
    DocumentState.ACQUIRED,
    DocumentState.PARSED,
    DocumentState.FAILED,
    DocumentState.UNAVAILABLE,
    DocumentState.RESTRICTED,
)


def test_every_state_is_represented_from_fixtures() -> None:
    """R1.4's nine states, each reached by a transition it allows, and every
    document that is expected but absent carries its missing_reason."""
    later = (
        DocumentState.PARTIAL,
        DocumentState.COMPLETED,
        DocumentState.COMPLETED_NO_THEME,
    )
    histories = [
        [step(E, None)],
        [step(E, None), step(U, E, sequence=1)],
        [step(E, None), step(R, E, sequence=1)],
        [step(E, None), step(A, E, sequence=1)],
        [step(E, None), step(A, E, sequence=1), step(F, A, sequence=2)],
        [
            step(E, None),
            step(A, E, sequence=1),
            step(U, A, sequence=2, missing_reason=MissingReason.NO_CONFIRMED_RELEASE),
        ],
        [step(E, None), step(A, E, sequence=1), step(P, A, sequence=2)],
        *(
            [
                step(E, None),
                step(A, E, sequence=1),
                step(P, A, sequence=2),
                step(state, P, run="run-2", recorded_at=AT + timedelta(hours=1)),
            ]
            for state in later
        ),
    ]
    transitions = [
        transition.model_copy(
            update={
                "event_id": event,
                "document_id": f"{event}:release",
                "run_id": f"{transition.run_id}-{number}",
            }
        )
        for number, history in enumerate(histories)
        for event in [f"cik-0009990001:2025-{number + 1:02d}-01"]
        for transition in history
    ]
    check_histories(transitions)
    current = current_states(transitions, PILOT)
    assert {t.to_state for t in current.values()} == set(DocumentState)
    for transition in current.values():
        absent = transition.to_state in {E, F, U, R}
        assert (transition.missing_reason is not None) is absent


@pytest.mark.parametrize(
    ("state", "fields", "message"),
    [
        (E, {"missing_reason": None}, "expected carries a missing_reason"),
        (U, {"missing_reason": MissingReason.PARSE_FAILED}, "unavailable carries"),
        (
            A,
            {"missing_reason": MissingReason.NOT_FOUND},
            "acquired carries no missing_reason",
        ),
        (F, {"failure_reason": None}, "failed names its FailureReason"),
        (U, {"failure_reason": FailureReason.PARSE_FAILED}, "only failed names"),
        (A, {"artifact_sha256": None}, "acquired names its accession"),
        (P, {"doc_id": None}, "parsed names its accession"),
    ],
)
def test_a_state_carries_its_own_details(state, fields, message) -> None:
    before = {E: None, U: E, A: E, F: A, P: A}[state]
    with pytest.raises(ValidationError, match=message):
        step(state, before, **fields)


def test_only_the_transitions_r1_4_allows() -> None:
    with pytest.raises(ValidationError, match="expected cannot become parsed"):
        step(P, E)
    with pytest.raises(ValidationError, match="the start cannot become acquired"):
        step(A, None)
    with pytest.raises(ValidationError, match="completed cannot become"):
        step(DocumentState.PARTIAL, DocumentState.COMPLETED)
    with pytest.raises(ValidationError, match="only under an acquisition override"):
        step(A, U)
    assert step(A, U, override_id="release-doc-acme").from_state is U
    assert step(A, F, override_id="release-doc-acme").from_state is F


def test_a_history_must_chain() -> None:
    with pytest.raises(ValueError, match="starts at expected, not from acquired"):
        check_histories([step(P, A)])
    with pytest.raises(ValueError, match="comes from acquired, but its state was"):
        check_histories([step(E, None), step(P, A, sequence=1)])
    with pytest.raises(ValueError, match="run-1 #0 is recorded twice"):
        check_histories([step(E, None), step(E, None)])


def test_the_current_state_is_the_latest_under_the_current_pilot() -> None:
    """A revert to an earlier pilot never inherits a later pilot's history (plan 8,
    P8-4): each pilot's transitions chain on their own."""
    mine = [step(E, None), step(A, E, sequence=1), step(P, A, sequence=2)]
    other = [
        step(E, None, run="run-2", pilot=OTHER_PILOT),
        step(U, E, run="run-2", sequence=1, pilot=OTHER_PILOT),
    ]
    check_histories([*mine, *other])
    (current,) = current_states([*other, *mine], PILOT).values()
    assert current.to_state is P
    (theirs,) = current_states([*mine, *other], OTHER_PILOT).values()
    assert theirs.to_state is U
    assert current_states(mine, OTHER_PILOT) == {}


def test_later_runs_follow_earlier_ones_by_time_then_run_then_sequence() -> None:
    first = [step(E, None), step(A, E, sequence=1)]
    rerun = [
        step(P, A, run="run-2", sequence=0).model_copy(
            update={"recorded_at": AT + timedelta(minutes=1)}
        )
    ]
    check_histories([*rerun, *first])
    (current,) = current_states([*rerun, *first], PILOT).values()
    assert (current.run_id, current.to_state) == ("run-2", P)


def test_a_document_is_its_event_s_release() -> None:
    """P8-6: each pilot event expects one document, ``<event_id>:release``."""
    with pytest.raises(ValidationError, match="expects cik-0009990001:2025-08-31"):
        step(E, None, document_id="cik-0009990002:2025-08-31:release")


def test_a_clock_that_steps_back_during_a_run_cannot_reorder_it() -> None:
    """Each run's transitions follow its sequence, whatever the clock read, and a
    later run still follows by its earliest time (plan 8's final review)."""
    back = AT - timedelta(minutes=5)
    first = [
        step(E, None),
        step(A, E, sequence=1).model_copy(update={"recorded_at": back}),
        step(P, A, sequence=2).model_copy(update={"recorded_at": back}),
    ]
    other = step(E, None, event="cik-0009990001:2025-11-30", run="run-2")
    check_histories([*first, other])
    current = current_states([other, *first], PILOT)
    assert current["cik-0009990001:2025-08-31:release"].to_state is P
