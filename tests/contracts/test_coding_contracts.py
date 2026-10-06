"""Blind public coding boundaries retain upstream producer contracts unchanged."""

import io

import earnings_core as core
import polars as pl
import pytest
from earnings_themes import codebook, coding
from earnings_themes.coding import records
from earnings_themes.coding.assignments import assignment_frame, project_assignments
from earnings_themes.coding.decide import (
    AssignmentPolicy,
    DecisionInput,
    DecisionSet,
    decide_assignments,
)
from earnings_themes.coding.input import (
    CodingInput,
    resolve_coding_input,
    reverify_coding_input,
)
from earnings_themes.coding.run import ProposalRun, propose_run
from earnings_themes.coding.store import (
    SCHEMAS,
    read_coding_run,
    reverify_coding_run,
    write_coding_run,
)
from earnings_themes.extraction import records as extraction
from earnings_themes.extraction.records import Claim, Quote
from earnings_themes.records import THEMES_SCHEMA_VERSION, record_json
from earnings_themes.support import records as support
from earnings_themes.support.records import (
    JudgeAnswer,
    ReviewOutcome,
    SupportSources,
    Target,
    ThemeSnapshot,
)


def test_upstream_contracts_are_unchanged():
    assert "theme" not in Claim.model_fields and "codebook" not in Claim.model_fields
    assert "quote_text" not in Quote.model_fields
    assert "quote_ids" not in Target.model_fields and "claim" not in Target.model_fields
    assert "accepted" not in ReviewOutcome.model_fields
    assert "new_theme" not in JudgeAnswer.model_fields
    assert "examples" not in ThemeSnapshot.model_fields


def test_producer_serialization_is_unchanged():
    claim = Claim(
        claim_id="c",
        doc_id="d",
        window_id="w",
        attempt=1,
        claim="Invented claim.",
        quote_ids=("q-0-10",),
    )
    expected = """{
 "attempt": 1,
 "claim": "Invented claim.",
 "claim_id": "c",
 "doc_id": "d",
 "quote_ids": [
  "q-0-10"
 ],
 "schema_version": 1,
 "window_id": "w"
}
"""
    assert record_json(claim) == expected.encode("utf-8")


def test_coding_versions_preserve_upstream_versions():
    assert (core.SCHEMA_VERSION, core.VALIDATOR_VERSION) == (2, "3")
    assert (THEMES_SCHEMA_VERSION, codebook.CODEBOOK_VERSION) == (1, 0)
    assert (extraction.EXTRACTION_SCHEMA_VERSION, extraction.EXTRACTOR_VERSION) == (
        1,
        "pointer-traversal/1",
    )
    assert (support.SUPPORT_SCHEMA_VERSION, support.SUPPORT_VERSION) == (
        1,
        "semantic-support/1",
    )
    assert (coding.CODING_SCHEMA_VERSION, coding.CODING_VERSION) == (
        1,
        "deductive-coding/1",
    )


def test_coding_exports_implemented_seams():
    expected = {
        name: getattr(records, name)
        for name in (
            "CODING_SCHEMA_VERSION",
            "CODING_VERSION",
            "CodingPart",
            "CodingRecord",
            "CodingProblem",
            "CodingError",
            "CodingAttributes",
            "CodingReply",
            "CodingSubject",
            "CodingRequest",
            "CodingPolicy",
            "CodingPolicySnapshot",
            "CodingCeilings",
            "ClassificationRecord",
            "CodingAttempt",
            "ProposalRecord",
            "AttributeRecord",
            "NoveltyItem",
            "ProposalRunRecord",
            "PolicyReference",
            "PolicyVote",
            "AssignmentDecision",
            "Assignment",
            "AssignmentClaimLink",
            "CodingRunRecord",
            "CodingRun",
            "checked",
        )
    }
    expected.update(
        {
            "SupportSources": SupportSources,
            "CodingInput": CodingInput,
            "ProposalRun": ProposalRun,
            "AssignmentPolicy": AssignmentPolicy,
            "DecisionInput": DecisionInput,
            "DecisionSet": DecisionSet,
            "resolve_coding_input": resolve_coding_input,
            "reverify_coding_input": reverify_coding_input,
            "propose_run": propose_run,
            "decide_assignments": decide_assignments,
            "project_assignments": project_assignments,
            "assignment_frame": assignment_frame,
            "write_coding_run": write_coding_run,
            "read_coding_run": read_coding_run,
            "reverify_coding_run": reverify_coding_run,
        }
    )
    assert len(coding.__all__) == len(set(coding.__all__))
    for name, value in expected.items():
        assert name in coding.__all__, name
        assert getattr(coding, name) is value, name
    assert set(coding.__all__) == set(expected)


def test_coding_does_not_export_concrete_bindings_or_caches():
    assert {
        "ClassifierBinding",
        "LocalAdapter",
        "CodingCache",
        "CodingCacheEntry",
        "ScriptedClassifier",
    }.isdisjoint(vars(coding))


@pytest.fixture
def invented_book():
    return support.CodebookReference(
        codebook_id="invented-contract",
        codebook_version=0,
        content_hash=core.digest("invented codebook"),
    )


@pytest.fixture
def invented_policy(invented_book):
    return records.PolicyReference(
        policy_id="invented-fixture-policy",
        policy_hash=core.digest("invented policy"),
        kind="fixture",
        codebook=invented_book,
        classifier_configuration_hash=core.digest("invented classifier configuration"),
        support_configuration_hash=core.digest("invented support configuration"),
        calibration_reference=None,
    )


def invented_review(book, policy=None):
    proposal_hash = core.digest("invented proposals")
    support_hash = core.digest("invented support")
    return records.AssignmentDecision(
        coding_run_id="invented-coding",
        decision_id="decision-"
        + core.digest(
            {
                "target_id": "invented-target",
                "proposal_hash": proposal_hash,
                "support_run_hash": support_hash,
                "policy": policy.model_dump(mode="json")
                if policy is not None
                else None,
            }
        ),
        doc_id="invented-document",
        claim_id="invented-claim",
        theme_id="invented-theme",
        codebook=book,
        target_id="invented-target",
        support_run_hash=support_hash,
        support_status=support.ReviewStatus.ASSESSED,
        flags=(),
        missing=(),
        status="review",
        reason="policy_review" if policy is not None else "calibration_required",
        policy=policy,
        supporting_quote_ids=(),
        proposal_hash=proposal_hash,
        input_hash=core.digest("invented complete input"),
    )


@pytest.mark.parametrize("table", tuple(SCHEMAS))
def test_persisted_coding_schema_covers_every_record_field(table):
    model, schema = SCHEMAS[table]
    assert set(schema) == set(model.model_fields)
    assert schema["schema_version"] == pl.Int64
    assert model.model_fields["schema_version"].default == coding.CODING_SCHEMA_VERSION
    assert pl.DataFrame(schema=schema).schema == schema


def test_nested_coding_schemas_retain_named_structure():
    book = pl.Struct(
        {
            "codebook_id": pl.String,
            "codebook_version": pl.Int64,
            "content_hash": pl.String,
        }
    )
    assert set(book.to_schema()) == set(support.CodebookReference.model_fields)
    assert SCHEMAS["proposals"][1]["target"] == pl.Struct(
        {
            "source_run_id": pl.String,
            "doc_id": pl.String,
            "claim_id": pl.String,
            "theme_id": pl.String,
            "codebook": book,
        }
    )
    attributes = SCHEMAS["attributes"][1]["attributes"]
    policy = SCHEMAS["decisions"][1]["policy"]
    assert attributes.to_schema() == {
        name: pl.String for name in records.CodingAttributes.model_fields
    }
    assert set(policy.to_schema()) == set(records.PolicyReference.model_fields)
    assert policy.to_schema()["codebook"] == book
    for table in ("classifications", "decisions", "assignments", "novelty"):
        assert SCHEMAS[table][1]["codebook"] == book


@pytest.mark.parametrize("kind", ["no-policy", "fixture-policy", "missing-assessment"])
def test_nested_nullable_decisions_round_trip_parquet(
    invented_book, invented_policy, kind
):
    policy = invented_policy if kind == "fixture-policy" else None
    record = invented_review(invented_book, policy)
    if kind == "missing-assessment":
        record = records.checked(
            record.model_copy(
                update={
                    "support_status": None,
                    "reason": "missing_assessment",
                    "missing": ("missing_assessment",),
                }
            ),
            records.AssignmentDecision,
        )
    model, schema = SCHEMAS["decisions"]
    frame = pl.DataFrame([record.model_dump(mode="json")], schema=schema)
    buffer = io.BytesIO()
    frame.write_parquet(buffer)
    restored = pl.read_parquet(io.BytesIO(buffer.getvalue()))
    assert restored.schema == schema
    row = restored.to_dicts()[0]
    assert row["status"] == "review" and row["supporting_quote_ids"] == []
    if kind == "fixture-policy":
        assert row["policy"]["calibration_reference"] is None
        assert row["policy"]["kind"] == "fixture"
    else:
        assert row["policy"] is None
        if kind == "missing-assessment":
            assert row["support_status"] is None
            assert row["reason"] == "missing_assessment"
        else:
            assert row["reason"] == "calibration_required"
    assert records.checked(row, model) == record


def test_nullable_annotations_stay_separate_from_the_source_claim():
    record = records.AttributeRecord(
        coding_run_id="invented-coding",
        doc_id="invented-document",
        claim_id="invented-claim",
        input_hash=core.digest("invented input"),
        attributes=records.CodingAttributes(),
    )
    model, schema = SCHEMAS["attributes"]
    frame = pl.DataFrame([record.model_dump(mode="json")], schema=schema)
    buffer = io.BytesIO()
    frame.write_parquet(buffer)
    row = pl.read_parquet(io.BytesIO(buffer.getvalue())).to_dicts()[0]
    assert row["attributes"] == {
        "topic": None,
        "sentiment": None,
        "direction": None,
        "event_type": None,
    }
    assert "theme_id" not in row["attributes"] and "claim" not in row
    assert records.checked(row, model) == record


def test_no_policy_review_cannot_be_promoted_to_acceptance(invented_book):
    review = invented_review(invented_book)
    assert review.policy is None and review.supporting_quote_ids == ()
    with pytest.raises(records.CodingError, match="^malformed_record$"):
        records.checked(
            review.model_copy(update={"status": "accepted", "reason": "policy_accept"}),
            records.AssignmentDecision,
        )


def test_fixture_and_calibrated_policy_bindings_remain_distinct(invented_policy):
    assert invented_policy.calibration_reference is None
    for update in (
        {"kind": "calibrated"},
        {"calibration_reference": core.digest("invented calibration")},
    ):
        with pytest.raises(records.CodingError, match="^malformed_record$"):
            records.checked(
                invented_policy.model_copy(update=update), records.PolicyReference
            )


def test_assignment_grain_qualifies_shared_quote_ids_by_document(invented_book):
    from earnings_themes.coding.assignments import assignment_id, assignment_key

    rows = []
    for doc_id, theme_id in (
        ("invented-a", "one"),
        ("invented-a", "two"),
        ("invented-b", "one"),
    ):
        key = (
            "invented-coding",
            invented_book.codebook_id,
            0,
            doc_id,
            theme_id,
            "q-0-10",
        )
        row = coding.Assignment(
            assignment_id=assignment_id(key),
            coding_run_id="invented-coding",
            doc_id=doc_id,
            quote_id="q-0-10",
            theme_id=theme_id,
            codebook=invented_book,
            canonical_hash=core.digest(doc_id),
            start=0,
            end=10,
            validator_version=core.VALIDATOR_VERSION,
            mask_ids=(),
            support_run_hash=core.digest("invented support"),
            policy_hash=core.digest("invented policy"),
            policy_kind="fixture",
        )
        assert assignment_key(row, row.quote_id) == key
        rows.append(row)
    frame = coding.assignment_frame(rows, scope="fixture")
    assert frame.height == 3 and frame["quote_id"].n_unique() == 1
    with pytest.raises(coding.CodingError, match="^fixture_policy$"):
        coding.assignment_frame(rows)
    with pytest.raises(coding.CodingError, match="^invalid_references$"):
        coding.assignment_frame((*rows, rows[0]), scope="fixture")
