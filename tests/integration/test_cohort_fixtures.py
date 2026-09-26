"""The committed synthetic cohort: it regenerates byte for byte, and replays offline
from saved evidence to its frozen manifest (P-VI's membership and issuer legs).

The replay runs with sockets disabled: building and freezing read committed files and
saved artifacts, never the network, and need no credential (P §Verification).
"""

import socket
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_ingestion.cohort.build import build
from earnings_ingestion.cohort.freeze import freeze, load_manifest
from earnings_ingestion.cohort.synthetic import (
    FIXTURE_DIR,
    build_options,
    write_synthetic_cohort,
)

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / FIXTURE_DIR / "manifests" / "djia-synthetic-v1.json"
REGENERATE = "uv run --locked --all-packages python tests/integration/regenerate_cohort_fixtures.py"


def files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_the_fixture_regenerates_byte_for_byte(tmp_path: Path) -> None:
    write_synthetic_cohort(tmp_path, FIXTURE_DIR)
    fresh, committed = files(tmp_path / FIXTURE_DIR), files(REPO / FIXTURE_DIR)
    changed = sorted(
        name
        for name in fresh.keys() | committed.keys()
        if fresh.get(name) != committed.get(name)
    )
    assert not changed, f"regenerate with `{REGENERATE}`; differs: {changed[:5]}"


@pytest.fixture
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("the offline cohort path opened a network connection")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


@pytest.mark.usefixtures("offline")
def test_saved_evidence_replays_to_the_frozen_manifest(tmp_path: Path) -> None:
    built = build(REPO, **build_options())
    committed = load_manifest(MANIFEST)
    assert built.content_hash == committed.definition.content_hash
    again = freeze(built, REPO / FIXTURE_DIR / "manifests", now=datetime.now(UTC))
    assert (again.created, again.path) == (False, MANIFEST)


def test_every_interval_rests_on_supported_evidence() -> None:
    manifest = load_manifest(MANIFEST)
    assertions = {a.membership_assertion_id: a for a in manifest.assertions}
    for interval in manifest.intervals:
        assert interval.assertion_ids
        for assertion_id in interval.assertion_ids:
            assertion = assertions[assertion_id]
            assert assertion.status == "supported"
            assert assertion.evidence_locators
            assert (assertion.effective_from, assertion.effective_to) == (
                interval.effective_from,
                interval.effective_to,
            )


def test_every_resolved_cik_is_ten_digits_and_one_issuer_per_cik() -> None:
    manifest = load_manifest(MANIFEST)
    ciks = [m.cik for m in manifest.mappings if m.cik is not None]
    assert ciks and all(len(cik) == 10 and cik.isdigit() for cik in ciks)
    assert len({i.cik for i in manifest.issuers}) == len(manifest.issuers)
    in_issuers = {s for i in manifest.issuers for s in i.security_ids}
    assert in_issuers == {m.security_id for m in manifest.mappings if m.cik}


def test_the_candidate_issuers_are_the_in_scope_securities_issuers() -> None:
    manifest = load_manifest(MANIFEST)
    definition = manifest.definition
    stop = definition.public_information_cutoff.toordinal() + 1
    in_scope = {
        i.security_id
        for i in manifest.intervals
        if i.overlaps(definition.period_end_start, datetime.fromordinal(stop).date())
    }
    mappings = {m.security_id: m for m in manifest.mappings}
    assert manifest.candidate_issuer_ids == tuple(
        sorted({mappings[s].issuer_id for s in in_scope if mappings[s].issuer_id})
    )


def ignored(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--no-index", path],
        cwd=REPO,
        check=False,
    )
    return result.returncode == 0


def test_saved_evidence_stays_local_and_the_fixture_is_committed() -> None:
    assert ignored("data/raw/cohort/wikipedia-djia/page.html")
    assert ignored("data/runs/cohort/live/20261001T000000Z.json")
    committed = files(REPO / FIXTURE_DIR)
    assert committed, f"{FIXTURE_DIR} holds no fixture"
    for path in committed:
        assert not ignored(f"{FIXTURE_DIR.as_posix()}/{path}"), path


def test_git_keeps_every_fixture_byte() -> None:
    """Saved artifacts are named by their hash, so a line-ending conversion on checkout
    would break them: .gitattributes marks every fixture file -text."""
    names = [f"{FIXTURE_DIR.as_posix()}/{path}" for path in files(REPO / FIXTURE_DIR)]
    assert names, f"{FIXTURE_DIR} holds no fixture"
    result = subprocess.run(
        ["git", "check-attr", "text", "--", *names],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.splitlines() == [f"{name}: text: unset" for name in names]
