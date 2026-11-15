"""The evidence record beside a frozen event manifest (the Stage 5 spec, §The event
manifest; EV11).

``events-v<N>.evidence.json`` cites what each row rests on, in Stage 4's
``Citation`` and ``EvidenceLocator``:

- the periodic report's submissions row, and its companyfacts labels;
- each candidate's index page, and each amendment's, at its Accepted value;
- the release filing's index page at its Accepted value, and its Item 2.02 text;
- the release's submissions row at ``acceptanceDateTime``, its cross-check.

A row with no ``acceptanceDateTime`` has nothing to cross-check (plan 26, D2): the
periodic report's row is cited without it, and the release has no cross-check.

It also records each submissions file and older page the build read, with its
convention, and each older page skipped by its dates. Every citation carries its
``retrieved_at``. The record lies outside the manifest's hash, so a re-fetch changes
it and nothing else. It holds URLs, hashes, and locators, never source text (P6-3).

``check_evidence`` verifies every citation again against a store: the saved bytes,
each locator, and the citation's source, URL and ``retrieved_at`` against its
artifact's retrievals. Loading checks that each release citation is its row's index
page (``freeze.load_event_evidence``).
"""

from datetime import datetime
from functools import cache

from earnings_ingestion.cohort.locators import ArtifactText, LocatorError
from earnings_ingestion.cohort.records import Citation
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.build import EventBuild, EventDetail
from earnings_ingestion.events.filings import Placed, SavedFile
from earnings_ingestion.events.records import (
    EventCitations,
    EventEvidence,
    EventManifest,
    FileEvidence,
)
from earnings_ingestion.events.saved import SavedResponses, cited_remedy
from earnings_ingestion.fetch.store import ArtifactStore, StoredArtifact
from earnings_ingestion.sec.data import Filing
from earnings_ingestion.sec.urls import companyfacts_url

LIMITATIONS = (
    (
        "first_publication_time is the release filing's EDGAR acceptance time, an"
        " upper bound on when its results first became public: a newswire release"
        " can come first (EV9)"
    ),
    (
        "Each acceptance time is its index page's Accepted value, read as Eastern"
        " wall time; submissions' acceptanceDateTime is only a cross-check, in the"
        " convention each file's cross-checked rows establish (EV10)"
    ),
    (
        "release-id/1 reads each candidate's primary document only; no exhibit was"
        " fetched before the freeze (EV2)"
    ),
)


def _row(file: SavedFile, filing: Filing, *columns: str) -> Citation:
    """A submissions row's values, by JSON pointer. A row with no value cites no
    ``acceptanceDateTime``."""
    if filing.accepted_at is None:
        columns = tuple(c for c in columns if c != "acceptanceDateTime")
    text = file.artifact.text
    return file.artifact.cite(*(text.pointer(filing.pointer(c)) for c in columns))


def _accepted(placed: Placed) -> Citation:
    """A filing's index page, at its Accepted value."""
    page = placed.index_artifact
    return page.cite(page.text.find(placed.index.accepted))


def _event(detail: EventDetail, saved: SavedResponses) -> EventCitations:
    slot, found, release = detail.slot, detail.identification, detail.release
    labels = None
    if slot.labels is not None:
        facts = saved.get(companyfacts_url(slot.cik))
        labels = facts.cite(facts.text.pointer(slot.labels.pointer))
    item_text = None
    if release is not None:
        for candidate in found.candidates:
            if candidate.placed.filing.accession == release.filing.accession:
                item_text = candidate.item_text()
    periodic = slot.periodic
    return EventCitations(
        event_id=slot.event_id,
        periodic_row=_row(
            periodic.file,
            periodic.filing,
            "accessionNumber",
            "form",
            "reportDate",
            "acceptanceDateTime",
        ),
        labels=labels,
        candidates=tuple(_accepted(c.placed) for c in found.candidates),
        amendments=tuple(_accepted(placed) for placed in found.amendments),
        release=None if release is None else _accepted(release),
        item_text=item_text,
        cross_check=(
            None
            if release is None or release.filing.accepted_at is None
            else _row(release.file, release.filing, "acceptanceDateTime")
        ),
    )


def evidence_of(
    build: EventBuild, manifest: EventManifest, saved: SavedResponses
) -> EventEvidence:
    """The evidence record of ``manifest``, the freeze of ``build``."""
    files, skipped = {}, {}
    for filings in build.issuers.values():
        for file in filings.files:
            artifact = file.artifact
            files[artifact.url] = FileEvidence(
                url=artifact.url,
                sha256=artifact.artifact.content_sha256,
                retrieved_at=artifact.retrieved_at,
                convention=file.survey.convention,
                rows_cross_checked=len(file.survey.checks),
            )
        for page in filings.skipped:
            skipped[page.url] = page
    definition = manifest.definition
    return EventEvidence(
        corpus_id=definition.corpus_id,
        event_manifest_version=definition.event_manifest_version,
        event_manifest_hash=definition.content_hash,
        limitations=LIMITATIONS,
        files=tuple(files[url] for url in sorted(files)),
        skipped_pages=tuple(skipped[url] for url in sorted(skipped)),
        events=tuple(
            _event(build.details[row.event_id], saved) for row in manifest.rows
        ),
    )


def _citations(events: EventCitations) -> list[tuple[str, Citation]]:
    single = [
        ("periodic_row", events.periodic_row),
        ("labels", events.labels),
        ("release", events.release),
        ("item_text", events.item_text),
        ("cross_check", events.cross_check),
    ]
    listed = [("candidates", c) for c in events.candidates]
    listed += [("amendments", c) for c in events.amendments]
    return [(name, c) for name, c in [*single, *listed] if c is not None]


def check_evidence(evidence: EventEvidence, store: ArtifactStore) -> tuple[str, ...]:
    """Every citation, and every file read, checked against ``store``'s saved bytes
    and retrievals; the problems found, or none. A citation or file must name a URL
    its artifact was retrieved from, and a ``retrieved_at`` that retrieval gave. A
    citation must name the ``sec-edgar`` source. An artifact whose bytes are gone or
    changed is named with ``cited_remedy``'s remedy, which reads the store's records
    only then, and its URL and ``retrieved_at`` are not checked."""
    problems = []
    saved = cache(lambda: SavedResponses(store))

    def read(sha256: str) -> StoredArtifact | None:
        try:
            return store.get(
                SEC_SOURCE_ID,
                sha256,
                rights_status=SEC_RIGHTS.rights_status,
                rights_basis=SEC_RIGHTS.rights_basis,
            )
        except (FileNotFoundError, ValueError) as exc:
            remedy = cited_remedy(saved(), sha256)
            problems.append(f"{exc}; {remedy}" if remedy else str(exc))
            return None

    def retrieved(
        where: str, url: str, retrieved_at: datetime, stored: StoredArtifact
    ) -> None:
        """Refuse a ``url`` that is not among the artifact's retrievals, or a
        ``retrieved_at`` that none of that URL's retrievals gave."""
        own = [r for r in stored.retrievals if r.request_url == url]
        if not own:
            problems.append(f"{where}: url {url} is not where its artifact came from")
        elif retrieved_at not in {r.retrieved_at for r in own}:
            problems.append(
                f"{where}: retrieved_at {retrieved_at.isoformat()} matches no"
                f" retrieval of {url}"
            )

    for file in evidence.files:
        if (stored := read(file.sha256)) is not None:
            retrieved(f"files {file.url}", file.url, file.retrieved_at, stored)
    for events in evidence.events:
        for name, citation in _citations(events):
            stored = read(citation.artifact.content_sha256)
            if stored is None:
                continue
            where = f"{events.event_id} {name}"
            if citation.source_id != SEC_SOURCE_ID:
                problems.append(
                    f"{where}: source_id {citation.source_id!r} is not"
                    f" {SEC_SOURCE_ID!r}"
                )
            retrieved(where, citation.url, citation.retrieved_at, stored)
            text = ArtifactText(stored.body, stored.ref.media_type)
            for locator in citation.locators:
                try:
                    text.verify(locator)
                except LocatorError as exc:
                    problems.append(f"{where}: {exc}")
    return tuple(problems)
