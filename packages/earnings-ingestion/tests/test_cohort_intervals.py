"""Interval reconstruction: P-VF's interval, conflict, and cutoff cases."""

from datetime import date

import pytest
from earnings_ingestion.cohort.intervals import (
    Statement,
    count_findings,
    reconstruct,
    roster,
)
from earnings_ingestion.cohort.records import (
    AssertedAction,
    AssertionStatus,
    BoundBasis,
    BoundTiming,
    FindingKind,
)

ANCHOR = date(2024, 6, 28)
CUTOFF = date(2026, 9, 22)
ADDED, REMOVED, MEMBER = (
    AssertedAction.ADDED,
    AssertedAction.REMOVED,
    AssertedAction.MEMBER_AT,
)


def say(
    security: str,
    action: AssertedAction,
    on: date,
    evidence: str,
    *,
    timing: BoundTiming = BoundTiming.BEFORE_OPEN,
    published: date | None = None,
) -> Statement:
    return Statement(
        assertion_id=f"{evidence}:{security}:{action}",
        security_id=security,
        action=action,
        on=on,
        timing=BoundTiming.UNSPECIFIED if action is MEMBER else timing,
        evidence_id=evidence,
        published_on=published or on,
    )


def anchor(*securities: str) -> list[Statement]:
    return [
        say(s, MEMBER, ANCHOR, "anchor", published=date(2024, 6, 20))
        for s in securities
    ]


def run(statements, rejections=None, anchor_date=ANCHOR):
    return reconstruct(
        statements,
        anchor_date=anchor_date,
        cutoff=CUTOFF,
        rejections=rejections or {},
    )


def test_anchor_additions_and_removals_make_half_open_intervals() -> None:
    result = run(
        [
            *anchor("acme", "borealis"),
            say("borealis", REMOVED, date(2024, 11, 8), "change-1"),
            say("corvid", ADDED, date(2024, 11, 8), "change-1"),
        ]
    )
    by_security = {i.security_id: i for i in result.intervals}
    acme, borealis, corvid = (by_security[s] for s in ("acme", "borealis", "corvid"))
    assert (acme.effective_from, acme.effective_to) == (ANCHOR, None)
    assert acme.effective_from_basis is BoundBasis.ANCHOR_SNAPSHOT
    assert acme.effective_to_timing is None
    assert (borealis.effective_to, borealis.effective_to_timing) == (
        date(2024, 11, 8),
        BoundTiming.BEFORE_OPEN,
    )
    assert corvid.effective_from_basis is BoundBasis.ANNOUNCED
    assert roster(result.intervals, date(2024, 11, 7)) == {"acme", "borealis"}
    assert roster(result.intervals, date(2024, 11, 8)) == {"acme", "corvid"}
    assert set(result.statuses.values()) == {AssertionStatus.SUPPORTED}
    assert result.findings == ()


def test_identical_claims_from_two_items_are_one_transition() -> None:
    result = run(
        [
            *anchor("acme"),
            say("corvid", ADDED, date(2024, 11, 8), "change-1"),
            say("corvid", ADDED, date(2024, 11, 8), "change-1-wire"),
        ]
    )
    (corvid,) = [i for i in result.intervals if i.security_id == "corvid"]
    assert corvid.assertion_ids == (
        "change-1-wire:corvid:added",
        "change-1:corvid:added",
    )


def test_conflicting_dates_stay_separate_and_hold_until_one_is_rejected() -> None:
    statements = [
        *anchor("acme"),
        say("corvid", ADDED, date(2024, 11, 7), "wire-report"),
        say("corvid", ADDED, date(2024, 11, 8), "change-1"),
    ]
    held = run(statements)
    assert [i.security_id for i in held.intervals] == ["acme"]
    assert held.statuses["wire-report:corvid:added"] is AssertionStatus.CONFLICTING
    assert held.statuses["change-1:corvid:added"] is AssertionStatus.CONFLICTING
    (finding,) = held.findings
    assert (finding.kind, finding.holds_freeze) == (
        FindingKind.MEMBERSHIP_CONFLICT,
        True,
    )

    reviewed = run(statements, {"wire-report:corvid:added": "reject-wire"})
    assert reviewed.statuses["wire-report:corvid:added"] is AssertionStatus.CONFLICTING
    assert reviewed.rejected_by == {"wire-report:corvid:added": "reject-wire"}
    assert reviewed.statuses["change-1:corvid:added"] is AssertionStatus.SUPPORTED
    (resolved,) = reviewed.findings
    assert resolved.resolved_by == ("reject-wire",)
    assert not resolved.holds_freeze


@pytest.mark.parametrize(
    ("statements", "detail"),
    [
        ([say("acme", ADDED, date(2024, 11, 8), "c")], "added on 2024-11-08 while a"),
        ([say("zeta", REMOVED, date(2024, 11, 8), "c")], "removed on 2024-11-08"),
        ([say("acme", REMOVED, ANCHOR, "c")], "on or before the anchor's date"),
        (
            [
                say("zeta", ADDED, date(2024, 11, 8), "c"),
                say(
                    "zeta",
                    ADDED,
                    date(2024, 11, 8),
                    "d",
                    timing=BoundTiming.AFTER_CLOSE,
                ),
            ],
            "with timings",
        ),
    ],
    ids=["added-while-member", "removed-while-not", "before-anchor", "two-timings"],
)
def test_every_break_in_the_sequence_is_a_conflict(statements, detail) -> None:
    result = run([*anchor("acme"), *statements])
    (finding,) = result.findings
    assert finding.kind is FindingKind.MEMBERSHIP_CONFLICT
    assert detail in finding.detail


def test_an_addition_and_a_removal_on_one_date_are_ambiguous() -> None:
    result = run(
        [
            *anchor("acme"),
            say("acme", REMOVED, date(2025, 3, 3), "c"),
            say("acme", ADDED, date(2025, 3, 3), "d", timing=BoundTiming.AFTER_CLOSE),
        ]
    )
    assert result.statuses["c:acme:removed"] is AssertionStatus.AMBIGUOUS
    assert result.statuses["anchor:acme:member_at"] is AssertionStatus.AMBIGUOUS
    assert result.findings[0].kind is FindingKind.MEMBERSHIP_AMBIGUITY
    assert result.intervals == ()


def test_evidence_published_after_the_cutoff_is_withheld() -> None:
    late = say("corvid", ADDED, date(2026, 9, 30), "late", published=date(2026, 9, 23))
    result = run([*anchor("acme"), late])
    assert result.statuses["late:corvid:added"] is AssertionStatus.WITHHELD
    assert [i.security_id for i in result.intervals] == ["acme"]


def test_evidence_published_on_the_cutoff_applies() -> None:
    change = say("corvid", ADDED, date(2026, 9, 30), "c", published=CUTOFF)
    result = run([*anchor("acme"), change])
    assert result.statuses["c:corvid:added"] is AssertionStatus.SUPPORTED


def test_only_a_conflicting_or_ambiguous_assertion_can_be_rejected() -> None:
    with pytest.raises(ValueError, match="only a conflicting or ambiguous"):
        run(anchor("acme"), {"anchor:acme:member_at": "reject"})
    with pytest.raises(ValueError, match="name no assertion"):
        run(anchor("acme"), {"nowhere": "reject"})


def test_without_an_anchor_only_announced_intervals_exist() -> None:
    result = run(
        [
            say("corvid", ADDED, date(2024, 11, 8), "c"),
            say("borealis", REMOVED, date(2024, 11, 8), "c"),
        ],
        anchor_date=None,
    )
    assert [i.security_id for i in result.intervals] == ["corvid"]
    assert result.statuses["c:borealis:removed"] is AssertionStatus.CONFLICTING


def test_a_roster_of_the_wrong_size_is_a_blocking_finding() -> None:
    result = run(
        [
            *anchor("acme", "borealis"),
            say("corvid", ADDED, date(2024, 11, 8), "c"),
        ]
    )
    (finding,) = count_findings(
        result.intervals, anchor_date=ANCHOR, cutoff=CUTOFF, expected=2
    )
    assert finding.finding_id == "member_count:2024-11-08"
    assert (
        finding.detail == "3 members on 2024-11-08, expected 2: acme, borealis, corvid"
    )
    assert finding.holds_freeze
