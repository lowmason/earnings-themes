"""The committed canonical-fixture format (Stage 3 spec: Canonical fixtures).

One JSON object with sorted keys: ``document``, ``elements``, ``manifest``, and
``masks``. Each record is one line with sorted keys and ASCII escapes, so a diff shows
which elements changed and no editor or tool can alter a character.
``from_fixture_json`` reads the format back, as Stage 6 reads a pilot document's
``data/runs/events/canonical/<doc_id>.json`` (plan 9).
"""

import json
from collections.abc import Iterable

from earnings_core import CanonicalDocument, DocumentElement, OverlayMask, apply_masks
from pydantic import BaseModel

from earnings_ingestion.canonical.records import (
    CanonicalizationManifest,
    Canonicalized,
)

PARTS = ("document", "elements", "manifest", "masks")


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


def from_fixture_json(text: str) -> Canonicalized:
    """The ``Canonicalized`` that ``to_fixture_json`` wrote as ``text``.

    Each record is read through its own contract from its own JSON, since the
    contracts are strict. The masks' policy is the one the manifest records. Any
    refusal is a ``ValueError``; a pydantic error's message holds the input, so a
    caller that reads a pilot document never prints it (plan 9, GS13).
    """
    data = json.loads(text)
    if not isinstance(data, dict) or tuple(sorted(data)) != PARTS:
        raise ValueError(f"a canonical document holds exactly {', '.join(PARTS)}")
    document = CanonicalDocument.model_validate_json(json.dumps(data["document"]))
    manifest = CanonicalizationManifest.model_validate_json(
        json.dumps(data["manifest"])
    )
    masks = tuple(
        OverlayMask.model_validate_json(json.dumps(record)) for record in data["masks"]
    )
    return Canonicalized(
        document=document,
        elements=tuple(
            DocumentElement.model_validate_json(json.dumps(record))
            for record in data["elements"]
        ),
        masked=apply_masks(
            document,
            masks,
            policy_id=manifest.mask_policy_id,
            policy_version=manifest.mask_policy_version,
        ),
        manifest=manifest,
    )
