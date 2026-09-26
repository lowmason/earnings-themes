"""The committed R3.5 report is what r35_report.py writes today.

The last section needs the user's local rendered copies, which are never committed:
the first test checks everything before it, and the second, which skips visibly
without the copies, checks the whole report.
"""

import pytest
from r35_report import COPIED, COPIES, REPORT, count, leg2, render
from walker1_report import load_fixtures

REGENERATE = (
    "regenerate: uv run --locked --all-packages python"
    " expirements/parser-fidelity/r35_report.py"
)


def fresh() -> str:
    fixtures = load_fixtures()
    return render([count(f) for f in fixtures], [leg2(f) for f in fixtures])


def test_the_committed_report_is_current_up_to_the_rendered_copies() -> None:
    committed = REPORT.read_text(encoding="utf-8")
    assert committed.split(COPIED)[0] == fresh().split(COPIED)[0], REGENERATE


def test_the_whole_committed_report_is_current_with_the_local_copies() -> None:
    missing = [
        fixture.fixture
        for fixture in load_fixtures()
        if not (COPIES / f"{fixture.fixture}.rendered.txt").is_file()
    ]
    if missing:
        pytest.skip(f"{len(missing)} of the user's local rendered copies are absent")
    assert REPORT.read_text(encoding="utf-8") == fresh(), REGENERATE
