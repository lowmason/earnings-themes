"""``earnings-pipeline events`` on the committed synthetic event corpus. ``discover``
runs the shared SEC client over a transport that serves the corpus's saved
responses, so no request leaves the process."""

import shutil
from contextlib import contextmanager
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import httpx
import pytest
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.fixture import COHORT_MANIFEST, FIXTURE_DIR
from earnings_ingestion.events.freeze import serialize
from earnings_ingestion.events.layer import (
    CORVID,
    DYNAMO,
    REPORTS,
    RETRIEVED,
    exhibit_bodies,
    filings,
)
from earnings_ingestion.events.records import PilotManifest, pilot_content_hash
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.state_table import read_runs
from earnings_ingestion.events.states import DocumentState
from earnings_ingestion.events.synthetic import SyntheticStore, save, submissions_file
from earnings_ingestion.fetch.client import ProcessLock
from earnings_ingestion.fetch.records import Retrieval
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec import client as sec_client
from earnings_ingestion.sec.urls import filing_index_url, submissions_url
from earnings_pipeline import cli, events_cli
from typer.testing import CliRunner

RUNNER = CliRunner()
REPO = Path(__file__).resolve().parents[3]
UNIVERSES = COHORT_MANIFEST.parent
IDENTITY = {"EDGAR_IDENTITY": "Plan 7 synthetic discovery test@example.com"}
EVENTS_STORE = Path("data") / "raw" / "events"
EVENTS_HASH = "438bfec835dee07c119e1b0b24e985fb549dc712564850dc3f73914b557bfe58"
PILOT_HASH = "71c6ac4fabc3b7e727da88b4ee74048a0ee3559c8e5ce26c02227376d820333c"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """The synthetic cohort's manifests and the event corpus, at their paths."""
    for directory in (UNIVERSES, FIXTURE_DIR):
        shutil.copytree(REPO / directory, tmp_path / directory)
    return tmp_path


@pytest.fixture
def moved(repo: Path) -> Path:
    """The corpus's saved responses, moved under data/raw, where a command that
    fetches may save."""
    (repo / EVENTS_STORE).parent.mkdir(parents=True)
    shutil.move(repo / FIXTURE_DIR / "raw", repo / EVENTS_STORE)
    return repo / EVENTS_STORE


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


def test_build_names_each_blocking_finding_s_own_remedy(repo) -> None:
    """Only a period_gap or no_slots is acknowledged. An acceptance_time_unknown
    needs its filing's index page; an acceptance_time_mismatch has no remedy here.
    Dynamo's 10-Q of 2026-04-03 loses its acceptanceDateTime, and its 8-K of
    2026-07-21, whose index page is saved, gets one that follows neither convention."""
    unknown, mismatch = "0009990005-26-000017", "0009990005-26-000018"
    written = {unknown: "", mismatch: "2026-07-21T12:00:00.000Z"}
    listed = [
        replace(filing, written=written.get(filing.accession))
        for filing, _ in filings(DYNAMO)
    ]
    body = submissions_file(
        DYNAMO.cik, DYNAMO.name, listed, convention=DYNAMO.convention
    )
    store = ArtifactStore(repo / FIXTURE_DIR / "raw", repo)
    later = RETRIEVED + timedelta(days=1)
    save(store, submissions_url(DYNAMO.cik), body, "application/json", later)
    (repo / FIXTURE_DIR / "overrides.toml").unlink()
    result = run(repo, "build")
    assert result.exit_code == 1, result.output
    lines = result.stdout.splitlines()
    acknowledged = [line for line in lines if line.startswith("acknowledge ")]
    assert {line.split(":")[0] for line in acknowledged} == {"acknowledge period_gap"}
    assert (
        f"acceptance_time_unknown:{unknown}: run events discover --filing"
        f" {DYNAMO.cik} {unknown}"
    ) in lines
    assert (
        f"acceptance_time_mismatch:{mismatch}: no override or discover run answers it"
    ) in lines


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
    assert lines[:2] == [
        "reads djia-synthetic v1",
        f"tests/fixtures/events/events-v1.json  {EVENTS_HASH}",
    ]
    assert lines[2] == "  1  cik-0009990003:2026-03-31  issuer_coverage"
    assert lines[29] == (
        "reported: cik-0009990002's exit on 2024-11-08 has no eligible event on its"
        " member side"
    )
    assert lines[30:] == [
        "unchanged: djia-synthetic-pilot v1: 27 of target 27, underfilled",
        f"tests/fixtures/events/pilot-v1.json  {PILOT_HASH}",
    ]


def test_select_refuses_without_a_frozen_event_manifest(repo) -> None:
    for name in ("events-v1.json", "events-v1.evidence.json", "pilot-v1.json"):
        (repo / FIXTURE_DIR / name).unlink()
    result = run(repo, "select")
    assert result.exit_code == 1
    assert "Refused: no frozen event manifest holds this build's content" in (
        result.stderr
    )


def test_select_reads_the_version_the_build_reproduces(repo) -> None:
    """Freeze v1, freeze a changed v2, revert, and select: the build decides which
    version is current, so select reads v1 and names pilot v1 again (PR #6's
    review, F4)."""
    raw = repo / FIXTURE_DIR / "raw"

    def corvid(days: int, *, agreeing: bool) -> None:
        facts = [
            (filing.accession, year, period)
            for filing, report in filings(CORVID)
            if report in REPORTS[CORVID]
            for year, period in (report.labels[:1] if agreeing else report.labels)
        ]
        at = RETRIEVED + timedelta(days=days)
        SyntheticStore(raw, repo, at).companyfacts(CORVID.cik, CORVID.name, facts)

    corvid(1, agreeing=True)
    assert run(repo, "freeze").stdout.splitlines()[0] == "froze djia-synthetic v2"
    changed = run(repo, "select").stdout.splitlines()
    assert changed[0] == "reads djia-synthetic v2"
    assert changed[-2].startswith("froze djia-synthetic-pilot v2: ")
    corvid(2, agreeing=False)
    assert run(repo, "freeze").stdout.splitlines()[0] == "unchanged: djia-synthetic v1"
    result = run(repo, "select")
    assert result.exit_code == 0, result.output
    lines = result.stdout.splitlines()
    assert lines[:2] == [
        "reads djia-synthetic v1",
        f"tests/fixtures/events/events-v1.json  {EVENTS_HASH}",
    ]
    assert lines[-2:] == [
        "unchanged: djia-synthetic-pilot v1: 27 of target 27, underfilled",
        f"tests/fixtures/events/pilot-v1.json  {PILOT_HASH}",
    ]


def served() -> dict[str, tuple[bytes, str]]:
    """The fixture's saved responses, but the exhibits acquisition saved."""
    root = REPO / FIXTURE_DIR / "raw"
    store = ArtifactStore(root, REPO)
    found = {}
    exhibits = exhibit_bodies()
    for path in sorted((root / SEC_SOURCE_ID / "retrievals").glob("*/*.json")):
        record = Retrieval.model_validate_json(path.read_text(encoding="utf-8"))
        if record.request_url in exhibits:
            continue
        stored = store.get(
            SEC_SOURCE_ID,
            record.sha256,
            rights_status=SEC_RIGHTS.rights_status,
            rights_basis=SEC_RIGHTS.rights_basis,
        )
        found[record.request_url] = (stored.body, record.media_type)
    return found


def client(
    monkeypatch,
    responses: dict[str, tuple[bytes, str]],
    status: int = 200,
    moved: str | None = None,
):
    """Replace the CLI's client with the shared client over a serving transport,
    which redirects any URL ending in ``moved``."""
    budgets: list[int] = []

    def handle(request: httpx.Request) -> httpx.Response:
        if moved is not None and str(request.url).endswith(moved):
            return httpx.Response(301, headers={"Location": f"{request.url}-moved"})
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


def test_discover_names_a_saved_response_it_cannot_read_and_fails(
    repo, moved, monkeypatch
) -> None:
    """A saved response whose bytes are gone is never fetched again: discover names
    it and exits 1, and promises nothing of a rerun, which cannot mend it."""
    url = submissions_url("0009990001")
    saved = SavedResponses(ArtifactStore(moved, repo))
    artifact = saved.get(url).artifact
    (repo / artifact.storage_ref).unlink()
    client(monkeypatch, served())
    result = run(repo, "discover", "--max-requests", "5", store=EVENTS_STORE)
    assert result.exit_code == 1
    assert result.stdout.splitlines()[1:] == [
        "submissions and companyfacts: 0 to fetch",
        "older pages and index pages: 0 to fetch",
        "primary documents: 0 to fetch",
        "fetched 0; requests sent: 0",
    ]
    assert result.stderr.splitlines() == [
        (
            f"problem: {url}: no artifact {artifact.content_sha256} for source"
            " 'sec-edgar': its retrieval records remain, but its bytes are gone"
        )
    ]


def test_discover_filing_spends_at_most_two_requests(repo, monkeypatch) -> None:
    budgets = client(monkeypatch, served())
    result = run(
        repo,
        "discover",
        "--filing",
        "0009990005",
        "0009990005-99-000001",
        store=EVENTS_STORE,
    )
    assert result.exit_code == 1
    assert budgets == [2]
    assert "Stopped: the saved filings of CIK 0009990005 list no" in result.stderr


FILED = ("0009990001", "0009990001-24-000003")
"""An Item 2.02 8-K that its issuer's saved submissions list."""


def unsave(repo: Path, cik: str, accession: str) -> tuple[str, str]:
    """Delete the retrieval records of a filing's saved index page and primary
    document, so that discovery lacks both; return the two URLs."""
    folder = f"/{int(cik)}/{accession.replace('-', '')}/"
    root = repo / EVENTS_STORE / SEC_SOURCE_ID / "retrievals"
    exhibits = exhibit_bodies()
    gone = []
    for path in sorted(root.glob("*/*.json")):
        record = Retrieval.model_validate_json(path.read_text(encoding="utf-8"))
        if folder in record.request_url and record.request_url not in exhibits:
            path.unlink()
            gone.append(record.request_url)
    index = filing_index_url(cik, accession)
    (document,) = set(gone) - {index}
    assert len(gone) == 2
    return index, document


def test_discover_filing_keeps_a_smaller_approved_cap(repo, moved, monkeypatch) -> None:
    """An approved --max-requests is a hard ceiling with --filing too: the run stops
    at it, and a rerun fetches only what is left."""
    index, document = unsave(repo, *FILED)
    budgets = client(monkeypatch, served())
    result = run(
        repo, "discover", "--max-requests", "1", "--filing", *FILED, store=EVENTS_STORE
    )
    assert result.exit_code == 1
    assert budgets == [1]
    assert result.stdout.splitlines() == [
        "at most 1 requests to SEC, through the shared client",
        f"8-K {FILED[1]}: 1 to fetch",
        f"8-K {FILED[1]}'s document: 1 to fetch",
        "requests sent: 1; a rerun fetches only what is missing",
    ]
    assert "Stopped: request budget of 1 reached" in result.stderr
    saved = SavedResponses(ArtifactStore(moved, repo))
    assert index in saved and document not in saved
    result = run(repo, "discover", "--filing", *FILED, store=EVENTS_STORE)
    assert result.exit_code == 0, result.output
    assert budgets == [1, 2]
    assert result.stdout.splitlines()[1:] == [
        f"8-K {FILED[1]}: 0 to fetch",
        f"8-K {FILED[1]}'s document: 1 to fetch",
        "fetched 1; requests sent: 1",
    ]


def test_discover_filing_never_raises_its_cap(repo, moved, monkeypatch) -> None:
    unsave(repo, *FILED)
    budgets = client(monkeypatch, served())
    result = run(
        repo, "discover", "--max-requests", "5", "--filing", *FILED, store=EVENTS_STORE
    )
    assert result.exit_code == 0, result.output
    assert budgets == [2]
    assert result.stdout.splitlines()[-1] == "fetched 2; requests sent: 2"


@pytest.mark.parametrize(
    "second",
    [
        ["--filing", "0009990001", "0009990001-25-000008"],
        ["--filing=0009990001", "0009990001-25-000008"],
    ],
)
def test_discover_refuses_a_second_filing(repo, monkeypatch, second) -> None:
    """Each filing's requests are approved on their own: a second --filing is refused
    before any client opens, never dropped."""
    budgets = client(monkeypatch, served())
    result = run(repo, "discover", "--filing", *FILED, *second, store=EVENTS_STORE)
    assert result.exit_code == 1
    assert budgets == []
    assert result.stdout == ""
    assert "Refused: pass one --filing" in result.stderr


def test_discover_refuses_a_store_outside_data_raw(repo, monkeypatch) -> None:
    """tests/fixtures/ is committed, so fetched SEC pages saved there would reach this
    public repository: discover refuses before any client opens (PR #6's review,
    F19)."""

    def refuse(**kwargs):
        raise AssertionError("the client opened")

    monkeypatch.setattr(events_cli, "open_sec_client", refuse)
    result = run(
        repo, "discover", "--max-requests", "1", store=Path("tests/fixtures/x")
    )
    assert result.exit_code == 1
    assert result.stderr.splitlines() == [
        (
            "Refused: tests/fixtures/x does not resolve under data/raw, where"
            " fetched bytes are kept out of Git"
        )
    ]


def test_freeze_and_select_print_a_corpus_outside_the_repo_in_full(
    repo, tmp_path_factory
) -> None:
    """A corpus directory outside the repository, or spelled through a symlinked
    prefix, prints in full rather than crashing after the write (F38)."""
    outside = tmp_path_factory.mktemp("elsewhere") / "corpus"
    shutil.copytree(repo / FIXTURE_DIR, outside, ignore=shutil.ignore_patterns("raw"))
    layout = ["--corpus-dir", str(outside), "--store", str(FIXTURE_DIR / "raw")]

    def invoke(command: str):
        args = ["events", "--repo", str(repo), "--universe-dir", str(UNIVERSES)]
        return RUNNER.invoke(
            cli.app, [*args, *layout, "--corpus-id", "djia-synthetic", command]
        )

    froze = invoke("freeze")
    assert froze.exit_code == 0, froze.output
    assert froze.stdout.splitlines()[1:] == [
        f"{outside / 'events-v1.json'}  {EVENTS_HASH}",
        str(outside / "events-v1.evidence.json"),
    ]
    selected = invoke("select")
    assert selected.exit_code == 0, selected.output
    assert selected.stdout.splitlines()[-1] == (
        f"{outside / 'pilot-v1.json'}  {PILOT_HASH}"
    )


def test_discover_prints_its_count_when_saving_fails(repo, monkeypatch) -> None:
    """A full disk, or permissions, stops the run with its count, never a traceback
    (PR #6's review, F31)."""
    client(monkeypatch, served())

    def full(*args, **kwargs):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(ArtifactStore, "put", full)
    result = run(repo, "discover", "--max-requests", "90", store=EVENTS_STORE)
    assert result.exit_code == 1
    assert result.stdout.splitlines()[-1] == (
        "requests sent: 1; a rerun fetches only what is missing"
    )
    assert "Stopped: [Errno 28] No space left on device" in result.stderr


def test_discover_prints_its_count_when_a_saved_body_is_gone(
    repo, moved, monkeypatch
) -> None:
    """A companyfacts file whose body is gone stops the documents phase with the
    count, never a traceback (F31)."""
    url = "https://data.sec.gov/api/xbrl/companyfacts/CIK0009990001.json"
    artifact = SavedResponses(ArtifactStore(moved, repo)).get(url).artifact
    (repo / artifact.storage_ref).unlink()
    client(monkeypatch, served())
    result = run(repo, "discover", "--max-requests", "5", store=EVENTS_STORE)
    assert result.exit_code == 1
    assert result.stdout.splitlines()[-1] == (
        "requests sent: 0; a rerun fetches only what is missing"
    )
    assert "Stopped: no artifact" in result.stderr


def test_discover_prints_its_count_on_ctrl_c(repo, monkeypatch) -> None:
    client(monkeypatch, served())
    calls = []

    def interrupted(*args, **kwargs):
        calls.append(args)
        raise KeyboardInterrupt

    monkeypatch.setattr(ArtifactStore, "put", interrupted)
    result = run(repo, "discover", "--max-requests", "90", store=EVENTS_STORE)
    assert result.exit_code == 130
    assert calls
    assert "requests sent: 1; a rerun fetches only what is missing" in result.stdout


MISSING = "dyna-20250422-ex991.htm"
"""The one exhibit of the synthetic pilot that SEC never served."""


def forget_exhibits(store: Path) -> list[str]:
    """Delete the retrieval records of every saved exhibit, so acquisition lacks
    them; return their URLs."""
    exhibits = exhibit_bodies()
    gone = []
    for path in sorted((store / SEC_SOURCE_ID / "retrievals").glob("*/*.json")):
        record = Retrieval.model_validate_json(path.read_text(encoding="utf-8"))
        if record.request_url in exhibits:
            path.unlink()
            gone.append(record.request_url)
    return gone


def acquire_lines(result) -> list[str]:
    return result.stdout.splitlines()


def test_acquire_reads_the_current_records_and_states_its_count(
    repo, moved, monkeypatch
) -> None:
    """Every saved exhibit is read from the store; only the one SEC never served is
    requested, through the shared client, within the approved count."""
    budgets = client(monkeypatch, served())
    result = run(repo, "acquire", "--max-requests", "1", store=EVENTS_STORE)
    assert result.exit_code == 0, result.output
    assert budgets == [1]
    lines = acquire_lines(result)
    assert lines[:5] == [
        "reads djia-synthetic v1",
        f"tests/fixtures/events/events-v1.json  {EVENTS_HASH}",
        "pilot djia-synthetic-pilot v1",
        f"tests/fixtures/events/pilot-v1.json  {PILOT_HASH}",
        "at most 1 requests to SEC, through the shared client; 1 first choices",
    ]
    assert lines[5] == "  1  cik-0009990003:2026-03-31:release  parsed"
    assert lines[12] == (
        "  8  cik-0009990003:2025-06-30:release  unavailable, no_confirmed_release"
    )
    assert lines[-3:] == [
        "parsed 24, unavailable 2, failed 1",
        "fetched 0; requests sent: 1",
        lines[-1],
    ]
    assert lines[-1].startswith("data/runs/events/states/acquire-")
    again = run(repo, "acquire", store=EVENTS_STORE)
    assert again.exit_code == 0, again.output
    assert budgets == [1]
    assert acquire_lines(again)[4] == "nothing to fetch; the client stays closed"
    assert acquire_lines(again)[-2:] == [
        "parsed 24, unavailable 2, failed 1",
        "fetched 0; requests sent: 0",
    ]


def test_acquire_fetches_through_the_shared_client_within_its_count(
    repo, moved, monkeypatch
) -> None:
    """D5: every exhibit goes through the shared client, whose budget is the approved
    count; acquisition has no throttle of its own."""
    assert len(forget_exhibits(moved)) == 27
    budgets = client(monkeypatch, {**served(), **exhibit_bodies()})
    result = run(repo, "acquire", "--max-requests", "28", store=EVENTS_STORE)
    assert result.exit_code == 0, result.output
    assert budgets == [28]
    lines = acquire_lines(result)
    assert lines[4] == (
        "at most 28 requests to SEC, through the shared client; 27 first choices"
    )
    assert lines[-2] == "fetched 27; requests sent: 28"


def test_acquire_needs_the_approved_count_when_it_would_fetch(
    repo, moved, monkeypatch
) -> None:
    budgets = client(monkeypatch, served())
    result = run(repo, "acquire", store=EVENTS_STORE)
    assert result.exit_code == 1
    assert budgets == []
    assert result.stderr == (
        "Refused: pass --max-requests, the request count the user approved\n"
    )
    assert "requests sent" not in result.stdout


def test_acquire_stops_on_a_persistent_403_and_leaves_the_rest_expected(
    repo, moved, monkeypatch
) -> None:
    forget_exhibits(moved)
    client(monkeypatch, {**served(), **exhibit_bodies()}, status=403)
    result = run(repo, "acquire", "--max-requests", "28", store=EVENTS_STORE)
    assert result.exit_code == 1
    assert "Stopped: 403 persisted" in result.stderr
    assert "requests sent: 2; a rerun attempts what is left" in result.stdout
    (path,) = (repo / "data" / "runs" / "events" / "states").glob("*.parquet")
    states = {t.to_state for t in read_runs(path.parent)}
    assert states == {DocumentState.EXPECTED}


def test_acquire_records_a_redirected_exhibit_within_the_stated_count(
    repo, moved, monkeypatch
) -> None:
    """The one exhibit to fetch is redirected. The client refuses it before
    following, within the count the run stated and the user approved, so its
    attempt is recorded rather than stalling every rerun (plan 8's final review)."""
    budgets = client(monkeypatch, served(), moved=MISSING)
    result = run(repo, "acquire", "--max-requests", "1", store=EVENTS_STORE)
    assert result.exit_code == 0, result.output
    assert budgets == [1]
    lines = acquire_lines(result)
    assert lines[4] == (
        "at most 1 requests to SEC, through the shared client; 1 first choices"
    )
    assert lines[-2] == "fetched 0; requests sent: 1"
    pilot_hash = PilotManifest.model_validate_json(
        (repo / FIXTURE_DIR / "pilot-v1.json").read_text(encoding="utf-8")
    ).definition.content_hash
    (path,) = (repo / "data" / "runs" / "events" / "states").glob("*.parquet")
    missing = [
        t
        for t in read_runs(path.parent)
        if t.pilot_hash == pilot_hash and any(a.filename == MISSING for a in t.attempts)
    ]
    (attempt,) = [a for a in missing[-1].attempts if a.filename == MISSING]
    assert "was redirected to" in attempt.detail


def test_acquire_s_cap_is_the_approved_count(repo, moved, monkeypatch) -> None:
    """The approval is the client's cap: a retry counts against it, so a count above
    the stated one leaves room for retries (plan 8's final review)."""
    forget_exhibits(moved)
    budgets = client(monkeypatch, {**served(), **exhibit_bodies()})
    result = run(repo, "acquire", "--max-requests", "56", store=EVENTS_STORE)
    assert result.exit_code == 0, result.output
    assert budgets == [56]


@pytest.mark.parametrize(
    "filename",
    [
        pytest.param("acquire-x.parquet", id="plain"),
        pytest.param("acquire-diagnostic-sentinel.parquet", id="diagnostic-sentinel"),
    ],
)
def test_acquire_refuses_a_run_file_it_cannot_read(
    repo, moved, monkeypatch, filename
) -> None:
    """Malformed state bytes refuse with a closed reason before a client opens."""
    budgets = client(monkeypatch, served())
    states = repo / "data" / "runs" / "events" / "states"
    states.mkdir(parents=True)
    (states / filename).write_bytes(b"not parquet")
    result = run(repo, "acquire", "--max-requests", "1", store=EVENTS_STORE)
    assert result.exit_code == 1
    assert budgets == []
    assert result.stderr == "Refused: state_storage_corrupt\n"


def test_acquire_refuses_while_another_run_holds_its_runs(
    repo, moved, monkeypatch
) -> None:
    """Two runs never record at once, offline ones included (plan 8's final
    review)."""
    budgets = client(monkeypatch, served())
    runs = repo / "data" / "runs" / "events"
    with ProcessLock(runs / events_cli.ACQUIRE_LOCK):
        result = run(repo, "acquire", "--max-requests", "1", store=EVENTS_STORE)
    assert result.exit_code == 1
    assert budgets == []
    assert result.stderr.startswith("Refused: another client holds")
    assert not (runs / "states").exists()


def unforeseen(*args, **kwargs):
    """An error no stop names, as httpx raises one."""
    raise LookupError("unforeseen")


def test_discover_prints_its_count_on_an_unforeseen_error(repo, monkeypatch) -> None:
    """The count ends every exit, not only a stop or a Ctrl-C (plan 8's final
    review)."""
    client(monkeypatch, served())
    monkeypatch.setattr(ArtifactStore, "put", unforeseen)
    result = run(repo, "discover", "--max-requests", "90", store=EVENTS_STORE)
    assert isinstance(result.exception, LookupError)
    assert result.stdout.splitlines()[-1] == (
        "requests sent: 1; a rerun fetches only what is missing"
    )


def test_acquire_prints_its_count_on_an_unforeseen_error(
    repo, moved, monkeypatch
) -> None:
    forget_exhibits(moved)
    client(monkeypatch, {**served(), **exhibit_bodies()})
    monkeypatch.setattr(ArtifactStore, "put", unforeseen)
    result = run(repo, "acquire", "--max-requests", "28", store=EVENTS_STORE)
    assert isinstance(result.exception, LookupError)
    assert result.stdout.splitlines()[-1] == (
        "requests sent: 1; a rerun attempts what is left"
    )


def test_acquire_refuses_without_a_pilot_over_the_current_manifest(
    repo, moved, monkeypatch
) -> None:
    budgets = client(monkeypatch, served())
    (repo / FIXTURE_DIR / "pilot-v1.json").unlink()
    result = run(repo, "acquire", "--max-requests", "1", store=EVENTS_STORE)
    assert result.exit_code == 1
    assert budgets == []
    assert "Refused: no pilot is frozen over events-v1.json: run events select" in (
        result.stderr
    )


def test_acquire_refuses_a_pilot_djia_pilot_1_does_not_reselect(
    repo, moved, monkeypatch
) -> None:
    """F10: a hand-edited pilot whose hash is recomputed is refused at the gate."""
    budgets = client(monkeypatch, served())
    path = repo / FIXTURE_DIR / "pilot-v1.json"
    pilot = PilotManifest.model_validate_json(path.read_bytes())
    one, two, *rest = pilot.rows
    rows = (
        one.model_copy(update={"event_id": two.event_id}),
        two.model_copy(update={"event_id": one.event_id}),
        *rest,
    )
    swapped = pilot.model_copy(update={"rows": rows})
    hashed = swapped.definition.model_copy(
        update={"content_hash": pilot_content_hash(swapped)}
    )
    path.write_bytes(serialize(swapped.model_copy(update={"definition": hashed})))
    result = run(repo, "acquire", "--max-requests", "1", store=EVENTS_STORE)
    assert result.exit_code == 1
    assert budgets == []
    assert "djia-pilot/1 over events-v1.json selects" in result.stderr


@pytest.mark.parametrize(
    ("option", "value", "refusal"),
    [
        ("--store", "tests/fixtures/events/raw", "does not resolve under data/raw"),
        ("--runs-dir", "tests/fixtures/runs", "does not resolve under data/runs"),
    ],
)
def test_acquire_refuses_a_path_git_would_keep(
    repo, moved, monkeypatch, option, value, refusal
) -> None:
    budgets = client(monkeypatch, served())
    args = ["acquire", "--max-requests", "1"]
    if option == "--runs-dir":
        args += [option, value]
        result = run(repo, *args, store=EVENTS_STORE)
    else:
        result = run(repo, *args, store=Path(value))
    assert result.exit_code == 1
    assert budgets == []
    assert refusal in result.stderr
