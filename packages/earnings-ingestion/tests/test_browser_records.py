"""RenderedCapture and its parts: hashes, statuses, and strict closed records (B2)."""

import json
from collections.abc import Callable

import pytest
from earnings_core import sha256_hex
from earnings_ingestion.browser.metadata import parse_metadata
from earnings_ingestion.browser.records import (
    CaptureReason,
    CaptureStatus,
    LayoutMetadata,
    RenderedCapture,
    layout_hash,
)
from earnings_ingestion.browser.renderer import EMPTY_LAYOUT
from pydantic import ValidationError

Make = Callable[..., RenderedCapture]


def test_a_completed_capture_round_trips_through_json(make_capture: Make) -> None:
    record = make_capture()
    assert RenderedCapture.model_validate_json(record.model_dump_json()) == record


def test_the_text_hash_must_be_the_texts(make_capture: Make) -> None:
    with pytest.raises(ValidationError, match="rendered_text_sha256"):
        make_capture(rendered_text_sha256=sha256_hex(b"something else"))


def test_the_layout_hash_must_be_the_layouts(make_capture: Make) -> None:
    with pytest.raises(ValidationError, match="layout_sha256"):
        make_capture(layout_sha256=layout_hash(EMPTY_LAYOUT))


def test_the_layout_hash_ignores_field_order_but_not_values(payload: dict) -> None:
    layout = parse_metadata(payload)
    again = parse_metadata(json.loads(json.dumps(payload, sort_keys=True)))
    assert layout_hash(layout) == layout_hash(again)
    payload["blocks"][0]["runs"][0]["bold"] = True
    assert layout_hash(parse_metadata(payload)) != layout_hash(layout)


def test_a_reason_is_recorded_exactly_when_not_completed(make_capture: Make) -> None:
    with pytest.raises(ValidationError, match="reason"):
        make_capture(reason=CaptureReason.TIMEOUT)
    with pytest.raises(ValidationError, match="reason"):
        make_capture(status=CaptureStatus.FAILED, rendered_text="", layout=EMPTY_LAYOUT)


def test_a_partial_capture_names_a_blocked_required_resource(
    make_capture: Make,
) -> None:
    partial = make_capture(
        status=CaptureStatus.PARTIAL, reason=CaptureReason.BLOCKED_REQUIRED_RESOURCE
    )
    assert partial.status is CaptureStatus.PARTIAL
    with pytest.raises(ValidationError, match="partial"):
        make_capture(status=CaptureStatus.PARTIAL, reason=CaptureReason.TIMEOUT)


@pytest.mark.parametrize("status", [CaptureStatus.FAILED, CaptureStatus.UNAVAILABLE])
def test_a_failure_is_never_an_empty_successful_capture(
    status: CaptureStatus, make_capture: Make
) -> None:
    with pytest.raises(ValidationError, match="holds no rendering"):
        make_capture(status=status, reason=CaptureReason.CAPTURE_FAILURE)
    empty = make_capture(
        status=status,
        reason=CaptureReason.CAPTURE_FAILURE,
        rendered_text="",
        layout=EMPTY_LAYOUT,
    )
    assert empty.layout.blocks == ()


def test_records_are_closed_and_strict(make_capture: Make) -> None:
    with pytest.raises(ValidationError):
        make_capture(unexpected="field")
    with pytest.raises(ValidationError):
        make_capture(viewport_width="1280")


def test_malformed_metadata_is_a_value_error(payload: dict) -> None:
    with pytest.raises(ValueError, match="malformed layout metadata"):
        parse_metadata({"blocks": [{"tag": "p"}], "tables": []})
    with pytest.raises(ValidationError):
        parse_metadata({"blocks": [{**payload["blocks"][0], "x": "8"}], "tables": []})


def test_the_empty_layout_is_empty() -> None:
    assert EMPTY_LAYOUT == LayoutMetadata(blocks=(), tables=())
