"""``release-content/1`` (the Stage 5 spec, §Content confirmation): an exhibit is the
slot's release when its text states the slot's period, as ``release-id/1`` reads it,
and its opening announces results. Stage 1's eight committed releases and invented
texts pin the vocabulary; Stage 1's 168 saved exhibits are checked where saved."""

from datetime import date
from pathlib import Path

import pytest
from earnings_ingestion.canonical import CanonicalizationFailure, canonicalize
from earnings_ingestion.events.content import OPENING, confirm

REPO = Path(__file__).resolve().parents[3]
RELEASES = REPO / "tests" / "fixtures" / "releases"
DISCOVERY = REPO / "data" / "raw" / "discovery"

STAGE_1 = {
    "0000007332-09-000032_ex-99": (date(2009, 9, 30), 2009, "Q3"),
    "0000009389-10-000004_ex-99-1": (date(2009, 12, 31), 2009, "FY"),
    "0000010795-22-000014_ex-99-1": (date(2021, 12, 31), 2022, "Q1"),
    "0000037785-14-000003_ex-99-1": (date(2013, 12, 31), 2013, "FY"),
    "0000092380-07-000011_ex-99-1": (date(2007, 3, 31), 2007, "Q1"),
    "0000706863-16-000110_ex-99-1": (date(2016, 6, 30), 2016, "Q2"),
    "0000877860-13-000100_ex-99-1": (date(2013, 9, 30), 2013, "Q3"),
    "0000949699-08-000023_ex-99-1": (date(2008, 6, 30), 2008, "FY"),
}
"""Each committed release's period end and fiscal labels, from its filing."""

NOT_ANNOUNCED = {
    "0000015847-10-000006_ex-99",
    "0000068270-05-000104_ex-99",
    "0000700565-07-000011_ex-99",
    "0000897101-15-000604_ex-99-1",
    "0001065280-12-000007_ex-99-1",
    "0001104659-24-081453_ex-99-1",
    "0001172358-08-000017_ex-99-1",
    "0001367644-10-000005_ex-99-1",
    "0001377789-24-000036_ex-99-1",
    "0001493152-20-014749_ex-99",
    "0001538716-20-000102_ex-99-1",
    "0001572910-14-000003_ex-99-1",
}
"""Stage 1's saved exhibits whose opening announces no results: the six that are not
releases (AMC's pro forma overview, Donaldson's guidance, Dorchester's and Phillips 66
Partners' distributions, Aviat's delayed 10-K, and Oportun's business update), and six
releases worded otherwise."""


def html(*blocks: str) -> bytes:
    return f"<html><body>{''.join(blocks)}</body></html>".encode()


def canonical(raw: bytes, name: str = "0009990001-25-000012_ex991.htm"):
    result = canonicalize(raw, source_document_id=name, media_type="text/html")
    assert not isinstance(result, CanonicalizationFailure), result
    return result


@pytest.mark.parametrize("fixture", sorted(STAGE_1))
def test_stage_1_s_committed_releases_are_confirmed(fixture: str) -> None:
    period_end, year, period = STAGE_1[fixture]
    result = canonical((RELEASES / fixture / "source.html").read_bytes(), fixture)
    check = confirm(result, period_end, year, period)
    assert (check.period, check.announced, check.confirmed) == (True, True, True)
    assert check.detail is None


RELEASE = html(
    "<h1>Acme Industrial Corp Reports Third Quarter Fiscal 2025 Results</h1>",
    "<p>Acme Industrial Corp today reported net sales of $1.2 billion for the quarter"
    " ended February 28, 2025.</p>",
)


def test_a_release_states_its_period_by_date_or_by_labels() -> None:
    result = canonical(RELEASE)
    assert confirm(result, date(2025, 2, 28), None, None).confirmed
    assert confirm(result, date(2025, 3, 1), 2025, "Q3").confirmed
    wrong = confirm(result, date(2025, 3, 1), 2025, "Q2")
    assert (wrong.period, wrong.announced, wrong.confirmed) == (False, True, False)
    assert wrong.detail == "it states no period ended 2025-03-01, and no Q2 2025"


def test_labels_other_than_a_quarter_or_a_year_judge_nothing() -> None:
    result = canonical(
        html("<p>Acme reported results for the third quarter of fiscal 2025.</p>")
    )
    assert not confirm(result, date(2025, 2, 28), 2025, "H1").period
    assert confirm(result, date(2025, 2, 28), 2025, "Q3").period


def test_a_fourth_quarter_or_full_year_is_the_year_s_period() -> None:
    result = canonical(
        html("<p>Corvid announced its fourth quarter and full year 2025 results.</p>")
    )
    assert confirm(result, date(2025, 12, 31), 2025, "FY").confirmed


def test_an_overview_that_announces_nothing_is_not_confirmed() -> None:
    """V2's AMC case: a pro forma overview that states the period, and announces no
    results."""
    result = canonical(
        html(
            "<h1>Pro Forma Financial Overview</h1>",
            "<p>Twelve months ended June 30, 2025</p>",
            "<table><tr><td>Revenue</td><td>1,000</td></tr></table>",
        )
    )
    check = confirm(result, date(2025, 6, 30), None, None)
    assert (check.period, check.announced, check.confirmed) == (True, False, False)
    assert check.detail == "its opening announces no results"


def test_only_the_opening_is_read_for_the_announcement() -> None:
    filler = [f"<p>Line {n}.</p>" for n in range(OPENING)]
    late = canonical(
        html(
            *filler,
            "<p>Acme reported results for the quarter ended February 28, 2025.</p>",
        )
    )
    assert not confirm(late, date(2025, 2, 28), None, None).announced
    early = canonical(
        html(
            *filler[1:],
            "<p>Acme reported results for the quarter ended February 28, 2025.</p>",
        )
    )
    assert confirm(early, date(2025, 2, 28), None, None).announced


@pytest.mark.parametrize(
    ("sentence", "announced"),
    [
        ("Dynamo Motors posted record revenue in its third quarter.", True),
        ("Eastfield Bank announces second quarter 2025 net income.", True),
        ("Borealis Air delivered EPS of $1.10.", True),
        ("Acme reported. Results follow in the tables.", False),
        ("Acme announced a quarterly cash distribution.", False),
        ("Acme updated its guidance for fiscal 2025 sales.", False),
    ],
)
def test_the_announcement_s_vocabulary(sentence: str, announced: bool) -> None:
    check = confirm(
        canonical(html(f"<p>{sentence}</p>")), date(2025, 9, 30), None, None
    )
    assert check.announced is announced


def test_stage_1_s_saved_exhibits_are_judged_as_before() -> None:
    """Of Stage 1's 168 saved exhibits, exactly these twelve announce no results in
    their opening. Every one states some period, so the announcement decides."""
    if not DISCOVERY.is_dir():
        pytest.skip("data/raw/discovery is not saved here")
    silent = set()
    pages = sorted(p for p in DISCOVERY.iterdir() if (p / "source.html").is_file())
    for page in pages:
        result = canonical((page / "source.html").read_bytes(), page.name)
        if not confirm(result, date(1900, 1, 1), None, None).announced:
            silent.add(page.name)
    assert len(pages) == 168
    assert silent == NOT_ANNOUNCED
