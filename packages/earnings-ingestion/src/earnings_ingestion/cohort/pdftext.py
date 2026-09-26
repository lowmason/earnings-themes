"""pdftext-1: the citation text of a saved PDF (plan 6, P6-24).

S&P Dow Jones Indices publishes its index notices as PDFs, and a citation needs text
to point into. Given a PDF's bytes, the policy:

1. reads them with pypdf 6.19.0, holding pypdf's logger below ERROR for the call;
2. takes each page's plain-mode text, in page order;
3. normalizes the text to NFC, never NFKC;
4. collapses each line's whitespace runs to one space and strips its ends, dropping
   the lines left empty;
5. joins every line, across pages, with a newline.

The result is hashed and cited as walker-1's canonical text is: the SHA-256 of its
UTF-8, and half-open code-point offsets into it. pypdf is pinned exactly because its
version defines the policy, so another version's text is ``pdftext-2``. Like this
stage's use of walker-1, the policy produces citation text only, never a
``CanonicalDocument``.

A PDF is data: pypdf runs no script, follows no link, and reaches no network. Its
recovery warnings are silenced, since the text's hash, not the warnings, is the
authority. The policy refuses bytes pypdf cannot read; any encrypted PDF, even one
that an empty password opens, so the text never depends on a decryption attempt; and
a PDF with no text layer, since OCR is out of scope.
"""

import io
import logging
import re
import unicodedata

from pypdf import PdfReader

PDFTEXT_VERSION = "pdftext-1"
_WHITESPACE = re.compile(r"\s+")


class PdfTextError(ValueError):
    """A PDF that has no pdftext-1 text."""


def _pages(body: bytes) -> list[str]:
    """Each page's plain-mode text, with pypdf's logger held below ERROR."""
    logger = logging.getLogger("pypdf")
    level = logger.level
    logger.setLevel(logging.ERROR)
    try:
        reader = PdfReader(io.BytesIO(body))
        if reader.is_encrypted:
            raise PdfTextError(f"{PDFTEXT_VERSION} refuses an encrypted PDF")
        return [page.extract_text(extraction_mode="plain") for page in reader.pages]
    except PdfTextError:
        raise
    except Exception as exc:  # pypdf raises many exception types on malformed bytes
        raise PdfTextError(f"{PDFTEXT_VERSION} cannot read it: {exc}") from exc
    finally:
        logger.setLevel(level)


def pdf_text(body: bytes) -> str:
    """pdftext-1's text of a PDF; ``PdfTextError`` if it has none."""
    text = unicodedata.normalize("NFC", "\n".join(_pages(body)))
    lines = (_WHITESPACE.sub(" ", line).strip() for line in text.splitlines())
    joined = "\n".join(line for line in lines if line)
    if not joined:
        raise PdfTextError(
            f"{PDFTEXT_VERSION} found no text layer; OCR is out of scope"
        )
    return joined
