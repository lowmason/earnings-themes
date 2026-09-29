"""What every earnings-themes record shares (Stage 6 spec, GS17).

- **The base.** Records are immutable, closed, and strictly typed, as earnings-core's
  contracts are. A top-level record carries ``schema_version``.
- **Hashing.** A frozen record's content hash is the SHA-256 of its canonical JSON:
  sorted keys, no whitespace, UTF-8. earnings-themes imports only earnings-core, so
  ``canonical_json`` repeats ``earnings_ingestion.cohort.digests``'s form rather than
  importing it.
- **Errors.** A pydantic error's message quotes its input, which may be a release's
  text. ``RecordError`` keeps each problem's field path and message only, never the
  input, so no command prints pilot text (GS13).
"""

import json
from datetime import date
from pathlib import Path
from typing import Annotated, Literal

from earnings_core import sha256_hex
from earnings_core.documents import IdPart
from earnings_core.hashing import Sha256Hex
from pydantic import (
    BaseModel,
    ConfigDict,
    PositiveInt,
    StringConstraints,
    ValidationError,
)

THEMES_SCHEMA_VERSION = 1

NonBlank = Annotated[str, StringConstraints(pattern=r"\S")]
"""A string holding at least one non-space character."""


class Part(BaseModel):
    """A record or a part of one: immutable, closed, strictly typed."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class ThemesRecord(Part):
    """A top-level record, which carries its schema version."""

    schema_version: Literal[1] = THEMES_SCHEMA_VERSION


class Pin(Part):
    """The pilot every Stage 6 record binds to, by content hash (GS2)."""

    pilot_id: IdPart
    pilot_version: PositiveInt
    pilot_hash: Sha256Hex
    events_version: PositiveInt
    events_hash: Sha256Hex
    universe_version: PositiveInt
    universe_operative_hash: Sha256Hex


class RecordError(ValueError):
    """A file that does not read as its record; ``problems`` never quote input."""

    def __init__(self, name: str, problems: tuple[str, ...]) -> None:
        super().__init__(f"{name}: {'; '.join(problems)}")
        self.name = name
        self.problems = problems


def _default(value: object) -> str:
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"{type(value).__name__} has no canonical JSON form")


def canonical_json(value: object) -> bytes:
    """``value`` as canonical JSON bytes; a model is dumped in JSON mode first."""
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    text = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=_default,
    )
    return text.encode("utf-8")


def digest(value: object) -> str:
    """SHA-256 of ``value``'s canonical JSON."""
    return sha256_hex(canonical_json(value))


def record_json(record: BaseModel) -> bytes:
    """Indented JSON with sorted keys, as the corpus records are written."""
    text = json.dumps(
        record.model_dump(mode="json"), indent=1, sort_keys=True, ensure_ascii=False
    )
    return f"{text}\n".encode()


def describe(error: ValidationError) -> tuple[str, ...]:
    """Each problem as its field path and message, without the input; an unknown or
    a refused dict key is redacted as ``<key>``.
    """
    problems = []
    for item in error.errors(include_input=False, include_url=False):
        loc = list(item["loc"])
        if item["type"] == "extra_forbidden" and loc:
            loc[-1] = "<key>"
        if len(loc) >= 2 and loc[-1] == "[key]":
            loc[-2] = "<key>"
        path = ".".join(str(part) for part in loc) or "record"
        problems.append(f"{path}: {item['msg']}")
    return tuple(problems)


def read_json(path: Path) -> object:
    """``path`` as JSON; a refusal names the line, never the text."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise RecordError(path.name, ("not found",)) from None
    except json.JSONDecodeError as error:
        raise RecordError(path.name, (f"not JSON at line {error.lineno}",)) from None


def parse[M: BaseModel](data: object, model: type[M], name: str) -> M:
    """``data`` read as ``model``; a refusal is a ``RecordError`` named ``name``."""
    try:
        return model.model_validate_json(canonical_json(data))
    except ValidationError as error:
        raise RecordError(name, describe(error)) from None


__all__ = [
    "THEMES_SCHEMA_VERSION",
    "IdPart",
    "NonBlank",
    "Part",
    "Pin",
    "RecordError",
    "Sha256Hex",
    "ThemesRecord",
    "canonical_json",
    "describe",
    "digest",
    "parse",
    "read_json",
    "record_json",
]
