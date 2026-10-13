"""Counts and stability diagnostics, over invented readings and observations."""

from dataclasses import replace

import pytest
from earnings_themes.evaluation.align import unit_index
from earnings_themes.evaluation.cells import event_cells
from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
from earnings_themes.evaluation.records import Metric
from earnings_themes.evaluation.report import (
    compare_readings,
    partition_report,
    stability_figures,
)
from earnings_themes.evaluation.scores import hard_negative_counts
from earnings_themes.gold import DraftCounts, NegativeKind
from earnings_themes.split import Partition

from .cases import example, negative, reading
from .test_report import BOOK, PLAN, observations


def test_gs5_figures_retain_the_counts_and_their_denominator():
    rows = observations()
    counts = (
        DraftCounts(accepted=3, edited=1, rejected=2, added=1),
        DraftCounts(accepted=2, edited=1, rejected=1, added=3),
    )
    rows = tuple(
        replace(o, gold=o.gold.model_copy(update={"counts": c}))
        for o, c in zip(rows, counts, strict=True)
    )
    report = partition_report(rows, (), BOOK, PLAN, partition=Partition.DEV)
    for metric, numerator, denominator in (
        (Metric.GS5_EDITED_SHARE, 2, 10),
        (Metric.GS5_REJECTED_SHARE, 3, 10),
        (Metric.GS5_ADDED_SHARE, 4, 11),
    ):
        assert dict(report.figure(metric).counts) == {
            "accepted": 5,
            "edited": 2,
            "rejected": 3,
            "added": 4,
            "numerator": numerator,
            "denominator": denominator,
        }


def test_stability_requires_unique_run_ids():
    rows = observations()
    with pytest.raises(EvaluationError) as refused:
        stability_figures((rows, rows), BOOK, PLAN, run_ids=("fresh1", "fresh1"))
    assert (refused.value.problem, refused.value.subject) == (
        EvaluationProblem.MALFORMED_RECORD,
        "fresh1",
    )


def test_stability_refuses_a_duplicate_event_by_run_and_event_id():
    rows = observations()
    with pytest.raises(EvaluationError) as refused:
        stability_figures(
            ((*rows, rows[0]), (*rows, rows[0])),
            BOOK,
            PLAN,
            run_ids=("fresh1", "fresh2"),
        )
    assert (refused.value.problem, refused.value.subject) == (
        EvaluationProblem.MALFORMED_RECORD,
        "fresh1:e1",
    )


def test_stability_names_the_run_with_a_different_event_set():
    rows = observations()
    with pytest.raises(EvaluationError) as refused:
        stability_figures((rows, rows[:1]), BOOK, PLAN, run_ids=("fresh1", "fresh2"))
    assert refused.value.subject == "fresh2"


@pytest.mark.parametrize("ids", [(), ("fresh1",), ("fresh1", " ")])
def test_stability_refuses_invalid_run_ids(ids):
    rows = observations()
    with pytest.raises(EvaluationError) as refused:
        stability_figures((rows, rows), BOOK, PLAN, run_ids=ids)
    assert refused.value.problem is EvaluationProblem.MALFORMED_RECORD
    assert refused.value.subject == "run_ids"


def test_negative_dangling_quotes_are_tolerated_counted_and_not_false_hits():
    source, complete = example()
    missing = reading(
        negatives=(negative("n-missing", "absent", NegativeKind.PERIOD, "capacity"),)
    )
    index = unit_index(source)
    dangling = event_cells(missing, index).dangling
    negative_counts = hard_negative_counts(missing, index, {})
    one_dangling = compare_readings(complete, missing, index).dangling
    both_dangling = compare_readings(missing, missing, index).dangling
    assert dangling == 1, "dangling_count_mismatch"
    assert negative_counts == {NegativeKind.PERIOD: (1, 0)}, "negative_count_mismatch"
    assert one_dangling == 1, "dangling_count_mismatch"
    assert both_dangling == 2, "dangling_count_mismatch"
