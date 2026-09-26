"""The committed comparison is what layout1_report.py writes today."""

from layout1_report import REPORT, load_fixtures, render
from layout1_units import load_units


def test_the_committed_comparison_is_current() -> None:
    assert REPORT.read_text(encoding="utf-8") == render(
        load_fixtures(), load_units()
    ), (
        "regenerate: uv run --locked --all-packages python"
        " expirements/parser-fidelity/layout1_report.py"
    )
