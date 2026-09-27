"""Readers for the SEC data Stage 4 uses: pure functions of saved bytes (A §410).

- ``company_tickers.json`` is SEC's current ticker list. Its tickers only propose
  candidates; they never establish identity (A §268).
- A registrant's submissions JSON holds its conformed name, former names, current
  tickers, and filings, with each filing's 8-K items where the file has that column.
  Older filings sit in separate pages that ``filings.files`` names, each with the
  filing dates it covers.
- An N-PORT primary document holds a fund's holdings on its report date.

Each reader checks the shape it relies on and raises ``SecDataError`` on any other, so
an HTML block page or a changed format never reads as empty data (A §407). Every
record carries the JSON pointer of the value it came from, so evidence can cite it.
"""

import json
from dataclasses import dataclass
from datetime import date, datetime

from lxml import etree

from earnings_ingestion.sec.identifiers import pad_cik

FILING_COLUMNS = (
    "accessionNumber",
    "filingDate",
    "reportDate",
    "acceptanceDateTime",
    "form",
    "primaryDocument",
)


class SecDataError(ValueError):
    """SEC bytes that do not have the shape a reader relies on."""


@dataclass(frozen=True)
class TickerEntry:
    ticker: str
    cik: str
    title: str
    pointer: str
    """The entry's JSON pointer in ``company_tickers.json``, e.g. ``/12``."""


@dataclass(frozen=True)
class FormerName:
    name: str
    valid_from: str | None
    valid_to: str | None
    pointer: str


@dataclass(frozen=True)
class Filing:
    accession: str
    form: str
    filing_date: date
    report_date: date | None
    accepted_at: datetime | None
    primary_document: str
    columns: str
    """The JSON pointer of the column arrays holding this filing, e.g. ``/filings/recent``."""
    index: int
    items: tuple[str, ...] = ()
    """The 8-K items SEC lists for the filing, e.g. ``("2.02", "9.01")``; empty for
    other forms, and for files with no ``items`` column, such as Stage 4's synthetic
    ones."""

    def pointer(self, column: str) -> str:
        """The JSON pointer of one of this filing's values."""
        return f"{self.columns}/{json_pointer_token(column)}/{self.index}"


@dataclass(frozen=True)
class OlderPage:
    """An older filings page, which is fetched separately when needed."""

    name: str
    filing_from: date | None
    filing_to: date | None
    """The filing dates the page covers, when the entry states them."""
    pointer: str


@dataclass(frozen=True)
class Registrant:
    cik: str
    name: str
    tickers: tuple[str, ...]
    former_names: tuple[FormerName, ...]
    filings: tuple[Filing, ...]
    older_pages: tuple[OlderPage, ...]


@dataclass(frozen=True)
class Holding:
    name: str
    title: str | None
    asset_category: str | None
    position: int
    """1-based order in the filing."""


@dataclass(frozen=True)
class HoldingsReport:
    report_date: date
    holdings: tuple[Holding, ...]


def json_pointer_token(key: str) -> str:
    """RFC 6901 escaping of one reference token."""
    return key.replace("~", "~0").replace("/", "~1")


def load_json(body: bytes, what: str) -> object:
    try:
        return json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SecDataError(f"{what} is not JSON: {exc}") from exc


def read_company_tickers(body: bytes) -> tuple[TickerEntry, ...]:
    data = load_json(body, "company_tickers.json")
    if not isinstance(data, dict) or not data:
        raise SecDataError("company_tickers.json is not a non-empty object")
    entries = []
    for key, entry in data.items():
        if not isinstance(entry, dict) or not {"cik_str", "ticker", "title"} <= set(
            entry
        ):
            raise SecDataError(f"entry {key!r} lacks cik_str, ticker, or title")
        entries.append(
            TickerEntry(
                ticker=str(entry["ticker"]),
                cik=pad_cik(entry["cik_str"]),
                title=str(entry["title"]),
                pointer=f"/{json_pointer_token(key)}",
            )
        )
    return tuple(entries)


def _date(value: object, where: str) -> date | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise SecDataError(f"{where}: {value!r} is not a date") from exc


def _datetime(value: object, where: str) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise SecDataError(f"{where}: {value!r} is not a timestamp") from exc
    if parsed.tzinfo is None:
        raise SecDataError(f"{where}: {value!r} has no time zone")
    return parsed


def read_filing_columns(columns: object, pointer: str) -> tuple[Filing, ...]:
    """Filings from SEC's column layout: one array per field, one index per filing."""
    if not isinstance(columns, dict) or not set(FILING_COLUMNS) <= set(columns):
        raise SecDataError(f"{pointer} lacks the columns {list(FILING_COLUMNS)}")
    arrays = [columns[name] for name in FILING_COLUMNS]
    if (
        not all(isinstance(array, list) for array in arrays)
        or len({len(array) for array in arrays}) != 1
    ):
        raise SecDataError(f"{pointer}'s columns are not arrays of one length")
    items = columns.get("items", [""] * len(arrays[0]))
    if (
        not isinstance(items, list)
        or len(items) != len(arrays[0])
        or not all(isinstance(value, str) for value in items)
    ):
        raise SecDataError(f"{pointer}'s items are not text, one per filing")
    filings = []
    for index, row in enumerate(zip(*arrays, items, strict=True)):
        accession, filed, reported, accepted, form, document, listed = row
        where = f"{pointer} index {index}"
        filing_date = _date(filed, where)
        if filing_date is None:
            raise SecDataError(f"{where} has no filing date")
        filings.append(
            Filing(
                accession=str(accession),
                form=str(form),
                filing_date=filing_date,
                report_date=_date(reported, where),
                accepted_at=_datetime(accepted, where),
                primary_document=str(document),
                columns=pointer,
                index=index,
                items=tuple(item.strip() for item in listed.split(",") if item.strip()),
            )
        )
    return tuple(filings)


def _named(entry: object, where: str) -> dict:
    """``entry`` if it is an object whose ``name`` is text."""
    if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
        raise SecDataError(f"{where} is not an object with a text name")
    return entry


def _optional_text(value: object, where: str) -> str | None:
    if value is not None and not isinstance(value, str):
        raise SecDataError(f"{where} is not text")
    return value


def _older_page(entry: object, index: int) -> OlderPage:
    pointer = f"/filings/files/{index}"
    entry = _named(entry, pointer)
    return OlderPage(
        name=entry["name"],
        filing_from=_date(entry.get("filingFrom"), f"{pointer}/filingFrom"),
        filing_to=_date(entry.get("filingTo"), f"{pointer}/filingTo"),
        pointer=pointer,
    )


def _former_name(entry: object, index: int) -> FormerName:
    pointer = f"/formerNames/{index}"
    entry = _named(entry, pointer)
    return FormerName(
        name=entry["name"],
        valid_from=_optional_text(entry.get("from"), f"{pointer}/from"),
        valid_to=_optional_text(entry.get("to"), f"{pointer}/to"),
        pointer=pointer,
    )


def read_submissions(body: bytes) -> Registrant:
    data = load_json(body, "the submissions file")
    if not isinstance(data, dict) or not {"cik", "name", "tickers", "filings"} <= set(
        data
    ):
        raise SecDataError("the submissions file lacks cik, name, tickers, or filings")
    filings = data["filings"]
    if not isinstance(filings, dict) or "recent" not in filings:
        raise SecDataError("the submissions file has no filings.recent")
    tickers = data["tickers"]
    if not isinstance(tickers, list) or not all(isinstance(t, str) for t in tickers):
        raise SecDataError("tickers is not a list of text")
    former = data.get("formerNames") or []
    if not isinstance(former, list):
        raise SecDataError("formerNames is not a list")
    older = filings.get("files") or []
    if not isinstance(older, list):
        raise SecDataError("filings.files is not a list")
    return Registrant(
        cik=pad_cik(data["cik"]),
        name=str(data["name"]),
        tickers=tuple(tickers),
        former_names=tuple(
            _former_name(entry, index) for index, entry in enumerate(former)
        ),
        filings=read_filing_columns(filings["recent"], "/filings/recent"),
        older_pages=tuple(_older_page(page, index) for index, page in enumerate(older)),
    )


def read_submissions_page(body: bytes) -> tuple[Filing, ...]:
    """An older filings page: the same columns, at the top level."""
    return read_filing_columns(load_json(body, "the filings page"), "")


def raw_document_name(primary_document: str) -> str:
    """The filed file itself: EDGAR's ``primaryDocument`` for an XML form can name
    its rendered view, such as ``xslFormNPORT-P_X01/primary_doc.xml``."""
    return primary_document.rsplit("/", 1)[-1]


def _local(element: etree._Element) -> str:
    return etree.QName(element).localname


def _child_text(element: etree._Element, name: str) -> str | None:
    for child in element:
        if isinstance(child.tag, str) and _local(child) == name:
            text = (child.text or "").strip()
            return text or None
    return None


def read_nport_holdings(body: bytes) -> HoldingsReport:
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    try:
        root = etree.fromstring(body, parser=parser)
    except etree.XMLSyntaxError as exc:
        raise SecDataError(f"the N-PORT document is not XML: {exc}") from exc
    if _local(root) != "edgarSubmission":
        raise SecDataError(f"the root element is {_local(root)!r}, not edgarSubmission")
    report_dates = [
        element.text
        for element in root.iter()
        if isinstance(element.tag, str) and _local(element) == "repPdDate"
    ]
    if len(report_dates) != 1:
        raise SecDataError(f"expected one repPdDate, found {len(report_dates)}")
    report_date = _date((report_dates[0] or "").strip(), "repPdDate")
    if report_date is None:
        raise SecDataError("repPdDate is empty")
    holdings = []
    positions = (
        element
        for element in root.iter()
        if isinstance(element.tag, str) and _local(element) == "invstOrSec"
    )
    for position, element in enumerate(positions, start=1):
        name = _child_text(element, "name")
        if name is None:
            raise SecDataError(f"holding {position} has no name")
        holdings.append(
            Holding(
                name=name,
                title=_child_text(element, "title"),
                asset_category=_child_text(element, "assetCat"),
                position=position,
            )
        )
    if not holdings:
        raise SecDataError("the N-PORT document lists no holdings")
    return HoldingsReport(report_date=report_date, holdings=tuple(holdings))
