"""External policy boundaries exercised through real scripted Stage 8 storage."""

import json
from dataclasses import replace

import pytest
from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    TextSpan,
    digest,
)
from earnings_themes.anchoring import Bundle
from earnings_themes.coding.records import CodingError, PolicyVote

from .cases import (
    FixturePolicy,
    make_assessed_case,
    make_proposal_job,
    make_sources,
    make_support_parts,
)


def test_assessed_without_policy_is_review_not_acceptance(assessed_case):
    result = assessed_case.decide(policy=None)
    assert result.decisions[0].reason == "calibration_required"
    assert [d.status for d in result.decisions] == ["review"]
    assert result.decisions[0].support_status == "assessed"
    assert result.decisions[0].supporting_quote_ids == ()


def test_fixture_policy_is_explicit_and_tagged(assessed_case, fixture_policy):
    result = assessed_case.decide(policy=fixture_policy)
    assert result.decisions[0].status == "accepted"
    assert result.decisions[0].policy.kind == "fixture"


def test_contextual_quote_is_never_promoted(contextual_case, fixture_policy):
    fixture_policy.vote_quote_ids = contextual_case.context_quote_ids
    with pytest.raises(CodingError, match="^invalid_contribution$"):
        contextual_case.decide(policy=fixture_policy)


def test_real_assessment_views_and_deterministic_decisions(
    assessed_case, fixture_policy
):
    assert len(assessed_case.support.trials) == 4
    assert len(assessed_case.support.entailment) == 2
    seen = []
    original = fixture_policy.evaluate

    def evaluate(view):
        seen.append(view)
        return original(view)

    fixture_policy.evaluate = evaluate
    first = assessed_case.decide(fixture_policy)
    second = assessed_case.decide(fixture_policy)
    assert first.decisions == second.decisions
    view = seen[0]
    assert view.target == assessed_case.support.targets[0]
    assert view.evidence == assessed_case.support.evidence
    assert view.entailment == assessed_case.support.entailment
    assert view.trials == assessed_case.support.trials
    assert view.outcome == assessed_case.support.outcomes[0]
    assert "Invented" not in repr(view)
    row = first.decisions[0]
    assert row.decision_id == "decision-" + digest(
        {
            "target_id": row.target_id,
            "proposal_hash": row.proposal_hash,
            "support_run_hash": row.support_run_hash,
            "policy": row.policy.model_dump(mode="json"),
        }
    )


@pytest.mark.parametrize("vote", ["reject", "review"])
def test_explicit_nonaccepting_policy_retains_raw_signals(
    assessed_case, fixture_policy, vote
):
    fixture_policy.evaluate = lambda view: PolicyVote(action=vote)
    result = assessed_case.decide(fixture_policy)
    row = result.decisions[0]
    assert row.status == ("rejected" if vote == "reject" else "review")
    assert row.reason == "policy_" + vote
    assert row.supporting_quote_ids == ()
    assert result.support == assessed_case.support


@pytest.mark.parametrize(
    "field",
    [
        "codebook_id",
        "codebook_version",
        "content_hash",
        "classifier_configuration_hash",
        "support_configuration_hash",
        "calibration_reference",
    ],
)
def test_external_policy_reference_is_bound_before_evaluation(
    assessed_case, fixture_policy, field
):
    reference = fixture_policy.reference
    if field in {"codebook_id", "codebook_version", "content_hash"}:
        value = 99 if field == "codebook_version" else digest("wrong")
        reference = reference.model_copy(
            update={"codebook": reference.codebook.model_copy(update={field: value})}
        )
    else:
        reference = reference.model_copy(update={field: digest("wrong")})
    fixture_policy.reference = reference
    fixture_policy.evaluate = lambda view: pytest.fail(
        "Mismatched policy was evaluated"
    )
    with pytest.raises(CodingError, match="^(policy_mismatch|malformed_record)$"):
        assessed_case.decide(fixture_policy)


def test_calibrated_declaration_requires_an_artifact_hash(
    assessed_case, fixture_policy
):
    fixture_policy.reference = fixture_policy.reference.model_copy(
        update={"kind": "calibrated"}
    )
    with pytest.raises(CodingError, match="^malformed_record$"):
        assessed_case.decide(fixture_policy)


@pytest.mark.parametrize("ids", [(), ("unknown",), ("duplicate", "duplicate")])
def test_policy_cannot_accept_empty_duplicate_or_unknown_quotes(
    assessed_case, fixture_policy, ids
):
    fixture_policy.evaluate = lambda view: PolicyVote.model_construct(
        action="accept", supporting_quote_ids=ids
    )
    with pytest.raises(CodingError, match="^(invalid_contribution|malformed_record)$"):
        assessed_case.decide(fixture_policy)


@pytest.mark.parametrize(
    "kind",
    ["exception", "reference", "view", "source", "proposal", "support", "request"],
)
def test_policy_callback_mutation_or_exception_aborts(
    assessed_case, fixture_policy, kind
):
    original = fixture_policy.evaluate

    def evaluate(view):
        if kind == "exception":
            raise RuntimeError("Invented secret exception text")
        if kind == "reference":
            fixture_policy.reference = fixture_policy.reference.model_copy(
                update={"policy_hash": digest("changed")}
            )
        elif kind == "view":
            view.target.__dict__["claim_hash"] = digest("changed")
        elif kind == "source":
            assessed_case.sources.stored_run.claims[0].__dict__["claim"] = (
                "Changed invented claim."
            )
        elif kind == "proposal":
            assessed_case.proposals.proposals[0].__dict__["input_hash"] = digest(
                "changed"
            )
        elif kind == "request":
            assessed_case.proposals.attempts[0].__dict__["request_hash"] = digest(
                "changed"
            )
        else:
            assessed_case.support.record.__dict__["configuration_hash"] = digest(
                "changed"
            )
        return original(view)

    fixture_policy.evaluate = evaluate
    with pytest.raises(
        CodingError, match="^(input_changed|unexpected_error)$"
    ) as failure:
        assessed_case.decide(fixture_policy)
    assert "secret" not in str(failure.value)
    assert failure.value.__cause__ is None
    assert failure.value.__suppress_context__


def test_source_mutation_after_support_storage_is_refused(
    assessed_case, fixture_policy
):
    assessed_case.sources.bundles[0].document.__dict__["canonical_text"] = (
        "Changed invented text."
    )
    fixture_policy.evaluate = lambda view: pytest.fail("Changed source reached policy")
    with pytest.raises(CodingError):
        assessed_case.decide(fixture_policy)


def test_missing_assessment_is_visible_review(assessed_case, tmp_path):
    case = make_assessed_case(
        assessed_case.proposals, assessed_case.sources, tmp_path / "omitted", targets=()
    )
    result = case.decide(FixturePolicy(case.proposals, case.support))
    assert len(result.decisions) == 1
    row = result.decisions[0]
    assert (row.status, row.reason, row.support_status) == (
        "review",
        "missing_assessment",
        None,
    )
    assert row.missing == ("missing_assessment",)
    assert row.supporting_quote_ids == ()
    assert result.proposals.novelty == ()


@pytest.mark.parametrize(
    "kind", ["target", "outcome", "proposal", "fabricated", "copied"]
)
def test_duplicate_or_fabricated_records_never_reach_policy(
    assessed_case, fixture_policy, kind
):
    support = assessed_case.support
    if kind == "target":
        assessed_case.support = replace(
            support, targets=(*support.targets, support.targets[0])
        )
    elif kind == "outcome":
        assessed_case.support = replace(
            support, outcomes=(*support.outcomes, support.outcomes[0])
        )
    elif kind == "proposal":
        proposals = assessed_case.proposals
        assessed_case.proposals = replace(
            proposals, proposals=(*proposals.proposals, proposals.proposals[0])
        )
    elif kind == "fabricated":
        assessed_case.support = replace(
            support, trials=(), entailment=(), attempts=(), usage=()
        )
    else:
        assessed_case.support = replace(
            support,
            outcomes=(support.outcomes[0].model_copy(update={"target_id": "copied"}),),
        )
    fixture_policy.evaluate = lambda view: pytest.fail(
        "Invalid assessment reached policy"
    )
    with pytest.raises(CodingError):
        assessed_case.decide(fixture_policy)


def test_extra_support_target_is_configuration_error(assessed_case, tmp_path):
    first = assessed_case.proposals.targets[0]
    second = first.model_copy(update={"theme_id": "demand"})
    case = make_assessed_case(
        assessed_case.proposals,
        assessed_case.sources,
        tmp_path / "extra",
        targets=(first, second),
    )
    with pytest.raises(CodingError, match="^invalid_references$"):
        case.decide(FixturePolicy(case.proposals, case.support))


@pytest.mark.parametrize("objection", ["claim_support", "theme_fit", "quote", "reason"])
def test_categorical_negatives_with_high_scores_stay_review(
    assessed_case, tmp_path, objection
):
    scorer, panel = make_support_parts(score=0.99)
    for judge in panel:
        script = judge.script

        def negative(request, script=script):
            reply = script(request)
            answer = json.loads(reply.text)
            answer["joint_support_score"] = 0.99
            if objection == "claim_support":
                answer["claim_support"] = "unsupported"
            elif objection == "theme_fit":
                answer["theme_fit"] = "does_not_fit"
            elif objection == "quote":
                answer["quote_assessments"][0]["contribution"] = "irrelevant"
            else:
                answer["reason_codes"] = ["context_only_support"]
            return reply.model_copy(update={"text": json.dumps(answer)})

        judge.script = negative
    case = make_assessed_case(
        assessed_case.proposals,
        assessed_case.sources,
        tmp_path / "negative",
        parts=(scorer, panel),
    )
    policy = FixturePolicy(case.proposals, case.support)
    policy.evaluate = lambda view: pytest.fail("Flagged assessment reached policy")
    result = case.decide(policy)
    assert all(signal.score == 0.99 for signal in case.support.entailment)
    assert all(
        trial.answer.joint_support_score == 0.99 for trial in case.support.trials
    )
    assert result.decisions[0].status == "review"
    assert result.decisions[0].reason == "assessment_flagged"
    assert result.decisions[0].flags == case.support.outcomes[0].flags
    assert result.decisions[0].supporting_quote_ids == ()


def test_incomplete_assessment_cannot_be_overridden(assessed_case, tmp_path):
    limits = assessed_case.support.record.ceilings.model_copy(
        update={"judge_per_run": 0}
    )
    case = make_assessed_case(
        assessed_case.proposals,
        assessed_case.sources,
        tmp_path / "incomplete",
        ceilings=limits,
    )
    policy = FixturePolicy(case.proposals, case.support)
    policy.evaluate = lambda view: pytest.fail("Incomplete assessment reached policy")
    row = case.decide(policy).decisions[0]
    assert (row.status, row.reason) == ("review", "assessment_incomplete")
    assert row.missing == case.support.outcomes[0].missing


def test_real_refusal_cannot_be_overridden(assessed_case, tmp_path):
    sources = replace(
        assessed_case.sources,
        stored_run=replace(assessed_case.sources.stored_run, quotes=()),
    )
    case = make_assessed_case(assessed_case.proposals, sources, tmp_path / "refused")
    case.sources = assessed_case.sources
    policy = FixturePolicy(case.proposals, case.support)
    policy.evaluate = lambda view: pytest.fail("Refused assessment reached policy")
    row = case.decide(policy).decisions[0]
    assert (row.status, row.reason) == ("refused", "assessment_refused")
    assert row.missing == ("unknown_quote",)


@pytest.mark.parametrize("mixed", [False, True])
def test_multiple_original_quotes_preserve_contributions(
    coding_case, coding_policy, classifier_identity, template, tmp_path, mixed
):
    text = "Lumen added a press.\nOrders rose at Lumen."
    doc = CanonicalDocument.create(
        source_document_id="invented-two-quotes",
        canonicalization_version="invented-1",
        canonical_text=text,
    )
    boundary = text.index("\n")
    elements = tuple(
        DocumentElement.create(
            doc, ElementType.PARAGRAPH, TextSpan(start=start, end=end)
        )
        for start, end in ((0, boundary), (boundary + 1, len(text)))
    )
    sources = make_sources(
        coding_case.codebook,
        Bundle("invented-two", doc, elements, ()),
        template,
        quote_labels=("U1", "U2"),
    )
    job = make_proposal_job(sources, coding_policy, classifier_identity, tmp_path)
    proposals, _ = job.run([{"theme_ids": ["capacity"], "attributes": {}}])
    quote_ids = sources.stored_run.claims[0].quote_ids
    contributions = {
        quote_ids[0]: "supporting",
        quote_ids[1]: "contextual" if mixed else "supporting",
    }
    case = make_assessed_case(proposals, sources, tmp_path, contribution=contributions)
    result = case.decide(FixturePolicy(proposals, case.support))
    row = result.decisions[0]
    expected = tuple(sorted(quote_ids[:1] if mixed else quote_ids))
    assert row.supporting_quote_ids == expected
    assert len(result.support.evidence) == 2
    assert len(result.support.entailment) == 3
    assert result.support.targets[0].original_quote_ids == quote_ids
    if mixed:
        policy = FixturePolicy(proposals, case.support)
        policy.vote_quote_ids = quote_ids
        with pytest.raises(CodingError, match="^invalid_contribution$"):
            case.decide(policy)


def test_policy_cannot_mutate_a_later_targets_raw_signals(proposal_job, tmp_path):
    proposals, _ = proposal_job.run(
        [{"theme_ids": ["capacity", "demand"], "attributes": {}}]
    )
    case = make_assessed_case(proposals, proposal_job.sources, tmp_path)
    policy = FixturePolicy(proposals, case.support)
    original = policy.evaluate
    later_id = case.support.targets[1].target_id

    def evaluate(view):
        if view.target.target_id != later_id:
            for signal in case.support.entailment:
                if signal.target_id == later_id:
                    signal.__dict__["score"] = 0.99
        return original(view)

    policy.evaluate = evaluate
    with pytest.raises(CodingError, match="^input_changed$"):
        case.decide(policy)


def test_reference_property_mutation_is_checked_before_evaluation(
    assessed_case, fixture_policy
):
    reference = fixture_policy.reference

    class MutatingReference:
        @property
        def reference(self):
            assessed_case.sources.stored_run.claims[0].__dict__["claim"] = (
                "Changed invented claim."
            )
            return reference

        def evaluate(self, view):
            pytest.fail("Reference-property source mutation reached evaluation")

    with pytest.raises(CodingError, match="^input_changed$"):
        assessed_case.decide(MutatingReference())


def test_copied_assessed_status_cannot_hide_real_negative_signals(
    assessed_case, tmp_path
):
    case = make_assessed_case(
        assessed_case.proposals,
        assessed_case.sources,
        tmp_path / "flagged",
        contribution="irrelevant",
    )
    case.support = replace(
        case.support,
        outcomes=(
            case.support.outcomes[0].model_copy(
                update={"status": "assessed", "flags": ()}
            ),
        ),
    )
    with pytest.raises(CodingError, match="^storage_corrupt$"):
        case.decide(FixturePolicy(case.proposals, case.support))


def test_original_document_identity_is_kept_with_shared_quote_ids(
    coding_case, coding_policy, classifier_identity, template, tmp_path
):
    from .cases import invented_bundle

    sources = make_sources(
        coding_case.codebook,
        invented_bundle("invented-first"),
        template,
        other_bundles=(invented_bundle("invented-second"),),
    )
    job = make_proposal_job(sources, coding_policy, classifier_identity, tmp_path)
    proposals, _ = job.run([{"theme_ids": ["capacity"], "attributes": {}}] * 2)
    case = make_assessed_case(proposals, sources, tmp_path)
    result = case.decide(FixturePolicy(proposals, case.support))
    assert len(result.decisions) == 2
    first, second = result.decisions
    assert first.doc_id != second.doc_id
    assert first.target_id != second.target_id
    assert first.supporting_quote_ids == second.supporting_quote_ids
    assert first.decision_id != second.decision_id


def test_contribution_disagreement_remains_flagged(assessed_case, tmp_path):
    scorer, panel = make_support_parts()
    panel = (panel[0], make_support_parts("contextual")[1][1])
    case = make_assessed_case(
        assessed_case.proposals,
        assessed_case.sources,
        tmp_path / "disagreement",
        parts=(scorer, panel),
    )
    row = case.decide(FixturePolicy(case.proposals, case.support)).decisions[0]
    assert row.reason == "assessment_flagged"
    assert "category_disagreement" in row.flags
    assert row.supporting_quote_ids == ()


def test_policy_reference_classifier_hash_is_required(fixture_policy):
    from earnings_themes.coding.records import PolicyReference, checked

    data = fixture_policy.reference.model_dump(mode="json")
    del data["classifier_configuration_hash"]
    with pytest.raises(CodingError, match="^malformed_record$"):
        checked(data, PolicyReference)


def test_policy_reference_exception_is_redacted(assessed_case):
    class BrokenReference:
        @property
        def reference(self):
            raise RuntimeError("Invented private property content")

        def evaluate(self, view):
            pytest.fail("Broken reference reached evaluation")

    with pytest.raises(CodingError, match="^unexpected_error$") as failure:
        assessed_case.decide(BrokenReference())
    assert failure.value.__cause__ is None
    assert failure.value.__suppress_context__


def test_decision_identifier_cannot_be_replaced(assessed_case, fixture_policy):
    from earnings_themes.coding.records import AssignmentDecision, checked

    row = assessed_case.decide(fixture_policy).decisions[0]
    with pytest.raises(CodingError, match="^malformed_record$"):
        checked(
            row.model_copy(update={"decision_id": "decision-" + digest("wrong")}),
            AssignmentDecision,
        )


def test_later_policy_reference_exception_is_redacted(assessed_case, fixture_policy):
    class BrokenLaterReference:
        reads = 0

        @property
        def reference(self):
            self.reads += 1
            if self.reads > 2:
                raise RuntimeError("Invented private later property content")
            return fixture_policy.reference

        def evaluate(self, view):
            return fixture_policy.evaluate(view)

    with pytest.raises(CodingError, match="^unexpected_error$"):
        assessed_case.decide(BrokenLaterReference())
