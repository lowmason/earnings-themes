"""The real corpus's frozen records against Stage 5's local store, which only this
machine holds: the test skips without it, so each gate runs it and reads "passed".

``planned_requests`` is what ``events acquire`` states before it sends anything, and
the live gate's count (plan 8, P8-12): the pilot's 40 release filings list 56
``EX-99*`` exhibits, and R1.2's order puts one first in each. That count holds until
the first acquisition saves its exhibits, so the test then skips. Once the live run
is saved, offline replay over the store reproduces each document's acquisition state
(the Stage 5 spec, §Verification (plan B), item 6). The theme workflow appends schema-2
processing records to the same state table later, and the replay test leaves them out.

Two more tests read the saved store (plan 26, Task 10): the store rebuilds events v1
to its frozen content hash with nothing holding the freeze, and every citation in v1's
evidence record verifies against it. Each skips without the store. A failure prints
hashes, counts, and IDs only, and cuts a problem line short, since a line can quote
saved text and the log is public.
"""

from collections.abc import Sequence
from pathlib import Path

import pytest
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.events.acquire import (
    OVERRIDES_FILE,
    acquire,
    load_acquisition_overrides,
    planned_requests,
)
from earnings_ingestion.events.build import (
    CORPUS_ID,
    EventBuild,
    EventBuildError,
    build_events,
    load_overrides,
)
from earnings_ingestion.events.evidence import check_evidence
from earnings_ingestion.events.freeze import load_event_evidence, load_event_manifest
from earnings_ingestion.events.pilot import load_pilot
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.state_table import read_runs
from earnings_ingestion.events.states import (
    ProcessingTransition,
    StateTransition,
    current_states,
)
from earnings_ingestion.fetch.responses import UnexpectedResponse
from earnings_ingestion.fetch.store import ArtifactStore

REPO = Path(__file__).resolve().parents[2]
STORE = REPO / "data" / "raw" / "events"
CORPUS = REPO / "config" / "corpus" / "djia-2024q3-2026q2"
UNIVERSE = (
    REPO / "config" / "universe" / "djia" / "manifests" / "djia-2024q3-2026q2-v1.json"
)
STATES = REPO / "data" / "runs" / "events" / "states"
SHOWN = 10
"""How many problem lines a failure prints."""
WIDTH = 100
"""How many characters of each problem line a failure prints."""


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
    """Each pilot document's acquisition state, replayed from the saved store with
    every exhibit never saved refused as SEC refused it, is the state the live runs
    left. The schema-2 processing records that a later stage appends are left out."""
    if not any(STATES.glob("*.parquet")):
        pytest.skip("no acquisition run is saved here: the live gate runs this test")
    universe = load_manifest(UNIVERSE)
    events = load_event_manifest(CORPUS / "events-v1.json")
    pilot = load_pilot(CORPUS / "pilot-v1.json", universe)
    acquisition_records = [
        record
        for record in read_runs(STATES)
        if not isinstance(record, ProcessingTransition)
    ]
    live = current_states(acquisition_records, pilot.definition.content_hash)

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


def needs_store() -> None:
    if not (STORE / "sec-edgar").is_dir():
        pytest.skip("data/raw/events is not saved here: each gate runs this test")


def described(problems: Sequence[str]) -> str:
    """The count, then each of the first ``SHOWN`` problems cut to ``WIDTH``
    characters. A problem line can quote saved text, so it is never printed whole."""
    lines = "".join(f"\n  {problem[:WIDTH]}" for problem in problems[:SHOWN])
    return f"{len(problems)} problems, the first {min(len(problems), SHOWN)}:{lines}"


def rebuilt() -> EventBuild:
    """Events v1's build over the saved store, the committed overrides, and universe
    v1. The failure is raised outside the ``except`` block, so that pytest chains no
    ``EventBuildError``, whose message holds every problem line whole."""
    try:
        return build_events(
            load_manifest(UNIVERSE),
            SavedResponses(ArtifactStore(STORE, REPO)),
            load_overrides(CORPUS / "overrides.toml"),
            corpus_id=CORPUS_ID,
        )
    except EventBuildError as error:
        problems = error.problems
    pytest.fail(
        "the saved store no longer builds events v1: "
        f"{described(problems)}\nrun `earnings-pipeline events build` for the full lines"
    )


def test_events_v1_rebuilds_from_the_saved_store() -> None:
    """The build holds nothing back from the freeze, as ``events freeze`` decides it,
    and its content hash is the frozen version's. A moved hash is a finding, never a
    reason to freeze again."""
    needs_store()
    frozen = load_event_manifest(CORPUS / "events-v1.json").definition.content_hash
    built = rebuilt()
    if built.holds_freeze:
        pytest.fail(
            "the build holds the freeze: "
            f"blocking findings {[f.finding_id for f in built.blocking]}, "
            f"stale overrides {list(built.stale_overrides)}, "
            f"unretained events {[row.event_id for row in built.unretained]}"
        )
    rebuilt_hash = built.content_hash  # not in the assert: pytest prints ``built``
    assert rebuilt_hash == frozen


def test_every_v1_citation_verifies_against_the_saved_store() -> None:
    needs_store()
    events = load_event_manifest(CORPUS / "events-v1.json")
    evidence = load_event_evidence(CORPUS / "events-v1.evidence.json", events)
    problems = check_evidence(evidence, ArtifactStore(STORE, REPO))
    if problems:
        pytest.fail(
            f"v1's evidence record fails against the store: {described(problems)}"
        )
