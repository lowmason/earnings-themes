"""CLI help uses no input, model, browser, or protected command."""

from earnings_pipeline.cli import app
from typer.testing import CliRunner


def test_extract_help_is_registered():
    result = CliRunner().invoke(app, ["extract", "run", "--help"])
    assert result.exit_code == 0
    assert "--config" in result.output


import importlib

config_cases = importlib.import_module("apps.earnings-pipeline.tests.test_theme_config")
workflow_cases = importlib.import_module(
    "apps.earnings-pipeline.tests.test_theme_workflow"
)


def test_cli_replay_success_prints_fixture_scope(tmp_path, monkeypatch):
    _config, payload = workflow_cases.seed_case(tmp_path)
    path = config_cases.write_config(tmp_path, payload)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["extract", "run", "--config", str(path)])
    assert result.exit_code == 0
    assert "scope=fixture" in result.output and "status=state_recorded" in result.output
    assert "Invented" not in result.output


def test_cli_ordinary_refusal_suppresses_source_text(tmp_path, monkeypatch):
    payload = config_cases.invented_replay_config(tmp_path)
    payload["mode"] = "Invented forbidden sentinel"
    path = config_cases.write_config(tmp_path, payload)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["extract", "run", "--config", str(path)])
    assert result.exit_code == 1
    assert "reason=malformed_record" in result.output
    assert (
        "forbidden sentinel" not in result.output and "Traceback" not in result.output
    )


def test_cli_arbitrary_crash_is_closed(tmp_path, monkeypatch):
    module = importlib.import_module("earnings_pipeline.extract_cli")
    monkeypatch.setattr(
        module,
        "load_workflow_config",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            RuntimeError("Invented forbidden sentinel")
        ),
    )
    result = CliRunner().invoke(
        app, ["extract", "run", "--config", str(tmp_path / "config.json")]
    )
    assert result.exit_code == 1
    assert "reason=unexpected_error" in result.output
    assert (
        "forbidden sentinel" not in result.output and "Traceback" not in result.output
    )
