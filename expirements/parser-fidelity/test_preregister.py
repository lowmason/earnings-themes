import datetime as dt

import pytest
from pf_paths import REPO_ROOT
from preregister import (
    PREREGISTERED,
    PREREGISTERED_FILES,
    amend,
    load,
    record,
    verify,
)

TODAY = dt.date(2026, 10, 2)
LAYOUT = "packages/earnings-ingestion/src/earnings_ingestion/layout/blocks.py"


@pytest.fixture
def root(tmp_path):
    for name in PREREGISTERED_FILES:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {name}\n")
    return tmp_path


def test_every_preregistered_file_exists() -> None:
    assert [
        name for name in PREREGISTERED_FILES if not (REPO_ROOT / name).is_file()
    ] == []


def test_the_committed_record_verifies_once_it_exists() -> None:
    if not PREREGISTERED.exists():
        pytest.skip("layout-1 is not pre-registered yet (plan 5, Task 10)")
    assert verify(REPO_ROOT, PREREGISTERED) == []


def test_record_then_verify_passes(root) -> None:
    record_file = root / "layout1-preregistered.toml"
    record(root, record_file, "abc123", TODAY)
    assert verify(root, record_file) == []
    assert load(record_file)["commit"] == "abc123"
    with pytest.raises(FileExistsError):
        record(root, record_file, "def456", TODAY)


def test_a_change_after_the_freeze_fails_verification(root) -> None:
    record_file = root / "layout1-preregistered.toml"
    record(root, record_file, "abc123", TODAY)
    (root / LAYOUT).write_text("# a retuned heading rule\n")
    assert verify(root, record_file) == [
        f"{LAYOUT} changed after the pre-registration without a recorded fix"
    ]


def test_amend_records_a_crash_fix_and_refuses_tuning(root) -> None:
    record_file = root / "layout1-preregistered.toml"
    record(root, record_file, "abc123", TODAY)
    with pytest.raises(ValueError, match="reason must be one of"):
        amend(root, record_file, LAYOUT, "tuning", "better headings", TODAY)
    with pytest.raises(ValueError, match="unchanged"):
        amend(root, record_file, LAYOUT, "crash", "nothing", TODAY)
    (root / LAYOUT).write_text("# a crash fix\n")
    amend(root, record_file, LAYOUT, "crash", "an empty cell crashed", TODAY)
    assert verify(root, record_file) == []
    [change] = load(record_file)["changes"]
    assert change["reason"] == "crash" and change["previous_sha256"] != change["sha256"]
