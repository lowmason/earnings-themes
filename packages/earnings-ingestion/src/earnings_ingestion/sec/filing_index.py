"""A filing's EDGAR index page: form, acceptance, items, and documents (Stage 5).

``<accession>-index.htm`` is EDGAR's own record of a filing. Its header states the
form, the filing date, and the time EDGAR accepted the filing, in Eastern wall time
(the Stage 5 spec, Finding 1); an 8-K's lists the items it reports. Its Document
Format Files table lists each document filed, with its type, so an 8-K's EX-99
exhibits are found there. The table's reading is ported from Stage 1's
``parse_filing_index`` (``expirements/parser-fidelity/discover.py``).

``read_filing_index`` is a pure function of the saved bytes. It checks the shape it
relies on and raises ``SecDataError`` on any other, so a block page never reads as a
filing with no items or no exhibits (A §407).
"""

import re
from dataclasses import dataclass
from datetime import date, time
from urllib.parse import parse_qs, urlparse

import lxml.html
from lxml import etree

from earnings_ingestion.sec.data import SecDataError

ACCESSION = re.compile(r"\b\d{10}-\d{2}-\d{6}\b")
ACCEPTED = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
ITEM = re.compile(r"Item (\d+\.\d+)\b")


@dataclass(frozen=True)
class IndexDocument:
    sequence: int | None
    """The filing's own order; ``None`` for the complete submission text file."""
    description: str
    filename: str
    doc_type: str


@dataclass(frozen=True)
class FilingIndex:
    accession: str
    form: str
    filing_date: date
    accepted: str
    """EDGAR's acceptance time as the page writes it, ``YYYY-MM-DD HH:MM:SS`` in
    Eastern wall time; ``events.acceptance`` reads it as an instant."""
    period_of_report: date | None
    items: tuple[str, ...]
    documents: tuple[IndexDocument, ...]

    def exhibits_99(self) -> tuple[IndexDocument, ...]:
        """The documents typed ``EX-99*``: ``EX-99``, ``EX-99.1``, ``EX-99.01``, and
        any other numbering, as Stage 1 matched them."""
        return tuple(
            document
            for document in self.documents
            if document.doc_type.upper().startswith("EX-99")
        )


def _text(element: etree._Element) -> str:
    return element.text_content().strip()


def _root(body: bytes) -> etree._Element:
    try:
        root = lxml.html.document_fromstring(
            body, parser=lxml.html.HTMLParser(encoding="utf-8")
        )
    except (etree.LxmlError, ValueError) as exc:
        raise SecDataError(f"the index page is not HTML: {exc}") from exc
    if root is None:
        raise SecDataError("the index page is empty")
    return root


def _one(root: etree._Element, path: str, what: str) -> etree._Element:
    found = root.xpath(path)
    if len(found) != 1:
        raise SecDataError(f"the index page has {len(found)} {what}, not one")
    return found[0]


def _info(root: etree._Element) -> dict[str, etree._Element]:
    """The header's label and value pairs, e.g. ``Accepted`` to its value."""
    pairs = {}
    for head in root.xpath('//div[@class="formGrouping"]/div[@class="infoHead"]'):
        value = head.getnext()
        if value is None or value.get("class") != "info":
            raise SecDataError(f"the index page's {_text(head)!r} has no value")
        if _text(head) in pairs:
            raise SecDataError(f"the index page states {_text(head)!r} twice")
        pairs[_text(head)] = value
    return pairs


def _date(value: str, what: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SecDataError(f"the index page's {what} {value!r} is not a date") from exc


def _accepted(value: str) -> str:
    """The page's Accepted text, once it is a real date and time of day."""
    try:
        if ACCEPTED.fullmatch(value):
            date.fromisoformat(value[:10])
            time.fromisoformat(value[11:])
            return value
    except ValueError:
        pass
    raise SecDataError(f"the index page's Accepted {value!r} is not a date and time")


def _items(value: etree._Element) -> tuple[str, ...]:
    """``Item 2.02: Results of ...`` lines, which ``<br/>`` separates."""
    items = []
    for line in (piece.strip() for piece in value.itertext()):
        if not line:
            continue
        match = ITEM.match(line)
        if match is None:
            raise SecDataError(f"the index page's item {line!r} has no number")
        items.append(match.group(1))
    return tuple(items)


def _filename_from_href(href: str) -> str:
    parsed = urlparse(href)
    target = parse_qs(parsed.query).get("doc", [parsed.path])[0]
    return target.rsplit("/", 1)[-1]


def _documents(root: etree._Element) -> tuple[IndexDocument, ...]:
    table = _one(
        root,
        '//table[@summary="Document Format Files"]',
        "Document Format Files tables",
    )
    documents = []
    for row in table.iter("tr"):
        cells = row.findall("td")
        if len(cells) < 4:
            continue
        sequence = _text(cells[0])
        if sequence and not (sequence.isascii() and sequence.isdigit()):
            raise SecDataError(
                f"the index page's sequence {sequence!r} is not a number"
            )
        link = cells[2].find(".//a")
        filename = _filename_from_href(link.get("href", "")) if link is not None else ""
        filename = filename or next(iter(_text(cells[2]).split()), "")
        if not filename:
            raise SecDataError("the index page lists a document with no file name")
        documents.append(
            IndexDocument(
                sequence=int(sequence) if sequence else None,
                description=_text(cells[1]),
                filename=filename,
                doc_type=_text(cells[3]),
            )
        )
    if not documents:
        raise SecDataError("the index page's Document Format Files table is empty")
    return tuple(documents)


def read_filing_index(body: bytes) -> FilingIndex:
    root = _root(body)
    form = _text(_one(root, '//div[@id="formName"]/strong', "form names"))
    if not form.startswith("Form "):
        raise SecDataError(f"the index page's form name {form!r} is not 'Form ...'")
    accessions = ACCESSION.findall(_text(_one(root, '//div[@id="secNum"]', "numbers")))
    if len(accessions) != 1:
        raise SecDataError("the index page states no single accession number")
    info = _info(root)
    for label in ("Filing Date", "Accepted"):
        if label not in info:
            raise SecDataError(f"the index page states no {label}")
    period = info.get("Period of Report")
    return FilingIndex(
        accession=accessions[0],
        form=form.removeprefix("Form ").strip(),
        filing_date=_date(_text(info["Filing Date"]), "Filing Date"),
        accepted=_accepted(_text(info["Accepted"])),
        period_of_report=(
            _date(_text(period), "Period of Report") if period is not None else None
        ),
        items=_items(info["Items"]) if "Items" in info else (),
        documents=_documents(root),
    )
