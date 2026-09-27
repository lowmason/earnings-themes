"""``earnings-pipeline events`` on the committed synthetic event corpus. ``discover``
runs the shared SEC client over a transport that serves the corpus's saved
responses, so no request leaves the process."""

import shutil
from contextlib import contextmanager
from pathlib import Path

import httpx
import pytest
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.fixture import COHORT_MANIFEST, FIXTURE_DIR
from earnings_ingestion.fetch.records import Retrieval
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec import client as sec_client
from earnings_pipeline import cli, events_cli
from typer.testing import CliRunner

RUNNER = CliRunner()
REPO = Path(__file__).resolve().parents[3]
UNIVERSES = COHORT_MANIFEST.parent
IDENTITY = {"EDGAR_IDENTITY": "Plan 7 synthetic discovery test@example.com"}
EVENTS_HASH = "438bfec835dee07c119e1b0b24e985fb549dc712564850dc3f73914b557bfe58"
PILOT_HASH = "71c6ac4fabc3b7e727da88b4ee74048a0ee3559c8e5ce26c02227376d820333c"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """The synthetic cohort's manifests and the event corpus, at their paths."""
    for directory in (UNIVERSES, FIXTURE_DIR):
        shutil.copytree(REPO / directory, tmp_path / directory)
    return tmp_path


def run(repo: Path, *args: str, store: Path = FIXTURE_DIR / "raw"):
    layout = [
        "events",
        "--repo",
        str(repo),
        "--universe-dir",
        str(UNIVERSES),
        "--corpus-dir",
        str(FIXTURE_DIR),
        "--store",
        str(store),
        "--corpus-id",
        "djia-synthetic",
    ]
    return RUNNER.invoke(cli.app, [*layout, *args])


def test_build_prints_every_event_and_passes_when_nothing_holds(repo) -> None:
    result = run(repo, "build")
    assert result.exit_code == 0, result.output
    assert (
        "cik-0009990001:2025-02-28  eligible  member_at_publication"
        "  0009990001-25-000008 (override)"
    ) in result.stdout
    assert "[acknowledged by gap-corvid]" in result.stdout
    assert result.stdout.splitlines()[-1] == (
        f"32 events, 27 eligible, content {EVENTS_HASH}"
    )


def test_build_fails_and_prints_digests_while_anything_holds(repo) -> None:
    (repo / FIXTURE_DIR / "overrides.toml").unlink()
    result = run(repo, "build")
    assert result.exit_code == 1
    assert (
        "acknowledge period_gap:cik-0009990003:2024-07-01:2024-12-31 with digest"
        " b6787303110f5ad9967e93c6140a79db0425d1ac99e4a67d3a67a82fd77f200e"
    ) in result.stdout
    assert "cik-0009990005:2025-06-27: no_release_filing, not retained" in (
        result.stdout
    )


def test_freeze_names_the_version_that_holds_the_content(repo) -> None:
    result = run(repo, "freeze")
    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines() == [
        "unchanged: djia-synthetic v1",
        f"tests/fixtures/events/events-v1.json  {EVENTS_HASH}",
        "tests/fixtures/events/events-v1.evidence.json",
    ]


def test_freeze_refuses_and_names_what_holds(repo) -> None:
    (repo / FIXTURE_DIR / "overrides.toml").unlink()
    result = run(repo, "freeze")
    assert result.exit_code == 1
    assert "HOLDS  period_gap:cik-0009990002:2025-03-31:2026-07-01: " in result.stderr
    assert "HOLDS  cik-0009990002:2024-09-30: same_day_transition, not retained" in (
        result.stderr
    )


def test_select_names_the_pilot_that_holds_the_selection(repo) -> None:
    result = run(repo, "select")
    assert result.exit_code == 0, result.output
    lines = result.stdout.splitlines()
    assert lines[0] == "  1  cik-0009990003:2026-03-31  issuer_coverage"
    assert lines[27] == (
        "reported: cik-0009990002's exit on 2024-11-08 has no eligible event on its"
        " member side"
    )
    assert lines[28:] == [
        "unchanged: djia-synthetic-pilot v1: 27 of target 27, underfilled",
        f"tests/fixtures/events/pilot-v1.json  {PILOT_HASH}",
    ]


def test_select_refuses_without_a_frozen_event_manifest(repo) -> None:
    for name in ("events-v1.json", "events-v1.evidence.json", "pilot-v1.json"):
        (repo / FIXTURE_DIR / name).unlink()
    result = run(repo, "select")
    assert result.exit_code == 1
    assert "Refused: no frozen event manifest in tests/fixtures/events" in (
        result.stderr
    )


def served() -> dict[str, tuple[bytes, str]]:
    root = REPO / FIXTURE_DIR / "raw"
    store = ArtifactStore(root, REPO)
    found = {}
    for path in sorted((root / SEC_SOURCE_ID / "retrievals").glob("*/*.json")):
        record = Retrieval.model_validate_json(path.read_text(encoding="utf-8"))
        stored = store.get(
            SEC_SOURCE_ID,
            record.sha256,
            rights_status=SEC_RIGHTS.rights_status,
            rights_basis=SEC_RIGHTS.rights_basis,
        )
        found[record.request_url] = (stored.body, record.media_type)
    return found


def client(monkeypatch, responses: dict[str, tuple[bytes, str]], status: int = 200):
    """Replace the CLI's client with the shared client over a serving transport."""
    budgets: list[int] = []

    def handle(request: httpx.Request) -> httpx.Response:
        body, media_type = responses.get(str(request.url), (b"", "text/plain"))
        code = status if str(request.url) in responses else 404
        return httpx.Response(code, content=body, headers={"content-type": media_type})

    @contextmanager
    def opened(*, max_requests: int):
        budgets.append(max_requests)
        with sec_client.open_sec_client(
            environ=IDENTITY,
            transport=httpx.MockTransport(handle),
            sleep=lambda seconds: None,
            max_requests=max_requests,
        ) as sec:
            yield sec

    monkeypatch.setattr(events_cli, "open_sec_client", opened)
    return budgets


def test_discover_states_its_budget_first_and_each_phase(repo, monkeypatch) -> None:
    budgets = client(monkeypatch, served())
    result = run(
        repo, "discover", "--max-requests", "90", store=Path("data/raw/events")
    )
    assert result.exit_code == 0, result.output
    assert budgets == [90]
    assert result.stdout.splitlines() == [
        "at most 90 requests to SEC, through the shared client",
        "submissions and companyfacts: 10 to fetch",
        "older pages and index pages: 38 to fetch",
        "older pages and index pages: 2 to fetch",
        "older pages and index pages: 0 to fetch",
        "primary documents: 34 to fetch",
        "fetched 84; requests sent: 84",
    ]


def test_discover_needs_the_approved_count(repo, monkeypatch) -> None:
    budgets = client(monkeypatch, served())
    result = run(repo, "discover", store=Path("data/raw/events"))
    assert result.exit_code == 1
    assert budgets == []
    assert "Refused: pass --max-requests" in result.stderr


def test_discover_stops_on_a_persistent_403_and_says_how_to_resume(
    repo, monkeypatch
) -> None:
    client(monkeypatch, served(), status=403)
    result = run(
        repo, "discover", "--max-requests", "90", store=Path("data/raw/events")
    )
    assert result.exit_code == 1
    assert "Stopped: " in result.stderr and "403" in result.stderr
    assert "a rerun fetches only what is missing" in result.stdout


def test_discover_filing_spends_at_most_two_requests(repo, monkeypatch) -> None:
    budgets = client(monkeypatch, served())
    result = run(repo, "discover", "--filing", "0009990005", "0009990005-99-000001")
    assert result.exit_code == 1
    assert budgets == [2]
    assert "Stopped: the saved filings of CIK 0009990005 list no" in result.stderr
