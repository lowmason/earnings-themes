"""TOML for Stage 6's records and drafts: written here, read with ``tomllib``.

No TOML writer is locked, and GS17 adds no dependency, so ``dumps`` writes the one
shape these records need: scalars, arrays of scalars, tables, and arrays of tables,
in key order. A string is a TOML basic string, written as JSON writes one, which TOML
reads the same way, with DEL escaped as TOML requires.
"""

import json
import re
from collections.abc import Mapping
from datetime import date
from pathlib import Path

import tomllib

from earnings_themes.records import RecordError

_BARE_KEY = re.compile(r"^[A-Za-z0-9_-]+$")


def _string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False).replace(chr(0x7F), chr(0x5C) + "u007f")


def _value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return _string(value)
    if isinstance(value, list | tuple):
        return "[" + ", ".join(_value(item) for item in value) + "]"
    raise TypeError(f"no TOML form for {type(value).__name__}")


def _is_table_array(value: object) -> bool:
    return (
        isinstance(value, list | tuple)
        and bool(value)
        and all(isinstance(item, Mapping) for item in value)
    )


def _lines(data: Mapping[str, object], prefix: str) -> list[str]:
    lines = []
    for key, value in data.items():
        if not _BARE_KEY.match(key):
            raise ValueError(f"{key!r} is not a bare TOML key")
        if value is None or isinstance(value, Mapping) or _is_table_array(value):
            continue
        lines.append(f"{key} = {_value(value)}")
    for key, value in data.items():
        name = f"{prefix}{key}"
        if isinstance(value, Mapping):
            lines += ["", f"[{name}]", *_lines(value, f"{name}.")]
        elif _is_table_array(value):
            for entry in value:
                lines += ["", f"[[{name}]]", *_lines(entry, f"{name}.")]
    return lines


def dumps(data: Mapping[str, object], header: str = "") -> str:
    """``data`` as TOML, after ``header``'s lines as comments; ``None`` is left out."""
    comments = [f"# {line}".rstrip() for line in header.splitlines()]
    body = "\n".join(_lines(data, "")).strip("\n")
    return "\n".join([*comments, body]) + "\n"


def read(path: Path) -> dict:
    """``path`` as TOML; a refusal names the line and column, never the text."""
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        where = f"line {error.lineno}, column {error.colno}"
        raise RecordError(path.name, (f"not TOML at {where}",)) from None
    except UnicodeDecodeError:
        raise RecordError(path.name, ("not UTF-8",)) from None
    except FileNotFoundError:
        raise RecordError(path.name, ("not found",)) from None
