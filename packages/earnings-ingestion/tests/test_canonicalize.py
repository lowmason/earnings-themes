"""``canonicalize``: the pipeline, its purity, its manifest, and its failures."""

import builtins
import io
import os
import socket
import sys

import pytest
from earnings_core import (
    SCHEMA_VERSION,
    ElementType,
    MaskCategory,
    Rejection,
    RejectionReason,
    TextOrigin,
    hash_canonical_text,
    sha256_hex,
    validate_elements,
)
from earnings_ingestion.canonical import (
    CANONICALIZATION_VERSION,
    CanonicalizationFailure,
    Canonicalized,
    FailureReason,
    canonicalize,
)
from earnings_ingestion.canonical import pipeline as pipeline_module

RELEASE = (
    b"<html><head><title>Hidden</title></head><body>"
    b"<p>EX-99.1 2 exhibit991.htm EXHIBIT 99.1</p>"
    b"<h1>Acme Reports Results</h1>"
    b"<p>Revenue rose 5%. Margins widened.</p>"
    b"<table><tr><th>Item</th><th>2024</th></tr>"
    b"<tr><td>Net sales</td><td>1,234</td></tr></table>"
    b"<pre>Net sales ........ 1,234\nCost    (56)</pre>"
    b"<h2>Forward-Looking Statements</h2>"
    b"<p>These statements involve risks.</p>"
    b'<p>- 2 -</p><img src="logo.gif">'
    b"</body></html>"
)


def canonical(raw: bytes = RELEASE, media_type: str = "text/html") -> Canonicalized:
    result = canonicalize(raw, source_document_id="acme-q1", media_type=media_type)
    assert isinstance(result, Canonicalized), result
    return result


def failed(raw: bytes, media_type: str = "text/html") -> CanonicalizationFailure:
    result = canonicalize(raw, source_document_id="acme-q1", media_type=media_type)
    assert isinstance(result, CanonicalizationFailure), result
    return result


def test_a_release_becomes_a_valid_canonical_document() -> None:
    result = canonical()
    document = result.document
    assert document.canonical_text == (
        "EX-99.1 2 exhibit991.htm EXHIBIT 99.1\n"
        "Acme Reports Results\n"
        "Revenue rose 5%. Margins widened.\n"
        "Item\t2024\nNet sales\t1,234\n"
        "Net sales ........ 1,234 Cost (56)\n"
        "Forward-Looking Statements\n"
        "These statements involve risks.\n"
        "- 2 -"
    )
    assert document.canonicalization_version == CANONICALIZATION_VERSION == "walker-1"
    assert document.doc_id.startswith("acme-q1@walker-1#")
    assert document.canonical_hash == hash_canonical_text(document.canonical_text)
    assert validate_elements(document, result.elements) == ()
    assert [
        (element.type.value, element.span.slice_of(document.canonical_text))
        for element in result.elements
        if element.type is not ElementType.TABLE_CELL
    ] == [
        ("page_artifact", "EX-99.1 2 exhibit991.htm EXHIBIT 99.1"),
        ("heading", "Acme Reports Results"),
        ("paragraph", "Revenue rose 5%. Margins widened."),
        ("sentence", "Revenue rose 5%."),
        ("sentence", "Margins widened."),
        ("table", "Item\t2024\nNet sales\t1,234"),
        ("table", "Net sales ........ 1,234 Cost (56)"),
        ("heading", "Forward-Looking Statements"),
        ("paragraph", "These statements involve risks."),
        ("sentence", "These statements involve risks."),
        ("page_artifact", "- 2 -"),
    ]
    assert {element.text_origin for element in result.elements} == {TextOrigin.NATIVE}
    assert [
        (mask.category, mask.span.slice_of(document.canonical_text))
        for mask in result.masked.masks
    ] == [
        (MaskCategory.SAFE_HARBOR, "Forward-Looking Statements"),
        (MaskCategory.SAFE_HARBOR, "These statements involve risks."),
    ]


def test_the_manifest_records_how_the_document_was_made() -> None:
    manifest = canonical().manifest
    assert manifest.canonicalization_version == "walker-1"
    assert manifest.components == pipeline_module.COMPONENTS
    assert manifest.source_document_id == "acme-q1"
    assert (manifest.raw_sha256, manifest.raw_bytes) == (
        sha256_hex(RELEASE),
        len(RELEASE),
    )
    assert (manifest.encoding, manifest.encoding_basis) == ("UTF-8", "valid-utf-8")
    assert manifest.element_counts == {
        "heading": 2,
        "page_artifact": 2,
        "paragraph": 2,
        "sentence": 3,
        "table": 2,
        "table_cell": 4,
    }
    assert manifest.image_count == 1
    assert manifest.replacement_characters == 0
    assert manifest.retypes == {"C1": 1, "C2": 1, "C3": 1, "C4": 0, "C5": 0}
    assert manifest.limitations == ("pre_table_without_cells",)
    assert (manifest.mask_policy_id, manifest.mask_policy_version) == (
        "boilerplate",
        "1",
    )
    assert manifest.mask_count == 2
    assert manifest.lxml_version.count(".") == 3
    assert manifest.libxml2_version.count(".") == 2
    assert manifest.python_version == ".".join(map(str, sys.version_info[:3]))
    assert manifest.schema_version == 1


def test_replacement_characters_are_kept_and_counted() -> None:
    result = canonical(b"<p>caf\xef\xbf\xbd and \xef\xbf\xbd</p>")
    assert (
        result.document.canonical_text
        == "caf\N{REPLACEMENT CHARACTER} and \N{REPLACEMENT CHARACTER}"
    )
    assert result.manifest.replacement_characters == 2


def test_a_prose_pre_piece_stays_a_paragraph() -> None:
    result = canonical(b"<pre>Revenue rose in every region.\nMargins widened.</pre>")
    assert result.elements[0].type is ElementType.PARAGRAPH
    assert result.manifest.limitations == ()


@pytest.mark.parametrize(
    "media_type", ["text/html", "text/html; charset=utf-8", "TEXT/HTML", " text/html "]
)
def test_the_media_type_essence_must_be_text_html(media_type: str) -> None:
    canonical(media_type=media_type)


@pytest.mark.parametrize(
    "media_type", ["application/pdf", "text/plain", "application/xhtml+xml", ""]
)
def test_other_media_types_are_refused(media_type: str) -> None:
    failure = failed(RELEASE, media_type=media_type)
    assert failure.reason is FailureReason.UNSUPPORTED_MEDIA_TYPE
    assert failure.raw_sha256 == sha256_hex(RELEASE)
    assert failure.canonicalization_version == "walker-1"
    assert (failure.image_count, failure.rejections) == (None, ())


@pytest.mark.parametrize("raw", [b"", b"   \n "], ids=["empty", "whitespace"])
def test_an_empty_document_fails_to_parse(raw: bytes) -> None:
    failure = failed(raw)
    assert failure.reason is FailureReason.PARSE_FAILED
    assert "Document is empty" in failure.detail


def deep(depth: int, before: str = "") -> bytes:
    body = before + "<div>" * depth + "Deep text." + "</div>" * depth
    return f"<html><body>{body}</body></html>".encode()


def test_nesting_past_libxml2s_depth_limit_fails_rather_than_losing_text() -> None:
    failure = failed(deep(300))
    assert failure.reason is FailureReason.PARSE_FAILED
    assert "Excessive depth" in failure.detail


def test_a_fatal_error_after_a_hundred_errors_is_still_caught() -> None:
    duplicates = "".join(f'<p id="dup">x{index}</p>' for index in range(150))
    assert failed(deep(300, before=duplicates)).reason is FailureReason.PARSE_FAILED


def test_the_deepest_nesting_libxml2_keeps_canonicalizes_at_the_default_limit() -> None:
    limit = sys.getrecursionlimit()
    result = canonical(deep(254))
    assert sys.getrecursionlimit() == limit
    assert result.document.canonical_text == "Deep text."


def test_image_only_input_has_no_native_text() -> None:
    failure = failed(
        b'<html><body><img src="a.png"><p><img src="b.png"></p></body></html>'
    )
    assert failure.reason is FailureReason.NO_NATIVE_TEXT
    assert failure.image_count == 2


def test_text_that_n1_deletes_entirely_is_no_native_text() -> None:
    failure = failed(
        "<p>\N{ZERO WIDTH SPACE}\N{SOFT HYPHEN}</p><ul><li> </li></ul>".encode()
    )
    assert (failure.reason, failure.image_count) == (FailureReason.NO_NATIVE_TEXT, 0)


def test_rejected_elements_fail_with_their_rejections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rejection = Rejection(reason=RejectionReason.CROSSING_ELEMENTS, detail="planted")
    monkeypatch.setattr(pipeline_module, "validate_elements", lambda *_: (rejection,))
    failure = failed(RELEASE)
    assert failure.reason is FailureReason.INVALID_ELEMENTS
    assert failure.rejections == (rejection,)


def test_an_invalid_source_document_id_is_the_callers_error() -> None:
    with pytest.raises(ValueError):
        canonicalize(RELEASE, source_document_id="has space", media_type="text/html")


def test_canonicalization_is_deterministic() -> None:
    assert canonical() == canonical()


def test_canonicalization_uses_no_network_and_no_files(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refuse(*args: object, **kwargs: object) -> object:
        raise AssertionError("canonicalize reached for the network or a file")

    for owner, name in (
        (socket.socket, "connect"),
        (socket.socket, "connect_ex"),
        (socket, "create_connection"),
        (socket, "getaddrinfo"),
        (builtins, "open"),
        (io, "open"),
        (os, "open"),
    ):
        monkeypatch.setattr(owner, name, refuse)
    result = canonical()
    assert result.manifest.image_count == 1


def test_the_records_carry_their_schema_versions() -> None:
    result = canonical()
    assert result.document.schema_version == SCHEMA_VERSION == 2
    assert result.manifest.schema_version == 1
    assert failed(b"").schema_version == 1
