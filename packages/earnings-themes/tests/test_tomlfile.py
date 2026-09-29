"""Stage 6's TOML writer: whatever it writes, tomllib reads back unchanged."""

from datetime import date

import pytest
import tomllib
from earnings_themes.records import IdPart, Part, Pin, RecordError, parse
from earnings_themes.tomlfile import dumps, read

AWKWARD = "".join(
    ['quote " and backslash \\ ', "tab\t", "newline\n", chr(0x7F), chr(0xE9)]
) + chr(0x1F600)


def test_scalars_tables_and_arrays_of_tables_round_trip() -> None:
    data = {
        "event_id": "cik-0009990001:2025-03-31",
        "no_theme": False,
        "count": 3,
        "drafted_on": date(2026, 10, 1),
        "tags": ["a", "b"],
        "empty": [],
        "aid": {"model_id": "m", "drafted_on": date(2026, 10, 2)},
        "themes": [
            {
                "theme_id": "t1",
                "examples": [{"text": "x"}, {"pointer": {"start": 1, "end": 2}}],
            },
            {"theme_id": "t2", "examples": []},
        ],
    }
    assert tomllib.loads(dumps(data)) == data


def test_a_string_round_trips_whatever_it_holds() -> None:
    assert tomllib.loads(dumps({"text": AWKWARD})) == {"text": AWKWARD}


def test_none_is_left_out_and_the_header_is_comments() -> None:
    text = dumps({"a": 1, "b": None}, header="Local draft.\nNever commit.")
    assert text.startswith("# Local draft.\n# Never commit.\n")
    assert tomllib.loads(text) == {"a": 1}


def test_a_key_that_is_not_bare_is_refused() -> None:
    with pytest.raises(ValueError, match="not a bare TOML key"):
        dumps({"a b": 1})


def test_a_file_that_is_not_toml_is_refused_by_position_only(tmp_path) -> None:
    path = tmp_path / "draft.toml"
    path.write_text("claim = 'Revenue rose sharply\n", encoding="utf-8")
    with pytest.raises(RecordError) as refused:
        read(path)
    assert refused.value.problems == ("not TOML at line 2, column 1",)
    assert "Revenue" not in str(refused.value)

    with pytest.raises(RecordError) as extra:
        parse({"a synthetic phrase with spaces": 1}, Pin, "x.toml")
    assert "a synthetic phrase with spaces" not in str(extra.value)
    assert "<key>" in str(extra.value)

    class WithItems(Part):
        items: dict[IdPart, int]

    with pytest.raises(RecordError) as bad_key:
        parse({"items": {"another synthetic key with spaces": 1}}, WithItems, "x.toml")
    assert "another synthetic key with spaces" not in str(bad_key.value)
    assert "<key>" in str(bad_key.value)


def test_a_missing_file_is_refused_by_name(tmp_path) -> None:
    with pytest.raises(RecordError) as caught:
        read(tmp_path / "codebook.working.toml")
    assert (caught.value.name, caught.value.problems) == (
        "codebook.working.toml",
        ("not found",),
    )
