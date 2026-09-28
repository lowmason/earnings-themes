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


COHORT_STORE = Path("data") / "raw" / "cohort"


def run(repo: Path, *args: str, store: Path = FIXTURE_DIR / "raw"):
    layout = [
        "cohort",
        "--repo",
        str(repo),
        "--config-dir",
        str(FIXTURE_DIR),
        "--store",
        str(store),
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


def test_freeze_refuses_a_revert(repo) -> None:
    universe = repo / FIXTURE_DIR / "universe.toml"
    text = universe.read_text(encoding="utf-8")
    one, two = (f'selection_policy_version = "djia-pilot/{n}"' for n in (1, 2))
    universe.write_text(text.replace(one, two, 1), encoding="utf-8")
    assert "froze djia-synthetic v2" in run(repo, "freeze").stdout
    universe.write_text(text, encoding="utf-8")
    result = run(repo, "freeze")
    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit), result.exception
    assert "Refused: the build is djia-synthetic-v1.json's content, but v2" in (
        result.stderr
    )


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
    def fake_open(*, max_requests):
        assert max_requests == 5
        yield FakeSec()

    monkeypatch.setattr(cohort_cli, "open_sec_client", fake_open)
    result = run(repo, "fetch-sec", "--max-requests", "5", store=COHORT_STORE)
    assert result.exit_code == 1
    assert "Stopped: 403 persisted" in result.stderr
    assert result.stdout.splitlines() == ["requests sent: 1"]
    assert requested == ["https://www.sec.gov/files/company_tickers.json"]


@pytest.mark.parametrize("command", ["fetch-sec", "verify-live"])
def test_a_live_command_needs_the_approved_count(repo, monkeypatch, command) -> None:
    """fetch-sec and verify-live take the count the user approved, as events
    discover does, and refuse before any client opens (PR #6's review, F35)."""

    def refuse(*args, **kwargs):
        raise AssertionError("a client opened")

    monkeypatch.setattr(cohort_cli, "open_sec_client", refuse)
    monkeypatch.setattr(cohort_cli, "run_live", refuse)
    result = run(repo, command, store=COHORT_STORE)
    assert result.exit_code == 1
    assert "Refused: pass --max-requests" in result.stderr


def test_verify_live_prints_its_count_when_it_stops(repo, monkeypatch) -> None:
    def stopped(repo, *, max_requests, sent):
        assert max_requests == 30
        sent.count = 4
        raise cohort_cli.AccessStop("another client holds the lock")

    monkeypatch.setattr(cohort_cli, "run_live", stopped)
    result = run(repo, "verify-live", "--max-requests", "30")
    assert result.exit_code == 1
    assert result.stdout.splitlines() == ["requests sent: 4"]
    assert "Stopped: another client holds the lock" in result.stderr


def test_verify_live_prints_its_count_on_an_unforeseen_error(repo, monkeypatch) -> None:
    """An error no stop names, such as one httpx raises, still ends with the count
    (plan 8's final review)."""

    def unforeseen(repo, *, max_requests, sent):
        sent.count = 4
        raise LookupError("unforeseen")

    monkeypatch.setattr(cohort_cli, "run_live", unforeseen)
    result = run(repo, "verify-live", "--max-requests", "30")
    assert isinstance(result.exception, LookupError)
    assert result.stdout.splitlines() == ["requests sent: 4"]


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
    def fake_open(hosts):
        assert hosts == ["index.example"]
        yield FakeWeb()

    monkeypatch.setattr(cohort_cli, "open_web_client", fake_open)
    result = run(
        repo,
        "fetch",
        "synthetic-index",
        "https://index.example/notices/new",
        store=COHORT_STORE,
    )
    assert result.exit_code == 0, result.output
    assert sha256_hex(body) in result.stdout


def test_register_saves_a_pdf_and_refuses_a_contradicting_type(
    repo, tmp_path_factory
) -> None:
    body = b"%PDF-1.4\n%%EOF\n"
    saved = tmp_path_factory.mktemp("browser") / "notice.pdf"
    saved.write_bytes(body)
    register = [
        "register",
        "synthetic-index",
        str(saved),
        "--url",
        "https://index.example/notices/by-hand.pdf",
        "--saved-at",
        "2026-09-29T10:00:00",
    ]
    stored = run(repo, *register, "--media-type", "application/pdf")
    assert stored.exit_code == 0, stored.output
    assert f"/synthetic-index/{sha256_hex(body)}.pdf" in stored.stdout
    refused = run(repo, *register, "--media-type", "text/html")
    assert refused.exit_code == 1
    assert "Refused: text/html contradicts the bytes" in refused.stderr


def test_terms_hashes_a_saved_copy_without_a_client(
    repo, monkeypatch, tmp_path_factory
) -> None:
    page = b"<html><body><p>Terms of use.</p></body></html>"
    saved = tmp_path_factory.mktemp("browser") / "terms.html"
    saved.write_bytes(page)
    for name in ("EDGAR_IDENTITY", "SOURCE_IDENTITY"):
        monkeypatch.delenv(name, raising=False)

    def no_client(*args, **kwargs):
        raise AssertionError("a saved copy needs no client")

    monkeypatch.setattr(cohort_cli, "open_web_client", no_client)
    monkeypatch.setattr(cohort_cli, "open_sec_client", no_client)
    terms = ["terms", "https://terms.example/terms-of-use", "--saved", str(saved)]
    hashed = run(repo, *terms)
    assert hashed.exit_code == 0, hashed.output
    digest = cohort_cli.terms_digest(page, "text/html")
    assert hashed.stdout == f'terms_sha256 = "{digest}"\n'
    refused = run(repo, *terms, "--media-type", "application/pdf")
    assert refused.exit_code == 1
    assert "Refused: application/pdf contradicts the bytes" in refused.stderr


@pytest.mark.parametrize(
    "command",
    [["fetch-sec"], ["fetch", "synthetic-index", "https://index.example/notices/n"]],
)
def test_a_fetching_command_refuses_a_store_outside_data_raw(
    repo, monkeypatch, command
) -> None:
    """Fetched bytes are saved only under data/raw, which Git ignores; the check
    comes before any client opens (PR #6's review, F19)."""

    def refuse(*args, **kwargs):
        raise AssertionError("a client opened")

    monkeypatch.setattr(cohort_cli, "open_sec_client", refuse)
    monkeypatch.setattr(cohort_cli, "open_web_client", refuse)
    result = run(repo, *command)
    assert result.exit_code == 1
    assert result.stderr.splitlines() == [
        (
            f"Refused: {FIXTURE_DIR / 'raw'} does not resolve under data/raw, where"
            " fetched bytes are kept out of Git"
        )
    ]


def test_freeze_prints_a_manifest_outside_the_repo_in_full(
    repo, tmp_path_factory
) -> None:
    outside = tmp_path_factory.mktemp("elsewhere") / "cohort"
    shutil.copytree(repo / FIXTURE_DIR, outside)
    result = RUNNER.invoke(
        cli.app,
        [
            "cohort",
            "--repo",
            str(repo),
            "--config-dir",
            str(outside),
            "--store",
            str(FIXTURE_DIR / "raw"),
            "--register",
            str(outside / "membership-source-register.toml"),
            "--sec-register",
            str(outside / "source-register.toml"),
            "freeze",
        ],
    )
    assert result.exit_code == 0, result.output
    (line,) = [line for line in result.stdout.splitlines() if "-v1.json" in line]
    assert line.startswith(str(outside / "manifests" / "djia-synthetic-v1.json"))
