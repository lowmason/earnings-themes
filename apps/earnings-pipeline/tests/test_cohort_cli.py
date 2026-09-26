"""``earnings-pipeline cohort`` on the synthetic cohort; the clients are replaced."""

import shutil
from contextlib import contextmanager
from pathlib import Path

import pytest
from earnings_core import sha256_hex
from earnings_ingestion.cohort.synthetic import FIXTURE_DIR, write_synthetic_cohort
from earnings_ingestion.fetch.client import Fetched
from earnings_ingestion.fetch.records import Retrieval
from earnings_pipeline import cli, cohort_cli
from typer.testing import CliRunner

RUNNER = CliRunner()


@pytest.fixture(scope="module")
def generated(tmp_path_factory) -> Path:
    repo = tmp_path_factory.mktemp("generated")
    write_synthetic_cohort(repo)
    return repo


@pytest.fixture
def repo(generated: Path, tmp_path: Path) -> Path:
    shutil.copytree(generated, tmp_path, dirs_exist_ok=True)
    return tmp_path


def run(repo: Path, *args: str):
    layout = [
        "cohort",
        "--repo",
        str(repo),
        "--config-dir",
        str(FIXTURE_DIR),
        "--store",
        str(FIXTURE_DIR / "raw"),
        "--register",
        str(FIXTURE_DIR / "membership-source-register.toml"),
        "--sec-register",
        str(FIXTURE_DIR / "source-register.toml"),
    ]
    return RUNNER.invoke(cli.app, [*layout, *args])


def test_build_reports_every_finding_and_no_blocking_one(repo) -> None:
    result = run(repo, "build")
    assert result.exit_code == 0, result.output
    assert "resolved  membership_conflict:corvid-common" in result.stdout
    assert "noted  gap:2026q3" in result.stdout
    assert "0 blocking findings" in result.stdout


def test_build_fails_while_a_finding_holds_the_freeze(repo) -> None:
    (repo / FIXTURE_DIR / "overrides.toml").unlink()
    result = run(repo, "build")
    assert result.exit_code == 1
    assert "BLOCKING  identity:eastfield-common  digest " in result.stdout


def test_freeze_names_the_version_that_holds_the_content(repo) -> None:
    result = run(repo, "freeze")
    assert result.exit_code == 0, result.output
    assert "unchanged: djia-synthetic v1" in result.stdout


def test_freeze_refuses_with_the_blocking_findings(repo) -> None:
    (repo / FIXTURE_DIR / "overrides.toml").unlink()
    result = run(repo, "freeze")
    assert result.exit_code == 1
    assert "BLOCKING  membership_conflict:corvid-common" in result.stderr


def test_cite_keeps_the_cited_text_off_stdout(repo) -> None:
    page = next(
        path
        for path in (repo / FIXTURE_DIR / "raw" / "synthetic-index").glob("*.html")
        if b"Corvid Systems (CRVD) will replace" in path.read_bytes()
    )
    result = run(
        repo, "cite", "synthetic-index", page.stem, "--find", "Corvid Systems (CRVD)"
    )
    assert result.exit_code == 0, result.output
    assert "span = [" in result.stdout
    assert f'cited_sha256 = "{sha256_hex(b"Corvid Systems (CRVD)")}"' in result.stdout
    assert "Corvid" not in result.stdout
    assert "Corvid Systems (CRVD)" in result.stderr


def test_cite_line_takes_the_whole_row(repo) -> None:
    page = next((repo / FIXTURE_DIR / "raw" / "synthetic-roster").glob("*.html"))
    result = run(repo, "cite", "synthetic-roster", page.stem, "--find", "ACM", "--line")
    assert result.exit_code == 0, result.output
    assert "span = [" in result.stdout
    assert "\\t" in result.stderr


def test_register_saves_a_hand_saved_page(repo, tmp_path_factory) -> None:
    saved = tmp_path_factory.mktemp("browser") / "notice.html"
    saved.write_bytes(b"<p>Saved by hand.</p>")
    result = run(
        repo,
        "register",
        "synthetic-index",
        str(saved),
        "--url",
        "https://index.example/notices/by-hand",
        "--saved-at",
        "2026-09-29T10:00:00",
    )
    assert result.exit_code == 0, result.output
    assert result.stdout.startswith(sha256_hex(b"<p>Saved by hand.</p>"))


def test_fetch_sec_goes_through_the_shared_client(repo, monkeypatch) -> None:
    requested = []

    class FakeSec:
        class throttle:
            count = 0

        def fetch(self, url, types):
            requested.append(url)
            FakeSec.throttle.count += 1
            raise cohort_cli.AccessStop(f"403 persisted for {url}")

    @contextmanager
    def fake_open(repo_path):
        yield FakeSec()

    monkeypatch.setattr(cohort_cli, "open_sec_client", fake_open)
    result = run(repo, "fetch-sec")
    assert result.exit_code == 1
    assert "Stopped: 403 persisted" in result.stderr
    assert requested == ["https://www.sec.gov/files/company_tickers.json"]


def test_fetch_saves_pages_through_the_web_client(repo, monkeypatch) -> None:
    body = b"<p>A notice.</p>"

    class FakeWeb:
        def fetch(self, url, types):
            return Fetched(
                body=body,
                retrieval=Retrieval.model_validate(
                    {
                        "request_url": url,
                        "final_url": url,
                        "retrieved_at": "2026-09-29T10:00:00Z",
                        "retrieval_method": "http",
                        "http_status": 200,
                        "media_type": "text/html",
                        "content_type": "text/html",
                        "byte_count": len(body),
                        "sha256": sha256_hex(body),
                    },
                    strict=False,
                ),
            )

    @contextmanager
    def fake_open(repo_path, hosts):
        assert hosts == ["index.example"]
        yield FakeWeb()

    monkeypatch.setattr(cohort_cli, "open_web_client", fake_open)
    result = run(repo, "fetch", "synthetic-index", "https://index.example/notices/new")
    assert result.exit_code == 0, result.output
    assert sha256_hex(body) in result.stdout
