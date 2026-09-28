"""Plan B's acquisition (the Stage 5 spec, §Plan B) over the synthetic layer and the
committed synthetic event manifest and pilot, with a fetch that serves the layer's
exhibits and counts each request."""

import shutil
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_core import sha256_hex
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.acquire import (
    EXHIBIT_TYPES,
    acquire,
    planned_requests,
)
from earnings_ingestion.events.build import build_events, load_overrides
from earnings_ingestion.events.fixture import (
    COHORT_MANIFEST,
    FIXTURE_DIR,
    SYNTHETIC_CORPUS,
)
from earnings_ingestion.events.freeze import current_events, load_event_manifest
from earnings_ingestion.events.layer import exhibit_bodies, write_layer
from earnings_ingestion.events.pilot import current_pilot, load_pilot
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.state_table import read_runs
from earnings_ingestion.events.states import (
    AttemptOutcome,
    DocumentState,
    ExhibitChoice,
    MissingReason,
    current_states,
)
from earnings_ingestion.fetch.client import AccessStop, Fetched, UnexpectedResponse
from earnings_ingestion.fetch.records import Retrieval, RetrievalMethod
from earnings_ingestion.fetch.store import ArtifactStore

REPO = Path(__file__).resolve().parents[3]
FETCHED = datetime(2026, 9, 29, 15, 0, tzinfo=UTC)
NOW = datetime(2026, 9, 29, 15, 30, tzinfo=UTC)
E, A, P, F, U = (
    DocumentState.EXPECTED,
    DocumentState.ACQUIRED,
    DocumentState.PARSED,
    DocumentState.FAILED,
    DocumentState.UNAVAILABLE,
)


class Served:
    """SEC as the layer's exhibits: a 404 for any other URL, and a persistent 403
    once ``stop_after`` requests are sent."""

    def __init__(self, stop_after: int | None = None) -> None:
        self.bodies = exhibit_bodies()
        self.stop_after = stop_after
        self.requested: list[str] = []

    def __call__(self, url: str, types) -> Fetched:
        assert types == EXHIBIT_TYPES
        if self.stop_after is not None and len(self.requested) >= self.stop_after:
            raise AccessStop(f"403 persisted for {url}; stopping")
        self.requested.append(url)
        if url not in self.bodies:
            raise UnexpectedResponse(f"HTTP 404 for {url}")
        body, media_type = self.bodies[url]
        retrieval = Retrieval(
            request_url=url,
            final_url=url,
            retrieved_at=FETCHED,
            retrieval_method=RetrievalMethod.HTTP,
            http_status=200,
            media_type=media_type,
            content_type=media_type,
            byte_count=len(body),
            sha256=sha256_hex(body),
        )
        return Fetched(body=body, retrieval=retrieval)


def refuse(url: str, types) -> Fetched:
    raise AssertionError(f"a rerun fetched {url}")


@pytest.fixture(scope="module")
def frozen():
    universe = load_manifest(REPO / COHORT_MANIFEST)
    events = load_event_manifest(REPO / FIXTURE_DIR / "events-v1.json")
    pilot = load_pilot(REPO / FIXTURE_DIR / "pilot-v1.json", universe)
    return universe, events, pilot


@pytest.fixture
def store(tmp_path) -> ArtifactStore:
    """The layer's saved responses, which hold no exhibit."""
    return write_layer(tmp_path / "data" / "raw" / "events", tmp_path).store


def run(frozen, store, fetch, tmp_path, run_id: str = "acquire-1"):
    _, events, pilot = frozen
    return acquire(
        events,
        pilot,
        store,
        fetch,
        states_dir=tmp_path / "states",
        canonical_dir=tmp_path / "canonical",
        run_id=run_id,
        now=lambda: NOW,
    )


def test_a_run_records_each_pilot_event_and_acquires_its_release(
    frozen, store, tmp_path
) -> None:
    served = Served()
    assert planned_requests(*frozen[1:], store, tmp_path / "states") == (27, 28)
    result = run(frozen, store, served, tmp_path)
    states = result.states
    assert len(states) == 27
    assert Counter(t.to_state for t in states.values()) == {P: 24, U: 2, F: 1}
    assert len(served.requested) == 28
    assert len(result.fetched) == 27
    assert len(result.transitions) == 80
    assert result.problems == ()
    assert result.path == tmp_path / "states" / "acquire-1.parquet"
    assert read_runs(tmp_path / "states") == list(result.transitions)
    parsed = [t for t in states.values() if t.to_state is P]
    assert sorted(p.name for p in (tmp_path / "canonical").iterdir()) == sorted(
        f"{t.doc_id}.json" for t in parsed
    )


def test_each_case_comes_to_its_state(frozen, store, tmp_path) -> None:
    states = run(frozen, store, Served(), tmp_path).states

    def attempts(event_id: str):
        return [
            (a.filename, a.choice, a.outcome)
            for a in states[f"{event_id}:release"].attempts
        ]

    acme = states["cik-0009990001:2025-08-31:release"]
    assert (acme.to_state, acme.exhibit) == (P, "acme-20250925-ex992.htm")
    assert attempts("cik-0009990001:2025-08-31") == [
        ("acme-20250925-ex991.htm", ExhibitChoice.NAMED, AttemptOutcome.NOT_CONFIRMED),
        ("acme-20250925-ex992.htm", ExhibitChoice.NAMED, AttemptOutcome.CONFIRMED),
    ]
    eastfield = states["cik-0009990006:2025-09-30:release"]
    assert (eastfield.to_state, eastfield.exhibit) == (P, "efb-20251017-ex99.htm")
    corvid = states["cik-0009990003:2025-06-30:release"]
    assert (corvid.to_state, corvid.missing_reason) == (
        U,
        MissingReason.NO_CONFIRMED_RELEASE,
    )
    assert attempts("cik-0009990003:2025-06-30") == [
        (
            "crvd-20250730-ex9901.htm",
            ExhibitChoice.NAMED,
            AttemptOutcome.NOT_CONFIRMED,
        )
    ]
    assert corvid.attempts[0].detail == "its opening announces no results"
    narrative = states["cik-0009990005:2025-09-26:release"]
    assert narrative.to_state is P
    image = states["cik-0009990006:2026-03-31:release"]
    assert (image.to_state, image.missing_reason, image.failure_reason) == (
        F,
        MissingReason.PARSE_FAILED,
        "no_native_text",
    )
    missing = states["cik-0009990005:2025-03-28:release"]
    assert (missing.from_state, missing.to_state, missing.missing_reason) == (
        E,
        U,
        MissingReason.NOT_FOUND,
    )
    assert missing.attempts[0].outcome is AttemptOutcome.NOT_FETCHED
    assert missing.attempts[0].detail.startswith("HTTP 404 for ")


def test_a_rerun_fetches_nothing_and_records_nothing(frozen, store, tmp_path) -> None:
    first = run(frozen, store, Served(), tmp_path)
    assert planned_requests(*frozen[1:], store, tmp_path / "states") == (0, 0)
    again = run(frozen, store, refuse, tmp_path, run_id="acquire-2")
    assert (again.transitions, again.path) == ((), None)
    assert again.states == first.states


def test_a_persistent_403_stops_the_run_and_leaves_the_rest_expected(
    frozen, store, tmp_path
) -> None:
    """R1.3: the run stops, its transitions so far are written, and a rerun takes up
    each document not yet attempted, fetching nothing twice."""
    stopped = Served(stop_after=3)
    with pytest.raises(AccessStop, match="403 persisted"):
        run(frozen, store, stopped, tmp_path)
    pilot_hash = frozen[2].definition.content_hash
    after = current_states(read_runs(tmp_path / "states"), pilot_hash)
    assert Counter(t.to_state for t in after.values()) == {E: 24, P: 3}
    order = [row.event_id for row in frozen[2].rows]
    assert [after[f"{event}:release"].to_state for event in order[:4]] == [P, P, P, E]
    served = Served()
    rest = run(frozen, store, served, tmp_path, run_id="acquire-2")
    assert Counter(t.to_state for t in rest.states.values()) == {P: 24, U: 2, F: 1}
    assert not set(served.requested) & set(stopped.requested)


def test_a_saved_exhibit_that_cannot_be_read_is_a_problem_never_fetched_again(
    frozen, store, tmp_path
) -> None:
    served = Served()
    first = frozen[2].rows[0].event_id
    row = next(row for row in frozen[1].rows if row.event_id == first)
    folder = row.release_accession.replace("-", "")
    url = next(url for url in served.bodies if f"/{folder}/" in url)
    fetched = served(url, EXHIBIT_TYPES)
    store.put(
        SEC_SOURCE_ID,
        fetched.body,
        fetched.retrieval,
        rights_status=SEC_RIGHTS.rights_status,
        rights_basis=SEC_RIGHTS.rights_basis,
    )
    saved_path = next((store.root / "sec-edgar").glob(f"{fetched.retrieval.sha256}.*"))
    saved_path.write_bytes(b"changed")
    served.requested.clear()
    result = run(frozen, store, served, tmp_path)
    (problem,) = result.problems
    assert problem.startswith(f"{url}: ")
    assert "repair the store by hand" in problem
    assert url not in served.requested
    assert result.states[f"{first}:release"].to_state is E


def test_acquisition_changes_no_frozen_record_and_the_build_still_decides(
    frozen, store, tmp_path
) -> None:
    """P-C7: after acquisition, failures included, the event manifest and the pilot
    are byte-identical, the build still reproduces v1, and the pilot over it is
    still v1, every selected event still selected (P8-4)."""
    corpus = tmp_path / "corpus"
    shutil.copytree(REPO / FIXTURE_DIR, corpus, ignore=shutil.ignore_patterns("raw"))
    before = {path.name: path.read_bytes() for path in corpus.iterdir()}
    result = run(frozen, store, Served(), tmp_path)
    assert {t.to_state for t in result.states.values()} >= {F, U}
    assert {path.name: path.read_bytes() for path in corpus.iterdir()} == before
    universe, events, pilot = frozen
    built = build_events(
        universe,
        SavedResponses(store),
        load_overrides(corpus / "overrides.toml"),
        corpus_id=SYNTHETIC_CORPUS,
    )
    current = current_events(built, corpus)
    assert current.manifest == events
    assert current_pilot(corpus, current.manifest, universe).manifest == pilot
    assert [row.event_id for row in pilot.rows] == list(
        dict.fromkeys(t.event_id for t in result.states.values())
    )


def test_a_pilot_not_frozen_over_the_manifest_is_refused(frozen, store, tmp_path):
    _, events, pilot = frozen
    other = pilot.model_copy(
        update={
            "definition": pilot.definition.model_copy(
                update={"eligible_event_manifest_hash": "0" * 64}
            )
        }
    )
    with pytest.raises(ValueError, match="is not frozen over events-v1.json"):
        acquire(
            events,
            other,
            store,
            refuse,
            states_dir=tmp_path / "states",
            canonical_dir=tmp_path / "canonical",
            run_id="acquire-1",
        )
