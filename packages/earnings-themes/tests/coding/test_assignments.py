"""Document-qualified assignment grain over real scripted Stage 8 roundtrips."""

from dataclasses import replace

import polars as pl
import pytest
from earnings_core import digest
from earnings_themes.coding.assignments import (
    ASSIGNMENT_SCHEMA,
    assignment_frame,
    assignment_id,
    assignment_key,
    merge_assignment,
    project_assignments,
)
from earnings_themes.coding.records import Assignment, CodingError, checked

from .cases import FixturePolicy, make_assessed_case


def test_one_quote_two_themes_is_two_rows(multilabel_decisions):
    rows, links = project_assignments(*multilabel_decisions)
    assert len(rows) == 2
    assert len({(r.doc_id, r.quote_id) for r in rows}) == 1
    assert {r.theme_id for r in rows} == {"capacity", "demand"}
    assert all(not hasattr(r, "quote_text") for r in rows)
    assert len(links) == 2


def test_two_claims_one_quote_theme_is_one_row(two_claim_decisions):
    rows, links = project_assignments(*two_claim_decisions)
    assert len(rows) == 1
    assert len({link.claim_id for link in links}) == 2
    assert len({link.assignment_id for link in links}) == 1


def test_document_scoped_quote_ids_never_collapse(two_document_decisions):
    rows, _ = project_assignments(*two_document_decisions)
    assert len(rows) == 2
    assert len({r.quote_id for r in rows}) == 1
    assert len({r.doc_id for r in rows}) == 2


def test_fixture_acceptance_cannot_enter_default_frame(multilabel_decisions):
    rows, _ = project_assignments(*multilabel_decisions)
    with pytest.raises(CodingError, match="^fixture_policy$"):
        assignment_frame(rows)
    assert assignment_frame(rows, scope="fixture").height == 2


def changed_decision(decision, **updates):
    row = decision.model_copy(update=updates)
    return row.model_copy(
        update={
            "decision_id": "decision-"
            + digest(
                {
                    "target_id": row.target_id,
                    "proposal_hash": row.proposal_hash,
                    "support_run_hash": row.support_run_hash,
                    "policy": row.policy.model_dump(mode="json")
                    if row.policy
                    else None,
                }
            )
        }
    )


@pytest.mark.parametrize(
    "field", ["coding_run_id", "doc_id", "claim_id", "theme_id", "input_hash"]
)
def test_altered_decision_source_references_refuse(multilabel_decisions, field):
    decisions, support = multilabel_decisions
    row = changed_decision(decisions.decisions[0], **{field: digest("changed")})
    with pytest.raises(CodingError, match="^(invalid_references|input_changed)$"):
        project_assignments(
            replace(decisions, decisions=(row, *decisions.decisions[1:])), support
        )


@pytest.mark.parametrize(
    "field", ["proposal_hash", "support_run_hash", "source_run_hash"]
)
def test_common_hash_mutation_refuses(multilabel_decisions, field):
    decisions, support = multilabel_decisions
    with pytest.raises(CodingError, match="^input_changed$"):
        project_assignments(replace(decisions, **{field: digest("changed")}), support)


@pytest.mark.parametrize("kind", ["duplicate", "omitted", "list", "wrong_container"])
def test_strict_decision_container_and_unique_targets(multilabel_decisions, kind):
    decisions, support = multilabel_decisions
    rows = decisions.decisions
    if kind == "wrong_container":
        value = rows
    else:
        rows = (
            (*rows, rows[0])
            if kind == "duplicate"
            else rows[:1]
            if kind == "omitted"
            else list(rows)
        )
        value = replace(decisions, decisions=rows)
    with pytest.raises(CodingError, match="^(malformed_record|invalid_references)$"):
        project_assignments(value, support)


def test_saved_acceptance_cannot_promote_contextual_quote(assessed_case, tmp_path):
    case = make_assessed_case(
        assessed_case.proposals,
        assessed_case.sources,
        tmp_path / "context",
        contribution="contextual",
    )
    decisions = case.decide(None)
    policy = FixturePolicy(case.proposals, case.support).reference
    row = changed_decision(
        decisions.decisions[0],
        policy=policy,
        status="accepted",
        reason="policy_accept",
        supporting_quote_ids=tuple(e.quote_id for e in case.support.evidence),
    )
    with pytest.raises(CodingError, match="^invalid_contribution$"):
        project_assignments(
            replace(decisions, decisions=(row,), policy=policy), case.support
        )


def test_policy_configuration_mutation_refuses(multilabel_decisions):
    decisions, support = multilabel_decisions
    policy = decisions.policy.model_copy(
        update={"classifier_configuration_hash": digest("changed")}
    )
    rows = tuple(changed_decision(row, policy=policy) for row in decisions.decisions)
    with pytest.raises(CodingError, match="^policy_mismatch$"):
        project_assignments(replace(decisions, decisions=rows, policy=policy), support)


@pytest.mark.parametrize("kind", ["source", "proposal", "support", "evidence"])
def test_retained_input_mutation_refuses(multilabel_decisions, kind):
    decisions, support = multilabel_decisions
    if kind == "source":
        decisions.sources.bundles[0].document.__dict__["canonical_text"] = (
            "Changed invented text."
        )
    elif kind == "proposal":
        decisions.proposals.proposals[0].__dict__["input_hash"] = digest("changed")
    elif kind == "support":
        support.trials[0].answer.__dict__["joint_support_score"] = 0.99
    else:
        support.evidence[0].__dict__["start"] = 1
    with pytest.raises(CodingError):
        project_assignments(decisions, support)


def test_typed_empty_frames_do_not_claim_exactness():
    for scope in ("production", "fixture"):
        frame = assignment_frame((), scope=scope)
        assert frame.height == 0
        assert frame.schema == pl.Schema(ASSIGNMENT_SCHEMA)
        assert "exactness" not in frame.columns
        assert "no_theme" not in frame.columns


@pytest.mark.parametrize("value", [None, {}, set(), iter(())])
def test_frame_requires_a_sequence_with_fixed_refusal(value):
    with pytest.raises(CodingError, match="^malformed_record$"):
        assignment_frame(value)


@pytest.mark.parametrize(
    "field,value",
    [
        ("start", True),
        ("end", 1.5),
        ("start", "0"),
        ("end", 0),
        ("mask_ids", ("same", "same")),
    ],
)
def test_assignment_strict_offsets_and_distinct_masks(
    multilabel_decisions, field, value
):
    rows, _ = project_assignments(*multilabel_decisions)
    with pytest.raises(CodingError, match="^malformed_record$"):
        checked(rows[0].model_copy(update={field: value}), Assignment)


@pytest.mark.parametrize(
    "field,value", [("codebook_version", 1), ("content_hash", digest("other book"))]
)
def test_frame_refuses_mixed_versions_and_hashes(multilabel_decisions, field, value):
    rows, _ = project_assignments(*multilabel_decisions)
    changed = rows[1].model_copy(
        update={"codebook": rows[1].codebook.model_copy(update={field: value})}
    )
    with pytest.raises(CodingError, match="^mixed_codebook$"):
        assignment_frame((rows[0], changed), scope="fixture")


@pytest.mark.parametrize("scope", ["production", "fixture", "unknown"])
def test_frame_refuses_mixed_scopes(multilabel_decisions, scope):
    rows, _ = project_assignments(*multilabel_decisions)
    changed = rows[1].model_copy(update={"policy_kind": "calibrated"})
    with pytest.raises(CodingError, match="^fixture_policy$"):
        assignment_frame((rows[0], changed), scope=scope)


def test_calibrated_rows_require_explicit_correct_scope(multilabel_decisions):
    rows, _ = project_assignments(*multilabel_decisions)
    rows = tuple(row.model_copy(update={"policy_kind": "calibrated"}) for row in rows)
    assert assignment_frame(rows).schema == pl.Schema(ASSIGNMENT_SCHEMA)
    with pytest.raises(CodingError, match="^fixture_policy$"):
        assignment_frame(rows, scope="fixture")


@pytest.mark.parametrize("field", [None, "start", "policy_hash", "assignment_id"])
def test_duplicate_assignment_keys_or_ids_refuse(multilabel_decisions, field):
    rows, _ = project_assignments(*multilabel_decisions)
    changed = (
        rows[0]
        if field is None
        else rows[0].model_copy(
            update={field: 1 if field == "start" else digest("changed")}
        )
    )
    with pytest.raises(CodingError, match="^invalid_references$"):
        assignment_frame((rows[0], changed), scope="fixture")


def test_merge_deduplicates_links_and_refuses_conflicting_rows(multilabel_decisions):
    projected, annotations = project_assignments(*multilabel_decisions)
    row, link = (
        projected[0],
        next(l for l in annotations if l.assignment_id == projected[0].assignment_id),
    )
    key = assignment_key(row, row.quote_id)
    rows, links = {}, {}
    merge_assignment(rows, links, key, row, link)
    merge_assignment(rows, links, key, row, link)
    assert len(rows) == len(links) == 1
    for field, value in (("start", 1), ("policy_hash", digest("changed"))):
        with pytest.raises(CodingError, match="^invalid_references$"):
            merge_assignment(
                rows, links, key, row.model_copy(update={field: value}), link
            )


def test_projection_is_stable_and_uses_saved_span_identity(multilabel_decisions):
    decisions, support = multilabel_decisions
    quotes = tuple(
        q.model_dump(mode="json") for q in decisions.sources.stored_run.quotes
    )
    rows, links = project_assignments(decisions, support)
    assert project_assignments(
        replace(decisions, decisions=tuple(reversed(decisions.decisions))), support
    ) == (rows, links)
    for row in rows:
        assert row.assignment_id == assignment_id(assignment_key(row, row.quote_id))
        evidence = next(
            e
            for e in support.evidence
            if e.doc_id == row.doc_id and e.quote_id == row.quote_id
        )
        assert (
            row.canonical_hash,
            row.start,
            row.end,
            row.mask_ids,
            row.validator_version,
        ) == (
            evidence.canonical_hash,
            evidence.start,
            evidence.end,
            evidence.mask_ids,
            evidence.validator_version,
        )
    assert quotes == tuple(
        q.model_dump(mode="json") for q in decisions.sources.stored_run.quotes
    )


@pytest.mark.parametrize("vote", [None, "reject", "review"])
def test_nonaccepted_decisions_yield_no_rows(assessed_case, vote):
    from earnings_themes.coding.records import PolicyVote

    policy = (
        None
        if vote is None
        else FixturePolicy(assessed_case.proposals, assessed_case.support)
    )
    if policy:
        policy.evaluate = lambda view: PolicyVote(action=vote)
    assert project_assignments(assessed_case.decide(policy), assessed_case.support) == (
        (),
        (),
    )


def test_contradictory_annotations_remain_separate_linked_claims(
    assignment_case_factory,
):
    case = assignment_case_factory(
        claims=("Invented capacity rose.", "Invented capacity fell."),
        attributes=[{"direction": "increase"}, {"direction": "decrease"}],
    )
    rows, links = project_assignments(
        case.decide(FixturePolicy(case.proposals, case.support)), case.support
    )
    assert len(rows) == 1 and len(links) == 2
    attributes = {
        (a.doc_id, a.claim_id): a.attributes.direction
        for a in case.proposals.attributes
    }
    assert {attributes[(link.doc_id, link.claim_id)] for link in links} == {
        "increase",
        "decrease",
    }


@pytest.mark.parametrize("theme", ["capacity", "demand"])
def test_parent_only_and_child_only_are_not_rolled_up(
    assignment_case_factory, coding_case, theme
):
    from earnings_themes.codebook import codebook_hash

    book = coding_case.codebook
    book = book.model_copy(
        update={
            "themes": (
                book.themes[0],
                book.themes[1].model_copy(update={"parent_id": "capacity"}),
            )
        }
    )
    book = book.model_copy(update={"content_hash": codebook_hash(book)})
    case = assignment_case_factory(themes=(theme,), book=book)
    rows, links = project_assignments(
        case.decide(FixturePolicy(case.proposals, case.support)), case.support
    )
    assert [row.theme_id for row in rows] == [theme]
    assert len(links) == 1


@pytest.mark.parametrize("kind", ["missing", "incomplete", "refused"])
def test_real_nonaccepted_assessments_yield_no_rows(assessed_case, tmp_path, kind):
    sources = assessed_case.sources
    kwargs = {}
    if kind == "missing":
        kwargs["targets"] = ()
    elif kind == "incomplete":
        kwargs["ceilings"] = assessed_case.support.record.ceilings.model_copy(
            update={"judge_per_run": 0}
        )
    else:
        sources = replace(sources, stored_run=replace(sources.stored_run, quotes=()))
    case = make_assessed_case(
        assessed_case.proposals, sources, tmp_path / kind, **kwargs
    )
    case.sources = assessed_case.sources
    decisions = case.decide(FixturePolicy(case.proposals, case.support))
    assert project_assignments(decisions, case.support) == ((), ())
    assert (
        decisions.decisions[0].reason
        == {
            "missing": "missing_assessment",
            "incomplete": "assessment_incomplete",
            "refused": "assessment_refused",
        }[kind]
    )


def test_projection_preserves_boilerplate_mask_ids(assignment_case_factory):
    from earnings_core import MaskCategory, OverlayMask, TextSpan
    from earnings_themes.anchoring import mask_id

    from .cases import invented_bundle

    bundle = invented_bundle("invented-masked")
    mask = OverlayMask(
        doc_id=bundle.document.doc_id,
        canonical_hash=bundle.document.canonical_hash,
        span=TextSpan(start=0, end=len(bundle.document.canonical_text)),
        category=MaskCategory.SAFE_HARBOR,
        policy_id="invented-mask",
        policy_version="1",
    )
    bundle = replace(bundle, masks=(mask,))
    case = assignment_case_factory(bundle=bundle)
    rows, _ = project_assignments(
        case.decide(FixturePolicy(case.proposals, case.support)), case.support
    )
    assert rows[0].mask_ids == (mask_id(mask),)


def test_frame_refuses_duplicate_ids_across_distinct_keys(multilabel_decisions):
    rows, _ = project_assignments(*multilabel_decisions)
    changed = rows[1].model_copy(update={"assignment_id": rows[0].assignment_id})
    with pytest.raises(CodingError, match="^invalid_references$"):
        assignment_frame((rows[0], changed), scope="fixture")


@pytest.mark.parametrize("scope", [None, [], {}])
def test_invalid_scope_has_fixed_reason(scope):
    with pytest.raises(CodingError, match="^fixture_policy$"):
        assignment_frame((), scope=scope)


def test_frame_unrepresentable_integer_refuses_without_value(multilabel_decisions):
    rows, _ = project_assignments(*multilabel_decisions)
    changed = rows[0].model_copy(update={"end": 2**65})
    with pytest.raises(CodingError, match="^malformed_record$"):
        assignment_frame((changed,), scope="fixture")
