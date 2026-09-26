"""Shared test data (plan 5): a small completed capture, its layout payload, and
builders for synthetic layout metadata."""

import copy
from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from earnings_core import sha256_hex
from earnings_ingestion.browser.metadata import METADATA_VERSION, parse_metadata
from earnings_ingestion.browser.policy import ISOLATED_1
from earnings_ingestion.browser.records import (
    CaptureStatus,
    RenderedCapture,
    layout_hash,
)
from earnings_ingestion.browser.renderer import (
    CaptureEnvironment,
    cache_key,
    capture_id,
)

ENVIRONMENT = CaptureEnvironment(
    browser_engine="Chrome for Testing",
    browser_version="154.0.8037.57",
    driver_version="154.0.8037.57",
    selenium_version="4.49.0",
    os_name="Darwin",
    os_version="26.6.2",
    architecture="arm64",
)
PAYLOAD = {
    "blocks": [
        {
            "tag": "p",
            "display": "block",
            "heading_level": None,
            "list_item": False,
            "list_depth": 0,
            "table": None,
            "row": None,
            "cell": None,
            "x": 8,
            "y": 16,
            "width": 1264,
            "height": 18,
            "runs": [
                {
                    "text": "Revenue rose.",
                    "br": False,
                    "visible": True,
                    "bold": False,
                    "underline": False,
                    "superscript": False,
                    "symbol_font": False,
                    "font_size": 16,
                }
            ],
        }
    ],
    "tables": [],
}


def build_capture(**changes: object) -> RenderedCapture:
    layout = changes.pop("layout", parse_metadata(PAYLOAD))
    text = changes.pop("rendered_text", "Revenue rose.")
    raw = b"<p>Revenue rose.</p>"
    key = cache_key(sha256_hex(raw), ISOLATED_1, ENVIRONMENT)
    fields = {
        "capture_id": capture_id("release", ISOLATED_1, key),
        "cache_key": key,
        "source_document_id": "release",
        "raw_sha256": sha256_hex(raw),
        "capture_policy": "isolated",
        "capture_policy_version": "1",
        "metadata_version": METADATA_VERSION,
        "browser_engine": "Chrome for Testing",
        "browser_version": "154.0.8037.57",
        "driver_version": "154.0.8037.57",
        "selenium_version": "4.49.0",
        "os_name": "Darwin",
        "os_version": "26.6.2",
        "architecture": "arm64",
        "viewport_width": 1280,
        "viewport_height": 1024,
        "device_scale_factor": 1,
        "locale": "en-US",
        "timezone": "UTC",
        "font_set": "Darwin 26.6.2 system fonts",
        "document_charset": "UTF-8",
        "script_policy": "disabled",
        "network_policy": "blocked",
        "image_policy": "blocked",
        "missing_resource_policy": "recorded",
        "rendered_text": text,
        "rendered_text_sha256": sha256_hex(text.encode("utf-8")),
        "layout": layout,
        "layout_sha256": layout_hash(layout),
        "screenshots": (),
        "blocked_requests": (),
        "captured_at": datetime(2026, 9, 26, 12, 0, tzinfo=UTC),
        "duration_seconds": 0.8,
        "status": CaptureStatus.COMPLETED,
        "reason": None,
        "detail": "",
    }
    fields.update(changes)
    return RenderedCapture(**fields)


@pytest.fixture
def make_capture() -> Callable[..., RenderedCapture]:
    """A factory: a completed capture of one paragraph, with any field replaced."""
    return build_capture


@pytest.fixture
def payload() -> dict:
    """The layout-metadata script's result for that paragraph, safe to change."""
    return copy.deepcopy(PAYLOAD)


class LayoutParts:
    """Builders for the layout-metadata script's output: runs, blocks, and tables."""

    @staticmethod
    def run(text: str, **style: object) -> dict:
        base = {
            "text": text,
            "br": False,
            "visible": True,
            "bold": False,
            "underline": False,
            "superscript": False,
            "symbol_font": False,
            "font_size": 16,
        }
        return {**base, **style}

    @staticmethod
    def br() -> dict:
        return LayoutParts.run("\n", br=True)

    @staticmethod
    def block(
        *runs: dict,
        tag: str = "p",
        cell: tuple[int, int, int] | None = None,
        **context: object,
    ) -> dict:
        base = {
            "tag": tag,
            "display": "block",
            "heading_level": None,
            "list_item": False,
            "list_depth": 0,
            "table": None if cell is None else cell[0],
            "row": None if cell is None else cell[1],
            "cell": None if cell is None else cell[2],
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 10,
            "runs": list(runs),
        }
        return {**base, **context}

    @staticmethod
    def table(
        *rows: list[int],
        parent: tuple[int, int, int] | None = None,
        head: int = 0,
        th: bool = False,
    ) -> dict:
        """Rows as colspans, one per rendered cell; the first ``head`` rows in thead."""
        return {
            "parent_table": None if parent is None else parent[0],
            "parent_row": None if parent is None else parent[1],
            "parent_cell": None if parent is None else parent[2],
            "rows": [
                {
                    "head": index < head,
                    "cells": [
                        {"header": th, "colspan": span, "rowspan": 1} for span in row
                    ],
                }
                for index, row in enumerate(rows)
            ],
        }

    @staticmethod
    def cells(rows: list[list[str]], table_index: int = 0) -> list[dict]:
        """One ``td`` block per non-empty cell text, in row-major order."""
        return [
            LayoutParts.block(LayoutParts.run(text), tag="td", cell=(table_index, r, c))
            for r, row in enumerate(rows)
            for c, text in enumerate(row)
            if text
        ]


@pytest.fixture
def parts() -> type[LayoutParts]:
    return LayoutParts
