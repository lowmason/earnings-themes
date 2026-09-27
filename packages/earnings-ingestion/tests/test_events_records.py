"""Stage 5's records: event rows, findings, overrides, and the manifest's hash."""

from datetime import UTC, date, datetime

import pytest
from earnings_ingestion.cohort.records import OverrideCitation
from earnings_ingestion.events.records import (
    EventFindingKind,
    EventManifest,
    EventManifestDefinition,
    EventOverride,
    EventOverrideKind,
    EventOverridesFile,
    EventReason,
    EventRow,
    EventStatus,
    IdentificationMethod,
    content_hash,
    event_finding,
)
from pydantic import ValidationError

ACCEPTED = datetime(2024, 10, 24, 20, 5, 12, tzinfo=UTC)
OPENER = "roster-2024-06-28:acme-common:member_at"


def row(**changes: object) -> EventRow:
    values = {
        "event_id": "cik-0009990001:2024-09-30",
        "issuer_id": "cik-0009990001",
        "cik": "0009990001",
        "period_end": date(2024, 9, 30),
        "reported_fiscal_year": 2025,
        "reported_fiscal_quarter": "Q1",
        "periodic_accession": "0009990001-24-000031",
        "periodic_form": "10-Q",
        "release_accession": "0009990001-24-000029",
        "candidate_accessions": ("0009990001-24-000029",),
        "identification_method": IdentificationMethod.STATED_PERIOD,
        "filing_acceptance_time": ACCEPTED,
        "first_publication_time": ACCEPTED,
        "source_timezone": "America/New_York",
        "first_publication_source_id": "sec-edgar",
        "membership_assertion_id": OPENER,
        "eligibility_status": EventStatus.ELIGIBLE,
        "eligibility_reason": EventReason.MEMBER_AT_PUBLICATION,
        "retained": False,
        "override_ids": (),
    }
    return EventRow(**(values | changes))


UNRELEASED = {
    "release_accession": None,
    "identification_method": None,
    "filing_acceptance_time": None,
    "first_publication_time": None,
    "first_publication_source_id": None,
    "membership_assertion_id": None,
    "eligibility_status": EventStatus.AMBIGUOUS,
    "eligibility_reason": EventReason.NO_RELEASE_FILING,
}


def test_an_eligible_row_keeps_every_time_and_label_apart() -> None:
    """R1.5 and P-A5: the period end, the labels, and both times are separate."""
    event = row()
    assert (event.period_end, event.reported_fiscal_quarter) == (
        date(2024, 9, 30),
        "Q1",
    )
    assert event.first_publication_time == event.filing_acceptance_time == ACCEPTED


def test_unknown_labels_stay_null_together() -> None:
    row(reported_fiscal_year=None, reported_fiscal_quarter=None)
    with pytest.raises(ValidationError, match="labels"):
        row(reported_fiscal_year=None)


def test_an_unidentified_release_has_no_times_and_no_assertion() -> None:
    event = row(**UNRELEASED)
    assert event.filing_acceptance_time is None
    with pytest.raises(ValidationError, match="release"):
        row(**(UNRELEASED | {"identification_method": IdentificationMethod.OVERRIDE}))


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"event_id": "cik-0009990001:2024-09-29"}, "event_id"),
        ({"first_publication_time": datetime(2024, 10, 24, 20, 6, tzinfo=UTC)}, "EV9"),
        ({"eligibility_status": EventStatus.INELIGIBLE}, "status"),
        ({"retained": True}, "retained"),
        ({"membership_assertion_id": None}, "membership_assertion_id"),
        (
            {
                "eligibility_status": EventStatus.INELIGIBLE,
                "eligibility_reason": EventReason.PUBLISHED_AFTER_CUTOFF,
            },
            "membership_assertion_id",
        ),
        (
            {
                "filing_acceptance_time": datetime.fromisoformat(
                    "2024-10-24T16:05:12-04:00"
                ),
                "first_publication_time": datetime.fromisoformat(
                    "2024-10-24T16:05:12-04:00"
                ),
            },
            "UTC",
        ),
        ({"candidate_accessions": ("0009990001-24-000029",) * 2}, "candidate"),
    ],
    ids=[
        "id-not-issuer-and-period",
        "publication-not-acceptance",
        "status-not-the-reasons",
        "retained-but-eligible",
        "member-without-assertion",
        "assertion-after-cutoff",
        "time-not-utc",
        "candidate-repeated",
    ],
)
def test_an_inconsistent_row_is_refused(changes, message) -> None:
    with pytest.raises(ValidationError, match=message):
        row(**changes)


def test_a_retained_ambiguous_row_keeps_its_reason() -> None:
    event = row(**(UNRELEASED | {"retained": True, "override_ids": ("keep-it",)}))
    assert (event.eligibility_status, event.retained) == (EventStatus.AMBIGUOUS, True)


def test_a_finding_s_id_and_digest_follow_what_it_says() -> None:
    first = event_finding(
        EventFindingKind.PERIOD_GAP,
        "cik-0009990006:2025-03-31:2025-09-30",
        "no period end between 2025-03-31 and 2025-09-30",
        issuer_id="cik-0009990006",
    )
    assert first.finding_id == "period_gap:cik-0009990006:2025-03-31:2025-09-30"
    assert (first.blocking, first.holds_freeze) == (True, True)
    again = event_finding(
        EventFindingKind.PERIOD_GAP,
        "cik-0009990006:2025-03-31:2025-09-30",
        "no period end between 2025-03-31 and 2025-09-30",
        issuer_id="cik-0009990006",
    )
    assert again.digest == first.digest
    changed = event_finding(
        EventFindingKind.PERIOD_GAP,
        "cik-0009990006:2025-03-31:2025-09-30",
        "no period end between 2025-03-31 and 2025-10-01",
        issuer_id="cik-0009990006",
    )
    assert changed.digest != first.digest
    labels = event_finding(
        EventFindingKind.FISCAL_LABELS_UNKNOWN, "cik-0009990003:2024-09-30", "none"
    )
    assert (labels.blocking, labels.holds_freeze) == (False, False)


CITATION = OverrideCitation(
    source_id="sec-edgar",
    url="https://www.sec.gov/Archives/edgar/data/9990001/000999000125000009/0009990001-25-000009-index.htm",
)
SIGNED = {
    "rationale": "Reviewed.",
    "reviewer": "A Reviewer",
    "recorded_on": date(2026, 9, 28),
}


@pytest.mark.parametrize(
    ("fields", "foreign"),
    [
        (
            {
                "kind": EventOverrideKind.SET_RELEASE_FILING,
                "event_id": "cik-0009990001:2025-02-28",
                "accession": "0009990001-25-000009",
                "citations": (CITATION,),
            },
            {"finding_id": "period_gap:cik-0009990006:2024-07-01:2024-10-15"},
        ),
        (
            {
                "kind": EventOverrideKind.RETAIN_UNRESOLVED,
                "event_id": "cik-0009990005:2025-06-27",
                "reason": EventReason.NO_RELEASE_FILING,
            },
            {"accession": "0009990005-25-000020"},
        ),
        (
            {
                "kind": EventOverrideKind.ACKNOWLEDGE,
                "finding_id": "period_gap:cik-0009990006:2025-03-31:2025-09-30",
                "finding_digest": "0" * 64,
            },
            {"event_id": "cik-0009990006:2025-03-31"},
        ),
    ],
    ids=["set-release-filing", "retain-unresolved", "acknowledge"],
)
def test_each_override_sets_exactly_its_targets(fields, foreign) -> None:
    assert (
        EventOverride(override_id="decision-1", **fields, **SIGNED).kind
        is (fields["kind"])
    )
    with pytest.raises(ValidationError, match="exactly"):
        EventOverride(override_id="decision-1", **fields, **foreign, **SIGNED)


def test_setting_a_release_filing_cites_it() -> None:
    with pytest.raises(ValidationError, match="cites"):
        EventOverride(
            override_id="decision-1",
            kind=EventOverrideKind.SET_RELEASE_FILING,
            event_id="cik-0009990001:2025-02-28",
            accession="0009990001-25-000009",
            **SIGNED,
        )


def test_only_an_ambiguous_reason_is_retained() -> None:
    with pytest.raises(ValidationError, match="ambiguous"):
        EventOverride(
            override_id="decision-1",
            kind=EventOverrideKind.RETAIN_UNRESOLVED,
            event_id="cik-0009990005:2025-06-27",
            reason=EventReason.NOT_MEMBER_AT_PUBLICATION,
            **SIGNED,
        )


def test_an_overrides_file_holds_one_override_of_each_kind_per_event() -> None:
    """A set release filing may leave an event ambiguous, so one event may carry a
    ``set_release_filing`` and a ``retain_unresolved``, but never two of either."""
    retain = EventOverride(
        override_id="keep",
        kind=EventOverrideKind.RETAIN_UNRESOLVED,
        event_id="cik-0009990005:2025-06-27",
        reason=EventReason.SAME_DAY_TRANSITION,
        **SIGNED,
    )
    chosen = EventOverride(
        override_id="choose",
        kind=EventOverrideKind.SET_RELEASE_FILING,
        event_id="cik-0009990005:2025-06-27",
        accession="0009990005-25-000031",
        citations=(CITATION,),
        **SIGNED,
    )
    EventOverridesFile(schema_version=1, overrides=(chosen, retain))
    with pytest.raises(ValidationError, match="override_id repeated"):
        EventOverridesFile(schema_version=1, overrides=(retain, retain))
    twice = retain.model_copy(update={"override_id": "keep-again"})
    with pytest.raises(ValidationError, match="event_id repeated in one kind"):
        EventOverridesFile(schema_version=1, overrides=(retain, twice))


def manifest(**changes: object) -> EventManifest:
    definition = {
        "corpus_id": "djia-synthetic",
        "event_manifest_version": 1,
        "universe_id": "djia-synthetic",
        "universe_version": 1,
        "universe_operative_hash": "1" * 64,
        "discovery_policy_version": "release-id/1",
        "eligibility_policy_version": "eligibility/1",
        "public_information_cutoff": date(2026, 9, 22),
        "content_hash": "0" * 64,
        "created_at": datetime(2026, 9, 28, tzinfo=UTC),
    }
    rows = changes.pop("rows", (row(),))
    return EventManifest(
        schema_version=1,
        definition=EventManifestDefinition(**(definition | changes)),
        rows=rows,
        findings=(),
        overrides=(),
    )


def test_the_hash_leaves_out_the_version_the_time_and_the_universe_version() -> None:
    """P7-2: a cohort version with unchanged facts never re-versions the events."""
    first = content_hash(manifest())
    assert first == content_hash(
        manifest(
            event_manifest_version=2,
            universe_version=2,
            content_hash="f" * 64,
            created_at=datetime(2026, 10, 1, tzinfo=UTC),
        )
    )
    assert first != content_hash(manifest(universe_operative_hash="2" * 64))
    assert first != content_hash(manifest(rows=(row(reported_fiscal_year=2024),)))


def test_rows_are_unique_and_sorted_by_event_id() -> None:
    later = row(
        event_id="cik-0009990001:2024-12-31",
        period_end=date(2024, 12, 31),
        periodic_accession="0009990001-25-000003",
    )
    manifest(rows=(row(), later))
    with pytest.raises(ValidationError, match="sorted"):
        manifest(rows=(later, row()))
    with pytest.raises(ValidationError, match="sorted"):
        manifest(rows=(row(), row()))
