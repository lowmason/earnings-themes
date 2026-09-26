"""The browser diagnostic path's capture side (Stage 3, plan B).

Importing this package loads no browser library: only ``selenium_capture`` imports
Selenium, and only the ``browser-capture`` extra installs it.
"""

from earnings_ingestion.browser.policy import ISOLATED_1, CapturePolicy
from earnings_ingestion.browser.records import (
    BlockedRequest,
    CaptureReason,
    CaptureStatus,
    LayoutBlock,
    LayoutCell,
    LayoutMetadata,
    LayoutRow,
    LayoutRun,
    LayoutTable,
    RenderedCapture,
)
from earnings_ingestion.browser.renderer import (
    BrowserRenderer,
    CaptureEnvironment,
    FakeRenderer,
)
from earnings_ingestion.browser.store import CaptureStore, capture_once

__all__ = [
    "ISOLATED_1",
    "BlockedRequest",
    "BrowserRenderer",
    "CaptureEnvironment",
    "CapturePolicy",
    "CaptureReason",
    "CaptureStatus",
    "CaptureStore",
    "FakeRenderer",
    "LayoutBlock",
    "LayoutCell",
    "LayoutMetadata",
    "LayoutRow",
    "LayoutRun",
    "LayoutTable",
    "RenderedCapture",
    "capture_once",
]
