"""The fixture-capture format: one block per line, sorted keys, ASCII, exact round trip."""

import json
from collections.abc import Callable

from earnings_ingestion.browser.metadata import parse_metadata
from earnings_ingestion.browser.records import RenderedCapture
from earnings_ingestion.browser.serialize import from_capture_json, to_capture_json

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
