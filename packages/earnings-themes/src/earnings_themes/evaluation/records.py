"""Stage 11's committed evaluation records: the pilot report and V6's gates (the
Stage 11 spec, §Metrics and §Artifacts; FP15; R12.2, R12.7).

- **Ids, numbers and hashes only** (GS3). A figure names its metric and, where one
  metric is reported several times, a qualifier: a judge family, a family and
  presentation as ``family:presentation``, a scorer view, or a negative kind.
- **Frozen.** Each top-level record carries ``content_hash``, the digest of every
  other field. ``sealed`` fills it in and ``checked`` rechecks it when the record is
  read; with ``content_hash`` itself they are ``earnings_themes.records``', re-exported
  here.
- **Feasibility only.** Every figure is labelled feasibility-only (R12.2), and train
  is marked in-sample (FP4).
"""

from enum import StrEnum
from typing import Literal, Self

from pydantic import NonNegativeInt, PositiveInt, model_validator

from earnings_themes.evaluation.bootstrap import Interval, Real
from earnings_themes.records import (
    IdPart,
    NonBlank,
    Part,
    Sha256Hex,
    ThemesRecord,
    checked,
    content_hash,
    sealed,
)
from earnings_themes.split import Partition

__all__ = [
    "Figure",
    "Gate",
    "GateResult",
    "GateVerdict",
    "Gates",
    "IndependentFigures",
    "Metric",
    "PartitionReport",
    "PilotReport",
    "ReadingAgreement",
    "Real",
    "Ungated",
    "checked",
    "content_hash",
    "sealed",
]


class Metric(StrEnum):
    """The pilot report's metrics (§Metrics)."""

    RELEASE_PRECISION = "release_precision"
    RELEASE_RECALL = "release_recall"
    THEME_F1_MICRO = "theme_f1_micro"
    THEME_F1_MACRO = "theme_f1_macro"
    THEME_F1_ROLLUP_MICRO = "theme_f1_rollup_micro"
    THEME_F1_ROLLUP_MACRO = "theme_f1_rollup_macro"
    SPAN_UNIT_PRECISION = "span_unit_precision"
    SPAN_UNIT_RECALL = "span_unit_recall"
    SPAN_UNIT_F1 = "span_unit_f1"
    SPAN_CHAR_JACCARD = "span_char_jaccard"
    RETENTION_QUOTES = "retention_quotes"
    RETENTION_TARGETS = "retention_targets"
    GOLD_EVIDENCE_RECALL = "gold_evidence_recall"
    SUPPORT_PRECISION = "support_precision"
    SCORER_AUC = "scorer_auc"
    JUDGE_KAPPA = "judge_kappa"
    JUDGE_AC1 = "judge_ac1"
    HARD_NEGATIVE_FALSE_ACCEPTANCE = "hard_negative_false_acceptance"
    RARE_THEME_RECALL = "rare_theme_recall"
    GS5_EDITED_SHARE = "gs5_edited_share"
    GS5_REJECTED_SHARE = "gs5_rejected_share"
    GS5_ADDED_SHARE = "gs5_added_share"
    NO_THEME_SHARE = "no_theme_share"
    STABILITY_FLEISS_KAPPA = "stability_fleiss_kappa"
    STABILITY_UNIT_JACCARD = "stability_unit_jaccard"
    STABILITY_ASSIGNMENT_JACCARD = "stability_assignment_jaccard"
    SECTOR_PREVALENCE = "sector_prevalence"
    SOURCE_SELECTION_BIAS = "source_selection_bias"


class Figure(Part):
    """One metric's point estimate and interval, with the counts behind it; or,
    for a metric that is not estimated, its reason."""

    metric: Metric
    qualifier: IdPart | None = None
    point: Real | None
    interval: Interval | None
    counts: tuple[tuple[NonBlank, NonNegativeInt], ...] = ()
    reason: NonBlank | None = None

    @model_validator(mode="after")
    def _sorted_counts_and_reason(self) -> Self:
        names = [name for name, _ in self.counts]
        if names != sorted(set(names)):
            raise ValueError("counts must be sorted and unique")
        if (self.interval is None) != (self.reason is not None):
            raise ValueError("a figure has an interval or a reason, never both")
        return self


class PartitionReport(Part):
    """One partition's figures; train is in-sample (FP4)."""

    partition: Partition
    in_sample: bool
    events: tuple[IdPart, ...]
    figures: tuple[Figure, ...]

    @model_validator(mode="after")
    def _train_or_dev(self) -> Self:
        if self.partition not in (Partition.TRAIN, Partition.DEV):
            raise ValueError("only train and dev are reported")
        if self.in_sample != (self.partition is Partition.TRAIN):
            raise ValueError("train, and only train, is in-sample")
        if self.events != tuple(sorted(set(self.events))):
            raise ValueError("events must be sorted and unique")
        keys = [(f.metric.value, f.qualifier or "") for f in self.figures]
        if len(keys) != len(set(keys)):
            raise ValueError("one figure per metric and qualifier")
        return self

    def figure(self, metric: Metric, qualifier: str | None = None) -> Figure | None:
        return next(
            (f for f in self.figures if (f.metric, f.qualifier) == (metric, qualifier)),
            None,
        )


class ReadingAgreement(Part):
    """Two readings of one bundle compared (GS19): release identification, exact
    theme F1, and unit F1, with their dangling references (D19-7)."""

    release_agrees: bool
    theme_f1: Real | None
    unit_f1: Real | None
    dangling: NonNegativeInt


class IndependentFigures(Part):
    """One dev event's independent-pass figures (§Metrics, D1: descriptive)."""

    event_id: IdPart
    record_vs_draft: ReadingAgreement
    signed_vs_record: ReadingAgreement


class PilotReport(ThemesRecord):
    """``report-v<N>.json``: every partition's figures, feasibility-only (R12.2)."""

    report_version: PositiveInt
    label: Literal["feasibility-only"] = "feasibility-only"
    preregistration_hash: Sha256Hex
    calibration_hash: Sha256Hex
    partitions: tuple[PartitionReport, ...]
    independent: tuple[IndependentFigures, ...] = ()
    content_hash: Sha256Hex

    def partition(self, partition: Partition) -> PartitionReport | None:
        return next((p for p in self.partitions if p.partition is partition), None)


class Gate(Part):
    """One gated metric's bound (FP15)."""

    metric: Metric
    bound: Real
    basis: Literal["lower_bound", "point_estimate"]


class Ungated(Part):
    """A preregistered gated metric that the dev baseline cannot gate."""

    metric: Metric
    reason: Literal["undefined_interval", "undefined_point", "not_in_report"]


class Gates(ThemesRecord):
    """``gates-v<N>.toml``: V6's gates from the dev baseline (FP15)."""

    gates_version: PositiveInt
    rule: Literal["dev-lower-bound/1"] = "dev-lower-bound/1"
    preregistration_hash: Sha256Hex
    report_hash: Sha256Hex
    judge_floor: Real
    gates: tuple[Gate, ...]
    ungated: tuple[Ungated, ...] = ()
    content_hash: Sha256Hex


class GateResult(Part):
    """One gate's outcome for a configuration's dev point estimate."""

    metric: Metric
    bound: Real | None
    value: Real | None
    passed: bool
    reason: Literal["met", "below_bound", "undefined", "zero_gold_evidence_recall"]


class GateVerdict(Part):
    """Whether a configuration passes every gate, and each gate's outcome."""

    passed: bool
    results: tuple[GateResult, ...]
