"""The cohort records refuse every shape their docstrings rule out."""

from datetime import UTC, date, datetime

import pytest
from earnings_core import RightsStatus
from earnings_ingestion.cohort.records import (
    AssertedAction,
    AssertionStatus,
    BoundBasis,
    BoundTiming,
    EvidenceLocator,
    Finding,
    FindingKind,
    IssuerCandidate,
    IssuerMapping,
    LocatorKind,
    MembershipAssertion,
    MembershipInterval,
    Override,
    OverrideCitation,
    OverrideKind,
    ResolutionMethod,
    ResolutionStatus,
    UniverseDefinition,
)
from pydantic import ValidationError

HASH = "a" * 64
SPAN = {
    "kind": LocatorKind.TEXT_SPAN,
    "canonicalization_version": "walker-1",
    "canonical_sha256": HASH,
    "start": 3,
    "end": 9,
    "cited_sha256": HASH,
}


def assertion(**changes) -> MembershipAssertion:
    fields = {
        "membership_assertion_id": "anchor:acme-common:member_at",
        "universe_id": "djia-test",
        "security_id": "acme-common",
        "issuer_id": None,
        "cik": None,
        "asserted_action": AssertedAction.MEMBER_AT,
        "asserted_date": date(2024, 6, 28),
        "asserted_timing": BoundTiming.UNSPECIFIED,
        "effective_from": date(2024, 6, 28),
        "effective_from_basis": BoundBasis.ANCHOR_SNAPSHOT,
        "effective_from_timing": BoundTiming.UNSPECIFIED,
        "effective_to": None,
        "effective_to_timing": None,
        "announcement_date": None,
        "source_snapshot_date": date(2024, 6, 28),
        "publication_date": date(2024, 6, 20),
        "publication_time": None,
        "retrieved_at": datetime(2026, 9, 27, tzinfo=UTC),
        "source_id": "synthetic-roster",
        "evidence_id": "anchor",
        "url": "https://roster.example/djia?rev=1",
        "evidence_locators": (EvidenceLocator(**SPAN),),
        "raw_content_hash": HASH,
        "rights_status": RightsStatus.REDISTRIBUTABLE,
        "status": AssertionStatus.SUPPORTED,
        "resolved_by": None,
    }
    return MembershipAssertion(**(fields | changes))


def test_a_text_span_locator_needs_offsets_and_a_text_hash() -> None:
    assert EvidenceLocator(**SPAN).end == 9
    with pytest.raises(ValidationError, match="start < end"):
        EvidenceLocator(**(SPAN | {"end": 3}))
    with pytest.raises(ValidationError, match="offsets"):
        EvidenceLocator(**(SPAN | {"canonical_sha256": None}))


def test_a_json_pointer_locator_has_only_its_pointer() -> None:
    whole = EvidenceLocator(
        kind=LocatorKind.JSON_POINTER, pointer="", cited_sha256=HASH
    )
    assert whole.pointer == ""
    with pytest.raises(ValidationError, match="starts with"):
        EvidenceLocator(kind=LocatorKind.JSON_POINTER, pointer="a", cited_sha256=HASH)
    with pytest.raises(ValidationError, match="nothing else"):
        EvidenceLocator(
            kind=LocatorKind.JSON_POINTER, pointer="/0", start=1, cited_sha256=HASH
        )


def test_only_a_supported_assertion_carries_an_interval() -> None:
    assert assertion().effective_to is None
    with pytest.raises(ValidationError, match="only a supported"):
        assertion(status=AssertionStatus.CONFLICTING)
    held = assertion(
        status=AssertionStatus.WITHHELD,
        effective_from=None,
        effective_from_basis=None,
        effective_from_timing=None,
    )
    assert held.effective_from is None


def test_an_interval_ends_after_it_starts_and_ends_with_its_timing() -> None:
    with pytest.raises(ValidationError, match="after effective_from"):
        assertion(
            effective_to=date(2024, 6, 28), effective_to_timing=BoundTiming.BEFORE_OPEN
        )
    with pytest.raises(ValidationError, match="come together"):
        assertion(effective_to=date(2024, 11, 8))


def test_an_issuer_and_its_cik_come_together() -> None:
    assert assertion(issuer_id="cik-0009990001", cik="0009990001").cik == "0009990001"
    with pytest.raises(ValidationError, match="come together"):
        assertion(issuer_id="cik-0009990001")
    with pytest.raises(ValidationError):
        assertion(issuer_id="cik-9990001", cik="9990001")


def test_intervals_are_half_open() -> None:
    interval = MembershipInterval(
        security_id="acme-common",
        effective_from=date(2024, 11, 8),
        effective_from_basis=BoundBasis.ANNOUNCED,
        effective_from_timing=BoundTiming.BEFORE_OPEN,
        effective_to=date(2025, 3, 3),
        effective_to_timing=BoundTiming.BEFORE_OPEN,
        assertion_ids=("a",),
    )
    assert interval.contains(date(2024, 11, 8))
    assert not interval.contains(date(2025, 3, 3))
    assert interval.overlaps(date(2025, 3, 2), date(2025, 3, 3))
    assert not interval.overlaps(date(2025, 3, 3), date(2025, 4, 1))


def test_a_candidate_is_confirmed_exactly_by_a_listed_ticker_and_a_name() -> None:
    fields = {
        "evidence_id": "anchor",
        "cited_name": "Acme Industrial",
        "ticker": "ACME",
        "cik": "0009990001",
        "sec_name": "Acme Industrial Corp",
        "ticker_listed": True,
        "matched_name": "Acme Industrial Corp",
        "confirmed": True,
        "citations": (),
    }
    assert IssuerCandidate(**fields).confirmed
    with pytest.raises(ValidationError, match="confirmed means"):
        IssuerCandidate(**(fields | {"matched_name": None}))


def test_a_mapping_is_resolved_exactly_when_it_has_an_issuer() -> None:
    resolved = IssuerMapping(
        security_id="acme-common",
        status=ResolutionStatus.RESOLVED,
        method=ResolutionMethod.SEC_TICKER_AND_NAME,
        issuer_id="cik-0009990001",
        cik="0009990001",
        candidates=(),
        override_id=None,
        reason=None,
    )
    assert resolved.cik == "0009990001"
    with pytest.raises(ValidationError, match="only a resolved"):
        IssuerMapping(
            **(resolved.model_dump() | {"status": ResolutionStatus.UNRESOLVED})
        )
    with pytest.raises(ValidationError, match="override_id"):
        IssuerMapping(**(resolved.model_dump() | {"override_id": "x"}))
    with pytest.raises(ValidationError, match="reason"):
        IssuerMapping(
            security_id="acme-common",
            status=ResolutionStatus.RETAINED_UNRESOLVED,
            method=None,
            issuer_id=None,
            cik=None,
            candidates=(),
            override_id="keep-acme",
            reason=None,
        )


def test_an_override_sets_exactly_its_kinds_targets() -> None:
    common = {
        "citations": (OverrideCitation(source_id="sec-edgar", url="https://x.test/"),),
        "rationale": "Reviewed.",
        "reviewer": "Reviewer Name",
        "recorded_on": date(2026, 9, 28),
        "effective_from": date(2024, 7, 1),
    }
    issuer = Override(
        override_id="acme-issuer",
        kind=OverrideKind.SET_ISSUER,
        security_id="acme-common",
        cik="0009990001",
        **common,
    )
    assert issuer.cik == "0009990001"
    with pytest.raises(ValidationError, match="sets exactly"):
        Override(
            override_id="acme-issuer",
            kind=OverrideKind.SET_ISSUER,
            security_id="acme-common",
            **common,
        )
    with pytest.raises(ValidationError, match="cites its evidence"):
        Override(**(issuer.model_dump() | {"citations": ()}))
    with pytest.raises(ValidationError, match="after effective_from"):
        Override(**(issuer.model_dump() | {"effective_to": date(2024, 7, 1)}))


def test_a_blocking_finding_holds_the_freeze_until_resolved() -> None:
    finding = Finding(
        finding_id="difference:x",
        kind=FindingKind.DIFFERENCE,
        blocking=True,
        security_id=None,
        detail="A snapshot disagrees.",
        evidence_ids=("x",),
        digest=HASH,
        resolved_by=(),
    )
    assert finding.holds_freeze
    assert not finding.model_copy(update={"resolved_by": ("ack-x",)}).holds_freeze


def test_the_cutoff_cannot_fall_inside_the_window() -> None:
    fields = {
        "universe_id": "djia-test",
        "universe_version": 1,
        "universe_name": "djia",
        "period_end_start": date(2024, 7, 1),
        "period_end_stop": date(2026, 7, 1),
        "public_information_cutoff": date(2026, 9, 22),
        "membership_reference": "first_publication_time",
        "expected_member_count": 30,
        "source_register_version": HASH,
        "selection_policy_version": "djia-pilot/1",
        "content_hash": HASH,
        "created_at": datetime(2026, 9, 28, tzinfo=UTC),
    }
    assert UniverseDefinition(**fields).universe_version == 1
    with pytest.raises(ValidationError, match="inside the window"):
        UniverseDefinition(
            **(fields | {"public_information_cutoff": date(2026, 6, 30)})
        )
