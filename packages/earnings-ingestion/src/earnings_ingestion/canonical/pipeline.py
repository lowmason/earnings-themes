"""``canonicalize``: saved release bytes to a canonical document, or a failure.

decode, walk (W0-W16), N1, C1-C5, L1, S1, ``validate_elements``, then M1-M5 under
policy boilerplate/1. The function is pure: no network, no file I/O, no global state
(the recursion limit included), and the same output for the same input.
"""

import platform
from collections import Counter

import lxml.html
from earnings_core import sha256_hex, validate_elements
from lxml import etree

from earnings_ingestion.canonical.blocks import to_blocks
from earnings_ingestion.canonical.boilerplate import (
    POLICY_ID,
    POLICY_VERSION,
    boilerplate_masks,
)
from earnings_ingestion.canonical.build import build
from earnings_ingestion.canonical.compensate import compensate
from earnings_ingestion.canonical.decode import decode_html_bytes
from earnings_ingestion.canonical.records import (
    CanonicalizationFailure,
    CanonicalizationManifest,
    Canonicalized,
    FailureReason,
)
from earnings_ingestion.canonical.sentences import with_sentences
from earnings_ingestion.canonical.walker import walk

CANONICALIZATION_VERSION = "walker-1"
"""The whole policy: any change to canonical text or elements makes it walker-2."""

COMPONENTS = {
    "decoding": "pf_decode@616721a",
    "walker": "W0-W16@616721a",
    "normalization": "N1",
    "compensation": "C1-C5",
    "layout": "L1",
    "sentences": "S1",
}
"""Each component's identifier; the frozen harness commit names the ported code."""

PRE_TABLE_WITHOUT_CELLS = "pre_table_without_cells"
"""Limitation: C1 typed a ``<pre>`` piece as a table, which yields no cell evidence."""

UNREADABLE = (etree.LxmlError, LookupError, ValueError)
"""What decoding, lxml, or the walker raises on input it cannot read: ``parse_failed``.

The ported rules raise these on crafted input: a charset label naming a codec that is
not a text encoding (``LookupError``) or that refuses ``errors="replace"``; a label that
decodes to a lone surrogate, which lxml cannot encode; a span or font weight that
``int()`` refuses. Added after plan 4's final review (docs/verification/walker-1.md).
"""


def canonicalize(
    raw: bytes, *, source_document_id: str, media_type: str
) -> Canonicalized | CanonicalizationFailure:
    """The canonical document for ``raw``, or the reason there is none.

    ``media_type``'s essence must be ``text/html``; parameters, such as a charset, are
    ignored, because decoding follows the ported rule alone. Input that decoding, lxml,
    or the walker cannot read is ``parse_failed``, never an exception. An invalid
    ``source_document_id`` raises ``ValueError``: it is the caller's error, not the
    document's.
    """
    raw_sha256 = sha256_hex(raw)

    def failure(
        reason: FailureReason, detail: str, **evidence: object
    ) -> CanonicalizationFailure:
        return CanonicalizationFailure(
            source_document_id=source_document_id,
            raw_sha256=raw_sha256,
            canonicalization_version=CANONICALIZATION_VERSION,
            reason=reason,
            detail=detail,
            **evidence,
        )

    if media_type.partition(";")[0].strip().lower() != "text/html":
        return failure(
            FailureReason.UNSUPPORTED_MEDIA_TYPE, f"{media_type!r} is not text/html"
        )
    try:
        decoded = decode_html_bytes(raw)
        fatal, image_count = _inspect(decoded.text)
        walked, pre_lines = walk(decoded.text) if fatal is None else ([], {})
    except UNREADABLE as error:
        return failure(FailureReason.PARSE_FAILED, f"{type(error).__name__}: {error}")
    if fatal is not None:
        return failure(FailureReason.PARSE_FAILED, fatal)

    blocks = to_blocks(walked, pre_lines)
    if all(block.container for block in blocks):
        return failure(
            FailureReason.NO_NATIVE_TEXT,
            "no text is left after N1",
            image_count=image_count,
        )
    blocks, retypes = compensate(blocks)
    document, elements = build(
        blocks,
        source_document_id=source_document_id,
        canonicalization_version=CANONICALIZATION_VERSION,
    )
    elements = with_sentences(document, elements)
    rejections = validate_elements(document, elements)
    if rejections:
        return failure(
            FailureReason.INVALID_ELEMENTS,
            f"validate_elements found {len(rejections)} problems",
            rejections=rejections,
        )
    masked = boilerplate_masks(document, elements)
    counts = Counter(element.type.value for element in elements)
    manifest = CanonicalizationManifest(
        canonicalization_version=CANONICALIZATION_VERSION,
        components=dict(COMPONENTS),
        lxml_version=".".join(map(str, etree.LXML_VERSION)),
        libxml2_version=".".join(map(str, etree.LIBXML_VERSION)),
        python_version=platform.python_version(),
        source_document_id=source_document_id,
        raw_sha256=raw_sha256,
        raw_bytes=len(raw),
        encoding=decoded.encoding,
        encoding_basis=decoded.basis,
        element_counts=dict(sorted(counts.items())),
        image_count=image_count,
        replacement_characters=document.canonical_text.count(
            "\N{REPLACEMENT CHARACTER}"
        ),
        retypes=retypes,
        limitations=(PRE_TABLE_WITHOUT_CELLS,) if retypes["C1"] else (),
        mask_policy_id=POLICY_ID,
        mask_policy_version=POLICY_VERSION,
        mask_count=len(masked.masks),
    )
    return Canonicalized(
        document=document, elements=tuple(elements), masked=masked, manifest=manifest
    )


def _inspect(text: str) -> tuple[str | None, int]:
    """libxml2's first fatal error, if any, and the ``<img>`` count.

    The walker parses with a parser it does not expose, so this parse uses its own,
    configured identically: the same bytes, the same explicit encoding. A fatal error,
    such as nesting past libxml2's depth limit, means content was silently dropped.
    """
    parser = lxml.html.HTMLParser(encoding="utf-8")
    root = lxml.html.document_fromstring(text.encode("utf-8"), parser=parser)
    fatal = next(
        (entry for entry in parser.error_log if entry.level == etree.ErrorLevels.FATAL),
        None,
    )
    detail = None
    if fatal is not None:
        detail = f"libxml2: {fatal.message.strip()} (line {fatal.line})"
    return detail, sum(1 for _ in root.iter("img"))
