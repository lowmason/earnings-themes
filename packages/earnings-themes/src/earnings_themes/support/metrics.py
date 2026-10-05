"""Pure metrics over explicitly joined human labels and external decisions.

Each call selects one task and one signal view. No missing observation becomes a
negative, and these functions neither choose a view nor derive acceptance.
"""

from collections.abc import Sequence
from typing import Literal, Self

from pydantic import Field, NonNegativeInt, field_validator, model_validator

from earnings_themes.records import NonBlank
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import SafePart, Score, parse_support

LabelTask = Literal["claim_support", "joint_support"]


class HumanLabel(SafePart):
    target_id: NonBlank = Field(repr=False)
    task: LabelTask
    supported: Literal[0, 1]

    @field_validator("supported", mode="before")
    @classmethod
    def _binary_integer(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("invalid_label")
        return value


class ContinuousSignal(SafePart):
    target_id: NonBlank = Field(repr=False)
    task: LabelTask
    view: NonBlank = Field(repr=False)
    score: Score | None


class Acceptance(SafePart):
    target_id: NonBlank = Field(repr=False)
    task: LabelTask
    accepted: bool


class MetricReport(SafePart):
    value: Score | None
    reason: Literal["no_scored_labels", "one_class", "no_labeled_accepted"] | None
    task: LabelTask
    view: NonBlank = Field(repr=False)
    population_count: NonNegativeInt
    labeled_count: NonNegativeInt
    scored_count: NonNegativeInt
    joined_count: NonNegativeInt
    accepted_count: NonNegativeInt
    missing_score_count: NonNegativeInt
    missing_label_count: NonNegativeInt
    accepted_without_label_count: NonNegativeInt

    @field_validator("value", mode="before")
    @classmethod
    def _numeric_value(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("invalid_score")  # noqa: TRY004 - Pydantic collects ValueError
        return value

    @model_validator(mode="after")
    def _distinct_references_and_fixed_reasons(self) -> Self:
        # Metric undefined reasons have their own closed vocabulary, rather than
        # support-processing refusal reasons inherited by other SafePart models.
        if (self.value is None) != (self.reason is not None):
            raise ValueError("invalid_metric_result")
        return self


def _population(population: Sequence[str], task: LabelTask, view: str) -> set[str]:
    if task not in ("claim_support", "joint_support"):
        raise SupportError("invalid_references")
    if type(view) is not str or not view.strip():
        raise SupportError("invalid_references")
    if isinstance(population, (str, bytes)):
        raise SupportError("invalid_references")
    ids: set[str] = set()
    for target_id in population:
        if type(target_id) is not str or not target_id.strip() or target_id in ids:
            raise SupportError("invalid_references")
        ids.add(target_id)
    return ids


def _index[M: HumanLabel | ContinuousSignal | Acceptance](
    records: Sequence[M],
    model: type[M],
    population: set[str],
    task: LabelTask,
    view: str | None = None,
) -> dict[str, M]:
    indexed: dict[str, M] = {}
    for record in records:
        if type(record) is not model:
            raise SupportError("malformed_record")
        try:
            data = record.model_dump(mode="json", warnings=False)
        except (ValueError, TypeError, OverflowError):
            raise SupportError("malformed_record") from None
        checked = parse_support(data, model)
        if (
            checked.target_id not in population
            or checked.target_id in indexed
            or checked.task != task
            or (view is not None and checked.view != view)
        ):
            raise SupportError("invalid_references")
        indexed[checked.target_id] = checked
    return indexed


def ranked_auc(positives: list[float], negatives: list[float]) -> float | None:
    """Pairwise ranking probability, awarding ties half credit."""
    if not positives or not negatives:
        return None
    wins = sum(
        1.0 if positive > negative else 0.5 if positive == negative else 0.0
        for positive in positives
        for negative in negatives
    )
    return wins / (len(positives) * len(negatives))


def precision_value(labeled_accepted: list[int]) -> float | None:
    """Supported fraction among externally accepted, human-labeled targets."""
    if not labeled_accepted:
        return None
    return sum(labeled_accepted) / len(labeled_accepted)


def auc_roc(
    population: Sequence[str],
    labels: Sequence[HumanLabel],
    signals: Sequence[ContinuousSignal],
    *,
    task: LabelTask,
    view: str,
) -> MetricReport:
    """Evaluate one explicitly selected continuous view against human labels."""
    ids = _population(population, task, view)
    human = _index(labels, HumanLabel, ids, task)
    continuous = _index(signals, ContinuousSignal, ids, task, view)
    scored = {
        target_id: item.score
        for target_id, item in continuous.items()
        if item.score is not None
    }
    joined = human.keys() & scored.keys()
    positives = [scored[i] for i in joined if human[i].supported == 1]
    negatives = [scored[i] for i in joined if human[i].supported == 0]
    value = ranked_auc(positives, negatives)
    reason = (
        None if value is not None else "one_class" if joined else "no_scored_labels"
    )
    return MetricReport(
        value=value,
        reason=reason,
        task=task,
        view=view,
        population_count=len(ids),
        labeled_count=len(human),
        scored_count=len(scored),
        joined_count=len(joined),
        accepted_count=0,
        missing_score_count=len(ids) - len(scored),
        missing_label_count=len(ids) - len(human),
        accepted_without_label_count=0,
    )


def accepted_claim_precision(
    population: Sequence[str],
    labels: Sequence[HumanLabel],
    decisions: Sequence[Acceptance],
    *,
    task: LabelTask,
) -> MetricReport:
    """Join external acceptance to labels; unlabeled accepted cases stay visible."""
    ids = _population(population, task, "external_acceptance")
    human = _index(labels, HumanLabel, ids, task)
    external = _index(decisions, Acceptance, ids, task)
    accepted = {target_id for target_id, item in external.items() if item.accepted}
    joined = accepted & human.keys()
    value = precision_value([human[i].supported for i in joined])
    return MetricReport(
        value=value,
        reason=None if value is not None else "no_labeled_accepted",
        task=task,
        view="external_acceptance",
        population_count=len(ids),
        labeled_count=len(human),
        scored_count=0,
        joined_count=len(joined),
        accepted_count=len(accepted),
        missing_score_count=0,
        missing_label_count=len(ids) - len(human),
        accepted_without_label_count=len(accepted - human.keys()),
    )
