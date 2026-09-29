"""issuer-time/1 (Stage 6 spec, §The split): each event in exactly one partition,
an issuer's events with its earliest, and fixtures never held out."""

import json
from datetime import date

import pytest
from earnings_themes.records import Pin, RecordError, record_json
from earnings_themes.split import (
    SPLIT_POLICY,
    WINDOWS,
    ExclusionReason,
    Partition,
    SplitEvent,
    load_split,
    quarter,
    split_events,
    split_hash,
    window_of,
)

PIN = Pin(
    pilot_id="synthetic-pilot",
    pilot_version=1,
    pilot_hash="1" * 64,
    events_version=1,
    events_hash="2" * 64,
    universe_version=1,
    universe_operative_hash="3" * 64,
)


def event(issuer: str, period_end: str) -> SplitEvent:
    return SplitEvent(
        event_id=f"cik-{issuer}:{period_end}",
        issuer_id=f"cik-{issuer}",
        period_end=date.fromisoformat(period_end),
    )


def placed(events: list[SplitEvent], **options: object) -> dict[str, tuple]:
    manifest = split_events(events, PIN, **options)
    return {row.event_id: (row.partition, row.reason) for row in manifest.rows}


@pytest.mark.parametrize(
    ("day", "partition"),
    [
        ("2024-07-01", Partition.TRAIN),
        ("2025-06-30", Partition.TRAIN),
        ("2025-07-01", Partition.DEV),
        ("2025-12-31", Partition.DEV),
        ("2026-01-01", Partition.TEST),
        ("2026-06-30", Partition.TEST),
    ],
)
def test_the_window_is_the_quarter_of_the_period_end(day: str, partition) -> None:
    assert window_of(date.fromisoformat(day)) is partition


@pytest.mark.parametrize("day", ["2024-06-30", "2026-07-01"])
def test_a_period_end_outside_the_windows_is_refused(day: str) -> None:
    with pytest.raises(ValueError, match="in no window of issuer-time/1"):
        window_of(date.fromisoformat(day))


def test_a_quarter_is_named_by_its_year_and_number() -> None:
    assert quarter(date(2024, 8, 31)) == "2024Q3"
    assert quarter(date(2026, 2, 1)) == "2026Q1"


def test_each_issuer_keeps_the_partition_of_its_earliest_event() -> None:
    events = [
        event("0000000001", "2024-09-30"),
        event("0000000001", "2025-03-31"),
        event("0000000001", "2026-06-30"),
        event("0000000002", "2025-09-30"),
        event("0000000002", "2025-12-31"),
        event("0000000002", "2026-03-31"),
        event("0000000003", "2026-03-31"),
    ]
    later = (Partition.EXCLUDED, ExclusionReason.ISSUER_IN_EARLIER_PARTITION)
    assert placed(events) == {
        "cik-0000000001:2024-09-30": (Partition.TRAIN, None),
        "cik-0000000001:2025-03-31": (Partition.TRAIN, None),
        "cik-0000000001:2026-06-30": later,
        "cik-0000000002:2025-09-30": (Partition.DEV, None),
        "cik-0000000002:2025-12-31": (Partition.DEV, None),
        "cik-0000000002:2026-03-31": later,
        "cik-0000000003:2026-03-31": (Partition.TEST, None),
    }


def test_a_fixture_event_is_never_held_out() -> None:
    events = [
        event("0000000004", "2024-12-31"),
        event("0000000005", "2025-09-30"),
        event("0000000006", "2026-03-31"),
    ]
    fixtures = {event.event_id for event in events}
    held = (Partition.EXCLUDED, ExclusionReason.FIXTURE_TRAIN_OR_EXCLUDE)
    assert placed(events, fixture_event_ids=fixtures) == {
        "cik-0000000004:2024-12-31": (Partition.TRAIN, None),
        "cik-0000000005:2025-09-30": held,
        "cik-0000000006:2026-03-31": held,
    }


def test_the_issuer_rule_comes_before_the_fixture_rule() -> None:
    events = [event("0000000007", "2024-12-31"), event("0000000007", "2025-09-30")]
    assert placed(events, fixture_event_ids={events[1].event_id})[
        events[1].event_id
    ] == (Partition.EXCLUDED, ExclusionReason.ISSUER_IN_EARLIER_PARTITION)


def test_the_manifest_records_the_rule_the_windows_and_the_pin() -> None:
    manifest = split_events([event("0000000001", "2024-09-30")], PIN)
    assert manifest.split_policy == SPLIT_POLICY == "issuer-time/1"
    assert manifest.split_version == 1
    assert manifest.windows == WINDOWS
    assert manifest.pin == PIN
    assert manifest.content_hash == split_hash(manifest)


def test_the_order_of_the_input_changes_nothing() -> None:
    events = [event("0000000001", "2025-03-31"), event("0000000001", "2024-09-30")]
    assert split_events(events, PIN) == split_events(events[::-1], PIN)


def test_an_event_listed_twice_is_refused() -> None:
    with pytest.raises(ValueError, match="listed twice"):
        split_events([event("0000000001", "2024-09-30")] * 2, PIN)


def test_a_frozen_split_loads_and_a_tampered_one_is_refused(tmp_path) -> None:
    manifest = split_events(
        [event("0000000001", "2024-09-30"), event("0000000002", "2025-09-30")], PIN
    )
    path = tmp_path / "split-v1.json"
    path.write_bytes(record_json(manifest))
    assert load_split(path) == manifest
    data = json.loads(path.read_text(encoding="utf-8"))
    data["rows"][1]["partition"] = "train"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(RecordError, match="does not hash to its content_hash"):
        load_split(path)


def test_an_event_in_two_partitions_is_refused(tmp_path) -> None:
    manifest = split_events([event("0000000001", "2024-09-30")], PIN)
    data = json.loads(record_json(manifest))
    data["rows"].append({**data["rows"][0], "partition": "dev"})
    path = tmp_path / "split-v1.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(RecordError, match="each event is in one"):
        load_split(path)
