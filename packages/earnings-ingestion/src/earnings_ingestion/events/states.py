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

Acquisition remains ingestion schema version 1 (P6-5). Processing outcomes use
an additive schema 2; ``docs/data-dictionary.md`` documents both contracts.
"""

from collections.abc import Iterable
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Literal, Self

from earnings_core.artifacts import NonBlankStr
from earnings_core.documents import IdPart
from earnings_core.hashing import Sha256Hex
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    NonNegativeInt,
    PositiveInt,
    field_validator,
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


class ProcessingMissingReason(StrEnum):
    """Closed schema-2 processing missingness, separate from acquisition."""

    PROCESSING_FAILED = "processing_failed"
    EXTRACTION_PARTIAL = "extraction_partial"
    CLASSIFICATION_INCOMPLETE = "classification_incomplete"
    ASSESSMENT_REFUSED = "assessment_refused"
    ASSESSMENT_INCOMPLETE = "assessment_incomplete"
    ASSESSMENT_FLAGGED = "assessment_flagged"
    CALIBRATION_REQUIRED = "calibration_required"
    POLICY_REVIEW = "policy_review"
    VALID_UNMATCHED = "valid_unmatched"
    NO_THEME_UNCONFIRMED = "no_theme_unconfirmed"
    NO_ELIGIBLE_UNITS = "no_eligible_units"
    COPY_PROCESSING_CONFLICT = "copy_processing_conflict"


class ProcessingReason(StrEnum):
    """Pinned extraction/support/coding causes without a themes dependency."""

    AMBIGUOUS_OCCURRENCE = "ambiguous_occurrence"
    ASSESSMENT_FLAGGED = "assessment_flagged"
    ASSESSMENT_INCOMPLETE = "assessment_incomplete"
    ASSESSMENT_REFUSED = "assessment_refused"
    BLANK_CLAIM = "blank_claim"
    BUDGET_EXHAUSTED = "budget_exhausted"
    CACHE_CORRUPT = "cache_corrupt"
    CALIBRATION_REQUIRED = "calibration_required"
    CANONICAL_HASH_MISMATCH = "canonical_hash_mismatch"
    CLAIM_TOO_LONG = "claim_too_long"
    CLASSIFICATION_INCOMPLETE = "classification_incomplete"
    CODEBOOK_NOT_APPROVED = "codebook_not_approved"
    COPY_PROCESSING_CONFLICT = "copy_processing_conflict"
    CROSSES_SPEAKER_TURN = "crosses_speaker_turn"
    CROSSING_ELEMENTS = "crossing_elements"
    DOCUMENT_INTEGRITY = "document_integrity"
    DUPLICATE_CLAIM = "duplicate_claim"
    DUPLICATE_ELEMENT = "duplicate_element"
    DUPLICATE_LABEL = "duplicate_label"
    DUPLICATE_QUOTE = "duplicate_quote"
    DUPLICATE_THEME = "duplicate_theme"
    ELEMENT_ID_MISMATCH = "element_id_mismatch"
    EXPLICIT_NO_THEME = "explicit_no_theme"
    EXTRACTION_PARTIAL = "extraction_partial"
    FIXTURE_POLICY = "fixture_policy"
    HIERARCHY_CONFLICT = "hierarchy_conflict"
    INPUT_CHANGED = "input_changed"
    INPUT_TOO_LONG = "input_too_long"
    INVALID_BUNDLE = "invalid_bundle"
    INVALID_CONTRIBUTION = "invalid_contribution"
    INVALID_HEADER_REFERENCE = "invalid_header_reference"
    INVALID_PANEL = "invalid_panel"
    INVALID_QUOTE = "invalid_quote"
    INVALID_REFERENCES = "invalid_references"
    JUDGE_EXHAUSTED = "judge_exhausted"
    LOCATOR_MISMATCH = "locator_mismatch"
    LOCATOR_NOT_FOUND = "locator_not_found"
    MALFORMED_RECORD = "malformed_record"
    MALFORMED_REPLY = "malformed_reply"
    MASKS_MISMATCH = "masks_mismatch"
    MISSING_ASSESSMENT = "missing_assessment"
    MIXED_CODEBOOK = "mixed_codebook"
    MODEL_MISMATCH = "model_mismatch"
    NO_ELIGIBLE_UNITS = "no_eligible_units"
    NO_THEME_FIT = "no_theme_fit"
    NO_THEME_UNCONFIRMED = "no_theme_unconfirmed"
    OCR_DERIVED_TEXT = "ocr_derived_text"
    OUTSIDE_CHUNK = "outside_chunk"
    OUTSIDE_ELEMENT = "outside_element"
    OUTSIDE_PARENT = "outside_parent"
    PARENT_CYCLE = "parent_cycle"
    PARENT_ORDER = "parent_order"
    POLICY_ACCEPT = "policy_accept"
    POLICY_MISMATCH = "policy_mismatch"
    POLICY_REJECT = "policy_reject"
    POLICY_REVIEW = "policy_review"
    PROCESSING_FAILED = "processing_failed"
    QUOTE_TEXT_MISMATCH = "quote_text_mismatch"
    REPLAY_MISS = "replay_miss"
    REQUESTS_EXHAUSTED = "requests_exhausted"
    SCORER_EXHAUSTED = "scorer_exhausted"
    SCORER_FAILED = "scorer_failed"
    SPAN_OUT_OF_BOUNDS = "span_out_of_bounds"
    STORAGE_CORRUPT = "storage_corrupt"
    TABLE_CELL_PARENT = "table_cell_parent"
    TOKENS_EXHAUSTED = "tokens_exhausted"
    TOOL_CALL_REFUSED = "tool_call_refused"
    TRANSPORT_ERROR = "transport_error"
    UNEXPECTED_ERROR = "unexpected_error"
    UNKNOWN_CLAIM = "unknown_claim"
    UNKNOWN_ELEMENT = "unknown_element"
    UNKNOWN_LABEL = "unknown_label"
    UNKNOWN_PARENT = "unknown_parent"
    UNKNOWN_QUOTE = "unknown_quote"
    UNKNOWN_THEME = "unknown_theme"
    VALID_UNMATCHED = "valid_unmatched"
    WRONG_CODEBOOK = "wrong_codebook"
    WRONG_DOCUMENT = "wrong_document"
    WRONG_SOURCE_RUN = "wrong_source_run"


class ProcessingTransition(StateTransition):
    """One schema-2 outcome from an acquired, parsed release.

    ``completion_hash`` binds DocumentCompletion, or WorkflowFailure for a failed
    outcome. The failed state explicitly identifies failure evidence; it never
    represents a completed extraction record.
    """

    schema_version: Literal[2] = 2
    processing_run_id: IdPart
    processing_run_hash: Sha256Hex
    completion_hash: Sha256Hex
    processing_reason: ProcessingReason | None = None
    missing_reason: ProcessingMissingReason | None = None

    @field_validator("schema_version", "sequence", "pilot_version", mode="before")
    @classmethod
    def _strict_integers(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("state_record_invalid")
        return value

    @model_validator(mode="after")
    def _state(self) -> Self:
        validate_processing_transition(self)
        return self


def validate_processing_transition(transition: ProcessingTransition) -> None:
    """Validate the processing graph; predecessor equality belongs to history."""
    if transition.document_id != f"{transition.event_id}:release":
        raise ValueError("state_record_invalid")
    if transition.from_state is not DocumentState.PARSED or transition.to_state not in {
        DocumentState.PARTIAL,
        DocumentState.COMPLETED,
        DocumentState.COMPLETED_NO_THEME,
        DocumentState.FAILED,
    }:
        raise ValueError("state_not_processable")
    acquired = (
        transition.accession,
        transition.exhibit,
        transition.artifact_sha256,
        transition.retrieved_at,
        transition.doc_id,
    )
    if None in acquired or transition.attempts or transition.failure_reason is not None:
        raise ValueError("state_record_invalid")
    for stamp in (transition.recorded_at, transition.retrieved_at):
        if stamp.utcoffset() != timedelta(0):
            raise ValueError("state_record_invalid")
    state = transition.to_state
    missing = transition.missing_reason
    reason = transition.processing_reason
    if state is DocumentState.FAILED:
        if missing is not ProcessingMissingReason.PROCESSING_FAILED or reason is None:
            raise ValueError("state_record_invalid")
        if reason is ProcessingReason.EXPLICIT_NO_THEME:
            raise ValueError("state_record_invalid")
    elif state is DocumentState.PARTIAL:
        if missing is None or missing is ProcessingMissingReason.PROCESSING_FAILED:
            raise ValueError("state_record_invalid")
        if reason is None or reason in {
            ProcessingReason.EXPLICIT_NO_THEME,
            ProcessingReason.PROCESSING_FAILED,
        }:
            raise ValueError("state_record_invalid")
    elif state is DocumentState.COMPLETED_NO_THEME:
        if missing is not None or reason is not ProcessingReason.EXPLICIT_NO_THEME:
            raise ValueError("state_record_invalid")
    elif missing is not None or reason is not None:
        raise ValueError("state_record_invalid")


type StateRecord = StateTransition | ProcessingTransition

# A processing row inherits provenance, but records no new acquisition attempt.
PROCESSING_PREDECESSOR_FIELDS = (
    "document_id",
    "event_id",
    "pilot_id",
    "pilot_version",
    "pilot_hash",
    "frozen_accession",
    "accession",
    "exhibit",
    "artifact_sha256",
    "retrieved_at",
    "doc_id",
    "override_id",
    "corpus_error",
)


def in_order(transitions: Iterable[StateRecord]) -> list[StateRecord]:
    """``transitions`` as they were recorded: runs by their earliest
    ``recorded_at``, then ``run_id``, and each run's by ``sequence``."""
    transitions = list(transitions)
    starts: dict[str, datetime] = {}
    for transition in transitions:
        start = starts.get(transition.run_id)
        if start is None or transition.recorded_at < start:
            starts[transition.run_id] = transition.recorded_at
    return sorted(transitions, key=lambda t: (starts[t.run_id], t.run_id, t.sequence))


def check_histories(transitions: Iterable[StateRecord]) -> None:
    """Refuse a run position recorded twice, or a document's transitions, under one
    pilot, that do not chain from ``expected``."""
    seen: set[tuple[str, int]] = set()
    histories: dict[tuple[str, str], list[StateRecord]] = {}
    for transition in in_order(transitions):
        if isinstance(transition, ProcessingTransition):
            # model_copy/model_construct may bypass construction validators.
            try:
                ProcessingTransition.model_validate_json(transition.model_dump_json())
            except ValueError:
                raise ValueError("state_record_invalid") from None
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
        predecessor: StateRecord | None = None
        for transition in history:
            if isinstance(predecessor, ProcessingTransition):
                raise ValueError("state_not_processable")  # noqa: TRY004 - valid type, terminal state
            if isinstance(transition, ProcessingTransition):
                if predecessor is None or state is not DocumentState.PARSED:
                    raise ValueError("state_not_processable")
                if any(
                    getattr(transition, field) != getattr(predecessor, field)
                    for field in PROCESSING_PREDECESSOR_FIELDS
                ):
                    raise ValueError("state_predecessor_mismatch")
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
            predecessor = transition


def current_states(
    transitions: Iterable[StateRecord], pilot_hash: str
) -> dict[str, StateRecord]:
    """Each document's latest transition recorded under the pilot of ``pilot_hash``,
    by ``document_id``."""
    current: dict[str, StateRecord] = {}
    for transition in in_order(transitions):
        if transition.pilot_hash == pilot_hash:
            current[transition.document_id] = transition
    return current
