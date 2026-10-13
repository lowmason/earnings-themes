"""A partition's figures, with hand-computed known answers (the Stage 11 spec,
§Metrics; R12.5, R12.7, R12.8, R12.10, R13.1)."""

from types import SimpleNamespace

import pytest
from earnings_themes.evaluation.align import unit_index
from earnings_themes.evaluation.bootstrap import BootstrapPlan
from earnings_themes.evaluation.problems import EvaluationError
from earnings_themes.evaluation.records import Metric
from earnings_themes.evaluation.report import (
    NOT_ESTIMATED,
    Accepted,
    EventObservation,
    LabelledTarget,
    compare_readings,
    partition_report,
    stability_figures,
)
from earnings_themes.gold import ReleaseLabel
from earnings_themes.split import Partition

from .cases import claim, example, gold, panel, quote, reading, row, unit_ids

PLAN = BootstrapPlan(seed=11, resamples=50, level=0.9, max_undefined_share=0.5)
BOOK = SimpleNamespace(
    themes=tuple(
        SimpleNamespace(theme_id=t, parent_id=None)
        for t in ("capacity", "costs", "debt", "demand", "labor", "pricing")
    )
)


def observations() -> tuple[EventObservation, EventObservation]:
    source, first = example()
    p0 = unit_ids(source)[0]
    index = unit_index(source)
    second = reading(
        quotes=(quote("q1", 0, 20, p0),),
        claims=(claim("c1", "q1"),),
        assignments=(row("c1", "unmatched"),),
        label=ReleaseLabel.NOT_RELEASE,
    )
    return (
        EventObservation(
            event_id="e1",
            gold=gold("e1", first),
            index=index,
            accepted=(
                Accepted("pricing", ((21, 37),)),
                Accepted("capacity", ((0, 20),)),
                Accepted("capacity", ((57, 73),)),
                Accepted("debt", ((57, 73),)),
            ),
            release_confirmed=True,
            quotes=(3, 4),
            targets=(3, 5),
        ),
        EventObservation(
            event_id="e2",
            gold=gold("e2", second, no_theme=True),
            index=index,
            accepted=(Accepted("capacity", ((0, 20),)),),
            release_confirmed=True,
            quotes=(1, 2),
            targets=(1, 1),
        ),
    )


def labelled() -> tuple[LabelledTarget, ...]:
    yes, no, unsure = (
        ("supported", "fits"),
        ("unsupported", "fits"),
        ("uncertain", "fits"),
    )
    return (
        LabelledTarget(
            "t1",
            "e1",
            1,
            1,
            True,
            {"minicheck": 0.9, "deberta": 0.8},
            panel("t1", yes, yes),
        ),
        LabelledTarget(
            "t2",
            "e1",
            0,
            0,
            True,
            {"minicheck": 0.7, "deberta": 0.9},
            panel("t2", yes, no),
        ),
        LabelledTarget(
            "t3",
            "e2",
            1,
            None,
            False,
            {"minicheck": 0.4, "deberta": None},
            panel("t3", unsure, yes),
        ),
        LabelledTarget(
            "t4",
            "e2",
            0,
            0,
            False,
            {"minicheck": 0.2, "deberta": 0.1},
            panel("t4", ("unsupported", "does_not_fit"), no),
        ),
    )


@pytest.fixture(scope="module")
def report():
    return partition_report(
        observations(), labelled(), BOOK, PLAN, partition=Partition.DEV
    )


@pytest.mark.parametrize(
    ("metric", "qualifier", "point"),
    [
        (Metric.THEME_F1_MICRO, None, 2 / 3),
        (Metric.THEME_F1_MACRO, None, 5 / 9),
        (Metric.SPAN_UNIT_PRECISION, None, 2 / 5),
        (Metric.SPAN_UNIT_RECALL, None, 2 / 3),
        (Metric.SPAN_UNIT_F1, None, 0.5),
        (Metric.SPAN_CHAR_JACCARD, None, 12 / 96),
        (Metric.RETENTION_QUOTES, None, 4 / 6),
        (Metric.RETENTION_TARGETS, None, 4 / 6),
        (Metric.GOLD_EVIDENCE_RECALL, None, 2 / 3),
        (Metric.RELEASE_PRECISION, None, 0.5),
        (Metric.RELEASE_RECALL, None, 1.0),
        (Metric.NO_THEME_SHARE, None, 0.5),
        (Metric.HARD_NEGATIVE_FALSE_ACCEPTANCE, None, 0.5),
        (Metric.HARD_NEGATIVE_FALSE_ACCEPTANCE, "period", 1.0),
        (Metric.HARD_NEGATIVE_FALSE_ACCEPTANCE, "issuer", 0.0),
        (Metric.RARE_THEME_RECALL, None, 1.0),
        (Metric.GS5_EDITED_SHARE, None, 0.0),
        (Metric.SUPPORT_PRECISION, None, 0.5),
        (Metric.SCORER_AUC, "minicheck", 0.75),
        (Metric.SCORER_AUC, "deberta", 0.5),
        (Metric.JUDGE_KAPPA, "f0", 0.4),
        (Metric.JUDGE_KAPPA, "f1", 1.0),
        (Metric.JUDGE_KAPPA, "f0:evidence_first", 0.4),
    ],
)
def test_known_answers(report, metric, qualifier, point) -> None:
    figure = report.figure(metric, qualifier)
    assert figure is not None
    assert figure.point == pytest.approx(point)
    assert figure.interval is not None and figure.interval.resamples == PLAN.resamples


def test_counts_keep_what_was_left_out(report) -> None:
    micro = dict(report.figure(Metric.THEME_F1_MICRO).counts)
    assert micro == {"tp": 2, "fp": 2, "fn": 0, "uncertain_left_out": 1}
    macro = dict(report.figure(Metric.THEME_F1_MACRO).counts)
    assert macro == {"themes_scored": 3, "themes_left_out": 3}
    support = dict(report.figure(Metric.SUPPORT_PRECISION).counts)
    assert support == {"labelled": 3, "accepted": 2, "accepted_unlabelled": 0}


def test_dev_is_held_out_and_two_metrics_are_not_estimated(report) -> None:
    assert report.partition is Partition.DEV and not report.in_sample
    assert report.events == ("e1", "e2")
    for metric in (Metric.SECTOR_PREVALENCE, Metric.SOURCE_SELECTION_BIAS):
        figure = report.figure(metric)
        assert figure.point is None and figure.interval is None
        assert figure.reason == NOT_ESTIMATED


def test_the_report_is_deterministic(report) -> None:
    again = partition_report(
        observations(), labelled(), BOOK, PLAN, partition=Partition.DEV
    )
    assert again == report


def test_wrong_partitions_and_unknown_events_are_refused() -> None:
    with pytest.raises(EvaluationError, match="wrong_partition"):
        partition_report(observations(), (), BOOK, PLAN, partition=Partition.TEST)
    with pytest.raises(EvaluationError, match="wrong_partition"):
        partition_report(observations(), (), BOOK, PLAN, partition=Partition.TRAIN)
    stray = LabelledTarget("t9", "e9", 1, 1, True, {}, ())
    with pytest.raises(EvaluationError, match="unknown_event"):
        partition_report(observations(), (stray,), BOOK, PLAN, partition=Partition.DEV)


def test_two_readings_compared() -> None:
    source, reference = example()
    p0 = unit_ids(source)[0]
    other = reading(
        quotes=(quote("q1", 0, 5, p0),),
        claims=(claim("c1", "q1"),),
        assignments=(row("c1", "capacity"),),
    )
    agreement = compare_readings(reference, other, unit_index(source))
    assert agreement.release_agrees is True
    assert agreement.theme_f1 == pytest.approx(2 / 3)
    assert agreement.unit_f1 == pytest.approx(0.5)
    assert agreement.dangling == 0


def test_stability_over_identical_and_empty_runs() -> None:
    runs = observations()
    same = stability_figures((runs, runs), BOOK, PLAN)
    by_metric = {f.metric: f.point for f in same}
    assert by_metric == {
        Metric.STABILITY_FLEISS_KAPPA: pytest.approx(1.0),
        Metric.STABILITY_UNIT_JACCARD: 1.0,
        Metric.STABILITY_ASSIGNMENT_JACCARD: 1.0,
    }
    empty = tuple(
        EventObservation(
            o.event_id, o.gold, o.index, (), o.release_confirmed, o.quotes, o.targets
        )
        for o in runs
    )
    apart = {f.metric: f.point for f in stability_figures((runs, empty), BOOK, PLAN)}
    assert apart[Metric.STABILITY_FLEISS_KAPPA] == pytest.approx(-0.2)
    assert apart[Metric.STABILITY_UNIT_JACCARD] == 0.0
    with pytest.raises(EvaluationError, match="malformed_record"):
        stability_figures((runs,), BOOK, PLAN)
