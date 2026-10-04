"""Canonical JSON: the one serialization every record hash is computed over (ES7).

Moved from earnings-ingestion's cohort tests with their expectations unchanged. A
local enum and a core model stand in for the cohort's, since core's tests import no
sibling package.
"""

from datetime import UTC, date, datetime
from enum import StrEnum

import pytest
from earnings_core import SpanLocator, canonical_json, digest, sha256_hex


class Action(StrEnum):
    ADDED = "added"


def test_keys_are_sorted_without_whitespace_and_text_stays_utf8() -> None:
    value = {"b": [1, 2], "a": "Soci" + chr(0xE9) + "t" + chr(0xE9)}
    expected = '{"a":"Soci' + chr(0xE9) + "t" + chr(0xE9) + '","b":[1,2]}'
    assert canonical_json(value) == expected.encode("utf-8")
    assert digest(value) == sha256_hex(expected.encode("utf-8"))


def test_dates_and_enums_are_written_as_iso_text_and_values() -> None:
    value = {
        "on": date(2024, 11, 8),
        "at": datetime(2024, 11, 1, 21, 0, tzinfo=UTC),
        "action": Action.ADDED,
    }
    assert canonical_json(value) == (
        b'{"action":"added","at":"2024-11-01T21:00:00+00:00","on":"2024-11-08"}'
    )


def test_a_model_is_dumped_in_json_mode_first() -> None:
    locator = SpanLocator(exact="caf" + chr(0xE9), prefix="the ", suffix=" line")
    assert canonical_json(locator) == canonical_json(locator.model_dump(mode="json"))


def test_a_value_without_a_json_form_is_refused() -> None:
    with pytest.raises(TypeError, match="no canonical JSON form"):
        canonical_json({"x": {1, 2}})
