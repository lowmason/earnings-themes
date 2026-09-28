"""Synthetic SEC responses for Stage 5 (the Stage 5 spec, §The synthetic event layer).

The builders write submissions files, older pages, companyfacts files, index pages,
and 8-K primary documents in SEC's formats, as Stage 5's readers read them, for
invented registrants. Tests build their cases
with them, and the synthetic event layer writes its committed fixture through them.
Every name and word they write is invented; none is copied from a filing.

Each builder returns bytes that depend on its arguments alone, so a fixture written
through them regenerates byte for byte.
"""

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from html import escape
from pathlib import Path

from earnings_core import sha256_hex

from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.acceptance import Convention, accepted_instant
from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.identifiers import unpad_cik
from earnings_ingestion.sec.urls import (
    archive_url,
    companyfacts_url,
    filing_index_url,
    submissions_page_url,
    submissions_url,
)

JSON = "application/json"
HTML = "text/html"
ITEM_TITLES = {
    "2.02": "Results of Operations and Financial Condition",
    "5.02": "Departure of Directors or Certain Officers; Election of Directors",
    "7.01": "Regulation FD Disclosure",
    "8.01": "Other Events",
    "9.01": "Financial Statements and Exhibits",
}


@dataclass(frozen=True)
class SyntheticFiling:
    """One filing, as a submissions row and an index page describe it."""

    accession: str
    form: str
    filing_date: date
    accepted: str
    """The index page's Accepted value: Eastern wall time, ``YYYY-MM-DD HH:MM:SS``."""
    report_date: date | None = None
    items: tuple[str, ...] = ()
    primary_document: str = ""
    written: str | None = None
    """``acceptanceDateTime`` exactly as written; ``None`` writes it by the file's
    convention, and ``""`` leaves it empty."""


def sec_timestamp(accepted: str, convention: Convention) -> str:
    """``acceptanceDateTime`` as SEC writes it under ``convention``."""
    if convention is Convention.UTC:
        return accepted_instant(accepted).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return f"{accepted.replace(' ', 'T')}.000Z"


def _columns(filings: Sequence[SyntheticFiling], convention: Convention) -> dict:
    """SEC's column layout: one array per field, one index per filing."""
    return {
        "accessionNumber": [f.accession for f in filings],
        "filingDate": [f.filing_date.isoformat() for f in filings],
        "reportDate": [
            f.report_date.isoformat() if f.report_date else "" for f in filings
        ],
        "acceptanceDateTime": [
            sec_timestamp(f.accepted, convention) if f.written is None else f.written
            for f in filings
        ],
        "form": [f.form for f in filings],
        "items": [",".join(f.items) for f in filings],
        "primaryDocument": [f.primary_document for f in filings],
    }


def _json(data: object) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()


def older_page_entry(name: str, filings: Sequence[SyntheticFiling]) -> dict:
    """A submissions file's ``filings.files`` entry for an older page."""
    dates = sorted(filing.filing_date for filing in filings)
    return {
        "name": name,
        "filingCount": len(filings),
        "filingFrom": dates[0].isoformat(),
        "filingTo": dates[-1].isoformat(),
    }


def submissions_file(
    cik: str,
    name: str,
    filings: Sequence[SyntheticFiling],
    *,
    convention: Convention,
    older_pages: Sequence[Mapping[str, object]] = (),
    tickers: Sequence[str] = (),
) -> bytes:
    """A registrant's submissions JSON: its recent filings, newest first as SEC
    lists them, and the older pages ``filings.files`` names."""
    recent = sorted(filings, key=lambda f: (f.accepted, f.accession), reverse=True)
    return _json(
        {
            "cik": unpad_cik(cik),
            "name": name,
            "tickers": list(tickers),
            "formerNames": [],
            "filings": {
                "recent": _columns(recent, convention),
                "files": [dict(page) for page in older_pages],
            },
        }
    )


def filings_page(
    filings: Sequence[SyntheticFiling], *, convention: Convention
) -> bytes:
    """An older filings page: the same columns, at the top level."""
    ordered = sorted(filings, key=lambda f: (f.accepted, f.accession), reverse=True)
    return _json(_columns(ordered, convention))


def companyfacts_file(
    cik: str, name: str, facts: Sequence[tuple[str, int | None, str | None]]
) -> bytes:
    """Companyfacts JSON: one revenue fact per ``(accession, fy, fp)``, in order. Two
    facts of one accession may state different labels, and ``None`` leaves one out."""
    entries = [
        {"accn": accession, "fp": period, "fy": year, "val": 1000 + number}
        for number, (accession, year, period) in enumerate(facts)
    ]
    return _json(
        {
            "cik": int(unpad_cik(cik)),
            "entityName": name,
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "label": "Revenues",
                        "description": "Invented revenue.",
                        "units": {"USD": entries},
                    }
                }
            },
        }
    )


def _row(sequence: str, description: str, href: str, name: str, kind: str) -> str:
    return (
        f'<tr><td scope="row">{sequence}</td><td scope="row">{description}</td>'
        f'<td scope="row"><a href="{href}">{name}</a></td>'
        f'<td scope="row">{kind}</td><td scope="row">1000</td></tr>'
    )


def index_page(
    cik: str,
    filing: SyntheticFiling,
    exhibits: Sequence[tuple[str, str, str]] = (),
) -> bytes:
    """A filing's EDGAR index page, shaped as EDGAR writes them. ``exhibits`` are
    ``(description, file name, type)`` after the primary document, in order."""
    folder = (
        f"/Archives/edgar/data/{unpad_cik(cik)}/{filing.accession.replace('-', '')}"
    )
    documents = [(filing.form, filing.primary_document, filing.form), *exhibits]
    rows = [
        _row(
            str(number),
            description,
            f"/ix?doc={folder}/{name}" if number == 1 else f"{folder}/{name}",
            name,
            kind,
        )
        for number, (description, name, kind) in enumerate(documents, start=1)
    ]
    rows.append(
        _row(
            "&nbsp;",
            "Complete submission text file",
            f"{folder}/{filing.accession}.txt",
            f"{filing.accession}.txt",
            "&nbsp;",
        )
    )
    groups = [
        (
            '<div class="formGrouping"><div class="infoHead">Filing Date</div>'
            f'<div class="info">{filing.filing_date.isoformat()}</div>'
            '<div class="infoHead">Accepted</div>'
            f'<div class="info">{filing.accepted}</div>'
            '<div class="infoHead">Documents</div>'
            f'<div class="info">{len(documents)}</div></div>'
        )
    ]
    if filing.report_date is not None:
        groups.append(
            '<div class="formGrouping"><div class="infoHead">Period of Report</div>'
            f'<div class="info">{filing.report_date.isoformat()}</div></div>'
        )
    if filing.items:
        lines = "".join(
            f"Item {item}: {ITEM_TITLES[item]}<br />" for item in filing.items
        )
        groups.append(
            '<div class="formGrouping"><div class="infoHead">Items</div>'
            f'<div class="info">{lines}</div></div>'
        )
    head = (
        "<tr><th>Seq</th><th>Description</th><th>Document</th><th>Type</th>"
        "<th>Size</th></tr>"
    )
    return (
        "<!DOCTYPE html><html><head><title>EDGAR Filing Documents for "
        f"{filing.accession}</title></head><body>"
        '<div class="formDiv"><div id="formHeader"><div id="formName">'
        f"<strong>Form {filing.form}</strong> - Filing</div>"
        '<div id="secNum"><strong>SEC Accession No.</strong> '
        f"{filing.accession}</div></div>"
        f'<div class="formContent">{"".join(groups)}</div></div>'
        '<table class="tableFile" summary="Document Format Files">'
        f"{head}{''.join(rows)}</table></body></html>\n"
    ).encode()


def eight_k(
    registrant: str,
    items: Sequence[tuple[str, Sequence[str]]],
    *,
    cover: bool = False,
    signed: date | None = None,
) -> bytes:
    """An 8-K's primary document: the registrant, then each ``(item, paragraphs)`` as
    a heading and its paragraphs, then a signature dated ``signed``. ``cover`` also
    lists the items in a table on the cover page, as some registrants do, which gives
    each item a heading with nothing under it."""
    parts = ["<p>Form 8-K</p><p>Current Report</p>", f"<p>{escape(registrant)}</p>"]
    if cover:
        rows = "".join(
            f"<tr><td></td><td>Item {item}</td><td>{ITEM_TITLES[item]}</td></tr>"
            for item, _ in items
        )
        parts.append(f"<table>{rows}</table>")
    for item, paragraphs in items:
        parts.append(f"<p><b>Item {item} {ITEM_TITLES[item]}</b></p>")
        parts.extend(f"<p>{escape(paragraph)}</p>" for paragraph in paragraphs)
    parts.append(f"<p>Signature</p><p>{escape(registrant)}</p>")
    if signed is not None:
        parts.append(f"<p>Date: {signed:%B} {signed.day}, {signed.year}</p>")
    return (
        "<!DOCTYPE html><html><head><title>Form 8-K</title></head><body>"
        f"{''.join(parts)}</body></html>\n"
    ).encode()


def _written(day: date) -> str:
    return f"{day:%B} {day.day}, {day.year}"


def exhibit_page(page: str, registrant: str, period_end: date) -> bytes:
    """An invented EX-99 exhibit for the quarter ending ``period_end``:

    - ``release``: a headline and a paragraph that report the quarter's results,
      and a table of figures;
    - ``narrative``: the same without a table, like Stage 1's narrative-only class;
    - ``supplement``: supplemental tables under a heading, announcing nothing;
    - ``overview``: a pro forma overview, like V2's AMC case, announcing nothing;
    - ``image``: an image and no text, which walker-1 refuses.
    """
    name, ended = escape(registrant), _written(period_end)
    table = (
        "<table><tr><td>Net sales</td><td>1,000</td></tr>"
        "<tr><td>Net income</td><td>100</td></tr></table>"
    )
    parts = {
        "release": [
            f"<h1>{name} Reports Results for the Quarter Ended {ended}</h1>",
            (
                f"<p>{name} today reported net sales of $1,000 million for the"
                f" quarter ended {ended}.</p>"
            ),
            table,
        ],
        "narrative": [
            f"<h1>{name} Reports Results for the Quarter Ended {ended}</h1>",
            (
                f"<p>{name} today reported higher deliveries for the quarter ended"
                f" {ended}.</p>"
            ),
            "<p>The company will discuss the quarter on a call this morning.</p>",
        ],
        "supplement": [
            "<h1>Supplemental Financial Information</h1>",
            f"<p>Quarter ended {ended}</p>",
            table,
        ],
        "overview": [
            "<h1>Pro Forma Financial Overview</h1>",
            f"<p>Twelve months ended {ended}</p>",
            table,
        ],
        "image": ['<p><img src="release.png" alt=""></p>'],
    }[page]
    return (
        "<!DOCTYPE html><html><head><title>Exhibit 99</title></head><body>"
        f"{''.join(parts)}</body></html>\n"
    ).encode()


def save(
    store: ArtifactStore,
    url: str,
    body: bytes,
    media_type: str,
    retrieved_at: datetime,
) -> None:
    """Save ``body`` as a retrieval of ``url`` under the ``sec-edgar`` source."""
    retrieval = Retrieval(
        request_url=url,
        final_url=url,
        retrieved_at=retrieved_at,
        retrieval_method=RetrievalMethod.HTTP,
        http_status=200,
        media_type=media_type,
        content_type=media_type,
        byte_count=len(body),
        sha256=sha256_hex(body),
    )
    store.put(
        SEC_SOURCE_ID,
        body,
        retrieval,
        rights_status=SEC_RIGHTS.rights_status,
        rights_basis=SEC_RIGHTS.rights_basis,
    )


class SyntheticStore:
    """Synthetic responses saved into an artifact store, all at one retrieval time,
    each under the URL discovery would fetch it from."""

    def __init__(self, root: Path, repo: Path, retrieved_at: datetime) -> None:
        self.store = ArtifactStore(root, repo)
        self.retrieved_at = retrieved_at

    def put(self, url: str, body: bytes, media_type: str) -> None:
        save(self.store, url, body, media_type, self.retrieved_at)

    def submissions(
        self,
        cik: str,
        name: str,
        filings: Sequence[SyntheticFiling],
        *,
        convention: Convention,
        older_pages: Sequence[Mapping[str, object]] = (),
    ) -> None:
        body = submissions_file(
            cik, name, filings, convention=convention, older_pages=older_pages
        )
        self.put(submissions_url(cik), body, JSON)

    def older_page(
        self, name: str, filings: Sequence[SyntheticFiling], *, convention: Convention
    ) -> None:
        body = filings_page(filings, convention=convention)
        self.put(submissions_page_url(name), body, JSON)

    def index(
        self,
        cik: str,
        filing: SyntheticFiling,
        exhibits: Sequence[tuple[str, str, str]] = (),
    ) -> None:
        self.put(
            filing_index_url(cik, filing.accession),
            index_page(cik, filing, exhibits),
            HTML,
        )

    def companyfacts(
        self,
        cik: str,
        name: str,
        facts: Sequence[tuple[str, int | None, str | None]],
    ) -> None:
        self.put(companyfacts_url(cik), companyfacts_file(cik, name, facts), JSON)

    def document(
        self,
        cik: str,
        filing: SyntheticFiling,
        body: bytes,
        media_type: str = HTML,
    ) -> None:
        """Save ``body`` as the filing's primary document."""
        url = archive_url(cik, filing.accession, filing.primary_document)
        self.put(url, body, media_type)
