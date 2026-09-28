"""Plan B's acquisition: each pilot event's release document, fetched through the
shared SEC client, canonicalized, and confirmed (the Stage 5 spec, §Plan B; plan 8,
P8-6 to P8-12).

- **What it reads.** The caller passes the current event manifest and the pilot
  frozen over it, as ``events acquire`` reads them (P8-4). Acquisition writes no
  frozen record (P-C7).
- **Expected.** A run first records ``expected`` for each pilot event that has no
  transition under the pilot, in selection order.
- **Attempts.** It then attempts each document whose current state is ``expected``
  or ``acquired``. It reads the release filing's saved index page and Item 2.02 text,
  and tries the filing's ``EX-99*`` exhibits in R1.2's order (``exhibit_order``). A
  saved exhibit is read from the store; any other is fetched and saved. The first
  exhibit's bytes make the document ``acquired``. ``walker-1`` canonicalizes each,
  and the first that ``release-content/1`` confirms makes it ``parsed``, with its
  canonical document written under ``canonical_dir``. Otherwise the document is
  ``unavailable`` with ``not_found`` when no exhibit could be fetched, ``failed``
  with ``parse_failed`` and the first ``FailureReason`` when one failed to
  canonicalize, and ``unavailable`` with ``no_confirmed_release`` when each fetched
  canonicalized and none was confirmed. Every attempt is recorded.
- **Requests.** Only ``fetch`` sends, which ``events acquire`` gives as the shared
  SEC client's (R1.3, D5); acquisition has no throttle of its own. A response the
  client refuses (``UnexpectedResponse``: a status other than 200, an unexpected
  media type, or a redirect) is that exhibit's attempt, and the next is tried.
  ``AccessStop`` ends the run: its transitions so far are written, and each document
  not attempted stays ``expected``. Acquisition saves exhibits only, never an index
  page or a primary document, so it never changes what the event build reads.
- **Problems.** A saved response that cannot be read is a problem naming its repair;
  it is never fetched again, and its document keeps its state.
- **The run.** Each run writes its transitions to ``<run_id>.parquet`` under
  ``states_dir``, even when it stops, and writes nothing when it records nothing.
"""

from collections.abc import Callable, Collection
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from earnings_ingestion.canonical import (
    CanonicalizationFailure,
    Canonicalized,
    canonicalize,
)
from earnings_ingestion.canonical.serialize import to_fixture_json
from earnings_ingestion.cohort.locators import ArtifactText, CitableArtifact
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.content import confirm
from earnings_ingestion.events.exhibits import ExhibitCandidate, exhibit_order
from earnings_ingestion.events.freeze import manifest_path
from earnings_ingestion.events.records import EventManifest, EventRow, PilotManifest
from earnings_ingestion.events.release import read_document
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.state_table import read_runs, write_run
from earnings_ingestion.events.states import (
    AttemptOutcome,
    DocumentState,
    ExhibitAttempt,
    MissingReason,
    StateTransition,
    current_states,
)
from earnings_ingestion.fetch.responses import Fetched, UnexpectedResponse
from earnings_ingestion.fetch.store import ArtifactStore, write_new
from earnings_ingestion.sec.data import SecDataError
from earnings_ingestion.sec.filing_index import read_filing_index
from earnings_ingestion.sec.urls import archive_url, filing_index_url

Fetch = Callable[[str, Collection[str]], Fetched]
EXHIBIT_TYPES = frozenset({"text/html", "text/plain"})
ATTEMPTED = frozenset({DocumentState.EXPECTED, DocumentState.ACQUIRED})
REPAIR = (
    "repair the store by hand: a saved response is never fetched again (PR #6's"
    " review, P2.1)"
)


def document_id(event_id: str) -> str:
    return f"{event_id}:release"


@dataclass(frozen=True)
class Acquisition:
    run_id: str
    transitions: tuple[StateTransition, ...]
    """This run's."""
    states: dict[str, StateTransition]
    """Each pilot document's current state after the run, in selection order."""
    fetched: tuple[str, ...]
    """The URLs fetched and saved."""
    problems: tuple[str, ...]
    path: Path | None
    """The run's file; ``None`` when it recorded nothing."""


@dataclass(frozen=True)
class _Filing:
    """A pilot event's release filing, as its saved pages give it."""

    candidates: tuple[ExhibitCandidate, ...]


def _filing(saved: SavedResponses, row: EventRow) -> _Filing:
    """The filing's exhibits in R1.2's order, read from its saved index page and
    Item 2.02 text; raises ``ValueError``, naming the URL, when a page is not saved
    or cannot be read."""
    url = filing_index_url(row.cik, row.release_accession)
    try:
        artifact = saved.get(url)
        if artifact is None:
            raise ValueError(f"{url} is not saved: run events discover")
        index = read_filing_index(artifact.text.body)
    except (FileNotFoundError, SecDataError) as exc:
        raise ValueError(f"{url}: {exc}; {REPAIR}") from exc
    except ValueError as exc:
        raise ValueError(f"{url}: {exc}; {REPAIR}") from exc
    primary = [d for d in index.documents if d.doc_type == index.form]
    text = ""
    if primary:
        document = archive_url(row.cik, row.release_accession, primary[0].filename)
        try:
            found = saved.get(document)
        except (FileNotFoundError, ValueError) as exc:
            raise ValueError(f"{document}: {exc}; {REPAIR}") from exc
        reading = None if found is None else read_document(found)
        if reading is not None and reading.sections:
            body, _ = found.text.canonical
            text = " ".join(body[start:end] for start, end in reading.sections)
    return _Filing(exhibit_order(index, text))


def planned_requests(
    events: EventManifest,
    pilot: PilotManifest,
    store: ArtifactStore,
    states_dir: Path,
) -> tuple[int, int]:
    """What a run would fetch: the first choices not saved, and every candidate not
    saved, over the documents it would attempt. The second is the most it can send."""
    saved = SavedResponses(store)
    rows = {row.event_id: row for row in events.rows}
    current = current_states(read_runs(states_dir), pilot.definition.content_hash)
    first = most = 0
    for pilot_row in pilot.rows:
        state = current.get(document_id(pilot_row.event_id))
        if state is not None and state.to_state not in ATTEMPTED:
            continue
        row = rows[pilot_row.event_id]
        try:
            candidates = _filing(saved, row).candidates
        except ValueError:
            continue
        urls = [
            archive_url(row.cik, row.release_accession, c.document.filename)
            for c in candidates
        ]
        missing = [url for url in urls if url not in saved]
        most += len(missing)
        if urls and urls[0] in missing:
            first += 1
    return first, most


class _Run:
    def __init__(
        self, pilot: PilotManifest, run_id: str, now: Callable[[], datetime]
    ) -> None:
        self.pilot, self.run_id, self.now = pilot.definition, run_id, now
        self.transitions: list[StateTransition] = []

    def record(
        self,
        before: StateTransition | None,
        row: EventRow,
        state: DocumentState,
        **details: object,
    ) -> StateTransition:
        transition = StateTransition(
            document_id=document_id(row.event_id),
            event_id=row.event_id,
            run_id=self.run_id,
            sequence=len(self.transitions),
            recorded_at=self.now(),
            from_state=None if before is None else before.to_state,
            to_state=state,
            pilot_id=self.pilot.pilot_id,
            pilot_version=self.pilot.pilot_version,
            pilot_hash=self.pilot.content_hash,
            frozen_accession=row.release_accession,
            **details,
        )
        self.transitions.append(transition)
        return transition


class _Unusable(Exception):
    """A saved exhibit that cannot be read."""


def _exhibit(
    saved: SavedResponses,
    store: ArtifactStore,
    fetch: Fetch,
    url: str,
    fetched: list[str],
) -> CitableArtifact:
    """The exhibit at ``url``, read from the store, or fetched and saved."""
    if url in saved:
        try:
            artifact = saved.get(url)
        except (FileNotFoundError, ValueError) as exc:
            raise _Unusable(f"{url}: {exc}; {REPAIR}") from exc
        assert artifact is not None
        return artifact
    got = fetch(url, EXHIBIT_TYPES)
    ref = store.put(
        SEC_SOURCE_ID,
        got.body,
        got.retrieval,
        rights_status=SEC_RIGHTS.rights_status,
        rights_basis=SEC_RIGHTS.rights_basis,
    )
    fetched.append(url)
    return CitableArtifact(
        source_id=SEC_SOURCE_ID,
        url=url,
        artifact=ref,
        retrieved_at=got.retrieval.retrieved_at,
        text=ArtifactText(got.body, got.retrieval.media_type),
    )


def _write(canonical_dir: Path, result: Canonicalized) -> None:
    path = canonical_dir / f"{result.document.doc_id}.json"
    write_new(path, to_fixture_json(result).encode())


def _attempt(
    run: _Run,
    state: StateTransition,
    row: EventRow,
    candidates: tuple[ExhibitCandidate, ...],
    saved: SavedResponses,
    store: ArtifactStore,
    fetch: Fetch,
    canonical_dir: Path,
    fetched: list[str],
) -> StateTransition:
    attempts: list[ExhibitAttempt] = []
    failure = None
    for candidate in candidates:
        name = candidate.document.filename
        url = archive_url(row.cik, row.release_accession, name)
        tried = {
            "accession": row.release_accession,
            "filename": name,
            "exhibit_type": candidate.document.doc_type.strip(),
            "choice": candidate.choice,
        }
        try:
            artifact = _exhibit(saved, store, fetch, url, fetched)
        except UnexpectedResponse as refused:
            attempts.append(
                ExhibitAttempt(
                    **tried, outcome=AttemptOutcome.NOT_FETCHED, detail=str(refused)
                )
            )
            continue
        acquired = {
            "accession": row.release_accession,
            "exhibit": name,
            "artifact_sha256": artifact.artifact.content_sha256,
            "retrieved_at": artifact.retrieved_at,
        }
        if state.to_state is DocumentState.EXPECTED:
            state = run.record(state, row, DocumentState.ACQUIRED, **acquired)
        result = canonicalize(
            artifact.text.body,
            source_document_id=f"{row.release_accession}_{name}",
            media_type=artifact.text.media_type,
        )
        sha = artifact.artifact.content_sha256
        if isinstance(result, CanonicalizationFailure):
            attempts.append(
                ExhibitAttempt(
                    **tried,
                    outcome=AttemptOutcome.CANONICALIZATION_FAILED,
                    artifact_sha256=sha,
                    failure_reason=result.reason,
                    detail=result.detail,
                )
            )
            failure = failure or result.reason
            continue
        check = confirm(
            result,
            row.period_end,
            row.reported_fiscal_year,
            row.reported_fiscal_quarter,
        )
        if not check.confirmed:
            attempts.append(
                ExhibitAttempt(
                    **tried,
                    outcome=AttemptOutcome.NOT_CONFIRMED,
                    artifact_sha256=sha,
                    detail=check.detail,
                )
            )
            continue
        attempts.append(
            ExhibitAttempt(
                **tried, outcome=AttemptOutcome.CONFIRMED, artifact_sha256=sha
            )
        )
        _write(canonical_dir, result)
        return run.record(
            state,
            row,
            DocumentState.PARSED,
            **acquired,
            doc_id=result.document.doc_id,
            attempts=tuple(attempts),
        )
    if state.to_state is DocumentState.EXPECTED:
        reason = {"missing_reason": MissingReason.NOT_FOUND}
        return run.record(
            state, row, DocumentState.UNAVAILABLE, **reason, attempts=tuple(attempts)
        )
    if failure is not None:
        return run.record(
            state,
            row,
            DocumentState.FAILED,
            missing_reason=MissingReason.PARSE_FAILED,
            failure_reason=failure,
            attempts=tuple(attempts),
        )
    return run.record(
        state,
        row,
        DocumentState.UNAVAILABLE,
        missing_reason=MissingReason.NO_CONFIRMED_RELEASE,
        attempts=tuple(attempts),
    )


def acquire(
    events: EventManifest,
    pilot: PilotManifest,
    store: ArtifactStore,
    fetch: Fetch,
    *,
    states_dir: Path,
    canonical_dir: Path,
    run_id: str,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> Acquisition:
    """Acquire the release of each pilot event of ``pilot``, which must be frozen
    over ``events``."""
    definition, read = pilot.definition, events.definition
    if (definition.event_manifest_version, definition.eligible_event_manifest_hash) != (
        read.event_manifest_version,
        read.content_hash,
    ):
        name = manifest_path(Path(), read.event_manifest_version).name
        raise ValueError(
            f"{definition.pilot_id} v{definition.pilot_version} is not frozen over {name}"
        )
    rows = {row.event_id: row for row in events.rows}
    current = current_states(read_runs(states_dir), definition.content_hash)
    saved = SavedResponses(store)
    run = _Run(pilot, run_id, now)
    fetched: list[str] = []
    problems: list[str] = []
    try:
        for pilot_row in pilot.rows:
            key = document_id(pilot_row.event_id)
            if key not in current:
                current[key] = run.record(
                    None,
                    rows[pilot_row.event_id],
                    DocumentState.EXPECTED,
                    missing_reason=MissingReason.NOT_YET_CHECKED,
                )
        for pilot_row in pilot.rows:
            key, row = document_id(pilot_row.event_id), rows[pilot_row.event_id]
            if current[key].to_state not in ATTEMPTED:
                continue
            try:
                candidates = _filing(saved, row).candidates
                current[key] = _attempt(
                    run,
                    current[key],
                    row,
                    candidates,
                    saved,
                    store,
                    fetch,
                    canonical_dir,
                    fetched,
                )
            except (_Unusable, ValueError) as problem:
                problems.append(str(problem))
    finally:
        path = write_run(states_dir, run.transitions) if run.transitions else None
    return Acquisition(
        run_id=run_id,
        transitions=tuple(run.transitions),
        states={
            document_id(r.event_id): current[document_id(r.event_id)]
            for r in pilot.rows
        },
        fetched=tuple(fetched),
        problems=tuple(problems),
        path=path,
    )
