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
- **Overrides.** A ``set_release_document`` in ``acquisition-overrides.toml`` names
  an event's document: an exhibit of the frozen release filing, or of another filing
  by the issuer whose index page is saved (``events discover --filing`` saves one),
  cited as ``build.citations_refused`` checks. Its document, once it canonicalizes,
  is the release, and ``release-content/1``'s verdict is recorded without deciding.
  An override applies to a document that is ``expected``, ``acquired``,
  ``unavailable``, or ``failed``, and each of its transitions names it. When the
  other filing's acceptance would change the event's eligibility, each marks a
  ``corpus_error`` for the next corpus version, and nothing is fixed in place (P8-11).
  An override that does not check is a problem, and its document is not attempted.
- **Problems.** A saved response that cannot be read is a problem naming its repair;
  it is never fetched again, and its document stays in the state the run recorded,
  to be attempted again once the store is repaired. An override applied under its
  ID and since edited to name another event or exhibit is a problem too: an applied
  override is not edited in place.
- **Canonical documents.** Each is written once under its ``doc_id``, which hashes
  its text. One already there that differs only in the Python, lxml, and libxml2
  versions its manifest records, as another environment writes it, is kept; any
  other difference is a problem.
- **The run.** Each run writes its transitions to ``<run_id>.parquet`` under
  ``states_dir``, even when it stops, and writes nothing when it records nothing.
"""

import json
from collections.abc import Callable, Collection, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from earnings_ingestion.canonical import (
    CanonicalizationFailure,
    Canonicalized,
    canonicalize,
)
from earnings_ingestion.canonical.serialize import to_fixture_json
from earnings_ingestion.cohort.config import load_toml
from earnings_ingestion.cohort.locators import ArtifactText, CitableArtifact
from earnings_ingestion.cohort.records import UniverseManifest
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.acceptance import (
    EASTERN,
    AcceptanceTimeError,
    accepted_instant,
)
from earnings_ingestion.events.build import citations_refused
from earnings_ingestion.events.content import confirm
from earnings_ingestion.events.eligibility import IssuerMembership, decide, memberships
from earnings_ingestion.events.exhibits import ExhibitCandidate, exhibit_order
from earnings_ingestion.events.freeze import manifest_path
from earnings_ingestion.events.records import (
    AcquisitionOverride,
    AcquisitionOverridesFile,
    EventManifest,
    EventRow,
    PilotManifest,
)
from earnings_ingestion.events.release import read_document
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.state_table import read_runs, write_run
from earnings_ingestion.events.states import (
    AttemptOutcome,
    DocumentState,
    ExhibitAttempt,
    ExhibitChoice,
    MissingReason,
    StateTransition,
    current_states,
    in_order,
)
from earnings_ingestion.fetch.responses import Fetched, UnexpectedResponse
from earnings_ingestion.fetch.store import ArtifactStore, write_new
from earnings_ingestion.sec.data import SecDataError
from earnings_ingestion.sec.filing_index import FilingIndex, read_filing_index
from earnings_ingestion.sec.urls import archive_url, filing_index_url

Fetch = Callable[[str, Collection[str]], Fetched]
EXHIBIT_TYPES = frozenset({"text/html", "text/plain"})
ATTEMPTED = frozenset({DocumentState.EXPECTED, DocumentState.ACQUIRED})
OVERRIDDEN = ATTEMPTED | {DocumentState.UNAVAILABLE, DocumentState.FAILED}
"""The states from which an acquisition override moves a document."""
OVERRIDES_FILE = "acquisition-overrides.toml"
ENVIRONMENT = ("python_version", "lxml_version", "libxml2_version")
"""The manifest fields another environment writes differently for the same text."""
REPAIR = (
    "repair the store by hand: a saved response is never fetched again (PR #6's"
    " review, P2.1)"
)


def document_id(event_id: str) -> str:
    return f"{event_id}:release"


def load_acquisition_overrides(path: Path) -> AcquisitionOverridesFile:
    """The corpus's ``acquisition-overrides.toml``, read strictly; empty when
    absent."""
    if not path.exists():
        return AcquisitionOverridesFile(schema_version=1)
    return load_toml(path, AcquisitionOverridesFile)


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
        index = None if artifact is None else read_filing_index(artifact.text.body)
    except (FileNotFoundError, SecDataError, ValueError) as exc:
        raise ValueError(f"{url}: {exc}; {REPAIR}") from exc
    if index is None:
        raise ValueError(f"{url} is not saved: run events discover")
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


Target = tuple[str, str, str]
"""An override's event, filing, and exhibit."""


def _target(override: AcquisitionOverride) -> Target:
    return (override.event_id, override.accession, override.exhibit)


def _pending(
    state: StateTransition | None,
    override: AcquisitionOverride | None,
    applied: Target | None,
) -> str | None:
    """What a run does with a document: ``override`` applies its override,
    ``attempt`` tries its exhibits, ``refused`` reports an override of a document
    no override moves, ``edited`` one whose ID was ``applied`` to another target,
    and ``None`` leaves it."""
    current = DocumentState.EXPECTED if state is None else state.to_state
    if override is not None:
        if applied is not None and applied != _target(override):
            return "edited"
        mine = state is not None and state.override_id == override.override_id
        if mine and current not in ATTEMPTED:
            return None
        return "override" if current in OVERRIDDEN else "refused"
    return "attempt" if current in ATTEMPTED else None


def _applications(transitions: Iterable[StateTransition]) -> dict[str, Target]:
    """Each override's latest target, by ``override_id``, under any pilot, so an ID
    keeps one meaning: as its acquisition names it, or its attempt when it failed
    from ``acquired`` and recorded no acquisition of its own."""
    latest: dict[str, Target] = {}
    for transition in in_order(transitions):
        if transition.override_id is None:
            continue
        if transition.exhibit is not None:
            latest[transition.override_id] = (
                transition.event_id,
                transition.accession,
                transition.exhibit,
            )
        for attempt in transition.attempts:
            if attempt.choice is ExhibitChoice.OVERRIDE:
                latest[transition.override_id] = (
                    transition.event_id,
                    attempt.accession,
                    attempt.filename,
                )
    return latest


def planned_requests(
    events: EventManifest,
    pilot: PilotManifest,
    store: ArtifactStore,
    states_dir: Path,
    overrides: AcquisitionOverridesFile | None = None,
) -> tuple[int, int]:
    """What a run would fetch: the first choices not saved, and every candidate not
    saved, over the documents it would attempt, an override's document counting as
    both. The second is the most it sends before any retry: a retry after a 429 or
    a server error adds one, within the approved count, the client's cap."""
    saved = SavedResponses(store)
    rows = {row.event_id: row for row in events.rows}
    recorded = read_runs(states_dir)
    current = current_states(recorded, pilot.definition.content_hash)
    applications = _applications(recorded)
    named = {} if overrides is None else {o.event_id: o for o in overrides.overrides}
    first = most = 0
    for pilot_row in pilot.rows:
        row = rows[pilot_row.event_id]
        override = named.get(row.event_id)
        applied = None if override is None else applications.get(override.override_id)
        pending = _pending(current.get(document_id(row.event_id)), override, applied)
        if pending == "override":
            url = archive_url(row.cik, override.accession, override.exhibit)
            if url not in saved:
                first, most = first + 1, most + 1
            continue
        if pending != "attempt":
            continue
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
        self.latest: dict[str, StateTransition] = {}
        """Each document's latest transition in this run."""

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
        self.latest[transition.document_id] = transition
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


def _without_environment(bundle: object) -> object:
    """A canonical bundle without ``ENVIRONMENT``'s fields; anything else, as it
    is, so that it differs."""
    if not isinstance(bundle, dict) or not isinstance(bundle.get("manifest"), dict):
        return bundle
    manifest = {k: v for k, v in bundle["manifest"].items() if k not in ENVIRONMENT}
    return {**bundle, "manifest": manifest}


def _write(canonical_dir: Path, result: Canonicalized) -> None:
    """Write ``result`` under its ``doc_id``, keeping a file already there that
    differs only in ``ENVIRONMENT``; raises ``ValueError`` for any other
    difference."""
    path = canonical_dir / f"{result.document.doc_id}.json"
    data = to_fixture_json(result)
    try:
        write_new(path, data.encode())
    except FileExistsError:
        kept = _without_environment(json.loads(path.read_bytes()))
        if kept != _without_environment(json.loads(data)):
            raise ValueError(
                f"{path.name} holds another canonical document for the same text"
            ) from None


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


@dataclass(frozen=True)
class _Named:
    """An override's filing, checked, and what it would do to eligibility."""

    index: FilingIndex
    corpus_error: str | None


def corpus_error(
    row: EventRow,
    instant: datetime,
    membership: IssuerMembership,
    universe: UniverseManifest,
) -> str | None:
    """Why a release accepted at ``instant`` would change ``row``'s eligibility, for
    the next corpus version; ``None`` when eligibility/1 decides it as before."""
    definition = universe.definition
    decision = decide(
        row.period_end,
        instant,
        None,
        membership,
        start=definition.period_end_start,
        stop=definition.period_end_stop,
        cutoff=definition.public_information_cutoff,
    )
    if (decision.status, decision.reason) == (
        row.eligibility_status,
        row.eligibility_reason,
    ):
        return None
    return (
        f"accepted {instant.astimezone(EASTERN):%Y-%m-%d %H:%M:%S} Eastern, the"
        f" filing would make the event {decision.status}, {decision.reason}, not"
        f" {row.eligibility_status}, {row.eligibility_reason}: the next corpus"
        " version corrects it"
    )


def _named(
    saved: SavedResponses,
    row: EventRow,
    override: AcquisitionOverride,
    membership: IssuerMembership,
    universe: UniverseManifest,
) -> _Named:
    """The override's filing, from its saved index page; raises ``ValueError``,
    naming the override, when the page is not saved or does not check."""
    tag = override.override_id
    url = filing_index_url(row.cik, override.accession)
    try:
        artifact = saved.get(url)
        if artifact is None:
            raise ValueError(
                f"{tag}: {url} is not saved: run events discover --filing"
                f" {row.cik} {override.accession}"
            )
        index = read_filing_index(artifact.text.body)
        instant = accepted_instant(index.accepted)
    except (FileNotFoundError, SecDataError, AcceptanceTimeError) as exc:
        raise ValueError(f"{tag}: {url}: {exc}") from exc
    if index.accession != override.accession:
        raise ValueError(f"{tag}: {url} is the index page of {index.accession}")
    if override.exhibit not in {document.filename for document in index.documents}:
        raise ValueError(f"{tag}: {url} lists no {override.exhibit}")
    folder = archive_url(row.cik, override.accession, "")
    if refused := citations_refused(override, saved, folder):
        raise ValueError("; ".join(refused))
    error = None
    if override.accession != row.release_accession:
        error = corpus_error(row, instant, membership, universe)
    return _Named(index, error)


def _apply(
    run: _Run,
    state: StateTransition,
    row: EventRow,
    override: AcquisitionOverride,
    named: _Named,
    saved: SavedResponses,
    store: ArtifactStore,
    fetch: Fetch,
    canonical_dir: Path,
    fetched: list[str],
) -> StateTransition:
    """Take the override's document as the release, once it canonicalizes."""
    (document,) = [d for d in named.index.documents if d.filename == override.exhibit]
    url = archive_url(row.cik, override.accession, override.exhibit)
    try:
        artifact = _exhibit(saved, store, fetch, url, fetched)
    except UnexpectedResponse as refused:
        raise ValueError(f"{override.override_id}: {refused}") from refused
    marks = {"override_id": override.override_id, "corpus_error": named.corpus_error}
    acquired = {
        "accession": override.accession,
        "exhibit": override.exhibit,
        "artifact_sha256": artifact.artifact.content_sha256,
        "retrieved_at": artifact.retrieved_at,
    }
    if state.to_state is not DocumentState.ACQUIRED:
        state = run.record(state, row, DocumentState.ACQUIRED, **acquired, **marks)
    tried = {
        "accession": override.accession,
        "filename": override.exhibit,
        "exhibit_type": document.doc_type.strip() or "(none)",
        "choice": ExhibitChoice.OVERRIDE,
        "artifact_sha256": artifact.artifact.content_sha256,
    }
    result = canonicalize(
        artifact.text.body,
        source_document_id=f"{override.accession}_{override.exhibit}",
        media_type=artifact.text.media_type,
    )
    if isinstance(result, CanonicalizationFailure):
        attempt = ExhibitAttempt(
            **tried,
            outcome=AttemptOutcome.CANONICALIZATION_FAILED,
            failure_reason=result.reason,
            detail=result.detail,
        )
        return run.record(
            state,
            row,
            DocumentState.FAILED,
            missing_reason=MissingReason.PARSE_FAILED,
            failure_reason=result.reason,
            attempts=(attempt,),
            **marks,
        )
    check = confirm(
        result, row.period_end, row.reported_fiscal_year, row.reported_fiscal_quarter
    )
    outcome = (
        AttemptOutcome.CONFIRMED if check.confirmed else AttemptOutcome.NOT_CONFIRMED
    )
    attempt = ExhibitAttempt(**tried, outcome=outcome, detail=check.detail)
    _write(canonical_dir, result)
    return run.record(
        state,
        row,
        DocumentState.PARSED,
        **acquired,
        doc_id=result.document.doc_id,
        attempts=(attempt,),
        **marks,
    )


def acquire(
    events: EventManifest,
    pilot: PilotManifest,
    universe: UniverseManifest,
    store: ArtifactStore,
    fetch: Fetch,
    *,
    overrides: AcquisitionOverridesFile,
    states_dir: Path,
    canonical_dir: Path,
    run_id: str,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> Acquisition:
    """Acquire the release of each pilot event of ``pilot``, which must be frozen
    over ``events``; ``universe`` is the one ``events`` read."""
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
    recorded = read_runs(states_dir)
    current = current_states(recorded, definition.content_hash)
    applications = _applications(recorded)
    saved = SavedResponses(store)
    run = _Run(pilot, run_id, now)
    fetched: list[str] = []
    selected = {row.event_id for row in pilot.rows}
    problems = [
        f"{override.override_id}: {override.event_id} is not a pilot event"
        for override in overrides.overrides
        if override.event_id not in selected
    ]
    named = {override.event_id: override for override in overrides.overrides}
    members = memberships(universe)
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
            state = current[key]
            override = named.get(row.event_id)
            last = None if override is None else applications.get(override.override_id)
            pending = _pending(state, override, last)
            if pending == "edited":
                problems.append(
                    f"{override.override_id} was applied to {' '.join(last)} and now"
                    f" names {' '.join(_target(override))}: an applied override is"
                    " not edited in place"
                )
                continue
            if pending == "refused":
                problems.append(
                    f"{override.override_id}: {key} is {state.to_state}, which no"
                    " override changes"
                )
                continue
            if pending == "override":
                try:
                    found = _named(
                        saved, row, override, members[row.issuer_id], universe
                    )
                    current[key] = _apply(
                        run,
                        state,
                        row,
                        override,
                        found,
                        saved,
                        store,
                        fetch,
                        canonical_dir,
                        fetched,
                    )
                except (_Unusable, ValueError) as problem:
                    problems.append(str(problem))
                continue
            if pending != "attempt":
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
            key: run.latest.get(key, current[key])
            for key in (document_id(r.event_id) for r in pilot.rows)
        },
        fetched=tuple(fetched),
        problems=tuple(problems),
        path=path,
    )
