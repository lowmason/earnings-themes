"""The fixture-capture format: one block per line, sorted keys, ASCII, exact round trip."""

import json
from collections.abc import Callable
from pathlib import Path

from earnings_core import ArtifactRef, RightsStatus
from earnings_ingestion.browser.fixture import fixture_capture_json
from earnings_ingestion.browser.metadata import parse_metadata
from earnings_ingestion.browser.records import (
    BlockedRequest,
    CaptureReason,
    CaptureStatus,
    RenderedCapture,
)
from earnings_ingestion.browser.serialize import from_capture_json, to_capture_json

CAPTURE_SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "tests"
    / "integration"
    / "capture_browser_fixtures.py"
)

Make = Callable[..., RenderedCapture]


def test_a_capture_round_trips_exactly(make_capture: Make) -> None:
    record = make_capture()
    assert from_capture_json(to_capture_json(record)) == record


def test_the_format_puts_each_block_on_its_own_line(
    make_capture: Make, payload: dict
) -> None:
    text = to_capture_json(make_capture())
    lines = text.splitlines()
    assert lines[0] == "{" and lines[-1] == "}"
    assert lines[1] == '"blocks": ['
    assert json.loads(lines[2]) == payload["blocks"][0]
    assert text.endswith("}\n")
    assert text.isascii()
    assert list(json.loads(text)) == ["blocks", "capture", "tables"]


def test_non_ascii_text_is_escaped(make_capture: Make, payload: dict) -> None:
    payload["blocks"][0]["runs"][0]["text"] = "Caf" + chr(0xE9)
    record = make_capture(
        layout=parse_metadata(payload), rendered_text="Caf" + chr(0xE9)
    )
    text = to_capture_json(record)
    assert text.isascii()
    assert from_capture_json(text) == record


def test_a_fixture_capture_drops_its_screenshots(make_capture: Make) -> None:
    tile = ArtifactRef.for_bytes(
        b"\x89PNG\r\n\x1a\n tile",
        media_type="image/png",
        storage_ref="data/runs/browser-capture/screenshots/tile.png",
        rights_status=RightsStatus.LOCAL_ONLY,
        rights_basis="a rendering of a saved filing, kept local under data/runs/",
    )
    capture = make_capture(screenshots=(tile,))
    kept = from_capture_json(fixture_capture_json(capture))
    assert kept.screenshots == ()
    assert kept == capture.model_copy(update={"screenshots": ()})
    assert capture.screenshots == (tile,)


def test_a_fixture_capture_keeps_everything_but_its_screenshots(
    make_capture: Make,
) -> None:
    tiles = tuple(
        ArtifactRef.for_bytes(
            f"tile {number}".encode(),
            media_type="image/png",
            storage_ref=f"data/runs/browser-capture/screenshots/{number}.png",
            rights_status=RightsStatus.LOCAL_ONLY,
            rights_basis="a rendering of a saved filing, kept local under data/runs/",
        )
        for number in (1, 2)
    )
    blocked = (
        BlockedRequest(
            url="https://example.invalid/site.css",
            resource_type="Stylesheet",
            required=True,
        ),
    )
    changes = {
        "status": CaptureStatus.PARTIAL,
        "reason": CaptureReason.BLOCKED_REQUIRED_RESOURCE,
        "detail": "a stylesheet was blocked",
        "blocked_requests": blocked,
    }
    capture = make_capture(screenshots=tiles, **changes)
    expected = make_capture(**changes)
    assert fixture_capture_json(capture) == to_capture_json(expected)
    assert from_capture_json(fixture_capture_json(capture)).blocked_requests == blocked


def test_a_capture_without_screenshots_has_the_same_fixture_text_either_way(
    make_capture: Make,
) -> None:
    capture = make_capture()
    assert capture.screenshots == ()
    assert fixture_capture_json(capture) == to_capture_json(capture)


def test_the_capture_script_writes_through_fixture_capture_json() -> None:
    text = CAPTURE_SCRIPT.read_text(encoding="utf-8")
    assert "fixture_capture_json(capture)" in text
    assert "to_capture_json(" not in text
