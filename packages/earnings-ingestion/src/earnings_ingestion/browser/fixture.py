"""A capture written as a committed fixture: the fixture format, without screenshots.

This lives apart from ``serialize``, which defines the format, because ``serialize`` is
frozen by layout-1's pre-registration (``expirements/parser-fidelity/preregister.py``).
"""

from earnings_ingestion.browser.records import RenderedCapture
from earnings_ingestion.browser.serialize import to_capture_json


def fixture_capture_json(capture: RenderedCapture) -> str:
    """``capture`` in the fixture format, without its screenshots.

    A committed fixture holds no screenshot reference, because a screenshot stays
    local under ``data/runs/``.
    """
    return to_capture_json(capture.model_copy(update={"screenshots": ()}))
