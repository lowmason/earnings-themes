"""The processing states of Stage 5's expected documents (the Stage 5 spec,
§Processing states; R1.4; plan 8, P8-6 and P8-7).

- **Documents.** Each pilot event expects one document, its release:
  ``<event_id>:release``.
- **Transitions.** Every change of state is a ``StateTransition``, kept with its run,
  time, reason, and details. ``NEXT`` holds the transitions R1.4 allows, and an
  ``unavailable`` or ``failed`` document goes back to ``acquired`` only under an
  acquisition override (``set_release_document``). ``parsed`` goes on to
  ``partial``, ``completed``, or ``completed-no-theme`` only when a later stage sets
  it; fixtures represent those now. ``restricted`` comes from fixtures only: no
  source this stage reads forbids local processing, since SEC documents are public.
- **Missing reasons.** A state in which the document is not at hand carries a
  ``missing_reason``: ``expected``, ``unavailable``, ``restricted``, and ``failed``.
  Every other state carries none, so a document that is expected but absent always
  says why (R1.4; A §376).
- **Order.** Runs are ordered by their earliest ``recorded_at``, then ``run_id``,
  and each run's transitions by ``sequence``, the position in its run, so a clock
  that steps back during a run cannot reorder it (plan 8's final review). A
  document's transitions must chain: the first starts at ``expected``, and each
  comes from the state the one before it reached.
- **The current state.** A document's current state is its latest transition among
  those recorded under the current pilot's content hash, and each pilot's
  transitions chain on their own. So a revert to an earlier pilot never inherits a
  later pilot's history (plan 8, P8-4).

These join ingestion schema version 1 (P6-5), and ``docs/data-dictionary.md``
documents every field and value.
"""

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Self

from earnings_core.artifacts import NonBlankStr
from earnings_core.documents import IdPart
from earnings_core.hashing import Sha256Hex
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    NonNegativeInt,
    PositiveInt,
    model_validator,
)

from earnings_ingestion.canonical.records import FailureReason, IngestionRecord
from earnings_ingestion.events.records import Accession


class DocumentState(StrEnum):
    """R1.4's processing states."""

    EXPECTED = "expected"
    ACQUIRED = "acquired"
    PARSED = "parsed"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"
    RESTRICTED = "restricted"
    PARTIAL = "partial"
    COMPLETED = "completed"
    COMPLETED_NO_THEME = "completed-no-theme"


class MissingReason(StrEnum):
    """Why a document is not at hand, in AGENTS.md's words where it has them."""

    NOT_YET_CHECKED = "not_yet_checked"
    NOT_FOUND = "not_found"
    NO_CONFIRMED_RELEASE = "no_confirmed_release"
    RIGHTS_RESTRICTED = "rights_restricted"
    PARSE_FAILED = "parse_failed"


REASONS = {
    DocumentState.EXPECTED: frozenset({MissingReason.NOT_YET_CHECKED}),
    DocumentState.UNAVAILABLE: frozenset(
        {MissingReason.NOT_FOUND, MissingReason.NO_CONFIRMED_RELEASE}
    ),
    DocumentState.RESTRICTED: frozenset({MissingReason.RIGHTS_RESTRICTED}),
    DocumentState.FAILED: frozenset({MissingReason.PARSE_FAILED}),
}
"""The missing reasons each state may carry; a state not listed carries none."""

NEXT: dict[DocumentState | None, frozenset[DocumentState]] = {
    None: frozenset({DocumentState.EXPECTED}),
    DocumentState.EXPECTED: frozenset(
        {DocumentState.ACQUIRED, DocumentState.UNAVAILABLE, DocumentState.RESTRICTED}
    ),
    DocumentState.ACQUIRED: frozenset(
        {DocumentState.PARSED, DocumentState.FAILED, DocumentState.UNAVAILABLE}
    ),
    DocumentState.PARSED: frozenset(
        {
            DocumentState.PARTIAL,
            DocumentState.COMPLETED,
            DocumentState.COMPLETED_NO_THEME,
        }
    ),
    DocumentState.FAILED: frozenset({DocumentState.ACQUIRED}),
    DocumentState.UNAVAILABLE: frozenset({DocumentState.ACQUIRED}),
    DocumentState.RESTRICTED: frozenset(),
    DocumentState.PARTIAL: frozenset(),
    DocumentState.COMPLETED: frozenset(),
    DocumentState.COMPLETED_NO_THEME: frozenset(),
}
"""The transitions R1.4 allows, from each state; ``None`` is the start."""

REOPENED = frozenset({DocumentState.FAILED, DocumentState.UNAVAILABLE})
"""States that go back to ``acquired`` only under an acquisition override."""


class ExhibitChoice(StrEnum):
    """Why an exhibit was tried, in the order R1.2 tries them."""

    NAMED = "named"
    DESCRIBED = "described"
    LOWEST_SEQUENCE = "lowest_sequence"
    OVERRIDE = "override"


class AttemptOutcome(StrEnum):
    """What one exhibit's attempt came to."""

    CONFIRMED = "confirmed"
    NOT_CONFIRMED = "not_confirmed"
    CANONICALIZATION_FAILED = "canonicalization_failed"
    NOT_FETCHED = "not_fetched"


class ExhibitAttempt(BaseModel):
    """One exhibit tried for a document: immutable, closed, strictly typed."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    accession: Accession
    filename: NonBlankStr
    exhibit_type: NonBlankStr
    choice: ExhibitChoice
    outcome: AttemptOutcome
    artifact_sha256: Sha256Hex | None = None
    failure_reason: FailureReason | None = None
    detail: NonBlankStr | None = None

    @model_validator(mode="after")
    def _outcome(self) -> Self:
        fetched = self.outcome is not AttemptOutcome.NOT_FETCHED
        if (self.artifact_sha256 is not None) is not fetched:
            raise ValueError("an attempt names its artifact exactly when it fetched it")
        failed = self.outcome is AttemptOutcome.CANONICALIZATION_FAILED
        if (self.failure_reason is not None) is not failed:
            raise ValueError(
                "an attempt names a FailureReason exactly when canonicalization failed"
            )
        return self


class StateTransition(IngestionRecord):
    """One document's change of state, in one run."""

    document_id: IdPart
    event_id: IdPart
    run_id: IdPart
    sequence: NonNegativeInt
    """Its position in its run."""
    recorded_at: AwareDatetime
    from_state: DocumentState | None
    to_state: DocumentState
    missing_reason: MissingReason | None = None
    failure_reason: FailureReason | None = None
    pilot_id: IdPart
    pilot_version: PositiveInt
    pilot_hash: Sha256Hex
    frozen_accession: Accession
    """The event manifest's release filing for the event."""
    accession: Accession | None = None
    """The filing whose exhibit was acquired: the frozen one, or an override's."""
    exhibit: NonBlankStr | None = None
    """The acquired exhibit's file name."""
    artifact_sha256: Sha256Hex | None = None
    retrieved_at: AwareDatetime | None = None
    doc_id: NonBlankStr | None = None
    override_id: IdPart | None = None
    corpus_error: NonBlankStr | None = None
    """Set when an override's filing would change the event's eligibility."""
    attempts: tuple[ExhibitAttempt, ...] = ()

    @model_validator(mode="after")
    def _state(self) -> Self:
        if self.document_id != f"{self.event_id}:release":
            raise ValueError(
                f"{self.event_id} expects {self.event_id}:release, not"
                f" {self.document_id}"
            )
        before = "the start" if self.from_state is None else self.from_state.value
        if self.to_state not in NEXT[self.from_state]:
            raise ValueError(f"{before} cannot become {self.to_state}")
        if (
            self.from_state in REOPENED
            and self.to_state is DocumentState.ACQUIRED
            and self.override_id is None
        ):
            raise ValueError(
                f"{before} becomes acquired only under an acquisition override"
            )
        allowed = REASONS.get(self.to_state, frozenset())
        if allowed and self.missing_reason not in allowed:
            raise ValueError(
                f"{self.to_state} carries a missing_reason of {sorted(allowed)}"
            )
        if not allowed and self.missing_reason is not None:
            raise ValueError(f"{self.to_state} carries no missing_reason")
        failed = self.to_state is DocumentState.FAILED
        if failed and self.failure_reason is None:
            raise ValueError("failed names its FailureReason")
        if not failed and self.failure_reason is not None:
            raise ValueError("only failed names a FailureReason")
        acquired = (self.accession, self.exhibit, self.artifact_sha256)
        if self.to_state in (DocumentState.ACQUIRED, DocumentState.PARSED) and (
            None in (*acquired, self.retrieved_at)
        ):
            raise ValueError(
                f"{self.to_state} names its accession, exhibit, artifact, and"
                " retrieval time"
            )
        if self.to_state is DocumentState.PARSED and self.doc_id is None:
            raise ValueError("parsed names its accession, exhibit, and doc_id")
        return self


def in_order(transitions: Iterable[StateTransition]) -> list[StateTransition]:
    """``transitions`` as they were recorded: runs by their earliest
    ``recorded_at``, then ``run_id``, and each run's by ``sequence``."""
    transitions = list(transitions)
    starts: dict[str, datetime] = {}
    for transition in transitions:
        start = starts.get(transition.run_id)
        if start is None or transition.recorded_at < start:
            starts[transition.run_id] = transition.recorded_at
    return sorted(transitions, key=lambda t: (starts[t.run_id], t.run_id, t.sequence))


def check_histories(transitions: Iterable[StateTransition]) -> None:
    """Refuse a run position recorded twice, or a document's transitions, under one
    pilot, that do not chain from ``expected``."""
    seen: set[tuple[str, int]] = set()
    histories: dict[tuple[str, str], list[StateTransition]] = {}
    for transition in in_order(transitions):
        position = (transition.run_id, transition.sequence)
        if position in seen:
            raise ValueError(
                f"{transition.run_id} #{transition.sequence} is recorded twice"
            )
        seen.add(position)
        key = (transition.pilot_hash, transition.document_id)
        histories.setdefault(key, []).append(transition)
    for (_, document), history in histories.items():
        state: DocumentState | None = None
        for transition in history:
            if transition.from_state != state:
                if state is None:
                    raise ValueError(
                        f"{document} starts at expected, not from"
                        f" {transition.from_state}"
                    )
                raise ValueError(
                    f"{document}: {transition.run_id} #{transition.sequence} comes"
                    f" from {transition.from_state}, but its state was {state}"
                )
            state = transition.to_state


def current_states(
    transitions: Iterable[StateTransition], pilot_hash: str
) -> dict[str, StateTransition]:
    """Each document's latest transition recorded under the pilot of ``pilot_hash``,
    by ``document_id``."""
    current: dict[str, StateTransition] = {}
    for transition in in_order(transitions):
        if transition.pilot_hash == pilot_hash:
            current[transition.document_id] = transition
    return current
