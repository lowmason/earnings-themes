"""The SEC data readers: ticker list, submissions, and N-PORT holdings."""

import json
from datetime import UTC, date, datetime

import pytest
from earnings_ingestion.sec.data import (
    OlderPage,
    SecDataError,
    raw_document_name,
    read_company_tickers,
    read_nport_holdings,
    read_submissions,
    read_submissions_page,
)


def submissions(**overrides) -> bytes:
    data = {
        "cik": "9990001",
        "name": "Acme Industrial Corp",
        "tickers": ["ACME"],
        "formerNames": [
            {
                "name": "ACME WIDGETS INC",
                "from": "2001-01-01T00:00:00.000Z",
                "to": "2025-03-01T00:00:00.000Z",
            }
        ],
        "filings": {
            "recent": {
                "accessionNumber": ["0009990001-25-000002", "0009990001-24-000001"],
                "filingDate": ["2025-02-01", "2024-08-01"],
                "reportDate": ["2024-12-31", ""],
                "acceptanceDateTime": [
                    "2025-02-01T16:05:00.000Z",
                    "2024-08-01T09:00:00.000Z",
                ],
                "form": ["10-K", "8-K"],
                "primaryDocument": ["acme-10k.htm", "acme-8k.htm"],
            },
            "files": [{"name": "CIK0009990001-submissions-001.json"}],
        },
    }
    return json.dumps(data | overrides).encode()


NPORT = b"""<?xml version="1.0" encoding="UTF-8"?>
<edgarSubmission xmlns="http://www.sec.gov/edgar/nport"
                 xmlns:com="http://www.sec.gov/edgar/common">
  <headerData><submissionType>NPORT-P</submissionType></headerData>
  <formData>
    <genInfo><repPdEnd>2024-10-31</repPdEnd><repPdDate>2024-07-31</repPdDate></genInfo>
    <invstOrSecs>
      <invstOrSec><name>Acme Industrial Corp</name><title>Acme Industrial Corp</title>
        <assetCat>EC</assetCat></invstOrSec>
      <invstOrSec><name>Borealis Air Inc/The</name><assetCat>EC</assetCat></invstOrSec>
    </invstOrSecs>
  </formData>
</edgarSubmission>
"""


def test_the_ticker_list_pads_ciks_and_cites_each_entry() -> None:
    body = json.dumps(
        {"0": {"cik_str": 9990001, "ticker": "ACME", "title": "Acme Industrial Corp"}}
    ).encode()
    (entry,) = read_company_tickers(body)
    assert (entry.ticker, entry.cik, entry.pointer) == ("ACME", "0009990001", "/0")


@pytest.mark.parametrize(
    "body",
    [
        b"<html>Undeclared Automated Tool</html>",
        b"{}",
        b'{"0": {"ticker": "ACME"}}',
    ],
    ids=["block-page", "empty", "no-cik"],
)
def test_a_ticker_list_of_another_shape_is_refused(body) -> None:
    with pytest.raises(SecDataError):
        read_company_tickers(body)


def test_submissions_give_name_former_names_tickers_and_filings() -> None:
    registrant = read_submissions(submissions())
    assert registrant.cik == "0009990001"
    assert registrant.name == "Acme Industrial Corp"
    assert registrant.tickers == ("ACME",)
    assert registrant.former_names[0].name == "ACME WIDGETS INC"
    assert registrant.former_names[0].pointer == "/formerNames/0"
    first, second = registrant.filings
    assert first.accepted_at == datetime(2025, 2, 1, 16, 5, tzinfo=UTC)
    assert (first.report_date, second.report_date) == (date(2024, 12, 31), None)
    assert second.pointer("form") == "/filings/recent/form/1"
    assert registrant.older_pages == (
        OlderPage(
            name="CIK0009990001-submissions-001.json",
            filing_from=None,
            filing_to=None,
            pointer="/filings/files/0",
        ),
    )
    assert (first.items, second.items) == ((), ())


def with_items(items: list) -> bytes:
    data = json.loads(submissions())
    data["filings"]["recent"]["items"] = items
    return json.dumps(data).encode()


def test_items_are_read_when_the_column_is_present() -> None:
    """Stage 5 reads each filing's items; Stage 4's files, which carry no items
    column, read as before (the Stage 5 spec, §Store, client, and readers)."""
    first, second = read_submissions(with_items(["", "2.02,9.01"])).filings
    assert (first.items, second.items) == ((), ("2.02", "9.01"))


@pytest.mark.parametrize("items", [["2.02"], ["", 202]], ids=["ragged", "not-text"])
def test_malformed_items_are_refused(items) -> None:
    with pytest.raises(SecDataError):
        read_submissions(with_items(items))


def test_an_older_page_records_the_dates_it_covers() -> None:
    body = pages(
        [
            {
                "name": "CIK0009990001-submissions-001.json",
                "filingCount": 2,
                "filingFrom": "2019-01-02",
                "filingTo": "2024-06-28",
            }
        ]
    )
    (page,) = read_submissions(body).older_pages
    assert (page.filing_from, page.filing_to) == (date(2019, 1, 2), date(2024, 6, 28))


def test_an_older_page_with_a_malformed_date_is_refused() -> None:
    body = pages([{"name": "p.json", "filingFrom": "2019-13-02"}])
    with pytest.raises(SecDataError, match="not a date"):
        read_submissions(body)


def pages(entries: list) -> bytes:
    """The submissions file with ``entries`` as its ``filings.files``."""
    data = json.loads(submissions())
    data["filings"]["files"] = entries
    return json.dumps(data).encode()


@pytest.mark.parametrize(
    "body",
    [
        submissions(formerNames=["ACME WIDGETS INC"]),
        submissions(formerNames=[{"from": "2001-01-01T00:00:00.000Z"}]),
        submissions(formerNames=[{"name": 7}]),
        submissions(tickers="ACME"),
        submissions(tickers=["ACME", 7]),
        pages(["CIK0009990001-submissions-001.json"]),
        pages([{"filingCount": 3}]),
        pages([{"name": 3}]),
    ],
    ids=[
        "former-name-not-an-object",
        "former-name-without-a-name",
        "former-name-not-text",
        "tickers-a-string",
        "ticker-not-text",
        "page-not-an-object",
        "page-without-a-name",
        "page-name-not-text",
    ],
)
def test_a_malformed_registrant_is_refused_as_sec_data(body) -> None:
    """Plan 6's deferred robustness fix: a changed shape raises SecDataError, never
    KeyError or TypeError, and a string of tickers is not read as characters."""
    with pytest.raises(SecDataError):
        read_submissions(body)


def test_ragged_filing_columns_are_refused() -> None:
    body = json.loads(submissions())
    body["filings"]["recent"]["form"] = ["10-K"]
    with pytest.raises(SecDataError, match="one length"):
        read_submissions(json.dumps(body).encode())


def test_an_older_page_has_the_columns_at_the_top_level() -> None:
    page = json.loads(submissions())["filings"]["recent"]
    filings = read_submissions_page(json.dumps(page).encode())
    assert [filing.form for filing in filings] == ["10-K", "8-K"]
    assert filings[0].pointer("form") == "/form/0"


def test_the_rendered_view_is_not_the_filed_document() -> None:
    assert raw_document_name("xslFormNPORT-P_X01/primary_doc.xml") == "primary_doc.xml"
    assert raw_document_name("primary_doc.xml") == "primary_doc.xml"


def test_nport_holdings_are_read_in_order_with_their_report_date() -> None:
    report = read_nport_holdings(NPORT)
    assert report.report_date == date(2024, 7, 31)
    assert [(h.name, h.asset_category, h.position) for h in report.holdings] == [
        ("Acme Industrial Corp", "EC", 1),
        ("Borealis Air Inc/The", "EC", 2),
    ]


@pytest.mark.parametrize(
    "body",
    [
        b"<html><body>Request Rate Threshold Exceeded</body></html>",
        NPORT.replace(b"<repPdDate>2024-07-31</repPdDate>", b""),
        NPORT.replace(b"<name>Acme Industrial Corp</name>", b""),
        b"not xml",
    ],
    ids=["html", "no-report-date", "unnamed-holding", "not-xml"],
)
def test_an_nport_document_of_another_shape_is_refused(body) -> None:
    with pytest.raises(SecDataError):
        read_nport_holdings(body)
