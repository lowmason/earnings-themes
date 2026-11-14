"""The command line's browser setup, with the install replaced: no download here."""

import ast
import subprocess
from pathlib import Path

import httpx
import pytest
from earnings_ingestion.browser import install as install_module
from earnings_ingestion.browser.install import Binaries, load_pin
from earnings_pipeline import cli
from typer.testing import CliRunner

RUNNER = CliRunner()


def test_setup_installs_the_pin_into_the_cache(monkeypatch, tmp_path: Path) -> None:
    calls = []

    def fake_install(pin, cache, fetch):
        calls.append((pin.version, cache, fetch))
        return Binaries(
            browser=cache / "chrome", driver=cache / "chromedriver", version=pin.version
        )

    monkeypatch.setattr(cli, "load_pin", lambda: load_pin("mac-arm64"))
    monkeypatch.setattr(cli, "install", fake_install)
    result = RUNNER.invoke(cli.app, ["browser", "setup", "--cache", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert calls == [("154.0.8037.57", tmp_path, cli.download)]
    assert "Chrome for Testing 154.0.8037.57 (mac-arm64)" in result.output
    assert f"driver: {tmp_path / 'chromedriver'}" in result.output


def test_setup_refuses_a_platform_with_no_pin(monkeypatch) -> None:
    monkeypatch.setattr(cli, "load_pin", lambda: None)
    result = RUNNER.invoke(cli.app, ["browser", "setup"])
    assert result.exit_code == 1
    assert "No Chrome for Testing build is pinned" in result.output


def test_setup_reports_a_refused_archive(monkeypatch, tmp_path: Path) -> None:
    def refuse(pin, cache, fetch):
        raise ValueError("chrome: got 3 bytes; the manifest pins 191429663")

    monkeypatch.setattr(cli, "load_pin", lambda: load_pin("mac-arm64"))
    monkeypatch.setattr(cli, "install", refuse)
    result = RUNNER.invoke(cli.app, ["browser", "setup", "--cache", str(tmp_path)])
    assert result.exit_code == 1
    assert "Refused: chrome: got 3 bytes" in result.output


@pytest.mark.parametrize(
    "error",
    [
        httpx.ConnectError("no route to host"),
        OSError("No space left on device"),
        subprocess.TimeoutExpired(["chrome", "--version"], 60),
        RuntimeError("the cache holds no installed pin after the install"),
    ],
)
def test_setup_reports_an_ordinary_failure_in_one_line(monkeypatch, tmp_path, error):
    def fail(pin, cache, fetch):
        raise error

    monkeypatch.setattr(cli, "load_pin", lambda: load_pin("mac-arm64"))
    monkeypatch.setattr(cli, "install", fail)
    result = RUNNER.invoke(cli.app, ["browser", "setup", "--cache", str(tmp_path)])
    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert result.stderr == f"Failed: {error}\n"


@pytest.mark.parametrize(
    "error",
    [
        subprocess.CalledProcessError(1, ["chromedriver", "--version"]),
        FileNotFoundError("chromedriver"),
    ],
    ids=["subprocess-exit", "missing-file"],
)
def test_setup_reports_each_subclass_of_a_setup_failure_in_one_line(
    monkeypatch, tmp_path, error
):
    def fail(pin, cache, fetch):
        raise error

    monkeypatch.setattr(cli, "load_pin", lambda: load_pin("mac-arm64"))
    monkeypatch.setattr(cli, "install", fail)
    result = RUNNER.invoke(cli.app, ["browser", "setup", "--cache", str(tmp_path)])
    assert result.exit_code == 1
    assert result.stderr == f"Failed: {error}\n"
    assert "Refused" not in result.output


@pytest.mark.parametrize(
    ("status", "headers"),
    [
        (403, {}),
        (302, {"location": "https://example.invalid/elsewhere.zip"}),
    ],
    ids=["client-error", "redirect"],
)
def test_setup_reports_a_real_http_status_error_as_its_first_line(
    monkeypatch, tmp_path, status, headers
):
    """``download`` calls ``raise_for_status``, whose message spans 2 or 3 lines."""
    request = httpx.Request("GET", "https://example.invalid/chrome.zip")
    reply = httpx.Response(status, headers=headers, request=request)
    with pytest.raises(httpx.HTTPStatusError) as raised:
        reply.raise_for_status()
    error = raised.value
    lines = str(error).splitlines()
    assert len(lines) >= 2

    def fail(pin, cache, fetch):
        raise error

    monkeypatch.setattr(cli, "load_pin", lambda: load_pin("mac-arm64"))
    monkeypatch.setattr(cli, "install", fail)
    result = RUNNER.invoke(cli.app, ["browser", "setup", "--cache", str(tmp_path)])
    assert result.exit_code == 1
    assert result.stderr == f"Failed: {lines[0]}\n"
    assert len(result.stderr.splitlines()) == 1


def test_a_refused_archive_keeps_its_refused_line_and_prints_no_failed_line(
    monkeypatch, tmp_path
):
    def refuse(pin, cache, fetch):
        raise ValueError("chromedriver reports '153.0.0.0', not 154.0.8037.57")

    monkeypatch.setattr(cli, "load_pin", lambda: load_pin("mac-arm64"))
    monkeypatch.setattr(cli, "install", refuse)
    result = RUNNER.invoke(cli.app, ["browser", "setup", "--cache", str(tmp_path)])
    assert result.exit_code == 1
    assert result.stderr == (
        "Refused: chromedriver reports '153.0.0.0', not 154.0.8037.57\n"
    )


def test_the_cli_reaches_the_setup_failures_through_ingestion_not_httpx() -> None:
    tree = ast.parse(Path(cli.__file__).read_text(encoding="utf-8"))
    imported = {
        alias.name.partition(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.partition(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "httpx" not in imported
    assert cli.SETUP_FAILURES is install_module.SETUP_FAILURES
