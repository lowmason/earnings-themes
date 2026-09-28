"""The real corpus's frozen v1 records load unchanged, and djia-pilot/1 reselects its
pilot, from committed files alone: no freeze, and nothing read from ``data/raw``.

The synthetic corpus cannot stand in for these: the real v1 holds shapes it lacks,
and ``regenerate_event_fixtures.py`` rewrites only the synthetic one. The overrides
file only has to load, since a later plan may add an override to it.
"""

import shutil
from pathlib import Path

import pytest
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.cohort.identity import operative_hash
from earnings_ingestion.events.build import load_overrides
from earnings_ingestion.events.freeze import (
    frozen_event_manifests,
    load_event_evidence,
    load_event_manifest,
    serialize,
)
from earnings_ingestion.events.pilot import frozen_pilots, load_pilot, select_pilot
from earnings_ingestion.events.records import EventStatus, pilot_content_hash

REPO = Path(__file__).resolve().parents[2]
CORPUS = REPO / "config" / "corpus" / "djia-2024q3-2026q2"
UNIVERSE = (
    REPO / "config" / "universe" / "djia" / "manifests" / "djia-2024q3-2026q2-v1.json"
)
EVENTS_V1 = "2348671b3ae8021d644df12ae2f539258670546970c918f8edb231ba1885c3b7"
PILOT_V1 = "3839c800151cc646f11064efdce583f988e511265f8893c90e9a2f2549145926"
OPERATIVE_V1 = "c350923422d9bf2e65a0b5929f4c0d45370458c6a044c3de012a1dfeb116e573"


def test_events_v1_loads_unchanged_with_its_evidence_record() -> None:
    events = load_event_manifest(CORPUS / "events-v1.json")
    definition = events.definition
    assert (definition.corpus_id, definition.event_manifest_version) == (
        "djia-2024q3-2026q2",
        1,
    )
    assert definition.content_hash == EVENTS_V1
    assert definition.universe_operative_hash == OPERATIVE_V1
    assert operative_hash(load_manifest(UNIVERSE)) == OPERATIVE_V1
    evidence = load_event_evidence(CORPUS / "events-v1.evidence.json", events)
    assert evidence.event_manifest_hash == EVENTS_V1
    assert frozen_event_manifests(CORPUS)[0] == events


def test_pilot_v1_loads_unchanged_and_djia_pilot_1_reselects_it() -> None:
    universe = load_manifest(UNIVERSE)
    pilot = load_pilot(CORPUS / "pilot-v1.json", universe)
    assert pilot.definition.content_hash == PILOT_V1
    assert frozen_pilots(CORPUS)[0] == pilot
    events = load_event_manifest(CORPUS / "events-v1.json")
    assert select_pilot(events, universe).content_hash == PILOT_V1


def test_a_pilot_with_a_row_swapped_for_another_eligible_event_is_refused(
    tmp_path,
) -> None:
    """Hashes, seed, and eligibility all check for a pilot whose row is swapped for an
    unselected eligible event, its hash recomputed; only selecting again refuses it
    (PR #6's review, F10)."""
    universe = load_manifest(UNIVERSE)
    events = load_event_manifest(CORPUS / "events-v1.json")
    pilot = load_pilot(CORPUS / "pilot-v1.json", universe)
    taken = {row.event_id for row in pilot.rows}
    other = next(
        row.event_id
        for row in events.rows
        if row.eligibility_status is EventStatus.ELIGIBLE and row.event_id not in taken
    )
    first = pilot.rows[0].model_copy(update={"event_id": other})
    swapped = pilot.model_copy(update={"rows": (first, *pilot.rows[1:])})
    definition = swapped.definition.model_copy(
        update={"content_hash": pilot_content_hash(swapped)}
    )
    swapped = swapped.model_copy(update={"definition": definition})
    shutil.copy(CORPUS / "events-v1.json", tmp_path / "events-v1.json")
    (tmp_path / "pilot-v1.json").write_bytes(serialize(swapped))
    with pytest.raises(ValueError, match="djia-pilot/1 over events-v1.json selects"):
        load_pilot(tmp_path / "pilot-v1.json", universe)


def test_the_overrides_load() -> None:
    assert load_overrides(CORPUS / "overrides.toml").overrides
