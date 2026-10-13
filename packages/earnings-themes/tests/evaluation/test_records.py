"""The report and gate records: what they refuse, and their content hashes (the
Stage 11 spec, §Artifacts; FP4, FP15; R12.2)."""

import pytest
from earnings_themes.evaluation.bootstrap import Interval
from earnings_themes.evaluation.records import (
    Figure,
    Metric,
    PartitionReport,
    PilotReport,
    checked,
    content_hash,
    sealed,
)
from earnings_themes.records import RecordError
from earnings_themes.split import Partition
from pydantic import ValidationError

INTERVAL = Interval(lower=0.1, upper=0.9, level=0.9, resamples=10, undefined=0)


def figure(**changes) -> Figure:
    data = {"metric": Metric.THEME_F1_MICRO, "point": 0.5, "interval": INTERVAL}
    return Figure(**{**data, **changes})


def test_a_figure_has_an_interval_or_a_reason() -> None:
    assert figure().reason is None
    absent = figure(point=None, interval=None, reason="not estimated")
    assert absent.interval is None
    with pytest.raises(ValidationError, match="never both"):
        figure(reason="not estimated")
    with pytest.raises(ValidationError, match="never both"):
        figure(interval=None)


def test_counts_are_sorted_and_points_are_finite() -> None:
    assert figure(counts=(("fn", 1), ("tp", 2))).counts == (("fn", 1), ("tp", 2))
    with pytest.raises(ValidationError, match="sorted and unique"):
        figure(counts=(("tp", 2), ("fn", 1)))
    with pytest.raises(ValidationError):
        figure(point=float("nan"))
    assert figure(point=-0.25).point == -0.25


def test_only_train_and_dev_are_reported_and_train_is_in_sample() -> None:
    def report(partition, in_sample):
        return PartitionReport(
            partition=partition, in_sample=in_sample, events=("e1",), figures=()
        )

    assert report(Partition.TRAIN, True).in_sample
    assert not report(Partition.DEV, False).in_sample
    with pytest.raises(ValidationError, match="in-sample"):
        report(Partition.DEV, True)
    with pytest.raises(ValidationError, match="only train and dev"):
        report(Partition.TEST, False)


def test_one_figure_per_metric_and_qualifier() -> None:
    twice = (figure(), figure())
    with pytest.raises(ValidationError, match="one figure per"):
        PartitionReport(
            partition=Partition.DEV, in_sample=False, events=(), figures=twice
        )
    qualified = (figure(qualifier="f0"), figure(qualifier="f1"), figure())
    report = PartitionReport(
        partition=Partition.DEV, in_sample=False, events=(), figures=qualified
    )
    assert report.figure(Metric.THEME_F1_MICRO, "f1") == qualified[1]
    assert report.figure(Metric.THEME_F1_MICRO) == qualified[2]
    assert report.figure(Metric.SPAN_UNIT_F1) is None


def test_a_sealed_record_is_checked_by_its_content_hash() -> None:
    record = sealed(
        PilotReport(
            report_version=1,
            preregistration_hash="1" * 64,
            calibration_hash="2" * 64,
            partitions=(),
            content_hash="0" * 64,
        )
    )
    assert record.content_hash == content_hash(record) != "0" * 64
    assert record.label == "feasibility-only"
    assert checked(record, "report-v1.json") is record
    with pytest.raises(RecordError, match="content_hash"):
        checked(record.model_copy(update={"report_version": 2}), "report-v1.json")
