"""Plan B's acquisition (the Stage 5 spec, §Plan B) over the synthetic layer and the
committed synthetic event manifest and pilot, with a fetch that serves the layer's
exhibits and counts each request."""

import json
import shutil
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from earnings_core import sha256_hex
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.cohort.records import OverrideCitation
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.acquire import (
    EXHIBIT_TYPES,
    acquire,
    load_acquisition_overrides,
    planned_requests,
)
from earnings_ingestion.events.build import build_events, load_overrides
from earnings_ingestion.events.fixture import (
    COHORT_MANIFEST,
    FIXTURE_DIR,
    SYNTHETIC_CORPUS,
)
from earnings_ingestion.events.freeze import current_events, load_event_manifest
from earnings_ingestion.events.layer import (
    REGISTRANTS,
    exhibit_bodies,
    filings,
    write_layer,
)
from earnings_ingestion.events.pilot import current_pilot, load_pilot
from earnings_ingestion.events.records import (
    AcquisitionOverride,
    AcquisitionOverridesFile,
)
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
from earnings_ingestion.sec.filing_index import read_filing_index
from earnings_ingestion.sec.urls import filing_index_url

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


def run(frozen, store, fetch, tmp_path, run_id: str = "acquire-1", overrides=()):
    universe, events, pilot = frozen
    return acquire(
        events,
        pilot,
        universe,
        store,
        fetch,
        overrides=AcquisitionOverridesFile(schema_version=1, overrides=overrides),
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


def save_unreadable(store, served: Served, url: str) -> None:
    """Save the exhibit at ``url``, then change its saved bytes."""
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


def test_a_saved_exhibit_that_cannot_be_read_is_a_problem_never_fetched_again(
    frozen, store, tmp_path
) -> None:
    served = Served()
    first = frozen[2].rows[0].event_id
    row = next(row for row in frozen[1].rows if row.event_id == first)
    folder = row.release_accession.replace("-", "")
    url = next(url for url in served.bodies if f"/{folder}/" in url)
    save_unreadable(store, served, url)
    result = run(frozen, store, served, tmp_path)
    (problem,) = result.problems
    assert problem.startswith(f"{url}: ")
    assert "repair the store by hand" in problem
    assert url not in served.requested
    assert result.states[f"{first}:release"].to_state is E


ACME_Q3 = "cik-0009990001:2025-08-31"
"""Acme's release for 2025-08-31: its first named exhibit is not confirmed, and its
second is."""


def test_a_problem_after_the_first_exhibit_leaves_the_state_the_run_recorded(
    frozen, store, tmp_path
) -> None:
    """Acme's first exhibit is fetched and not confirmed, and its second is saved
    but cannot be read: the document stays acquired, as the run file says, to be
    attempted again once the store is repaired (plan 8's final review)."""
    served = Served()
    url = next(u for u in served.bodies if u.endswith("acme-20250925-ex992.htm"))
    save_unreadable(store, served, url)
    result = run(frozen, store, served, tmp_path)
    assert [p for p in result.problems if p.startswith(f"{url}: ")]
    key = f"{ACME_Q3}:release"
    assert result.states[key].to_state is A
    pilot_hash = frozen[2].definition.content_hash
    recorded = current_states(read_runs(tmp_path / "states"), pilot_hash)
    assert recorded[key] == result.states[key]


def test_an_index_page_never_saved_names_discover_not_a_repair(
    frozen, store, tmp_path, monkeypatch
) -> None:
    first = frozen[2].rows[0].event_id
    row = next(row for row in frozen[1].rows if row.event_id == first)
    url = filing_index_url(row.cik, row.release_accession)
    get = SavedResponses.get
    monkeypatch.setattr(
        SavedResponses, "get", lambda self, u: None if u == url else get(self, u)
    )
    result = run(frozen, store, Served(), tmp_path)
    assert f"{url} is not saved: run events discover" in result.problems
    assert result.states[f"{first}:release"].to_state is E


def _change(written: dict, part: str) -> None:
    if part == "no manifest":
        del written["manifest"]
    elif part == "elements":
        written["elements"] = written["elements"][1:]
    else:
        written["manifest"][part] = "0" * 64 if part == "raw_sha256" else "3.14.1"


@pytest.mark.parametrize(
    ("part", "kept"),
    [
        ("python_version", True),
        ("lxml_version", True),
        ("raw_sha256", False),
        ("no manifest", False),
        ("elements", False),
    ],
)
def test_a_canonical_document_already_written_is_kept_when_only_its_environment_differs(
    frozen, store, tmp_path, part, kept
) -> None:
    """A canonical file is named by its ``doc_id``, which hashes its text. One
    written in another environment differs only in the Python, lxml, and libxml2
    versions its manifest records, and is kept; any other difference is a problem,
    and its document stays acquired."""
    first = run(frozen, store, Served(), tmp_path / "first")
    key = f"{ACME_Q3}:release"
    name = f"{first.states[key].doc_id}.json"
    written = json.loads((tmp_path / "first" / "canonical" / name).read_text())
    _change(written, part)
    (tmp_path / "canonical").mkdir()
    (tmp_path / "canonical" / name).write_text(json.dumps(written))
    result = run(frozen, store, Served(), tmp_path)
    assert json.loads((tmp_path / "canonical" / name).read_text()) == written
    if kept:
        assert result.problems == ()
        assert result.states[key].to_state is P
    else:
        (problem,) = result.problems
        assert name in problem
        assert result.states[key].to_state is A


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
            frozen[0],
            store,
            refuse,
            overrides=AcquisitionOverridesFile(schema_version=1),
            states_dir=tmp_path / "states",
            canonical_dir=tmp_path / "canonical",
            run_id="acquire-1",
        )


def document_override(
    store, cik: str, accession: str, exhibit: str, event_id: str, **changes
) -> AcquisitionOverride:
    """A ``set_release_document`` citing its filing's saved index page by the
    Accepted value's locator, as a reviewer would."""
    page = SavedResponses(store).get(filing_index_url(cik, accession))
    accepted = read_filing_index(page.text.body).accepted
    values = {
        "override_id": f"release-doc-{event_id.replace(':', '-')}",
        "kind": "set_release_document",
        "event_id": event_id,
        "accession": accession,
        "exhibit": exhibit,
        "citations": (
            OverrideCitation(
                source_id=SEC_SOURCE_ID,
                url=page.url,
                artifact_sha256=page.artifact.content_sha256,
                locator=page.text.find(accepted),
            ),
        ),
        "rationale": "Chosen by review.",
        "reviewer": "Synthetic Reviewer",
        "recorded_on": date(2026, 9, 29),
    }
    return AcquisitionOverride(**{**values, **changes})


def accession_of(registrant_cik: str, accepted: str) -> str:
    (registrant,) = [r for r in REGISTRANTS if r.cik == registrant_cik]
    (filing,) = [f for f, _ in filings(registrant) if f.accepted == accepted]
    return filing.accession


EASTFIELD_Q1 = "cik-0009990006:2026-03-31"
MISSING = "dyna-20250422-ex991.htm"
"""The one exhibit of the synthetic pilot that SEC never served."""
LATE = "2026-07-17 07:30:00"
"""Eastfield's release for 2026-06-30, accepted after it left on 2026-06-22."""


def test_an_override_takes_another_filing_s_exhibit_and_marks_a_corpus_error(
    frozen, store, tmp_path
) -> None:
    """Eastfield's release for 2026-03-31 failed: its exhibit is an image. A
    reviewer names its next release's exhibit, accepted after Eastfield left, so the
    record marks a corpus_error and fixes nothing in place; the exhibit is taken
    though release-content/1 does not confirm it for the quarter (P8-11)."""
    first = run(frozen, store, Served(), tmp_path)
    assert first.states[f"{EASTFIELD_Q1}:release"].to_state is F
    late = accession_of("0009990006", LATE)
    override = document_override(
        store, "0009990006", late, "efb-20260717-ex991.htm", EASTFIELD_Q1
    )
    corpus = tmp_path / "corpus"
    shutil.copytree(REPO / FIXTURE_DIR, corpus, ignore=shutil.ignore_patterns("raw"))
    served = Served()
    second = run(
        frozen, store, served, tmp_path, run_id="acquire-2", overrides=(override,)
    )
    assert second.problems == ()
    acquired, parsed = second.transitions
    assert (acquired.from_state, acquired.to_state) == (F, A)
    assert (parsed.to_state, parsed.accession, parsed.frozen_accession) == (
        P,
        late,
        frozen[1]
        .rows[[r.event_id for r in frozen[1].rows].index(EASTFIELD_Q1)]
        .release_accession,
    )
    assert {acquired.override_id, parsed.override_id} == {override.override_id}
    assert parsed.corpus_error == acquired.corpus_error
    assert "not_member_at_publication" in parsed.corpus_error
    (attempt,) = parsed.attempts
    assert (attempt.choice, attempt.outcome) == (
        ExhibitChoice.OVERRIDE,
        AttemptOutcome.NOT_CONFIRMED,
    )
    assert served.requested == [
        url for url in served.bodies if url.endswith("efb-20260717-ex991.htm")
    ]
    universe, events, pilot = frozen
    built = build_events(
        universe,
        SavedResponses(store),
        load_overrides(corpus / "overrides.toml"),
        corpus_id=SYNTHETIC_CORPUS,
    )
    assert current_events(built, corpus).manifest == events
    assert current_pilot(corpus, events, universe).manifest == pilot
    third = run(
        frozen, store, refuse, tmp_path, run_id="acquire-3", overrides=(override,)
    )
    assert third.transitions == ()


def test_an_override_of_the_frozen_filing_or_a_member_s_filing_marks_no_error(
    frozen, store, tmp_path
) -> None:
    """Acme's release for 2025-08-31 is its second exhibit, and its release for
    2025-02-28 is named from the 8-K of 2025-03-11, while Acme is a member."""
    second = document_override(
        store,
        "0009990001",
        accession_of("0009990001", "2025-09-25 16:05:00"),
        "acme-20250925-ex992.htm",
        "cik-0009990001:2025-08-31",
    )
    earlier = document_override(
        store,
        "0009990001",
        accession_of("0009990001", "2025-03-11 08:00:00"),
        "acme-20250311-ex991.htm",
        "cik-0009990001:2025-02-28",
    )
    file = AcquisitionOverridesFile(schema_version=1, overrides=(second, earlier))
    assert planned_requests(*frozen[1:], store, tmp_path / "states", file) == (27, 27)
    result = run(frozen, store, Served(), tmp_path, overrides=(second, earlier))
    for override in (second, earlier):
        state = result.states[f"{override.event_id}:release"]
        assert (state.to_state, state.exhibit, state.override_id) == (
            P,
            override.exhibit,
            override.override_id,
        )
        assert state.corpus_error is None
        assert [a.choice for a in state.attempts] == [ExhibitChoice.OVERRIDE]


@pytest.mark.parametrize(
    ("change", "problem"),
    [
        ({"accession": "0009990006-26-000099"}, "is not saved: run events discover"),
        ({"exhibit": "efb-absent.htm"}, "lists no efb-absent.htm"),
        ({"event_id": "cik-0009990002:2024-09-30"}, "is not a pilot event"),
        ({"citations": ("wrong",)}, "no citation is in"),
    ],
)
def test_an_override_that_does_not_check_is_a_problem(
    frozen, store, tmp_path, change, problem
) -> None:
    late = accession_of("0009990006", LATE)
    override = document_override(
        store, "0009990006", late, "efb-20260717-ex991.htm", EASTFIELD_Q1
    )
    if change.get("citations") == ("wrong",):
        wrong = override.citations[0].model_copy(
            update={"url": "https://www.sec.gov/Archives/edgar/data/1/x-index.htm"}
        )
        change = {"citations": (wrong,)}
    changed = override.model_copy(update=change)
    result = run(frozen, store, Served(), tmp_path, overrides=(changed,))
    assert any(problem in found for found in result.problems), result.problems
    if "event_id" not in change:
        assert result.states[f"{EASTFIELD_Q1}:release"].override_id is None


def test_an_override_of_a_parsed_document_is_a_problem(frozen, store, tmp_path) -> None:
    run(frozen, store, Served(), tmp_path)
    override = document_override(
        store,
        "0009990001",
        accession_of("0009990001", "2025-09-25 16:05:00"),
        "acme-20250925-ex991.htm",
        "cik-0009990001:2025-08-31",
    )
    result = run(
        frozen, store, refuse, tmp_path, run_id="acquire-2", overrides=(override,)
    )
    assert result.problems == (
        (
            f"{override.override_id}: cik-0009990001:2025-08-31:release is parsed,"
            " which no override changes"
        ),
    )


EDITED = "an applied override is not edited in place"


def test_an_applied_override_edited_in_place_is_a_problem(
    frozen, store, tmp_path
) -> None:
    """An override that parsed its document, then named another exhibit under the
    same ID, is reported, never silently kept (plan 8's final review)."""
    accession = accession_of("0009990001", "2025-09-25 16:05:00")
    override = document_override(
        store, "0009990001", accession, "acme-20250925-ex992.htm", ACME_Q3
    )
    first = run(frozen, store, Served(), tmp_path, overrides=(override,))
    assert first.states[f"{ACME_Q3}:release"].override_id == override.override_id
    edited = override.model_copy(update={"exhibit": "acme-20250925-ex991.htm"})
    file = AcquisitionOverridesFile(schema_version=1, overrides=(edited,))
    assert planned_requests(*frozen[1:], store, tmp_path / "states", file) == (0, 0)
    again = run(
        frozen, store, refuse, tmp_path, run_id="acquire-2", overrides=(edited,)
    )
    assert again.transitions == ()
    (problem,) = again.problems
    assert problem.startswith(
        f"{override.override_id} was applied to {ACME_Q3} {accession}"
    )
    assert problem.endswith(EDITED)


def test_an_applied_override_moved_to_another_event_is_a_problem(
    frozen, store, tmp_path
) -> None:
    """An applied override's ID keeps one meaning. Eastfield's override parsed its
    document; moved under the same ID to Dyna's unavailable document, which an
    override could change, it is reported, and nothing is fetched or applied (plan
    8's final review)."""
    run(frozen, store, Served(), tmp_path)
    late = accession_of("0009990006", LATE)
    override = document_override(
        store, "0009990006", late, "efb-20260717-ex991.htm", EASTFIELD_Q1
    )
    applied = run(
        frozen, store, Served(), tmp_path, run_id="acquire-2", overrides=(override,)
    )
    assert applied.states[f"{EASTFIELD_Q1}:release"].to_state is P
    dyna = "cik-0009990005:2025-03-28"
    (row,) = [row for row in frozen[1].rows if row.event_id == dyna]
    moved = document_override(
        store,
        "0009990005",
        row.release_accession,
        MISSING,
        dyna,
        override_id=override.override_id,
    )
    again = run(frozen, store, refuse, tmp_path, run_id="acquire-3", overrides=(moved,))
    assert again.transitions == ()
    (problem,) = again.problems
    assert problem.startswith(
        f"{override.override_id} was applied to {EASTFIELD_Q1} {late}"
    )
    assert problem.endswith(EDITED)


def test_an_override_that_failed_edited_in_place_is_a_problem(
    frozen, store, tmp_path
) -> None:
    """Eastfield's image exhibit, named by an override, fails again; naming its
    next release under the same ID is reported, since the failed transition names
    no exhibit and the acquisition before it does."""
    first = run(frozen, store, Served(), tmp_path)
    failed = first.states[f"{EASTFIELD_Q1}:release"]
    (image,) = failed.attempts
    override = document_override(
        store, "0009990006", failed.frozen_accession, image.filename, EASTFIELD_Q1
    )
    second = run(
        frozen, store, refuse, tmp_path, run_id="acquire-2", overrides=(override,)
    )
    assert second.states[f"{EASTFIELD_Q1}:release"].to_state is F
    late = accession_of("0009990006", LATE)
    edited = override.model_copy(
        update={
            "accession": late,
            "exhibit": "efb-20260717-ex991.htm",
            "citations": document_override(
                store, "0009990006", late, "efb-20260717-ex991.htm", EASTFIELD_Q1
            ).citations,
        }
    )
    third = run(
        frozen, store, refuse, tmp_path, run_id="acquire-3", overrides=(edited,)
    )
    assert third.transitions == ()
    (problem,) = third.problems
    assert problem.endswith(EDITED)


def test_the_overrides_file_loads_or_is_empty(tmp_path) -> None:
    assert load_acquisition_overrides(tmp_path / "absent.toml").overrides == ()
    path = tmp_path / "acquisition-overrides.toml"
    path.write_text(
        'schema_version = 1\n\n[[overrides]]\noverride_id = "x"\n'
        'kind = "set_release_document"\nevent_id = "cik-0009990006:2026-03-31"\n'
        'accession = "0009990006-26-000016"\nexhibit = "efb.htm"\n'
        'rationale = "r"\nreviewer = "v"\nrecorded_on = 2026-09-29\n\n'
        '[[overrides.citations]]\nsource_id = "sec-edgar"\nurl = "u"\n',
        encoding="utf-8",
    )
    (loaded,) = load_acquisition_overrides(path).overrides
    assert (loaded.override_id, loaded.recorded_on) == ("x", date(2026, 9, 29))
