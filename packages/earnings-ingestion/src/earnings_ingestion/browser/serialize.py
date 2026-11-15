"""The committed fixture-capture format (plan 5, PB-7).

One JSON object with sorted keys: ``blocks``, ``capture``, and ``tables``. ``capture``
is the record without its layout; each layout block and table is one line. Every line
has sorted keys and ASCII escapes, so a diff shows which blocks changed and no editor
or tool can alter a character.
"""

import json

from earnings_ingestion.browser.records import RenderedCapture


def to_capture_json(capture: RenderedCapture) -> str:
    """``capture`` in the fixture format, ending with a newline."""
    record = capture.model_dump(mode="json")
    layout = record.pop("layout")
    lines = [
        "{",
        f'"blocks": {_rows(layout["blocks"])},',
        f'"capture": {_line(record)},',
        f'"tables": {_rows(layout["tables"])}',
        "}",
    ]
    return "\n".join(lines) + "\n"


def from_capture_json(text: str) -> RenderedCapture:
    """The capture a fixture file holds; its validators recheck both hashes."""
    data = json.loads(text)
    layout = {"blocks": data["blocks"], "tables": data["tables"]}
    return RenderedCapture.model_validate_json(
        json.dumps({**data["capture"], "layout": layout})
    )


def _line(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True)


def _rows(values: list) -> str:
    if not values:
        return "[]"
    return "[\n" + ",\n".join(_line(value) for value in values) + "\n]"
