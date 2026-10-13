"""The calibrated policy decides exactly as calibration simulated (the Stage 11
spec, A5; Stage 9's ``AssignmentPolicy``; D19-5)."""

from importlib import import_module

import pytest
from earnings_themes.coding.decide import decision_inputs
from earnings_themes.evaluation.calibration import ScorerCutoff, accepts
from earnings_themes.evaluation.policy import CalibratedPolicy
from earnings_themes.evaluation.problems import EvaluationError
from earnings_themes.evaluation.records import sealed

from .test_calibration import run

_cases = import_module("packages.earnings-themes.tests.coding.cases")


def artifact_with(cutoff: float):
    base = run()
    selection = base.selection.model_copy(update={"cutoff": cutoff})
    return sealed(base.model_copy(update={"selection": selection}))


def bind(case, artifact) -> CalibratedPolicy:
    return CalibratedPolicy(
        artifact,
        codebook=case.support.record.codebook,
        classifier_configuration_hash=case.proposals.record.configuration_hash,
        support_configuration_hash=case.support.record.configuration_hash,
    )


@pytest.mark.parametrize(("cutoff", "status"), [(0.2, "accepted"), (0.3, "review")])
def test_decisions_match_the_simulated_calibration(
    assessed_case, cutoff, status
) -> None:
    case = assessed_case
    policy = bind(case, artifact_with(cutoff))
    decision = case.decide(policy).decisions[0]
    assert decision.status == status
    view = next(iter(decision_inputs(case.support, case.sources).values()))
    assert accepts(ScorerCutoff(cutoff), view) == (status == "accepted")
    assert decision.policy == policy.reference
    assert policy.reference.kind == "calibrated"
    assert policy.reference.calibration_reference == artifact_with(cutoff).content_hash


def test_a_flagged_target_stays_in_review(assessed_case, tmp_path) -> None:
    case = _cases.make_assessed_case(
        assessed_case.proposals,
        assessed_case.sources,
        tmp_path / "flagged",
        parts=_cases.make_support_parts("uncertain", score=0.99),
    )
    decision = case.decide(bind(case, artifact_with(0.0))).decisions[0]
    assert (decision.status, decision.reason) == ("review", "assessment_flagged")


def test_no_candidate_or_a_changed_artifact_binds_no_policy(assessed_case) -> None:
    base = run()
    none = sealed(
        base.model_copy(update={"outcome": "no_candidate", "selection": None})
    )
    with pytest.raises(EvaluationError, match="no_candidate") as refused:
        bind(assessed_case, none)
    assert refused.value.subject == "selection"
    changed = base.model_copy(update={"usable_labels": 59})
    with pytest.raises(EvaluationError, match="content_hash_mismatch") as refused:
        bind(assessed_case, changed)
    assert refused.value.subject == "content_hash"
