"""``earnings-pipeline events`` on the committed synthetic event corpus. ``discover``
runs the shared SEC client over a transport that serves the corpus's saved
responses, so no request leaves the process."""

import shutil
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import httpx
import pytest
from earnings_core import sha256_hex
from earnings_ingestion.cohort.locators import LocatorError
from earnings_ingestion.cohort.register import SEC_RIGHTS, SEC_SOURCE_ID
from earnings_ingestion.events.acquire import exhibit_remedy
from earnings_ingestion.events.filings import issuer_filings
from earnings_ingestion.events.fixture import COHORT_MANIFEST, FIXTURE_DIR
from earnings_ingestion.events.freeze import (
    LeftoverEvidence,
    load_event_manifest,
    serialize,
)
from earnings_ingestion.events.layer import (
    ACME,
    CORVID,
    CUTOFF,
    DYNAMO,
    EASTFIELD,
    OLDER_PAGES,
    REPORTS,
    RETRIEVED,
    START,
    exhibit_bodies,
    filings,
)
from earnings_ingestion.events.records import PilotManifest, pilot_content_hash
from earnings_ingestion.events.saved import SavedResponses, refetch_remedy
from earnings_ingestion.events.state_table import read_runs
from earnings_ingestion.events.states import DocumentState
from earnings_ingestion.events.synthetic import (
    SyntheticStore,
    eight_k,
    index_page,
    save,
    submissions_file,
)
from earnings_ingestion.fetch import store as store_module
from earnings_ingestion.fetch.client import ProcessLock
from earnings_ingestion.fetch.records import Retrieval
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec import client as sec_client
from earnings_ingestion.sec.urls import (
    archive_url,
    filing_index_url,
    submissions_page_url,
    submissions_url,
)
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
    2026-07-21, whose index page is saved, gets one that follows neither convention.
    Acme's 8-K of 2025-06-26 is written in true UTC, so Acme's file follows both
    conventions and establishes none. Acme's 10-Q of 2026-08-31 gets a value that
    falls on the cutoff in true UTC and on the next day in Eastern digits."""
    unknown, mismatch = "0009990005-26-000017", "0009990005-26-000018"
    utc, late = "0009990001-25-000010", "0009990001-26-000021"
    written = {
        unknown: "",
        mismatch: "2026-07-21T12:00:00.000Z",
        utc: "2025-06-26T20:05:00.000Z",
        late: "2026-09-23T01:30:00.000Z",
    }
    store = ArtifactStore(repo / FIXTURE_DIR / "raw", repo)
    later = RETRIEVED + timedelta(days=1)
    for registrant in (DYNAMO, ACME):
        listed = [
            replace(filing, written=written.get(filing.accession))
            for filing, _ in filings(registrant)
        ]
        body = submissions_file(
            registrant.cik, registrant.name, listed, convention=registrant.convention
        )
        save(store, submissions_url(registrant.cik), body, "application/json", later)
    acme = issuer_filings(
        SavedResponses(store), ACME.cik, "cik-0009990001", start=START, cutoff=CUTOFF
    )
    (file,) = acme.files
    assert late in [filing.accession for filing in file.filings]
    assert file.survey.convention is None
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
        f"acceptance_time_unknown:{late}: run events discover --filing"
        f" {ACME.cik} {late}"
    ) in lines
    assert (
        f"acceptance_time_mismatch:{mismatch}: no override or discover run answers it"
    ) in lines


def test_an_emptied_10q_with_its_index_page_saved_still_freezes(repo) -> None:
    """Review Focus (plan 26, D2): a row with no acceptanceDateTime has nothing to
    cross-check. Dynamo's 10-Q of 2026-04-03 loses its value, and its index page is
    saved, so the page places it, and the build and the freeze reproduce v1."""
    emptied = "0009990005-26-000017"
    listed = [
        replace(filing, written="" if filing.accession == emptied else None)
        for filing, _ in filings(DYNAMO)
    ]
    (report,) = [filing for filing in listed if filing.accession == emptied]
    store = ArtifactStore(repo / FIXTURE_DIR / "raw", repo)
    later = RETRIEVED + timedelta(days=1)
    body = submissions_file(
        DYNAMO.cik, DYNAMO.name, listed, convention=DYNAMO.convention
    )
    save(store, submissions_url(DYNAMO.cik), body, "application/json", later)
    page = index_page(DYNAMO.cik, report)
    save(store, filing_index_url(DYNAMO.cik, emptied), page, "text/html", later)
    result = run(repo, "build")
    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines()[-1] == (
        f"32 events, 27 eligible, content {EVENTS_HASH}"
    )
    result = run(repo, "freeze")
    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines()[0] == "unchanged: djia-synthetic v1"


MISMATCH = "0009990005-26-000018"
REPEATED = (
    f"acceptance_time_mismatch:{MISMATCH}: 2 findings share this ID,"
    " under cik-0009990003, cik-0009990005"
)


def list_dynamo_8k_under_corvid(repo: Path, *, document: bool) -> None:
    """List Dynamo's 8-K of 2026-07-21 under Corvid too, written with an
    ``acceptanceDateTime`` that follows neither convention, so each issuer makes an
    ``acceptance_time_mismatch`` finding under one ID. Corvid's copy gets the index
    page. It gets a primary document too when ``document``, which Corvid's slot for
    2026-06-30 reads as a candidate."""
    (shared,) = [
        replace(filing, written="2026-07-21T12:00:00.000Z")
        for filing, _ in filings(DYNAMO)
        if filing.accession == MISMATCH
    ]
    store = ArtifactStore(repo / FIXTURE_DIR / "raw", repo)
    later = RETRIEVED + timedelta(days=1)
    for registrant in (DYNAMO, CORVID):
        listed = [
            filing for filing, _ in filings(registrant) if filing.accession != MISMATCH
        ]
        body = submissions_file(
            registrant.cik,
            registrant.name,
            [*listed, shared],
            convention=registrant.convention,
        )
        save(store, submissions_url(registrant.cik), body, "application/json", later)
    page = SavedResponses(store).get(filing_index_url(DYNAMO.cik, MISMATCH))
    index = filing_index_url(CORVID.cik, MISMATCH)
    save(store, index, page.text.body, "text/html", later)
    if document:
        released = ("Corvid Systems Inc announced its results.",)
        body = eight_k(CORVID.name, [("2.02", released)], signed=shared.filing_date)
        url = archive_url(CORVID.cik, MISMATCH, shared.primary_document)
        save(store, url, body, "text/html", later)


def test_build_refuses_a_finding_id_two_issuers_share(repo) -> None:
    """Corvid's copy of Dynamo's 8-K has no primary document saved, so the build also
    reports that. It reports the repeated ID, as a problem, and exits."""
    list_dynamo_8k_under_corvid(repo, document=False)
    result = run(repo, "build")
    assert result.exit_code == 1, result.output
    assert isinstance(result.exception, SystemExit), result.exception
    assert f"problem: {REPEATED}" in result.stderr.splitlines()


def test_build_prints_a_repeated_finding_id_as_a_problem_not_a_traceback(
    repo,
) -> None:
    """With nothing else missing, the repeated ID is the build's only problem. Before
    the check, ``EventManifest`` refused it after the build, with a pydantic error."""
    list_dynamo_8k_under_corvid(repo, document=True)
    result = run(repo, "build")
    assert result.exit_code == 1, result.output
    assert isinstance(result.exception, SystemExit), result.exception
    assert result.stderr.splitlines() == [f"problem: {REPEATED}"]


OVERRIDES_PROBLEM = "problem: tests/fixtures/events/overrides.toml: "
SECOND_OF_ONE_KIND = """
[[overrides]]
override_id = "keep-borealis-again"
kind = "retain_unresolved"
event_id = "cik-0009990002:2024-09-30"
reason = "same_day_transition"
rationale = "A second retain_unresolved override of one event."
reviewer = "Synthetic Reviewer"
recorded_on = 2026-09-28
"""


def named_lines(result, prefix: str) -> list[str]:
    """``result``'s stderr lines, each checked to start with ``prefix`` and to hold
    no line of a pydantic error's own text."""
    assert result.exit_code == 1, result.output
    assert isinstance(result.exception, SystemExit), result.exception
    lines = result.stderr.splitlines()
    assert lines
    assert all(line.startswith(prefix) for line in lines), lines
    assert not any("For further information" in line for line in lines), lines
    return lines


@pytest.mark.parametrize("command", ["build", "freeze"])
@pytest.mark.parametrize(
    ("edit", "said"),
    [
        (
            lambda text: text.replace(
                'override_id = "gap-corvid"', 'override_id = "gap-borealis"', 1
            ),
            "override_id repeated: ['gap-borealis']",
        ),
        (
            lambda text: text + SECOND_OF_ONE_KIND,
            (
                "event_id repeated in one kind:"
                " ['cik-0009990002:2024-09-30 (retain_unresolved)']"
            ),
        ),
        (
            lambda text: text.replace("schema_version = 1", "schema_version = ", 1),
            "(at line 2, column",
        ),
    ],
    ids=["repeated-override-id", "second-of-one-kind", "toml-syntax"],
)
def test_an_overrides_error_ends_with_a_problem_line(repo, command, edit, said) -> None:
    path = repo / FIXTURE_DIR / "overrides.toml"
    path.write_text(edit(path.read_text(encoding="utf-8")), encoding="utf-8")
    lines = named_lines(run(repo, command), OVERRIDES_PROBLEM)
    assert any(said in line for line in lines), lines


def test_an_overrides_error_of_two_entries_prints_a_problem_line_for_each(
    repo,
) -> None:
    """A validation error with two entries prints two lines, each with the path."""
    path = repo / FIXTURE_DIR / "overrides.toml"
    text = path.read_text(encoding="utf-8")
    for override_id in ("gap-borealis", "gap-corvid"):
        text = text.replace(
            f'override_id = "{override_id}"',
            f'override_id = "{override_id}"\nunexpected = 1',
            1,
        )
    path.write_text(text, encoding="utf-8")
    lines = named_lines(run(repo, "build"), OVERRIDES_PROBLEM)
    assert len(lines) == 2, lines


@pytest.mark.parametrize(
    ("named", "label"),
    [
        (FIXTURE_DIR / "overrides.toml", "problem:"),
        (UNIVERSES / "djia-synthetic-v1.json", "Refused:"),
    ],
    ids=["overrides", "universe"],
)
def test_a_file_that_cannot_be_read_is_named(repo, named, label) -> None:
    """A read error is an ``OSError``, not a ``ValueError``, and is named too."""
    path = repo / named
    path.unlink()
    path.mkdir()
    lines = named_lines(run(repo, "build"), f"{label} {named}: ")
    assert len(lines) == 1, lines
    assert "Is a directory" in lines[0], lines


def test_an_error_inside_the_build_is_never_named_as_the_overrides_file(
    repo, monkeypatch
) -> None:
    """Only the overrides file's load is wrapped: a ``LocatorError`` the build raises
    is a ``ValueError`` too, and no line blames the overrides file for it."""

    def uncited(*args, **kwargs):
        raise LocatorError("'Acme Industrial' is not in the walker-1 text")

    monkeypatch.setattr(events_cli, "build_events", uncited)
    result = run(repo, "build")
    assert isinstance(result.exception, LocatorError), result.exception
    assert "overrides.toml" not in result.stderr


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


def test_freeze_reports_a_citation_error_as_a_problem(repo, monkeypatch) -> None:
    """The evidence record cites a value the saved page's text does not hold."""

    def uncited(*args, **kwargs):
        raise LocatorError("'Acme Industrial' is not in the walker-1 text")

    monkeypatch.setattr(events_cli, "freeze_events", uncited)
    result = run(repo, "freeze")
    assert result.exit_code == 1, result.output
    assert isinstance(result.exception, SystemExit), result.exception
    assert result.stderr.splitlines() == [
        "problem: 'Acme Industrial' is not in the walker-1 text"
    ]


def test_freeze_reports_a_leftover_evidence_file_as_a_refusal(
    repo, monkeypatch
) -> None:
    corpus = repo / FIXTURE_DIR
    leftover = LeftoverEvidence(
        corpus / "events-v2.evidence.json", corpus / "events-v2.json"
    )

    def left(*args, **kwargs):
        raise leftover

    monkeypatch.setattr(events_cli, "freeze_events", left)
    result = run(repo, "freeze")
    assert result.exit_code == 1, result.output
    assert isinstance(result.exception, SystemExit), result.exception
    assert result.stderr.splitlines() == [f"Refused: {leftover}"]
    assert "delete it" in result.stderr


def test_freeze_refuses_a_write_that_fails(repo, monkeypatch) -> None:
    """A failed write is an ``OSError``, not a ``ValueError``, and is refused too."""

    def full(*args, **kwargs):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(events_cli, "freeze_events", full)
    result = run(repo, "freeze")
    assert result.exit_code == 1, result.output
    assert isinstance(result.exception, SystemExit), result.exception
    assert result.stderr.splitlines() == ["Refused: [Errno 28] No space left on device"]


def test_select_says_to_rerun_when_another_select_froze_first(
    repo, monkeypatch
) -> None:
    """Two selects raced, and the other wrote ``pilot-v2.json`` first."""
    pilot = repo / FIXTURE_DIR / "pilot-v2.json"

    def raced(*args, **kwargs):
        raise FileExistsError(f"{pilot} holds other bytes")

    monkeypatch.setattr(events_cli, "freeze_pilot", raced)
    result = run(repo, "select")
    assert result.exit_code == 1, result.output
    assert isinstance(result.exception, SystemExit), result.exception
    assert result.stderr.endswith("rerun events select\n")
    assert result.stderr == (
        f"Refused: {pilot} holds other bytes; another events select froze this pilot"
        " first: rerun events select\n"
    )


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
    requested: list[str] | None = None,
    statuses: dict[str, list[int]] | None = None,
):
    """Replace the CLI's client with the shared client over a serving transport,
    which redirects any URL ending in ``moved``, answers a URL in ``statuses`` with
    each of its statuses in turn and then with ``status``, as it answers any other,
    and appends each URL it is asked for to ``requested``."""
    budgets: list[int] = []
    pending = {url: list(codes) for url, codes in (statuses or {}).items()}

    def handle(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if requested is not None:
            requested.append(url)
        if moved is not None and url.endswith(moved):
            return httpx.Response(301, headers={"Location": f"{request.url}-moved"})
        body, media_type = responses.get(url, (b"", "text/plain"))
        code = status
        if pending.get(url):
            code = pending[url].pop(0)
        if url not in responses:
            code = 404
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
            " 'sec-edgar': its retrieval records remain, but its bytes are gone;"
            f" {refetch_remedy(url)}"
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


def test_discover_handles_a_vanished_companyfacts_artifact(
    repo, moved, monkeypatch
) -> None:
    """A companyfacts file whose body is gone, with its record kept, no longer stops
    the documents phase. Its issuer is skipped, and discover ends with its count and
    a problem line that names the file, never a traceback (item P2.3, F31)."""
    url = "https://data.sec.gov/api/xbrl/companyfacts/CIK0009990001.json"
    artifact = SavedResponses(ArtifactStore(moved, repo)).get(url).artifact
    (repo / artifact.storage_ref).unlink()
    client(monkeypatch, served())
    result = run(repo, "discover", "--max-requests", "5", store=EVENTS_STORE)
    assert result.exit_code == 1, result.output
    assert isinstance(result.exception, SystemExit), result.exception
    assert result.stdout.splitlines()[-1] == "fetched 0; requests sent: 0"
    assert result.stderr.splitlines() == [
        (
            f"problem: {url}: no artifact {artifact.content_sha256} for source"
            " 'sec-edgar': its retrieval records remain, but its bytes are gone;"
            f" {refetch_remedy(url)}"
        )
    ]


UNREADABLE = (
    "unreadable retrieval record; repair it by hand"
    ' (docs/verification/djia-events.md, "Repairing the store")'
)


def test_an_empty_retrieval_record_is_named(repo, moved, monkeypatch) -> None:
    """Build names the record and its manual repair. Discover stops on it with its
    count and gives no rerun advice, since a rerun meets the same record."""
    (record, *_) = sorted((moved / SEC_SOURCE_ID / "retrievals").glob("*/*.json"))
    record.write_bytes(b"")
    built = run(repo, "build", store=EVENTS_STORE)
    assert built.exit_code == 1, built.output
    assert isinstance(built.exception, SystemExit), built.exception
    assert built.stderr.splitlines() == [
        f"problem: {record.relative_to(repo)}: {UNREADABLE}"
    ]
    assert built.stderr.startswith("problem: data/raw/events/sec-edgar/retrievals/")
    client(monkeypatch, served())
    result = run(repo, "discover", "--max-requests", "5", store=EVENTS_STORE)
    assert result.exit_code == 1, result.output
    assert isinstance(result.exception, SystemExit), result.exception
    assert result.stdout.splitlines()[-1] == "requests sent: 0"
    assert result.stderr.splitlines() == [f"Stopped: {record}: {UNREADABLE}"]
    output = result.stdout + result.stderr
    assert "a rerun fetches only what is missing" not in output


def tamper_universe(repo: Path, change: Callable[[str], str]) -> str:
    """Apply ``change`` to the copy's universe manifest; return the refusal's
    prefix, which names the manifest's path."""
    path = repo / UNIVERSES / "djia-synthetic-v1.json"
    path.write_text(change(path.read_text(encoding="utf-8")), encoding="utf-8")
    return f"Refused: {path.relative_to(repo)}: "


def test_build_refuses_a_tampered_universe_manifest(repo, monkeypatch) -> None:
    """One fact changed, so the manifest no longer hashes to its content_hash. Build
    and discover refuse it, discover before any client opens."""
    prefix = tamper_universe(
        repo,
        lambda text: text.replace(
            '"announcement_date": "2024-10-31"', '"announcement_date": "2024-10-30"', 1
        ),
    )
    built = run(repo, "build")
    assert built.exit_code == 1, built.output
    assert isinstance(built.exception, SystemExit), built.exception
    assert built.stderr.startswith(prefix)
    assert "does not hash to its content_hash" in built.stderr
    budgets = client(monkeypatch, served())
    result = run(repo, "discover", "--max-requests", "5", store=EVENTS_STORE)
    assert result.exit_code == 1, result.output
    assert isinstance(result.exception, SystemExit), result.exception
    assert result.stderr.startswith(prefix)
    assert budgets == []


def test_a_universe_manifest_that_does_not_validate_is_refused_line_by_line(
    repo,
) -> None:
    """Each entry of its validation error is one line, and each names the path."""
    prefix = tamper_universe(repo, lambda text: "{}")
    lines = named_lines(run(repo, "build"), prefix)
    assert len(lines) > 1, lines


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


INDEX = (
    "https://www.sec.gov/Archives/edgar/data/9990001/000999000125000008/"
    "0009990001-25-000008-index.htm"
)
"""Acme's index page, which an override of the corpus cites."""
EASTFIELD_MAIN = submissions_url(EASTFIELD.cik)
EASTFIELD_PAGE = submissions_page_url(OLDER_PAGES[EASTFIELD][0][0])
"""Eastfield's one saved older page, which a refetch of its main file brings."""
UNSAVED_PAGE = submissions_page_url("CIK0009990006-submissions-002.json")
"""Eastfield's older page whose dates miss the range, which discovery never saves."""
REFETCH = "refetch: {} requests to SEC, through the shared client"
RERUN = "requests sent: {}; a rerun may name only the URLs that are still unusable"
"""A stopped refetch's count. A rerun that names a URL it saved is refused, since that
URL now reads; discover's own tail, that a rerun fetches only what is missing, would
mislead."""


def truncate(repo: Path, url: str) -> str:
    """Cut ``url``'s saved artifact to its first 10 bytes; return the line a refetch
    of its earlier bytes prints when it moves the cut bytes aside."""
    saved = SavedResponses(ArtifactStore(repo / EVENTS_STORE, repo)).get(url)
    sha = saved.artifact.content_sha256
    path = repo / saved.artifact.storage_ref
    cut = path.read_bytes()[:10]
    path.write_bytes(cut)
    moved = EVENTS_STORE / SEC_SOURCE_ID / "quarantine" / sha
    return f"quarantined: {moved / f'{sha256_hex(cut)}{path.suffix}'}"


def changed(url: str) -> str:
    return (
        f"changed: {url} returned other bytes than its earlier retrieval; run events"
        " build and compare its content hash with the frozen version's before"
        " relying on it"
    )


def other_bytes(url: str) -> dict[str, tuple[bytes, str]]:
    """``url`` served with other valid bytes than any it was saved with."""
    body, media_type = served()[url]
    return {url: (body + b"\n", media_type)}


def test_refetch_mends_a_truncated_index_page_and_rebuilds_the_frozen_hash(
    repo, moved, monkeypatch
) -> None:
    quarantined = truncate(repo, INDEX)
    built = run(repo, "build", store=EVENTS_STORE)
    assert built.exit_code == 1
    problems = [
        line for line in built.stderr.splitlines() if line.startswith("problem: ")
    ]
    assert problems
    assert all(line.endswith(refetch_remedy(INDEX)) for line in problems)
    requested: list[str] = []
    budgets = client(monkeypatch, served(), requested=requested)
    result = run(repo, "discover", "--refetch", INDEX, store=EVENTS_STORE)
    assert result.exit_code == 1
    assert result.stdout.splitlines() == [REFETCH.format(1), f"  {INDEX}"]
    assert budgets == []
    assert result.stderr == (
        "Refused: pass --max-requests, the request count the user approved\n"
    )
    result = run(
        repo, "discover", "--refetch", INDEX, "--max-requests", "1", store=EVENTS_STORE
    )
    assert result.exit_code == 0, result.output
    assert budgets == [1]
    assert requested == [INDEX]
    assert result.stdout.splitlines() == [
        REFETCH.format(1),
        f"  {INDEX}",
        "refetched 1; requests sent: 1",
        quarantined,
    ]
    assert quarantined.startswith("quarantined: data/raw/events/sec-edgar/quarantine/")
    rebuilt = run(repo, "build", store=EVENTS_STORE)
    assert rebuilt.exit_code == 0, rebuilt.output
    frozen = load_event_manifest(REPO / FIXTURE_DIR / "events-v1.json")
    assert rebuilt.stdout.splitlines()[-1] == (
        f"32 events, 27 eligible, content {frozen.definition.content_hash}"
    )


def test_refetch_adds_a_submissions_files_older_pages_to_its_stated_count(
    repo, moved, monkeypatch
) -> None:
    truncate(repo, EASTFIELD_MAIN)
    budgets = client(monkeypatch, served())
    result = run(
        repo,
        "discover",
        "--refetch",
        EASTFIELD_MAIN,
        "--max-requests",
        "1",
        store=EVENTS_STORE,
    )
    assert result.exit_code == 1
    assert result.stdout.splitlines() == [
        REFETCH.format(2),
        f"  {EASTFIELD_MAIN}",
        f"  {EASTFIELD_PAGE}",
    ]
    assert budgets == []
    assert result.stderr == (
        "Refused: --max-requests 1 is below the 2 requests to refetch\n"
    )


def saved_exhibit(repo: Path) -> str:
    """A saved exhibit, its bytes cut: only events acquire refetches it (EV2)."""
    saved = SavedResponses(ArtifactStore(repo / EVENTS_STORE, repo))
    url = next(url for url in sorted(exhibit_bodies()) if url in saved)
    truncate(repo, url)
    return url


@pytest.mark.parametrize(
    ("named", "refusal"),
    [
        pytest.param(
            lambda repo: submissions_url("0009990001"),
            "is not among the responses discovery cannot use",
            id="usable",
        ),
        pytest.param(lambda repo: UNSAVED_PAGE, "nothing saved from ", id="unsaved"),
        pytest.param(saved_exhibit, "events acquire --refetch", id="exhibit"),
    ],
)
def test_refetch_refuses_what_is_not_unusable(
    repo, moved, monkeypatch, named, refusal
) -> None:
    """Each is refused before the count is stated, so before --max-requests is
    asked for, and before any client opens."""
    url = named(repo)
    budgets = client(monkeypatch, served())
    result = run(repo, "discover", "--refetch", url, store=EVENTS_STORE)
    assert result.exit_code == 1
    assert budgets == []
    assert result.stdout == ""
    assert result.stderr.startswith("Refused: ")
    assert url in result.stderr and refusal in result.stderr


def test_refetch_refuses_filing_beside_it(repo, moved, monkeypatch) -> None:
    """Refused first, before the named URL, which reads, is refused itself."""
    budgets = client(monkeypatch, served())
    result = run(
        repo,
        "discover",
        "--refetch",
        submissions_url("0009990001"),
        "--filing",
        *FILED,
        store=EVENTS_STORE,
    )
    assert result.exit_code == 1
    assert budgets == []
    assert result.stdout == ""
    assert result.stderr == "Refused: pass --refetch or --filing, not both\n"


def test_refetch_stops_on_a_persistent_403_and_prints_its_count(
    repo, moved, monkeypatch
) -> None:
    """The approved count is the cap, above the stated count: the retry of a 403
    counts against it."""
    truncate(repo, INDEX)
    requested: list[str] = []
    budgets = client(monkeypatch, served(), status=403, requested=requested)
    result = run(
        repo, "discover", "--refetch", INDEX, "--max-requests", "2", store=EVENTS_STORE
    )
    assert result.exit_code == 1
    assert budgets == [2]
    assert requested == [INDEX, INDEX]
    assert result.stdout.splitlines() == [
        REFETCH.format(1),
        f"  {INDEX}",
        RERUN.format(2),
    ]
    assert result.stderr == (
        f"Stopped: 403 persisted for {INDEX}; stopping without changing identity\n"
    )
    assert not (moved / SEC_SOURCE_ID / "quarantine").exists()


def test_refetch_reports_other_bytes(repo, moved, monkeypatch) -> None:
    """Other bytes are a new artifact: nothing is moved, and the build may read
    other bytes than it froze."""
    truncate(repo, INDEX)
    budgets = client(monkeypatch, {**served(), **other_bytes(INDEX)})
    result = run(
        repo, "discover", "--refetch", INDEX, "--max-requests", "1", store=EVENTS_STORE
    )
    assert result.exit_code == 0, result.output
    assert budgets == [1]
    assert result.stdout.splitlines() == [
        REFETCH.format(1),
        f"  {INDEX}",
        "refetched 1; requests sent: 1",
        changed(INDEX),
    ]


def test_refetch_prints_each_url_that_returned_other_bytes(
    repo, moved, monkeypatch
) -> None:
    """Eastfield's main file and the older page it brings both come back other:
    one changed line for each, in the plan's order."""
    truncate(repo, EASTFIELD_MAIN)
    responses = {
        **served(),
        **other_bytes(EASTFIELD_MAIN),
        **other_bytes(EASTFIELD_PAGE),
    }
    budgets = client(monkeypatch, responses)
    result = run(
        repo,
        "discover",
        "--refetch",
        EASTFIELD_MAIN,
        "--max-requests",
        "2",
        store=EVENTS_STORE,
    )
    assert result.exit_code == 0, result.output
    assert budgets == [2]
    assert result.stdout.splitlines() == [
        REFETCH.format(2),
        f"  {EASTFIELD_MAIN}",
        f"  {EASTFIELD_PAGE}",
        "refetched 2; requests sent: 2",
        changed(EASTFIELD_MAIN),
        changed(EASTFIELD_PAGE),
    ]


def test_refetch_prints_each_move_and_then_each_change(
    repo, moved, monkeypatch
) -> None:
    """Eastfield's main file and its older page come back as they were saved, so
    each cut file is moved aside; Acme's index page comes back other."""
    moves = [truncate(repo, url) for url in (EASTFIELD_MAIN, EASTFIELD_PAGE, INDEX)]
    budgets = client(monkeypatch, {**served(), **other_bytes(INDEX)})
    result = run(
        repo,
        "discover",
        "--refetch",
        EASTFIELD_MAIN,
        "--refetch",
        INDEX,
        "--max-requests",
        "3",
        store=EVENTS_STORE,
    )
    assert result.exit_code == 0, result.output
    assert budgets == [3]
    assert result.stdout.splitlines() == [
        REFETCH.format(3),
        f"  {EASTFIELD_MAIN}",
        f"  {EASTFIELD_PAGE}",
        f"  {INDEX}",
        "refetched 3; requests sent: 3",
        *moves[:2],
        changed(INDEX),
    ]


def test_refetch_fails_on_what_it_did_not_mend(repo, moved, monkeypatch) -> None:
    """Eastfield's main file is cut too, but not named: the read-back after the
    refetch still names it."""
    truncate(repo, EASTFIELD_MAIN)
    quarantined = truncate(repo, INDEX)
    client(monkeypatch, served())
    result = run(
        repo, "discover", "--refetch", INDEX, "--max-requests", "1", store=EVENTS_STORE
    )
    assert result.exit_code == 1
    assert result.stdout.splitlines()[-2:] == [
        "refetched 1; requests sent: 1",
        quarantined,
    ]
    (problem,) = result.stderr.splitlines()
    assert problem.startswith(f"problem: {EASTFIELD_MAIN}: ")
    assert problem.endswith(
        f" no longer hashes to its name; {refetch_remedy(EASTFIELD_MAIN)}"
    )


@pytest.mark.parametrize("returned", ["other bytes", "the same bytes"])
def test_refetch_stopped_partway_prints_what_it_saved(
    repo, moved, monkeypatch, returned
) -> None:
    """Eastfield's main file is saved before its older page meets a persistent 403.
    What the save changed, or moved aside, is printed before the stop, since a
    rerun cannot tell it: the saved file then reads, and is refused as usable."""
    quarantined = truncate(repo, EASTFIELD_MAIN)
    responses = served()
    if returned == "other bytes":
        responses |= other_bytes(EASTFIELD_MAIN)
        saved = changed(EASTFIELD_MAIN)
    else:
        saved = quarantined
    requested: list[str] = []
    budgets = client(
        monkeypatch,
        responses,
        requested=requested,
        statuses={EASTFIELD_PAGE: [403, 403]},
    )
    result = run(
        repo,
        "discover",
        "--refetch",
        EASTFIELD_MAIN,
        "--max-requests",
        "3",
        store=EVENTS_STORE,
    )
    assert result.exit_code == 1
    assert budgets == [3]
    assert requested == [EASTFIELD_MAIN, EASTFIELD_PAGE, EASTFIELD_PAGE]
    stopped = (
        f"Stopped: 403 persisted for {EASTFIELD_PAGE}; stopping without changing"
        " identity"
    )
    assert result.stdout.splitlines() == [
        REFETCH.format(2),
        f"  {EASTFIELD_MAIN}",
        f"  {EASTFIELD_PAGE}",
        saved,
        RERUN.format(3),
    ]
    assert result.stderr == f"{stopped}\n"
    assert result.output.splitlines()[-3:] == [saved, RERUN.format(3), stopped]


def test_refetch_stopped_at_its_first_url_prints_nothing_saved(
    repo, moved, monkeypatch
) -> None:
    truncate(repo, EASTFIELD_MAIN)
    requested: list[str] = []
    budgets = client(
        monkeypatch,
        served(),
        requested=requested,
        statuses={EASTFIELD_MAIN: [403, 403]},
    )
    result = run(
        repo,
        "discover",
        "--refetch",
        EASTFIELD_MAIN,
        "--max-requests",
        "3",
        store=EVENTS_STORE,
    )
    assert result.exit_code == 1
    assert budgets == [3]
    assert requested == [EASTFIELD_MAIN, EASTFIELD_MAIN]
    assert result.stdout.splitlines() == [
        REFETCH.format(2),
        f"  {EASTFIELD_MAIN}",
        f"  {EASTFIELD_PAGE}",
        RERUN.format(2),
    ]
    assert result.stderr == (
        f"Stopped: 403 persisted for {EASTFIELD_MAIN}; stopping without changing"
        " identity\n"
    )


def test_refetch_prints_its_count_on_an_unforeseen_error(
    repo, moved, monkeypatch
) -> None:
    truncate(repo, INDEX)
    client(monkeypatch, served())
    monkeypatch.setattr(ArtifactStore, "put", unforeseen)
    result = run(
        repo, "discover", "--refetch", INDEX, "--max-requests", "1", store=EVENTS_STORE
    )
    assert isinstance(result.exception, LookupError)
    assert result.stdout.splitlines()[-1] == RERUN.format(1)


def test_refetch_names_every_url_it_refuses(repo, moved, monkeypatch) -> None:
    usable = submissions_url("0009990001")
    budgets = client(monkeypatch, served())
    result = run(
        repo,
        "discover",
        "--refetch",
        usable,
        "--refetch",
        UNSAVED_PAGE,
        "--max-requests",
        "5",
        store=EVENTS_STORE,
    )
    assert result.exit_code == 1
    assert budgets == []
    assert result.stdout == ""
    first, second = result.stderr.splitlines()
    assert first.startswith(f"Refused: {usable} is not among the responses")
    assert second.startswith(f"nothing saved from {UNSAVED_PAGE}: ")


def test_refetch_counts_a_retry_against_its_cap(repo, moved, monkeypatch) -> None:
    """One 403, then the page: the retry fits the approved cap, above the stated
    count, and the count sent is not the count refetched."""
    quarantined = truncate(repo, INDEX)
    requested: list[str] = []
    budgets = client(
        monkeypatch, served(), requested=requested, statuses={INDEX: [403]}
    )
    result = run(
        repo, "discover", "--refetch", INDEX, "--max-requests", "2", store=EVENTS_STORE
    )
    assert result.exit_code == 0, result.output
    assert budgets == [2]
    assert requested == [INDEX, INDEX]
    assert result.stdout.splitlines() == [
        REFETCH.format(1),
        f"  {INDEX}",
        "refetched 1; requests sent: 2",
        quarantined,
    ]


def test_refetch_stopped_partway_prints_each_move_and_then_each_change(
    repo, moved, monkeypatch
) -> None:
    """Eastfield's main file comes back as it was saved, so its cut file is moved
    aside, and its older page comes back other; Acme's index page then meets a
    persistent 403."""
    quarantined = truncate(repo, EASTFIELD_MAIN)
    truncate(repo, INDEX)
    budgets = client(
        monkeypatch,
        {**served(), **other_bytes(EASTFIELD_PAGE)},
        statuses={INDEX: [403, 403]},
    )
    result = run(
        repo,
        "discover",
        "--refetch",
        EASTFIELD_MAIN,
        "--refetch",
        INDEX,
        "--max-requests",
        "4",
        store=EVENTS_STORE,
    )
    assert result.exit_code == 1
    assert budgets == [4]
    assert result.stdout.splitlines()[4:] == [
        quarantined,
        changed(EASTFIELD_PAGE),
        RERUN.format(4),
    ]
    assert result.stderr.startswith(f"Stopped: 403 persisted for {INDEX}; ")


def full_disk(*args, **kwargs):
    raise OSError(28, "No space left on device")


def ctrl_c(*args, **kwargs):
    raise KeyboardInterrupt


def test_refetch_prints_its_count_when_saving_fails(repo, moved, monkeypatch) -> None:
    """A stop that is not a 403 is stopped as discover stops it, with its count."""
    truncate(repo, INDEX)
    client(monkeypatch, served())
    monkeypatch.setattr(ArtifactStore, "put", full_disk)
    result = run(
        repo, "discover", "--refetch", INDEX, "--max-requests", "1", store=EVENTS_STORE
    )
    assert result.exit_code == 1
    assert result.stdout.splitlines()[-1] == RERUN.format(1)
    assert result.stderr == "Stopped: [Errno 28] No space left on device\n"


def test_refetch_prints_its_count_on_ctrl_c(repo, moved, monkeypatch) -> None:
    truncate(repo, INDEX)
    client(monkeypatch, served())
    monkeypatch.setattr(ArtifactStore, "put", ctrl_c)
    result = run(
        repo, "discover", "--refetch", INDEX, "--max-requests", "1", store=EVENTS_STORE
    )
    assert result.exit_code == 130
    assert result.stdout.splitlines()[-1] == RERUN.format(1)


STOP_TAIL = "requests sent: {}; a rerun attempts what is left"
REFETCH_STOP_TAIL = (
    f"{STOP_TAIL}, and --refetch may name only the exhibits that are still unusable"
)
"""A stopped acquire's count with --refetch. A rerun that names an exhibit the run
saved is refused, since that exhibit now reads."""
STOPPED = "Stopped: 403 persisted for {}; stopping without changing identity\n"


def pilot_exhibit(position: int = 0) -> str:
    """The one exhibit of the release filing of the pilot's event at ``position``,
    found as the acquire tests find it. A run reaches the first pilot row's first, so
    a later candidate behind a confirmed exhibit never hides it."""
    pilot = PilotManifest.model_validate_json(
        (REPO / FIXTURE_DIR / "pilot-v1.json").read_bytes()
    )
    events = load_event_manifest(REPO / FIXTURE_DIR / "events-v1.json")
    event_id = pilot.rows[position].event_id
    row = next(row for row in events.rows if row.event_id == event_id)
    folder = row.release_accession.replace("-", "")
    return next(url for url in exhibit_bodies() if f"/{folder}/" in url)


def test_acquire_refetch_states_its_count_first_and_fetches_the_exhibit(
    repo, moved, monkeypatch
) -> None:
    url = pilot_exhibit()
    quarantined = truncate(repo, url)
    requested: list[str] = []
    budgets = client(monkeypatch, {**served(), **exhibit_bodies()}, requested=requested)
    result = run(repo, "acquire", "--refetch", url, store=EVENTS_STORE)
    assert result.exit_code == 1
    lines = acquire_lines(result)
    assert lines[4].startswith("at most 2 requests to SEC, through the shared client;")
    assert lines[5:] == [f"refetch: {url}"]
    assert result.stderr == (
        "Refused: pass --max-requests, the request count the user approved\n"
    )
    assert budgets == []
    result = run(
        repo, "acquire", "--refetch", url, "--max-requests", "2", store=EVENTS_STORE
    )
    assert result.exit_code == 0, result.output
    assert budgets == [2]
    assert requested.count(url) == 1
    lines = acquire_lines(result)
    assert lines[4:6] == [
        "at most 2 requests to SEC, through the shared client; 2 first choices",
        f"refetch: {url}",
    ]
    assert lines[6] == "  1  cik-0009990003:2026-03-31:release  parsed"
    assert lines[-3] == "fetched 1; requests sent: 2"
    assert lines[-2].startswith("data/runs/events/states/acquire-")
    assert lines[-1] == quarantined


def test_acquire_without_a_refetch_names_the_remedy_and_fetches_nothing_for_it(
    repo, moved, monkeypatch
) -> None:
    url = pilot_exhibit()
    truncate(repo, url)
    requested: list[str] = []
    budgets = client(monkeypatch, {**served(), **exhibit_bodies()}, requested=requested)
    result = run(repo, "acquire", "--max-requests", "1", store=EVENTS_STORE)
    assert result.exit_code == 1
    assert budgets == [1]
    lines = acquire_lines(result)
    assert lines[4] == (
        "at most 1 requests to SEC, through the shared client; 1 first choices"
    )
    assert not any(line.startswith(("refetch:", "quarantined:")) for line in lines)
    (problem,) = result.stderr.splitlines()
    assert problem.startswith(f"problem: {url}: ")
    assert problem.endswith(exhibit_remedy(url))
    assert url not in requested


def unsaved_exhibit(moved: Path) -> str:
    """The first pilot row's exhibit, with every saved exhibit forgotten."""
    forget_exhibits(moved)
    return pilot_exhibit()


@pytest.mark.parametrize(
    ("named", "refusal"),
    [
        pytest.param(
            lambda moved: pilot_exhibit(),
            " is not a saved exhibit that a run would try and cannot read",
            id="usable",
        ),
        pytest.param(unsaved_exhibit, "nothing saved from ", id="unsaved"),
        pytest.param(
            lambda moved: INDEX,
            "refetched by earnings-pipeline events discover --refetch",
            id="index",
        ),
    ],
)
def test_acquire_refetch_refuses_a_usable_exhibit_before_the_client_opens(
    repo, moved, monkeypatch, named, refusal
) -> None:
    """Each is refused before the count is stated, and before any client opens."""
    url = named(moved)
    budgets = client(monkeypatch, {**served(), **exhibit_bodies()})
    result = run(
        repo, "acquire", "--refetch", url, "--max-requests", "5", store=EVENTS_STORE
    )
    assert result.exit_code == 1
    assert budgets == []
    assert not any(
        line.startswith(("at most", "refetch:")) for line in acquire_lines(result)
    )
    assert result.stderr.startswith("Refused: ")
    assert url in result.stderr and refusal in result.stderr


@pytest.mark.parametrize("refetching", [True, False], ids=["refetch", "plain"])
def test_acquire_stopped_says_what_a_rerun_may_name(
    repo, moved, monkeypatch, refetching
) -> None:
    """The first pilot row's exhibit meets a persistent 403: cut and named by
    --refetch, or not saved. With --refetch, a rerun that names it again once it
    reads is refused, so the tail says so; without, the tail is acquire's own."""
    url = pilot_exhibit()
    if refetching:
        truncate(repo, url)
        named, tail = ["--refetch", url], REFETCH_STOP_TAIL
    else:
        forget_exhibits(moved)
        named, tail = [], STOP_TAIL
    requested: list[str] = []
    budgets = client(
        monkeypatch,
        {**served(), **exhibit_bodies()},
        status=403,
        requested=requested,
    )
    result = run(repo, "acquire", *named, "--max-requests", "2", store=EVENTS_STORE)
    assert result.exit_code == 1
    assert budgets == [2]
    assert requested == [url, url]
    assert acquire_lines(result)[-1] == tail.format(2)
    assert result.stderr == STOPPED.format(url)


def test_acquire_refetch_keeps_acquire_s_tail_on_an_unforeseen_error(
    repo, moved, monkeypatch
) -> None:
    """Only a stop names what --refetch may name; any other error keeps acquire's
    own tail."""
    url = pilot_exhibit()
    truncate(repo, url)
    client(monkeypatch, {**served(), **exhibit_bodies()})
    monkeypatch.setattr(ArtifactStore, "put", unforeseen)
    result = run(
        repo, "acquire", "--refetch", url, "--max-requests", "2", store=EVENTS_STORE
    )
    assert isinstance(result.exception, LookupError)
    assert acquire_lines(result)[-1] == STOP_TAIL.format(1)


def test_acquire_prints_each_quarantined_file_once(repo, moved, monkeypatch) -> None:
    """The same damage twice in one run. The first and second pilot rows' exhibits
    are cut and refetched, and the second is served with the first's bytes. The
    first's file is cut again, to the same bytes, before each save, so both saves
    move the same bytes to the same place."""
    first, second = pilot_exhibit(0), pilot_exhibit(1)
    found = SavedResponses(ArtifactStore(moved, repo)).get(first)
    sha, path = found.artifact.content_sha256, repo / found.artifact.storage_ref
    quarantined = truncate(repo, first)
    cut = path.read_bytes()
    truncate(repo, second)
    responses = {**served(), **exhibit_bodies()}
    responses[second] = responses[first]
    client(monkeypatch, responses)
    put = ArtifactStore.put

    def cut_again(self, source_id, body, *args, **kwargs):
        if sha256_hex(body) == sha:
            path.write_bytes(cut)
        return put(self, source_id, body, *args, **kwargs)

    monkeypatch.setattr(ArtifactStore, "put", cut_again)
    result = run(
        repo,
        "acquire",
        "--refetch",
        first,
        "--refetch",
        second,
        "--max-requests",
        "3",
        store=EVENTS_STORE,
    )
    moves = [line for line in acquire_lines(result) if line.startswith("quarantined:")]
    assert moves == [quarantined]


def test_acquire_refetch_names_each_exhibit_once_in_the_order_given(
    repo, moved, monkeypatch
) -> None:
    """The first three pilot rows' exhibits, named out of the order a run reaches
    them and out of sorted order, one twice: one refetch line for each, in the order
    named, and each move after the run, in the order the run made it."""
    first, second, third = (pilot_exhibit(position) for position in range(3))
    moves = [truncate(repo, url) for url in (first, second, third)]
    budgets = client(monkeypatch, {**served(), **exhibit_bodies()})
    named = [
        arg for url in (second, third, first, second) for arg in ("--refetch", url)
    ]
    result = run(repo, "acquire", *named, "--max-requests", "4", store=EVENTS_STORE)
    assert result.exit_code == 0, result.output
    assert budgets == [4]
    lines = acquire_lines(result)
    assert lines[4:8] == [
        "at most 4 requests to SEC, through the shared client; 4 first choices",
        f"refetch: {second}",
        f"refetch: {third}",
        f"refetch: {first}",
    ]
    assert lines[8] == "  1  cik-0009990003:2026-03-31:release  parsed"
    assert lines[-3:] == moves


def test_acquire_refetch_stopped_partway_prints_each_move_before_its_count(
    repo, moved, monkeypatch
) -> None:
    """The first pilot row's exhibit is saved again, its cut file moved aside, before
    the second's meets a persistent 403. The move is printed before the count, which
    stays last: no later run could tell it."""
    first, second = pilot_exhibit(0), pilot_exhibit(1)
    quarantined = truncate(repo, first)
    truncate(repo, second)
    requested: list[str] = []
    budgets = client(
        monkeypatch,
        {**served(), **exhibit_bodies()},
        requested=requested,
        statuses={second: [403, 403]},
    )
    result = run(
        repo,
        "acquire",
        "--refetch",
        first,
        "--refetch",
        second,
        "--max-requests",
        "3",
        store=EVENTS_STORE,
    )
    assert result.exit_code == 1
    assert budgets == [3]
    assert requested == [first, second, second]
    assert acquire_lines(result)[-2:] == [quarantined, REFETCH_STOP_TAIL.format(3)]
    assert result.stderr == STOPPED.format(second)


def test_acquire_refetch_stopped_between_the_move_and_the_save_prints_the_move(
    repo, moved, monkeypatch
) -> None:
    """A full disk after the cut file is moved aside and before the exhibit is saved
    again: the exhibit's file has left its place, and the output says where it went
    (plan 25, Review Focus)."""
    url = pilot_exhibit()
    quarantined = truncate(repo, url)
    client(monkeypatch, {**served(), **exhibit_bodies()})
    monkeypatch.setattr(store_module, "write_new", full_disk)
    result = run(
        repo, "acquire", "--refetch", url, "--max-requests", "2", store=EVENTS_STORE
    )
    assert result.exit_code == 1
    assert acquire_lines(result)[-2:] == [quarantined, REFETCH_STOP_TAIL.format(1)]
    assert result.stderr == "Stopped: [Errno 28] No space left on device\n"


def test_acquire_refetch_interrupted_prints_each_move_before_its_count(
    repo, moved, monkeypatch
) -> None:
    """The first pilot row's exhibit is saved again, its cut file moved aside, and
    the second's save meets an error no stop names. The move is printed before the
    count, whose tail is acquire's own."""
    first, second = pilot_exhibit(0), pilot_exhibit(1)
    quarantined = truncate(repo, first)
    truncate(repo, second)
    client(monkeypatch, {**served(), **exhibit_bodies()})
    put = ArtifactStore.put

    def once(self, *args, **kwargs):
        if self.quarantined:
            unforeseen()
        return put(self, *args, **kwargs)

    monkeypatch.setattr(ArtifactStore, "put", once)
    result = run(
        repo,
        "acquire",
        "--refetch",
        first,
        "--refetch",
        second,
        "--max-requests",
        "3",
        store=EVENTS_STORE,
    )
    assert isinstance(result.exception, LookupError)
    assert acquire_lines(result)[-2:] == [quarantined, STOP_TAIL.format(2)]


INDEXED = ("0009990001", "0009990001-25-000008")
"""The filing whose index page is ``INDEX``."""
DISCOVER_TAIL = "requests sent: {}; a rerun fetches only what is missing"


def cut_and_unsaved(repo: Path) -> tuple[str, str]:
    """Cut ``INDEX``'s file and delete its filing's retrieval records, so the save
    of its index page needs the cut file's name. Return the line that save prints
    and the filing's primary document."""
    quarantined = truncate(repo, INDEX)
    index, document = unsave(repo, *INDEXED)
    assert index == INDEX
    return quarantined, document


@pytest.mark.parametrize("stopped", [False, True], ids=["finished", "stopped"])
@pytest.mark.parametrize(
    "filing", [(), ("--filing", *INDEXED)], ids=["discover", "filing"]
)
def test_discover_prints_each_quarantined_file_once(
    repo, moved, monkeypatch, filing, stopped
) -> None:
    """The save of ``INDEX`` moves its cut file aside. The move prints once, after
    the count, or before it when the primary document's fetch then stops (plan 26,
    Review Focus)."""
    quarantined, document = cut_and_unsaved(repo)
    statuses = {document: [403, 403]} if stopped else None
    client(monkeypatch, served(), statuses=statuses)
    result = run(repo, "discover", *filing, "--max-requests", "5", store=EVENTS_STORE)
    lines = result.stdout.splitlines()
    assert lines.count(quarantined) == 1
    assert [line for line in lines if line.startswith("quarantined:")] == [quarantined]
    if stopped:
        assert result.exit_code == 1
        assert isinstance(result.exception, SystemExit), result.exception
        # A 403 is retried once. --filing caps itself at 2, so its cap stops the
        # retry, and plain discover's 403 persists at its third request.
        assert lines[-2:] == [quarantined, DISCOVER_TAIL.format(2 if filing else 3)]
        assert result.stderr.startswith("Stopped: ")
    else:
        assert result.exit_code == 0, result.output
        assert lines[-2:] == ["fetched 2; requests sent: 2", quarantined]


@pytest.mark.parametrize("failure", ["unreadable record", "unforeseen"])
def test_discover_prints_each_quarantined_file_before_its_count_on_any_exit(
    repo, moved, monkeypatch, failure
) -> None:
    """After the save of ``INDEX`` moves its cut file aside, a retrieval record turns
    unreadable, or the next save meets an error no stop names. The move prints
    before the count on each early exit."""
    quarantined, _ = cut_and_unsaved(repo)
    (record, *_) = sorted((moved / SEC_SOURCE_ID / "retrievals").glob("*/*.json"))
    client(monkeypatch, served())
    put = ArtifactStore.put

    def then_fail(self, *args, **kwargs):
        if self.quarantined:
            unforeseen()
        saved = put(self, *args, **kwargs)
        if self.quarantined and failure == "unreadable record":
            record.write_bytes(b"")
        return saved

    monkeypatch.setattr(ArtifactStore, "put", then_fail)
    result = run(repo, "discover", "--max-requests", "5", store=EVENTS_STORE)
    assert result.exit_code == 1
    if failure == "unreadable record":
        assert isinstance(result.exception, SystemExit), result.exception
        assert result.stdout.splitlines()[-2:] == [quarantined, "requests sent: 1"]
        assert result.stderr.splitlines() == [f"Stopped: {record}: {UNREADABLE}"]
    else:
        assert isinstance(result.exception, LookupError)
        assert result.stdout.splitlines()[-2:] == [quarantined, DISCOVER_TAIL.format(2)]
