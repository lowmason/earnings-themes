"""The canonical-fixture format: fixed, ASCII, one record per line, and lossless."""

import json

from earnings_core import CanonicalDocument, DocumentElement, OverlayMask
from earnings_ingestion.canonical import (
    CanonicalizationManifest,
    Canonicalized,
    canonicalize,
)
from earnings_ingestion.canonical.serialize import to_fixture_json

E_ACUTE, EN_DASH = chr(0x00E9), chr(0x2013)
RAW = (
    "<h2>Forward-Looking Statements</h2><p>Revenue rose. We may be wrong.</p>"
    f"<p>Caf{E_ACUTE} {EN_DASH} r{E_ACUTE}sum{E_ACUTE}</p>"
).encode()


def result(raw: bytes = RAW) -> Canonicalized:
    made = canonicalize(raw, source_document_id="doc-1", media_type="text/html")
    assert isinstance(made, Canonicalized)
    return made


def test_the_format_is_one_record_per_line_under_sorted_keys() -> None:
    made = result()
    lines = to_fixture_json(made).splitlines()
    assert lines[0] == "{"
    assert lines[1].startswith('"document": {"canonical_hash": ')
    assert lines[2] == '"elements": ['
    assert made.masked.masks
    assert len(lines) == 8 + len(made.elements) + len(made.masked.masks)
    assert lines[-1] == "}"
    assert [line.split('"', 2)[1] for line in lines if line.startswith('"')] == [
        "document",
        "elements",
        "manifest",
        "masks",
    ]


def test_the_format_is_ascii_and_ends_with_a_newline() -> None:
    text = to_fixture_json(result())
    assert text.isascii()
    assert text.endswith("}\n")
    assert json.dumps(E_ACUTE)[1:-1] in text


def test_no_masks_is_an_empty_list() -> None:
    text = to_fixture_json(result(b"<p>Revenue rose.</p>"))
    assert '"masks": []\n}' in text


def test_every_record_reads_back_through_its_contract() -> None:
    made = result()
    data = json.loads(to_fixture_json(made))
    assert (
        CanonicalDocument.model_validate_json(json.dumps(data["document"]))
        == made.document
    )
    assert (
        tuple(
            DocumentElement.model_validate_json(json.dumps(record))
            for record in data["elements"]
        )
        == made.elements
    )
    assert (
        tuple(
            OverlayMask.model_validate_json(json.dumps(record))
            for record in data["masks"]
        )
        == made.masked.masks
    )
    assert (
        CanonicalizationManifest.model_validate_json(json.dumps(data["manifest"]))
        == made.manifest
    )


def test_the_same_result_serializes_to_the_same_bytes() -> None:
    assert to_fixture_json(result()) == to_fixture_json(result())
