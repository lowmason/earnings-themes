"""Canonical JSON and its SHA-256, the one serialization every record hash uses.

Keys are sorted, separators carry no whitespace, and non-ASCII characters are
written as themselves in UTF-8. Dates and datetimes are ISO 8601 strings. A hash
computed here is reproducible from the committed values alone. Moved unchanged from
earnings-ingestion's cohort, so earnings-themes imports the same definition (ES7).
"""

import json
from datetime import date

from pydantic import BaseModel

from earnings_core.hashing import sha256_hex


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
