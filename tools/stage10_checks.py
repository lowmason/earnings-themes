"""Run reviewed pytest nodes behind a captured, metadata-only output boundary."""

import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

if __package__:
    from tools.stage10_pytest import COUNTS
else:
    from stage10_pytest import COUNTS

ROOT = Path(__file__).resolve().parents[1]
THEMES = "packages/earnings-themes/tests/"
GROUPS = {
    "records": (
        THEMES + "analysis/test_records.py",
        THEMES + "analysis/test_safe_output.py",
    ),
    "runner": ("tests/contracts/test_stage10_check_runner.py",),
    "dictionary": ("tests/contracts/test_data_dictionary.py",),
    "extraction": tuple(
        THEMES + "test_extraction_" + name + ".py"
        for name in (
            "records",
            "store",
            "window",
            "run",
            "windows",
            "cache",
            "injection",
        )
    ),
}
TIMEOUT_SECONDS = 300
SAFE_ID = re.compile(
    r"(?:test-[a-f0-9]{12}|[A-Za-z0-9_./-]+(?:::[A-Za-z0-9_:]+)?)(?:\[case-[a-f0-9]{8}\])?"
)


def emit(reason=None, metadata=None):
    result = dict.fromkeys(COUNTS, 0) | {"ids": []}
    if metadata is not None:
        result.update(metadata)
    result["reason"] = reason
    print(json.dumps(result, sort_keys=True))


def checked_metadata(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {*COUNTS, "ids"}:
        raise ValueError("runner_failed")
    if any(type(data[key]) is not int or data[key] < 0 for key in COUNTS):
        raise ValueError("runner_failed")
    if not isinstance(data["ids"], list) or any(
        not isinstance(item, str) or SAFE_ID.fullmatch(item) is None
        for item in data["ids"]
    ):
        raise ValueError("runner_failed")
    return data


def run_checks(
    nodes: Sequence[str], *, root: Path = ROOT, timeout: float = TIMEOUT_SECONDS
) -> int:
    """Capture child output; only validated metadata leaves this boundary."""
    try:
        with tempfile.TemporaryDirectory(prefix="stage10-checks-") as temporary:
            metadata_path = Path(temporary) / "result.json"
            env = os.environ.copy()
            env.pop("PYTEST_ADDOPTS", None)
            env.pop("PYTEST_PLUGINS", None)
            env.update(
                {
                    "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
                    "STAGE10_METADATA_PATH": str(metadata_path),
                    "PYTHONPATH": str(ROOT),
                }
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-p",
                    "tools.stage10_pytest",
                    "-p",
                    "pytest_asyncio.plugin",
                    *nodes,
                    "-m",
                    "not live and not browser",
                    "--tb=no",
                    "--show-capture=no",
                    "-q",
                ],
                cwd=root,
                env=env,
                capture_output=True,
                check=False,
                timeout=timeout,
            )
            metadata = checked_metadata(metadata_path)
        reason = None
        if result.returncode:
            reason = (
                "collection_failed"
                if metadata["collection_failed"]
                else ("test_failed" if result.returncode == 1 else "runner_failed")
            )
        emit(reason, metadata)
        return result.returncode
    except subprocess.TimeoutExpired:
        emit("runner_timeout")
        return 124
    except Exception:  # noqa: BLE001 - never expose child or plugin exceptions
        emit("runner_failed")
        return 3


def main(args: Sequence[str] | None = None) -> int:
    args = sys.argv[1:] if args is None else args
    if len(args) != 1 or args[0] not in GROUPS:
        emit("runner_failed")
        return 3
    return run_checks(GROUPS[args[0]])


if __name__ == "__main__":
    raise SystemExit(main())
