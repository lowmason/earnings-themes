"""Discovery: save every SEC response the event build reads, through the shared SEC
client (the Stage 5 spec, §Store, client, and readers; EV2; plan 7, P7-9, P7-10).

``discover(universe, fetch, store)`` takes ``fetch``, the shared client's
``SecClient.fetch``, and saves each response in ``store`` under ``sec-edgar``. Only
the CLI opens the client (P6-22). It fetches only what ``store`` lacks, so a rerun
resumes where a stopped run left off. Each phase reads what the one before saved:

1. each candidate issuer's submissions file and companyfacts file;
2. what ``issuer_filings`` reads and finds missing, until nothing is: each older page
   whose dates meet ``[start, cutoff]``, then the index page of every Item 2.02 8-K
   and 8-K/A that either convention places in that range (P7-9);
3. the primary document of every candidate that ``release-id/1`` finds.

So discovery fetches exactly what the build reads, and never an exhibit (EV2).

Last, it reads what it saved as the build does. A saved response the build cannot
read, because its bytes are gone or changed or it is not the response its URL names,
is never fetched again, since it is saved. ``Discovery.problems`` names each one, and
``events discover`` exits 1.

``discover_filing`` saves one filing's index page, and an 8-K's or 8-K/A's primary
document. It is the remedy for an ``acceptance_time_unknown`` finding, and for a
``set_release_filing`` that names a filing discovery did not read.
"""

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from earnings_ingestion.cohort.records import UniverseManifest
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.filings import RELEASE_FORMS, issuer_filings
from earnings_ingestion.events.release import identify
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.slots import issuer_slots
from earnings_ingestion.fetch.client import Fetched
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.companyfacts import read_companyfacts
from earnings_ingestion.sec.urls import (
    archive_url,
    companyfacts_url,
    filing_index_url,
    submissions_url,
)

type Fetch = Callable[[str, frozenset[str]], Fetched]
JSON = frozenset({"application/json"})
HTML = frozenset({"text/html"})
DOCUMENT = frozenset({"text/html", "text/plain"})
"""A primary document may be plain text; ``release-id/1`` then reports it unread."""
NOT_SAVED = "nothing saved from "
"""How the readers begin a problem that discovery answers by fetching."""


@dataclass
class Discovery:
    """What a discovery run requested, in order, and what it saved but cannot read."""

    fetched: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)
    """Each saved response the build cannot read: its bytes are gone or changed, or
    it is not the response its URL names. It is saved, so no rerun fetches it again."""


class _Run:
    def __init__(
        self, fetch: Fetch, store: ArtifactStore, say: Callable[[str], None]
    ) -> None:
        self.fetch, self.store, self.say = fetch, store, say
        self.result = Discovery()

    def phase(self, name: str, wanted: Iterable[tuple[str, frozenset[str]]]) -> int:
        """Fetch what ``wanted`` names and the store lacks; return how many."""
        saved = SavedResponses(self.store)
        todo = {url: types for url, types in wanted if url not in saved}
        self.say(f"{name}: {len(todo)} to fetch")
        for url, types in todo.items():
            if url in self.result.fetched:
                raise RuntimeError(f"{url} was fetched, and is still missing")
            fetched = self.fetch(url, types)
            self.store.put(
                SEC_SOURCE_ID,
                fetched.body,
                fetched.retrieval,
                rights_status=SEC_RIGHTS.rights_status,
                rights_basis=SEC_RIGHTS.rights_basis,
            )
            self.result.fetched.append(url)
        return len(todo)


def discover(
    universe: UniverseManifest,
    fetch: Fetch,
    store: ArtifactStore,
    *,
    say: Callable[[str], None] = lambda line: None,
) -> Discovery:
    """Save every response the event build reads for ``universe``'s candidates.
    ``say`` hears each phase's count before it is fetched."""
    definition = universe.definition
    start, stop = definition.period_end_start, definition.period_end_stop
    cutoff = definition.public_information_cutoff
    ciks = {issuer.issuer_id: issuer.cik for issuer in universe.issuers}
    issuers = [(i, ciks[i]) for i in sorted(universe.candidate_issuer_ids)]
    run = _Run(fetch, store, say)

    run.phase(
        "submissions and companyfacts",
        [
            (url, JSON)
            for _, cik in issuers
            for url in (submissions_url(cik), companyfacts_url(cik))
        ],
    )
    while True:
        saved = SavedResponses(store)
        missing = [
            url
            for issuer_id, cik in issuers
            for url in issuer_filings(
                saved, cik, issuer_id, start=start, cutoff=cutoff
            ).missing
        ]
        wanted = [(url, JSON if url.endswith(".json") else HTML) for url in missing]
        if not run.phase("older pages and index pages", wanted):
            break

    saved = SavedResponses(store)
    documents = []
    for issuer_id, cik in issuers:
        filings = issuer_filings(saved, cik, issuer_id, start=start, cutoff=cutoff)
        facts = saved.get(companyfacts_url(cik))
        if filings.registrant is None or facts is None:
            continue
        made, _ = issuer_slots(
            filings,
            read_companyfacts(facts.text.body),
            issuer_id,
            start=start,
            stop=stop,
        )
        for slot in made:
            found = identify(slot, filings.releases, saved, cutoff=cutoff)
            for candidate in found.candidates:
                filing = candidate.placed.filing
                url = archive_url(cik, filing.accession, filing.primary_document)
                documents.append((url, DOCUMENT))
    run.phase("primary documents", documents)
    run.result.problems.extend(_unreadable(SavedResponses(store), issuers, universe))
    return run.result


def _unreadable(
    saved: SavedResponses, issuers: list[tuple[str, str]], universe: UniverseManifest
) -> list[str]:
    """What the build would refuse among the saved responses, read as the build reads
    them: each issuer's problems but what is not saved, which discovery fetches, and
    each problem with a candidate's primary document."""
    definition = universe.definition
    start, stop = definition.period_end_start, definition.period_end_stop
    cutoff = definition.public_information_cutoff
    problems = []
    for issuer_id, cik in issuers:
        filings = issuer_filings(saved, cik, issuer_id, start=start, cutoff=cutoff)
        problems.extend(p for p in filings.problems if not p.startswith(NOT_SAVED))
        facts = saved.get(companyfacts_url(cik))
        if filings.registrant is None or facts is None:
            continue
        made, _ = issuer_slots(
            filings,
            read_companyfacts(facts.text.body),
            issuer_id,
            start=start,
            stop=stop,
        )
        for slot in made:
            found = identify(slot, filings.releases, saved, cutoff=cutoff)
            problems.extend(found.problems)
    return problems


def discover_filing(
    universe: UniverseManifest,
    cik: str,
    accession: str,
    fetch: Fetch,
    store: ArtifactStore,
    *,
    say: Callable[[str], None] = lambda line: None,
) -> Discovery:
    """Save one filing's index page, and its primary document if it is an 8-K or
    8-K/A. The issuer's saved submissions must list it."""
    named = [issuer.issuer_id for issuer in universe.issuers if issuer.cik == cik]
    if not named:
        raise ValueError(
            f"no issuer of {universe.definition.universe_id} has CIK {cik}"
        )
    definition = universe.definition
    filings = issuer_filings(
        SavedResponses(store),
        cik,
        named[0],
        start=definition.period_end_start,
        cutoff=definition.public_information_cutoff,
    )
    listed = [
        f for file in filings.files for f in file.filings if f.accession == accession
    ]
    if not listed:
        raise ValueError(
            f"the saved filings of CIK {cik} list no {accession}: run events discover"
        )
    filing = listed[0]
    wanted = [(filing_index_url(cik, accession), HTML)]
    if filing.form in RELEASE_FORMS:
        wanted.append((archive_url(cik, accession, filing.primary_document), DOCUMENT))
    run = _Run(fetch, store, say)
    run.phase(f"{filing.form} {accession}", wanted)
    return run.result
