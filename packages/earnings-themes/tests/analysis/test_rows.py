"""Invented projection cases use real upstream gates and safe assertions only."""

from dataclasses import fields, replace

import polars as pl
import pytest
from earnings_core import digest, sha256_hex
from earnings_themes import analysis
from earnings_themes.analysis import (
    TABLE_SCHEMAS,
    AnalysisError,
    CopyAssertion,
    reverify_analysis_inputs,
)

from .cases import NOW


def project(inputs):
    assert callable(getattr(analysis, "build_observations", None)), "projection_missing"
    return analysis.build_observations(reverify_analysis_inputs(inputs))


def upstream_hash(inputs):
    return digest(
        {
            name: {
                f.name: getattr(value, f.name).model_dump(mode="json")
                if f.name == "record"
                else [r.model_dump(mode="json") for r in getattr(value, f.name)]
                for f in fields(value)
            }
            for name, value in (
                ("source", inputs.sources.stored_run),
                ("support", inputs.support),
                ("coding", inputs.coding),
            )
        }
    )


def test_projection_grain_and_all_original_links(analysis_input_factory):
    inputs, root = analysis_input_factory(
        themes=("capacity_expansion", "demand"), quote_labels=("U1",)
    )
    before = upstream_hash(inputs)
    artifact_hashes = {
        name: sha256_hex((root / name / "run.json").read_bytes())
        for name in ("extraction", "coding", "support")
    }
    tables = project(inputs)
    observations = tables.frames["observations"]
    assert observations.height == 2
    assert observations["quote_id"].n_unique() == 1
    assert tables.frames["assignment_claims"].height == 4
    assert set(
        tables.frames["assignment_claims"]
        .select("assignment_id", "doc_id", "claim_id", "decision_id", "target_id")
        .iter_rows()
    ) == {
        (r.assignment_id, r.doc_id, r.claim_id, r.decision_id, r.target_id)
        for r in inputs.coding.assignment_claims
    }
    assert tables.frames["claims"].height == 2
    expected = {
        (c.doc_id, c.claim_id, q)
        for c in inputs.sources.stored_run.claims
        for q in c.quote_ids
    }
    assert (
        set(
            tables.frames["claim_evidence"]
            .select("doc_id", "claim_id", "quote_id")
            .iter_rows()
        )
        == expected
    )
    assert observations["speaker_role"].unique().to_list() == ["not_applicable"]
    assert set(observations["theme_id"]) == {"capacity_expansion", "demand"}
    assert set(observations["policy_scope"]) == {"fixture"}
    assert upstream_hash(inputs) == before
    assert artifact_hashes == {
        name: sha256_hex((root / name / "run.json").read_bytes())
        for name in artifact_hashes
    }


def test_exact_slices_and_repeated_occurrences(analysis_inputs):
    tables = project(analysis_inputs)
    document = analysis_inputs.sources.bundles[0].document
    quotes = tables.frames["quotes"]
    assert quotes.height == 2
    assert quotes["quote_text"].n_unique() == 1
    assert quotes["start"].n_unique() == 2
    assert all(
        row["quote_text"] == document.canonical_text[row["start"] : row["end"]]
        for row in quotes.iter_rows(named=True)
    )
    assert set(tables.frames) == set(TABLE_SCHEMAS)
    assert all(
        frame.schema == pl.Schema(TABLE_SCHEMAS[name])
        for name, frame in tables.frames.items()
    )
    assert all(
        tables.frames[name].height == 0
        for name in ("completions", "coverage", "prevalence", "evidence")
    )
    assert set(tables.frames["claims"]["attempt_id"]) == {
        f"a-{c.window_id}-{c.attempt}"
        for c in analysis_inputs.sources.stored_run.claims
    }


@pytest.mark.parametrize(
    "contribution", ["contextual", "irrelevant"], ids=["contextual", "irrelevant"]
)
def test_unselected_links_survive(analysis_input_factory, contribution):
    inputs, _ = analysis_input_factory(
        contribution=contribution, assignment_action="reject"
    )
    tables = project(inputs)
    assert tables.frames["observations"].height == 0
    assert tables.frames["quotes"].height == 2
    assert tables.frames["claims"].height == 2
    assert tables.frames["claim_evidence"].height == 4
    assert tables.frames["decisions"].height == 2
    assert set(tables.frames["decisions"]["status"]) == {
        d.status for d in inputs.coding.decisions
    }


def test_review_is_not_acceptance(review_analysis_inputs):
    tables = project(review_analysis_inputs)
    assert tables.frames["observations"].height == 0
    assert tables.frames["claim_evidence"].height == 4
    assert set(tables.frames["decisions"]["reason"]) == {"calibration_required"}


def test_unmatched_keeps_novelty_and_originals(analysis_input_factory):
    inputs, _ = analysis_input_factory(themes=())
    tables = project(inputs)
    assert tables.frames["observations"].height == 0
    assert tables.frames["novelty"].height == 2
    assert tables.frames["classifications"].height == 2
    assert tables.frames["claims"].height == 2
    assert tables.frames["claim_evidence"].height == 4


def test_refusals_keep_closed_reason_and_attempt_pointer(analysis_input_factory):
    inputs, _ = analysis_input_factory(quote_labels=("U999",))
    tables = project(inputs)
    assert tables.frames["observations"].height == 0
    refusals = inputs.sources.stored_run.rejections
    assert tables.frames["rejections"].height == len(refusals) > 0
    expected = {
        (
            r.doc_id,
            r.window_id,
            f"a-{r.window_id}-{r.attempt}",
            r.candidate_index,
            r.reason,
        )
        for r in refusals
    }
    assert (
        set(
            tables.frames["rejections"]
            .select("doc_id", "window_id", "attempt_id", "candidate_index", "reason")
            .iter_rows()
        )
        == expected
    )
    assert set(tables.frames["rejections"].columns).isdisjoint(
        {"labels", "detail", "rejection"}
    )


def test_current_masks_remain_audit(analysis_input_factory):
    inputs, _ = analysis_input_factory(masked=True)
    tables = project(inputs)
    observations = tables.frames["observations"]
    assert observations.height == 2
    assert observations["headline_eligible"].sum() == 1
    assert sum(bool(row["mask_ids"]) for row in observations.iter_rows(named=True)) == 1


def test_copy_group_keeps_document_qualified_evidence(analysis_input_factory):
    inputs, _ = analysis_input_factory(documents=2)
    tables = project(inputs)
    observations = tables.frames["observations"]
    assert observations.height == 4
    assert observations.select("doc_id", "quote_id").unique().height == 4
    assert observations["quote_id"].n_unique() == 2
    assert observations["disclosure_group"].n_unique() == 1
    assert observations.select("disclosure_group", "start", "end").unique().height == 2
    assert tables.frames["copies"].height == 2
    assert set(tables.frames["copies"]["status"]) == {"consistent"}
    assert tables.frames["claim_evidence"].height == 8


def test_copy_processing_conflict_retains_all_rows(analysis_input_factory):
    inputs, _ = analysis_input_factory(
        documents=2, themes_by_document=(("capacity_expansion",), ())
    )
    tables = project(inputs)
    assert tables.frames["copies"].height == 2
    assert set(tables.frames["copies"]["status"]) == {"copy_processing_conflict"}
    assert tables.frames["observations"].height == 2
    assert tables.frames["claim_evidence"].height == 8
    assert tables.frames["novelty"].height == 2


def test_reviewed_copy_binds_assertion(analysis_input_factory):
    inputs, _ = analysis_input_factory(
        documents=2, copy_first_text="Invented 🛠 plant expanded."
    )
    members = tuple(sorted((m.doc_id, m.canonical_hash) for m in inputs.metadata))
    assertion = CopyAssertion(
        copy_id="invented-reviewed-copy",
        event_id="A-Q1",
        doc_ids=tuple(d for d, _ in members),
        documents=members,
        method="reviewed_copy",
        evidence_ref="invented-review",
        rule_version="invented-1",
        actor_id="invented-reviewer",
        reviewed_at=NOW,
    )
    tables = project(replace(inputs, copies=(assertion,)))
    assert tables.frames["copies"]["disclosure_group"].n_unique() == 1
    assert set(tables.frames["copies"]["copy_assertion_id"]) == {assertion.copy_id}
    assert set(tables.frames["copies"]["copy_assertion_hash"]) == {
        digest(assertion.model_dump(mode="json"))
    }


def test_stale_bound_does_not_grant_projection(analysis_inputs):
    bound = reverify_analysis_inputs(analysis_inputs)
    snapshot = bound.inputs.canonical_snapshots[0]
    object.__setattr__(snapshot, "data", b"{}")
    assert callable(getattr(analysis, "build_observations", None)), "projection_missing"
    with pytest.raises(AnalysisError, match="^input_changed$"):
        analysis.build_observations(bound)


def test_mixed_assignment_version_refuses(analysis_inputs):
    bound = reverify_analysis_inputs(analysis_inputs)
    row = bound.inputs.coding.assignments[0]
    altered = row.model_copy(
        update={"codebook": row.codebook.model_copy(update={"codebook_version": 1})}
    )
    object.__setattr__(
        bound.inputs.coding,
        "assignments",
        (altered, *bound.inputs.coding.assignments[1:]),
    )
    assert callable(getattr(analysis, "build_observations", None)), "projection_missing"
    with pytest.raises(AnalysisError):
        analysis.build_observations(bound)


@pytest.mark.parametrize("other", ["B-Q1", "A-Q2"], ids=["issuer", "period"])
def test_equal_hash_across_events_is_not_a_copy(analysis_input_factory, other):
    inputs, _ = analysis_input_factory(
        documents=2, event_ids_by_document=("A-Q1", other)
    )
    tables = project(inputs)
    assert tables.frames["copies"]["canonical_hash"].n_unique() == 1
    assert tables.frames["copies"]["disclosure_group"].n_unique() == 2
    assert tables.frames["observations"].height == 4


def test_classifier_incomplete_keeps_original_outcomes(analysis_input_factory):
    inputs, _ = analysis_input_factory(classification_reply="{")
    tables = project(inputs)
    assert tables.frames["observations"].height == 0
    assert tables.frames["classifications"].height == 2
    assert set(tables.frames["classifications"]["status"]) == {"incomplete"}
    assert tables.frames["claims"].height == 2
    assert tables.frames["claim_evidence"].height == 4


def test_support_incomplete_keeps_decisions(analysis_input_factory):
    inputs, _ = analysis_input_factory(contribution="invented-invalid-contribution")
    tables = project(inputs)
    expected = {
        (d.decision_id, d.status, d.reason, d.support_status)
        for d in inputs.coding.decisions
    }
    assert tables.frames["observations"].height == 0
    assert tables.frames["decisions"].height == 2
    assert (
        set(
            tables.frames["decisions"]
            .select("decision_id", "status", "reason", "support_status")
            .iter_rows()
        )
        == expected
    )
    assert set(tables.frames["decisions"]["support_status"]) <= {
        "incomplete",
        "flagged",
        "refused",
    }
    assert tables.frames["claim_evidence"].height == 4


def test_retention_permissions_withhold_text_fields(analysis_input_factory):
    inputs, _ = analysis_input_factory(retain_text=False)
    tables = project(inputs)
    for name, field in (
        ("quotes", "quote_text"),
        ("observations", "quote_text"),
        ("claims", "interpretation"),
    ):
        assert tables.frames[name][field].null_count() == tables.frames[name].height > 0
    assert tables.frames["claims"]["interpretation_hash"].n_unique() == 2
    assert tables.frames["observations"].height == 2


def test_projection_is_offline_and_deterministic(analysis_inputs, monkeypatch):
    from pathlib import Path

    bound = reverify_analysis_inputs(analysis_inputs)
    before = upstream_hash(analysis_inputs)

    def forbidden(*args, **kwargs):
        raise AssertionError("implicit_io_forbidden")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    first = analysis.build_observations(bound)
    second = analysis.build_observations(bound)
    assert all(
        frame.equals(second.frames[name]) for name, frame in first.frames.items()
    )
    assert upstream_hash(analysis_inputs) == before


def test_empty_extraction_does_not_adjudicate_absence(analysis_input_factory):
    inputs, _ = analysis_input_factory(claims=())
    tables = project(inputs)
    assert all(
        tables.frames[name].height == 0
        for name in (
            "quotes",
            "claims",
            "claim_evidence",
            "observations",
            "classifications",
            "decisions",
            "completions",
        )
    )
    assert tables.frames["copies"].height == 1


def test_non_theme_attributes_do_not_populate_theme_id(analysis_input_factory):
    inputs, _ = analysis_input_factory(
        classification_reply={
            "theme_ids": ["capacity_expansion"],
            "attributes": {
                "topic": "invented-topic",
                "sentiment": "positive",
                "direction": "increase",
                "event_type": "invented-cluster",
            },
        }
    )
    assert len(inputs.coding.attributes) == 2
    tables = project(inputs)
    assert set(tables.frames["observations"]["theme_id"]) == {"capacity_expansion"}
    assert tables.frames["observations"].height == 2
