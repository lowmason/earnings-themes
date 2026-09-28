"""EDGAR acceptance time (the Stage 5 spec, EV10 and §Acceptance time)."""

from datetime import UTC, date, datetime

import pytest
from earnings_ingestion.events.acceptance import (
    AcceptanceTimeError,
    Convention,
    accepted_instant,
    convention_of,
    eastern_date,
    eastern_dates,
    survey,
)
from earnings_ingestion.sec.data import Filing


def written(value: str) -> datetime:
    """A submissions ``acceptanceDateTime`` as ``read_submissions`` returns it."""
    return datetime.fromisoformat(value)


@pytest.mark.parametrize(
    ("accepted", "instant"),
    [
        ("2024-10-24 16:05:12", datetime(2024, 10, 24, 20, 5, 12, tzinfo=UTC)),
        ("2025-01-28 07:00:03", datetime(2025, 1, 28, 12, 0, 3, tzinfo=UTC)),
    ],
    ids=["daylight-time", "standard-time"],
)
def test_the_accepted_value_is_eastern_wall_time(accepted, instant) -> None:
    assert accepted_instant(accepted) == instant


@pytest.mark.parametrize(
    "accepted",
    ["2025-11-02 01:30:00", "2025-03-09 02:30:00"],
    ids=["repeated-hour", "skipped-hour"],
)
def test_a_wall_time_daylight_saving_repeats_or_skips_is_refused(accepted) -> None:
    with pytest.raises(AcceptanceTimeError, match=accepted):
        accepted_instant(accepted)


def test_dates_are_judged_on_the_eastern_calendar() -> None:
    assert eastern_date(datetime(2026, 9, 23, 2, 0, tzinfo=UTC)) == date(2026, 9, 22)
    assert eastern_date(datetime(2026, 9, 23, 4, 0, tzinfo=UTC)) == date(2026, 9, 23)


@pytest.mark.parametrize(
    ("value", "convention"),
    [
        ("2024-10-24T20:05:12.000Z", Convention.UTC),
        ("2024-10-24T16:05:12.000Z", Convention.EASTERN_DIGITS),
        ("2024-10-24T16:05:12-04:00", Convention.UTC),
        ("2024-10-24T16:05:13.000Z", None),
        ("2024-10-24T16:05:12-05:00", None),
    ],
    ids=["utc", "eastern-digits", "stated-offset", "a-second-off", "wrong-offset"],
)
def test_a_row_uses_one_convention_or_mismatches(value, convention) -> None:
    instant = accepted_instant("2024-10-24 16:05:12")
    assert convention_of(written(value), instant) == convention


def test_a_row_without_a_value_mismatches() -> None:
    assert convention_of(None, accepted_instant("2024-10-24 16:05:12")) is None


def test_a_value_has_an_eastern_date_under_each_convention_it_can_be_in() -> None:
    assert eastern_dates(written("2026-09-23T01:30:00.000Z")) == {
        Convention.UTC: date(2026, 9, 22),
        Convention.EASTERN_DIGITS: date(2026, 9, 23),
    }
    assert eastern_dates(written("2026-09-22T15:00:00.000Z")) == {
        Convention.UTC: date(2026, 9, 22),
        Convention.EASTERN_DIGITS: date(2026, 9, 22),
    }
    assert eastern_dates(written("2026-09-22T23:30:00-04:00")) == {
        Convention.UTC: date(2026, 9, 22)
    }


def filing(index: int, value: str | None) -> Filing:
    return Filing(
        accession=f"0009990001-24-00001{index}",
        form="8-K",
        filing_date=date(2024, 10, 24),
        report_date=None,
        accepted_at=None if value is None else written(value),
        primary_document="acme-8k.htm",
        columns="/filings/recent",
        index=index,
        items=("2.02", "9.01"),
    )


INSTANTS = {
    "0009990001-24-000010": accepted_instant("2024-10-24 16:05:12"),
    "0009990001-24-000011": accepted_instant("2025-01-28 07:00:03"),
}


def test_a_file_s_convention_is_the_one_its_cross_checked_rows_share() -> None:
    rows = [
        filing(0, "2024-10-24T20:05:12.000Z"),
        filing(1, "2025-01-28T12:00:03.000Z"),
        filing(2, "2025-04-24T20:00:00.000Z"),
    ]
    checked = survey("CIK0009990001.json", rows, INSTANTS)
    assert checked.convention is Convention.UTC
    assert [check.accession for check in checked.checks] == [
        "0009990001-24-000010",
        "0009990001-24-000011",
    ]
    assert checked.checks[0].pointer == "/filings/recent/acceptanceDateTime/0"
    assert (checked.mismatches, checked.mixed) == ((), False)


def test_a_mismatch_is_named_and_leaves_the_convention_to_the_other_rows() -> None:
    rows = [filing(0, "2024-10-24T16:05:12.000Z"), filing(1, None)]
    checked = survey("CIK0009990001.json", rows, INSTANTS)
    assert checked.convention is Convention.EASTERN_DIGITS
    assert [check.accession for check in checked.mismatches] == ["0009990001-24-000011"]


def test_a_file_using_both_conventions_has_none() -> None:
    rows = [filing(0, "2024-10-24T16:05:12.000Z"), filing(1, "2025-01-28T12:00:03Z")]
    checked = survey("CIK0009990001.json", rows, INSTANTS)
    assert (checked.convention, checked.mixed) == (None, True)


def test_a_file_with_no_cross_checked_row_has_no_convention() -> None:
    checked = survey("CIK0009990001.json", [filing(2, "2025-04-24T20:00:00Z")], {})
    assert (checked.checks, checked.convention, checked.mixed) == ((), None, False)
