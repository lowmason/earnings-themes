"""Build the event manifest from the frozen cohort and Stage 5's saved responses (the
Stage 5 spec, §Slots through §Review overrides; plan 7, P7-12, P7-15, and P7-16).

``build_events`` fetches nothing. Every fact it uses is in the frozen cohort, the
overrides file, or a response saved under ``data/raw/events/``. For each candidate
issuer, it reads the saved filings, makes the slots, identifies each slot's release
filing by ``release-id/1``, and decides its eligibility by ``eligibility/1``. Then it
applies the overrides:

- ``set_release_filing`` names an 8-K or 8-K/A of the event's issuer, listed in the
  issuer's read files, whose index page is saved and which was accepted, on the
  Eastern calendar, in the range ``release-id/1`` reads: after the event's period end
  P and by the issuer's next period end P', or by the cutoff when none is visible. One
  of its citations is in that filing's folder. The event takes the filing's acceptance
  time and the method ``override``, and its eligibility is decided again, with any
  outcome. A release accepted after P' has no override: the event keeps what the rule
  gives it, which ``retain_unresolved`` can keep when it is ``ambiguous`` (the
  ``release-id/2`` item in specs/deferred_items.md). No two events share a release (S
  §Review overrides, amended 2026-09-27).
- ``retain_unresolved`` keeps an event that is ``ambiguous`` with the override's
  reason. It is judged after any ``set_release_filing`` of the same event.
- ``acknowledge`` answers a ``period_gap`` or ``no_slots`` finding whose digest it
  names.

**Refused or stale** (P7-16). An override that names no such event, finding, or
filing is refused, as S §Review overrides says. So is one that acknowledges another
kind of finding, or whose citation does not verify. A refusal is a problem. An
acknowledgement whose finding has changed is stale, as is a ``retain_unresolved``
whose event is no longer ``ambiguous`` with its reason. A stale override holds the
freeze, and ``events build`` names it.

What no review can settle stops the build with ``EventBuildError``, which lists every
problem: a missing or unreadable response, a filing an issuer's files list more than
once, and a refused override. Every row and finding the manifest hashes is a fact: no
retrieval time, file hash, or pointer into a saved file. An override is hashed whole,
with its citations, and a ``set_release_filing``'s citation carries its artifact's
hash and a locator, which the build looks up in the store. So a re-fetch re-versions
no manifest while the store keeps each cited artifact; in a fresh store, a cited page
served with other bytes refuses the override until it is re-cited, and the re-cited
override re-versions the manifest. What each row rests on stays on the build, outside
the hash, for the evidence record and the report.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

from earnings_ingestion.cohort.config import load_toml
from earnings_ingestion.cohort.identity import operative_hash
from earnings_ingestion.cohort.locators import ArtifactText, LocatorError
from earnings_ingestion.cohort.records import UniverseManifest
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.acceptance import (
    SOURCE_TIMEZONE,
    AcceptanceTimeError,
    accepted_instant,
    eastern_date,
)
from earnings_ingestion.events.eligibility import (
    ELIGIBILITY_POLICY,
    Decision,
    decide,
    memberships,
)
from earnings_ingestion.events.filings import (
    IssuerFilings,
    Placed,
    index_disagreement,
    issuer_filings,
)
from earnings_ingestion.events.records import (
    ACKNOWLEDGEABLE,
    AcquisitionOverride,
    EventFinding,
    EventManifest,
    EventManifestDefinition,
    EventOverride,
    EventOverrideKind,
    EventOverridesFile,
    EventRow,
    EventStatus,
    IdentificationMethod,
    content_hash,
)
from earnings_ingestion.events.release import (
    RELEASE_POLICY,
    Identification,
    identify,
)
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.slots import Slot, issuer_slots
from earnings_ingestion.sec.companyfacts import CompanyFacts, read_companyfacts
from earnings_ingestion.sec.data import SecDataError
from earnings_ingestion.sec.filing_index import read_filing_index
from earnings_ingestion.sec.urls import archive_url, companyfacts_url, filing_index_url

CORPUS_ID = "djia-2024q3-2026q2"
CORPUS_DIR = Path("config") / "corpus" / CORPUS_ID
EVENTS_STORE = Path("data") / "raw" / "events"
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
RELEASE_FORMS = frozenset({"8-K", "8-K/A"})


class EventBuildError(ValueError):
    """Problems no review can settle; the build stops and lists every one."""

    def __init__(self, problems: Sequence[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("; ".join(problems))


def load_overrides(path: Path) -> EventOverridesFile:
    """The corpus's ``overrides.toml``, read strictly; empty when absent."""
    if not path.exists():
        return EventOverridesFile(schema_version=1)
    return load_toml(path, EventOverridesFile)


@dataclass(frozen=True)
class EventDetail:
    """What one row rests on, kept outside the manifest's hash."""

    slot: Slot
    identification: Identification
    release: Placed | None
    """The rule's release filing, or the one a ``set_release_filing`` names."""
    decision: Decision


@dataclass(frozen=True)
class EventBuild:
    """Everything an event manifest holds except its version, hash, and time."""

    corpus_id: str
    universe: UniverseManifest
    rows: tuple[EventRow, ...]
    findings: tuple[EventFinding, ...]
    overrides: tuple[EventOverride, ...]
    stale_overrides: tuple[str, ...]
    details: dict[str, EventDetail]
    """By ``event_id``."""
    issuers: dict[str, IssuerFilings]
    """By ``issuer_id``."""

    @property
    def blocking(self) -> tuple[EventFinding, ...]:
        """The findings that hold the freeze."""
        return tuple(finding for finding in self.findings if finding.holds_freeze)

    @property
    def unretained(self) -> tuple[EventRow, ...]:
        """The ``ambiguous`` rows no ``retain_unresolved`` keeps."""
        return tuple(
            row
            for row in self.rows
            if row.eligibility_status is EventStatus.AMBIGUOUS and not row.retained
        )

    @property
    def holds_freeze(self) -> bool:
        return bool(self.blocking or self.stale_overrides or self.unretained)

    def manifest(self, version: int, created_at: datetime) -> EventManifest:
        definition = self.universe.definition
        draft = EventManifest(
            definition=EventManifestDefinition(
                corpus_id=self.corpus_id,
                event_manifest_version=version,
                universe_id=definition.universe_id,
                universe_version=definition.universe_version,
                universe_operative_hash=operative_hash(self.universe),
                discovery_policy_version=RELEASE_POLICY,
                eligibility_policy_version=ELIGIBILITY_POLICY,
                public_information_cutoff=definition.public_information_cutoff,
                content_hash="0" * 64,
                created_at=created_at,
            ),
            rows=self.rows,
            findings=self.findings,
            overrides=self.overrides,
        )
        hashed = draft.definition.model_copy(
            update={"content_hash": content_hash(draft)}
        )
        return draft.model_copy(update={"definition": hashed})

    @property
    def content_hash(self) -> str:
        return self.manifest(1, EPOCH).definition.content_hash

    def report(self) -> list[str]:
        """What ``events build`` prints: each row with its candidates' readings, then
        the findings and what holds the freeze (P7-15)."""
        lines = []
        for row in self.rows:
            detail = self.details[row.event_id]
            method = row.identification_method
            release = (
                "no release filing"
                if row.release_accession is None
                else f"{row.release_accession} ({method})"
            )
            lines.append(
                f"{row.event_id}  {row.eligibility_status}"
                f"  {row.eligibility_reason}  {release}"
            )
            found = detail.identification
            for candidate in found.candidates:
                reading = candidate.reading
                said = [
                    f"dates {', '.join(d.isoformat() for d in reading.dates) or '-'}",
                    f"periods {', '.join(map(str, reading.periods)) or '-'}",
                    f"preliminary {'yes' if reading.preliminary else 'no'}",
                ]
                if reading.unread:
                    said.append(f"unread: {reading.unread}")
                lines.append(
                    f"  candidate {candidate.placed.filing.accession}"
                    f" accepted {candidate.placed.instant:%Y-%m-%d %H:%M} UTC:"
                    f" {'; '.join(said)}; {candidate.dropped or 'kept'}"
                )
            for placed in found.amendments:
                lines.append(
                    f"  amendment {placed.filing.accession}, never chosen by the rule"
                )
            for placed, why in found.passed_over:
                lines.append(f"  passed over {placed.filing.accession}: {why}")
        for finding in self.findings:
            if finding.holds_freeze:
                state = "blocks"
            elif finding.resolved_by:
                state = f"acknowledged by {', '.join(finding.resolved_by)}"
            else:
                state = "reported"
            lines.append(f"{finding.finding_id} [{state}]: {finding.detail}")
        for override_id in self.stale_overrides:
            lines.append(f"{override_id}: stale, and holds the freeze")
        for row in self.unretained:
            lines.append(
                f"{row.event_id}: {row.eligibility_reason}, not retained, and holds"
                " the freeze"
            )
        return lines


def _companyfacts(
    saved: SavedResponses, cik: str, problems: list[str]
) -> CompanyFacts | None:
    url = companyfacts_url(cik)
    try:
        artifact = saved.get(url)
        if artifact is None:
            problems.append(f"nothing saved from {url}: run events discover")
            return None
        facts = read_companyfacts(artifact.text.body)
    except (FileNotFoundError, ValueError) as exc:
        problems.append(f"{url}: {exc}")
        return None
    if facts.cik != cik:
        problems.append(f"{url} is the companyfacts file of CIK {facts.cik}")
        return None
    return facts


def _named_filing(
    filings: IssuerFilings,
    saved: SavedResponses,
    accession: str,
    slot: Slot,
    cutoff: date,
) -> tuple[Placed | None, str | None]:
    """The filing a ``set_release_filing`` names for ``slot``, placed by its index
    page; or why the override is refused."""
    listed = [
        (filing, file)
        for file in filings.files
        for filing in file.filings
        if filing.accession == accession
    ]
    if not listed:
        return None, f"the issuer's read filings list no {accession}"
    filing, file = listed[0]
    if filing.form not in RELEASE_FORMS:
        return None, f"{accession} is a {filing.form}, not an 8-K or 8-K/A"
    url = filing_index_url(filings.cik, accession)
    try:
        artifact = saved.get(url)
        if artifact is None:
            return None, (
                f"no index page of {accession} is saved: run events discover"
                f" --filing {filings.cik} {accession}"
            )
        index = read_filing_index(artifact.text.body)
        instant = accepted_instant(index.accepted)
    except (FileNotFoundError, ValueError, SecDataError, AcceptanceTimeError) as exc:
        return None, f"{url}: {exc}"
    if index.accession != accession:
        return None, f"{url} is the index page of {index.accession}"
    if (why := index_disagreement(filing, index)) is not None:
        return None, f"{url}: {why}"
    why = release_refusal(
        accession, instant, slot.period_end, slot.next_period_end, cutoff
    )
    if why is not None:
        return None, why
    return Placed(filing, file, index, artifact, instant), None


def release_refusal(
    accession: str,
    instant: datetime,
    period_end: date,
    next_period_end: date | None,
    cutoff: date,
) -> str | None:
    """Why a filing accepted at ``instant`` cannot be a ``set_release_filing``'s
    choice for the event of ``period_end``, or ``None``. It must fall, on the Eastern
    calendar, in the range ``release-id/1`` reads, ``(P, P']``, where P' is the
    issuer's next period end, or the cutoff when none is visible; and never after the
    cutoff (P-C4)."""
    day = eastern_date(instant)
    if day <= period_end:
        return (
            f"{accession} was accepted on {day}, on or before the event's period end"
            f" {period_end}"
        )
    if day > cutoff:
        return f"{accession} was accepted on {day}, after the cutoff {cutoff} (P-C4)"
    if next_period_end is not None and day > next_period_end:
        return (
            f"{accession} was accepted on {day}, after the issuer's next period end"
            f" {next_period_end}"
        )
    return None


def citations_refused(
    override: EventOverride | AcquisitionOverride,
    saved: SavedResponses,
    folder: str | None,
) -> list[str]:
    """Why an override's citations fail: a stored locator that no longer cites what it
    hashed, or a cited URL whose retrievals were all redirected (F13); or, with the
    named filing's ``folder``, no citation there of an SEC artifact retrieved from its
    own URL, unredirected, at a locator that verifies."""
    refused = []
    grounded = failed = False
    for citation in override.citations:
        if citation.artifact_sha256 is None or citation.source_id != SEC_SOURCE_ID:
            continue
        inside = folder is not None and citation.url.startswith(folder)
        try:
            stored = saved.store.get(
                SEC_SOURCE_ID,
                citation.artifact_sha256,
                rights_status=SEC_RIGHTS.rights_status,
                rights_basis=SEC_RIGHTS.rights_basis,
            )
            if citation.locator is not None:
                ArtifactText(stored.body, stored.ref.media_type).verify(
                    citation.locator
                )
        except (FileNotFoundError, ValueError, LocatorError) as exc:
            refused.append(f"{override.override_id}: {exc}")
            failed |= inside
            continue
        own = [r for r in stored.retrievals if r.request_url == citation.url]
        if own and all(r.final_url != r.request_url for r in own):
            refused.append(
                f"{override.override_id}: {citation.url} was redirected to"
                f" {own[-1].final_url}"
            )
            failed |= inside
            continue
        grounded |= inside and citation.locator is not None and bool(own)
    if folder is not None and not (grounded or failed):
        if any(citation.url.startswith(folder) for citation in override.citations):
            refused.append(
                f"{override.override_id}: no citation in {folder} is a saved SEC"
                " artifact, retrieved from its URL, with a locator"
            )
        else:
            refused.append(f"{override.override_id}: no citation is in {folder}")
    return refused


def shared_releases(
    rows: Sequence[EventRow], sets: dict[str, tuple[EventOverride, Placed]]
) -> list[str]:
    """A refusal for each filing that two rows take as their release, naming the
    ``set_release_filing`` overrides that chose it, or else ``release-id/1``. Within
    one issuer every release lies in its own event's range ``(P, P']``, by the rule
    or an override, and those ranges never meet; so only a filing that two issuers
    list, such as a co-registrant's 8-K, can be shared, and the rule can share it
    without any override (see specs/deferred_items.md)."""
    events: dict[str, list[str]] = {}
    for row in rows:
        if row.release_accession is not None:
            events.setdefault(row.release_accession, []).append(row.event_id)
    refused = []
    for accession, sharing in sorted(events.items()):
        if len(sharing) < 2:
            continue
        named = sorted(sharing)
        chosen = [sets[event][0].override_id for event in named if event in sets]
        refused.append(
            f"{', '.join(chosen) or RELEASE_POLICY}: {accession} would be the"
            f" release of {' and '.join(named)}"
        )
    return refused


def build_events(
    universe: UniverseManifest,
    saved: SavedResponses,
    overrides: EventOverridesFile,
    *,
    corpus_id: str,
) -> EventBuild:
    """The event manifest's content that the cohort, overrides, and saved responses
    support; ``EventBuildError`` lists what no review can settle."""
    definition = universe.definition
    start, stop = definition.period_end_start, definition.period_end_stop
    cutoff = definition.public_information_cutoff
    issuers = {issuer.issuer_id: issuer for issuer in universe.issuers}
    problems: list[str] = []
    findings: list[EventFinding] = []
    read: dict[str, IssuerFilings] = {}
    slots: list[tuple[Slot, Identification]] = []
    for issuer_id in sorted(universe.candidate_issuer_ids):
        cik = issuers[issuer_id].cik
        filings = issuer_filings(saved, cik, issuer_id, start=start, cutoff=cutoff)
        read[issuer_id] = filings
        problems.extend(filings.problems)
        findings.extend(filings.findings)
        facts = _companyfacts(saved, cik, problems)
        if filings.registrant is None or facts is None:
            continue
        made, found = issuer_slots(filings, facts, issuer_id, start=start, stop=stop)
        findings.extend(found)
        for slot in made:
            identification = identify(slot, filings.releases, saved, cutoff=cutoff)
            problems.extend(identification.problems)
            slots.append((slot, identification))
    if problems:
        raise EventBuildError(problems)

    by_event = {slot.event_id: (slot, found) for slot, found in slots}
    by_finding = {finding.finding_id: finding for finding in findings}
    sets: dict[str, tuple[EventOverride, Placed]] = {}
    retains: dict[str, EventOverride] = {}
    acknowledged: dict[str, list[str]] = {}
    stale: list[str] = []
    for override in overrides.overrides:
        if override.kind is EventOverrideKind.ACKNOWLEDGE:
            finding = by_finding.get(override.finding_id)
            if finding is None:
                problems.append(
                    f"{override.override_id}: no finding {override.finding_id}"
                )
            elif finding.kind not in ACKNOWLEDGEABLE:
                problems.append(
                    f"{override.override_id}: a {finding.kind} finding is never"
                    " acknowledged"
                )
            elif finding.digest != override.finding_digest:
                stale.append(override.override_id)
            else:
                acknowledged.setdefault(finding.finding_id, []).append(
                    override.override_id
                )
            continue
        if override.event_id not in by_event:
            problems.append(f"{override.override_id}: no event {override.event_id}")
            continue
        if override.kind is EventOverrideKind.RETAIN_UNRESOLVED:
            retains[override.event_id] = override
            continue
        slot, _ = by_event[override.event_id]
        placed, why = _named_filing(
            read[slot.issuer_id], saved, override.accession, slot, cutoff
        )
        if placed is None:
            problems.append(f"{override.override_id}: {why}")
            continue
        folder = archive_url(slot.cik, override.accession, "")
        refused = citations_refused(override, saved, folder)
        if refused:
            problems.extend(refused)
            continue
        sets[override.event_id] = (override, placed)
    for override in overrides.overrides:
        if override.kind is not EventOverrideKind.SET_RELEASE_FILING:
            problems.extend(citations_refused(override, saved, None))
    if problems:
        raise EventBuildError(problems)

    members = memberships(universe)
    rows, details = [], {}
    for slot, found in slots:
        applied = []
        if slot.event_id in sets:
            chosen, release = sets[slot.event_id]
            method = IdentificationMethod.OVERRIDE
            applied.append(chosen.override_id)
        elif found.release is not None:
            release, method = found.release.placed, found.method
        else:
            release, method = None, None
        decision = decide(
            slot.period_end,
            None if release is None else release.instant,
            None if release is not None else found.reason,
            members[slot.issuer_id],
            start=start,
            stop=stop,
            cutoff=cutoff,
        )
        retained = False
        if (retain := retains.get(slot.event_id)) is not None:
            if (
                decision.status is EventStatus.AMBIGUOUS
                and decision.reason is retain.reason
            ):
                retained = True
                applied.append(retain.override_id)
            else:
                stale.append(retain.override_id)
        labels = slot.labels
        instant = None if release is None else release.instant
        rows.append(
            EventRow(
                event_id=slot.event_id,
                issuer_id=slot.issuer_id,
                cik=slot.cik,
                period_end=slot.period_end,
                reported_fiscal_year=None if labels is None else labels.fiscal_year,
                reported_fiscal_quarter=(
                    None if labels is None else labels.fiscal_period
                ),
                periodic_accession=slot.periodic.filing.accession,
                periodic_form=slot.periodic.filing.form,
                release_accession=None if release is None else release.filing.accession,
                candidate_accessions=tuple(
                    candidate.placed.filing.accession for candidate in found.candidates
                ),
                identification_method=method,
                filing_acceptance_time=instant,
                first_publication_time=instant,
                source_timezone=SOURCE_TIMEZONE,
                first_publication_source_id=None if release is None else SEC_SOURCE_ID,
                membership_assertion_id=decision.membership_assertion_id,
                eligibility_status=decision.status,
                eligibility_reason=decision.reason,
                retained=retained,
                override_ids=tuple(sorted(applied)),
            )
        )
        details[slot.event_id] = EventDetail(slot, found, release, decision)
    problems.extend(shared_releases(rows, sets))
    if problems:
        raise EventBuildError(problems)
    resolved = tuple(
        finding.model_copy(
            update={"resolved_by": tuple(sorted(acknowledged[finding.finding_id]))}
        )
        if finding.finding_id in acknowledged
        else finding
        for finding in sorted(findings, key=lambda f: f.finding_id)
    )
    return EventBuild(
        corpus_id=corpus_id,
        universe=universe,
        rows=tuple(sorted(rows, key=lambda row: row.event_id)),
        findings=resolved,
        overrides=tuple(sorted(overrides.overrides, key=lambda o: o.override_id)),
        stale_overrides=tuple(sorted(stale)),
        details=details,
        issuers=read,
    )
