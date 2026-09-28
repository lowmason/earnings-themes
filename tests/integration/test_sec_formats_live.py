"""SEC's live formats still match what the readers rely on; run with ``-m live``.

It needs EDGAR_IDENTITY, set outside Git, and sends at most eight requests through
the shared SEC client. It saves nothing: ``earnings-pipeline cohort fetch-sec`` saves
what a build reads. Run it with ``-rP`` to see what it read, including the fund's
name, which must be the SPDR Dow Jones Industrial Average ETF Trust before any
curated file names its CIK. It never runs by default.
"""

import os

import pytest
from earnings_ingestion.sec.client import open_sec_client
from earnings_ingestion.sec.data import (
    raw_document_name,
    read_company_tickers,
    read_nport_holdings,
    read_submissions,
    read_submissions_page,
)
from earnings_ingestion.sec.urls import (
    COMPANY_TICKERS_URL,
    archive_url,
    submissions_page_url,
    submissions_url,
)

pytestmark = pytest.mark.live
JSON = frozenset({"application/json"})
XML = frozenset({"application/xml", "text/xml"})
NPORT = frozenset({"NPORT-P", "NPORT-P/A"})
MAX_REQUESTS = 8

FUND_CIK = "0001041130"
"""The fund's CIK, a lead from planning that this check confirms by the fund's name."""
FUND_NAME = "Dow Jones Industrial Average"
COMPANY = ("AAPL", "0000320193", "Apple")
"""A ticker, its CIK, and a name the ticker list and submissions must agree on."""
HOLDINGS = range(25, 36)
"""The equity holdings a fund tracking the 30-stock average should report."""


def test_sec_formats_match_the_readers() -> None:
    if not os.environ.get("EDGAR_IDENTITY"):
        pytest.skip("set EDGAR_IDENTITY outside Git to run this check")
    ticker, cik, name = COMPANY
    with open_sec_client(max_requests=MAX_REQUESTS) as client:
        entries = read_company_tickers(client.fetch(COMPANY_TICKERS_URL, JSON).body)
        company = read_submissions(client.fetch(submissions_url(cik), JSON).body)
        fund = read_submissions(client.fetch(submissions_url(FUND_CIK), JSON).body)
        older = [
            filing
            for page in fund.older_pages[:1]
            for filing in read_submissions_page(
                client.fetch(submissions_page_url(page.name), JSON).body
            )
        ]
        reports = [f for f in fund.filings if f.form in NPORT]
        assert reports, "the fund's recent filings hold no N-PORT report"
        latest = max(reports, key=lambda f: (f.filing_date, f.accession))
        document = raw_document_name(latest.primary_document)
        holdings = read_nport_holdings(
            client.fetch(archive_url(FUND_CIK, latest.accession, document), XML).body
        )
        requests = client.throttle.count
    equities = [h for h in holdings.holdings if h.asset_category in (None, "EC")]
    print(f"requests: {requests}")
    print(f"ticker list: {len(entries)} entries")
    print(f"{ticker}: {company.cik} {company.name}; tickers {list(company.tickers)}")
    print(f"fund: {fund.cik} {fund.name}")
    print(
        f"fund former names: {[(n.name, n.valid_from, n.valid_to) for n in fund.former_names]}"
    )
    print(
        f"fund recent filings: {len(fund.filings)}, from"
        f" {min(f.filing_date for f in fund.filings)}; older pages:"
        f" {[page.name for page in fund.older_pages]}; first older page: {len(older)} filings"
    )
    print(
        f"latest N-PORT: {latest.accession} {latest.form} filed {latest.filing_date},"
        f" accepted {latest.accepted_at}, primaryDocument {latest.primary_document}"
    )
    print(
        f"its report date {holdings.report_date}: {len(holdings.holdings)} holdings,"
        f" {len(equities)} equity; categories"
        f" {sorted({str(h.asset_category) for h in holdings.holdings})}"
    )
    assert [e.cik for e in entries if e.ticker == ticker] == [cik]
    assert company.cik == cik and ticker in company.tickers
    assert name.casefold() in company.name.casefold()
    assert fund.cik == FUND_CIK
    assert FUND_NAME.casefold() in fund.name.casefold(), (
        f"CIK {FUND_CIK} is {fund.name!r}"
    )
    assert holdings.report_date == latest.report_date
    assert len(equities) in HOLDINGS
    assert requests <= MAX_REQUESTS
