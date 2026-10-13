"""Local label templates and append-only checked labels, over invented passes."""

import importlib
import subprocess
from datetime import date
from types import SimpleNamespace

import pytest
from earnings_themes.evaluation import load_labels
from earnings_themes.records import RecordError
from earnings_themes.split import Partition

cases = importlib.import_module("apps.earnings-pipeline.tests.test_pilot_workflow")
prereg_cases = importlib.import_module(
    "packages.earnings-themes.tests.evaluation.test_preregistration"
)


def git(repo, *args):
    result = subprocess.run(
        [
            "git",
            "-c",
            "user.name=Invented",
            "-c",
            "user.email=invented@example.invalid",
            *args,
        ],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    return result.stdout


def make_case(tmp_path):
    from earnings_pipeline.pilot_workflow import load_pass, make_pass

    config, _ = cases.seed_case(tmp_path, seed=False, review=True)
    git(tmp_path, "init", "--quiet")
    git(tmp_path, "commit", "--allow-empty", "--quiet", "-m", "invented initial")
    rt = cases.runtime(config, [])
    record = make_pass(
        config,
        rt,
        rt.scorer,
        partition=Partition.TRAIN,
        directory=tmp_path / "data/runs/pilot/train/pass",
        fresh=None,
        support_ready=lambda: None,
        now=lambda: cases.cases.NOW,
    )
    loaded = load_pass(config, record)
    prereg = prereg_cases.freeze_preregistration(prereg_cases.fields())
    intake = SimpleNamespace(
        config=config,
        settings=SimpleNamespace(
            alternative_scorer=loaded.alternative.record.scorer_identity
        ),
        partition=Partition.TRAIN,
        preregistration=prereg,
        local=tmp_path / "data/runs/pilot",
        pinned=SimpleNamespace(evaluation=tmp_path / "evaluation"),
        layout=SimpleNamespace(shown=lambda path: path.name),
    )
    return intake, loaded


def test_view_writes_local_template_with_unsure_defaults_and_never_prints(
    tmp_path, capsys
):
    from earnings_pipeline.pilot_labels import sample, write_view

    intake, loaded = make_case(tmp_path)
    drawn = sample(intake, loaded, 0)
    view, working = write_view(intake, loaded, 0, date(2026, 10, 13))
    assert drawn
    assert view.is_relative_to(intake.local / "labels/views")
    assert "Invented expansion." in view.read_text()
    assert "score" not in view.read_text().lower()
    labels = load_labels(working)
    assert {l.claim_support.value for l in labels.labels} == {"unsure"}
    assert {l.theme_fit.value for l in labels.labels} == {"unsure"}
    assert "deliberately confirm labelled_on" in working.read_text()
    assert capsys.readouterr().out == ""


def test_check_never_promotes_a_changed_hash_or_counter_without_growth(
    tmp_path, monkeypatch
):
    import earnings_pipeline.pilot_labels as module
    from earnings_pipeline.pilot_labels import check_working, write_view
    from earnings_themes.evaluation import labels_toml

    monkeypatch.setattr(module, "require_committed", lambda *args: None)
    intake, loaded = make_case(tmp_path)
    _, working = write_view(intake, loaded, 0, date(2026, 10, 13))
    labels = load_labels(working)
    changed = labels.labels[0].model_copy(update={"target_input_hash": "a" * 64})
    working.write_text(labels_toml(labels.model_copy(update={"labels": (changed,)})))
    with pytest.raises(RecordError, match="target_hash_mismatch"):
        check_working(intake, loaded, 0)
    working.write_text(labels_toml(labels))
    target = check_working(intake, loaded, 0)
    before = target.read_bytes()
    working.write_text(labels_toml(labels.model_copy(update={"train_extensions": 1})))
    with pytest.raises(RecordError, match="labels_changed"):
        check_working(intake, loaded, 1)
    assert target.read_bytes() == before


def test_labels_reject_wrong_alternative_and_confine_working_symlinks(tmp_path):
    from dataclasses import replace

    from earnings_pipeline.pilot_labels import write_view
    from earnings_pipeline.theme_config import WorkflowError

    intake, loaded = make_case(tmp_path)
    intake.settings.alternative_scorer = (
        loaded.alternative.record.scorer_identity.model_copy(
            update={"input_limit": 999}
        )
    )
    with pytest.raises(WorkflowError, match="input_changed"):
        write_view(intake, loaded, 0, date(2026, 10, 13))
    intake.settings.alternative_scorer = loaded.alternative.record.scorer_identity
    (intake.local / "labels").mkdir(parents=True)
    outside = tmp_path / "outside.toml"
    outside.write_text("INVENTED_PRIVATE_SENTINEL")
    (intake.local / "labels/train-working.toml").symlink_to(outside)
    with pytest.raises(WorkflowError, match="malformed_record"):
        write_view(intake, replace(loaded), 0, date(2026, 10, 13))
    assert outside.read_text() == "INVENTED_PRIVATE_SENTINEL"


def test_existing_label_base_requires_head_and_unknown_target_is_redacted(
    tmp_path, monkeypatch
):
    import earnings_pipeline.pilot_labels as module
    from earnings_themes.evaluation import labels_toml

    intake, loaded = make_case(tmp_path)
    _, working = module.write_view(intake, loaded, 0, date(2026, 10, 13))
    labels = load_labels(working)
    changed = labels.labels[0].model_copy(
        update={"target_id": "INVENTED SOURCE SENTINEL sentence"}
    )
    working.write_text(labels_toml(labels.model_copy(update={"labels": (changed,)})))
    with pytest.raises(RecordError) as found:
        module.check_working(intake, loaded, 0)
    assert "INVENTED SOURCE" not in str(found.value)
    working.write_text(labels_toml(labels))
    target = module.check_working(intake, loaded, 0)
    target.write_text("INVENTED SOURCE SENTINEL sentence")

    def refuse(*args):
        raise RecordError("labels", ("not_committed",))

    monkeypatch.setattr(module, "require_committed", refuse)
    with pytest.raises(RecordError, match="not_committed"):
        module.check_working(intake, loaded, 0)


def test_support_reverification_precedes_pool_and_view(tmp_path, monkeypatch):
    import earnings_pipeline.pilot_labels as module

    intake, loaded = make_case(tmp_path)
    calls = []
    original_reverify = module.reverify_support_run
    original_pool = module.label_pool
    original_view = module.label_views

    def reverify(*args):
        calls.append("reverify")
        return original_reverify(*args)

    def pool(*args):
        assert calls == ["reverify"]
        calls.append("pool")
        return original_pool(*args)

    def view(*args):
        assert calls == ["reverify", "pool"]
        calls.append("view")
        return original_view(*args)

    monkeypatch.setattr(module, "reverify_support_run", reverify)
    monkeypatch.setattr(module, "label_pool", pool)
    monkeypatch.setattr(module, "label_views", view)
    module.write_view(intake, loaded, 0, date(2026, 10, 13))
    assert calls == ["reverify", "pool", "view"]


def test_check_preserves_other_partition_and_checks_before_merge(tmp_path, monkeypatch):
    import earnings_pipeline.pilot_labels as module
    from earnings_themes.evaluation import labels_toml

    monkeypatch.setattr(module, "require_committed", lambda *args: None)
    intake, loaded = make_case(tmp_path)
    _, working = module.write_view(intake, loaded, 0, date(2026, 10, 13))
    target = module.check_working(intake, loaded, 0)
    committed = load_labels(target)
    dev = committed.labels[0].model_copy(
        update={"target_id": "invented-dev", "partition": Partition.DEV}
    )
    target.write_text(
        labels_toml(committed.model_copy(update={"labels": (*committed.labels, dev)}))
    )
    calls = []
    original_check = module.check_labels
    original_merge = module.merge_labels

    def check(*args, **kwargs):
        calls.append("check")
        return original_check(*args, **kwargs)

    def merge(*args):
        assert calls == ["check"]
        calls.append("merge")
        return original_merge(*args)

    monkeypatch.setattr(module, "check_labels", check)
    monkeypatch.setattr(module, "merge_labels", merge)
    module.check_working(intake, loaded, 0)
    after = load_labels(target)
    assert after.of(Partition.DEV) == (dev,)
    assert after.of(Partition.TRAIN) == load_labels(working).labels
    assert after.train_extensions == committed.train_extensions
    assert calls == ["check", "merge"]


def test_failed_atomic_promotion_preserves_previous_bytes(tmp_path, monkeypatch):
    import earnings_pipeline.pilot_labels as module

    monkeypatch.setattr(module, "require_committed", lambda *args: None)
    intake, loaded = make_case(tmp_path)
    module.write_view(intake, loaded, 0, date(2026, 10, 13))
    target = module.check_working(intake, loaded, 0)
    before = target.read_bytes()
    path_type = type(target)

    def fail_replace(self, destination):
        raise OSError("invented_write_failed")

    monkeypatch.setattr(path_type, "replace", fail_replace)
    with pytest.raises(OSError, match="invented_write_failed"):
        module.check_working(intake, loaded, 0)
    assert target.read_bytes() == before


def test_missing_committed_train_dev_base_refuses_without_recreation(tmp_path):
    import earnings_pipeline.pilot_labels as module
    from earnings_themes.evaluation import labels_toml

    intake, loaded = make_case(tmp_path)
    _, working = module.write_view(intake, loaded, 0, date(2026, 10, 13))
    target = module.check_working(intake, loaded, 0)
    labels = load_labels(target)
    dev = labels.labels[0].model_copy(
        update={"target_id": "invented-dev", "partition": Partition.DEV}
    )
    target.write_text(
        labels_toml(
            labels.model_copy(
                update={"labels": (*labels.labels, dev), "train_extensions": 1}
            )
        )
    )
    relative = target.relative_to(tmp_path).as_posix()
    git(tmp_path, "add", "--", relative)
    git(tmp_path, "commit", "--quiet", "-m", "invented labels")
    committed_bytes = git(tmp_path, "show", "HEAD:" + relative)
    working_before = working.read_bytes()
    target.unlink()
    with pytest.raises(RecordError, match="not_committed"):
        module.check_working(intake, loaded, 0)
    assert not target.exists()
    assert working.read_bytes() == working_before
    assert git(tmp_path, "show", "HEAD:" + relative) == committed_bytes


def test_absent_label_base_refuses_git_failure_without_publication(tmp_path):
    import shutil

    import earnings_pipeline.pilot_labels as module

    intake, loaded = make_case(tmp_path)
    _, working = module.write_view(intake, loaded, 0, date(2026, 10, 13))
    shutil.rmtree(tmp_path / ".git")
    before = working.read_bytes()
    with pytest.raises(RecordError, match="not_committed"):
        module.check_working(intake, loaded, 0)
    assert working.read_bytes() == before
    assert not (intake.pinned.evaluation / "labels/support-labels-v1.toml").exists()
