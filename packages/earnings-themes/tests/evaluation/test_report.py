"""A partition's figures, with hand-computed known answers (the Stage 11 spec,
§Metrics; R12.5, R12.7, R12.8, R12.10, R13.1)."""

from dataclasses import replace
from types import SimpleNamespace

import pytest
from earnings_themes.evaluation.align import unit_index
from earnings_themes.evaluation.bootstrap import BootstrapPlan
from earnings_themes.evaluation.cells import event_cells
from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
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
from earnings_themes.evaluation.scores import char_counts, unit_tally
from earnings_themes.gold import DraftCounts, ReleaseLabel, Support
from earnings_themes.split import Partition

from .cases import (
    bundle,
    claim,
    example,
    gold,
    panel,
    quote,
    reading,
    row,
    unit_ids,
)

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
        (Metric.JUDGE_AC1, "f0", 1 / 3),
        (Metric.JUDGE_AC1, "f0:evidence_first", 1 / 3),
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


def test_the_span_figures_count_each_side(report) -> None:
    """e1: g1 resolves to the predicted pricing; cells capacity {P0} and g1 {P1,
    P2}. Accepted: capacity {P0, P3} (1 hit), pricing {P1} (1 hit), debt {P3},
    decided against, so scored (0 hits): 2 of 4. Gold: P0 and P1 covered, P2 not: 2
    of 3. e2 has no gold cell; its accepted capacity {P0} is scored: 0 of 1. Summed:
    precision 2/5, recall 2/3, F1 = 2 * 2 * 2 / (2 * 3 + 2 * 5) = 1/2. Characters:
    e1 accepts 36 + 16 + 16 = 68 with 5 + 7 = 12 hits, its gold 5 + 15 = 20 with 12
    covered, union 68 + 20 - 12 = 76; e2 accepts 20, union 20: 12 / 96."""
    units = {"accepted": 5, "accepted_hits": 2, "gold": 3, "gold_hits": 2}
    for metric in (
        Metric.SPAN_UNIT_PRECISION,
        Metric.SPAN_UNIT_RECALL,
        Metric.SPAN_UNIT_F1,
    ):
        assert dict(report.figure(metric).counts) == units
    jaccard = report.figure(Metric.SPAN_CHAR_JACCARD)
    assert dict(jaccard.counts) == {"shared": 12, "union": 96}


def test_judge_agreement_counts_uncertain_verdicts_over_joint_labelled_events() -> None:
    """Over ``observations()``'s events: e1 holds t1, t2 and t3, each with a joint
    label; e2 holds only t4, whose joint label is left out (claim 1, fit unsure).

    Family verdicts (a family supports only when both presentations answer
    ``supported`` and ``fits``): t1 is (f0 1, f1 1); t2 is (f0 0, uncertain; f1 0,
    opposes); t3 is (f0 0, opposes; f1 0, uncertain). Pairs (verdict, joint label)
    for each family: (1, 1), (0, 0), (0, 1). Observed 2/3; verdict share 1/3, label
    share 2/3. κ chance = 1/3 * 2/3 + 2/3 * 1/3 = 4/9, κ = (2/3 - 4/9) / (5/9) = 2/5.
    AC1 mean = 1/2, chance = 2 * 1/2 * 1/2 = 1/2, AC1 = (2/3 - 1/2) / (1/2) = 1/3.
    Each family has 3 labels, and 1 uncertain consensus (f0's t2, f1's t3).

    The resampled events are those holding a joint label: e1 alone. Every one of the
    50 resamples draws e1 once, so the interval is [2/5, 2/5] with none undefined.
    (Over e1 and e2, ``random.Random(11)`` draws only e2 12 times: 12 undefined.)
    The presentation figures pair the same targets: f0 under ``evidence_first``
    answers t1 ``supported``, t2 ``uncertain`` and t3 ``unsupported``, so it too
    counts 1 uncertain over e1 alone."""
    yes, no, unsure = (
        ("supported", "fits"),
        ("unsupported", "fits"),
        ("uncertain", "fits"),
    )
    targets = (
        LabelledTarget("t1", "e1", 1, 1, False, {}, panel("t1", yes, yes)),
        LabelledTarget("t2", "e1", 0, 0, False, {}, panel("t2", unsure, no)),
        LabelledTarget("t3", "e1", 1, 1, False, {}, panel("t3", no, unsure)),
        LabelledTarget("t4", "e2", 1, None, False, {}, panel("t4", yes, yes)),
    )
    report = partition_report(
        observations(), targets, BOOK, PLAN, partition=Partition.DEV
    )
    for family in ("f0", "f1"):
        for metric, point in ((Metric.JUDGE_KAPPA, 2 / 5), (Metric.JUDGE_AC1, 1 / 3)):
            figure = report.figure(metric, family)
            assert figure.point == pytest.approx(point)
            assert dict(figure.counts) == {"labels": 3, "uncertain": 1}
            interval = figure.interval
            assert interval.undefined == 0
            assert interval.lower == pytest.approx(point)
            assert interval.upper == pytest.approx(point)
    presentation = report.figure(Metric.JUDGE_KAPPA, "f0:evidence_first")
    assert presentation.point == pytest.approx(2 / 5)
    assert dict(presentation.counts) == {"labels": 3, "uncertain": 1}
    assert presentation.interval.undefined == 0


def test_support_precision_interval_skips_draws_without_an_accepted_label(
    report,
) -> None:
    """``random.Random(11)`` draws two of the sorted events (e1, e2) per resample,
    50 times: 18 draw only e1, 12 only e2, and 20 both. e2 holds no accepted labelled
    target, so a draw of only e2 is undefined. e1's accepted targets are labelled 1
    and 0, so every other draw is 1/2, and the interval is [1/2, 1/2]."""
    interval = report.figure(Metric.SUPPORT_PRECISION).interval
    assert interval.undefined == 12
    assert interval.lower == pytest.approx(0.5)
    assert interval.upper == pytest.approx(0.5)


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


TREE = SimpleNamespace(
    themes=tuple(
        SimpleNamespace(theme_id=t, parent_id=p)
        for t, p in (
            ("capacity", None),
            ("debt", None),
            ("workforce", None),
            ("labor", "workforce"),
            ("hiring", "workforce"),
            ("sales", None),
            ("pricing", "sales"),
            ("demand", "sales"),
        )
    )
)


@pytest.fixture(scope="module")
def tree():
    """One event over a codebook of 8 themes and 4 roots (capacity, debt, workforce
    and sales; labor and hiring sit under workforce, pricing and demand under sales).

    Gold: capacity and labor are supported; hiring, pricing and demand are only
    uncertain; debt is decided against. The run accepts capacity, hiring, demand and
    debt.

    Exact level. Present: capacity, labor. Uncertain-only: hiring, pricing, demand
    (3). Scored cells: capacity is a hit, labor a miss, debt a false positive;
    hiring and demand are uncertain-only, so they score nothing. Micro: tp 1, fp 1,
    fn 1, so F1 = 2 / (2 + 1 + 1) = 1/2. Macro over three themes: (1 + 0 + 0) / 3 =
    1/3, with 8 - 3 = 5 themes left out.

    Roll-up. Present: capacity, workforce. Pricing and demand are two uncertain
    siblings under sales, so they count once, and hiring is uncertain beside a
    present sibling, so it counts for nothing: uncertain-only is {sales} (1).
    Hiring rolls up to workforce, a hit. Scored cells: capacity and workforce are
    hits, debt a false positive; sales is uncertain-only, so it scores nothing.
    Micro: tp 2, fp 1, fn 0, so F1 = 4 / (4 + 1 + 0) = 4/5. Macro over three roots:
    (1 + 0 + 1) / 3 = 2/3, with 4 - 3 = 1 root left out.
    """
    source = bundle()
    p0, p1, p2, p3 = unit_ids(source)
    base = reading(
        quotes=(
            quote("q1", 0, 20, p0),
            quote("q2", 21, 37, p1),
            quote("q3", 38, 56, p2),
            quote("q4", 57, 73, p3),
        ),
        claims=(
            claim("c1", "q1"),
            claim("c2", "q2"),
            claim("c3", "q3"),
            claim("c4", "q4"),
        ),
        assignments=(
            row("c1", "capacity"),
            row("c2", "labor"),
            row("c2", "hiring", Support.UNCERTAIN),
            row("c3", "pricing", Support.UNCERTAIN),
            row("c3", "demand", Support.UNCERTAIN),
            row("c4", "debt", Support.DOES_NOT_SUPPORT),
        ),
    )
    observed = EventObservation(
        event_id="e1",
        gold=gold("e1", base),
        index=unit_index(source),
        accepted=(
            Accepted("capacity", ((0, 20),)),
            Accepted("hiring", ((21, 37),)),
            Accepted("demand", ((38, 56),)),
            Accepted("debt", ((57, 73),)),
        ),
        release_confirmed=True,
        quotes=(4, 4),
        targets=(4, 4),
    )
    return partition_report((observed,), (), TREE, PLAN, partition=Partition.DEV)


def test_the_exact_level_counts_every_theme_and_uncertain_cell(tree) -> None:
    micro = tree.figure(Metric.THEME_F1_MICRO)
    assert micro.point == pytest.approx(1 / 2)
    assert dict(micro.counts) == {"tp": 1, "fp": 1, "fn": 1, "uncertain_left_out": 3}
    macro = tree.figure(Metric.THEME_F1_MACRO)
    assert macro.point == pytest.approx(1 / 3)
    assert dict(macro.counts) == {"themes_scored": 3, "themes_left_out": 5}


def test_the_rollup_micro_counts_its_own_uncertain_cells(tree) -> None:
    micro = tree.figure(Metric.THEME_F1_ROLLUP_MICRO)
    assert micro.point == pytest.approx(4 / 5)
    assert dict(micro.counts) == {"tp": 2, "fp": 1, "fn": 0, "uncertain_left_out": 1}


def test_the_rollup_macro_counts_its_own_roots(tree) -> None:
    macro = tree.figure(Metric.THEME_F1_ROLLUP_MACRO)
    assert macro.point == pytest.approx(2 / 3)
    assert dict(macro.counts) == {"themes_scored": 3, "themes_left_out": 1}


def test_gs5_shares_sum_the_draft_counts_of_every_event() -> None:
    """e1 drafts accepted 3, edited 1 and rejected 2, and adds 1; e2 drafts accepted
    2, edited 1 and rejected 1, and adds 3. Summed: accepted 5, edited 2, rejected 3,
    added 4. Drafted items: 5 + 2 + 3 = 10; signed items: 5 + 2 + 4 = 11. Edited 2/10,
    rejected 3/10, added 4/11."""
    counts = (
        DraftCounts(accepted=3, edited=1, rejected=2, added=1),
        DraftCounts(accepted=2, edited=1, rejected=1, added=3),
    )
    changed = tuple(
        replace(o, gold=o.gold.model_copy(update={"counts": c}))
        for o, c in zip(observations(), counts, strict=True)
    )
    shares = partition_report(changed, (), BOOK, PLAN, partition=Partition.DEV)
    assert shares.figure(Metric.GS5_EDITED_SHARE).point == pytest.approx(2 / 10)
    assert shares.figure(Metric.GS5_REJECTED_SHARE).point == pytest.approx(3 / 10)
    assert shares.figure(Metric.GS5_ADDED_SHARE).point == pytest.approx(4 / 11)


def test_a_duplicated_event_is_refused_by_its_id() -> None:
    first, second = observations()
    with pytest.raises(EvaluationError) as refused:
        partition_report(
            (first, second, second), (), BOOK, PLAN, partition=Partition.DEV
        )
    assert refused.value.problem is EvaluationProblem.MALFORMED_RECORD
    assert refused.value.subject == "e2"


def test_a_duplicated_target_is_refused_by_its_id() -> None:
    targets = labelled()
    with pytest.raises(EvaluationError) as refused:
        partition_report(
            observations(),
            (*targets, targets[2]),
            BOOK,
            PLAN,
            partition=Partition.DEV,
        )
    assert refused.value.problem is EvaluationProblem.DUPLICATE_TARGET
    assert refused.value.subject == "t3"


def test_an_observation_over_another_events_gold_is_malformed() -> None:
    first, second = observations()
    with pytest.raises(EvaluationError) as refused:
        partition_report(
            (replace(first, gold=second.gold),), (), BOOK, PLAN, partition=Partition.DEV
        )
    assert refused.value.problem is EvaluationProblem.MALFORMED_RECORD
    assert refused.value.subject == "e1"


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


def overlapping_ties():
    """Pricing supported untied by c0 (P0); tie group g1 over demand and pricing by
    c1 (P1); tie group g2 over demand and labor by c2 (P2)."""
    source = bundle()
    p0, p1, p2, _ = unit_ids(source)
    return source, reading(
        quotes=(
            quote("q0", 0, 20, p0),
            quote("q1", 21, 37, p1),
            quote("q2", 38, 56, p2),
        ),
        claims=(claim("c0", "q0"), claim("c1", "q1"), claim("c2", "q2")),
        assignments=(
            row("c0", "pricing"),
            row("c1", "demand", tie_group="g1"),
            row("c1", "pricing", tie_group="g1"),
            row("c2", "demand", tie_group="g2"),
            row("c2", "labor", tie_group="g2"),
        ),
    )


def shared_quote_ties():
    """Tie group g1 over capacity and demand by c1, and g2 over demand and pricing by
    c2, both quoting q1 (P0)."""
    source = bundle()
    p0 = unit_ids(source)[0]
    return source, reading(
        quotes=(quote("q1", 0, 20, p0),),
        claims=(claim("c1", "q1"), claim("c2", "q1")),
        assignments=(
            row("c1", "capacity", tie_group="g1"),
            row("c1", "demand", tie_group="g1"),
            row("c2", "demand", tie_group="g2"),
            row("c2", "pricing", tie_group="g2"),
        ),
    )


def untied_and_tied_share_a_unit():
    """Capacity supported untied by c0, quoting [0, 5); tie group g1 over capacity
    and pricing by c1, quoting [10, 15): both quotes lie in P0 (N1)."""
    source = bundle()
    p0 = unit_ids(source)[0]
    return source, reading(
        quotes=(quote("q0", 0, 5, p0), quote("q1", 10, 15, p0)),
        claims=(claim("c0", "q0"), claim("c1", "q1")),
        assignments=(
            row("c0", "capacity"),
            row("c1", "capacity", tie_group="g1"),
            row("c1", "pricing", tie_group="g1"),
        ),
    )


@pytest.mark.parametrize(
    "case",
    [example, overlapping_ties, shared_quote_ties, untied_and_tied_share_a_unit],
)
def test_a_reading_compared_with_itself_agrees_fully(case) -> None:
    """A reading scored against itself, its present themes and their evidence taken
    as a run's, agrees fully on units and characters, whatever its tie groups.

    ``overlapping_ties``: as the run, the reading resolves with nothing predicted:
    g1 to pricing (present untied), g2 to demand (lowest ID), so it predicts pricing
    over P0 and P1, and demand over P2. As the reference, g1 resolves to demand, the
    lower predicted member. The evidence cells are pricing's own {P0}, g1's {P1}
    (demand or pricing) and g2's {P2} (demand or labor): all 3 gold units covered;
    pricing's P0 and P1 lie in its cells and demand's P2 in g2: 3 of 3 accepted.
    Unit precision, recall and F1 1; characters 54 accepted, all hits, 54 gold, all
    covered, Jaccard 54 / 54. (Before the tie cells: tp 2, fp 1, fn 1, unit F1 2/3.)

    ``untied_and_tied_share_a_unit`` (N1): the run predicts capacity over P0, with
    spans [0, 5) and [10, 15). Gold cells capacity {P0} and g1 {P0}, both covered:
    2 of 2; accepted (capacity, P0), in its cells, once: 1 of 1. Characters: 10
    accepted, all hits; 5 + 5 gold, all covered: Jaccard 10 / 10."""
    source, gold = case()
    index = unit_index(source)
    agreement = compare_readings(gold, gold, index)
    assert agreement.theme_f1 == 1.0
    assert agreement.unit_f1 == 1.0
    theirs = event_cells(gold, index)
    mine = event_cells(gold, index, theirs.present)
    units = unit_tally(mine, theirs.units)
    assert (units.precision(), units.recall(), units.f1()) == (1.0, 1.0, 1.0)
    chars = char_counts(mine, theirs.spans)
    assert chars.jaccard() == 1.0


def test_stability_over_identical_and_empty_runs() -> None:
    runs = observations()
    same = stability_figures((runs, runs), BOOK, PLAN, run_ids=("fresh1", "fresh2"))
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
    apart = {
        f.metric: f.point
        for f in stability_figures(
            (runs, empty), BOOK, PLAN, run_ids=("fresh1", "fresh2")
        )
    }
    assert apart[Metric.STABILITY_FLEISS_KAPPA] == pytest.approx(-0.2)
    assert apart[Metric.STABILITY_UNIT_JACCARD] == 0.0
    # Every resample holds an event with accepted pairs in the first run (e1: four,
    # e2: one) and none in the empty run, so the intersection is 0 over a non-empty
    # union, and the mean over the one pair of runs is 0.
    assert apart[Metric.STABILITY_ASSIGNMENT_JACCARD] == 0.0
    with pytest.raises(EvaluationError, match="malformed_record"):
        stability_figures((runs,), BOOK, PLAN, run_ids=("fresh1",))
