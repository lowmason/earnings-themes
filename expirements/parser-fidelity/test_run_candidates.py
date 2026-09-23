import json
import subprocess
from pathlib import Path

import run_candidates
from run_candidates import Candidate, child_env, run_pair


def fake_runner(outputs):
    """Stand-in for subprocess.run: writes the dump and sidecar an adapter would write."""
    calls = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        dump = command[command.index("--output") + 1]
        sidecar = command[command.index("--sidecar") + 1]
        status, body = outputs[len(calls) - 1]
        if body is not None:
            Path(dump).write_bytes(body)
        side = {"status": status, "python": "3.14.0", "parse_seconds": 0.1}
        if status == "void_network":
            side["guard_trips"] = ["socket.getaddrinfo"]
        Path(sidecar).write_text(json.dumps(side))
        return subprocess.CompletedProcess(command, 0, "", "")

    return runner, calls


def test_identical_dumps_are_deterministic(tmp_path):
    runner, calls = fake_runner([("ok", b"A"), ("ok", b"A")])
    outcome = run_pair(
        Candidate("walker.py", True), tmp_path / "s.html", tmp_path / "out", runner
    )
    assert outcome["deterministic"] is True and outcome["status"] == ["ok", "ok"]
    command, kwargs = calls[0]
    assert command[:4] == ["uv", "run", "--locked", "--script"]
    assert "PYTHONHASHSEED" not in kwargs["env"]


def test_different_dumps_fail_the_determinism_gate(tmp_path):
    runner, _ = fake_runner([("ok", b"A"), ("ok", b"B")])
    assert (
        run_pair(
            Candidate("walker.py", True), tmp_path / "s.html", tmp_path / "out", runner
        )["deterministic"]
        is False
    )


def test_a_guard_trip_is_reported_and_voids_determinism(tmp_path):
    runner, _ = fake_runner([("void_network", None), ("ok", b"A")])
    outcome = run_pair(
        Candidate("adapter_edgartools.py", True),
        tmp_path / "s.html",
        tmp_path / "out",
        runner,
    )
    assert outcome["guard_trips"] == ["socket.getaddrinfo"]
    assert outcome["deterministic"] is False


def test_child_env_drops_pythonhashseed_and_points_edgar_home(monkeypatch):
    monkeypatch.setenv("PYTHONHASHSEED", "0")
    env = child_env()
    assert "PYTHONHASHSEED" not in env
    assert env["EDGAR_LOCAL_DATA_DIR"].endswith("edgar-home")


def test_fixture_runs_refuse_until_freeze_and_gold_are_ready(tmp_path, monkeypatch):
    folder = tmp_path / "0001234567-25-000123_ex-99-1"
    folder.mkdir()
    (folder / "source.html").write_text("<p>x</p>")
    monkeypatch.setattr(
        run_candidates,
        "verify",
        lambda harness, freeze_file: ["FROZEN.toml is missing"],
    )
    problems = run_candidates.fixture_preconditions(tmp_path)
    assert "FROZEN.toml is missing" in problems
    assert any("gold.toml is missing" in p for p in problems)


def test_child_env_keeps_the_identity_out_of_candidate_runs(monkeypatch):
    monkeypatch.setenv("EDGAR_IDENTITY", "Jane Doe research jane@example.org")
    assert "EDGAR_IDENTITY" not in child_env()
