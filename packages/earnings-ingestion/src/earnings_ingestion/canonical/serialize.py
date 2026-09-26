"""The committed canonical-fixture format (Stage 3 spec: Canonical fixtures).

One JSON object with sorted keys: ``document``, ``elements``, ``manifest``, and
``masks``. Each record is one line with sorted keys and ASCII escapes, so a diff shows
which elements changed and no editor or tool can alter a character.
"""

import json
from collections.abc import Iterable

from pydantic import BaseModel

from earnings_ingestion.canonical.records import Canonicalized


def to_fixture_json(result: Canonicalized) -> str:
    """``result`` in the fixture format, ending with a newline."""
    lines = [
        "{",
        f'"document": {_record(result.document)},',
        f'"elements": {_records(result.elements)},',
        f'"manifest": {_record(result.manifest)},',
        f'"masks": {_records(result.masked.masks)}',
        "}",
    ]
    return "\n".join(lines) + "\n"


def _record(model: BaseModel) -> str:
    return json.dumps(model.model_dump(mode="json"), sort_keys=True, ensure_ascii=True)


def _records(models: Iterable[BaseModel]) -> str:
    rows = [_record(model) for model in models]
    if not rows:
        return "[]"
    return "[\n" + ",\n".join(rows) + "\n]"
