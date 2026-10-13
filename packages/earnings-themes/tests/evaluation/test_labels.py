"""Support labels: derived labels, the committed file, and ``labels check``'s
refusals (the Stage 11 spec, A4 and §Labels; FP17, FP21)."""

from datetime import date

import pytest
from earnings_themes.evaluation.labels import (
    ClaimAnswer,
    FitAnswer,
    SupportLabel,
    SupportLabelSet,
    check_labels,
    claim_label,
    human_labels,
    joint_label,
    labels_toml,
    load_labels,
    merge_labels,
    usable,
)
from earnings_themes.evaluation.problems import EvaluationError
from earnings_themes.problems import Refusal
from earnings_themes.records import RecordError
from earnings_themes.split import Partition

PREREG = "a" * 64
INPUT = "b" * 64


def label(
    target_id: str, claim: str, fit: str, partition: str = "train"
) -> SupportLabel:
    return SupportLabel(
        target_id=target_id,
        target_input_hash=INPUT,
        partition=Partition(partition),
        claim_support=ClaimAnswer(claim),
        theme_fit=FitAnswer(fit),
        labelled_on=date(2026, 10, 20),
    )


@pytest.mark.parametrize(
    ("claim", "fit", "claim_value", "joint_value"),
    [
        ("supported", "fits", 1, 1),
        ("supported", "does_not_fit", 1, 0),
        ("supported", "unsure", 1, None),
        ("unsupported", "fits", 0, 0),
        ("unsupported", "unsure", 0, 0),
        ("unsure", "fits", None, None),
        ("unsure", "does_not_fit", None, 0),
        ("unsure", "unsure", None, None),
    ],
)
def test_claim_and_joint_labels(claim, fit, claim_value, joint_value) -> None:
    one = label("t1", claim, fit)
    assert claim_label(one) == claim_value
    assert joint_label(one) == joint_value


def test_human_labels_leave_unsure_out() -> None:
    labels = (label("t1", "supported", "fits"), label("t2", "unsure", "fits"))
    joint = human_labels(labels, "joint_support")
    assert [(h.target_id, h.supported) for h in joint] == [("t1", 1)]
    assert len(human_labels(labels, "claim_support")) == 1
    assert usable(labels) == 1


def test_a_label_holds_no_text_and_only_train_or_dev() -> None:
    assert set(SupportLabel.model_fields) == {
        "target_id",
        "target_input_hash",
        "partition",
        "claim_support",
        "theme_fit",
        "labelled_on",
    }
    with pytest.raises(ValueError, match="only train and dev"):
        label("t1", "supported", "fits", "test")
    with pytest.raises(ValueError, match="one label per target"):
        SupportLabelSet(
            preregistration_hash=PREREG,
            labels=(label("t1", "supported", "fits"), label("t1", "unsure", "fits")),
        )


def test_the_file_round_trips_train_then_dev(tmp_path) -> None:
    labels = SupportLabelSet(
        preregistration_hash=PREREG,
        labels=(
            label("t3", "unsure", "fits", "dev"),
            label("t2", "supported", "fits"),
            label("t1", "unsupported", "does_not_fit"),
        ),
    )
    path = tmp_path / "support-labels-v1.toml"
    path.write_text(labels_toml(labels), encoding="utf-8")
    loaded = load_labels(path)
    assert [x.target_id for x in loaded.labels] == ["t1", "t2", "t3"]
    assert set(loaded.labels) == set(labels.labels)
    path.write_text("labels = 3\n", encoding="utf-8")
    with pytest.raises(RecordError):
        load_labels(path)


def test_check_refuses_by_target_and_reason() -> None:
    working = SupportLabelSet(
        preregistration_hash=PREREG,
        labels=(
            label("t1", "supported", "fits"),
            label("t2", "supported", "fits", "dev"),
            label("t3", "supported", "fits"),
            label("t4", "supported", "fits"),
            label("t9", "supported", "fits"),
        ),
    )
    refusals = check_labels(
        working,
        partition=Partition.TRAIN,
        sample=("t1", "t3", "t4", "t5", "t2"),
        input_hashes={"t1": INPUT, "t2": INPUT, "t3": "c" * 64},
        preregistration_hash="d" * 64,
    )
    assert refusals == sorted(
        [
            Refusal("labels", "preregistration_mismatch"),
            Refusal("t2", "wrong_partition"),
            Refusal("t3", "target_hash_mismatch"),
            Refusal("t4", "unknown_target"),
            Refusal("t9", "not_sampled"),
            Refusal("t5", "not_labelled"),
        ]
    )


def test_a_matching_working_file_has_nothing_to_refuse() -> None:
    working = SupportLabelSet(
        preregistration_hash=PREREG, labels=(label("t1", "unsure", "unsure"),)
    )
    assert (
        check_labels(
            working,
            partition=Partition.TRAIN,
            sample=("t1",),
            input_hashes={"t1": INPUT},
            preregistration_hash=PREREG,
        )
        == []
    )


def test_merging_adds_dev_and_extends_train_but_never_changes_labels() -> None:
    train = SupportLabelSet(
        preregistration_hash=PREREG, labels=(label("t1", "supported", "fits"),)
    )
    committed = merge_labels(None, train, Partition.TRAIN)
    dev = SupportLabelSet(
        preregistration_hash=PREREG, labels=(label("d1", "unsure", "fits", "dev"),)
    )
    both = merge_labels(committed, dev, Partition.DEV)
    assert {x.target_id for x in both.labels} == {"t1", "d1"}
    assert merge_labels(both, dev, Partition.DEV) == both
    extended = SupportLabelSet(
        preregistration_hash=PREREG,
        train_extensions=1,
        labels=(label("t1", "supported", "fits"), label("t2", "unsure", "fits")),
    )
    grown = merge_labels(both, extended, Partition.TRAIN)
    assert grown.train_extensions == 1
    assert {x.target_id for x in grown.of(Partition.TRAIN)} == {"t1", "t2"}
    changed = SupportLabelSet(
        preregistration_hash=PREREG, labels=(label("t1", "unsupported", "fits"),)
    )
    with pytest.raises(EvaluationError, match="labels_changed"):
        merge_labels(both, changed, Partition.TRAIN)
    other = SupportLabelSet(preregistration_hash="e" * 64, labels=())
    with pytest.raises(EvaluationError, match="preregistration_mismatch"):
        merge_labels(both, other, Partition.DEV)
