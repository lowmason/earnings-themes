"""The committed calibration report is what calibrate.py writes today.

It needs the user's local rendered copies, which are never committed, so it skips
visibly without them.
"""

import pytest
from calibrate import REPORT, calibrate, missing_inputs, render


def test_the_committed_calibration_report_is_current() -> None:
    missing = missing_inputs()
    if missing:
        pytest.skip(f"calibration inputs absent: {', '.join(missing)}")
    assert REPORT.read_text(encoding="utf-8") == render(calibrate()), (
        "regenerate: uv run --locked --all-packages python"
        " expirements/parser-fidelity/calibrate.py"
    )
