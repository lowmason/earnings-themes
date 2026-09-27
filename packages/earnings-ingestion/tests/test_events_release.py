"""release-id/1: which candidate 8-K first published a slot's results (the Stage 5
spec, §Candidates and ``release-id/1``; plan 7, P7-7).

Every document here is invented. Each is shaped like one of the two-filing quarters
of the spec's Finding 4, never worded like one: a cover page that lists the items, a
section with no later heading, a preliminary release, a recast, a transaction's
effect on a quarter, and an 8-K with no Item 2.02 heading.
"""

from dataclasses import replace
from datetime import UTC, date, datetime

import pytest
from earnings_ingestion.cohort.locators import ArtifactText
from earnings_ingestion.events.acceptance import Convention
from earnings_ingestion.events.filings import issuer_filings
from earnings_ingestion.events.records import EventReason, IdentificationMethod
from earnings_ingestion.events.release import (
    RELEASE_POLICY,
    FiscalPeriod,
    Identification,
    identify,
    read_text,
)
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.slots import issuer_slots
from earnings_ingestion.events.synthetic import (
    HTML,
    SyntheticFiling,
    SyntheticStore,
    eight_k,
    index_page,
)
from earnings_ingestion.sec.companyfacts import read_companyfacts
from earnings_ingestion.sec.urls import archive_url, companyfacts_url, filing_index_url

CIK = "0009990001"
ISSUER = "cik-0009990001"
NAME = "Acme Industrial Corp"
START, STOP, CUTOFF = date(2024, 7, 1), date(2026, 7, 1), date(2026, 9, 22)
RETRIEVED = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
P = date(2024, 9, 30)
EXHIBIT = (("EARNINGS RELEASE", "ex991.htm", "EX-99.1"),)
NINE_01 = ("9.01", ["Exhibit 99.1 is furnished with this report."])


def text_of(*items, cover: bool = False) -> str:
    """The walker-1 text of an invented 8-K."""
    body = eight_k(NAME, items, cover=cover, signed=date(2024, 10, 24))
    return ArtifactText(body, HTML).canonical[0]


def reading_of(*paragraphs: str):
    return read_text(text_of(("2.02", paragraphs), NINE_01))


def test_the_policy_is_named() -> None:
    assert RELEASE_POLICY == "release-id/1"


def test_item_text_runs_from_each_item_2_02_heading_to_the_next_heading() -> None:
    """A cover page that lists the items gives Item 2.02 a heading with nothing under
    it; the sections are read together."""
    text = text_of(
        ("2.02", ["Acme Industrial Corp posted its third quarter of 2024 figures."]),
        ("8.01", ["Acme Industrial Corp moved its head office."]),
        cover=True,
    )
    reading = read_text(text)
    cover, body = (text[start:end] for start, end in reading.sections)
    assert cover.startswith("Item 2.02\t")
    assert "\n" not in cover
    assert body.startswith("Item 2.02 Results of Operations and Financial Condition")
    assert "head office" not in body
    assert reading.periods == (FiscalPeriod(2024, "Q3"),)


def test_a_section_with_no_later_heading_runs_to_the_end_of_the_text() -> None:
    """A guidance update's section runs through the signature, whose date is read as
    no period."""
    text = text_of(
        (
            "2.02",
            [
                "Acme Industrial Corp revised its outlook for the year.",
                "The revised range appears in the table below.",
            ],
        )
    )
    reading = read_text(text)
    ((start, end),) = reading.sections
    assert end == len(text.rstrip())
    assert "October 24, 2024" in text[start:end]
    assert reading.dates == ()


def test_a_document_with_no_item_2_02_heading_states_nothing() -> None:
    reading = read_text(
        text_of(("5.02", ["The board elected Dana Reyes a director."]), NINE_01)
    )
    assert reading.sections == ()
    assert reading.unread == "it has no Item 2.02 heading"
    assert (reading.dates, reading.periods, reading.preliminary) == ((), (), False)


@pytest.mark.parametrize(
    ("phrase", "dates"),
    [
        ("for the quarter ended September 30, 2024.", (date(2024, 9, 30),)),
        ("for the period ending Sept. 30, 2024.", (date(2024, 9, 30),)),
        ("for the fiscal year ended May 31, 2026.", (date(2026, 5, 31),)),
        ("for the quarter ended Dec. 31, 2024.", (date(2024, 12, 31),)),
        ("on October 24, 2024, for its latest quarter.", ()),
        ("for the quarter ended February 30, 2025.", ()),
        ("for the quarter ended September 30 2024.", ()),
    ],
    ids=[
        "ended",
        "ending-abbreviated",
        "may",
        "dec",
        "announced",
        "no-day",
        "no-comma",
    ],
)
def test_a_date_is_stated_after_ended_or_ending(phrase, dates) -> None:
    """An announcement date states no period (P7-7)."""
    assert reading_of(f"Acme Industrial Corp reported {phrase}").dates == dates


@pytest.mark.parametrize(
    ("phrase", "periods"),
    [
        ("its third quarter of 2024 results", {"Q3 2024"}),
        ("third-quarter 2024 earnings", {"Q3 2024"}),
        ("results for the second fiscal quarter of 2025", {"Q2 2025"}),
        ("the first quarter of fiscal 2026", {"Q1 2026"}),
        ("its fiscal 2025 second quarter", {"Q2 2025"}),
        ("its fiscal year 2025 first quarter", {"Q1 2025"}),
        ("Q3 2024 figures", {"Q3 2024"}),
        ("Q2 fiscal 2025 figures", {"Q2 2025"}),
        ("its 3Q 2024 figures", {"Q3 2024"}),
        ("fiscal 2025 figures", {"FY 2025"}),
        ("fiscal year 2025 figures", {"FY 2025"}),
        ("full year 2024 figures", {"FY 2024"}),
        ("full-year 2024 figures", {"FY 2024"}),
        ("fourth quarter and full year 2025 figures", {"FY 2025"}),
        (
            "the third quarter of 2024 against the third quarter of 2023",
            {"Q3 2024", "Q3 2023"},
        ),
        ("figures for the quarter and year", set()),
    ],
)
def test_fiscal_periods_are_read_quarters_before_years(phrase, periods) -> None:
    reading = reading_of(f"Acme Industrial Corp shared {phrase}.")
    assert {str(period) for period in reading.periods} == periods


@pytest.mark.parametrize(
    ("phrase", "preliminary"),
    [
        ("preliminary figures for the quarter", True),
        ("Preliminary figures for the quarter", True),
        ("its expected results for the quarter", True),
        ("its expected quarterly results", True),
        ("its expected third-quarter operating results", True),
        ("its expected strong and steady results", False),
        ("that the sale is expected to result in a gain", False),
        ("unexpected results for the quarter", False),
        ("results that were as expected", False),
    ],
)
def test_preliminary_results_are_read(phrase, preliminary) -> None:
    reading = reading_of(f"Acme Industrial Corp described {phrase}.")
    assert reading.preliminary is preliminary


def report(period: date, form: str, accepted: str) -> SyntheticFiling:
    return SyntheticFiling(
        accession=f"0009990001-{accepted[2:4]}-{period:%m%d}00",
        form=form,
        filing_date=date.fromisoformat(accepted[:10]),
        accepted=accepted,
        report_date=period,
        primary_document=f"acme-{period:%Y%m%d}.htm",
    )


REPORTS = [
    report(date(2024, 6, 30), "10-Q", "2024-08-01 16:30:00"),
    report(date(2024, 9, 30), "10-Q", "2024-11-01 16:30:00"),
    report(date(2024, 12, 31), "10-K", "2025-02-20 16:30:00"),
]
"""Acme's reports around the slot P = 2024-09-30, whose P' is 2024-12-31."""


class Issuer(SyntheticStore):
    """Acme's saved responses around one slot, and release-id/1's reading of it."""

    def __init__(self, root, repo) -> None:
        super().__init__(root, repo, RETRIEVED)
        self.filings = list(REPORTS)

    def release(
        self,
        number: int,
        accepted: str,
        *items,
        form: str = "8-K",
        exhibits=EXHIBIT,
        listed=("2.02", "9.01"),
        indexed=None,
    ) -> SyntheticFiling:
        """An 8-K that SEC lists with ``listed``, whose index page gives ``indexed``
        (by default ``listed``), and whose document holds ``items``; with no
        ``items``, its document is not saved."""
        filing = SyntheticFiling(
            accession=f"0009990001-{accepted[2:4]}-{number:06d}",
            form=form,
            filing_date=date.fromisoformat(accepted[:10]),
            accepted=accepted,
            report_date=date.fromisoformat(accepted[:10]),
            items=listed,
            primary_document=f"acme-8k-{number}.htm",
        )
        self.filings.append(filing)
        shown = filing if indexed is None else replace(filing, items=indexed)
        self.put(
            filing_index_url(CIK, filing.accession),
            index_page(CIK, shown, exhibits),
            HTML,
        )
        if items:
            body = eight_k(NAME, [*items, NINE_01], signed=filing.filing_date)
            self.document(CIK, filing, body)
        return filing

    def identify(
        self, labels=(2024, "Q3"), labelled=REPORTS[1]
    ) -> dict[date, Identification]:
        """Each slot's identification, by period end; the ``labelled`` report, by
        default P's, has ``labels``."""
        self.submissions(CIK, NAME, self.filings, convention=Convention.UTC)
        facts = [] if labels is None else [(labelled.accession, *labels)]
        self.companyfacts(CIK, NAME, facts)
        saved = SavedResponses(self.store)
        filings = issuer_filings(saved, CIK, ISSUER, start=START, cutoff=CUTOFF)
        body = saved.get(companyfacts_url(CIK)).text.body
        slots, _ = issuer_slots(
            filings, read_companyfacts(body), ISSUER, start=START, stop=STOP
        )
        return {
            slot.period_end: identify(slot, filings.releases, saved, cutoff=CUTOFF)
            for slot in slots
        }


@pytest.fixture
def acme(tmp_path) -> Issuer:
    return Issuer(tmp_path / "data" / "raw" / "events", tmp_path)


def accessions(candidates) -> list[str]:
    return [candidate.placed.filing.accession for candidate in candidates]


def test_the_preliminary_filing_is_dropped_and_the_actual_release_chosen(
    acme,
) -> None:
    early = acme.release(
        31,
        "2024-10-09 07:30:00",
        (
            "2.02",
            ["Acme Industrial Corp gave preliminary third quarter of 2024 sales."],
        ),
    )
    actual = acme.release(
        40,
        "2024-10-24 16:05:00",
        ("2.02", ["Acme Industrial Corp published its third quarter of 2024 results."]),
    )
    found = acme.identify()[P]
    assert accessions(found.candidates) == [early.accession, actual.accession]
    assert found.candidates[0].dropped == "it calls its results preliminary"
    assert found.release.placed.filing.accession == actual.accession
    assert (found.method, found.reason) == (IdentificationMethod.STATED_PERIOD, None)
    assert found.problems == ()


def test_a_recast_that_states_other_periods_is_dropped(acme) -> None:
    actual = acme.release(
        40,
        "2024-10-24 16:05:00",
        ("2.02", ["Acme Industrial Corp published its third-quarter 2024 earnings."]),
    )
    acme.release(
        52,
        "2024-12-10 16:05:00",
        (
            "2.02",
            [
                (
                    "Acme Industrial Corp will report Fluid Systems as its own"
                    " segment starting in the first quarter of 2025."
                ),
                (
                    "Exhibit 99.1 restates its segments for the three months ended"
                    " March 31, 2024."
                ),
            ],
        ),
    )
    found = acme.identify()[P]
    assert [c.dropped for c in found.candidates] == [
        None,
        "it states another period",
    ]
    assert found.release.placed.filing.accession == actual.accession
    assert found.method is IdentificationMethod.STATED_PERIOD


def test_two_candidates_the_rule_cannot_separate_are_ambiguous(acme) -> None:
    """A transaction's effect on the quarter states the quarter, as the release does."""
    acme.release(
        33,
        "2024-10-08 17:00:00",
        (
            "2.02",
            [
                (
                    "Acme Industrial Corp agreed to sell its Tooling division, which"
                    " it estimates will add $0.12 to diluted earnings per share for"
                    " the third quarter of 2024."
                )
            ],
        ),
        ("8.01", ["The sale awaits approval."]),
    )
    acme.release(
        40,
        "2024-10-24 16:05:00",
        (
            "2.02",
            [
                "Acme Industrial Corp posted results for the quarter ended September 30, 2024."
            ],
        ),
    )
    found = acme.identify()[P]
    assert [c.dropped for c in found.candidates] == [None, None]
    assert (found.release, found.method) == (None, None)
    assert found.reason is EventReason.SEVERAL_RELEASE_FILINGS


def test_a_candidate_with_no_item_2_02_heading_stays(acme) -> None:
    """SEC lists Item 2.02 for an 8-K whose document holds none: it states nothing,
    so the rule keeps it, and review decides."""
    director = acme.release(
        29,
        "2024-10-11 08:30:00",
        ("5.02", ["The board elected Dana Reyes a director."]),
        listed=("2.02", "7.01", "9.01"),
    )
    acme.release(
        40,
        "2024-10-24 16:05:00",
        (
            "2.02",
            [
                "Acme Industrial Corp posted results for the quarter ended September 30, 2024."
            ],
        ),
    )
    found = acme.identify()[P]
    assert found.candidates[0].placed.filing.accession == director.accession
    assert found.candidates[0].reading.unread == "it has no Item 2.02 heading"
    assert found.candidates[0].dropped is None
    assert found.reason is EventReason.SEVERAL_RELEASE_FILINGS


@pytest.mark.parametrize(
    ("labels", "paragraph", "method"),
    [
        (
            (2024, "Q3"),
            "Acme Industrial Corp published its third quarter of 2024 results.",
            IdentificationMethod.STATED_PERIOD,
        ),
        (
            None,
            "Acme Industrial Corp published its third quarter of 2024 results.",
            IdentificationMethod.SOLE_CANDIDATE,
        ),
        (
            None,
            (
                "Acme Industrial Corp published results for the quarter ended"
                " September 30, 2024."
            ),
            IdentificationMethod.STATED_PERIOD,
        ),
        (
            (2024, "Q3"),
            (
                "On October 24, 2024, Acme Industrial Corp issued a news release on"
                " its results, furnished as Exhibit 99.1."
            ),
            IdentificationMethod.SOLE_CANDIDATE,
        ),
    ],
    ids=["labels", "no-labels", "date", "narrative-only"],
)
def test_a_sole_candidate_is_stated_period_only_with_a_matching_statement(
    acme, labels, paragraph, method
) -> None:
    """A fiscal period is judged only against labels; an announcement date states no
    period, so a narrative-only release is kept."""
    acme.release(40, "2024-10-24 16:05:00", ("2.02", [paragraph]))
    found = acme.identify(labels)[P]
    assert found.method is method
    assert found.release.dropped is None


@pytest.mark.parametrize(
    ("labels", "statement", "dropped"),
    [
        ((2024, "FY"), "its fourth quarter of 2024 results", None),
        ((2024, "FY"), "its full-year 2024 results", None),
        ((2024, "FY"), "its third quarter of 2024 results", "it states another period"),
        (
            (2024, "FY"),
            "its fourth quarter of 2023 results",
            "it states another period",
        ),
        ((2024, "H2"), "its third quarter of 2024 results", None),
    ],
    ids=["fourth-quarter", "full-year", "another-quarter", "another-year", "unjudged"],
)
def test_fy_labels_match_the_fourth_quarter_or_the_full_year(
    acme, labels, statement, dropped
) -> None:
    """A 10-K's ``FY`` is never renamed ``Q4``; an ``fp`` other than ``Q1``-``Q3``
    or ``FY`` judges nothing."""
    item = ("2.02", [f"Acme Industrial Corp published {statement}."])
    acme.release(70, "2025-01-28 16:05:00", item)
    found = acme.identify(labels, REPORTS[2])[date(2024, 12, 31)]
    assert found.candidates[0].dropped == dropped


def test_candidates_are_accepted_after_p_and_by_p_prime_on_the_eastern_calendar(
    acme,
) -> None:
    """P' is the next visible period end, or the cutoff when none is visible."""
    item = ("2.02", ["Acme Industrial Corp published its quarterly results."])
    late_on_p = acme.release(20, "2024-09-30 23:00:00", item)
    first = acme.release(21, "2024-10-01 00:30:00", item)
    on_p_prime = acme.release(60, "2024-12-31 18:00:00", item)
    next_year = acme.release(61, "2025-01-02 07:00:00", item)
    found = acme.identify()
    assert late_on_p.accession not in accessions(found[P].candidates)
    assert accessions(found[P].candidates) == [first.accession, on_p_prime.accession]
    assert accessions(found[date(2024, 12, 31)].candidates) == [next_year.accession]


def test_the_index_page_decides_candidacy(acme) -> None:
    """Any exhibit typed EX-99*, and Items that confirm 2.02; an 8-K/A is recorded
    and never chosen."""
    item = (
        "2.02",
        ["Acme Industrial Corp published its third quarter of 2024 results."],
    )
    plain = acme.release(
        40, "2024-10-24 16:05:00", item, exhibits=(("NEWS", "a.htm", "EX-99"),)
    )
    padded = acme.release(
        41, "2024-10-25 09:00:00", item, exhibits=(("NEWS", "b.htm", "EX-99.01"),)
    )
    acme.release(
        42, "2024-10-28 09:00:00", item, exhibits=(("PLAN", "c.htm", "EX-10.1"),)
    )
    acme.release(43, "2024-10-29 09:00:00", item, indexed=("7.01", "9.01"))
    amended = acme.release(44, "2024-10-30 09:00:00", item, form="8-K/A")
    found = acme.identify()[P]
    assert accessions(found.candidates) == [plain.accession, padded.accession]
    assert [(p.filing.accession[-2:], why) for p, why in found.passed_over] == [
        ("42", "its index page lists no exhibit typed EX-99*"),
        ("43", "its index page lists no Item 2.02"),
    ]
    assert [p.filing.accession for p in found.amendments] == [amended.accession]
    assert found.reason is EventReason.SEVERAL_RELEASE_FILINGS


def test_an_unsaved_primary_document_is_a_problem(acme) -> None:
    filing = acme.release(40, "2024-10-24 16:05:00")
    url = archive_url(CIK, filing.accession, filing.primary_document)
    found = acme.identify()[P]
    assert found.problems == (f"nothing saved from {url}: run events discover",)
    assert found.candidates[0].reading.unread == "nothing saved"


@pytest.mark.parametrize(
    ("body", "media_type", "unread"),
    [
        (
            b"<html><body></body></html>",
            HTML,
            "walker-1 cannot read it: no text is left after N1",
        ),
        (b"Item 2.02 Results", "text/plain", "it is text/plain, not HTML"),
    ],
    ids=["walker-1-fails", "not-html"],
)
def test_a_document_the_rule_cannot_read_states_nothing(
    acme, body, media_type, unread
) -> None:
    filing = acme.release(40, "2024-10-24 16:05:00")
    acme.document(CIK, filing, body, media_type)
    found = acme.identify()[P]
    assert found.candidates[0].reading.unread == unread
    assert found.method is IdentificationMethod.SOLE_CANDIDATE
    assert found.problems == ()


def test_the_release_cites_its_item_text(acme) -> None:
    acme.release(
        40,
        "2024-10-24 16:05:00",
        ("2.02", ["Acme Industrial Corp published its third quarter of 2024 results."]),
    )
    found = acme.identify()[P]
    citation = found.release.item_text()
    assert citation.url == archive_url(
        CIK, found.release.placed.filing.accession, "acme-8k-40.htm"
    )
    (locator,) = citation.locators
    assert locator.canonicalization_version == "walker-1"
    cited = found.release.document.text.cited(locator)
    assert cited.startswith("Item 2.02 Results of Operations and Financial Condition")
    assert cited.endswith("third quarter of 2024 results.")
