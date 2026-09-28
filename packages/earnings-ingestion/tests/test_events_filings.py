"""An issuer's saved filings, placed on the Eastern calendar (plan 7, P7-8)."""

from dataclasses import replace
from datetime import UTC, date, datetime

import pytest
from earnings_ingestion.events.acceptance import Convention
from earnings_ingestion.events.filings import IssuerFilings, issuer_filings
from earnings_ingestion.events.records import EventFindingKind, SkippedPage
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.synthetic import (
    HTML,
    JSON,
    SyntheticFiling,
    SyntheticStore,
    index_page,
    older_page_entry,
    save,
    submissions_file,
)
from earnings_ingestion.sec.data import read_submissions
from earnings_ingestion.sec.filing_index import read_filing_index
from earnings_ingestion.sec.urls import (
    filing_index_url,
    submissions_page_url,
    submissions_url,
)

CIK = "0009990001"
ISSUER = "cik-0009990001"
START, CUTOFF = date(2024, 7, 1), date(2026, 9, 22)
RETRIEVED = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
EXHIBIT = (("PRESS RELEASE", "acme-ex991.htm", "EX-99.1"),)


def periodic(number: int, period: date, accepted: str, **fields) -> SyntheticFiling:
    return SyntheticFiling(
        accession=f"0009990001-{accepted[2:4]}-{number:06d}",
        form="10-Q",
        filing_date=date.fromisoformat(accepted[:10]),
        accepted=accepted,
        report_date=period,
        primary_document=f"acme-{period:%Y%m%d}.htm",
        **fields,
    )


def release(number: int, accepted: str, **fields) -> SyntheticFiling:
    values = {
        "accession": f"0009990001-{accepted[2:4]}-{number:06d}",
        "form": "8-K",
        "filing_date": date.fromisoformat(accepted[:10]),
        "accepted": accepted,
        "report_date": date.fromisoformat(accepted[:10]),
        "items": ("2.02", "9.01"),
        "primary_document": f"acme-8k-{number}.htm",
    }
    return SyntheticFiling(**(values | fields))


class Saved(SyntheticStore):
    """One issuer's synthetic responses, and its filings as the build reads them."""

    def submissions(self, filings, convention=Convention.UTC, pages=()) -> None:
        super().submissions(
            CIK,
            "Acme Industrial Corp",
            filings,
            convention=convention,
            older_pages=pages,
        )

    def page(self, name, filings, convention=Convention.UTC) -> None:
        self.older_page(name, filings, convention=convention)

    def index(self, filing, exhibits=EXHIBIT) -> None:
        super().index(CIK, filing, exhibits)

    def read(self) -> IssuerFilings:
        saved = SavedResponses(self.store)
        return issuer_filings(saved, CIK, ISSUER, start=START, cutoff=CUTOFF)


@pytest.fixture
def saved(tmp_path) -> Saved:
    return Saved(tmp_path / "data" / "raw" / "events", tmp_path, RETRIEVED)


def test_the_synthetic_formats_read_back() -> None:
    filing = release(29, "2024-10-24 16:05:12")
    registrant = read_submissions(
        submissions_file(
            CIK, "Acme Industrial Corp", [filing], convention=Convention.UTC
        )
    )
    (row,) = registrant.filings
    assert (row.accession, row.items) == (filing.accession, ("2.02", "9.01"))
    assert row.accepted_at == datetime(2024, 10, 24, 20, 5, 12, tzinfo=UTC)
    index = read_filing_index(index_page(CIK, filing, EXHIBIT))
    assert (index.accession, index.form, index.accepted) == (
        filing.accession,
        "8-K",
        "2024-10-24 16:05:12",
    )
    assert index.items == ("2.02", "9.01")
    assert [d.filename for d in index.exhibits_99()] == ["acme-ex991.htm"]


def test_older_pages_in_range_are_read_and_the_rest_skipped_by_their_dates(
    saved,
) -> None:
    old = [periodic(3, date(2024, 3, 31), "2024-05-02 16:30:00")]
    recent = [periodic(40, date(2024, 9, 30), "2024-11-04 16:30:00")]
    undated = [periodic(9, date(2023, 12, 31), "2024-02-20 16:30:00")]
    pages = [
        older_page_entry("CIK0009990001-submissions-001.json", recent),
        older_page_entry("CIK0009990001-submissions-002.json", old),
        {"name": "CIK0009990001-submissions-003.json", "filingCount": 1},
    ]
    saved.submissions([], pages=pages)
    saved.page("CIK0009990001-submissions-001.json", recent)
    saved.page("CIK0009990001-submissions-003.json", undated)
    read = saved.read()
    assert [file.artifact.url for file in read.files] == [
        submissions_url(CIK),
        submissions_page_url("CIK0009990001-submissions-001.json"),
        submissions_page_url("CIK0009990001-submissions-003.json"),
    ]
    assert read.skipped == (
        SkippedPage(
            url=submissions_page_url("CIK0009990001-submissions-002.json"),
            filing_from=date(2024, 5, 2),
            filing_to=date(2024, 5, 2),
        ),
    )
    assert [p.filing.report_date for p in read.periodic] == [
        date(2023, 12, 31),
        date(2024, 9, 30),
    ]
    assert read.problems == ()


def test_a_missing_response_is_a_problem(saved) -> None:
    assert saved.read().problems == (
        f"nothing saved from {submissions_url(CIK)}: run events discover",
    )
    recent = [periodic(40, date(2024, 9, 30), "2024-11-04 16:30:00")]
    pages = [older_page_entry("CIK0009990001-submissions-001.json", recent)]
    saved.submissions([], pages=pages)
    url = submissions_page_url("CIK0009990001-submissions-001.json")
    assert saved.read().problems == (f"nothing saved from {url}: run events discover",)


def test_an_index_page_places_a_release_and_cross_checks_its_row(saved) -> None:
    filing = release(29, "2024-10-24 16:05:12")
    saved.submissions([filing])
    saved.index(filing)
    read = saved.read()
    (placed,) = read.releases
    assert placed.instant == datetime(2024, 10, 24, 20, 5, 12, tzinfo=UTC)
    assert placed.accepted_on == date(2024, 10, 24)
    assert read.files[0].survey.convention is Convention.UTC
    assert (read.findings, read.problems) == ((), ())


def test_a_row_in_neither_convention_is_a_blocking_mismatch(saved) -> None:
    filing = release(29, "2024-10-24 16:05:12", written="2024-10-24T17:05:12.000Z")
    saved.submissions([filing])
    saved.index(filing)
    (finding,) = saved.read().findings
    assert finding.finding_id == f"acceptance_time_mismatch:{filing.accession}"
    assert finding.kind is EventFindingKind.ACCEPTANCE_TIME_MISMATCH
    assert finding.holds_freeze
    assert finding.detail == (
        f"{submissions_url(CIK)} gives 2024-10-24T17:05:12+00:00 for"
        f" {filing.accession}, whose index page says 2024-10-24 16:05:12 Eastern"
    )


LATE = "2026-09-23T01:30:00.000Z"
"""Under true UTC, 21:30 Eastern on the cutoff; as Eastern digits, the next day."""


@pytest.mark.parametrize(
    ("convention", "visible"),
    [(Convention.UTC, True), (Convention.EASTERN_DIGITS, False)],
)
def test_a_periodic_report_follows_its_file_s_convention(
    saved, convention, visible
) -> None:
    report = periodic(80, date(2026, 6, 30), "2026-09-22 21:30:00", written=LATE)
    anchor = release(70, "2026-07-23 16:05:00")
    saved.submissions([report, anchor], convention=convention)
    saved.index(anchor)
    read = saved.read()
    assert read.files[0].survey.convention is convention
    assert bool(read.periodic) is visible
    assert read.findings == ()


def test_a_side_of_the_cutoff_that_turns_on_an_unknown_convention_blocks(
    saved,
) -> None:
    report = periodic(80, date(2026, 6, 30), "2026-09-22 21:30:00", written=LATE)
    saved.submissions([report])
    read = saved.read()
    (finding,) = read.findings
    assert finding.finding_id == f"acceptance_time_unknown:{report.accession}"
    assert finding.holds_freeze
    assert finding.detail == (
        f"10-Q {report.accession}, filed 2026-09-22: acceptanceDateTime"
        " 2026-09-23T01:30:00+00:00 falls on 2026-09-22 or 2026-09-23, either side of"
        " the cutoff 2026-09-22, and its file establishes no convention"
    )
    assert read.periodic == ()
    saved.index(report)
    read = saved.read()
    assert (read.findings, len(read.periodic)) == ((), 1)


def test_readings_on_one_side_of_the_cutoff_need_no_convention(saved) -> None:
    before = periodic(80, date(2026, 6, 30), "2026-08-05 16:00:00")
    after = periodic(90, date(2026, 9, 30), "2026-10-05 16:00:00")
    saved.submissions([before, after])
    read = saved.read()
    assert [p.filing.accession for p in read.periodic] == [before.accession]
    assert read.findings == ()


def test_a_release_either_convention_places_in_range_needs_its_index_page(
    saved,
) -> None:
    edge = release(10, "2024-06-30 22:30:00")
    early = release(5, "2024-05-01 16:05:00")
    other = release(12, "2024-08-01 16:05:00", items=("7.01", "9.01"))
    saved.submissions([edge, early, other])
    url = filing_index_url(CIK, edge.accession)
    read = saved.read()
    assert read.problems == (f"nothing saved from {url}: run events discover",)
    saved.index(edge)
    read = saved.read()
    assert (read.problems, read.releases) == ((), ())


def test_a_missing_value_is_unknown_unless_filed_before_the_range(saved) -> None:
    report = periodic(80, date(2026, 6, 30), "2026-08-05 16:00:00", written="")
    unplaced = release(20, "2025-01-28 07:00:00", written="")
    early = release(5, "2024-05-01 16:05:00", written="")
    saved.submissions([report, unplaced, early])
    read = saved.read()
    assert [f.finding_id for f in read.findings] == [
        f"acceptance_time_unknown:{unplaced.accession}",
        f"acceptance_time_unknown:{report.accession}",
    ]
    assert read.findings[1].detail == (
        f"10-Q {report.accession}, filed 2026-08-05: no acceptanceDateTime"
    )


def test_an_index_page_of_another_filing_is_a_problem(saved) -> None:
    filing = release(29, "2024-10-24 16:05:12")
    other = replace(filing, accession="0009990001-24-000030")
    saved.submissions([filing])
    body = index_page(CIK, other, EXHIBIT)
    save(saved.store, filing_index_url(CIK, filing.accession), body, HTML, RETRIEVED)
    url = filing_index_url(CIK, filing.accession)
    assert saved.read().problems == (
        f"{url} is the index page of 0009990001-24-000030",
    )


def test_a_submissions_file_of_another_registrant_is_a_problem(saved) -> None:
    """Each submissions file states its CIK, as each index page states its
    accession: one saved under this issuer's URL but naming another is not read."""
    filing = release(29, "2024-10-24 16:05:12")
    body = submissions_file(
        "0009990002", "Borealis Corp", [filing], convention=Convention.UTC
    )
    save(saved.store, submissions_url(CIK), body, JSON, RETRIEVED)
    found = saved.read()
    assert (found.registrant, found.releases, found.periodic) == (None, (), ())
    assert found.problems == (
        f"{submissions_url(CIK)} is the submissions file of CIK 0009990002",
    )


def test_an_older_page_of_another_count_is_a_problem(saved) -> None:
    """An older page states no CIK, so the count its entry in the CIK-checked
    submissions file states binds it: a page holding another number is not read."""
    recent = [periodic(40, date(2024, 9, 30), "2024-11-04 16:30:00")]
    name = "CIK0009990001-submissions-001.json"
    saved.submissions([], pages=[older_page_entry(name, recent)])
    saved.page(name, [*recent, periodic(41, date(2024, 12, 31), "2025-02-04 16:30:00")])
    found = saved.read()
    assert found.periodic == ()
    assert found.problems == (
        (
            f"{submissions_page_url(name)}: {name}'s filing count, 2, is not the 1"
            " its entry at /filings/files/0 states"
        ),
    )


def test_a_filing_listed_in_two_files_is_a_problem(saved) -> None:
    """Two copies of one 8-K would make two candidates of one filing, and so a false
    several_release_filings. The repeat is refused, never deduplicated, naming each
    copy's pointer."""
    filing = release(29, "2024-10-24 16:05:12")
    name = "CIK0009990001-submissions-001.json"
    saved.submissions([filing], pages=[older_page_entry(name, [filing])])
    saved.page(name, [filing])
    saved.index(filing)
    assert saved.read().problems == (
        (
            f"{filing.accession} is listed 2 times:"
            f" at /filings/recent/accessionNumber/0 in {submissions_url(CIK)},"
            f" at /accessionNumber/0 in {submissions_page_url(name)}"
        ),
    )


def test_a_filing_listed_twice_in_one_block_is_a_problem(saved) -> None:
    report = periodic(40, date(2024, 9, 30), "2024-11-04 16:30:00")
    saved.submissions([report, report])
    assert saved.read().problems == (
        (
            f"{report.accession} is listed 2 times:"
            f" at /filings/recent/accessionNumber/0 in {submissions_url(CIK)},"
            f" at /filings/recent/accessionNumber/1 in {submissions_url(CIK)}"
        ),
    )


def test_the_newest_retrieval_of_each_url_is_read(saved) -> None:
    first = [release(29, "2024-10-24 16:05:12")]
    saved.submissions(first)
    later = RETRIEVED.replace(day=29)
    body = submissions_file(CIK, "Acme Industrial Corp", [], convention=Convention.UTC)
    save(saved.store, submissions_url(CIK), body, JSON, later)
    responses = SavedResponses(saved.store)
    assert len(responses) == 1
    assert responses.get(submissions_url(CIK)).retrieved_at == later
    assert responses.get("https://www.sec.gov/nothing") is None
