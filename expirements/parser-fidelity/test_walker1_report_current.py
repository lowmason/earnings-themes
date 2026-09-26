"""The committed walker-1 report is what walker1_report.py writes today."""

from walker1_report import REPORT, load_fixtures, render


def test_the_committed_report_is_current() -> None:
    assert REPORT.read_text(encoding="utf-8") == render(load_fixtures()), (
        "regenerate: uv run --locked --all-packages python"
        " expirements/parser-fidelity/walker1_report.py"
    )
