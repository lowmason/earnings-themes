"""Refetch the saved SEC responses that discovery cannot use (plan 25).

Discovery never fetches a saved response again, even one that cannot be used.
``read_back`` (``events.discover``) lists each such response's URL as unusable, and
a refetch replaces it with a newer retrieval of that URL, which ``SavedResponses``
then reads.

``plan_refetch`` accepts only URLs that ``read_back`` finds unusable, so a refetch
never replaces a usable response under a frozen citation. It refuses an empty list,
a URL that is not saved, and a saved URL that is not unusable: an exhibit, which
``events acquire --refetch`` refetches, a response that reads, or a page behind an
unusable submissions file, which is read, and classified, once that file is
refetched. A submissions file brings each older page saved for its issuer, matched
by URL, since a damaged file cannot list them.

``run_refetch`` fetches exactly the plan's URLs through ``fetch``, the shared SEC
client's ``SecClient.fetch``, which only the CLI opens (P6-22), and saves each as
discovery does. ``ArtifactStore.put`` moves bytes that no longer hash to their name
into ``quarantine/`` before it writes them again, and never moves valid bytes. A URL
whose new bytes match no earlier retrieval of it is ``changed``: the build may then
read other bytes than it froze. Last, it reads back the saved responses and returns
what still cannot be used. It runs no discovery phase: a plain ``events discover``
rerun fetches what a refetched file now lists.

A fetch or a save that fails stops the refetch. ``RefetchInterrupted`` is raised
from that failure, and its ``partial`` holds what was saved before it: the URLs,
which of them changed, and where bytes were moved. A rerun cannot tell this again,
because the saved URLs then read, and are refused as usable.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from earnings_ingestion.cohort.records import UniverseManifest
from earnings_ingestion.events.discover import (
    DOCUMENT,
    HTML,
    JSON,
    NOT_SAVED,
    Fetch,
    read_back,
    save_fetched,
)
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.identifiers import pad_cik
from earnings_ingestion.sec.urls import submissions_page_url, submissions_url


@dataclass(frozen=True)
class RefetchPlan:
    """The URLs a refetch fetches, each once, in order."""

    urls: tuple[str, ...]

    @property
    def count(self) -> int:
        """The requests the refetch sends: one for each URL."""
        return len(self.urls)


@dataclass(frozen=True)
class Refetched:
    """What a refetch fetched, and what it found."""

    fetched: tuple[str, ...]
    """Each URL fetched and saved, in plan order."""
    changed: tuple[str, ...]
    """Each URL whose new bytes match no earlier retrieval of it."""
    quarantined: tuple[Path, ...]
    """Where the refetch moved bytes that no longer hashed to their name, each once."""
    problems: tuple[str, ...]
    """What the read-back after the refetch still cannot use."""


def expected_types(url: str) -> frozenset[str]:
    """The media types discovery accepts from ``url``."""
    if url.endswith(".json"):
        return JSON
    if url.endswith("-index.htm"):
        return HTML
    return DOCUMENT


def _refusal(url: str, saved: SavedResponses) -> str:
    if url not in saved:
        return (
            f"{NOT_SAVED}{url}: events discover fetches a missing response, and"
            " events acquire a missing exhibit"
        )
    return (
        f"{url} is not among the responses discovery cannot use, and a refetch"
        " replaces only those; an exhibit is refetched by earnings-pipeline events"
        " acquire --refetch, and a page behind an unusable submissions file is"
        " classified once that file is refetched"
    )


def plan_refetch(
    universe: UniverseManifest, store: ArtifactStore, named: Sequence[str]
) -> RefetchPlan:
    """The refetch of ``named``, each a saved response that discovery cannot use, in
    the order named, each with its saved older pages if it is a submissions file.
    ``ValueError`` names every URL it refuses, one to a line."""
    names = tuple(dict.fromkeys(named))
    if not names:
        raise ValueError("name at least one saved response to refetch")
    saved = SavedResponses(store)
    unusable = frozenset(read_back(universe, saved).unusable)
    refused = [_refusal(url, saved) for url in names if url not in unusable]
    if refused:
        raise ValueError("\n".join(refused))
    pages = {
        submissions_url(issuer.cik): submissions_page_url(
            f"CIK{pad_cik(issuer.cik)}-submissions-"
        )
        for issuer in universe.issuers
    }
    urls = [
        url
        for name in names
        for url in (name, *(saved.urls(prefix=pages[name]) if name in pages else ()))
    ]
    return RefetchPlan(urls=tuple(dict.fromkeys(urls)))


class RefetchInterrupted(Exception):
    """A refetch that stopped when a fetch or a save failed. ``partial`` holds what it
    saved before, with no problems read back; ``__cause__`` is the failure. Only the
    refetch knows each URL's earlier hashes, so only it can tell what ``changed``."""

    def __init__(self, partial: Refetched) -> None:
        super().__init__(
            f"the refetch stopped after it saved {len(partial.fetched)} URL(s)"
        )
        self.partial = partial


def run_refetch(
    universe: UniverseManifest, plan: RefetchPlan, fetch: Fetch, store: ArtifactStore
) -> Refetched:
    """Fetch each of ``plan``'s URLs again and save it as its newest response, then
    read back what still cannot be used. A fetch or a save that fails raises
    ``RefetchInterrupted`` from that failure, with what was saved before it."""
    saved = SavedResponses(store)
    earlier = {url: saved.hashes(url) for url in plan.urls}
    before = len(store.quarantined)
    fetched, changed = [], []

    def found(problems: tuple[str, ...]) -> Refetched:
        return Refetched(
            fetched=tuple(fetched),
            changed=tuple(changed),
            quarantined=tuple(dict.fromkeys(store.quarantined[before:])),
            problems=problems,
        )

    for url in plan.urls:
        try:
            response = fetch(url, expected_types(url))
            save_fetched(store, response)
        except Exception as exc:
            raise RefetchInterrupted(found(())) from exc
        fetched.append(url)
        if response.retrieval.sha256 not in earlier[url]:
            changed.append(url)
    return found(read_back(universe, SavedResponses(store)).problems)
