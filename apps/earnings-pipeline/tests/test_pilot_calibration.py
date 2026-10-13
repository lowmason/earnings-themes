"""Calibration intake binds exactly parsed bytes and Stage 9's proposal/source gate."""

import importlib

import pytest
from earnings_core import sha256_hex
from earnings_themes.evaluation import EvaluationError

cases = importlib.import_module("apps.earnings-pipeline.tests.test_pilot_labels")


def test_calibration_hashes_exact_label_bytes_and_checks_sample(tmp_path, monkeypatch):
    from datetime import date

    import earnings_pipeline.pilot_calibration as module
    from earnings_pipeline.pilot_labels import check_working, write_view

    monkeypatch.setattr(module, "require_committed", lambda *args: None)
    intake, loaded = cases.make_case(tmp_path)
    _, working = write_view(intake, loaded, 0, date(2026, 10, 13))
    target = check_working(intake, loaded, 0)
    target.write_bytes(b"# invented intentional comment\n" + target.read_bytes())
    before = target.read_bytes()
    seen = {}

    def capture(preregistration, labels, **kwargs):
        seen.update(kwargs)
        return cases.cases.bound_artifact(intake.config, loaded)

    monkeypatch.setattr(module, "calibrate", capture)
    artifact = module.calibrate_pilot(intake, loaded)
    assert seen["labels_hash"] == sha256_hex(before)
    assert artifact.is_file()
    assert target.read_bytes() == before
    assert working.is_file()


def test_too_few_labels_refuses_without_artifact(tmp_path, monkeypatch):
    from datetime import date

    import earnings_pipeline.pilot_calibration as module
    from earnings_pipeline.pilot_labels import check_working, write_view

    monkeypatch.setattr(module, "require_committed", lambda *args: None)
    intake, loaded = cases.make_case(tmp_path)
    write_view(intake, loaded, 0, date(2026, 10, 13))
    check_working(intake, loaded, 0)
    with pytest.raises(EvaluationError, match="too_few_labels"):
        module.calibrate_pilot(intake, loaded)
    assert not (intake.pinned.evaluation / "calibration-v1.json").exists()


def test_calibration_requires_head_labels_before_any_label_read(tmp_path, monkeypatch):
    import earnings_pipeline.pilot_calibration as module
    from earnings_themes.records import RecordError

    intake, loaded = cases.make_case(tmp_path)

    def refuse(*args):
        raise RecordError("labels", ("not_committed",))

    monkeypatch.setattr(module, "require_committed", refuse)
    monkeypatch.setattr(
        module,
        "read_label_bytes",
        lambda *args: pytest.fail("label read preceded HEAD gate"),
    )
    with pytest.raises(RecordError, match="not_committed"):
        module.calibrate_pilot(intake, loaded)


@pytest.mark.parametrize(
    "changed,missing", [(False, False), (True, False), (False, True)]
)
def test_original_label_history_allows_dev_append_but_refuses_train_edits_or_missing_hash(
    tmp_path, monkeypatch, changed, missing
):
    from datetime import date
    from types import SimpleNamespace

    import earnings_pipeline.pilot_calibration as module
    from earnings_pipeline.pilot_labels import write_view
    from earnings_themes.evaluation import labels_toml, load_labels
    from earnings_themes.records import RecordError
    from earnings_themes.split import Partition

    intake, loaded = cases.make_case(tmp_path)
    _, working = write_view(intake, loaded, 0, date(2026, 10, 13))
    labels = load_labels(working)
    original = labels_toml(labels).encode()
    current = labels.model_copy(
        update={
            "labels": (
                *labels.labels,
                labels.labels[0].model_copy(
                    update={"partition": Partition.DEV, "target_id": "dev-target"}
                ),
            )
        }
    )
    if changed:
        train = current.labels[0].model_copy(update={"labelled_on": date(2026, 10, 14)})
        current = current.model_copy(update={"labels": (train, *current.labels[1:])})
    path = intake.pinned.evaluation / "labels/support-labels-v1.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(labels_toml(current))
    artifact = cases.cases.bound_artifact(intake.config, loaded).model_copy(
        update={
            "preregistration_hash": labels.preregistration_hash,
            "labels_hash": sha256_hex(original),
        }
    )
    monkeypatch.setattr(module, "require_committed", lambda *args: None)

    def git(args, **kwargs):
        assert kwargs["capture_output"] and not kwargs["check"]
        assert args[:2] in (["git", "rev-list"], ["git", "show"])
        data = (
            (b"a" * 40 + b"\n")
            if args[1] == "rev-list"
            else (b"missing" if missing else original)
        )
        return SimpleNamespace(returncode=0, stdout=data)

    monkeypatch.setattr(module.subprocess, "run", git)
    if changed or missing:
        with pytest.raises(RecordError, match="labels_changed"):
            module.validate_calibration_labels(intake, artifact)
    else:
        module.validate_calibration_labels(intake, artifact)


@pytest.mark.parametrize("failed_command", ["rev-list", "show"])
def test_label_history_launch_failure_is_closed_and_unchained(
    tmp_path, monkeypatch, failed_command
):
    from datetime import date
    from types import SimpleNamespace

    import earnings_pipeline.pilot_calibration as module
    from earnings_pipeline.pilot_labels import write_view
    from earnings_themes.evaluation import labels_toml, load_labels
    from earnings_themes.records import RecordError

    intake, loaded = cases.make_case(tmp_path)
    _, working = write_view(intake, loaded, 0, date(2026, 10, 13))
    labels = load_labels(working)
    original = labels_toml(labels).encode()
    path = intake.pinned.evaluation / "labels/support-labels-v1.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"# invented current comment\n" + original)
    artifact = cases.cases.bound_artifact(intake.config, loaded).model_copy(
        update={
            "preregistration_hash": labels.preregistration_hash,
            "labels_hash": sha256_hex(original),
        }
    )
    monkeypatch.setattr(module, "require_committed", lambda *args: None)

    def git(args, **kwargs):
        if args[1] == failed_command:
            raise OSError("INVENTED_PRIVATE_SENTINEL")
        return SimpleNamespace(returncode=0, stdout=b"a" * 40 + b"\n")

    monkeypatch.setattr(module.subprocess, "run", git)
    with pytest.raises(RecordError, match="labels_changed") as found:
        module.validate_calibration_labels(intake, artifact)
    assert "INVENTED_PRIVATE_SENTINEL" not in str(found.value)
    assert found.value.__cause__ is None
    assert found.value.__suppress_context__
