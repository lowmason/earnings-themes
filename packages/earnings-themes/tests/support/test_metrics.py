"""Hand-computed metric semantics on invented observation IDs only."""

import pytest
from earnings_themes.support.metrics import (
    Acceptance,
    ContinuousSignal,
    HumanLabel,
    MetricReport,
    accepted_claim_precision,
    auc_roc,
)
from pydantic import ValidationError

TASK = "joint_support"
VIEW = "nli-joint"


def label(target, supported, task=TASK):
    return HumanLabel(target_id=target, task=task, supported=supported)


def signal(target, score, view=VIEW, task=TASK):
    return ContinuousSignal(target_id=target, task=task, view=view, score=score)


def decision(target, accepted, task=TASK):
    return Acceptance(target_id=target, task=task, accepted=accepted)


@pytest.mark.parametrize(
    "scores,expected", [([0.9, 0.1], 1.0), ([0.1, 0.9], 0.0), ([0.4, 0.4], 0.5)]
)
def test_auc_ranking_and_ties(scores, expected):
    result = auc_roc(
        ["a", "b"],
        [label("a", 1), label("b", 0)],
        [signal(i, s) for i, s in zip(("a", "b"), scores)],
        task=TASK,
        view=VIEW,
    )
    assert result.value == expected
    assert result.joined_count == 2
    assert result.reason is None


def test_auc_multiple_pairs():
    result = auc_roc(
        ["a", "b", "c", "d"],
        [label("a", 1), label("b", 1), label("c", 0), label("d", 0)],
        [signal("a", 0.8), signal("b", 0.4), signal("c", 0.4), signal("d", 0.2)],
        task=TASK,
        view=VIEW,
    )
    assert result.value == 0.875


@pytest.mark.parametrize(
    "population,labels,signals,reason",
    [
        ([], [], [], "no_scored_labels"),
        (["a"], [label("a", 1)], [], "no_scored_labels"),
        (["a"], [label("a", 1)], [signal("a", 0.3)], "one_class"),
        (["a"], [label("a", 0)], [signal("a", 0.3)], "one_class"),
    ],
)
def test_undefined_auc(population, labels, signals, reason):
    result = auc_roc(population, labels, signals, task=TASK, view=VIEW)
    assert result.value is None
    assert result.reason == reason


def test_missing_scores_and_labels_have_independent_counts():
    result = auc_roc(
        ["a", "b", "c", "d"],
        [label("a", 1), label("b", 0)],
        [signal("a", 0.8), signal("b", None), signal("c", 0.4)],
        task=TASK,
        view=VIEW,
    )
    assert (
        result.population_count,
        result.labeled_count,
        result.scored_count,
        result.joined_count,
    ) == (4, 2, 2, 1)
    assert (result.missing_score_count, result.missing_label_count) == (2, 2)
    assert (result.accepted_count, result.accepted_without_label_count) == (0, 0)


def test_externally_accepted_precision_and_unlabeled_acceptance():
    result = accepted_claim_precision(
        ["a", "b", "c", "d", "e"],
        [label("a", 1), label("b", 1), label("c", 0), label("e", 0)],
        [
            decision("a", True),
            decision("b", True),
            decision("c", True),
            decision("d", True),
            decision("e", False),
        ],
        task=TASK,
    )
    assert result.value == pytest.approx(2 / 3)
    assert result.view == "external_acceptance"
    assert (
        result.population_count,
        result.labeled_count,
        result.joined_count,
        result.accepted_count,
    ) == (5, 4, 3, 4)
    assert (result.missing_label_count, result.accepted_without_label_count) == (1, 1)
    assert (result.scored_count, result.missing_score_count) == (0, 0)


@pytest.mark.parametrize(
    "labels,decisions",
    [([], []), ([], [decision("a", True)]), ([label("a", 1)], [decision("a", False)])],
)
def test_no_labeled_accepted_is_undefined(labels, decisions):
    result = accepted_claim_precision(["a"], labels, decisions, task=TASK)
    assert result.value is None
    assert result.reason == "no_labeled_accepted"


def test_four_judge_views_reuse_labels_in_separate_calls():
    labels = [label("a", 1), label("b", 0)]
    for view in (
        "family-a-evidence",
        "family-a-claim",
        "family-b-evidence",
        "family-b-claim",
    ):
        result = auc_roc(
            ["a", "b"],
            labels,
            [signal("a", 0.8, view), signal("b", 0.2, view)],
            task=TASK,
            view=view,
        )
        assert (result.value, result.labeled_count, result.joined_count) == (1.0, 2, 2)


@pytest.mark.parametrize(
    "population,labels,signals",
    [
        (["a", "a"], [], []),
        (["a"], [label("a", 1), label("a", 0)], []),
        (["a"], [], [signal("a", 0.1), signal("a", 0.2)]),
        (["a"], [label("foreign", 1)], []),
        (["a"], [], [signal("foreign", 0.1)]),
        (["a"], [label("a", 1, "claim_support")], []),
        (["a"], [], [signal("a", 0.1, task="claim_support")]),
        (["a"], [], [signal("a", 0.1, view="other")]),
        ([""], [], []),
        ([True], [], []),
    ],
)
def test_invalid_auc_joins_are_refused(population, labels, signals):
    with pytest.raises(ValueError, match="invalid_references"):
        auc_roc(population, labels, signals, task=TASK, view=VIEW)


@pytest.mark.parametrize(
    "decisions",
    [
        [decision("a", True), decision("a", False)],
        [decision("foreign", True)],
        [decision("a", True, "claim_support")],
    ],
)
def test_invalid_acceptance_joins_are_refused(decisions):
    with pytest.raises(ValueError, match="invalid_references"):
        accepted_claim_precision(["a"], [], decisions, task=TASK)


@pytest.mark.parametrize("value", [True, False, 2, -1, 1.0, "1"])
def test_labels_are_strict_binary_integers(value):
    with pytest.raises(ValidationError):
        label("a", value)


@pytest.mark.parametrize("value", [True, float("nan"), float("inf"), -0.1, 1.1, "0.5"])
def test_scores_refuse_invalid_values(value):
    with pytest.raises(ValidationError):
        signal("a", value)


@pytest.mark.parametrize("value", [1, 0, "true"])
def test_acceptance_is_strict_bool(value):
    with pytest.raises(ValidationError):
        decision("a", value)


def test_parts_are_closed_frozen_and_safe_to_render():
    for model in (
        label("secret-target", 1),
        signal("secret-target", 0.2, "secret-view"),
        decision("secret-target", True),
    ):
        assert "secret" not in repr(model)
        assert "secret" not in str(model)
        with pytest.raises(ValidationError):
            type(model)(**model.model_dump(), unexpected="secret")
        with pytest.raises(ValidationError):
            model.target_id = "changed"


def test_copied_invalid_model_is_revalidated_at_metric_boundary():
    forged = label("a", 1).model_copy(update={"supported": True})
    with pytest.raises(ValueError, match="malformed_record"):
        auc_roc(["a"], [forged], [], task=TASK, view=VIEW)


def test_report_reasons_and_counts_are_closed():
    result = auc_roc([], [], [], task=TASK, view=VIEW)
    with pytest.raises(ValidationError):
        MetricReport(**(result.model_dump() | {"reason": "secret"}))
    with pytest.raises(ValidationError):
        MetricReport(**(result.model_dump() | {"population_count": True}))


@pytest.mark.parametrize(
    "model",
    [
        label("a", 1).model_copy(update={"supported": object()}),
        signal("a", 0.2).model_copy(update={"score": object()}),
        decision("a", True).model_copy(update={"accepted": object()}),
    ],
)
def test_unserializable_copied_input_has_fixed_error(model):
    with pytest.raises(ValueError, match="^malformed_record$"):
        if isinstance(model, Acceptance):
            accepted_claim_precision(["a"], [], [model], task=TASK)
        elif isinstance(model, ContinuousSignal):
            auc_roc(["a"], [], [model], task=TASK, view=VIEW)
        else:
            auc_roc(["a"], [model], [], task=TASK, view=VIEW)


def test_raw_unexpected_keys_are_refused_without_rendering():
    with pytest.raises(ValueError, match="^malformed_record$") as error:
        auc_roc(
            ["a"],
            [
                {
                    "target_id": "a",
                    "task": TASK,
                    "supported": 1,
                    "secret-key": "secret-value",
                }
            ],
            [],
            task=TASK,
            view=VIEW,
        )
    assert "secret" not in str(error.value)


@pytest.mark.parametrize("task,view", [("other", VIEW), (TASK, ""), (TASK, True)])
def test_invalid_selection_has_fixed_error(task, view):
    with pytest.raises(ValueError, match="^invalid_references$"):
        auc_roc([], [], [], task=task, view=view)


def test_metric_report_safe_rendering():
    result = auc_roc([], [], [], task=TASK, view="secret-view")
    assert "secret" not in str(result)
    assert "secret" not in repr(result)
