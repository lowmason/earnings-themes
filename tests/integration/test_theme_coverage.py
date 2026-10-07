"""V10 integration of declared invented matrix, typed public counting and saved baseline."""

import json
from collections import Counter

import polars as pl
import pytest
from earnings_themes import analysis

from tests.integration import stage10_cases
from tests.integration.stage10_cases import (
    FIXTURES,
    REPO,
    analysis_cases,
    theme_fixtures,
)

no_network = stage10_cases.no_network


@pytest.fixture
def matrix(tmp_path, no_network):
    inputs = analysis_cases.make_inputs(
        theme_fixtures.codebook.__wrapped__(),
        theme_fixtures.template.__wrapped__(),
        tmp_path,
        quote_labels=("U1",),
    )
    case = analysis_cases.make_counting_case(
        inputs.sources.codebook, inputs.coding.record.policy
    )
    scenario = json.loads((FIXTURES / "scenario.json").read_bytes())
    assert scenario["scope"] == "fixture" and len(scenario["cases"]) == 10
    by_event = {r.event_id: r for r in case.coverage if r.doc_type == "release"}
    for row in scenario["cases"]:
        actual = by_event[row["event_id"]]
        assert actual.latest_state == row["processing_state"]
        assert tuple(actual.missing_reasons) == tuple(row["reasons"])
    declaration = case.declarations[0]
    declared = next(r for r in scenario["cases"] if r["finding"] == "no_theme")
    assert (
        declaration.actor_id == declared["actor_id"]
        and declaration.finding == declared["finding"]
    )
    mapping = json.loads((FIXTURES / "family-map-v1.json").read_bytes())
    assert tuple(map(tuple, mapping["memberships"])) == case.families.memberships
    analysis.validate_analysis_tables(case.tables)
    return case


def counts(case):
    return analysis.prevalence(
        case.tables,
        case.tables.frames["coverage"],
        case.book,
        case.policy,
        case.families,
    )


def test_v10_declared_matrix_counts_and_restrictions(matrix):
    result = counts(matrix)
    parent = result.filter(
        (pl.col("view_kind") == "parent")
        & (pl.col("view_id") == "capacity")
        & (pl.col("doc_type") == "release")
    )
    periods = parent.filter(pl.col("unit") == "issuer_period").sort("period_end")
    assert periods.select("numerator", "denominator", "rate").rows() == [
        (1.0, 2, 0.5),
        (0.0, 1, 0.0),
    ]
    window = {
        r["unit"]: (r["numerator"], r["denominator"], r["rate"])
        for r in parent.filter(pl.col("unit") != "issuer_period").iter_rows(named=True)
    }
    assert window == {
        "issuer_window": (1.0, 2, 0.5),
        "firm_quarter": (1.0, 3, 1 / 3),
        "equal_issuer_mean": (0.5, 2, 0.25),
    }
    assert set(result["view_kind"]) == {"direct", "parent", "family"}
    families = result.filter(
        (pl.col("view_kind") == "family")
        & (pl.col("unit") == "issuer_window")
        & (pl.col("doc_type") == "release")
    )
    assert (
        families.select("numerator", "denominator", "rate").rows()
        == [(1.0, 2, 0.5)] * 2
    )
    releases = matrix.tables.frames["coverage"].filter(pl.col("doc_type") == "release")
    assert (
        releases.height == 10
        and releases["available"].sum() == releases["parsed"].sum() == 7
    )
    assert releases["observable"].sum() == 3
    transcripts = matrix.tables.frames["coverage"].filter(
        pl.col("doc_type") == "transcript"
    )
    assert transcripts.height == 10 and transcripts["observable"].sum() == 0
    assert transcripts["document_id"].null_count() == 10
    assert (
        transcripts["missing_reasons"].to_list() == [["transcript_not_in_scope"]] * 10
    )
    assert set(result.filter(pl.col("doc_type") == "transcript")["rate"]) == {None}
    assert set(result.filter(pl.col("doc_type") == "transcript")["reason"]) == {
        "empty_denominator"
    }
    masked = matrix.tables.frames["observations"].filter(
        pl.col("mask_ids").list.len() > 0
    )
    assert masked.height == 1 and masked["headline_eligible"].sum() == 0


def test_v10_evidence_claim_and_copy_inflation_preserves_issuer_votes(matrix):
    original = counts(matrix)
    frames = dict(matrix.tables.frames)
    original_doc = "invented-doc-A-Q1"
    selected = {
        name: [row for row in frame.to_dicts() if row.get("doc_id") == original_doc]
        for name, frame in frames.items()
        if "doc_id" in frame.columns
    }
    identity_columns = (
        "doc_id",
        "quote_id",
        "claim_id",
        "assignment_id",
        "classification_id",
        "decision_id",
        "target_id",
        "novelty_id",
    )
    additions = {name: [] for name in selected}
    copy_docs = []
    for index in range(20):
        identities = {
            row[key]: row[key] + f"-inflated-{index}"
            for rows in selected.values()
            for row in rows
            for key in identity_columns
            if isinstance(row.get(key), str)
        }

        def replace_identity(value, mapping=identities):
            if isinstance(value, str):
                return mapping.get(value, value)
            if isinstance(value, list):
                return [replace_identity(item, mapping) for item in value]
            if isinstance(value, dict):
                return {
                    key: replace_identity(item, mapping) for key, item in value.items()
                }
            return value

        for name, rows in selected.items():
            for row in rows:
                clone = replace_identity(row)
                if name == "copies":
                    clone["representative_doc_id"] = original_doc
                additions[name].append(clone)
        copy_docs.append(identities[original_doc])
    for name, rows in additions.items():
        frames[name] = pl.concat(
            [frames[name], pl.DataFrame(rows, schema=analysis.TABLE_SCHEMAS[name])]
        )
    coverage = frames["coverage"].to_dicts()
    for row in coverage:
        if row["event_id"] == "A-Q1" and row["doc_type"] == "release":
            row["doc_ids"] += copy_docs
    frames["coverage"] = pl.DataFrame(
        coverage, schema=analysis.TABLE_SCHEMAS["coverage"]
    )
    analysis.validate_analysis_tables(analysis.AnalysisTables(frames))
    inflated = analysis.AnalysisTables(frames)
    result = analysis.prevalence(
        inflated, frames["coverage"], matrix.book, matrix.policy, matrix.families
    )
    assert (
        result.select("numerator", "denominator", "rate").rows()
        == original.select("numerator", "denominator", "rate").rows()
    )
    assert matrix.tables.frames["observations"].height == 3


@pytest.mark.parametrize(
    "kind",
    ["unavailable", "restricted", "failed", "empty-observable"],
    ids=["unavailable", "restricted", "failed", "empty-observable"],
)
def test_v10_all_unobservable_has_null_rate(matrix, kind):
    frames = dict(matrix.tables.frames)
    state, availability, available, parsed, reason = {
        "unavailable": ("unavailable", "unavailable", False, False, "not_found"),
        "restricted": ("restricted", "restricted", False, False, "rights_restricted"),
        "failed": ("failed", "unavailable", False, False, "parse_failed"),
        "empty-observable": (
            "partial",
            "available",
            True,
            True,
            "no_theme_unconfirmed",
        ),
    }[kind]
    rows = frames["coverage"].to_dicts()
    for row in rows:
        if row["doc_type"] == "release":
            row.update(
                observable=False,
                available=available,
                parsed=parsed,
                availability=availability,
                latest_state=state,
                missing_reasons=[reason],
            )
    coverage = pl.DataFrame(rows, schema=analysis.TABLE_SCHEMAS["coverage"])
    frames["coverage"] = coverage
    frames["observations"] = pl.DataFrame(schema=analysis.TABLE_SCHEMAS["observations"])
    result = analysis.prevalence(
        analysis.AnalysisTables(frames),
        coverage,
        matrix.book,
        matrix.policy,
        matrix.families,
    )
    assert set(result["denominator"]) == {0} and set(result["rate"]) == {None}
    assert set(result["reason"]) == {"empty_denominator"}


@pytest.mark.parametrize(
    "kind", ["book", "policy", "corpus"], ids=["book", "policy", "corpus"]
)
def test_v10_mixed_selection_refuses(matrix, kind):
    policy = matrix.policy
    book = matrix.book
    if kind == "book":
        book = book.model_copy(update={"content_hash": "f" * 64})
    elif kind == "policy":
        policy = policy.model_copy(update={"mask_policy_version": "changed"})
    else:
        policy = policy.model_copy(update={"population_hash": "f" * 64})
    with pytest.raises(analysis.AnalysisError):
        analysis.prevalence(
            matrix.tables,
            matrix.tables.frames["coverage"],
            book,
            policy,
            matrix.families,
        )


def test_v10_frozen_synthetic_baseline_is_not_extractor_denominator(no_network):
    from earnings_ingestion.cohort.freeze import load_manifest
    from earnings_ingestion.events.fixture import (
        COHORT_MANIFEST,
        FIXTURE_DIR,
        load_transitions,
    )
    from earnings_ingestion.events.pilot import load_pilot
    from earnings_ingestion.events.states import current_states

    universe = load_manifest(REPO / COHORT_MANIFEST)
    pilot = load_pilot(REPO / FIXTURE_DIR / "pilot-v1.json", universe)
    states = current_states(
        load_transitions(REPO / FIXTURE_DIR / "acquisition.json"),
        pilot.definition.content_hash,
    )
    assert Counter(s.to_state.value for s in states.values()) == {
        "parsed": 24,
        "unavailable": 2,
        "failed": 1,
    }
    assert len(states) == 27
