"""Metadata-only pytest hooks; no failure, warning, or capture text is serialized."""

import hashlib
import json
import os
import re
from pathlib import Path


def safe_test_id(nodeid: str) -> str:
    base, _, case = nodeid.partition("[")
    path, _, name = base.partition("::")
    if not re.fullmatch(r"[A-Za-z0-9_./-]+", path) or not re.fullmatch(
        r"[A-Za-z0-9_:]+", name
    ):
        return "test-" + hashlib.sha256(nodeid.encode()).hexdigest()[:12]
    suffix = (
        ""
        if not case
        else "[case-" + hashlib.sha256(case.encode()).hexdigest()[:8] + "]"
    )
    return base + suffix


COUNTS = ("passed", "failed", "skipped", "deselected", "warnings", "collection_failed")


class Metadata:
    def __init__(self):
        self.counts = dict.fromkeys(COUNTS, 0)
        self.ids = set()
        self.failed = set()
        self.skipped = set()

    def pytest_runtest_logreport(self, report):
        nodeid = safe_test_id(report.nodeid)
        if report.failed:
            self.failed.add(nodeid)
            self.ids.add(nodeid)
        elif report.skipped:
            self.skipped.add(nodeid)
        elif report.when == "call" and report.passed:
            self.counts["passed"] += 1

    def pytest_collectreport(self, report):
        if report.failed:
            self.counts["collection_failed"] += 1
            self.ids.add(safe_test_id(report.nodeid))

    def pytest_deselected(self, items):
        self.counts["deselected"] += len(items)

    def pytest_warning_recorded(self, warning_message, when, nodeid, location):
        self.counts["warnings"] += 1

    def pytest_sessionfinish(self, session, exitstatus):
        self.counts["failed"] = len(self.failed)
        self.counts["skipped"] = len(self.skipped)
        Path(os.environ["STAGE10_METADATA_PATH"]).write_text(
            json.dumps(self.counts | {"ids": sorted(self.ids)}), encoding="utf-8"
        )


def pytest_configure(config):
    config.pluginmanager.register(Metadata(), "stage10-metadata")
