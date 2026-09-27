"""The committed synthetic event corpus: it regenerates byte for byte, and replays
offline from the synthetic cohort's saved evidence and the event layer's saved
responses to its frozen event manifest and pilot (P-VI; SV12).

The replay runs with sockets disabled and no SEC identity set: the cohort's intervals
and resolution, eligibility, and both freezes read committed files alone, and need no
network, credential, proprietary roster, or model call.
"""

import json
import socket
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_ingestion.cohort.build import build
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.cohort.locators import ArtifactText
from earnings_ingestion.cohort.synthetic import build_options
from earnings_ingestion.events.build import build_events, load_overrides
from earnings_ingestion.events.evidence import check_evidence
from earnings_ingestion.events.fixture import (
    COHORT_MANIFEST,
    FIXTURE_DIR,
    SYNTHETIC_CORPUS,
    write_fixture,
)
from earnings_ingestion.events.freeze import (
    freeze_events,
    load_event_evidence,
    load_event_manifest,
)
from earnings_ingestion.events.pilot import freeze_pilot, load_pilot, select_pilot
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.fetch.store import ArtifactStore

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / FIXTURE_DIR
REGENERATE = "uv run --locked --all-packages python tests/integration/regenerate_event_fixtures.py"
MANIFESTS = ("events-v1.json", "events-v1.evidence.json", "pilot-v1.json")


def files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_the_fixture_regenerates_byte_for_byte(tmp_path: Path) -> None:
    write_fixture(tmp_path, load_manifest(REPO / COHORT_MANIFEST))
    fresh, committed = files(tmp_path / FIXTURE_DIR), files(ROOT)
    changed = sorted(
        name
        for name in fresh.keys() | committed.keys()
        if fresh.get(name) != committed.get(name)
    )
    assert not changed, f"regenerate with `{REGENERATE}`; differs: {changed[:5]}"
    assert set(MANIFESTS) | {"overrides.toml"} <= set(committed)


@pytest.fixture
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("the offline event path opened a network connection")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.delenv("EDGAR_IDENTITY", raising=False)
    monkeypatch.delenv("SOURCE_IDENTITY", raising=False)


@pytest.mark.usefixtures("offline")
def test_p_vi_replays_offline_to_the_frozen_manifests() -> None:
    committed = load_manifest(REPO / COHORT_MANIFEST)
    definition = committed.definition
    cohort = build(REPO, **build_options())
    universe = cohort.manifest(definition.universe_version, definition.created_at)
    assert universe == committed
    saved = SavedResponses(ArtifactStore(ROOT / "raw", REPO))
    overrides = load_overrides(ROOT / "overrides.toml")
    built = build_events(universe, saved, overrides, corpus_id=SYNTHETIC_CORPUS)
    events = load_event_manifest(ROOT / "events-v1.json")
    assert built.content_hash == events.definition.content_hash
    now = datetime.now(UTC)
    assert not freeze_events(built, saved, ROOT, now=now).created
    pilot = select_pilot(events, universe)
    assert not freeze_pilot(pilot, universe, ROOT, now=now).created
    frozen = load_pilot(ROOT / "pilot-v1.json", universe)
    assert (frozen.definition.target, frozen.definition.underfilled) == (27, True)
    assert [t.issuer_id for t in frozen.unmatched_transitions] == ["cik-0009990002"]


def test_every_citation_verifies_against_the_committed_store() -> None:
    manifest = load_event_manifest(ROOT / "events-v1.json")
    evidence = load_event_evidence(ROOT / "events-v1.evidence.json", manifest)
    assert check_evidence(evidence, ArtifactStore(ROOT / "raw", REPO)) == ()
    assert len(evidence.events) == 32


def strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for item in value.values() for s in strings(item)]
    if isinstance(value, list):
        return [s for item in value for s in strings(item)]
    return []


def test_the_committed_records_quote_no_saved_page() -> None:
    """P6-3: the committed records hold facts, URLs, hashes, and locators, never
    source text, so no string in them of 30 characters or more is in any saved
    page's walker-1 text."""
    written = {
        s
        for name in MANIFESTS
        for s in strings(json.loads((ROOT / name).read_text(encoding="utf-8")))
        if len(s) >= 30
    }
    pages = [
        ArtifactText(path.read_bytes(), "text/html").canonical[0]
        for path in sorted((ROOT / "raw" / "sec-edgar").glob("*.html"))
    ]
    assert written and pages
    assert not [s for s in written if any(s in page for page in pages)]


def ignored(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--no-index", path],
        cwd=REPO,
        check=False,
    )
    return result.returncode == 0


def test_saved_responses_stay_local_and_the_fixture_is_committed() -> None:
    assert ignored("data/raw/events/sec-edgar/retrievals/x/y.json")
    committed = files(ROOT)
    assert committed, f"{FIXTURE_DIR} holds no fixture"
    for path in committed:
        assert not ignored(f"{FIXTURE_DIR.as_posix()}/{path}"), path


def test_git_keeps_every_fixture_byte() -> None:
    """Saved responses are named by their hash, so a line-ending conversion on
    checkout would break them: .gitattributes marks every fixture file -text."""
    names = [f"{FIXTURE_DIR.as_posix()}/{path}" for path in files(ROOT)]
    assert names, f"{FIXTURE_DIR} holds no fixture"
    result = subprocess.run(
        ["git", "check-attr", "text", "--", *names],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.splitlines() == [f"{name}: text: unset" for name in names]
