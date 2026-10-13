"""V6's gates: derived from the dev baseline, and a configuration that rejects
everything fails them (the Stage 11 spec, A3 and FP15; R12.8)."""

from dataclasses import replace

import pytest
from earnings_themes.evaluation.gates import (
    derive_gates,
    evaluate_gates,
    gates_toml,
    load_gates,
)
from earnings_themes.evaluation.preregistration import REQUIRED_GATES, GateRule
from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
from earnings_themes.evaluation.records import Metric, PilotReport, sealed
from earnings_themes.evaluation.report import EventObservation, partition_report
from earnings_themes.records import RecordError
from earnings_themes.split import Partition

from .test_report import BOOK, PLAN, labelled, observations

HASH = "1" * 64
GATED = tuple(sorted(REQUIRED_GATES))


def rule(undefined_gate="not_gated"):
    return GateRule(
        rule="dev-lower-bound/1", gated=GATED, undefined_gate=undefined_gate
    )


def pilot(dev) -> PilotReport:
    return sealed(
        PilotReport(
            report_version=1,
            preregistration_hash=HASH,
            calibration_hash=HASH,
            partitions=(
                dev.model_copy(
                    update={"partition": Partition.TRAIN, "in_sample": True}
                ),
                dev,
            ),
            content_hash="0" * 64,
        )
    )


@pytest.fixture(scope="module")
def baseline():
    return partition_report(
        observations(), labelled(), BOOK, PLAN, partition=Partition.DEV
    )


def gates_of(baseline, **options):
    return derive_gates(
        pilot(baseline),
        rule=rule(options.get("undefined_gate", "not_gated")),
        judge_floor=0.4,
        preregistration_hash=HASH,
    )


def test_each_gate_is_the_baselines_lower_bound(baseline) -> None:
    gates = gates_of(baseline)
    for gate in gates.gates:
        figure = baseline.figure(gate.metric)
        assert gate.basis == "lower_bound"
        assert gate.bound == figure.interval.lower
    assert {g.metric for g in gates.gates} | {u.metric for u in gates.ungated} == set(
        GATED
    )
    assert gates.report_hash == pilot(baseline).content_hash


def test_the_baseline_passes_its_own_gates(baseline) -> None:
    verdict = evaluate_gates(gates_of(baseline), baseline)
    assert verdict.passed, verdict.results


def test_a_configuration_that_rejects_everything_fails(baseline) -> None:
    """R12.8: no accepted assignment leaves gold-evidence recall at zero and
    support precision undefined, and either fails whatever the bounds."""
    rejecting = tuple(
        EventObservation(
            o.event_id, o.gold, o.index, (), o.release_confirmed, o.quotes, (0, 1)
        )
        for o in observations()
    )
    labels = tuple(replace(t, accepted=False) for t in labelled())
    report = partition_report(rejecting, labels, BOOK, PLAN, partition=Partition.DEV)
    gates = gates_of(baseline)
    assert {Metric.SUPPORT_PRECISION, Metric.GOLD_EVIDENCE_RECALL} <= {
        g.metric for g in gates.gates
    }
    verdict = evaluate_gates(gates, report)
    assert not verdict.passed
    failed = {(r.metric, r.reason) for r in verdict.results if not r.passed}
    assert (Metric.GOLD_EVIDENCE_RECALL, "zero_gold_evidence_recall") in failed
    assert (Metric.SUPPORT_PRECISION, "undefined") in failed


def test_an_undefined_interval_is_ungated_or_gated_at_the_point(baseline) -> None:
    figures = tuple(
        f.model_copy(update={"interval": f.interval.model_copy(update={"lower": None})})
        if f.metric is Metric.SPAN_UNIT_F1
        else f
        for f in baseline.figures
    )
    dev = baseline.model_copy(update={"figures": figures})
    off = gates_of(dev)
    assert [(u.metric, u.reason) for u in off.ungated] == [
        (Metric.SPAN_UNIT_F1, "undefined_interval")
    ]
    on = gates_of(dev, undefined_gate="point_estimate")
    gate = next(g for g in on.gates if g.metric is Metric.SPAN_UNIT_F1)
    assert (gate.basis, gate.bound) == ("point_estimate", 0.5)


def test_gates_round_trip_through_toml_and_refuse_a_changed_file(
    baseline, tmp_path
) -> None:
    gates = gates_of(baseline)
    path = tmp_path / "gates-v1.toml"
    path.write_text(gates_toml(gates), encoding="utf-8")
    assert load_gates(path) == gates
    path.write_text(
        gates_toml(gates).replace("judge_floor = 0.4", "judge_floor = 0.5"),
        encoding="utf-8",
    )
    with pytest.raises(RecordError, match="content_hash"):
        load_gates(path)


def test_gates_need_the_dev_partition_and_its_preregistration(baseline) -> None:
    train = baseline.model_copy(
        update={"partition": Partition.TRAIN, "in_sample": True}
    )
    with pytest.raises(EvaluationError, match="wrong_partition"):
        derive_gates(
            pilot(baseline).model_copy(update={"partitions": (train,)}),
            rule=rule(),
            judge_floor=0.4,
            preregistration_hash=HASH,
        )
    with pytest.raises(EvaluationError) as refused:
        derive_gates(
            pilot(baseline),
            rule=rule(),
            judge_floor=0.4,
            preregistration_hash="2" * 64,
        )
    assert refused.value.problem is EvaluationProblem.PREREGISTRATION_MISMATCH
    assert refused.value.subject == "preregistration_hash"
    with pytest.raises(EvaluationError, match="wrong_partition"):
        evaluate_gates(gates_of(baseline), train)


def without_gold_evidence(report, point):
    """``report`` with gold-evidence recall's point set to ``point``."""
    figures = tuple(
        f.model_copy(update={"point": point})
        if f.metric is Metric.GOLD_EVIDENCE_RECALL
        else f
        for f in report.figures
    )
    return report.model_copy(update={"figures": figures})


@pytest.mark.parametrize(
    ("point", "reason"),
    [(None, "undefined"), (0.0, "zero_gold_evidence_recall"), (0.5, "met")],
)
def test_the_gold_evidence_rule_names_why_it_fails(baseline, point, reason) -> None:
    """R12.8's rule: recall strictly above zero passes; zero fails as
    ``zero_gold_evidence_recall``, and an undefined recall fails as ``undefined``,
    as every other gate's does."""
    verdict = evaluate_gates(gates_of(baseline), without_gold_evidence(baseline, point))
    rule = next(
        r
        for r in verdict.results
        if r.metric is Metric.GOLD_EVIDENCE_RECALL and r.bound is None
    )
    assert (rule.value, rule.passed, rule.reason) == (point, point == 0.5, reason)


def test_a_missing_gold_evidence_figure_is_undefined(baseline) -> None:
    figures = tuple(
        f for f in baseline.figures if f.metric is not Metric.GOLD_EVIDENCE_RECALL
    )
    verdict = evaluate_gates(
        gates_of(baseline), baseline.model_copy(update={"figures": figures})
    )
    rule = next(
        r
        for r in verdict.results
        if r.metric is Metric.GOLD_EVIDENCE_RECALL and r.bound is None
    )
    assert (rule.value, rule.passed, rule.reason) == (None, False, "undefined")
