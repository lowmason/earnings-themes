"""The Stage 6 wording guard (the Stage 6 spec, §Wording guard; F20's rule, as
``test_corpus_quotes.py`` applies it): no 40-character window of any string in a
committed Stage 6 file, dates masked, occurs in the canonical text of a pilot
document or of a Stage 1 fixture.

- **The files.** Under ``evaluation/``: the split, the coverage report, the gold,
  and the briefs; codebook v0 and ADR 0003; and the curated hard negatives:
  whichever are committed yet. A Markdown file is read a paragraph at a time, its
  lines joined, so a phrase copied across a wrapped line is still caught.
- **What a failure prints.** Each finding is a pair: the file with its field or
  paragraph, and the event or fixture. Never the window or the string, since either
  may quote a release (GS13).
- **Where it runs.** The fixture leg always runs. The pilot leg reads the pilot's
  canonical documents from the local store and skips visibly without it, so each
  gate runs this module with ``-rs`` and reads "passed". Never run it with ``-l``,
  ``--showlocals``, ``--pdb``, or ``-vv``, which print pilot text on a failure.
"""

import json
from pathlib import Path

import pytest
import tomllib
from earnings_ingestion.canonical.serialize import from_fixture_json
from earnings_ingestion.events.coverage import parsed_documents
from earnings_ingestion.events.state_table import read_runs
from earnings_themes.wording import WIDTH, labelled_strings, markdown_paragraphs, shared

REPO = Path(__file__).resolve().parents[2]
PILOT_V1_HASH = "3839c800151cc646f11064efdce583f988e511265f8893c90e9a2f2549145926"
EVENT_RUNS = REPO / "data" / "runs" / "events"
FIXTURES = REPO / "tests" / "fixtures" / "canonical"
STAGE6 = (
    "evaluation/*/pilot-v*/*.json",
    "evaluation/*/pilot-v*/gold/*.toml",
    "evaluation/*/pilot-v*/briefs/*.md",
    "codebooks/*/codebook-v*.toml",
    "docs/adr/0003-*.md",
    "tests/fixtures/gold/*.toml",
)
BRIEFS = (
    "evaluation/djia-2024q3-2026q2/pilot-v1/briefs/codebook.md",
    "evaluation/djia-2024q3-2026q2/pilot-v1/briefs/gold.md",
)


def committed() -> list[Path]:
    return sorted({path for pattern in STAGE6 for path in REPO.glob(pattern)})


def strings(paths: list[Path]) -> list[tuple[str, str]]:
    """Each string of each file, labelled by the file and its field or paragraph."""
    found = []
    for path in paths:
        name = path.relative_to(REPO).as_posix()
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".md":
            found += markdown_paragraphs(text, name)
        elif path.suffix == ".toml":
            found += labelled_strings(tomllib.loads(text), name)
        else:
            found += labelled_strings(json.loads(text), name)
    return found


def fixture_texts() -> list[tuple[str, str]]:
    return [
        (
            path.stem,
            from_fixture_json(path.read_text(encoding="utf-8")).document.canonical_text,
        )
        for path in sorted(FIXTURES.glob("*.json"))
    ]


def test_the_briefs_are_among_the_files_checked() -> None:
    names = {path.relative_to(REPO).as_posix() for path in committed()}
    assert set(BRIEFS) <= names


def test_no_stage_6_file_quotes_a_stage_1_fixture() -> None:
    found = shared(strings(committed()), fixture_texts())
    assert found == set()


def test_no_stage_6_file_quotes_a_pilot_document() -> None:
    states = EVENT_RUNS / "states"
    if not states.is_dir():
        pytest.skip(
            "data/runs/events/ is not here: each Stage 6 gate runs this test with -rs"
        )
    doc_ids = parsed_documents(read_runs(states), PILOT_V1_HASH)
    assert len(doc_ids) == 40
    paths = {e: EVENT_RUNS / "canonical" / f"{d}.json" for e, d in doc_ids.items()}
    assert sorted(e for e, path in paths.items() if not path.is_file()) == []
    texts = [
        (e, from_fixture_json(path.read_text(encoding="utf-8")).document.canonical_text)
        for e, path in sorted(paths.items())
    ]
    found = shared(strings(committed()), texts)
    # Bound first: pytest's report of a failed assert shows each call's arguments,
    # and ``texts`` holds pilot text (GS13). ``found`` holds labels and IDs only.
    assert found == set()


@pytest.mark.parametrize(("width", "caught"), [(WIDTH, True), (WIDTH - 1, False)])
def test_a_copy_across_a_wrapped_line_is_caught(
    tmp_path: Path, width: int, caught: bool
) -> None:
    """A brief paragraph that copies 40 characters of a fixture, wrapped across two
    lines, is caught, and one that copies 39 is not. The copy is taken when the test
    runs, never typed here."""
    fixture_id, text = fixture_texts()[0]
    start = next(i for i in range(len(text)) if text[i : i + width].count(" ") >= 4)
    copied = text[start : start + width]
    assert "\n" not in copied
    cut = copied.index(" ", width // 2)
    brief = tmp_path / "brief.md"
    brief.write_text(
        f"# Brief\n\nOur words [{copied[:cut]}\n{copied[cut + 1 :]}] end here.\n",
        encoding="utf-8",
    )
    found = shared(
        markdown_paragraphs(brief.read_text(encoding="utf-8"), "brief"),
        [(fixture_id, text)],
    )
    assert found == ({("brief paragraph 2", fixture_id)} if caught else set())
