"""The preregistration: its schema, its self-hash, and the gate list it must hold
(the Stage 11 spec, A5 and §Preregistration; FP9)."""

import pytest
from earnings_themes.evaluation.preregistration import (
    REQUIRED_GATES,
    freeze_preregistration,
    load_preregistration,
    preregistration_toml,
)
from earnings_themes.evaluation.records import Metric
from earnings_themes.records import RecordError
from earnings_themes.synthetic import PIN

HASH = "0" * 64


def fields(**changes) -> dict:
    """An invented preregistration's fields; the user picks the real numbers (B2)."""
    data = {
        "preregistration_version": 1,
        "pin": PIN.model_dump(mode="json"),
        "split_hash": HASH,
        "codebook": {
            "codebook_id": "invented",
            "codebook_version": 0,
            "content_hash": HASH,
        },
        "floor": {
            "statistic": "cohen_kappa",
            "reported": "gwet_ac1",
            "population": "family_verdict_vs_joint_label",
            "bound": "event_bootstrap_lower",
            "floor": 0.4,
            "consequence": "reported_only",
        },
        "menu": [
            {
                "candidate_id": "scorer-only",
                "rule": "scorer_cutoff",
                "signal": "minicheck_joint",
                "signals": 1,
                "grid": [0.0, 0.5, 0.9],
            }
        ],
        "selection": {
            "recall_floor": 0.5,
            "objective": "max_train_precision",
            "tie_break": "fewer_signals_then_lower_cutoff",
        },
        "sampling": {
            "seed": 19,
            "pool": "assessed_and_flagged",
            "train_size": 70,
            "train_cap": 5,
            "dev_size": 24,
            "dev_cap": 3,
            "minimum_usable": 50,
            "extension_step": 10,
        },
        "bootstrap": {
            "seed": 23,
            "resamples": 200,
            "level": 0.9,
            "max_undefined_share": 0.05,
        },
        "gates": {
            "rule": "dev-lower-bound/1",
            "gated": sorted(m.value for m in REQUIRED_GATES),
            "undefined_gate": "not_gated",
        },
    }
    return {**data, **changes}


def test_it_round_trips_and_hashes_itself(tmp_path) -> None:
    record = freeze_preregistration(fields())
    path = tmp_path / "preregistration-v1.toml"
    path.write_text(preregistration_toml(record), encoding="utf-8")
    assert load_preregistration(path) == record
    edited = path.read_text(encoding="utf-8").replace("floor = 0.4", "floor = 0.5")
    path.write_text(edited, encoding="utf-8")
    with pytest.raises(RecordError, match="content_hash"):
        load_preregistration(path)


@pytest.mark.parametrize(
    "gated",
    [
        sorted(m.value for m in REQUIRED_GATES - {Metric.SPAN_UNIT_F1}),
        sorted({*(m.value for m in REQUIRED_GATES), "rare_theme_recall"}),
    ],
)
def test_the_gates_must_be_the_specs(gated) -> None:
    gates = {"rule": "dev-lower-bound/1", "gated": gated, "undefined_gate": "not_gated"}
    with pytest.raises(RecordError, match="gated metrics"):
        freeze_preregistration(fields(gates=gates))


@pytest.mark.parametrize(
    ("section", "change"),
    [
        ("floor", {"floor": 0.7}),
        ("sampling", {"minimum_usable": 49}),
        ("selection", {"recall_floor": 0.0}),
    ],
)
def test_out_of_range_numbers_are_refused(section, change) -> None:
    data = fields()
    with pytest.raises(RecordError):
        freeze_preregistration({**data, section: {**data[section], **change}})


def test_the_bootstrap_level_is_the_specs_ninety_percent() -> None:
    """The spec reports the 90% percentile interval throughout, and V6's gates file
    says so, so a preregistration at another level is refused, naming the field and
    the value."""
    data = fields()
    with pytest.raises(RecordError, match=r"bootstrap\.level must be 0\.9.*0\.95"):
        freeze_preregistration(
            {**data, "bootstrap": {**data["bootstrap"], "level": 0.95}}
        )
    assert freeze_preregistration(data).bootstrap.level == 0.9


def test_an_unsorted_grid_is_refused() -> None:
    menu = [{**fields()["menu"][0], "grid": [0.5, 0.0]}]
    with pytest.raises(RecordError, match="sorted and unique"):
        freeze_preregistration(fields(menu=menu))


def gate_rule(gated, undefined_gate="not_gated") -> dict:
    """A gate rule with ``gated`` as given."""
    return {
        "rule": "dev-lower-bound/1",
        "gated": gated,
        "undefined_gate": undefined_gate,
    }


def test_an_unsorted_grid_names_its_candidate() -> None:
    menu = [{**fields()["menu"][0], "grid": [0.5, 0.0]}]
    with pytest.raises(RecordError, match="scorer-only.*sorted and unique"):
        freeze_preregistration(fields(menu=menu))


@pytest.mark.parametrize(
    "extra",
    [
        "hard_negative_false_acceptance",
        "gs5_edited_share",
        "gs5_rejected_share",
        "gs5_added_share",
        "judge_ac1",
        "scorer_auc",
    ],
)
def test_a_reported_metric_cannot_be_gated(extra) -> None:
    gated = sorted({*(m.value for m in REQUIRED_GATES), extra})
    with pytest.raises(RecordError, match=f"gated metrics.*{extra}"):
        freeze_preregistration(fields(gates=gate_rule(gated)))


@pytest.mark.parametrize("missing", sorted(m.value for m in REQUIRED_GATES))
def test_a_required_gate_cannot_be_dropped(missing) -> None:
    gated = sorted(m.value for m in REQUIRED_GATES if m.value != missing)
    with pytest.raises(RecordError, match=f"gated metrics.*{missing}"):
        freeze_preregistration(fields(gates=gate_rule(gated)))


def test_a_metric_is_gated_once() -> None:
    gated = [*sorted(m.value for m in REQUIRED_GATES), "release_precision"]
    with pytest.raises(RecordError, match="gated once.*release_precision"):
        freeze_preregistration(fields(gates=gate_rule(gated)))


def test_an_unknown_undefined_gate_is_refused() -> None:
    gated = sorted(m.value for m in REQUIRED_GATES)
    with pytest.raises(RecordError, match="gates.undefined_gate"):
        freeze_preregistration(fields(gates=gate_rule(gated, "never")))


def test_point_estimate_round_trips(tmp_path) -> None:
    gated = sorted(m.value for m in REQUIRED_GATES)
    record = freeze_preregistration(fields(gates=gate_rule(gated, "point_estimate")))
    path = tmp_path / "preregistration-v1.toml"
    path.write_text(preregistration_toml(record), encoding="utf-8")
    loaded = load_preregistration(path)
    assert loaded == record
    assert loaded.content_hash == record.content_hash
    assert loaded.gates.undefined_gate == "point_estimate"
    assert record.content_hash != freeze_preregistration(fields()).content_hash


def test_a_duplicate_candidate_is_refused_and_named() -> None:
    first = fields()["menu"][0]
    menu = [first, {**first, "grid": [0.1]}]
    with pytest.raises(RecordError, match="menu: .*unique.*scorer-only"):
        freeze_preregistration(fields(menu=menu))
