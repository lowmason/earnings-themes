"""Strict analytical boundaries over wholly invented metadata; no source readers."""

import json
from dataclasses import replace
from datetime import date, timedelta, timezone

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
    assert len(counting_case.observations) == 3
    assert len(counting_case.claim_evidence) == 11
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
    assert frame["published_at"].null_count() == 3
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


def intermediate_tables(counting_case):
    frames = dict(counting_case.tables.frames)
    for name in ("completions", "coverage", "prevalence", "evidence"):
        frames[name] = frames[name].clear()
    return r.AnalysisTables(frames)


def test_intermediate_audit_frames_do_not_require_invented_completion(counting_case):
    tables = intermediate_tables(counting_case)
    assert tables.frames["observations"].height > 0
    assert tables.frames["completions"].height == 0
    assert tables.frames["coverage"].height == 0


def test_final_table_gate_requires_completion(counting_case):
    tables = intermediate_tables(counting_case)
    with pytest.raises(AnalysisError, match="^invalid_references$"):
        r.validate_analysis_tables(tables)
    assert (
        r.validate_analysis_tables(counting_case.tables).frames["observations"].height
        > 0
    )


@pytest.mark.parametrize(
    "change",
    ["cross_document", "same_document_claim", "target"],
    ids=["document", "claim", "target"],
)
def test_assignment_links_refuse_borrowed_context(counting_case, change):
    rows = list(counting_case.rows["assignment_claims"])
    first = rows[0]
    donor = (
        next(row for row in rows if row.doc_id != first.doc_id)
        if change == "cross_document"
        else next(
            row
            for row in rows
            if row.doc_id == first.doc_id and row.claim_id != first.claim_id
        )
    )
    updates = {"target_id": donor.target_id}
    if change != "target":
        updates["decision_id"] = donor.decision_id
    rows[0] = first.model_copy(update=updates)
    frames = dict(counting_case.tables.frames)
    frames["assignment_claims"] = pl.DataFrame(
        [row.model_dump() for row in rows],
        schema=r.TABLE_SCHEMAS["assignment_claims"],
        strict=True,
    )
    with pytest.raises(AnalysisError, match="^invalid_references$"):
        r.AnalysisTables(frames)


@pytest.mark.parametrize(
    "change", ["cross_document", "same_document_claim"], ids=["document", "claim"]
)
def test_novelty_refuses_borrowed_classification_context(counting_case, change):
    row = counting_case.rows["novelty"][0]
    classes = counting_case.rows["classifications"]
    donor = classes[0]
    updates = {"classification_id": donor.classification_id}
    if change == "same_document_claim":
        other = next(
            part
            for part in classes
            if part.doc_id == donor.doc_id and part.claim_id != donor.claim_id
        )
        updates.update(doc_id=other.doc_id, claim_id=other.claim_id)
    changed = row.model_copy(update=updates)
    frames = dict(counting_case.tables.frames)
    frames["novelty"] = pl.DataFrame(
        [changed.model_dump()], schema=r.TABLE_SCHEMAS["novelty"], strict=True
    )
    with pytest.raises(AnalysisError, match="^invalid_references$"):
        r.AnalysisTables(frames)


def prevalence_fields(
    counting_case, *, unit="issuer_period", numerator=1.0, role="not_applicable"
):
    return {
        "population_hash": counting_case.policy.population_hash,
        "period_end": date(2025, 3, 31) if unit == "issuer_period" else None,
        "window_start": None if unit == "issuer_period" else date(2025, 3, 31),
        "window_end": None if unit == "issuer_period" else date(2025, 6, 30),
        "doc_type": "release",
        "speaker_role": role,
        "view_kind": "direct",
        "view_id": "capacity",
        "codebook_id": counting_case.book.codebook_id,
        "codebook_version": counting_case.book.codebook_version,
        "codebook_hash": counting_case.book.content_hash,
        "analysis_policy_hash": counting_case.policy.content_hash,
        "family_map_hash": None,
        "unit": unit,
        "numerator": numerator,
        "denominator": 1,
        "rate": numerator,
        "reason": None,
        "expected_count": 1,
        "available_count": 1,
        "parsed_count": 1,
        "observable_count": 1,
        "excluded_count": 0,
        "missing_period_count": 0,
        "restrictions": (),
        "policy_scope": "fixture",
    }


@pytest.mark.parametrize(
    "unit",
    ["issuer_period", "issuer_window", "firm_quarter"],
    ids=["period", "window", "quarter"],
)
def test_count_unit_refuses_fractional_numerator(counting_case, unit):
    with pytest.raises(ValidationError):
        r.PrevalenceRow.model_validate(
            prevalence_fields(counting_case, unit=unit, numerator=0.5)
        )
    assert (
        r.PrevalenceRow.model_validate(
            prevalence_fields(counting_case, unit=unit)
        ).numerator
        == 1.0
    )


def test_equal_issuer_mean_permits_fractional_sum(counting_case):
    assert (
        r.PrevalenceRow.model_validate(
            prevalence_fields(counting_case, unit="equal_issuer_mean", numerator=0.5)
        ).numerator
        == 0.5
    )


def test_prevalence_release_role_is_not_applicable(counting_case):
    with pytest.raises(ValidationError):
        r.PrevalenceRow.model_validate(prevalence_fields(counting_case, role="unknown"))


def test_duplicate_disclosure_has_accepted_and_original_audit_rows(counting_case):
    doc_ids = {"invented-doc-A-Q1", "invented-doc-A-Q1-copy"}
    rows = counting_case.rows
    assert {
        row.doc_id for row in rows["observations"] if row.event_id == "A-Q1"
    } == doc_ids
    assert {row.doc_id for row in rows["quotes"] if row.doc_id in doc_ids} == doc_ids
    assert {
        row.doc_id for row in rows["assignment_claims"] if row.doc_id in doc_ids
    } == doc_ids
    assert (
        len(
            {
                row.disclosure_group
                for row in rows["observations"]
                if row.event_id == "A-Q1"
            }
        )
        == 1
    )
    slot = next(
        row
        for row in counting_case.coverage
        if row.event_id == "A-Q1" and row.doc_type == "release"
    )
    assert set(slot.doc_ids) == doc_ids


def count_only_record(case):
    from datetime import UTC, datetime

    from earnings_core import digest

    h = digest("invented-final-reference-test")
    return r.AnalysisRunRecord(
        run_id="invented-final-reference-test",
        created_at=datetime(2026, 10, 5, tzinfo=UTC),
        scope="fixture",
        audience="local",
        population_hash=case.policy.population_hash,
        event_manifest_hash=h,
        pilot_hash=h,
        universe_hash=h,
        documents=(),
        canonical_manifests=(),
        mask_manifests=(),
        source_run_hash=h,
        coding_run_hash=h,
        support_run_hash=h,
        configuration_hashes=(),
        prompt_hashes=(),
        identity_hashes=(),
        codebook=case.completions[0].codebook,
        assignment_policy=case.completions[0].assignment_policy,
        analysis_policy=case.policy,
        family_map=case.families,
        completion_hashes=(),
        copy_hashes=(),
        validator_version="invented-1",
        software=(),
        lock_hash=h,
        counts_by_state=(),
        counts_by_decision=(),
        counts_by_reason=(),
        raw_verification=(),
        table_hashes=(),
        evidence_hashes=(),
        binding_hash=h,
    )


@pytest.mark.parametrize(
    "container", [r.AnalysisRun, r.StoredAnalysisRun], ids=["run", "stored"]
)
def test_complete_run_container_requires_final_foreign_keys(counting_case, container):
    record = count_only_record(counting_case)
    extra = (
        {}
        if container is r.AnalysisRun
        else {"manifest_hash": record.binding_hash, "published_hashes": ()}
    )
    with pytest.raises(AnalysisError, match="^invalid_references$"):
        container(record=record, tables=intermediate_tables(counting_case), **extra)
    complete = container(record=record, tables=counting_case.tables, **extra)
    assert complete.tables.frames["observations"].height == 3
    assert complete.tables is not counting_case.tables


def test_partial_nonempty_completion_table_is_not_deferred(counting_case):
    frames = dict(counting_case.tables.frames)
    frames["completions"] = frames["completions"].filter(
        pl.col("doc_id") != "invented-doc-A-Q1-copy"
    )
    with pytest.raises(AnalysisError, match="^invalid_references$"):
        r.AnalysisTables(frames)


def test_final_table_gate_rechecks_mutated_frame(counting_case):
    tables = r.AnalysisTables(counting_case.tables.frames)
    frame = tables.frames["observations"]
    frame.replace_column(
        frame.columns.index("schema_version"),
        pl.Series("schema_version", [9] * frame.height, dtype=pl.Int64),
    )
    with pytest.raises(AnalysisError, match="^malformed_record$"):
        r.validate_analysis_tables(tables)


@pytest.mark.parametrize(
    "kind", ["canonical", "authorization"], ids=["canonical", "authorization"]
)
def test_c2_containers_are_frozen_and_repr_false(analysis_inputs, kind):
    from dataclasses import FrozenInstanceError

    value = (
        analysis_inputs.canonical_snapshots[0]
        if kind == "canonical"
        else analysis_inputs.fixture_authorization
    )
    assert "data=" not in repr(value) and "provenance_hash=" not in repr(value)
    with pytest.raises(FrozenInstanceError):
        value.doc_id = "invented-other"


def test_canonical_snapshot_strict_bytes(analysis_inputs):
    snapshot = analysis_inputs.canonical_snapshots[0]
    with pytest.raises(AnalysisError, match="^malformed_record$"):
        r.CanonicalSnapshot(snapshot.doc_id, bytearray(snapshot.data))
    with pytest.raises(AnalysisError, match="^malformed_record$"):
        r.FixtureAuthorization("invented-unapproved", "0" * 64, "0" * 64, "0" * 64)


def test_canonical_snapshot_duplicate_refused(analysis_inputs):
    snapshot = analysis_inputs.canonical_snapshots[0]
    with pytest.raises(AnalysisError, match="^malformed_record$"):
        replace(analysis_inputs, canonical_snapshots=(snapshot, snapshot))


def test_document_level_refusal_preserves_absent_window():
    row = r.RejectionAudit(
        source_run_id="invented-run",
        doc_id="invented-doc",
        window_id=None,
        attempt_id=None,
        candidate_index=None,
        reason="wrong_document",
        element_ids=(),
    )
    frames = dict(r.AnalysisTables.empty().frames)
    frames["rejections"] = pl.DataFrame(
        [row.model_dump()], schema=r.TABLE_SCHEMAS["rejections"]
    )
    tables = r.AnalysisTables(frames)
    assert tables.frames["rejections"]["window_id"].null_count() == 1
    assert tables.frames["rejections"]["attempt_id"].null_count() == 1


def test_declared_no_theme_preserves_unmatched_audit(counting_case):
    row = next(
        r
        for r in counting_case.completions
        if r.processing_state == "completed-no-theme"
    )
    data = row.model_dump()
    data["unmatched_count"] = 2
    checked = r.DocumentCompletion.model_validate(data)
    assert checked.observable and checked.unmatched_count == 2
    for changes in (
        {"declaration_hash": None},
        {"processing_state": "completed", "accepted_count": 1},
        {"processing_state": "partial"},
        {"review_count": 1},
        {"refused_count": 1},
        {"incomplete_count": 1},
        {"traversal_complete": False},
    ):
        with pytest.raises(ValidationError):
            r.DocumentCompletion.model_validate(data | changes)


@pytest.mark.parametrize(
    "value",
    [None, "", "A" * 64, "0" * 63, 0],
    ids=["null", "empty", "uppercase", "short", "integer"],
)
def test_selected_universe_hash_is_required_strict(analysis_inputs, value):
    with pytest.raises(AnalysisError):
        replace(analysis_inputs, selected_universe_hash=value)


def test_selected_universe_field_required(analysis_inputs):
    from dataclasses import fields

    assert "selected_universe_hash" in {f.name for f in fields(type(analysis_inputs))}


def test_selected_universe_hash_refuses_string_subclass(analysis_inputs):
    class HashSubclass(str):
        pass

    with pytest.raises(AnalysisError):
        replace(analysis_inputs, selected_universe_hash=HashSubclass("c" * 64))
