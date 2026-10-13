"""Public consumer helpers and closed view errors, using invented records."""

from dataclasses import replace

import pytest
from earnings_themes import evaluation
from earnings_themes.evaluation.label_view import label_views
from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem


@pytest.mark.parametrize(
    "name",
    [
        "joint_score",
        "sealed",
        "claim_label",
        "joint_label",
        "Figure",
        "ReadingAgreement",
        "IndependentFigures",
        "EvidenceTally",
        "configuration_hash",
    ],
)
def test_application_helpers_are_exported(name):
    assert name in evaluation.__all__
    assert getattr(evaluation, name) is not None


def test_label_view_missing_evidence_document_is_a_closed_error(assessed_case):
    case = assessed_case
    evidence = case.support.evidence[0].model_copy(update={"doc_id": "absent"})
    altered = replace(case.support, evidence=(evidence,))
    with pytest.raises(EvaluationError) as refused:
        label_views(altered, case.sources, (case.support.targets[0].target_id,))
    assert (refused.value.problem, refused.value.subject) == (
        EvaluationProblem.MALFORMED_RECORD,
        "evidence.doc_id",
    )
