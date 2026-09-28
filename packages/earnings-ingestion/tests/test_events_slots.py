"""Slots, their guards, and their fiscal labels (the Stage 5 spec, §Slots)."""

from datetime import UTC, date, datetime, timedelta

import pytest
from earnings_ingestion.events.acceptance import Convention
from earnings_ingestion.events.filings import issuer_filings
from earnings_ingestion.events.records import EventFindingKind
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.slots import issuer_slots
from earnings_ingestion.events.synthetic import SyntheticFiling, SyntheticStore
from earnings_ingestion.sec.companyfacts import read_companyfacts
from earnings_ingestion.sec.urls import companyfacts_url

CIK = "0009990001"
ISSUER = "cik-0009990001"
START, STOP, CUTOFF = date(2024, 7, 1), date(2026, 7, 1), date(2026, 9, 22)
RETRIEVED = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)


def report(period: date, *, form: str = "10-Q", lag: int = 35) -> SyntheticFiling:
    filed = period + timedelta(days=lag)
    return SyntheticFiling(
        accession=f"0009990001-{filed:%y}-{period:%m%d}00",
        form=form,
        filing_date=filed,
        accepted=f"{filed.isoformat()} 16:30:00",
        report_date=period,
        primary_document=f"acme-{period:%Y%m%d}.htm",
    )


QUARTERS = [
    date(2024, 3, 31),
    date(2024, 6, 30),
    date(2024, 9, 30),
    date(2024, 12, 31),
    date(2025, 3, 31),
    date(2025, 6, 30),
    date(2025, 9, 30),
    date(2025, 12, 31),
    date(2026, 3, 31),
    date(2026, 6, 30),
]
"""A calendar-quarter issuer's period ends, one before and eight in the window."""


def slots_of(tmp_path, reports, facts=None):
    """The issuer's slots and findings, from its saved submissions and companyfacts."""
    synthetic = SyntheticStore(tmp_path / "events", tmp_path, RETRIEVED)
    synthetic.submissions(CIK, "Acme", reports, convention=Convention.UTC)
    labels = [(r.accession, 2025, "Q1") for r in reports] if facts is None else facts
    synthetic.companyfacts(CIK, "Acme", labels)
    saved = SavedResponses(synthetic.store)
    filings = issuer_filings(saved, CIK, ISSUER, start=START, cutoff=CUTOFF)
    body = saved.get(companyfacts_url(CIK)).text.body
    return issuer_slots(
        filings, read_companyfacts(body), ISSUER, start=START, stop=STOP
    )


def test_one_slot_per_period_end_in_the_window(tmp_path) -> None:
    reports = [
        report(end, form="10-K" if end.month == 12 else "10-Q", lag=50)
        for end in QUARTERS
    ]
    amendment = SyntheticFiling(
        accession="0009990001-25-000777",
        form="10-Q/A",
        filing_date=date(2025, 6, 1),
        accepted="2025-06-01 12:00:00",
        report_date=date(2025, 3, 31),
    )
    slots, findings = slots_of(tmp_path, [*reports, amendment])
    assert [slot.period_end for slot in slots] == QUARTERS[2:]
    assert slots[0].event_id == "cik-0009990001:2024-09-30"
    assert slots[0].periodic.filing.form == "10-Q"
    assert (slots[0].next_period_end, slots[-1].next_period_end) == (
        date(2024, 12, 31),
        None,
    )
    assert findings == ()


def test_a_periodic_report_after_the_cutoff_makes_no_slot_and_no_successor(
    tmp_path,
) -> None:
    """The window's last quarter, filed after the cutoff, is not visible (P-C4)."""
    reports = [report(end) for end in QUARTERS[:-1]]
    late = report(date(2026, 6, 30), lag=90)
    slots, findings = slots_of(tmp_path, [*reports, late])
    assert slots[-1].period_end == date(2026, 3, 31)
    assert [f.finding_id for f in findings] == [
        "period_gap:cik-0009990001:2026-03-31:2026-07-01"
    ]


def test_a_nike_like_calendar_trips_no_guard(tmp_path) -> None:
    """The last in-window period ends 2026-05-31, and its successor is filed after
    the cutoff: the guards judge the window's edges by quarter length (S §Slots)."""
    ends = [
        date(2024, 5, 31),
        date(2024, 8, 31),
        date(2024, 11, 30),
        date(2025, 2, 28),
        date(2025, 5, 31),
        date(2025, 8, 31),
        date(2025, 11, 30),
        date(2026, 2, 28),
        date(2026, 5, 31),
    ]
    slots, findings = slots_of(tmp_path, [report(end) for end in ends])
    assert len(slots) == 8
    assert findings == ()


@pytest.mark.parametrize(
    ("missing", "finding"),
    [
        (
            date(2025, 6, 30),
            "period_gap:cik-0009990001:2025-03-31:2025-09-30",
        ),
        (None, "period_gap:cik-0009990001:2024-07-01:2024-12-31"),
        (date(2026, 6, 30), "period_gap:cik-0009990001:2026-03-31:2026-07-01"),
    ],
    ids=["between-two-period-ends", "no-predecessor", "no-successor"],
)
def test_each_period_gap_case_blocks(tmp_path, missing, finding) -> None:
    if missing is None:
        ends = QUARTERS[3:]
    else:
        ends = [end for end in QUARTERS if end != missing]
    _, findings = slots_of(tmp_path, [report(end) for end in ends])
    (found,) = findings
    assert found.finding_id == finding
    assert found.kind is EventFindingKind.PERIOD_GAP
    assert found.holds_freeze


def test_the_gap_s_detail_states_the_dates_and_days(tmp_path) -> None:
    ends = [end for end in QUARTERS if end != date(2025, 6, 30)]
    _, (found,) = slots_of(tmp_path, [report(end) for end in ends])
    assert found.detail == (
        "no period end is visible between 2025-03-31 and 2025-09-30, 183 days apart"
    )


def test_an_issuer_without_a_slot_blocks(tmp_path) -> None:
    _, findings = slots_of(tmp_path, [report(date(2024, 3, 31))])
    assert [f.finding_id for f in findings] == ["no_slots:cik-0009990001"]
    assert findings[0].detail == (
        "no original periodic report with a period end in [2024-07-01, 2026-07-01)"
        " was accepted by the cutoff"
    )


def test_labels_come_from_companyfacts_and_unknown_ones_are_reported(
    tmp_path,
) -> None:
    reports = [report(end) for end in QUARTERS]
    facts = [(reports[2].accession, 2024, "Q3"), (reports[3].accession, 2024, "FY")]
    facts += [(reports[4].accession, 2025, "Q1"), (reports[4].accession, 2025, "Q2")]
    slots, findings = slots_of(tmp_path, reports, facts)
    labels = [
        None if s.labels is None else (s.labels.fiscal_year, s.labels.fiscal_period)
        for s in slots
    ]
    assert labels[:3] == [(2024, "Q3"), (2024, "FY"), None]
    unknown = [f for f in findings if f.kind is EventFindingKind.FISCAL_LABELS_UNKNOWN]
    assert len(unknown) == 6
    assert not any(f.blocking for f in unknown)
    assert unknown[0].finding_id == "fiscal_labels_unknown:cik-0009990001:2025-03-31"
    assert unknown[0].detail == (
        f"companyfacts' facts of {reports[4].accession} disagree on fy and fp, or"
        " leave one out"
    )
    assert unknown[1].detail == (
        f"companyfacts holds no fact of {reports[5].accession}"
    )


def test_the_earliest_filed_original_report_of_a_period_makes_its_slot(
    tmp_path,
) -> None:
    first = report(date(2024, 9, 30), lag=35)
    second = SyntheticFiling(
        accession="0009990001-24-000999",
        form="10-Q",
        filing_date=date(2024, 11, 20),
        accepted="2024-11-20 09:00:00",
        report_date=date(2024, 9, 30),
    )
    reports = [first, second, *[report(end) for end in QUARTERS[3:]]]
    reports.insert(0, report(date(2024, 6, 30)))
    slots, _ = slots_of(tmp_path, reports)
    assert slots[0].periodic.filing.accession == first.accession


def test_the_window_is_half_open(tmp_path) -> None:
    """P-VF: period ends on each side of 2024-07-01 and of 2026-07-01."""
    ends = [date(2024, 6, 30), date(2024, 7, 1), date(2026, 6, 30), date(2026, 7, 1)]
    slots, _ = slots_of(tmp_path, [report(end, lag=20) for end in ends])
    assert [slot.period_end for slot in slots] == [date(2024, 7, 1), date(2026, 6, 30)]
