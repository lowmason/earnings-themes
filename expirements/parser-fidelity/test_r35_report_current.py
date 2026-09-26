"""The committed R3.5 report is what r35_report.py writes today."""

from r35_report import REPORT, count, render
from walker1_report import load_fixtures


def test_the_committed_report_is_current() -> None:
    counts = [count(fixture) for fixture in load_fixtures()]
    assert REPORT.read_text(encoding="utf-8") == render(counts), (
        "regenerate: uv run --locked --all-packages python"
        " expirements/parser-fidelity/r35_report.py"
    )
