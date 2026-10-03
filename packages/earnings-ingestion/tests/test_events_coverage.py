"""The D4 coverage report (the Stage 6 spec, §The coverage report; plan 9): the
observed count of each state over the pilot's documents, each missing failure class
as a gap, the overrides applied, and only the runs it names."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.events.coverage import (
    AppliedOverride,
    CoverageGap,
    build_coverage,
    load_coverage,
    parsed_documents,
    pilot_pin,
)
from earnings_ingestion.events.fixture import (
    ACQUISITION,
    ACQUISITION_RUN,
    COHORT_MANIFEST,
    FIXTURE_DIR,
    load_transitions,
)
from earnings_ingestion.events.freeze import load_event_manifest, serialize
from earnings_ingestion.events.pilot import load_pilot
from earnings_ingestion.events.states import (
    AttemptOutcome,
    DocumentState,
    ExhibitAttempt,
    ExhibitChoice,
    StateTransition,
)

REPO = Path(__file__).resolve().parents[3]
ROOT = REPO / FIXTURE_DIR
LATER = datetime(2026, 9, 30, 9, 0, tzinfo=UTC)
UNAVAILABLE = "cik-0009990003:2025-06-30:release"


@pytest.fixture(scope="module")
def synthetic():
    universe = load_manifest(REPO / COHORT_MANIFEST)
    pilot = load_pilot(ROOT / "pilot-v1.json", universe)
    events = load_event_manifest(ROOT / "events-v1.json")
    return (
        pilot,
        pilot_pin(pilot, events, universe),
        load_transitions(ROOT / ACQUISITION),
    )


def test_the_synthetic_acquisition_is_counted_by_state(synthetic) -> None:
    pilot, pin, transitions = synthetic
    report = build_coverage(pilot, pin, transitions)
    assert report.documents == len(pilot.rows) == 27
    assert {c.state: c.count for c in report.states if c.count} == {
        DocumentState.PARSED: 24,
        DocumentState.UNAVAILABLE: 2,
        DocumentState.FAILED: 1,
    }
    assert report.gaps == (CoverageGap(state=DocumentState.RESTRICTED),)
    assert report.overrides == ()
    assert report.run_ids == (ACQUISITION_RUN,)
    assert report.no_theme == ()


def test_a_pilot_holding_no_failure_class_reports_three_gaps(synthetic) -> None:
    pilot, pin, transitions = synthetic
    report = build_coverage(pilot, pin, [*transitions, *_override_run(transitions)])
    assert report.count(DocumentState.UNAVAILABLE) == 1
    assert [gap.state for gap in report.gaps] == [DocumentState.RESTRICTED]
    assert report.overrides == (
        AppliedOverride(
            override_id="release-doc-crvd-2025-06-30",
            document_id=UNAVAILABLE,
            verdict=AttemptOutcome.NOT_CONFIRMED,
        ),
    )
    assert report.run_ids == (ACQUISITION_RUN, "acquire-override")

    # A pilot holding only the 24 rows already parsed: none unavailable, restricted,
    # or failed, so build_coverage reports all three failure classes as gaps.
    clean_ids = parsed_documents(transitions, pin.pilot_hash)
    clean_pilot = pilot.model_copy(
        update={"rows": tuple(row for row in pilot.rows if row.event_id in clean_ids)}
    )
    clean_report = build_coverage(clean_pilot, pin, transitions)
    assert clean_report.documents == len(clean_ids) == 24
    assert [gap.state for gap in clean_report.gaps] == [
        DocumentState.UNAVAILABLE,
        DocumentState.RESTRICTED,
        DocumentState.FAILED,
    ]


def test_a_rebuild_reads_only_the_runs_it_names(synthetic) -> None:
    pilot, pin, transitions = synthetic
    first = build_coverage(pilot, pin, transitions)
    later = [*transitions, *_later_run(transitions)]
    assert build_coverage(pilot, pin, later, run_ids=first.run_ids) == first
    assert build_coverage(pilot, pin, later).count(DocumentState.PARTIAL) == 1


def test_an_unknown_run_and_another_pilot_are_refused(synthetic) -> None:
    pilot, pin, transitions = synthetic
    with pytest.raises(ValueError, match="no transition under the pilot in run x"):
        build_coverage(pilot, pin, transitions, run_ids=["x"])
    other = pin.model_copy(update={"pilot_hash": "0" * 64})
    with pytest.raises(ValueError, match="the pin names another pilot"):
        build_coverage(pilot, other, transitions)


def test_a_document_with_no_state_is_refused(synthetic) -> None:
    pilot, pin, transitions = synthetic
    kept = [t for t in transitions if t.document_id != UNAVAILABLE]
    with pytest.raises(ValueError, match=f"{UNAVAILABLE} has no state"):
        build_coverage(pilot, pin, kept)


def test_a_frozen_report_loads_and_a_tampered_one_is_refused(
    synthetic, tmp_path
) -> None:
    pilot, pin, transitions = synthetic
    report = build_coverage(pilot, pin, transitions)
    path = tmp_path / "coverage-v1.json"
    path.write_bytes(serialize(report))
    assert load_coverage(path) == report
    data = json.loads(path.read_text(encoding="utf-8"))
    data["gaps"] = []
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="does not hash to its content_hash"):
        load_coverage(path)


def test_the_pin_holds_the_chain(synthetic) -> None:
    _, pin, _ = synthetic
    assert pin.pilot_id == "djia-synthetic-pilot"
    assert pin.pilot_hash == (
        "71c6ac4fabc3b7e727da88b4ee74048a0ee3559c8e5ce26c02227376d820333c"
    )
    assert pin.events_hash == (
        "438bfec835dee07c119e1b0b24e985fb549dc712564850dc3f73914b557bfe58"
    )


def _last(transitions, document_id: str) -> StateTransition:
    return [t for t in transitions if t.document_id == document_id][-1]


def _override_run(transitions) -> list[StateTransition]:
    """The unavailable document taken to parsed by an override whose attempt keeps
    ``not_confirmed``, as Disney's was in the real acquisition."""
    last = _last(transitions, UNAVAILABLE)
    common = {
        "document_id": last.document_id,
        "event_id": last.event_id,
        "run_id": "acquire-override",
        "recorded_at": LATER,
        "pilot_id": last.pilot_id,
        "pilot_version": last.pilot_version,
        "pilot_hash": last.pilot_hash,
        "frozen_accession": last.frozen_accession,
        "accession": last.frozen_accession,
        "exhibit": "crvd-ex992.htm",
        "artifact_sha256": "a" * 64,
        "retrieved_at": LATER,
        "override_id": "release-doc-crvd-2025-06-30",
    }
    attempt = ExhibitAttempt(
        accession=last.frozen_accession,
        filename="crvd-ex992.htm",
        exhibit_type="EX-99.2",
        choice=ExhibitChoice.OVERRIDE,
        outcome=AttemptOutcome.NOT_CONFIRMED,
        artifact_sha256="a" * 64,
    )
    return [
        StateTransition(
            **common,
            sequence=0,
            from_state=DocumentState.UNAVAILABLE,
            to_state=DocumentState.ACQUIRED,
        ),
        StateTransition(
            **common,
            sequence=1,
            from_state=DocumentState.ACQUIRED,
            to_state=DocumentState.PARSED,
            doc_id="0009990003-25-000005_crvd-ex992.htm@walker-1#0123456789abcdef",
            attempts=(attempt,),
        ),
    ]


def _later_run(transitions) -> list[StateTransition]:
    """A later stage's run under the same pilot: one document goes on to partial."""
    parsed = next(t for t in transitions if t.to_state is DocumentState.PARSED)
    return [
        StateTransition(
            **{
                **parsed.model_dump(),
                "run_id": "stage-7",
                "sequence": 0,
                "recorded_at": LATER,
                "from_state": DocumentState.PARSED,
                "to_state": DocumentState.PARTIAL,
                "doc_id": None,
                "attempts": (),
            }
        )
    ]


def test_parsed_documents_keep_their_doc_id_through_later_states(synthetic) -> None:
    _, pin, transitions = synthetic
    found = parsed_documents(transitions, pin.pilot_hash)
    assert len(found) == 24
    assert UNAVAILABLE.removesuffix(":release") not in found
    later = [*transitions, *_later_run(transitions)]
    (moved,) = [t.event_id for t in _later_run(transitions)]
    assert parsed_documents(later, pin.pilot_hash)[moved] == found[moved]
    overridden = parsed_documents(
        [*transitions, *_override_run(transitions)], pin.pilot_hash
    )
    assert overridden[UNAVAILABLE.removesuffix(":release")].startswith(
        "0009990003-25-000005_crvd-ex992.htm@walker-1#"
    )
    assert parsed_documents(transitions, "0" * 64) == {}
