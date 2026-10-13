"""The label view and the label pool (the Stage 11 spec, A4; FP8). The view shows
the claim, its quotes in context and the theme, and nothing a model said."""

from importlib import import_module

import pytest
from earnings_themes.evaluation.label_view import label_views
from earnings_themes.evaluation.problems import EvaluationError
from earnings_themes.evaluation.sampling import PoolTarget, label_pool
from earnings_themes.support import reverify_support_run

_cases = import_module("packages.earnings-themes.tests.coding.cases")


@pytest.fixture
def flagged_case(assessed_case, tmp_path):
    """The same target, judged with a marked score and an uncertain quote, so its
    view could leak either."""
    return _cases.make_assessed_case(
        assessed_case.proposals,
        assessed_case.sources,
        tmp_path / "flagged",
        parts=_cases.make_support_parts("uncertain", score=0.123456789),
    )


def test_the_view_shows_the_claim_quote_and_theme(assessed_case) -> None:
    case = assessed_case
    target = case.support.targets[0]
    view = label_views(case.support, case.sources, (target.target_id,))
    assert f"## 1. {target.target_id}" in view
    assert "**Claim:** An invented operating claim." in view
    assert "⟦Lumen added a press and served more orders.⟧" in view
    assert "**Theme:** Capacity" in view
    assert "- Explicit equipment or facility expansion." in view
    assert "- Orders without equipment changes." in view


def test_the_view_holds_no_score_answer_flag_or_model_identity(flagged_case) -> None:
    case = flagged_case
    reverify_support_run(case.support, case.sources)
    assert case.support.outcomes[0].status == "flagged"
    target = case.support.targets[0]
    view = label_views(case.support, case.sources, (target.target_id,))
    for planted in (
        "0.123456789",
        "0.12345",
        "Invented fixture assessment",
        "uncertain",
        "quote_uncertain",
        "invented-support",
        "invented-family",
        "invented-extractor",
        "scripted",
        case.support.record.run_id,
        case.sources.stored_run.record.run_id,
    ):
        assert planted not in view, planted


def test_an_unknown_target_is_refused(assessed_case) -> None:
    case = assessed_case
    with pytest.raises(EvaluationError, match="unknown_target"):
        label_views(case.support, case.sources, ("support-unknown",))


def test_the_pool_is_assessed_and_flagged_targets_with_their_events(
    assessed_case, flagged_case
) -> None:
    for case in (assessed_case, flagged_case):
        target = case.support.targets[0]
        events = {target.target.doc_id: "e1"}
        assert label_pool(case.support.targets, case.support.outcomes, events) == (
            PoolTarget(target.target_id, "e1", target.target.theme_id),
        )
    refused = flagged_case.support.outcomes[0].model_copy(update={"status": "refused"})
    assert label_pool(flagged_case.support.targets, (refused,), events) == ()
    with pytest.raises(EvaluationError, match="unknown_event"):
        label_pool(flagged_case.support.targets, flagged_case.support.outcomes, {})
