"""Stage 6's commands over the synthetic pilot (plan 9): the split and the coverage
report freeze once, over the pin; codebook v0 freezes only once its ADR cites it;
every refusal names its item and reason; and no command prints a document's text
(GS13) or changes a frozen record (P-C7).

The synthetic acquisition is replayed offline once, into ``data/runs/events/``, as
Stage 5's replay test does; its documents are the synthetic layer's invented text.
"""

import shutil
from pathlib import Path

import pytest
from earnings_ingestion.canonical.serialize import from_fixture_json
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.events.acquire import acquire
from earnings_ingestion.events.coverage import load_coverage
from earnings_ingestion.events.fixture import (
    ACQUIRED_AT,
    ACQUISITION_RUN,
    COHORT_MANIFEST,
    FIXTURE_DIR,
)
from earnings_ingestion.events.freeze import load_event_manifest
from earnings_ingestion.events.pilot import load_pilot
from earnings_ingestion.events.records import AcquisitionOverridesFile
from earnings_ingestion.events.state_table import read_runs, write_run
from earnings_ingestion.events.states import DocumentState
from earnings_ingestion.fetch.responses import UnexpectedResponse
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_pipeline import cli
from earnings_pipeline.stage6 import (
    Layout,
    documents,
    load_pinned,
    wording_refusals,
    wording_texts,
)
from earnings_themes import tomlfile
from earnings_themes.codebook import load_codebook
from earnings_themes.gold import ReleaseIdentification, ReleaseLabel
from earnings_themes.split import load_split
from earnings_themes.synthetic import codebook_draft
from earnings_themes.wording import WIDTH, masked
from typer.testing import CliRunner

RUNNER = CliRunner()
REPO = Path(__file__).resolve().parents[3]
PILOT_HASH = "71c6ac4fabc3b7e727da88b4ee74048a0ee3559c8e5ce26c02227376d820333c"
EVENT_RUNS = Path("data") / "runs" / "events"
DRAFTS = Path("data") / "runs" / "gold" / "drafts"
EVALUATION = Path("evaluation") / "djia-synthetic" / "pilot-v1"
CANONICAL = Path("tests") / "fixtures" / "canonical"
RELEASES = Path("tests") / "fixtures" / "releases" / "manifest.toml"
CODEBOOK = Path("codebooks") / "djia-pilot" / "codebook-v0.toml"
ADR = Path("docs") / "adr" / "0003-codebook-v0.md"
FIRST = "cik-0009990001:2024-08-31"
UNPARSED = ("cik-0009990003:2025-06-30", "cik-0009990005:2025-03-28")
EXCLUDED = "cik-0009990001:2025-08-31"
SENTENCE = "today reported net sales of $1,000 million"
WINDOW = 20


@pytest.fixture(scope="module")
def acquired(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The synthetic acquisition's run file and canonical documents, replayed
    offline: the one exhibit SEC never served stays unavailable."""
    root = tmp_path_factory.mktemp("acquired")
    store = tmp_path_factory.mktemp("store")
    shutil.copytree(REPO / FIXTURE_DIR / "raw", store / "raw")
    universe = load_manifest(REPO / COHORT_MANIFEST)

    def sec(url: str, types) -> None:
        raise UnexpectedResponse(f"HTTP 404 for {url}")

    acquire(
        load_event_manifest(REPO / FIXTURE_DIR / "events-v1.json"),
        load_pilot(REPO / FIXTURE_DIR / "pilot-v1.json", universe),
        universe,
        ArtifactStore(store / "raw", store),
        sec,
        overrides=AcquisitionOverridesFile(schema_version=1),
        states_dir=root / EVENT_RUNS / "states",
        canonical_dir=root / EVENT_RUNS / "canonical",
        run_id=ACQUISITION_RUN,
        now=lambda: ACQUIRED_AT,
    )
    return root


@pytest.fixture
def repo(tmp_path: Path, acquired: Path) -> Path:
    """The synthetic cohort and pilot, Stage 1's fixtures, and the acquisition."""
    ignore = shutil.ignore_patterns("raw")
    for directory in (COHORT_MANIFEST.parent, FIXTURE_DIR, CANONICAL):
        shutil.copytree(REPO / directory, tmp_path / directory, ignore=ignore)
    (tmp_path / RELEASES).parent.mkdir(parents=True)
    shutil.copy2(REPO / RELEASES, tmp_path / RELEASES)
    shutil.copytree(acquired / "data", tmp_path / "data")
    return tmp_path


def texts(repo: Path) -> list[str]:
    """Every canonical text a command could read: the pilot's and Stage 1's."""
    paths = [
        *(repo / EVENT_RUNS / "canonical").glob("*.json"),
        *(repo / CANONICAL).glob("*.json"),
    ]
    return [
        from_fixture_json(path.read_text(encoding="utf-8")).document.canonical_text
        for path in paths
    ]


def quiet(repo: Path, output: str) -> None:
    """GS13: no 20-character window of any canonical text is printed. The
    assertion names a count, never the window."""
    windows = {
        text[i : i + WINDOW]
        for text in texts(repo)
        for i in range(len(text) - WINDOW + 1)
    }
    leaked = sum(
        1 for i in range(len(output) - WINDOW + 1) if output[i : i + WINDOW] in windows
    )
    assert leaked == 0, f"{leaked} printed windows of document text"


def run(repo: Path, group: str, *args: str):
    layout = [
        "--repo",
        str(repo),
        "--universe",
        str(COHORT_MANIFEST),
        "--pilot",
        str(FIXTURE_DIR / "pilot-v1.json"),
        "--pilot-hash",
        PILOT_HASH,
    ]
    result = RUNNER.invoke(cli.app, [group, *layout, *args])
    quiet(repo, result.output)
    return result


def lines(result) -> list[str]:
    return result.output.splitlines()


def write_drafts(repo: Path, name: str, drafted: dict, working: dict | None = None):
    folder = repo / DRAFTS
    folder.mkdir(parents=True, exist_ok=True)
    for kind, data in (("draft", drafted), ("working", working or drafted)):
        text = tomlfile.dumps(data)
        path = folder / f"{name.replace(':', '_')}.{kind}.toml"
        path.write_text(text, encoding="utf-8")


def the_codebook(**changes) -> dict:
    draft = codebook_draft(**changes)
    draft["themes"][0]["positive_examples"] = [{"event_id": FIRST, "text": SENTENCE}]
    return draft


def frozen(repo: Path) -> Path:
    """The split frozen and codebook v0 approved, as gate 3 leaves them."""
    assert run(repo, "pilot", "split").exit_code == 0
    write_drafts(repo, "codebook", the_codebook())
    first = run(repo, "codebook", "freeze")
    content_hash = lines(first)[-2].split()[-1]
    (repo / ADR).parent.mkdir(parents=True)
    (repo / ADR).write_text(f"Codebook v0 is {content_hash}.\n", encoding="utf-8")
    approved = run(
        repo,
        "codebook",
        "freeze",
        "--adr",
        str(ADR),
        "--approver",
        "Lowell Mason",
        "--approved-on",
        "2026-10-02",
    )
    assert approved.exit_code == 0, approved.output
    return repo / CODEBOOK


def pilot_bytes(repo: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in (repo / FIXTURE_DIR).glob("*.json")}


def guarded_texts(repo: Path) -> dict[str, str]:
    """What the wording guard reads over the synthetic pilot, by text ID."""
    layout = Layout(repo, COHORT_MANIFEST, FIXTURE_DIR / "pilot-v1.json", PILOT_HASH)
    return wording_texts(layout, load_pinned(layout))


def first_fixture(repo: Path) -> str:
    return min(path.stem for path in (repo / CANONICAL).glob("*.json"))


def unique_window(found: dict[str, str], name: str) -> str:
    """One window of the named text, with no date and four spaces or more, that no
    other text holds once dates are masked, as the guard compares them; taken when
    the test runs, never typed here."""
    others = [masked(text) for key, text in found.items() if key != name]
    text = masked(found[name])
    for start in range(len(text) - WIDTH + 1):
        window = text[start : start + WIDTH]
        if "\n" in window or "\0" in window or window.count(" ") < 4:
            continue
        if not any(window in other for other in others):
            return window
    raise AssertionError(f"{name} has no window of its own")


def test_split_freezes_once_and_prints_only_ids_and_counts(repo) -> None:
    result = run(repo, "pilot", "split")
    assert result.exit_code == 0, result.output
    assert lines(result)[:5] == [
        f"pilot djia-synthetic-pilot v1  {PILOT_HASH}",
        "train  13",
        "dev  0",
        "test  0",
        "excluded  14",
    ]
    assert f"excluded  {EXCLUDED}  issuer_in_earlier_partition" in lines(result)
    assert lines(result)[-2] == "froze split v1 by issuer-time/1"
    split = load_split(repo / EVALUATION / "split-v1.json")
    assert lines(result)[-1] == (
        f"evaluation/djia-synthetic/pilot-v1/split-v1.json  {split.content_hash}"
    )
    again = run(repo, "pilot", "split")
    assert lines(again)[-2] == "unchanged: split v1 by issuer-time/1"


def test_a_changed_split_is_refused_and_never_edited(repo) -> None:
    path = repo / EVALUATION / "split-v1.json"
    path.parent.mkdir(parents=True)
    path.write_text("{}\n", encoding="utf-8")
    result = run(repo, "pilot", "split")
    assert result.exit_code == 1
    assert lines(result)[-1] == (
        "Refused: evaluation/djia-synthetic/pilot-v1/split-v1.json holds other"
        " content; a changed record is a new version, never an edit"
    )
    assert path.read_text(encoding="utf-8") == "{}\n"


def test_another_pilot_hash_is_refused(repo) -> None:
    result = RUNNER.invoke(
        cli.app,
        [
            "pilot",
            "--repo",
            str(repo),
            "--universe",
            str(COHORT_MANIFEST),
            "--pilot",
            str(FIXTURE_DIR / "pilot-v1.json"),
            "--pilot-hash",
            "0" * 64,
            "split",
        ],
    )
    assert result.exit_code == 1
    assert lines(result) == [
        (
            f"Refused: tests/fixtures/events/pilot-v1.json holds pilot {PILOT_HASH},"
            f" not the pin's {'0' * 64}"
        )
    ]
    assert not (repo / EVALUATION).exists()


def test_a_universe_that_is_not_the_pin_s_is_refused(repo) -> None:
    other = Path("config") / "universe" / "djia" / "manifests"
    other = other / "djia-2024q3-2026q2-v1.json"
    (repo / other).parent.mkdir(parents=True)
    shutil.copy2(REPO / other, repo / other)
    result = RUNNER.invoke(
        cli.app,
        [
            "pilot",
            "--repo",
            str(repo),
            "--universe",
            str(other),
            "--pilot",
            str(FIXTURE_DIR / "pilot-v1.json"),
            "--pilot-hash",
            PILOT_HASH,
            "split",
        ],
    )
    assert result.exit_code == 1
    assert lines(result) == [
        (
            "Refused: the universe's operative hash is not the one the pilot and its"
            " event manifest read"
        )
    ]


def test_coverage_counts_each_state_and_rereads_only_its_runs(repo) -> None:
    before = pilot_bytes(repo)
    result = run(repo, "pilot", "coverage")
    assert result.exit_code == 0, result.output
    assert lines(result)[1:7] == [
        "parsed  24",
        "failed  1",
        "unavailable  2",
        "gap  restricted  (D4: never repaired by reselecting)",
        f"runs  {ACQUISITION_RUN}",
        "froze coverage v1: 27 documents",
    ]
    report = load_coverage(repo / EVALUATION / "coverage-v1.json")
    states = repo / EVENT_RUNS / "states"
    parsed = next(t for t in read_runs(states) if t.to_state is DocumentState.PARSED)
    later = parsed.model_copy(
        update={
            "run_id": "stage-7",
            "sequence": 0,
            "recorded_at": ACQUIRED_AT.replace(hour=14),
            "from_state": DocumentState.PARSED,
            "to_state": DocumentState.PARTIAL,
            "attempts": (),
        }
    )
    write_run(states, [later])
    again = run(repo, "pilot", "coverage")
    assert again.exit_code == 0, again.output
    assert lines(again)[-2] == "unchanged: coverage v1: 27 documents"
    assert load_coverage(repo / EVALUATION / "coverage-v1.json") == report
    assert pilot_bytes(repo) == before


def test_a_record_is_checked_against_every_text_the_wording_guard_reads(
    repo,
) -> None:
    """GS3: before a command writes a record, it checks the record's strings against
    each parsed pilot document and each Stage 1 fixture, as the committed guard
    does; a copy is named by its field and the text's ID, never quoted."""
    layout = Layout(repo, COHORT_MANIFEST, FIXTURE_DIR / "pilot-v1.json", PILOT_HASH)
    pinned = load_pinned(layout)
    found = wording_texts(layout, pinned)
    fixture_ids = [path.stem for path in sorted((repo / CANONICAL).glob("*.json"))]
    assert sorted(found) == sorted([*documents(layout, pinned), *fixture_ids])
    last = fixture_ids[-1]
    copied = unique_window(found, last)
    record = ReleaseIdentification(label=ReleaseLabel.RELEASE, note=f"Ours: {copied}")
    refusals = [str(refusal) for refusal in wording_refusals(record, found)]
    assert refusals == [f"note ({last}): source_wording"]


def test_codebook_v0_is_written_only_once_its_adr_cites_it(repo) -> None:
    assert run(repo, "pilot", "split").exit_code == 0
    write_drafts(repo, "codebook", the_codebook())
    first = run(repo, "codebook", "freeze")
    assert first.exit_code == 0, first.output
    assert lines(first)[:3] == [
        f"no parsed document  {UNPARSED[0]}",
        f"no parsed document  {UNPARSED[1]}",
        "codebook djia-pilot v0: 1 themes, 2 examples, from 11 training bundles",
    ]
    assert lines(first)[-1].startswith("not written: ADR 0003 cites this hash")
    assert not (repo / CODEBOOK).exists()
    content_hash = lines(first)[-2].split()[-1]
    (repo / ADR).parent.mkdir(parents=True)
    (repo / ADR).write_text("Codebook v0.\n", encoding="utf-8")
    approve = ["--adr", str(ADR), "--approver", "Lowell Mason"]
    uncited = run(repo, "codebook", "freeze", *approve, "--approved-on", "2026-10-02")
    assert lines(uncited)[-1] == f"Refused: {ADR} does not cite {content_hash}"
    assert not (repo / CODEBOOK).exists()
    (repo / ADR).write_text(f"Codebook v0 is {content_hash}.\n", encoding="utf-8")
    cited = run(repo, "codebook", "freeze", *approve, "--approved-on", "2026-10-02")
    assert cited.exit_code == 0, cited.output
    assert lines(cited)[-2:] == [
        "froze djia-pilot v0, approved",
        f"{CODEBOOK}  {content_hash}",
    ]
    codebook = load_codebook(repo / CODEBOOK)
    assert codebook.content_hash == content_hash
    assert codebook.discovery_corpus.event_ids[0] == FIRST
    assert (
        FIRST
        not in (repo / CODEBOOK)
        .read_text(encoding="utf-8")
        .split("[[themes]]")[1]
        .split("event_id")[0]
    )
    valid = run(repo, "codebook", "validate")
    assert valid.exit_code == 0, valid.output
    assert lines(valid)[-2] == (
        "valid: djia-pilot v0, 1 themes, approved by Lowell Mason on 2026-10-02"
    )


def test_a_codebook_that_copies_a_training_release_is_refused(repo) -> None:
    assert run(repo, "pilot", "split").exit_code == 0
    copied = the_codebook()
    copied["themes"][0]["definition"] = (
        f"Acme Industrial Corp {SENTENCE} for the quarter."
    )
    write_drafts(repo, "codebook", copied)
    result = run(repo, "codebook", "freeze")
    assert result.exit_code == 1
    refusals = [line for line in lines(result) if line.startswith("refused: ")]
    assert f"refused: themes[0].definition ({FIRST}): source_wording" in refusals
    assert all(line.endswith("): source_wording") for line in refusals)
    assert lines(result)[-1] == (
        f"Refused: {len(refusals)} problem(s); nothing written"
    )


def test_a_codebook_that_copies_any_pilot_release_is_refused_before_its_hash(
    repo,
) -> None:
    """GS3: codebook freeze checks v0 against every text the committed guard reads,
    not only the training releases, so a codebook the guard would refuse gets no
    content hash, and nothing is written. The synthetic releases share one template,
    so the copy is taken from a Stage 1 fixture, which the guard also reads."""
    assert run(repo, "pilot", "split").exit_code == 0
    found = guarded_texts(repo)
    other = first_fixture(repo)
    changed = the_codebook()
    changed["themes"][0]["definition"] = f"Ours: {unique_window(found, other)}"
    write_drafts(repo, "codebook", changed)
    result = run(repo, "codebook", "freeze")
    assert result.exit_code == 1
    assert [line for line in lines(result) if line.startswith("refused: ")] == [
        f"refused: themes[0].definition ({other}): source_wording"
    ]
    assert not any(line.startswith("content_hash") for line in lines(result))
    assert not (repo / CODEBOOK).exists()


def test_codebook_validate_checks_every_text_the_guard_reads(repo) -> None:
    """P9-21: codebook validate rechecks the committed v0 against every text the
    committed guard reads, as freeze does."""
    path = frozen(repo)
    other = first_fixture(repo)
    record = tomlfile.read(path)
    copied = unique_window(guarded_texts(repo), other)
    record["themes"][0]["definition"] = f"Ours: {copied}"
    path.write_text(tomlfile.dumps(record), encoding="utf-8")
    result = run(repo, "codebook", "validate")
    assert result.exit_code == 1
    assert f"refused: themes[0].definition ({other}): source_wording" in lines(result)
