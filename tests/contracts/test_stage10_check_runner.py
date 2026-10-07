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


def test_browser_unit_and_existing_contracts_have_exact_allowlists():
    from tools.stage10_checks import GROUPS

    assert GROUPS.get("browser-unit") == (
        "packages/earnings-ingestion/tests/test_browser_evidence_lifecycle.py",
        "packages/earnings-ingestion/tests/test_browser_renderer.py",
        "packages/earnings-ingestion/tests/test_browser_records.py",
        "packages/earnings-ingestion/tests/test_browser_store.py",
        "apps/earnings-pipeline/tests/test_browser_evidence.py",
    )
    assert GROUPS.get("contracts") == (
        "tests/contracts/test_analysis_contracts.py",
        "tests/contracts/test_processing_state_compatibility.py",
        "tests/contracts/test_data_dictionary.py",
        "tests/contracts/test_import_scan.py",
        "tests/contracts/test_support_contracts.py",
        "tests/contracts/test_coding_contracts.py",
        "packages/earnings-themes/tests/test_import_boundaries.py",
        "packages/earnings-ingestion/tests/test_import_boundaries.py",
    )


def test_user_browser_routes_only_explicit_guard_with_invented_stub(
    monkeypatch, capsys
):
    from tools import stage10_checks

    calls = []
    monkeypatch.setattr(
        stage10_checks, "run_checks", lambda *a, **k: calls.append((a, k)) or 0
    )
    assert stage10_checks.main(["browser-user"]) == 3
    assert calls == []
    assert stage10_checks.main(["browser-user", "--user-only"]) == 0
    assert calls == [
        ((("tests/integration/test_stage10_browser.py",),), {"marker": "browser"})
    ]
    assert "browser-user" not in capsys.readouterr().out


def test_browser_marker_reaches_only_invented_child(tmp_path, capsys):
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\nmarkers = browser: invented marker\n"
    )
    path = child(
        tmp_path, "import pytest\n@pytest.mark.browser\ndef test_ok(): assert True\n"
    )
    assert run_checks((path.name,), root=tmp_path, timeout=20, marker="browser") == 0
    metadata = json.loads(capsys.readouterr().out)
    assert metadata["passed"] == 1 and metadata["deselected"] == 0


def test_task11_groups_are_exact_bounded_and_blind():
    from tools.stage10_checks import GROUPS, USER_GROUPS

    assert GROUPS["vertical"] == (
        "tests/integration/test_theme_vertical_slice.py",
        "tests/integration/test_theme_coverage.py",
        "tests/integration/test_theme_frozen_v0.py",
        "tests/integration/test_theme_wording.py",
    )
    expected = tuple(
        dict.fromkeys(
            node
            for group, nodes in GROUPS.items()
            if group not in ("stage10", "browser-unit")
            for node in nodes
        )
    )
    assert GROUPS["stage10"] == expected
    assert len(expected) == len(set(expected)) == 72
    assert set(USER_GROUPS) == {
        "browser-user",
        "root-user",
        "wording-fixture-user",
        "wording-pilot-user",
    }
    assert all(
        node.endswith(".py")
        and "stage6_wording" not in node
        and "nli_live" not in node
        and "stage10_browser" not in node
        for node in expected
    )
    assert "packages/earnings-themes/tests/support/test_nli.py" in GROUPS["upstream"]


def test_combined_timeout_is_bounded_without_changing_individual_groups(monkeypatch):
    from tools import stage10_checks

    calls = []

    def invented(nodes, *, timeout=stage10_checks.TIMEOUT_SECONDS, **kwargs):
        calls.append((nodes, timeout))
        return 0

    monkeypatch.setattr(stage10_checks, "run_checks", invented)
    assert stage10_checks.main(["stage10"]) == 0
    assert calls == [(stage10_checks.GROUPS["stage10"], 900)]
    calls.clear()
    assert stage10_checks.main(["coverage"]) == 0
    assert calls == [(stage10_checks.GROUPS["coverage"], 300)]
    assert stage10_checks.TIMEOUT_SECONDS == 300
