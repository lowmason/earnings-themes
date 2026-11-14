"""Where fetched bytes and run outputs may be written, and how paths print (PR #6's
review, F19 and F38; plan 8, P8-13)."""

import json
from pathlib import Path

import pytest
from earnings_ingestion.cohort.config import OverridesFile
from earnings_pipeline.paths import error_lines, raw_store_refusal, runs_refusal, shown
from pydantic import ValidationError


def test_a_store_under_a_symlinked_data_directory_is_under_data_raw(
    tmp_path,
) -> None:
    repo, elsewhere = tmp_path / "repo", tmp_path / "disk"
    (elsewhere / "raw").mkdir(parents=True)
    repo.mkdir()
    (repo / "data").symlink_to(elsewhere)
    assert raw_store_refusal(repo, Path("data/raw/events")) is None
    assert raw_store_refusal(repo, Path("data/raw/../../tests/fixtures/x"))


def test_a_path_prints_relative_under_the_repo_and_in_full_elsewhere(
    tmp_path,
) -> None:
    repo = tmp_path / "repo"
    assert shown(repo / "config" / "x.json", repo) == "config/x.json"
    assert shown(tmp_path / "other" / "x.json", repo) == str(
        tmp_path / "other" / "x.json"
    )


def test_run_outputs_stay_under_data_runs(tmp_path) -> None:
    assert runs_refusal(tmp_path, Path("data/runs/events")) is None
    refusal = runs_refusal(tmp_path, Path("data/raw/../runs-elsewhere"))
    assert refusal is not None
    assert "does not resolve under data/runs" in refusal


OVERRIDE = {
    "override_id": "o1",
    "kind": "retain_unresolved",
    "security_id": "s1",
    "citations": [],
    "rationale": "Synthetic.",
    "reviewer": "Synthetic Reviewer",
    "recorded_on": "2026-09-28",
    "effective_from": "2024-07-01",
}


def refused_overrides(*overrides: dict) -> ValidationError:
    """The error the real overrides model raises for ``overrides``."""
    text = json.dumps({"schema_version": 1, "overrides": list(overrides)})
    with pytest.raises(ValidationError) as caught:
        OverridesFile.model_validate_json(text)
    return caught.value


def test_a_validation_error_gives_one_line_for_each_entry() -> None:
    """The entries are the lines: not pydantic's header, its echo of the input, or
    its documentation URL."""
    unnamed = {key: value for key, value in OVERRIDE.items() if key != "rationale"}
    error = refused_overrides({**unnamed, "bogus_key": 1})
    assert len(error.errors()) == 2
    assert error_lines(error) == [
        "overrides.0.bogus_key: Extra inputs are not permitted",
        "overrides.0.rationale: Field required",
    ]


def test_a_validation_error_with_no_location_gives_its_message_alone() -> None:
    error = refused_overrides(OVERRIDE, OVERRIDE)
    assert error.errors()[0]["loc"] == ()
    assert error_lines(error) == ["Value error, override_id repeated"]


def test_a_plain_error_gives_the_non_empty_lines_of_its_text() -> None:
    error = ValueError("first\n\n  second\n   \nthird\n")
    assert error_lines(error) == ["first", "  second", "third"]


def test_a_one_line_error_gives_one_unchanged_line() -> None:
    assert error_lines(ValueError("walker-1 found no text")) == [
        "walker-1 found no text"
    ]
    missing = FileNotFoundError(2, "No such file or directory", "evidence.toml")
    assert error_lines(missing) == [
        "[Errno 2] No such file or directory: 'evidence.toml'"
    ]


def test_an_error_with_no_text_still_gives_one_line() -> None:
    assert error_lines(ValueError()) == ["ValueError"]
