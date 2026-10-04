"""Findings hash what they say, and an acknowledgement accepts only what it read."""

from datetime import date

import pytest
from earnings_core import digest
from earnings_ingestion.cohort.findings import acknowledge, make_finding
from earnings_ingestion.cohort.records import FindingKind, Override, OverrideKind


def difference(detail: str = "roster-x on 2025-01-31: snapshot only: acme-common"):
    return make_finding(
        FindingKind.DIFFERENCE,
        "roster-x",
        detail,
        blocking=True,
        evidence_ids=["roster-x", "anchor", "roster-x"],
    )


def ack(finding_id: str, finding_digest: str, override_id: str = "ack-x") -> Override:
    return Override(
        override_id=override_id,
        kind=OverrideKind.ACKNOWLEDGE,
        finding_id=finding_id,
        finding_digest=finding_digest,
        citations=(),
        rationale="The roster lagged the announced change by one day.",
        reviewer="Reviewer Name",
        recorded_on=date(2026, 9, 28),
        effective_from=date(2024, 7, 1),
    )


def test_a_finding_is_named_by_kind_and_subject_and_hashes_what_it_says() -> None:
    finding = difference()
    assert finding.finding_id == "difference:roster-x"
    assert finding.evidence_ids == ("anchor", "roster-x")
    assert finding.digest == digest(
        {
            "kind": "difference",
            "subject": "roster-x",
            "detail": finding.detail,
            "blocking": True,
            "security_id": None,
            "evidence_ids": ["anchor", "roster-x"],
        }
    )
    assert difference("another detail").digest != finding.digest
    resolved = make_finding(
        FindingKind.DIFFERENCE,
        "roster-x",
        finding.detail,
        blocking=True,
        evidence_ids=["anchor", "roster-x"],
        resolved_by=["ack-x"],
    )
    assert (resolved.digest, resolved.resolved_by) == (finding.digest, ("ack-x",))


def test_an_acknowledgement_resolves_only_the_finding_it_read() -> None:
    finding = difference()
    (resolved,), stale = acknowledge(
        [finding], [ack(finding.finding_id, finding.digest)]
    )
    assert (resolved.resolved_by, stale) == (("ack-x",), ())
    assert not resolved.holds_freeze
    changed = difference("roster-x on 2025-01-31: snapshot only: corvid-common")
    (held,), stale = acknowledge([changed], [ack(finding.finding_id, finding.digest)])
    assert (held.holds_freeze, stale) == (True, ("ack-x",))
    _, stale = acknowledge([], [ack("difference:gone", finding.digest, "ack-gone")])
    assert stale == ("ack-gone",)


def test_only_counts_and_differences_can_be_acknowledged() -> None:
    gap = make_finding(FindingKind.GAP, "2025q1", "no snapshot", blocking=False)
    with pytest.raises(ValueError, match="never acknowledged"):
        acknowledge([gap], [ack(gap.finding_id, gap.digest)])
