"""Approved boundary tidies exercised with invented records only."""

from datetime import date

import pytest
from earnings_themes.evaluation.gates import derive_gates, evaluate_gates
from earnings_themes.evaluation.labels import (
    ClaimAnswer,
    FitAnswer,
    SupportLabel,
    SupportLabelSet,
    merge_labels,
)
from earnings_themes.evaluation.preregistration import (
    REQUIRED_GATES,
    Candidate,
    GateRule,
)
from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
from earnings_themes.evaluation.records import PartitionReport, PilotReport
from earnings_themes.evaluation.sampling import sample_targets
from earnings_themes.records import RecordError
from earnings_themes.split import Partition
from pydantic import ValidationError

HASH = "1" * 64


def partition(kind):
    return PartitionReport(
        partition=kind, in_sample=kind is Partition.TRAIN, events=(), figures=()
    )


def report(*parts):
    return PilotReport(
        report_version=1,
        preregistration_hash=HASH,
        calibration_hash=HASH,
        partitions=parts,
        content_hash=HASH,
    )


@pytest.mark.parametrize(
    "parts",
    [(), (Partition.TRAIN,), (Partition.DEV,), (Partition.TRAIN, Partition.TRAIN)],
)
def test_report_requires_exactly_one_train_and_dev(parts):
    with pytest.raises(ValidationError, match="one train and one dev"):
        report(*(partition(kind) for kind in parts))


def test_report_accepts_both_partition_orders():
    for kinds in ((Partition.TRAIN, Partition.DEV), (Partition.DEV, Partition.TRAIN)):
        assert len(report(*(partition(kind) for kind in kinds)).partitions) == 2


def test_every_candidate_uses_one_signal():
    with pytest.raises(ValidationError):
        Candidate(
            candidate_id="c1",
            rule="scorer_cutoff",
            signal="minicheck_joint",
            signals=2,
            grid=(0.5,),
        )


def test_derive_gates_takes_and_rechecks_the_preregistered_rule():
    base = report(partition(Partition.TRAIN), partition(Partition.DEV))
    rule = GateRule(
        rule="dev-lower-bound/1",
        gated=tuple(sorted(REQUIRED_GATES)),
        undefined_gate="not_gated",
    )
    result = derive_gates(base, rule=rule, judge_floor=0.4, preregistration_hash=HASH)
    assert {r.metric for r in result.ungated} == REQUIRED_GATES
    with pytest.raises(EvaluationError) as refused:
        derive_gates(
            base,
            rule=rule.model_copy(update={"undefined_gate": "typo"}),
            judge_floor=0.4,
            preregistration_hash=HASH,
        )
    assert (refused.value.problem, refused.value.subject) == (
        EvaluationProblem.MALFORMED_RECORD,
        "rule",
    )


@pytest.mark.parametrize(("size", "cap", "subject"), [(-1, 1, "size"), (1, 0, "cap")])
def test_sampling_refuses_invalid_bounds(size, cap, subject):
    with pytest.raises(EvaluationError) as refused:
        sample_targets((), seed=1, size=size, cap=cap)
    assert (refused.value.problem, refused.value.subject) == (
        EvaluationProblem.MALFORMED_RECORD,
        subject,
    )


def test_merged_labels_revalidate_cross_partition_target_ids():
    def label(kind):
        return SupportLabel(
            target_id="same-target",
            target_input_hash=HASH,
            partition=kind,
            claim_support=ClaimAnswer.SUPPORTED,
            theme_fit=FitAnswer.FITS,
            labelled_on=date(2026, 10, 1),
        )

    train = SupportLabelSet(preregistration_hash=HASH, labels=(label(Partition.TRAIN),))
    dev = SupportLabelSet(preregistration_hash=HASH, labels=(label(Partition.DEV),))
    with pytest.raises(RecordError, match="one label per target"):
        merge_labels(train, dev, Partition.DEV)


def test_wrong_partition_refusals_use_the_same_field_path():
    base = report(partition(Partition.TRAIN), partition(Partition.DEV))
    rule = GateRule(
        rule="dev-lower-bound/1",
        gated=tuple(sorted(REQUIRED_GATES)),
        undefined_gate="not_gated",
    )
    gates = derive_gates(base, rule=rule, judge_floor=0.4, preregistration_hash=HASH)
    missing = base.model_copy(update={"partitions": (partition(Partition.TRAIN),)})
    for call in (
        lambda: derive_gates(
            missing, rule=rule, judge_floor=0.4, preregistration_hash=HASH
        ),
        lambda: evaluate_gates(gates, partition(Partition.TRAIN)),
    ):
        with pytest.raises(EvaluationError) as refused:
            call()
        assert (refused.value.problem, refused.value.subject) == (
            EvaluationProblem.WRONG_PARTITION,
            "partition",
        )


def test_hash_helpers_have_a_hashed_record_contract_and_shared_check():
    from earnings_themes import records

    assert hasattr(records, "HashedRecord")
    base = report(partition(Partition.TRAIN), partition(Partition.DEV))
    sealed = records.sealed(base)
    assert records.hash_matches(sealed)
    assert not records.hash_matches(sealed.model_copy(update={"report_version": 2}))
    assert records.checked.__type_params__[0].__bound__ is records.HashedRecord
