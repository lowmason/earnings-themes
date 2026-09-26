"""The command line's browser setup, with the install replaced: no download here."""

from pathlib import Path

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
