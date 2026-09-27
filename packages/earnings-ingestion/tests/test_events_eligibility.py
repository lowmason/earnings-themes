"""eligibility/1: each event's status, reason, and deciding assertion (the Stage 5
spec, §Eligibility; plan 7, P7-11).

The membership cases read Stage 4's committed synthetic cohort: Borealis leaves and
Corvid joins before the open on 2024-11-08, Dynamo holds two securities, and
Eastfield leaves before the open on 2026-06-22.
"""

from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.cohort.records import BoundTiming
from earnings_ingestion.events.acceptance import accepted_instant
from earnings_ingestion.events.eligibility import (
    ELIGIBILITY_POLICY,
    Bound,
    IssuerMembership,
    Side,
    Span,
    Standing,
    decide,
    memberships,
    side,
    standing,
)
from earnings_ingestion.events.records import EventReason, EventStatus

ROOT = Path(__file__).resolve().parents[3]
COHORT = ROOT / "tests" / "fixtures" / "cohort" / "manifests" / "djia-synthetic-v1.json"
START, STOP, CUTOFF = date(2024, 7, 1), date(2026, 7, 1), date(2026, 9, 22)


@pytest.fixture(scope="module")
def issuers() -> dict[str, IssuerMembership]:
    return memberships(load_manifest(COHORT))


def eastern(wall: str) -> datetime:
    """The UTC instant of an Eastern wall time."""
    return accepted_instant(wall)


def test_the_policy_is_named() -> None:
    assert ELIGIBILITY_POLICY == "eligibility/1"


@pytest.mark.parametrize(
    ("timing", "wall", "expected"),
    [
        (BoundTiming.BEFORE_OPEN, "2024-11-07 23:59:59", Side.BEFORE),
        (BoundTiming.BEFORE_OPEN, "2024-11-08 00:00:00", Side.UNORDERED),
        (BoundTiming.BEFORE_OPEN, "2024-11-08 09:29:59", Side.UNORDERED),
        (BoundTiming.BEFORE_OPEN, "2024-11-08 09:30:00", Side.AFTER),
        (BoundTiming.BEFORE_OPEN, "2024-11-09 00:00:00", Side.AFTER),
        (BoundTiming.AFTER_CLOSE, "2024-11-07 16:05:00", Side.BEFORE),
        (BoundTiming.AFTER_CLOSE, "2024-11-08 12:59:59", Side.BEFORE),
        (BoundTiming.AFTER_CLOSE, "2024-11-08 13:00:00", Side.UNORDERED),
        (BoundTiming.AFTER_CLOSE, "2024-11-08 23:59:59", Side.UNORDERED),
        (BoundTiming.AFTER_CLOSE, "2024-11-09 06:00:00", Side.AFTER),
        (BoundTiming.UNSPECIFIED, "2024-11-07 23:59:59", Side.BEFORE),
        (BoundTiming.UNSPECIFIED, "2024-11-08 09:30:00", Side.UNORDERED),
        (BoundTiming.UNSPECIFIED, "2024-11-09 00:00:00", Side.AFTER),
    ],
)
def test_the_bound_rules_in_winter(timing, wall, expected) -> None:
    """2024-11-08 is in Eastern Standard Time."""
    assert side(date(2024, 11, 8), timing, eastern(wall)) is expected


@pytest.mark.parametrize(
    ("timing", "wall", "expected"),
    [
        (BoundTiming.BEFORE_OPEN, "2026-06-22 09:29:59", Side.UNORDERED),
        (BoundTiming.BEFORE_OPEN, "2026-06-22 09:30:00", Side.AFTER),
        (BoundTiming.AFTER_CLOSE, "2026-06-22 12:59:59", Side.BEFORE),
        (BoundTiming.AFTER_CLOSE, "2026-06-22 13:00:00", Side.UNORDERED),
    ],
)
def test_the_bound_rules_in_summer(timing, wall, expected) -> None:
    """2026-06-22 is in Eastern Daylight Time: 09:30 there is 13:30 UTC."""
    instant = eastern(wall)
    assert side(date(2026, 6, 22), timing, instant) is expected
    assert side(date(2026, 6, 22), timing, instant.astimezone(UTC)) is expected


def test_a_naive_instant_is_refused() -> None:
    with pytest.raises(ValueError, match="carries its offset"):
        naive = datetime(2024, 11, 8, 12, tzinfo=UTC).replace(tzinfo=None)
        side(date(2024, 11, 8), BoundTiming.UNSPECIFIED, naive)


@pytest.mark.parametrize(
    ("issuer", "wall", "expected", "assertion"),
    [
        (
            "cik-0009990003",
            "2024-11-07 16:05:00",
            Standing.NOT_MEMBER,
            "index-2024-11-01:corvid-common:added",
        ),
        (
            "cik-0009990003",
            "2024-11-08 07:00:00",
            Standing.UNORDERED,
            "index-2024-11-01:corvid-common:added",
        ),
        (
            "cik-0009990003",
            "2024-11-08 09:30:00",
            Standing.MEMBER,
            "index-2024-11-01:corvid-common:added",
        ),
        (
            "cik-0009990002",
            "2024-10-24 16:05:00",
            Standing.MEMBER,
            "roster-2024-06-28:borealis-common:member_at",
        ),
        (
            "cik-0009990002",
            "2024-11-08 07:00:00",
            Standing.UNORDERED,
            "index-2024-11-01:borealis-common:removed",
        ),
        (
            "cik-0009990002",
            "2024-11-08 09:30:00",
            Standing.NOT_MEMBER,
            "index-2024-11-01:borealis-common:removed",
        ),
        (
            "cik-0009990001",
            "2024-07-25 16:05:00",
            Standing.MEMBER,
            "roster-2024-06-28:acme-common:member_at",
        ),
        (
            "cik-0009990001",
            "2024-06-28 07:00:00",
            Standing.MEMBER,
            "roster-2024-06-28:acme-common:member_at",
        ),
        (
            "cik-0009990005",
            "2026-07-23 16:05:00",
            Standing.MEMBER,
            "roster-2024-06-28:dynamo-class-a:member_at",
        ),
        (
            "cik-0009990005",
            "2026-06-22 07:00:00",
            Standing.MEMBER,
            "roster-2024-06-28:dynamo-class-a:member_at",
        ),
        (
            "cik-0009990006",
            "2026-07-30 16:05:00",
            Standing.NOT_MEMBER,
            "index-2026-06-16:eastfield-common:removed",
        ),
    ],
    ids=[
        "corvid-day-before",
        "corvid-pre-market",
        "corvid-at-open",
        "borealis-member",
        "borealis-pre-market",
        "borealis-at-open",
        "acme-anchor",
        "acme-on-the-anchor-date",
        "dynamo-first-opened",
        "dynamo-one-security-holds",
        "eastfield-removed",
    ],
)
def test_membership_at_publication_and_its_assertion(
    issuers, issuer, wall, expected, assertion
) -> None:
    """An anchor's start is a lower bound, whatever the time on its date. Dynamo is a
    member while one security's interval holds T, though another's start is
    unordered; of two intervals holding T, the one that opened first decides."""
    assert standing(issuers[issuer], eastern(wall)) == (expected, assertion)


def gap(removed: date, added: date) -> IssuerMembership:
    """An invented issuer whose security leaves on ``removed`` and returns on
    ``added``, each before the open."""
    first = Span(
        security_id="gamma-common",
        start=Bound(date(2024, 6, 28), BoundTiming.UNSPECIFIED, ("a-member_at",)),
        anchor=True,
        end=Bound(removed, BoundTiming.BEFORE_OPEN, ("b-removed",)),
    )
    second = Span(
        security_id="gamma-common",
        start=Bound(added, BoundTiming.BEFORE_OPEN, ("c-added",)),
        anchor=False,
        end=None,
    )
    return IssuerMembership("cik-0009990007", (first, second))


@pytest.mark.parametrize(
    ("wall", "assertion"),
    [
        ("2025-03-10 16:05:00", "b-removed"),
        ("2025-03-12 16:05:00", "b-removed"),
        ("2025-03-14 16:05:00", "c-added"),
    ],
    ids=["nearer-removal", "tie", "nearer-addition"],
)
def test_a_non_member_cites_the_nearer_change_and_a_tie_goes_to_the_removal(
    wall, assertion
) -> None:
    membership = gap(date(2025, 3, 3), date(2025, 3, 21))
    assert standing(membership, eastern(wall)) == (Standing.NOT_MEMBER, assertion)


def decision(
    issuers, period_end, published, unidentified=None, issuer="cik-0009990002"
):
    return decide(
        period_end,
        published,
        unidentified,
        issuers[issuer],
        start=START,
        stop=STOP,
        cutoff=CUTOFF,
    )


@pytest.mark.parametrize(
    ("period_end", "wall", "unidentified", "status", "reason", "assertion"),
    [
        (
            date(2024, 6, 30),
            "2024-07-25 16:05:00",
            None,
            EventStatus.INELIGIBLE,
            EventReason.PERIOD_END_OUTSIDE_WINDOW,
            None,
        ),
        (
            date(2026, 7, 1),
            None,
            EventReason.NO_RELEASE_FILING,
            EventStatus.INELIGIBLE,
            EventReason.PERIOD_END_OUTSIDE_WINDOW,
            None,
        ),
        (
            date(2024, 9, 30),
            None,
            EventReason.NO_RELEASE_FILING,
            EventStatus.AMBIGUOUS,
            EventReason.NO_RELEASE_FILING,
            None,
        ),
        (
            date(2024, 9, 30),
            None,
            EventReason.SEVERAL_RELEASE_FILINGS,
            EventStatus.AMBIGUOUS,
            EventReason.SEVERAL_RELEASE_FILINGS,
            None,
        ),
        (
            date(2026, 6, 30),
            "2026-09-23 00:30:00",
            None,
            EventStatus.INELIGIBLE,
            EventReason.PUBLISHED_AFTER_CUTOFF,
            None,
        ),
        (
            date(2024, 9, 30),
            "2024-10-24 16:05:00",
            None,
            EventStatus.ELIGIBLE,
            EventReason.MEMBER_AT_PUBLICATION,
            "roster-2024-06-28:borealis-common:member_at",
        ),
        (
            date(2024, 12, 31),
            "2025-01-28 16:05:00",
            None,
            EventStatus.INELIGIBLE,
            EventReason.NOT_MEMBER_AT_PUBLICATION,
            "index-2024-11-01:borealis-common:removed",
        ),
        (
            date(2024, 9, 30),
            "2024-11-08 07:00:00",
            None,
            EventStatus.AMBIGUOUS,
            EventReason.SAME_DAY_TRANSITION,
            "index-2024-11-01:borealis-common:removed",
        ),
    ],
    ids=[
        "window-before",
        "window-stop",
        "no-release",
        "several",
        "after-cutoff",
        "member",
        "not-member",
        "same-day",
    ],
)
def test_every_reason_and_the_checks_order(
    issuers, period_end, wall, unidentified, status, reason, assertion
) -> None:
    """The first check that applies decides, and only check 4 names an assertion."""
    published = None if wall is None else eastern(wall)
    found = decision(issuers, period_end, published, unidentified)
    assert (found.status, found.reason) == (status, reason)
    assert found.membership_assertion_id == assertion


def test_the_cutoff_is_judged_on_the_eastern_calendar(issuers) -> None:
    """21:30 Eastern on the cutoff is 01:30 UTC the next day, and is not after it."""
    late = datetime(2026, 9, 23, 1, 30, tzinfo=UTC)
    found = decision(issuers, date(2026, 6, 30), late, issuer="cik-0009990001")
    assert found.reason is EventReason.MEMBER_AT_PUBLICATION


def test_an_event_without_a_release_needs_its_identification_reason(issuers) -> None:
    with pytest.raises(ValueError, match="no_release_filing or several"):
        decision(issuers, date(2024, 9, 30), None, None)
