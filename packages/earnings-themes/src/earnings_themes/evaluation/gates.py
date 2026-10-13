"""V6's gates and the gate evaluator (the Stage 11 spec, A3 and FP15; R12.8, R13.1).

- **The rule** (FP15). Each preregistered gated metric's gate is the dev baseline's
  90% bootstrap lower bound. When that bound is undefined, the preregistration says
  whether the metric is left ungated or gated at the baseline's point estimate.
- **Passing.** A configuration passes when its dev point estimate meets every gate.
  Whatever the gates, gold-evidence recall must be strictly above zero, and an
  undefined (``None``) metric fails its gate, so a configuration that rejects
  everything fails (R12.8).
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from earnings_themes import tomlfile
from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
from earnings_themes.evaluation.records import (
    Gate,
    GateResult,
    Gates,
    GateVerdict,
    Metric,
    PartitionReport,
    PilotReport,
    Ungated,
    checked,
    sealed,
)
from earnings_themes.records import parse
from earnings_themes.split import Partition

HEADER = (
    "Stage 11's V6 gates (FP15): each gated metric's bound is the dev baseline's 90%"
    " bootstrap lower bound. Written by `earnings-pipeline pilot gates`."
)


def derive_gates(
    report: PilotReport,
    *,
    gated: Sequence[Metric],
    undefined_gate: Literal["not_gated", "point_estimate"],
    judge_floor: float,
    preregistration_hash: str,
    version: int = 1,
) -> Gates:
    """V6's gates from ``report``'s dev partition (FP15)."""
    dev = report.partition(Partition.DEV)
    if dev is None:
        raise EvaluationError(EvaluationProblem.WRONG_PARTITION, "dev")
    if report.preregistration_hash != preregistration_hash:
        raise EvaluationError(
            EvaluationProblem.PREREGISTRATION_MISMATCH, "preregistration_hash"
        )
    gates: list[Gate] = []
    ungated: list[Ungated] = []
    for metric in sorted(set(gated)):
        figure = dev.figure(metric)
        if figure is None:
            ungated.append(Ungated(metric=metric, reason="not_in_report"))
        elif figure.interval is not None and figure.interval.lower is not None:
            gates.append(
                Gate(metric=metric, bound=figure.interval.lower, basis="lower_bound")
            )
        elif undefined_gate == "point_estimate" and figure.point is not None:
            gates.append(
                Gate(metric=metric, bound=figure.point, basis="point_estimate")
            )
        else:
            reason = "undefined_point" if figure.point is None else "undefined_interval"
            ungated.append(Ungated(metric=metric, reason=reason))
    return sealed(
        Gates(
            gates_version=version,
            preregistration_hash=preregistration_hash,
            report_hash=report.content_hash,
            judge_floor=judge_floor,
            gates=tuple(gates),
            ungated=tuple(ungated),
            content_hash="0" * 64,
        )
    )


def evaluate_gates(gates: Gates, report: PartitionReport) -> GateVerdict:
    """Whether a configuration's dev figures pass every gate (FP15, R12.8)."""
    if report.partition is not Partition.DEV:
        raise EvaluationError(EvaluationProblem.WRONG_PARTITION, report.partition.value)
    results = []
    for gate in gates.gates:
        figure = report.figure(gate.metric)
        value = None if figure is None else figure.point
        if value is None:
            passed, reason = False, "undefined"
        elif value < gate.bound:
            passed, reason = False, "below_bound"
        else:
            passed, reason = True, "met"
        results.append(
            GateResult(
                metric=gate.metric,
                bound=gate.bound,
                value=value,
                passed=passed,
                reason=reason,
            )
        )
    figure = report.figure(Metric.GOLD_EVIDENCE_RECALL)
    value = None if figure is None else figure.point
    if value is None:
        positive, reason = False, "undefined"
    elif value > 0:
        positive, reason = True, "met"
    else:
        positive, reason = False, "zero_gold_evidence_recall"
    results.append(
        GateResult(
            metric=Metric.GOLD_EVIDENCE_RECALL,
            bound=None,
            value=value,
            passed=positive,
            reason=reason,
        )
    )
    return GateVerdict(passed=all(r.passed for r in results), results=tuple(results))


def gates_toml(gates: Gates) -> str:
    """The committed file: metrics, bounds and hashes only (GS3)."""
    return tomlfile.dumps(gates.model_dump(mode="json"), header=HEADER)


def load_gates(path: Path) -> Gates:
    """A gates file, refused unless it hashes to its ``content_hash``."""
    return checked(parse(tomlfile.read(path), Gates, path.name), path.name)
