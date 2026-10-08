"""Completion proofs use invented, round-tripped upstream runs only."""

from dataclasses import replace

import pytest
from earnings_core import digest
from earnings_themes import analysis
from earnings_themes.coding.decide import support_run_hash


def complete(inputs):
    assert callable(getattr(analysis, "document_completions", None)), (
        "completion_missing"
    )
    return analysis.document_completions(analysis.reverify_analysis_inputs(inputs))


def declare(inputs):
    from earnings_themes.analysis import NoThemeDeclaration

    meta = inputs.metadata[0]
    declaration = NoThemeDeclaration(
        doc_id=meta.doc_id,
        canonical_hash=meta.canonical_hash,
        source_run_hash=inputs.coding.record.source_run_hash,
        coding_run_hash=digest(inputs.coding.record.model_dump(mode="json")),
        support_run_hash=support_run_hash(inputs.support),
        codebook=inputs.coding.record.codebook,
        analysis_policy_hash=inputs.analysis_policy.content_hash,
        assignment_policy=inputs.assignment_policy.reference,
        actor_id="invented-adjudicator",
        declared_at=inputs.coding.record.started_at,
        policy_scope="fixture",
    )
    return replace(inputs, no_theme=(declaration,))


def test_complete_accepted_expected_work(analysis_inputs):
    (row,) = complete(analysis_inputs)
    assert row.traversal_complete and row.classification_complete
    assert row.assessment_complete and row.decision_complete
    assert (row.eligible_units, row.completed_windows, row.failed_windows) == (2, 1, 0)
    assert row.observable and row.processing_state == "completed"


@pytest.mark.parametrize(
    "kind",
    ["empty", "unmatched", "rejected", "review", "refused"],
    ids=["empty", "unmatched", "rejected", "review", "refused"],
)
def test_empty_acceptance_never_declares_absence(analysis_input_factory, kind):
    options = {
        "empty": {"claims": ()},
        "unmatched": {"themes": ()},
        "rejected": {"assignment_action": "reject"},
        "review": {"review": True},
        "refused": {"quote_labels": ("U999",)},
    }
    inputs, _ = analysis_input_factory(**options[kind])
    (row,) = complete(inputs)
    assert not row.observable and row.processing_state == "partial"
    reason = {
        "unmatched": "valid_unmatched",
        "review": "calibration_required",
        "refused": "extraction_partial",
    }.get(kind, "no_theme_unconfirmed")
    assert reason in row.reasons


@pytest.mark.parametrize(
    "claims,themes",
    [((), ("capacity",)), (("Invented unmatched.",), ())],
    ids=["claimless", "unmatched"],
)
def test_explicit_no_theme_with_complete_work(analysis_input_factory, claims, themes):
    inputs, _ = analysis_input_factory(claims=claims, themes=themes)
    (row,) = complete(declare(inputs))
    assert row.observable and row.processing_state == "completed-no-theme"
    assert row.declaration_hash is not None and row.accepted_count == 0
    assert row.unmatched_count == len(claims)


@pytest.mark.parametrize(
    "kind",
    ["accepted", "rejected_candidate", "stale", "duplicate"],
    ids=["accepted", "candidate", "stale", "duplicate"],
)
def test_invalid_declaration_refuses(analysis_input_factory, kind):
    options = {
        "accepted": {},
        "rejected_candidate": {"quote_labels": ("U999",)},
        "stale": {"claims": ()},
        "duplicate": {"claims": ()},
    }
    inputs, _ = analysis_input_factory(**options[kind])
    inputs = declare(inputs)
    if kind == "stale":
        inputs = replace(
            inputs,
            no_theme=(
                inputs.no_theme[0].model_copy(update={"canonical_hash": "0" * 64}),
            ),
        )
    with pytest.raises(analysis.AnalysisError):
        if kind == "duplicate":
            inputs = replace(inputs, no_theme=inputs.no_theme * 2)
        complete(inputs)


def test_masked_only_acceptance_stays_observed(analysis_input_factory):
    inputs, _ = analysis_input_factory(masked=True, quote_labels=("U1",))
    (row,) = complete(inputs)
    assert row.observable and row.accepted_count == row.masked_count == 1


@pytest.mark.parametrize(
    "mode,reason,state",
    [
        ("failed", "processing_failed", "failed"),
        ("partial", "extraction_partial", "partial"),
        ("replay", "replay_miss", "failed"),
        ("exhausted", "budget_exhausted", "partial"),
        ("no_units", "no_eligible_units", "partial"),
    ],
    ids=["failed", "partial", "replay", "exhausted", "no_units"],
)
def test_traversal_outcomes_keep_expected_work(
    analysis_input_factory, mode, reason, state
):
    options = {"budget": 1, "mode": mode}
    if mode == "exhausted":
        options.update(mode="complete", requests=1)
    if mode == "no_units":
        options.update(mode="complete", no_units=True)
    inputs, _ = analysis_input_factory(extraction_options=options)
    (row,) = complete(inputs)
    assert not row.traversal_complete and not row.observable
    assert row.processing_state == state and reason in row.reasons


def test_missing_classification_is_not_complete(analysis_input_factory):
    inputs, _ = analysis_input_factory(
        claim_order=lambda source: tuple(
            (c.doc_id, c.claim_id) for c in source.stored_run.claims[:1]
        )
    )
    (row,) = complete(inputs)
    assert not row.classification_complete and not row.observable
    assert "classification_incomplete" in row.reasons


@pytest.mark.parametrize(
    "kind",
    ["flagged", "incomplete", "policy_review", "classification_refused"],
    ids=["flagged", "incomplete", "review", "classification"],
)
def test_downstream_obstacles_stay_partial(analysis_input_factory, kind):
    from earnings_themes.support.records import SupportCeilings

    options = {
        "flagged": {"contribution": "uncertain"},
        "incomplete": {
            "support_ceilings": SupportCeilings(
                scorer_per_target=0,
                scorer_per_document=0,
                scorer_per_run=0,
                judge_per_target=0,
                judge_per_document=0,
                judge_per_run=0,
                tokens_per_document=0,
                tokens_per_run=0,
            )
        },
        "policy_review": {"assignment_action": "review"},
        "classification_refused": {
            "classification_reply": {"theme_ids": ["unknown"], "attributes": {}}
        },
    }
    inputs, _ = analysis_input_factory(**options[kind])
    (row,) = complete(inputs)
    assert not row.observable and row.processing_state == "partial"
    assert {
        "flagged": "assessment_flagged",
        "incomplete": "assessment_incomplete",
        "policy_review": "policy_review",
        "classification_refused": "classification_incomplete",
    }[kind] in row.reasons


def test_declaration_cannot_waive_missing_claim_work(analysis_input_factory):
    inputs, _ = analysis_input_factory(themes=(), claim_order=lambda source: ())
    with pytest.raises(analysis.AnalysisError):
        complete(declare(inputs))


def test_completed_subset_of_expected_units_is_partial(analysis_input_factory):
    inputs, _ = analysis_input_factory(claims=(), extraction_options={"mode": "subset"})
    (row,) = complete(inputs)
    assert row.eligible_units == 2 and not row.traversal_complete and not row.observable
    assert "extraction_partial" in row.reasons
    with pytest.raises(analysis.AnalysisError):
        complete(declare(inputs))
