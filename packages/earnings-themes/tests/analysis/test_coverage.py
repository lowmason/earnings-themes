"""Expected-slot coverage uses invented releases and out-of-scope transcripts."""

from earnings_themes import analysis


def test_build_coverage_owns_expected_slots(analysis_inputs):
    assert callable(getattr(analysis, "build_coverage", None)), "coverage_missing"
    bound = analysis.reverify_analysis_inputs(analysis_inputs)
    rows = analysis.build_coverage(bound, analysis.document_completions(bound))
    assert rows.height == 2
    release = rows.filter(rows["doc_type"] == "release")
    transcript = rows.filter(rows["doc_type"] == "transcript")
    assert release["observable"].to_list() == [True]
    assert transcript["observable"].to_list() == [False]
    assert transcript["document_id"].to_list() == [None]
    assert transcript["missing_reasons"].to_list() == [["transcript_not_in_scope"]]


def test_analysis_build_fills_typed_frames(analysis_inputs):
    assert callable(getattr(analysis, "build_analysis", None)), "analysis_missing"
    result = analysis.build_analysis(
        analysis_inputs, analysis_inputs.analysis_policy, None
    )
    assert len(result.tables.frames) == 14
    assert result.tables.frames["completions"].height == 1
    assert result.tables.frames["coverage"].height == 2
    assert result.tables.frames["prevalence"].height > 0
    assert result.record.table_hashes and result.record.completion_hashes


def test_caller_completion_cannot_forge_observability(analysis_inputs):
    import pytest

    bound = analysis.reverify_analysis_inputs(analysis_inputs)
    rows = analysis.document_completions(bound)
    with pytest.raises(analysis.AnalysisError):
        analysis.build_coverage(bound, ())
    with pytest.raises(analysis.AnalysisError):
        analysis.build_coverage(
            bound, (rows[0].model_copy(update={"eligible_units": 1}),)
        )


def test_copy_processing_conflict_excludes_event(analysis_input_factory):
    inputs, _ = analysis_input_factory(
        documents=2, themes_by_document=(("capacity",), ("demand",))
    )
    bound = analysis.reverify_analysis_inputs(inputs)
    completions = analysis.document_completions(bound)
    frame = analysis.build_coverage(bound, completions)
    release = frame.filter(frame["doc_type"] == "release")
    assert release["observable"].to_list() == [False]
    assert "copy_processing_conflict" in release["missing_reasons"][0]


def test_analysis_refuses_caller_policy_change(analysis_inputs):
    import pytest

    with pytest.raises(analysis.AnalysisError):
        analysis.build_analysis(
            analysis_inputs,
            analysis_inputs.analysis_policy.model_copy(
                update={"population_hash": "0" * 64}
            ),
            None,
        )


def test_v10_ten_event_coverage_denominators(counting_case):
    frame = counting_case.tables.frames["coverage"]
    release = frame.filter(frame["doc_type"] == "release")
    assert release.height == 10
    assert sum(release["available"]) == sum(release["parsed"]) == 7
    assert sum(release["observable"]) == 3
    assert release.filter(~release["observable"]).height == 7
    transcript = frame.filter(frame["doc_type"] == "transcript")
    assert (
        transcript.height == 10
        and sum(transcript["observable"]) == sum(transcript["available"]) == 0
    )
    assert transcript["missing_reasons"].to_list() == [["transcript_not_in_scope"]] * 10


def test_frozen_synthetic_acquisition_v10(codebook, template, tmp_path, no_network):
    from collections import Counter
    from pathlib import Path

    import polars as pl
    from earnings_core import sha256_hex
    from earnings_ingestion.cohort.freeze import load_manifest
    from earnings_ingestion.cohort.identity import operative_hash
    from earnings_ingestion.events.fixture import (
        COHORT_MANIFEST,
        FIXTURE_DIR,
        load_transitions,
    )
    from earnings_ingestion.events.freeze import load_event_manifest
    from earnings_ingestion.events.pilot import load_pilot
    from earnings_ingestion.events.states import current_states

    from .cases import make_inputs

    root = Path(__file__).resolve().parents[4]
    frozen_paths = tuple(
        root / FIXTURE_DIR / name
        for name in ("events-v1.json", "pilot-v1.json", "acquisition.json")
    )
    before = tuple(sha256_hex(p.read_bytes()) for p in frozen_paths)
    universe = load_manifest(root / COHORT_MANIFEST)
    events = load_event_manifest(frozen_paths[0])
    pilot = load_pilot(frozen_paths[1], universe)
    assert (
        operative_hash(universe)
        == events.definition.universe_operative_hash
        == pilot.definition.universe_operative_hash
    )
    states = current_states(
        load_transitions(frozen_paths[2]), pilot.definition.content_hash
    )
    assert Counter(s.to_state.value for s in states.values()) == {
        "parsed": 24,
        "unavailable": 2,
        "failed": 1,
    }
    by_event = {e.event_id: e for e in events.rows}
    projected = {
        row.event_id: analysis.ExpectedEvent(
            event_id=e.event_id,
            entity_id=e.issuer_id,
            cik=e.cik,
            period_end=e.period_end,
            fiscal_year=e.reported_fiscal_year,
            fiscal_quarter={"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}.get(
                e.reported_fiscal_quarter
            ),
            eligibility_status=e.eligibility_status.value,
            eligibility_reason=e.eligibility_reason.value,
            membership_assertion_id=e.membership_assertion_id,
            event_manifest_hash=events.definition.content_hash,
            pilot_hash=pilot.definition.content_hash,
        )
        for row in pilot.rows
        for e in (by_event[row.event_id],)
    }
    parsed = tuple(s for s in states.values() if s.to_state.value == "parsed")
    missing = tuple(s for s in states.values() if s.to_state.value != "parsed")
    extras = tuple(
        analysis.AcquisitionStatus(
            event_id=s.event_id,
            document_id=s.document_id,
            state=s.to_state.value,
            missing_reason=s.missing_reason.value,
            failure_reason=s.failure_reason.value if s.failure_reason else None,
            doc_id=None,
            source_document_id=None,
            raw_hash=s.artifact_sha256,
            accession=s.accession,
            exhibit=s.exhibit,
            retrieved_at=s.retrieved_at,
            state_run_id=s.run_id,
            state_schema_version=s.schema_version,
            pilot_hash=s.pilot_hash,
        )
        for s in missing
    )
    selected = tuple(projected[s.event_id] for s in (*parsed, *missing))
    from earnings_themes.support.records import SupportCeilings

    ceilings = SupportCeilings(
        scorer_per_target=40,
        scorer_per_document=40,
        scorer_per_run=200,
        judge_per_target=40,
        judge_per_document=40,
        judge_per_run=200,
        tokens_per_document=200000,
        tokens_per_run=2000000,
    )
    inputs = make_inputs(
        codebook,
        template,
        tmp_path / "invented-synthetic-processing",
        support_ceilings=ceilings,
        selected_universe_hash=operative_hash(universe),
        documents=24,
        claims=("Invented fixture capacity.",),
        quote_labels=("U1",),
        themes=("capacity",),
        extraction_options={"mode": "complete"},
        selected_expected=selected,
        extra_acquisition=extras,
        original_slots=parsed,
    )
    result = analysis.build_analysis(inputs, inputs.analysis_policy, None)
    release = result.tables.frames["coverage"].filter(pl.col("doc_type") == "release")
    assert (
        release.height,
        sum(release["available"]),
        sum(release["parsed"]),
        sum(release["observable"]),
    ) == (27, 24, 24, 24)
    transcript = result.tables.frames["coverage"].filter(
        pl.col("doc_type") == "transcript"
    )
    assert transcript.height == 27 and sum(transcript["observable"]) == 0
    capacity = result.tables.frames["prevalence"].filter(
        (pl.col("view_kind") == "direct")
        & (pl.col("view_id") == "capacity")
        & (pl.col("unit") == "firm_quarter")
        & (pl.col("doc_type") == "release")
    )
    assert capacity.select(
        "numerator", "denominator", "expected_count", "available_count"
    ).rows() == [(24.0, 24, 27, 24)]
    assert before == tuple(sha256_hex(p.read_bytes()) for p in frozen_paths)
    assert no_network == []


def test_separate_invented_restricted_event_has_empty_denominator(
    codebook, template, tmp_path, no_network
):
    import polars as pl
    from earnings_core import canonical_json, digest

    from .cases import HASH, event, make_inputs

    expected = (event("A-Q1"), event("E-Q2"))
    manifest = canonical_json(
        {
            "corpus_id": "stage10-invented",
            "events": [e.model_dump(mode="json") for e in expected],
        }
    )
    (tmp_path / "invented-restricted-manifest.json").write_bytes(manifest)
    expected = tuple(
        e.model_copy(update={"event_manifest_hash": digest(manifest.hex())})
        for e in expected
    )
    restricted = analysis.AcquisitionStatus(
        event_id="E-Q2",
        document_id="invented-restricted-slot",
        state="restricted",
        missing_reason="rights_restricted",
        failure_reason=None,
        doc_id=None,
        source_document_id=None,
        raw_hash=None,
        accession=None,
        exhibit=None,
        retrieved_at=None,
        state_run_id="invented-restricted-run",
        state_schema_version=1,
        pilot_hash=HASH,
    )
    inputs = make_inputs(
        codebook,
        template,
        tmp_path / "invented-restricted",
        selected_expected=expected,
        extra_acquisition=(restricted,),
    )
    result = analysis.build_analysis(inputs, inputs.analysis_policy, None)
    period = result.tables.frames["prevalence"].filter(
        (pl.col("period_end") == expected[1].period_end)
        & (pl.col("unit") == "issuer_period")
        & (pl.col("doc_type") == "release")
    )
    assert set(period["denominator"]) == {0} and set(period["rate"]) == {None}
    assert set(period["reason"]) == {"empty_denominator"}
    assert all("rights_restricted" in r for r in period["restrictions"])
    assert no_network == []


def test_copies_need_consistent_completion_adjudication(analysis_input_factory):
    from .test_completion import declare

    inputs, _ = analysis_input_factory(documents=2, claims=())
    inputs = declare(inputs)
    bound = analysis.reverify_analysis_inputs(inputs)
    coverage = analysis.build_coverage(bound, analysis.document_completions(bound))
    release = coverage.filter(coverage["doc_type"] == "release")
    assert release["observable"].to_list() == [False]
    assert "copy_processing_conflict" in release["missing_reasons"][0]


def test_manifest_uses_selected_universe_only(analysis_inputs):
    result = analysis.build_analysis(
        analysis_inputs, analysis_inputs.analysis_policy, None
    )
    assert result.record.universe_hash == analysis_inputs.selected_universe_hash
    assert (
        result.record.universe_hash
        != analysis_inputs.sources.codebook.discovery_corpus.pin.universe_operative_hash
    )


def test_shared_analysis_run_fixture_is_complete(
    analysis_run, analysis_inputs, family_map
):
    assert len(analysis_run.tables.frames) == 14
    assert analysis_run.record.universe_hash == analysis_inputs.selected_universe_hash
    assert analysis_run.record.family_map == family_map
