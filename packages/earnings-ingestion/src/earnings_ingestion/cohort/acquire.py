"""Acquire and cite cohort evidence: every network step of Stage 4 lives here.

- ``fetch_page`` saves a roster revision or index notice through the web client.
- ``register_saved`` saves a page a person saved in a browser, for a source whose
  robots.txt or access refuses automated fetching; it records that nothing was
  fetched (``saved_by_user``).
- ``fetch_sec`` saves, through the shared SEC client, SEC's ticker list, the
  submissions of every CIK a cited ticker proposes or an override names, and the
  fund's N-PORT filings over the window. Filed documents are fetched once; the
  ticker list and submissions are fetched fresh, and the build uses the latest.
- ``cite`` finds evidence in a saved artifact and returns its locator, with the cited
  text for a person's terminal; that text never goes into a committed file.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from earnings_core import ArtifactRef, sha256_hex

from earnings_ingestion.cohort.config import CohortConfig
from earnings_ingestion.cohort.locators import ArtifactText
from earnings_ingestion.cohort.records import EvidenceLocator, OverrideKind
from earnings_ingestion.cohort.register import Registers
from earnings_ingestion.fetch.client import Fetched
from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.data import (
    raw_document_name,
    read_company_tickers,
    read_submissions,
    read_submissions_page,
)
from earnings_ingestion.sec.urls import (
    COMPANY_TICKERS_URL,
    archive_url,
    submissions_page_url,
    submissions_url,
)

JSON = frozenset({"application/json"})
HTML = frozenset({"text/html"})
XML = frozenset({"application/xml", "text/xml"})


def _put(
    store: ArtifactStore,
    registers: Registers,
    source_id: str,
    body: bytes,
    retrieval: Retrieval,
) -> ArtifactRef:
    rights = registers.rights(source_id)
    return store.put(
        source_id,
        body,
        retrieval,
        rights_status=rights.rights_status,
        rights_basis=rights.rights_basis,
    )


def fetch_page(
    fetch: Callable[[str, frozenset[str]], Fetched],
    store: ArtifactStore,
    registers: Registers,
    source_id: str,
    url: str,
) -> ArtifactRef:
    """Fetch one HTML page of a registered source and save it."""
    registers.entry(source_id)
    fetched = fetch(url, HTML)
    return _put(store, registers, source_id, fetched.body, fetched.retrieval)


def register_saved(
    store: ArtifactStore,
    registers: Registers,
    source_id: str,
    body: bytes,
    *,
    url: str,
    media_type: str,
    saved_at: datetime,
) -> ArtifactRef:
    """Save a page a person saved in a browser from ``url`` at ``saved_at``."""
    registers.entry(source_id)
    retrieval = Retrieval(
        request_url=url,
        final_url=url,
        retrieved_at=saved_at,
        retrieval_method=RetrievalMethod.SAVED_BY_USER,
        http_status=None,
        media_type=media_type,
        content_type=media_type,
        byte_count=len(body),
        sha256=sha256_hex(body),
    )
    return _put(store, registers, source_id, body, retrieval)


@dataclass
class SecFetch:
    """What ``fetch_sec`` requested, and what it found already saved."""

    fetched: list[str]
    kept: list[str]


def fetch_sec(
    fetch: Callable[[str, frozenset[str]], Fetched],
    store: ArtifactStore,
    registers: Registers,
    config: CohortConfig,
) -> SecFetch:
    """Save every SEC record the build reads for ``config``."""
    result = SecFetch(fetched=[], kept=[])

    def get(source_id: str, url: str, types: frozenset[str]) -> bytes:
        fetched = fetch(url, types)
        _put(store, registers, source_id, fetched.body, fetched.retrieval)
        result.fetched.append(url)
        return fetched.body

    entries = read_company_tickers(get("sec-edgar", COMPANY_TICKERS_URL, JSON))
    evidence = config.evidence
    rows = [
        *(row for item in evidence.snapshots for row in item.members),
        *(row for item in evidence.changes for row in item.entries),
    ]
    cited = {row.ticker for row in rows}
    ciks = {entry.cik for entry in entries if entry.ticker in cited}
    ciks |= {
        o.cik for o in config.overrides.overrides if o.kind is OverrideKind.SET_ISSUER
    }
    for cik in sorted(ciks):
        get("sec-edgar", submissions_url(cik), JSON)

    universe = config.universe
    proxy = universe.etf_proxy
    if proxy is None:
        return result
    registrant = read_submissions(get("sec-edgar", submissions_url(proxy.cik), JSON))
    filings = list(registrant.filings)
    for page in registrant.older_pages:
        filings += read_submissions_page(
            get("sec-edgar", submissions_page_url(page), JSON)
        )
    rights = registers.rights(proxy.source_id)
    for filing in filings:
        if filing.form not in proxy.forms or filing.report_date is None:
            continue
        if (
            not universe.period_end_start
            <= filing.report_date
            <= universe.public_information_cutoff
        ):
            continue
        url = archive_url(
            proxy.cik, filing.accession, raw_document_name(filing.primary_document)
        )
        saved = store.latest(
            proxy.source_id,
            url,
            rights_status=rights.rights_status,
            rights_basis=rights.rights_basis,
        )
        if saved is not None:
            result.kept.append(url)
            continue
        get(proxy.source_id, url, XML)
    return result


def cite(
    store: ArtifactStore,
    registers: Registers,
    source_id: str,
    sha256: str,
    *,
    find: str | None = None,
    occurrence: int = 1,
    span: tuple[int, int] | None = None,
    pointer: str | None = None,
    line: bool = False,
) -> tuple[EvidenceLocator, str]:
    """A locator into a saved artifact, and the text it cites (for the terminal).
    With ``line``, the locator spans the whole line holding the found text."""
    if sum(option is not None for option in (find, span, pointer)) != 1:
        raise ValueError("give exactly one of find, span, or pointer")
    if line and find is None:
        raise ValueError("line needs find")
    rights = registers.rights(source_id)
    stored = store.get(
        source_id,
        sha256,
        rights_status=rights.rights_status,
        rights_basis=rights.rights_basis,
    )
    text = ArtifactText(stored.body, stored.ref.media_type)
    if find is not None:
        locator = (text.line if line else text.find)(find, occurrence)
    elif span is not None:
        locator = text.span(*span)
    else:
        locator = text.pointer(pointer)
    return locator, text.cited(locator)


def terms_digest(body: bytes, media_type: str) -> str:
    """The hash a register records for a terms page: its canonical text's, if HTML."""
    if media_type.partition(";")[0].strip().lower() == "text/html":
        return ArtifactText(body, media_type).canonical[1]
    return sha256_hex(body)
