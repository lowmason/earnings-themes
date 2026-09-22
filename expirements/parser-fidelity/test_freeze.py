import datetime as dt

import pytest
from freeze import FROZEN_FILES, amend, load, record, verify

TODAY = dt.date(2026, 10, 2)


@pytest.fixture
def harness(tmp_path):
    for name in FROZEN_FILES:
        (tmp_path / name).write_text(f"# {name}\n")
    return tmp_path


def test_record_then_verify_passes(harness):
    freeze_file = harness / "FROZEN.toml"
    record(harness, freeze_file, "abc123", TODAY)
    assert verify(harness, freeze_file) == []
    frozen = load(freeze_file)
    assert frozen["commit"] == "abc123" and frozen["frozen_on"] == TODAY
    with pytest.raises(FileExistsError):
        record(harness, freeze_file, "def456", TODAY)


def test_unrecorded_change_fails_verification(harness):
    freeze_file = harness / "FROZEN.toml"
    record(harness, freeze_file, "abc123", TODAY)
    (harness / "walker.py").write_text("# retuned\n")
    assert verify(harness, freeze_file) == [
        "walker.py changed after the freeze without a recorded crash or network-guard fix"
    ]


def test_amend_records_a_permitted_fix(harness):
    freeze_file = harness / "FROZEN.toml"
    record(harness, freeze_file, "abc123", TODAY)
    (harness / "adapter_edgartools.py").write_text("# crash fix\n")
    amend(
        harness,
        freeze_file,
        "adapter_edgartools.py",
        "crash",
        "None caption crashed",
        TODAY,
    )
    assert verify(harness, freeze_file) == []
    [change] = load(freeze_file)["changes"]
    assert change["reason"] == "crash" and change["previous_sha256"] != change["sha256"]


def test_amend_refuses_other_reasons_and_no_ops(harness):
    freeze_file = harness / "FROZEN.toml"
    record(harness, freeze_file, "abc123", TODAY)
    with pytest.raises(ValueError, match="reason must be one of"):
        amend(harness, freeze_file, "walker.py", "tuning", "better headings", TODAY)
    with pytest.raises(ValueError, match="unchanged"):
        amend(harness, freeze_file, "walker.py", "crash", "nothing", TODAY)


def test_verify_without_a_freeze_file_fails(harness):
    assert "is missing" in verify(harness, harness / "FROZEN.toml")[0]
