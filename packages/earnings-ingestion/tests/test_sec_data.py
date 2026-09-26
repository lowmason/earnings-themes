"""The SEC data readers: ticker list, submissions, and N-PORT holdings."""

import json
from datetime import UTC, date, datetime

import pytest
from earnings_ingestion.sec.data import (
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
    assert registrant.older_pages == ("CIK0009990001-submissions-001.json",)


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
