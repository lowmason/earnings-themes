"""Stage 6 over the committed pilot v1 (the Stage 6 spec, §The pin, §The split, and
§The coverage report; GS2, GS10, P-C7): the pin's values, the split's counts and
exclusions, and that neither command changes a frozen record.

The split needs only committed files, so it runs everywhere; once gate 1 commits
it, the rebuild must reproduce it byte for byte. The coverage report, codebook v0,
and the gold are checked against the local store: those legs skip visibly without
it, and each gate runs this module with ``-rs``. Every assertion compares IDs,
counts, and hashes; none prints a document's text (GS13).
"""

import re
import shutil
from collections import Counter
from pathlib import Path

import pytest
from earnings_ingestion.events.coverage import build_coverage, load_coverage
from earnings_ingestion.events.freeze import serialize
from earnings_ingestion.events.state_table import read_runs
from earnings_ingestion.events.states import DocumentState
from earnings_pipeline import cli
from earnings_pipeline.stage6 import (
    FIXTURE_MANIFEST,
    PILOT_V1,
    PILOT_V1_HASH,
    UNIVERSE_V1,
    Layout,
    file_stem,
    load_pinned,
)
from earnings_themes.split import Partition, load_split
from typer.testing import CliRunner

RUNNER = CliRunner()
REPO = Path(__file__).resolve().parents[2]
EVALUATION = REPO / "evaluation" / "djia-2024q3-2026q2" / "pilot-v1"
STATES = REPO / "data" / "runs" / "events" / "states"
EXCLUDED = [
    "cik-0000004962:2026-06-30",
    "cik-0000320187:2026-05-31",
    "cik-0000731766:2026-06-30",
    "cik-0000732712:2026-03-31",
    "cik-0001403161:2026-06-30",
]


def frozen_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted((root / "config").rglob("*"))
        if path.is_file()
    }


@pytest.fixture(scope="module")
def split_run(tmp_path_factory: pytest.TempPathFactory):
    """``pilot split`` over a copy of the committed records."""
    root = tmp_path_factory.mktemp("repo")
    shutil.copytree(REPO / "config", root / "config")
    (root / FIXTURE_MANIFEST).parent.mkdir(parents=True)
    shutil.copy2(REPO / FIXTURE_MANIFEST, root / FIXTURE_MANIFEST)
    before = frozen_bytes(root)
    result = RUNNER.invoke(cli.app, ["pilot", "--repo", str(root), "split"])
    return root, before, result


def test_the_pin_is_pilot_v1_and_its_chain() -> None:
    pinned = load_pinned(Layout(REPO, UNIVERSE_V1, PILOT_V1, PILOT_V1_HASH))
    assert pinned.pin.model_dump() == {
        "pilot_id": "djia-2024q3-2026q2-pilot",
        "pilot_version": 1,
        "pilot_hash": PILOT_V1_HASH,
        "events_version": 1,
        "events_hash": (
            "2348671b3ae8021d644df12ae2f539258670546970c918f8edb231ba1885c3b7"
        ),
        "universe_version": 1,
        "universe_operative_hash": (
            "c350923422d9bf2e65a0b5929f4c0d45370458c6a044c3de012a1dfeb116e573"
        ),
    }
    assert pinned.evaluation == EVALUATION


def test_the_split_gives_the_spec_s_counts_and_exclusions(split_run) -> None:
    root, _, result = split_run
    assert result.exit_code == 0, result.output
    split = load_split(root / EVALUATION.relative_to(REPO) / "split-v1.json")
    counts = Counter(row.partition for row in split.rows)
    assert counts == {
        Partition.TRAIN: 20,
        Partition.DEV: 8,
        Partition.TEST: 7,
        Partition.EXCLUDED: 5,
    }
    assert split.events_in(Partition.EXCLUDED) == tuple(EXCLUDED)
    assert {row.reason for row in split.rows if row.reason} == {
        "issuer_in_earlier_partition"
    }
    pinned = load_pinned(Layout(REPO, UNIVERSE_V1, PILOT_V1, PILOT_V1_HASH))
    boundary = [
        row.event_id
        for row in pinned.pilot.rows
        if row.selection_reason == "membership_boundary"
    ]
    assert Counter(split.partition_of(e) for e in boundary) == {
        Partition.TRAIN: 2,
        Partition.EXCLUDED: 1,
    }


def test_the_split_changes_no_frozen_record(split_run) -> None:
    """P-C7: the split reads the pilot by path and writes only under evaluation/."""
    root, before, _ = split_run
    assert frozen_bytes(root) == before


def test_the_committed_split_reproduces_byte_for_byte(split_run) -> None:
    committed = EVALUATION / "split-v1.json"
    if not committed.is_file():
        pytest.skip("split-v1.json is frozen at gate 1")
    root, _, _ = split_run
    rebuilt = root / EVALUATION.relative_to(REPO) / "split-v1.json"
    assert rebuilt.read_bytes() == committed.read_bytes()


def test_the_committed_coverage_report_reproduces_from_its_runs() -> None:
    committed = EVALUATION / "coverage-v1.json"
    if not committed.is_file():
        pytest.skip("coverage-v1.json is frozen at gate 1")
    if not STATES.is_dir():
        pytest.skip("data/runs/events/ is not here: each Stage 6 gate runs this test")
    report = load_coverage(committed)
    pinned = load_pinned(Layout(REPO, UNIVERSE_V1, PILOT_V1, PILOT_V1_HASH))
    rebuilt = build_coverage(
        pinned.pilot,
        pinned.coverage_pin,
        read_runs(STATES),
        run_ids=report.run_ids,
    )
    assert serialize(rebuilt) == committed.read_bytes()
    assert report.documents == 40
    assert report.count(DocumentState.PARSED) == 40
    assert [gap.state for gap in report.gaps] == ["unavailable", "restricted", "failed"]
    assert [(o.override_id, o.verdict) for o in report.overrides] == [
        ("release-doc-dis-2026-03-28", "not_confirmed")
    ]


@pytest.mark.parametrize(
    ("group", "args", "needs"),
    [
        ("codebook", ["validate"], "codebooks/djia-pilot/codebook-v0.toml"),
        ("gold", ["validate"], "evaluation/djia-2024q3-2026q2/pilot-v1/gold"),
    ],
)
def test_committed_records_validate_against_the_local_store(
    group: str, args: list[str], needs: str
) -> None:
    if not (REPO / needs).exists():
        pytest.skip(f"{needs} is committed at a later gate")
    if not STATES.is_dir():
        pytest.skip("data/runs/events/ is not here: each Stage 6 gate runs this test")
    result = RUNNER.invoke(cli.app, [group, "--repo", str(REPO), *args])
    assert result.exit_code == 0, result.output
    assert result.output.startswith("valid: ") or "\nvalid: " in result.output


def test_the_codebook_brief_lists_exactly_the_training_releases(split_run) -> None:
    """The spec, §Drafting and tools: the brief lists the 20 training bundles'
    paths, taken from the split."""
    root, _, _ = split_run
    split = load_split(root / EVALUATION.relative_to(REPO) / "split-v1.json")
    brief = (EVALUATION / "briefs" / "codebook.md").read_text(encoding="utf-8")
    listed = re.findall(r"^- `data/runs/gold/texts/([^`/]+)\.md`$", brief, re.MULTILINE)
    assert listed == [file_stem(e) for e in split.events_in(Partition.TRAIN)]
    assert len(listed) == 20


def test_the_curated_hard_negatives_validate_offline() -> None:
    """Their fixtures' canonical text and codebook v0 are committed, so they are
    checked in the default suite, with no local store."""
    if not (REPO / "tests" / "fixtures" / "gold" / "hard-negatives.toml").is_file():
        pytest.skip("the curated hard negatives are committed at gate 4")
    result = RUNNER.invoke(
        cli.app, ["gold", "--repo", str(REPO), "validate", "--hard-negatives"]
    )
    assert result.exit_code == 0, result.output
    assert result.output.startswith("valid: hard-negatives, ")
