"""Strict analytical boundaries over wholly invented metadata; no source readers."""

import json
from dataclasses import replace
from datetime import timedelta, timezone

import polars as pl
import pytest
from earnings_themes.analysis import records as r
from earnings_themes.analysis.problems import AnalysisError
from pydantic import ValidationError


def test_public_identity():
    import earnings_themes.analysis as public

    for name in r.PUBLIC_NAMES:
        assert getattr(public, name) is getattr(r, name)


@pytest.mark.parametrize(
    "change",
    ["extra", "bool_schema", "bool_fiscal", "cik"],
    ids=["extra", "schema", "fiscal", "cik"],
)
def test_expected_event_strict(analysis_inputs, change):
    fields = analysis_inputs.expected[0].model_dump(mode="json")
    if change == "extra":
        fields["unknown"] = "invented"
    elif change == "bool_schema":
        fields["schema_version"] = True
    elif change == "bool_fiscal":
        fields["fiscal_year"] = True
    else:
        fields["cik"] = "1"
    with pytest.raises(ValidationError):
        r.ExpectedEvent.model_validate_json(json.dumps(fields))


def test_family_map_refuses_duplicate_pair(family_map):
    fields = family_map.model_dump(mode="json")
    fields["memberships"] = [fields["memberships"][0]] * 2
    with pytest.raises(ValidationError):
        r.ThemeFamilyMap.model_validate_json(json.dumps(fields))


def test_family_hash_binding(family_map):
    fields = family_map.model_dump(mode="json")
    fields["content_hash"] = "0" * 64
    with pytest.raises(ValidationError):
        r.ThemeFamilyMap.model_validate_json(json.dumps(fields))


def test_family_unknown_and_stale(family_map, counting_case):
    with pytest.raises(AnalysisError):
        family_map.validate_codebook(
            counting_case.book.model_copy(update={"content_hash": "0" * 64})
        )
    fields = family_map.model_dump()
    fields["memberships"] = (("unknown", "operations"),)
    fields["content_hash"] = r.family_map_hash(fields)
    changed = r.ThemeFamilyMap.model_validate(fields)
    with pytest.raises(AnalysisError):
        changed.validate_codebook(counting_case.book)


def test_unknown_fiscal_is_preserved(analysis_inputs):
    event = analysis_inputs.expected[0].model_dump()
    event.update(fiscal_year=None, fiscal_quarter=None)
    assert r.ExpectedEvent.model_validate(event).fiscal_quarter is None


def test_non_utc_metadata_refused(analysis_inputs):
    fields = analysis_inputs.metadata[0].model_dump()
    fields["retrieved_at"] = fields["retrieved_at"].astimezone(
        timezone(timedelta(hours=1))
    )
    with pytest.raises(ValidationError):
        r.DocumentMetadata.model_validate(fields)


@pytest.mark.parametrize(
    "field",
    ["retain_text", "export_text", "retain_raw", "export_raw", "retain_capture"],
)
def test_restricted_rights_cannot_widen(analysis_inputs, field):
    from earnings_core import RightsStatus

    fields = analysis_inputs.metadata[0].model_dump()
    fields.update(
        rights_status=RightsStatus.RESTRICTED,
        retain_text=False,
        export_text=False,
        retain_raw=False,
        export_raw=False,
        retain_capture=False,
        raw_artifact=None,
    )
    fields[field] = True
    with pytest.raises(ValidationError):
        r.DocumentMetadata.model_validate(fields)


def test_inputs_refuse_duplicate_and_stale_snapshots(analysis_inputs):
    snapshot = analysis_inputs.raw_snapshots[0]
    with pytest.raises(AnalysisError):
        replace(analysis_inputs, raw_snapshots=(snapshot, snapshot))
    with pytest.raises(AnalysisError):
        replace(
            analysis_inputs, raw_snapshots=(replace(snapshot, doc_id="invented-stale"),)
        )


def test_inputs_refuse_fiscal_conflict(analysis_inputs):
    metadata = analysis_inputs.metadata[0].model_copy(update={"fiscal_quarter": 2})
    with pytest.raises(AnalysisError):
        replace(analysis_inputs, metadata=(metadata,))


def test_empty_tables_are_exactly_typed():
    tables = r.AnalysisTables.empty()
    assert set(tables.frames) == set(r.TABLE_SCHEMAS)
    assert len(tables.frames) == 14
    assert all(
        frame.height == 0 and frame.schema == pl.Schema(r.TABLE_SCHEMAS[name])
        for name, frame in tables.frames.items()
    )
    with pytest.raises(AnalysisError):
        r.AnalysisTables({})
    frames = dict(tables.frames)
    frames["quotes"] = pl.DataFrame()
    with pytest.raises(AnalysisError):
        r.AnalysisTables(frames)


def test_table_fields_match_models():
    for name, model in r.TABLE_MODELS.items():
        assert set(r.TABLE_SCHEMAS[name]) == set(model.model_fields)
        assert r.TABLE_GRAINS[name]
        assert name in r.TABLE_FOREIGN_KEYS


def test_matrix_denominators_and_outcomes(counting_case):
    assert len(counting_case.coverage) == 20
    release = [row for row in counting_case.coverage if row.doc_type == "release"]
    assert sum(row.observable for row in release) == 3
    assert {row.event_id for row in release if row.observable} == {
        "A-Q1",
        "A-Q2",
        "B-Q1",
    }
    assert sum(row.masked_count for row in release) == 1
    assert {row.event_id for row in release if row.unmatched_count} == {"F-Q1"}
    assert all(
        not row.observable
        for row in counting_case.coverage
        if row.doc_type == "transcript"
    )
    assert len(counting_case.observations) == 2
    assert len(counting_case.claim_evidence) == 9
    assert len(counting_case.copies) == 3


def test_boolean_span_and_count_refused(counting_case):
    for row, field in (
        (counting_case.observations[0], "start"),
        (counting_case.coverage[0], "accepted_count"),
    ):
        data = row.model_dump()
        data[field] = True
        with pytest.raises(ValidationError):
            type(row).model_validate(data)


def test_policy_and_book_hash_required(counting_case):
    for field in ("policy_hash", "codebook_hash"):
        data = counting_case.observations[0].model_dump()
        data.pop(field)
        with pytest.raises(ValidationError):
            r.Observation.model_validate(data)


def test_fixture_completion_cannot_enter_research(counting_case):
    row = counting_case.completions[0]
    data = row.model_dump()
    data["policy_scope"] = "research"
    with pytest.raises(ValidationError):
        r.DocumentCompletion.model_validate(data)


def test_counting_matrix_retains_nonacceptance_audit(counting_case):
    rows = counting_case.rows
    assert len(rows["novelty"]) == 1
    assert {
        row.reason for row in rows["decisions"] if row.doc_id == "invented-doc-H-Q1"
    } == {"assessment_refused", "assessment_flagged", "assessment_incomplete"}
    assert {
        row.reason for row in rows["decisions"] if row.doc_id == "invented-doc-C-Q1"
    } == {"calibration_required"}
    assert {
        row.reason for row in rows["decisions"] if row.doc_id == "invented-doc-G-Q1"
    } == {"policy_reject"}


def test_separate_review_input_binding(review_analysis_inputs):
    assert review_analysis_inputs.assignment_policy is None
    assert review_analysis_inputs.coding.record.policy is None
    assert not review_analysis_inputs.coding.assignments
    assert {d.reason for d in review_analysis_inputs.coding.decisions} == {
        "calibration_required"
    }


def test_tables_refuse_broken_foreign_keys(counting_case):
    frames = dict(counting_case.tables.frames)
    frames["quotes"] = frames["quotes"].clear()
    with pytest.raises(AnalysisError):
        r.AnalysisTables(frames)


def test_tables_refuse_mixed_book(counting_case):
    frames = dict(counting_case.tables.frames)
    frames["observations"] = frames["observations"].with_columns(
        pl.when(pl.col("entity_id") == "B")
        .then(pl.lit("0" * 64))
        .otherwise(pl.col("codebook_hash"))
        .alias("codebook_hash")
    )
    with pytest.raises(AnalysisError):
        r.AnalysisTables(frames)


def test_public_import_has_no_readers_or_adapters():
    import json
    import subprocess
    import sys

    child = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json, sys, earnings_themes.analysis; print(json.dumps(sorted(sys.modules)))",
        ],
        capture_output=True,
        check=True,
        text=True,
    )
    modules = set(json.loads(child.stdout))
    assert {
        "earnings_themes.extraction.local",
        "earnings_themes.coding.local",
        "earnings_themes.support.nli",
    }.isdisjoint(modules)
    assert not any(
        name.startswith(
            ("earnings_ingestion", "earnings_pipeline", "tests.", "packages.")
        )
        for name in modules
    )
    assert {"torch", "transformers", "httpx", "selenium"}.isdisjoint(modules)


def test_tables_validate_required_values(counting_case):
    frames = dict(counting_case.tables.frames)
    frames["quotes"] = frames["quotes"].with_columns(
        pl.lit(None, dtype=pl.String).alias("doc_id")
    )
    with pytest.raises(AnalysisError):
        r.AnalysisTables(frames)


def test_nonempty_null_metadata_keeps_declared_dtype(counting_case):
    frame = counting_case.tables.frames["observations"]
    assert frame["published_at"].null_count() == 2
    assert frame.schema["published_at"] == pl.Datetime("us", "UTC")
    assert frame.schema["fiscal_quarter"] == pl.Int64
    assert frame.schema["mask_ids"] == pl.List(pl.String)


def test_snapshot_payload_is_bytes_only(analysis_inputs):
    raw = analysis_inputs.raw_snapshots[0]
    with pytest.raises(AnalysisError):
        r.RawSnapshot(raw.doc_id, raw.artifact, bytearray(raw.data))


def test_tables_validate_row_schema_version(counting_case):
    frames = dict(counting_case.tables.frames)
    frames["quotes"] = frames["quotes"].with_columns(
        pl.lit(9, dtype=pl.Int64).alias("schema_version")
    )
    with pytest.raises(AnalysisError):
        r.AnalysisTables(frames)


@pytest.mark.parametrize(
    "field", ["canonical_hash", "source_document_id", "canonicalization_version"]
)
def test_inputs_metadata_agrees_with_canonical_identity(analysis_inputs, field):
    metadata = analysis_inputs.metadata[0].model_copy(
        update={field: "0" * 64 if field == "canonical_hash" else "invented-other"}
    )
    with pytest.raises(AnalysisError):
        replace(analysis_inputs, metadata=(metadata,), raw_snapshots=())


def test_inputs_acquisition_agrees_with_metadata(analysis_inputs):
    row = analysis_inputs.acquisition[0].model_copy(update={"raw_hash": "0" * 64})
    with pytest.raises(AnalysisError):
        replace(analysis_inputs, acquisition=(row,))
