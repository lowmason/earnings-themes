"""Stage 5's saved SEC responses, indexed once per build (plan 7, P7-12).

``ArtifactStore.latest`` reads every retrieval record on each call. That suits
Stage 4's few dozen SEC files, but not the several hundred responses Stage 5 reads.
``SavedResponses`` reads the records once, keeps the newest retrieval of each URL,
and returns each artifact as a ``CitableArtifact``, which the store rechecks against
its name when it is first read.

Every response is cited with the ``sec-edgar`` source's rights, as Stage 4 cites
SEC's records (``cohort.register.SEC_RIGHTS``).

A response whose newest retrieval was redirected is refused by raising, never
skipped: it stays among the saved URLs, so discovery never fetches it again, and
every reader reports it (PR #6's review, F13). The shared SEC client refuses a
redirect before it is saved, so only a record saved before that check can be one.

A saved response that cannot be used is replaced only by an explicit refetch, a
newer retrieval of its URL (plan 25). ``refetch_remedy`` names that command, and
``cited_remedy`` names it for an artifact cited by its hash, when a refetch can
restore it.
"""

from earnings_ingestion.cohort.locators import ArtifactText, CitableArtifact
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.fetch.records import Retrieval
from earnings_ingestion.fetch.store import ArtifactStore


def refetch_remedy(url: str, what: str = "it") -> str:
    """The command that replaces ``url``'s saved response, which cannot be used."""
    return f"refetch {what}: earnings-pipeline events discover --refetch {url}"


class SavedResponses:
    """The newest saved response of each URL in one store's ``sec-edgar`` source."""

    def __init__(self, store: ArtifactStore) -> None:
        self.store = store
        newest: dict[str, Retrieval] = {}
        hashes: dict[str, set[str]] = {}
        folder = store.root / SEC_SOURCE_ID / "retrievals"
        for path in sorted(folder.glob("*/*.json")):
            record = Retrieval.model_validate_json(path.read_text(encoding="utf-8"))
            hashes.setdefault(record.request_url, set()).add(record.sha256)
            known = newest.get(record.request_url)
            if known is None or (record.retrieved_at, record.sha256) > (
                known.retrieved_at,
                known.sha256,
            ):
                newest[record.request_url] = record
        self._newest = newest
        self._hashes = {url: frozenset(found) for url, found in hashes.items()}
        self._read: dict[str, CitableArtifact] = {}

    def __contains__(self, url: str) -> bool:
        return url in self._newest

    def __len__(self) -> int:
        return len(self._newest)

    def urls(self, prefix: str = "") -> tuple[str, ...]:
        """Every saved URL that begins with ``prefix``, sorted."""
        return tuple(sorted(url for url in self._newest if url.startswith(prefix)))

    def hashes(self, url: str) -> frozenset[str]:
        """The SHA-256 of every retrieval ever saved from ``url``; empty if none."""
        return self._hashes.get(url, frozenset())

    def get(self, url: str) -> CitableArtifact | None:
        """The newest response saved from ``url``, or ``None``. Raises
        ``FileNotFoundError`` or ``ValueError`` if its bytes are gone or changed, and
        ``ValueError`` if it was redirected."""
        if url in self._read:
            return self._read[url]
        record = self._newest.get(url)
        if record is None:
            return None
        if record.final_url != record.request_url:
            raise ValueError(
                f"it was redirected to {record.final_url}, and a redirected response"
                " is never read"
            )
        stored = self.store.get(
            SEC_SOURCE_ID,
            record.sha256,
            rights_status=SEC_RIGHTS.rights_status,
            rights_basis=SEC_RIGHTS.rights_basis,
        )
        citable = CitableArtifact(
            source_id=SEC_SOURCE_ID,
            url=url,
            artifact=stored.ref,
            retrieved_at=record.retrieved_at,
            text=ArtifactText(stored.body, stored.ref.media_type),
        )
        self._read[url] = citable
        return citable


def cited_remedy(saved: SavedResponses, sha256: str) -> str:
    """The remedy for an artifact cited by its hash whose bytes are gone or changed:
    the refetch of the URL whose newest response it is. Once that URL is saved again
    with other bytes, a refetch saves its newest bytes, never the cited ones, and the
    result says so. Empty when no saved retrieval names the artifact."""
    named = [url for url in saved.urls() if sha256 in saved.hashes(url)]
    for url in named:
        if saved._newest[url].sha256 == sha256:
            return refetch_remedy(url)
    if not named:
        return ""
    return (
        f"{named[0]} was saved again with other bytes, so a refetch cannot restore"
        " a citation that names these bytes by hash"
    )
