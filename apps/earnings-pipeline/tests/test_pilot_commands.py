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


@pytest.mark.parametrize(
    ("fresh", "resume"), [(False, False), (True, False), (True, True)]
)
def test_run_dispatch_binds_before_runtime_and_uses_exact_config(
    tmp_path, monkeypatch, fresh, resume
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
        assert kwargs["resume"] is resume
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
        ("processed", lambda passed: passed is (loaded if fresh else baseline)),
    ):
        monkeypatch.setattr(module, name, callback)
    args = ["pilot", "--repo", str(tmp_path), "run", "--settings", "invented.json"]
    args += ["--partition", "dev"]
    if fresh:
        args += ["--fresh", "invented-fresh", "--models-root", str(tmp_path)]
    if resume:
        args += ["--resume"]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0
    assert result.output.strip().splitlines()[-1].endswith("processed yes")
    assert MARKER not in result.output
    assert calls == (
        ["bind", "live", "pass", "load", "check", "run"] if fresh else ["bind", "run"]
    )


RESUME_LINE = "Stopped: rerun the same command with --resume"
NO_STATE_LINE = "Stopped before any state was written: rerun the same command"


def fresh_current(tmp_path):
    from types import SimpleNamespace

    from earnings_themes.split import Partition

    config = SimpleNamespace(
        repo=tmp_path,
        extraction_cache="data/runs/pilot/caches/extraction",
        coding_cache="data/runs/pilot/caches/coding",
        support_cache="data/runs/pilot/caches/support",
    )
    return SimpleNamespace(
        config=config, local=tmp_path / "data/runs/pilot", partition=Partition.DEV
    )


def fresh_args(tmp_path, *extra):
    return [
        "pilot",
        "--repo",
        str(tmp_path),
        "run",
        "--settings",
        "invented.json",
        *extra,
    ]


@pytest.mark.parametrize(
    "extra",
    [
        ("--partition", "dev", "--resume"),
        ("--partition", "train", "--resume", "--fresh", "invented-fresh"),
    ],
    ids=("without_fresh", "train"),
)
def test_resume_without_fresh_or_off_dev_refuses_before_intake(
    tmp_path, monkeypatch, extra
):
    module = importlib.import_module("earnings_pipeline.pilot_commands")
    monkeypatch.setattr(module, "intake", lambda *args: pytest.fail("intake ran"))
    if "--fresh" in extra:
        extra = (*extra, "--models-root", str(tmp_path))
    result = CliRunner().invoke(app, fresh_args(tmp_path, *extra))
    assert result.exit_code == 1
    assert result.output.strip().splitlines() == ["Refused: fresh: malformed_record"]


def test_resume_over_a_finished_run_refuses_state_run_conflict(tmp_path, monkeypatch):
    module = importlib.import_module("earnings_pipeline.pilot_commands")
    current = fresh_current(tmp_path)
    record = current.local / "fresh/invented-fresh/run/run-record.json"
    record.parent.mkdir(parents=True)
    record.write_bytes(b"{}")
    monkeypatch.setattr(module, "intake", lambda *args: current)
    for name in ("baseline", "artifact", "bind_policy", "live", "make_pass"):
        monkeypatch.setattr(
            module, name, lambda *args, _name=name, **kwargs: pytest.fail(_name)
        )
    args = ["--partition", "dev", "--fresh", "invented-fresh", "--resume"]
    args += ["--models-root", str(tmp_path)]
    result = CliRunner().invoke(app, fresh_args(tmp_path, *args))
    assert result.exit_code == 1
    assert result.output.strip().splitlines() == [
        "Refused: configuration: state_run_conflict"
    ]


@pytest.mark.parametrize("where", ["make_pass", "checkpoint", "intake"])
def test_a_stop_prints_one_closed_line_and_exits_130(tmp_path, monkeypatch, where):
    """D21-38 rule 8: one closed line and status 130, at any point of a fresh run."""
    from types import SimpleNamespace

    import typer

    module = importlib.import_module("earnings_pipeline.pilot_commands")
    current = fresh_current(tmp_path)

    def intake(*args):
        if where == "intake":
            raise KeyboardInterrupt()
        return current

    def make_pass(*args, **kwargs):
        kwargs["directory"].mkdir(parents=True)
        if where == "checkpoint":
            kwargs["support_ready"]()
        raise KeyboardInterrupt()

    def confirm(*args, **kwargs):
        raise typer.Abort()

    monkeypatch.setattr(module, "intake", intake)
    monkeypatch.setattr(module, "baseline", lambda selected: object())
    monkeypatch.setattr(module, "artifact", lambda selected: object())
    monkeypatch.setattr(module, "bind_policy", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        module,
        "live",
        lambda *args: SimpleNamespace(workflow=object(), alternative_scorer=object()),
    )
    monkeypatch.setattr(module, "make_pass", make_pass)
    monkeypatch.setattr(module.typer, "confirm", confirm)
    args = ["--partition", "dev", "--fresh", "invented-fresh"]
    args += ["--models-root", str(tmp_path)]
    result = CliRunner().invoke(app, fresh_args(tmp_path, *args))
    expected = NO_STATE_LINE if where == "intake" else RESUME_LINE
    assert result.exit_code == 130
    assert result.output.strip().splitlines()[-1] == expected
    assert result.output.count("Stopped") == 1
    assert "Traceback" not in result.output
    assert "Aborted" not in result.output
    if where == "intake":
        assert "--resume" not in result.output
        assert not (current.local / "fresh").exists()


@pytest.mark.parametrize(
    ("status", "counted", "expected"),
    [("complete", True, "yes"), ("partial", True, "yes"), ("partial", False, "no")],
)
def test_run_prints_whether_its_pass_is_processed(
    tmp_path, monkeypatch, status, counted, expected
):
    from types import SimpleNamespace

    from earnings_themes.split import Partition

    module = importlib.import_module("earnings_pipeline.pilot_commands")
    baseline = object()
    current = SimpleNamespace(
        config=object(), local=tmp_path / "data/runs/pilot", partition=Partition.DEV
    )
    seen = []
    monkeypatch.setattr(module, "intake", lambda *args: current)
    monkeypatch.setattr(module, "baseline", lambda selected: baseline)
    monkeypatch.setattr(module, "artifact", lambda selected: object())
    monkeypatch.setattr(module, "bind_policy", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        module, "processed", lambda passed: seen.append(passed) or counted
    )
    monkeypatch.setattr(
        module,
        "make_run",
        lambda *args, **kwargs: SimpleNamespace(
            partition=Partition.DEV,
            status=status,
            event_ids=("invented-event",),
            fresh=None,
        ),
    )
    args = ["pilot", "--repo", str(tmp_path), "run", "--settings", "invented.json"]
    result = CliRunner().invoke(app, [*args, "--partition", "dev"])
    assert result.exit_code == 0
    assert result.output.strip().splitlines()[-1] == (
        f"partition dev status {status} events 1 fresh none processed {expected}"
    )
    assert seen == [baseline]


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


def _assessment_error(kind):
    from earnings_themes.coding.records import CodingError
    from earnings_themes.support.problems import SupportError

    class Unlisted(SupportError):
        def __str__(self):
            return MARKER

    return {
        "coding": lambda: CodingError("hierarchy_conflict"),
        "support": lambda: SupportError("unexpected_error"),
        "unlisted": lambda: Unlisted("unexpected_error"),
    }[kind]()


@pytest.mark.parametrize(
    ("kind", "reason"),
    [
        ("coding", "hierarchy_conflict"),
        ("support", "unexpected_error"),
        ("unlisted", "malformed_record"),
    ],
)
def test_assessment_refusal_prints_its_closed_reason(
    kind, reason, tmp_path, monkeypatch
):
    """D21-28: the closed reason is printed; anything else stays malformed_record."""
    module = importlib.import_module("earnings_pipeline.pilot_commands")

    def refuse(*args, **kwargs):
        raise _assessment_error(kind)

    monkeypatch.setattr(module, "open_pilot", refuse)
    args = ["pilot", "--repo", str(tmp_path), "pass", "--settings", "invented.json"]
    result = CliRunner().invoke(app, [*args, "--models-root", str(tmp_path)])
    assert result.exit_code == 1
    assert f"Refused: assessment: {reason}" in result.output
    assert MARKER not in result.output


@pytest.mark.parametrize("fresh", [False, True])
def test_run_prints_processed_yes_for_a_pass_cut_at_the_request_ceiling(
    tmp_path, monkeypatch, fresh
):
    """D21-35 end to end: only intake, calibration and the live runtime are invented.

    The real baseline, checked_pass, bind_policy, make_run and processed all run, over
    a document with more claims than its request ceiling.
    """
    from types import SimpleNamespace

    from earnings_themes.split import Partition

    workflow = importlib.import_module(
        "apps.earnings-pipeline.tests.test_pilot_workflow"
    )
    module = importlib.import_module("earnings_pipeline.pilot_commands")
    partition = Partition.DEV
    config, loaded = workflow.cut_case(tmp_path, partition=partition)
    current = SimpleNamespace(
        config=config,
        local=tmp_path / "data/runs/pilot",
        partition=partition,
        settings=SimpleNamespace(
            alternative_scorer=loaded.alternative.record.scorer_identity
        ),
    )
    calibration = workflow.bound_artifact(config, loaded)
    rt = workflow.runtime(config, [], claims=3)
    monkeypatch.setattr(module, "intake", lambda *args: current)
    monkeypatch.setattr(module, "artifact", lambda selected: calibration)
    monkeypatch.setattr(
        module,
        "live",
        lambda selected, root: SimpleNamespace(
            workflow=rt, alternative_scorer=rt.scorer
        ),
    )
    monkeypatch.setattr(module, "support_checkpoint", lambda: None)
    args = ["pilot", "--repo", str(tmp_path), "run", "--settings", "invented.json"]
    args += ["--partition", "dev"]
    if fresh:
        args += ["--fresh", "invented-fresh", "--models-root", str(tmp_path)]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert result.output.strip().splitlines()[-1] == (
        f"partition dev status partial events {len(config.selected_event_ids)} "
        f"fresh {'invented-fresh' if fresh else 'none'} processed yes"
    )
