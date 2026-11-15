"""An issuer's saved filings, placed on the Eastern calendar (plan 7, P7-8)."""

from dataclasses import replace
from datetime import UTC, date, datetime

import pytest
from earnings_ingestion.events.acceptance import Convention
from earnings_ingestion.events.filings import IssuerFilings, issuer_filings
from earnings_ingestion.events.records import EventFindingKind, SkippedPage
from earnings_ingestion.events.saved import SavedResponses, refetch_remedy
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


def test_an_older_page_that_starts_after_the_cutoff_is_read(saved) -> None:
    """A filing accepted after 17:30 takes the next business day's filing date. So a
    page whose ``filingFrom`` is the day after the cutoff can hold a filing accepted
    on the cutoff's evening. The padded skip reads the page, and the filing stays
    visible. The recent block starts the day after the page ends."""
    late = release(96, "2026-09-22 18:00:00", filing_date=date(2026, 9, 23))
    newest = release(97, "2026-09-24 16:05:00", items=("8.01",))
    name = "CIK0009990001-submissions-001.json"
    entry = older_page_entry(name, [late])
    assert (entry["filingFrom"], entry["filingTo"]) == ("2026-09-23", "2026-09-23")
    saved.submissions([newest], pages=[entry])
    saved.page(name, [late])
    read = saved.read()
    assert submissions_page_url(name) not in [page.url for page in read.skipped]
    saved.index(late)
    read = saved.read()
    assert [p.filing.accession for p in read.releases] == [late.accession]
    assert (read.findings, read.problems) == ((), ())


def test_the_padded_skip_reads_a_page_ending_seven_days_before_the_start(
    saved,
) -> None:
    edge = release(31, "2024-06-24 16:05:00", items=("8.01",))
    past = release(30, "2024-06-23 16:05:00", items=("8.01",))
    read_name = "CIK0009990001-submissions-001.json"
    skip_name = "CIK0009990001-submissions-002.json"
    pages = [older_page_entry(read_name, [edge]), older_page_entry(skip_name, [past])]
    saved.submissions([], pages=pages)
    saved.page(read_name, [edge])
    read = saved.read()
    assert [file.artifact.url for file in read.files] == [
        submissions_url(CIK),
        submissions_page_url(read_name),
    ]
    assert read.skipped == (
        SkippedPage(
            url=submissions_page_url(skip_name),
            filing_from=date(2024, 6, 23),
            filing_to=date(2024, 6, 23),
        ),
    )
    assert read.problems == ()


def test_the_padded_skip_reads_a_page_starting_seven_days_after_the_cutoff(
    saved,
) -> None:
    """A page is skipped only when its ``filingFrom`` is more than seven days after
    the cutoff. The skipped page still bounds the page below it, whose dates end
    before the skipped page's ``filingFrom``."""
    past = release(98, "2026-09-30 07:00:00", items=("8.01",))
    edge = release(97, "2026-09-29 07:00:00", items=("8.01",))
    skip_name = "CIK0009990001-submissions-001.json"
    read_name = "CIK0009990001-submissions-002.json"
    pages = [older_page_entry(skip_name, [past]), older_page_entry(read_name, [edge])]
    saved.submissions([], pages=pages)
    saved.page(read_name, [edge])
    read = saved.read()
    assert [file.artifact.url for file in read.files] == [
        submissions_url(CIK),
        submissions_page_url(read_name),
    ]
    assert read.skipped == (
        SkippedPage(
            url=submissions_page_url(skip_name),
            filing_from=date(2026, 9, 30),
            filing_to=date(2026, 9, 30),
        ),
    )
    assert read.problems == ()


def test_a_page_that_straddles_the_padded_start_is_read(saved) -> None:
    """The page's ``filingTo``, not its ``filingFrom``, decides the skip at the
    window's start. A page that begins before the padded start and ends after it is
    read, and its in-range release is placed."""
    old = release(20, "2024-05-20 16:05:00", items=("8.01",))
    inside = release(21, "2024-07-15 16:05:00")
    recent = release(30, "2024-08-01 16:05:00", items=("8.01",))
    name = "CIK0009990001-submissions-001.json"
    saved.submissions([recent], pages=[older_page_entry(name, [old, inside])])
    saved.page(name, [old, inside])
    saved.index(inside)
    read = saved.read()
    assert read.skipped == ()
    assert [p.filing.accession for p in read.releases] == [inside.accession]
    assert read.problems == ()


def test_a_page_that_straddles_the_padded_cutoff_is_read(saved) -> None:
    """The page's ``filingFrom``, not its ``filingTo``, decides the skip at the
    cutoff. A page that begins the day after the cutoff and ends more than seven days
    after it is read, and the release accepted on the cutoff's evening is placed."""
    late = release(96, "2026-09-22 18:00:00", filing_date=date(2026, 9, 23))
    after = release(98, "2026-10-09 16:05:00", items=("8.01",))
    recent = release(99, "2026-10-20 16:05:00", items=("8.01",))
    name = "CIK0009990001-submissions-001.json"
    saved.submissions([recent], pages=[older_page_entry(name, [late, after])])
    saved.page(name, [late, after])
    saved.index(late)
    read = saved.read()
    assert read.skipped == ()
    assert [p.filing.accession for p in read.releases] == [late.accession]
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
    """Under reading (a) (plan 26, D2), a row with no value has nothing to
    cross-check: once each unknown filing's index page is saved, the page places it,
    and nothing is found."""
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
    saved.index(report)
    saved.index(unplaced)
    read = saved.read()
    assert read.findings == ()
    assert report.accession in [p.filing.accession for p in read.periodic]
    assert unplaced.accession in [p.filing.accession for p in read.releases]


def test_an_old_periodic_report_with_no_value_raises_nothing(saved, tmp_path) -> None:
    """No slot or guard reads a report older than the issuer's latest one before the
    window, so its missing value holds nothing, and the reports read are the same as
    without it."""
    old = periodic(60, date(2023, 12, 31), "2024-02-20 16:30:00", written="")
    latest = periodic(70, date(2024, 3, 31), "2024-05-02 16:30:00")
    inside = periodic(90, date(2024, 9, 30), "2024-11-04 16:30:00")
    saved.submissions([old, latest, inside])
    read = saved.read()
    assert read.findings == ()
    without = Saved(tmp_path / "data" / "raw" / "without", tmp_path, RETRIEVED)
    without.submissions([latest, inside])
    assert [p.filing.accession for p in read.periodic] == [
        p.filing.accession for p in without.read().periodic
    ]


def test_the_latest_report_before_the_window_with_no_value_still_blocks(
    saved,
) -> None:
    """The slots' guards pair the latest report before the window with the first
    in-window report, so its missing value still blocks."""
    older = periodic(60, date(2023, 12, 31), "2024-02-20 16:30:00")
    latest = periodic(70, date(2024, 3, 31), "2024-05-02 16:30:00", written="")
    inside = periodic(90, date(2024, 9, 30), "2024-11-04 16:30:00")
    saved.submissions([older, latest, inside])
    (finding,) = saved.read().findings
    assert finding.finding_id == f"acceptance_time_unknown:{latest.accession}"
    assert finding.kind is EventFindingKind.ACCEPTANCE_TIME_UNKNOWN


def test_an_older_report_raises_nothing_when_the_latest_has_no_value_either(
    saved,
) -> None:
    """The latest report before the window bounds the rest whether or not its own
    side of the cutoff is known: it blocks, and the older report does not."""
    older = periodic(60, date(2023, 12, 31), "2024-02-20 16:30:00", written="")
    latest = periodic(70, date(2024, 3, 31), "2024-05-02 16:30:00", written="")
    inside = periodic(90, date(2024, 9, 30), "2024-11-04 16:30:00")
    saved.submissions([older, latest, inside])
    (finding,) = saved.read().findings
    assert finding.finding_id == f"acceptance_time_unknown:{latest.accession}"


def test_a_report_accepted_after_the_cutoff_does_not_bound_the_older_ones(
    saved,
) -> None:
    """The slots' guards read visible reports only. When the latest report before the
    window was accepted after the cutoff, they read the one before it, so that
    report's missing value still blocks."""
    older = periodic(60, date(2023, 12, 31), "2024-02-20 16:30:00", written="")
    late = periodic(70, date(2024, 3, 31), "2026-09-25 16:30:00")
    inside = periodic(90, date(2024, 9, 30), "2024-11-04 16:30:00")
    saved.submissions([older, late, inside])
    saved.index(late)
    read = saved.read()
    assert [p.filing.accession for p in read.periodic] == [inside.accession]
    (finding,) = read.findings
    assert finding.finding_id == f"acceptance_time_unknown:{older.accession}"


def test_a_report_dated_on_the_window_s_start_is_inside_the_window(saved) -> None:
    """A report dated on the window's start is in the window, so the latest report
    before the window is the one before it, whose missing value still blocks."""
    latest = periodic(70, date(2024, 3, 31), "2024-05-02 16:30:00", written="")
    first = periodic(90, date(2024, 7, 1), "2024-08-05 16:30:00")
    saved.submissions([latest, first])
    (finding,) = saved.read().findings
    assert finding.finding_id == f"acceptance_time_unknown:{latest.accession}"


def test_a_visible_report_older_than_the_latest_before_the_window_is_kept(
    saved,
) -> None:
    """Only a report whose side of the cutoff is unknown is passed over below the
    latest report before the window: a visible one is placed as before."""
    older = periodic(60, date(2023, 12, 31), "2024-02-20 16:30:00")
    latest = periodic(70, date(2024, 3, 31), "2024-05-02 16:30:00")
    inside = periodic(90, date(2024, 9, 30), "2024-11-04 16:30:00")
    saved.submissions([older, latest, inside])
    read = saved.read()
    assert [p.filing.accession for p in read.periodic] == [
        older.accession,
        latest.accession,
        inside.accession,
    ]
    assert read.findings == ()


def test_the_latest_report_before_the_window_is_the_issuer_s_not_its_file_s(
    saved,
) -> None:
    """An older page that states no range is read. The report it holds is older than
    the latest report before the window, which the submissions file holds, so its
    missing value holds nothing."""
    old = periodic(60, date(2023, 12, 31), "2024-02-20 16:30:00", written="")
    latest = periodic(70, date(2024, 3, 31), "2024-05-02 16:30:00")
    inside = periodic(90, date(2024, 9, 30), "2024-11-04 16:30:00")
    name = "CIK0009990001-submissions-001.json"
    saved.submissions([latest, inside], pages=[{"name": name, "filingCount": 1}])
    saved.page(name, [old])
    read = saved.read()
    assert [file.artifact.url for file in read.files] == [
        submissions_url(CIK),
        submissions_page_url(name),
    ]
    assert (read.findings, read.problems) == ((), ())


def test_a_no_value_release_past_the_cutoff_margin_raises_nothing(saved) -> None:
    """A filing accepted after 17:30 takes the next business day's filing date, so a
    release with no value blocks only when filed by seven days after the cutoff."""
    past = release(95, "2026-09-30 07:00:00", written="", filing_date=date(2026, 9, 30))
    margin = release(
        94, "2026-09-29 07:00:00", written="", filing_date=date(2026, 9, 29)
    )
    saved.submissions([past, margin])
    (finding,) = saved.read().findings
    assert finding.finding_id == f"acceptance_time_unknown:{margin.accession}"


def test_a_no_value_release_filed_on_the_window_s_start_is_unknown(saved) -> None:
    """The window's start is inside the 8-K trigger's range, and the day before it
    is not."""
    first = release(30, "2024-07-01 07:00:00", written="")
    before = release(25, "2024-06-30 07:00:00", written="")
    saved.submissions([first, before])
    (finding,) = saved.read().findings
    assert finding.finding_id == f"acceptance_time_unknown:{first.accession}"


def test_an_index_page_of_another_filing_is_a_problem(saved) -> None:
    filing = release(29, "2024-10-24 16:05:12")
    other = replace(filing, accession="0009990001-24-000030")
    saved.submissions([filing])
    body = index_page(CIK, other, EXHIBIT)
    save(saved.store, filing_index_url(CIK, filing.accession), body, HTML, RETRIEVED)
    url = filing_index_url(CIK, filing.accession)
    assert saved.read().problems == (
        f"{url} is the index page of 0009990001-24-000030; {refetch_remedy(url)}",
    )


def test_an_index_page_of_another_form_is_a_problem(saved) -> None:
    """The index page's form must be the submissions row's: a page for an 8-K/A
    listed as an 8-K would make it a candidate the rule may choose (PR #6's review,
    F12)."""
    filing = release(29, "2024-10-24 16:05:12")
    saved.submissions([filing])
    body = index_page(CIK, replace(filing, form="8-K/A"), EXHIBIT)
    url = filing_index_url(CIK, filing.accession)
    save(saved.store, url, body, HTML, RETRIEVED)
    read = saved.read()
    assert read.problems == (
        f"{url}: its form is 8-K/A, but its row's is 8-K; {refetch_remedy(url)}",
    )
    assert read.releases == ()


@pytest.mark.parametrize("named", ["acme-ex991.htm", ""])
def test_a_row_whose_primary_document_the_index_does_not_type_as_its_form(
    saved, named
) -> None:
    """The row's primary document must be listed in the index, typed as the form: a
    row naming the EX-99 file, or none, would have discovery fetch an exhibit before
    the freeze (EV2) (PR #6's review, F12)."""
    filing = release(29, "2024-10-24 16:05:12")
    saved.submissions([replace(filing, primary_document=named)])
    saved.index(filing)
    read = saved.read()
    url = filing_index_url(CIK, filing.accession)
    assert read.problems == (
        (
            f"{url}: it lists no {named or '(none)'} typed 8-K, its row's primary"
            f" document; {refetch_remedy(url)}"
        ),
    )
    assert read.releases == ()


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
        (
            f"{submissions_url(CIK)} is the submissions file of CIK 0009990002;"
            f" {refetch_remedy(submissions_url(CIK))}"
        ),
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
            " its entry at /filings/files/0 states;"
            f" {refetch_remedy(submissions_page_url(name))}"
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
    remedy = refetch_remedy(
        submissions_url(CIK), "the submissions file with its older pages"
    )
    assert saved.read().problems == (
        (
            f"{filing.accession} is listed 2 times:"
            f" at /filings/recent/accessionNumber/0 in {submissions_url(CIK)},"
            f" at /accessionNumber/0 in {submissions_page_url(name)}; {remedy}"
        ),
    )


def test_a_filing_listed_twice_in_one_block_is_a_problem(saved) -> None:
    report = periodic(40, date(2024, 9, 30), "2024-11-04 16:30:00")
    saved.submissions([report, report])
    remedy = refetch_remedy(
        submissions_url(CIK), "the submissions file with its older pages"
    )
    assert saved.read().problems == (
        (
            f"{report.accession} is listed 2 times:"
            f" at /filings/recent/accessionNumber/0 in {submissions_url(CIK)},"
            f" at /filings/recent/accessionNumber/1 in {submissions_url(CIK)};"
            f" {remedy}"
        ),
    )


NEWER = "CIK0009990001-submissions-001.json"
OLDER = "CIK0009990001-submissions-002.json"


def test_an_older_page_with_shifted_dates_is_refused(saved, tmp_path) -> None:
    """The count binds an older page to its entry, and its dates bind it to its
    place. A page with the right count that holds a filing date on or after the next
    newer page's ``filingFrom``, or the recent block's earliest filing date, is one
    that SEC cut again."""
    remedy = refetch_remedy(
        submissions_url(CIK), "the submissions file with its older pages"
    )
    first = periodic(50, date(2024, 12, 31), "2025-02-04 16:30:00")
    second = periodic(51, date(2025, 3, 31), "2025-05-01 16:30:00")
    early = periodic(40, date(2024, 6, 30), "2024-08-05 16:30:00")
    late = periodic(41, date(2024, 9, 30), "2024-11-04 16:30:00")
    recent = periodic(60, date(2025, 6, 30), "2025-08-05 16:30:00")
    pages = [
        older_page_entry(NEWER, [first, second]),
        older_page_entry(OLDER, [early, late]),
    ]
    saved.submissions([recent], pages=pages)
    saved.page(NEWER, [first, second])
    saved.page(OLDER, [replace(early, filing_date=first.filing_date), late])
    read = saved.read()
    assert read.problems == (
        (
            f"{submissions_page_url(OLDER)} lists a filing dated 2025-02-04, not"
            " before 2025-02-04, the next newer page's filingFrom at"
            f" /filings/files/0/filingFrom in {submissions_url(CIK)}; {remedy}"
        ),
    )
    assert read.unusable == (submissions_url(CIK),)

    newest = Saved(tmp_path / "data" / "raw" / "newest", tmp_path, RETRIEVED)
    later = periodic(61, date(2025, 9, 30), "2025-11-04 16:30:00")
    newest.submissions([recent, later], pages=[older_page_entry(NEWER, [first])])
    newest.page(NEWER, [replace(first, filing_date=recent.filing_date)])
    read = newest.read()
    assert read.problems == (
        (
            f"{submissions_page_url(NEWER)} lists a filing dated 2025-08-05, not"
            " before 2025-08-05, the earliest filing date at /filings/recent in"
            f" {submissions_url(CIK)}; {remedy}"
        ),
    )
    assert read.unusable == (submissions_url(CIK),)


def test_a_skipped_newer_page_still_bounds_the_page_below_it(saved) -> None:
    """A page skipped for starting more than seven days after the cutoff is still the
    next newer page of the page below it."""
    past = release(98, "2026-09-30 07:00:00", items=("8.01",))
    edge = release(97, "2026-09-29 07:00:00", items=("8.01",))
    pages = [older_page_entry(NEWER, [past]), older_page_entry(OLDER, [edge])]
    saved.submissions([], pages=pages)
    saved.page(OLDER, [replace(edge, filing_date=past.filing_date)])
    remedy = refetch_remedy(
        submissions_url(CIK), "the submissions file with its older pages"
    )
    assert saved.read().problems == (
        (
            f"{submissions_page_url(OLDER)} lists a filing dated 2026-09-30, not"
            " before 2026-09-30, the next newer page's filingFrom at"
            f" /filings/files/0/filingFrom in {submissions_url(CIK)}; {remedy}"
        ),
    )


def test_older_pages_whose_dates_end_the_day_before_their_bounds_are_read(
    saved,
) -> None:
    """Each bound is strict, so a page whose latest filing date is the day before its
    bound is read. The pages are ordered by their ``filingFrom``, whatever order the
    submissions file lists them in."""
    early = release(40, "2025-02-03 16:05:00", items=("8.01",))
    first = release(50, "2025-02-04 16:05:00", items=("8.01",))
    last = release(51, "2025-04-30 16:05:00", items=("8.01",))
    recent = release(60, "2025-05-01 16:05:00", items=("8.01",))
    pages = [
        older_page_entry(OLDER, [early]),
        older_page_entry(NEWER, [first, last]),
    ]
    saved.submissions([recent], pages=pages)
    saved.page(OLDER, [early])
    saved.page(NEWER, [first, last])
    read = saved.read()
    assert [file.artifact.url for file in read.files] == [
        submissions_url(CIK),
        submissions_page_url(OLDER),
        submissions_page_url(NEWER),
    ]
    assert read.problems == ()


def test_an_older_page_s_dates_need_not_match_its_entry_s_range(saved) -> None:
    """Only the bound binds a page's dates (plan 26, owner default 5). The page's
    last filing, on the Friday before a long weekend, is two days before its
    ``filingTo``, and its first is a day after its ``filingFrom``."""
    first = release(50, "2025-02-04 16:05:00", items=("8.01",))
    last = release(51, "2025-02-14 16:05:00", items=("8.01",))
    recent = release(60, "2025-02-18 16:05:00", items=("8.01",))
    entry = older_page_entry(NEWER, [first, last]) | {
        "filingFrom": "2025-02-03",
        "filingTo": "2025-02-16",
    }
    saved.submissions([recent], pages=[entry])
    saved.page(NEWER, [first, last])
    read = saved.read()
    assert [file.artifact.url for file in read.files] == [
        submissions_url(CIK),
        submissions_page_url(NEWER),
    ]
    assert read.problems == ()


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
