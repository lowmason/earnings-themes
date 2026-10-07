"""The output boundary uses only invented child programs in temporary roots."""

import json
from pathlib import Path

import pytest

from tools.stage10_checks import run_checks
from tools.stage10_pytest import safe_test_id

SENTINEL = "invented sentinel wording never printed"


def child(tmp_path: Path, source: str) -> Path:
    path = tmp_path / "test_invented.py"
    path.write_text(source, encoding="utf-8")
    return path


def test_failure_warning_case_and_capture_are_guarded(tmp_path, capsys):
    path = child(
        tmp_path,
        f"""import pytest, warnings
@pytest.mark.parametrize("value", [0], ids=[{SENTINEL!r}])
def test_invented(value):
    print({SENTINEL!r})
    warnings.warn({SENTINEL!r})
    raise ValueError({SENTINEL!r})
""",
    )
    status = run_checks((path.name,), root=tmp_path, timeout=20)
    output = capsys.readouterr()
    assert status == 1
    assert SENTINEL not in output.out + output.err
    metadata = json.loads(output.out)
    assert metadata["reason"] == "test_failed"
    assert metadata["failed"] == 1
    assert metadata["warnings"] == 1
    assert metadata["ids"] == [safe_test_id(f"{path.name}::test_invented[{SENTINEL}]")]


def test_collection_failure_is_guarded(tmp_path, capsys):
    path = child(tmp_path, f"raise ValueError({SENTINEL!r})\n")
    assert run_checks((path.name,), root=tmp_path, timeout=20) == 2
    output = capsys.readouterr()
    assert SENTINEL not in output.out + output.err
    assert json.loads(output.out)["reason"] == "collection_failed"


def test_timeout_is_guarded(tmp_path, capsys):
    path = child(tmp_path, "import time\ndef test_wait(): time.sleep(10)\n")
    assert run_checks((path.name,), root=tmp_path, timeout=0.1) != 0
    assert json.loads(capsys.readouterr().out)["reason"] == "runner_timeout"


@pytest.mark.parametrize(
    "node",
    [
        "test_safe.py::test_ok",
        "test_safe.py::test_ok[unsafe words]",
        "unsafe words::test_ok",
    ],
    ids=["static", "case", "path"],
)
def test_ids_only_preserve_validated_static_parts(node):
    safe = safe_test_id(node)
    assert "unsafe words" not in safe
    if "[" in node:
        assert "[case-" in safe
    elif "unsafe" in node:
        assert safe.startswith("test-")
    else:
        assert safe == node


def test_passing_child_reports_counts(tmp_path, capsys):
    path = child(tmp_path, "def test_ok(): assert True\n")
    assert run_checks((path.name,), root=tmp_path, timeout=20) == 0
    metadata = json.loads(capsys.readouterr().out)
    assert metadata["passed"] == 1
    assert metadata["failed"] == metadata["warnings"] == 0


def test_parent_refuses_untrusted_metadata(tmp_path, capsys, monkeypatch):
    import subprocess

    from tools import stage10_checks

    def forged(*args, **kwargs):
        metadata_path = Path(kwargs["env"]["STAGE10_METADATA_PATH"])
        metadata = dict.fromkeys(stage10_checks.COUNTS, 0) | {"ids": [SENTINEL]}
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        return subprocess.CompletedProcess(args[0], 1, stdout=SENTINEL, stderr=SENTINEL)

    monkeypatch.setattr(stage10_checks.subprocess, "run", forged)
    assert run_checks(("test_invented.py",), root=tmp_path) == 3
    output = capsys.readouterr()
    assert SENTINEL not in output.out + output.err
    assert json.loads(output.out)["reason"] == "runner_failed"


def test_parent_suppresses_plugin_and_subprocess_exceptions(
    tmp_path, capsys, monkeypatch
):
    from tools import stage10_checks

    def fail(*args, **kwargs):
        raise OSError(SENTINEL)

    monkeypatch.setattr(stage10_checks.subprocess, "run", fail)
    assert run_checks(("test_invented.py",), root=tmp_path) == 3
    output = capsys.readouterr()
    assert SENTINEL not in output.out + output.err
    assert json.loads(output.out)["reason"] == "runner_failed"


def test_unknown_options_never_echo_input(capsys):
    from tools.stage10_checks import main

    assert main([SENTINEL]) == 3
    assert SENTINEL not in capsys.readouterr().out


def test_keyboard_interrupt_is_metadata_only(tmp_path, capsys, monkeypatch):
    from tools import stage10_checks

    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt(SENTINEL)

    monkeypatch.setattr(stage10_checks.subprocess, "run", interrupted)
    assert run_checks(("test_invented.py",), root=tmp_path) == 130
    output = capsys.readouterr()
    assert SENTINEL not in output.out + output.err
    metadata = json.loads(output.out)
    assert metadata["reason"] == "runner_interrupted"
    assert metadata["ids"] == []
    assert all(metadata[name] == 0 for name in stage10_checks.COUNTS)
