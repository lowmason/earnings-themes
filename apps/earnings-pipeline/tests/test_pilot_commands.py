"""Every A8 command is counts-only and keeps model/runtime dispatch behind intake."""

import importlib

import pytest
from earnings_pipeline.cli import app
from typer.testing import CliRunner

MARKER = "INVENTED_SOURCE_JUDGE_LABEL_EXCEPTION_SENTINEL"


@pytest.mark.parametrize(
    "command",
    [
        "pass",
        "run",
        "calibrate",
        "independent",
        "report",
        "gates",
        "labels sample",
        "labels view",
        "labels check",
    ],
)
def test_each_command_redacts_unexpected_source_judge_label_exception(
    command, tmp_path, monkeypatch
):
    module = importlib.import_module("earnings_pipeline.pilot_commands")

    def refuse(*args, **kwargs):
        raise ValueError(MARKER)

    monkeypatch.setattr(module, "open_pilot", refuse)
    args = [
        "pilot",
        "--repo",
        str(tmp_path),
        *command.split(),
        "--settings",
        "invented.json",
    ]
    if command == "pass":
        args += ["--models-root", str(tmp_path)]
    if command == "labels view":
        args += ["--labelled-on", "2026-10-13"]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 1
    assert MARKER not in result.output
    assert "ValueError" in result.output


@pytest.mark.parametrize(
    "command",
    [
        "pass",
        "run",
        "calibrate",
        "independent",
        "labels sample",
        "labels view",
        "labels check",
    ],
)
@pytest.mark.parametrize("partition", ["test", "excluded"])
def test_forbidden_partition_refuses_before_metadata(
    command, partition, tmp_path, monkeypatch
):
    module = importlib.import_module("earnings_pipeline.pilot_commands")
    monkeypatch.setattr(
        module, "open_pilot", lambda *args: pytest.fail("metadata opened")
    )
    args = [
        "pilot",
        "--repo",
        str(tmp_path),
        *command.split(),
        "--settings",
        "invented.json",
        "--partition",
        partition,
    ]
    if command == "pass":
        args += ["--models-root", str(tmp_path)]
    if command == "labels view":
        args += ["--labelled-on", "2026-10-13"]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 1
    assert "partition" in result.output
    assert "metadata opened" not in result.output


@pytest.mark.parametrize(
    "help_command",
    [
        "",
        "pass",
        "run",
        "calibrate",
        "independent",
        "report",
        "gates",
        "labels",
        "labels sample",
        "labels view",
        "labels check",
    ],
)
def test_negative_support_checkpoint_aborts_and_help_loads_no_runtime(
    tmp_path, monkeypatch, help_command
):
    module = importlib.import_module("earnings_pipeline.pilot_commands")
    from earnings_pipeline.theme_config import WorkflowError

    monkeypatch.setattr(module.typer, "confirm", lambda *args, **kwargs: False)
    with pytest.raises(WorkflowError):
        module.support_checkpoint()
    runtime_module = importlib.import_module("earnings_pipeline.model_runtime")
    attempts = []

    def refuse_runtime(*args, **kwargs):
        attempts.append("runtime")
        pytest.fail("help constructed runtime")

    monkeypatch.setattr(runtime_module, "build_runtime", refuse_runtime)
    result = CliRunner().invoke(app, ["pilot", *help_command.split(), "--help"])
    assert result.exit_code == 0
    assert attempts == []
    if help_command:
        return
    for word in (
        "pass",
        "run",
        "calibrate",
        "independent",
        "report",
        "gates",
        "labels",
    ):
        assert word in result.output


@pytest.mark.parametrize("command", ["split", "recount", "coverage"])
def test_legacy_metadata_value_errors_never_print_source_text(
    command, tmp_path, monkeypatch
):
    import earnings_pipeline.stage6 as module

    def refuse(*args, **kwargs):
        raise ValueError(MARKER)

    monkeypatch.setattr(module, "load_manifest", refuse)
    import earnings_pipeline.pilot_cli as legacy

    monkeypatch.setattr(legacy, "pinned_codebook", lambda *args: object())
    args = ["pilot", "--repo", str(tmp_path), command]
    if command == "coverage":
        args += ["--version", "2"]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 1
    assert MARKER not in result.output
    assert "pinned_metadata" in result.output


def test_baseline_loads_with_exact_intake_configuration(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from earnings_themes.split import Partition

    module = importlib.import_module("earnings_pipeline.pilot_commands")
    config = SimpleNamespace(repo=tmp_path)
    current = SimpleNamespace(
        config=config, local=tmp_path / "data/runs/pilot", partition=Partition.TRAIN
    )
    record = object()
    loaded = object()
    calls = []
    monkeypatch.setattr(module, "read_json", lambda *args: record)

    def load(selected, stored):
        assert selected is config
        assert stored is record
        calls.append("load")
        return loaded

    def check(selected, stored):
        assert selected is current
        assert stored is loaded
        calls.append("check")

    monkeypatch.setattr(module, "load_pass", load)
    monkeypatch.setattr(module, "checked_pass", check)
    assert module.baseline(current) is loaded
    assert calls == ["load", "check"]


@pytest.mark.parametrize("fresh", [False, True])
def test_run_dispatch_binds_before_runtime_and_uses_exact_config(
    tmp_path, monkeypatch, fresh
):
    from types import SimpleNamespace

    from earnings_themes.split import Partition

    module = importlib.import_module("earnings_pipeline.pilot_commands")
    config = object()
    current = SimpleNamespace(
        config=config, local=tmp_path / "data/runs/pilot", partition=Partition.DEV
    )
    baseline = object()
    calibration = object()
    loaded = object()
    record = object()
    runtime = SimpleNamespace(workflow=object(), alternative_scorer=object())
    calls = []
    monkeypatch.setattr(module, "intake", lambda *args: current)
    monkeypatch.setattr(module, "baseline", lambda selected: baseline)
    monkeypatch.setattr(module, "artifact", lambda selected: calibration)

    def bind(selected, passed, artifact, *, replay):
        assert selected is config
        assert passed is baseline
        assert artifact is calibration
        assert replay
        calls.append("bind")

    def live(selected, root):
        assert fresh
        assert selected is current
        assert root == tmp_path
        calls.append("live")
        return runtime

    def make_pass(selected, workflow, scorer, **kwargs):
        assert selected is config
        assert workflow is runtime.workflow
        assert scorer is runtime.alternative_scorer
        assert kwargs["fresh"] == "invented-fresh"
        assert kwargs["directory"] == current.local / "fresh/invented-fresh/pass"
        assert kwargs["support_ready"] is module.support_checkpoint
        calls.append("pass")
        return record

    def load_pass(selected, passed):
        assert selected is config
        assert passed is record
        calls.append("load")
        return loaded

    def checked_pass(selected, passed, *, fresh):
        assert selected is current
        assert passed is loaded
        assert fresh
        calls.append("check")

    def make_run(selected, passed, artifact, **kwargs):
        assert selected is config
        assert passed is (loaded if fresh else baseline)
        assert artifact is calibration
        suffix = "fresh/invented-fresh/run" if fresh else "dev/run"
        assert kwargs["directory"] == current.local / suffix
        calls.append("run")
        return SimpleNamespace(
            partition=Partition.DEV,
            status="complete",
            event_ids=("invented-event",),
            fresh="invented-fresh" if fresh else None,
        )

    for name, callback in (
        ("bind_policy", bind),
        ("live", live),
        ("make_pass", make_pass),
        ("load_pass", load_pass),
        ("checked_pass", checked_pass),
        ("make_run", make_run),
    ):
        monkeypatch.setattr(module, name, callback)
    args = ["pilot", "--repo", str(tmp_path), "run", "--settings", "invented.json"]
    args += ["--partition", "dev"]
    if fresh:
        args += ["--fresh", "invented-fresh", "--models-root", str(tmp_path)]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0
    assert MARKER not in result.output
    assert calls == (
        ["bind", "live", "pass", "load", "check", "run"] if fresh else ["bind", "run"]
    )


@pytest.mark.parametrize(
    "options", [[], ["--partition", "train", "--models-root", "."]]
)
def test_fresh_requirements_refuse_before_intake(tmp_path, monkeypatch, options):
    module = importlib.import_module("earnings_pipeline.pilot_commands")
    monkeypatch.setattr(module, "intake", lambda *args: pytest.fail("intake opened"))
    result = CliRunner().invoke(
        app,
        [
            "pilot",
            "--repo",
            str(tmp_path),
            "run",
            "--settings",
            "invented.json",
            "--fresh",
            "invented-fresh",
            *options,
        ],
    )
    assert result.exit_code == 1
    assert "fresh" in result.output
    assert "intake opened" not in result.output
