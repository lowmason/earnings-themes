"""Where fetched bytes and run outputs may be written, and how paths print (PR #6's
review, F19 and F38; plan 8, P8-13)."""

from pathlib import Path

from earnings_pipeline.paths import raw_store_refusal, runs_refusal, shown


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
