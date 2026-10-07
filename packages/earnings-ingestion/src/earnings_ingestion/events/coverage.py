"""The D4 coverage report over the pinned pilot (the Stage 6 spec, §The coverage
report; GS8; plan 9).

- **What it counts.** Each pilot document's current state, read from the runs it
  names, and so each of ``unavailable``, ``restricted``, and ``failed``. A failure
  class the pilot does not hold is a coverage gap (D4): the pilot is never reselected
  to fill it (P-C7).
- **Overrides.** Each acquisition override applied to a pilot document, with the
  verdict its attempt kept, such as ``release-content/1``'s ``not_confirmed``.
- **Its runs.** The report names the runs it read, and a rebuild reads only those.
  So later runs under the same pilot, which move documents on to ``partial`` or
  ``completed``, never change it.
- **No text.** It holds IDs, states, counts, and hashes. An attempt's ``detail`` and
  a transition's ``corpus_error`` are free text, and it copies neither.
- **No theme.** ``no_theme`` stays empty until Stage 11 counts it over train and
  dev, and Stage 14 over test (R12.4, GS18).
"""

from collections import Counter
from collections.abc import Collection, Iterable
from pathlib import Path
from typing import Literal, Self

from earnings_core import digest
from earnings_core.documents import IdPart
from earnings_core.hashing import Sha256Hex
from pydantic import (
    BaseModel,
    ConfigDict,
    NonNegativeInt,
    PositiveInt,
    model_validator,
)

from earnings_ingestion.canonical.records import IngestionRecord
from earnings_ingestion.cohort.identity import operative_hash
from earnings_ingestion.cohort.records import UniverseManifest
from earnings_ingestion.events.records import EventManifest, PilotManifest
from earnings_ingestion.events.states import (
    AttemptOutcome,
    DocumentState,
    ExhibitChoice,
    ProcessingTransition,
    StateRecord,
    current_states,
    in_order,
)

FAILURE_CLASSES = (
    DocumentState.UNAVAILABLE,
    DocumentState.RESTRICTED,
    DocumentState.FAILED,
)
"""R12.4's classes, which D4 reports as observed coverage."""


class _Part(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class PilotPin(_Part):
    """The pilot a Stage 6 record binds to (GS2); earnings-themes' ``Pin`` has the
    same fields, and the application builds both from one loaded pilot."""

    pilot_id: IdPart
    pilot_version: PositiveInt
    pilot_hash: Sha256Hex
    events_version: PositiveInt
    events_hash: Sha256Hex
    universe_version: PositiveInt
    universe_operative_hash: Sha256Hex


class StateCount(_Part):
    """How many pilot documents are in one state."""

    state: DocumentState
    count: NonNegativeInt


class CoverageGap(_Part):
    """A failure class the pilot does not hold (D4)."""

    state: DocumentState
    basis: Literal["D4"] = "D4"

    @model_validator(mode="after")
    def _a_failure_class(self) -> Self:
        if self.state not in FAILURE_CLASSES:
            raise ValueError(f"{self.state} is not one of R12.4's failure classes")
        return self


class AppliedOverride(_Part):
    """An acquisition override applied to a pilot document, and its verdict."""

    override_id: IdPart
    document_id: IdPart
    verdict: AttemptOutcome


class NoThemeCount(_Part):
    """Stage 11's and Stage 14's count of annotated bundles with no theme."""

    partition: Literal["train", "dev", "test"]
    bundles: NonNegativeInt
    no_theme: NonNegativeInt


class CoverageReport(IngestionRecord):
    """``coverage-v<N>.json``: the observed coverage of one pinned pilot."""

    coverage_version: PositiveInt
    pin: PilotPin
    run_ids: tuple[IdPart, ...]
    documents: NonNegativeInt
    states: tuple[StateCount, ...]
    gaps: tuple[CoverageGap, ...]
    overrides: tuple[AppliedOverride, ...]
    no_theme: tuple[NoThemeCount, ...] = ()
    content_hash: Sha256Hex

    @model_validator(mode="after")
    def _counts_agree(self) -> Self:
        if tuple(count.state for count in self.states) != tuple(DocumentState):
            raise ValueError("states lists every DocumentState once, in order")
        if sum(count.count for count in self.states) != self.documents:
            raise ValueError("the state counts sum to the documents")
        return self

    def count(self, state: DocumentState) -> int:
        """How many pilot documents are in ``state``."""
        return next(c.count for c in self.states if c.state is state)


def pilot_pin(
    pilot: PilotManifest, events: EventManifest, universe: UniverseManifest
) -> PilotPin:
    """The pin of a pilot loaded with its chain: its events and its universe."""
    definition = pilot.definition
    if events.definition.content_hash != definition.eligible_event_manifest_hash:
        raise ValueError("the event manifest is not the one the pilot names")
    if operative_hash(universe) != definition.universe_operative_hash:
        raise ValueError("the universe is not the one the pilot names")
    return PilotPin(
        pilot_id=definition.pilot_id,
        pilot_version=definition.pilot_version,
        pilot_hash=definition.content_hash,
        events_version=events.definition.event_manifest_version,
        events_hash=events.definition.content_hash,
        universe_version=universe.definition.universe_version,
        universe_operative_hash=definition.universe_operative_hash,
    )


def coverage_hash(report: CoverageReport) -> str:
    """The content hash: every field but ``content_hash`` itself."""
    return digest(report.model_dump(mode="json", exclude={"content_hash"}))


def _runs(transitions: Iterable[StateRecord]) -> list[str]:
    seen: list[str] = []
    for transition in in_order(transitions):
        if transition.run_id not in seen:
            seen.append(transition.run_id)
    return seen


def _overrides(
    transitions: Iterable[StateRecord], documents: Collection[str]
) -> tuple[AppliedOverride, ...]:
    kept: dict[tuple[str, str], AttemptOutcome] = {}
    for transition in in_order(transitions):
        if transition.override_id is None or transition.document_id not in documents:
            continue
        for attempt in transition.attempts:
            if attempt.choice is ExhibitChoice.OVERRIDE:
                key = (transition.override_id, transition.document_id)
                kept[key] = attempt.outcome
    return tuple(
        AppliedOverride(override_id=override, document_id=document, verdict=verdict)
        for (override, document), verdict in sorted(kept.items())
    )


def build_coverage(
    pilot: PilotManifest,
    pin: PilotPin,
    transitions: Iterable[StateRecord],
    *,
    run_ids: Collection[str] | None = None,
    version: int = 1,
) -> CoverageReport:
    """The coverage report over ``pilot``'s documents, from ``run_ids`` or, when
    none is named, from every run recorded under the pilot."""
    pilot_hash = pilot.definition.content_hash
    if pin.pilot_hash != pilot_hash:
        raise ValueError("the pin names another pilot")
    under = [t for t in transitions if t.pilot_hash == pilot_hash]
    recorded = _runs(under)
    if run_ids is not None:
        if unknown := sorted(set(run_ids) - set(recorded)):
            raise ValueError(f"no transition under the pilot in run {unknown[0]}")
        under = [t for t in under if t.run_id in run_ids]
    current = current_states(under, pilot_hash)
    documents = [f"{row.event_id}:release" for row in pilot.rows]
    if missing := [document for document in documents if document not in current]:
        raise ValueError(f"{missing[0]} has no state in these runs")
    counts = Counter(current[document].to_state for document in documents)
    draft = CoverageReport(
        coverage_version=version,
        pin=pin,
        run_ids=tuple(_runs(under)),
        documents=len(documents),
        states=tuple(
            StateCount(state=state, count=counts[state]) for state in DocumentState
        ),
        gaps=tuple(
            CoverageGap(state=state) for state in FAILURE_CLASSES if not counts[state]
        ),
        overrides=_overrides(under, set(documents)),
        content_hash="0" * 64,
    )
    return draft.model_copy(update={"content_hash": coverage_hash(draft)})


AFTER_PARSED = frozenset(
    {
        DocumentState.PARSED,
        DocumentState.PARTIAL,
        DocumentState.COMPLETED,
        DocumentState.COMPLETED_NO_THEME,
    }
)
"""The states of a document whose canonical document exists."""


def parsed_documents(
    transitions: Iterable[StateRecord], pilot_hash: str
) -> dict[str, str]:
    """Each pilot event whose document is ``parsed`` or later, with the ``doc_id``
    its ``parsed`` transition named: later stages' runs need not repeat it.
    A processing failure preserves canonical availability; a parse failure does
    not. Availability here confers no successful analytical observation."""
    under = [t for t in in_order(transitions) if t.pilot_hash == pilot_hash]
    doc_ids = {
        t.event_id: t.doc_id
        for t in under
        if t.to_state is DocumentState.PARSED and t.doc_id is not None
    }
    current = current_states(under, pilot_hash)
    return {
        state.event_id: doc_ids[state.event_id]
        for state in current.values()
        if (state.to_state in AFTER_PARSED or isinstance(state, ProcessingTransition))
        and state.event_id in doc_ids
    }


def load_coverage(path: Path) -> CoverageReport:
    """A frozen report, refused unless it hashes to its ``content_hash``."""
    report = CoverageReport.model_validate_json(path.read_bytes())
    if coverage_hash(report) != report.content_hash:
        raise ValueError(f"{path} does not hash to its content_hash")
    return report
