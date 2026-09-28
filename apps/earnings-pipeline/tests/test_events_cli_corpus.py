"""``earnings-pipeline events`` keeps one corpus per corpus directory: ``freeze``
refuses a build of another corpus, and ``select`` one whose ``--corpus-id`` is not
the directory's, or a directory that holds two. Each runs on a copy of the committed
synthetic event corpus, whose ``corpus_id`` is ``djia-synthetic``."""

import shutil
from pathlib import Path

import pytest
from earnings_ingestion.events.fixture import COHORT_MANIFEST, FIXTURE_DIR
from earnings_ingestion.events.freeze import load_event_manifest, serialize
from earnings_ingestion.events.records import content_hash
from earnings_pipeline import cli
from typer.testing import CliRunner

RUNNER = CliRunner()
REPO = Path(__file__).resolve().parents[3]
UNIVERSES = COHORT_MANIFEST.parent


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """The synthetic cohort's manifests and the event corpus, at their paths."""
    for directory in (UNIVERSES, FIXTURE_DIR):
        shutil.copytree(REPO / directory, tmp_path / directory)
    return tmp_path


def run(repo: Path, command: str, corpus_id: str | None):
    layout = [
        "events",
        "--repo",
        str(repo),
        "--universe-dir",
        str(UNIVERSES),
        "--corpus-dir",
        str(FIXTURE_DIR),
        "--store",
        str(FIXTURE_DIR / "raw"),
    ]
    if corpus_id is not None:
        layout += ["--corpus-id", corpus_id]
    return RUNNER.invoke(cli.app, [*layout, command])


def names(repo: Path) -> list[str]:
    return sorted(path.name for path in (repo / FIXTURE_DIR).iterdir())


def refused(result, *words: str) -> None:
    """A refusal the command reports, not an exception it lets escape."""
    assert result.exit_code == 1, result.output
    assert isinstance(result.exception, SystemExit), result.exception
    assert "Refused: " in result.stderr
    for word in words:
        assert word in result.stderr


def test_freeze_refuses_a_build_of_another_corpus(repo) -> None:
    """Without --corpus-id, the build is the real corpus's, djia-2024q3-2026q2."""
    before = names(repo)
    result = run(repo, "freeze", None)
    refused(result, "djia-synthetic", "djia-2024q3-2026q2")
    assert names(repo) == before


def test_select_refuses_another_corpus_id(repo) -> None:
    before = names(repo)
    result = run(repo, "select", "djia-other")
    refused(result, "djia-synthetic", "djia-other")
    assert names(repo) == before


@pytest.mark.parametrize("command", ["freeze", "select"])
def test_a_directory_of_two_corpora_is_refused(repo, command) -> None:
    corpus = repo / FIXTURE_DIR
    events = load_event_manifest(corpus / "events-v1.json")
    other = events.model_copy(
        update={
            "definition": events.definition.model_copy(
                update={"corpus_id": "djia-other", "event_manifest_version": 2}
            )
        }
    )
    hashed = other.definition.model_copy(update={"content_hash": content_hash(other)})
    (corpus / "events-v2.json").write_bytes(
        serialize(other.model_copy(update={"definition": hashed}))
    )
    before = names(repo)
    result = run(repo, command, "djia-synthetic")
    refused(result, "more than one corpus", "djia-other", "djia-synthetic")
    assert names(repo) == before
