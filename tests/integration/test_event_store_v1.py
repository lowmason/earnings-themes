"""The real corpus's frozen records against Stage 5's local store, which only this
machine holds: the test skips without it, so each gate runs it and reads "passed".

``planned_requests`` is what ``events acquire`` states before it sends anything, and
the live gate's count (plan 8, P8-12): the pilot's 40 release filings list 56
``EX-99*`` exhibits, and R1.2's order puts one first in each. That count holds until
the first acquisition saves its exhibits, so the test then skips. Once the live run
is saved, offline replay over the store reproduces each document's state (the Stage 5
spec, §Verification (plan B), item 6).
"""

from pathlib import Path

import pytest
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.events.acquire import (
    OVERRIDES_FILE,
    acquire,
    load_acquisition_overrides,
    planned_requests,
)
from earnings_ingestion.events.freeze import load_event_manifest
from earnings_ingestion.events.pilot import load_pilot
from earnings_ingestion.events.state_table import read_runs
from earnings_ingestion.events.states import StateTransition, current_states
from earnings_ingestion.fetch.responses import UnexpectedResponse
from earnings_ingestion.fetch.store import ArtifactStore

REPO = Path(__file__).resolve().parents[2]
STORE = REPO / "data" / "raw" / "events"
CORPUS = REPO / "config" / "corpus" / "djia-2024q3-2026q2"
UNIVERSE = (
    REPO / "config" / "universe" / "djia" / "manifests" / "djia-2024q3-2026q2-v1.json"
)
STATES = REPO / "data" / "runs" / "events" / "states"


def test_the_first_acquisition_sends_40_to_56_requests(tmp_path) -> None:
    if not (STORE / "sec-edgar").is_dir():
        pytest.skip("data/raw/events is not saved here: each gate runs this test")
    if any(STATES.glob("*.parquet")):
        pytest.skip(
            "the first acquisition has run: docs/verification/djia-events.md"
            " records its count"
        )
    events = load_event_manifest(CORPUS / "events-v1.json")
    pilot = load_pilot(CORPUS / "pilot-v1.json", load_manifest(UNIVERSE))
    store = ArtifactStore(STORE, REPO)
    assert planned_requests(events, pilot, store, tmp_path / "states") == (40, 56)


def facts(state: StateTransition) -> tuple:
    return (
        state.to_state,
        state.missing_reason,
        state.failure_reason,
        state.accession,
        state.exhibit,
        state.artifact_sha256,
        state.doc_id,
        state.override_id,
    )


def test_offline_replay_reproduces_the_live_acquisition(tmp_path) -> None:
    """Each pilot document's state, replayed from the saved store with every
    exhibit never saved refused as SEC refused it, is the state the live runs left."""
    if not any(STATES.glob("*.parquet")):
        pytest.skip("no acquisition run is saved here: the live gate runs this test")
    universe = load_manifest(UNIVERSE)
    events = load_event_manifest(CORPUS / "events-v1.json")
    pilot = load_pilot(CORPUS / "pilot-v1.json", universe)
    live = current_states(read_runs(STATES), pilot.definition.content_hash)

    def unsaved(url: str, types) -> None:
        raise UnexpectedResponse(f"{url} is not saved")

    replay = acquire(
        events,
        pilot,
        universe,
        ArtifactStore(STORE, REPO),
        unsaved,
        overrides=load_acquisition_overrides(CORPUS / OVERRIDES_FILE),
        states_dir=tmp_path / "states",
        canonical_dir=tmp_path / "canonical",
        run_id="replay",
    )
    assert replay.fetched == ()
    assert {key: facts(state) for key, state in replay.states.items()} == {
        key: facts(state) for key, state in live.items()
    }
