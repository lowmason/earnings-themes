"""A minimal TOML writer for the harness's generated files (the standard library only reads TOML)."""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class Bare:
    """A TOML value written without quotes (dates and datetimes)."""

    text: str


def toml_value(value: object) -> str:
    if isinstance(value, Bare):
        return value.text
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return repr(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)  # a valid TOML basic string
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    raise TypeError(f"cannot write {type(value).__name__} as TOML")
