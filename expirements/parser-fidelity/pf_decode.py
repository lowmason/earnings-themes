"""Browser-equivalent decoding of saved release bytes.

Every consumer of a fixture's text -- the class tests, the gold validator, the
scorer, and every candidate adapter -- decodes the saved bytes with this one
function, so V2 compares structure rather than charset guessing. The rule follows
what a browser does with a local file, where no HTTP header is available:

1. a byte-order mark;
2. a ``<meta>`` charset declared in the first 1024 bytes (WHATWG label mapping:
   ``iso-8859-1`` and ``us-ascii`` mean windows-1252, a UTF-16 label means UTF-8);
3. UTF-8, when the bytes are valid UTF-8;
4. windows-1252 otherwise.

The annotator confirms per fixture that the browser agreed (``document.characterSet``).
"""

from __future__ import annotations

import codecs
import re
from dataclasses import dataclass

PRESCAN_BYTES = 1024

_META_CHARSET = re.compile(
    rb"""<meta[^>]*?charset\s*=\s*["']?\s*([A-Za-z0-9._:\-]+)""", re.IGNORECASE
)
_WINDOWS_1252_LABELS = frozenset(
    {
        "ansi_x3.4-1968",
        "ascii",
        "cp1252",
        "cp819",
        "csisolatin1",
        "ibm819",
        "iso-8859-1",
        "iso-ir-100",
        "iso8859-1",
        "iso88591",
        "iso_8859-1",
        "iso_8859-1:1987",
        "l1",
        "latin1",
        "us-ascii",
        "windows-1252",
        "x-cp1252",
    }
)
_UTF8_LABELS = frozenset(
    {
        "unicode-1-1-utf-8",
        "unicode11utf8",
        "unicode20utf8",
        "utf-8",
        "utf8",
        "x-unicode20utf8",
        "utf-16",
        "utf-16le",
        "utf-16be",
        "unicode",
        "ucs-2",
        "csunicode",
        "iso-10646-ucs-2",
        "unicodefeff",
        "unicodefffe",
    }
)
_BOMS = (
    (codecs.BOM_UTF8, "utf-8", "UTF-8"),
    (codecs.BOM_UTF16_LE, "utf-16-le", "UTF-16LE"),
    (codecs.BOM_UTF16_BE, "utf-16-be", "UTF-16BE"),
)
# WHATWG windows-1252 is cp1252 plus five bytes Python leaves undefined, which map
# to the C1 controls of the same value.
_CP1252_UNDEFINED = frozenset({0x81, 0x8D, 0x8F, 0x90, 0x9D})
_LATIN1_TO_WINDOWS_1252 = {
    code: bytes([code]).decode("cp1252")
    for code in range(0x80, 0xA0)
    if code not in _CP1252_UNDEFINED
}


@dataclass(frozen=True)
class DecodedHtml:
    text: str
    encoding: str  # the name a browser reports, e.g. "UTF-8" or "windows-1252"
    basis: str  # "bom", "meta", "valid-utf-8", or "default"
    ascii_only: bool  # True when every byte is ASCII, so every encoding agrees


def decode_html_bytes(raw: bytes) -> DecodedHtml:
    ascii_only = raw.isascii()
    for bom, codec, name in _BOMS:
        if raw.startswith(bom):
            text = raw[len(bom) :].decode(codec, errors="replace")
            return DecodedHtml(text, name, "bom", ascii_only)
    match = _META_CHARSET.search(raw[:PRESCAN_BYTES])
    if match is not None:
        decoded = _decode_label(
            raw, match.group(1).decode("ascii").strip().lower(), ascii_only
        )
        if decoded is not None:
            return decoded
    try:
        return DecodedHtml(raw.decode("utf-8"), "UTF-8", "valid-utf-8", ascii_only)
    except UnicodeDecodeError:
        return DecodedHtml(
            decode_windows_1252(raw), "windows-1252", "default", ascii_only
        )


def decode_windows_1252(raw: bytes) -> str:
    return raw.decode("latin-1").translate(_LATIN1_TO_WINDOWS_1252)


def _decode_label(raw: bytes, label: str, ascii_only: bool) -> DecodedHtml | None:
    if label in _WINDOWS_1252_LABELS:
        return DecodedHtml(decode_windows_1252(raw), "windows-1252", "meta", ascii_only)
    if label in _UTF8_LABELS:
        return DecodedHtml(
            raw.decode("utf-8", errors="replace"), "UTF-8", "meta", ascii_only
        )
    try:
        info = codecs.lookup(label)
    except LookupError:
        return None  # a browser ignores an unknown label too
    return DecodedHtml(
        raw.decode(info.name, errors="replace"), info.name, "meta", ascii_only
    )
