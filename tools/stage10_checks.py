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
    "vertical": (
        "tests/integration/test_theme_vertical_slice.py",
        "tests/integration/test_theme_coverage.py",
        "tests/integration/test_theme_frozen_v0.py",
        "tests/integration/test_theme_wording.py",
    ),
    "browser-unit": (
        "packages/earnings-ingestion/tests/test_browser_evidence_lifecycle.py",
        "packages/earnings-ingestion/tests/test_browser_renderer.py",
        "packages/earnings-ingestion/tests/test_browser_records.py",
        "packages/earnings-ingestion/tests/test_browser_store.py",
        "apps/earnings-pipeline/tests/test_browser_evidence.py",
    ),
    "contracts": (
        "tests/contracts/test_analysis_contracts.py",
        "tests/contracts/test_processing_state_compatibility.py",
        "tests/contracts/test_data_dictionary.py",
        "tests/contracts/test_import_scan.py",
        "tests/contracts/test_support_contracts.py",
        "tests/contracts/test_coding_contracts.py",
        "packages/earnings-themes/tests/test_import_boundaries.py",
        "packages/earnings-ingestion/tests/test_import_boundaries.py",
    ),
    "workflow": (
        "apps/earnings-pipeline/tests/test_theme_config.py",
        "apps/earnings-pipeline/tests/test_theme_workflow.py",
        "apps/earnings-pipeline/tests/test_extract_cli.py",
        "apps/earnings-pipeline/tests/test_cli.py",
    ),
    "export": (
        THEMES + "analysis/test_store.py",
        "apps/earnings-pipeline/tests/test_theme_report.py",
    ),
    "evidence": (
        "apps/earnings-pipeline/tests/test_evidence_views.py",
        "apps/earnings-pipeline/tests/test_browser_evidence.py",
        "packages/earnings-core/tests/test_locators.py",
        "packages/earnings-core/tests/test_evidence.py",
    ),
    "coverage": (
        THEMES + "analysis/test_completion.py",
        THEMES + "analysis/test_coverage.py",
        THEMES + "analysis/test_prevalence.py",
    ),
    "rows": (THEMES + "analysis/test_rows.py", THEMES + "analysis/test_safe_output.py"),
    "states": (
        "packages/earnings-ingestion/tests/test_events_states.py",
        "packages/earnings-ingestion/tests/test_events_state_table.py",
        "tests/contracts/test_processing_state_compatibility.py",
        "tests/integration/test_event_fixtures.py",
        "tests/integration/test_event_corpus_v1.py",
    ),
    "consume": (
        THEMES + "analysis/test_consume.py",
        "tests/contracts/test_support_contracts.py",
        "tests/contracts/test_coding_contracts.py",
    ),
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
GROUPS["upstream"] = (
    *GROUPS["extraction"],
    *(
        THEMES + "support/" + name + ".py"
        for name in (
            "test_allowance",
            "test_assess",
            "test_cache",
            "test_context",
            "test_injection",
            "test_judges",
            "test_metrics",
            "test_nli",
            "test_prompt",
            "test_records",
            "test_resolve",
            "test_run",
            "test_safe_output",
            "test_scorers",
            "test_store",
        )
    ),
    *(
        THEMES + "coding/" + name + ".py"
        for name in (
            "test_adapters",
            "test_assignments",
            "test_cache",
            "test_classify",
            "test_decide",
            "test_injection",
            "test_input",
            "test_prompt",
            "test_records",
            "test_run",
            "test_safe_output",
            "test_store",
        )
    ),
    "tests/integration/test_support_fixtures.py",
    "tests/integration/test_support_wording.py",
    "tests/integration/test_coding_frozen_v0.py",
    "tests/integration/test_coding_wording.py",
)
GROUPS["stage10"] = tuple(
    dict.fromkeys(
        node
        for group, nodes in GROUPS.items()
        if group != "browser-unit"
        for node in nodes
    )
)
USER_GROUPS = {
    "browser-user": (("tests/integration/test_stage10_browser.py",), "browser"),
    "root-user": (("packages", "apps", "tests"), "not live and not browser"),
    "wording-fixture-user": (
        (
            "tests/integration/test_stage6_wording.py::test_no_stage_6_file_quotes_a_stage_1_fixture",
        ),
        "not live and not browser",
    ),
    "wording-pilot-user": (
        (
            "tests/integration/test_stage6_wording.py::test_no_stage_6_file_quotes_a_pilot_document",
        ),
        "not live and not browser",
    ),
}
TIMEOUT_SECONDS = 300
COMBINED_TIMEOUT_SECONDS = 900
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
    nodes: Sequence[str],
    *,
    root: Path = ROOT,
    timeout: float = TIMEOUT_SECONDS,
    marker: str = "not live and not browser",
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
                    marker,
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
    except KeyboardInterrupt:
        emit("runner_interrupted")
        return 130
    except subprocess.TimeoutExpired:
        emit("runner_timeout")
        return 124
    except Exception:  # noqa: BLE001 - never expose child or plugin exceptions
        emit("runner_failed")
        return 3


def main(args: Sequence[str] | None = None) -> int:
    args = sys.argv[1:] if args is None else args
    if len(args) == 2 and args[0] in USER_GROUPS and args[1] == "--user-only":
        nodes, marker = USER_GROUPS[args[0]]
        return run_checks(nodes, marker=marker)
    if len(args) != 1 or args[0] not in GROUPS:
        emit("runner_failed")
        return 3
    return run_checks(
        GROUPS[args[0]],
        timeout=COMBINED_TIMEOUT_SECONDS if args[0] == "stage10" else TIMEOUT_SECONDS,
    )


if __name__ == "__main__":
    raise SystemExit(main())
