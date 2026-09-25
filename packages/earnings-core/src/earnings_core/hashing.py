"""SHA-256 helpers: the one hash every contract uses."""

import hashlib
from typing import Annotated

from pydantic import StringConstraints

Sha256Hex = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
"""A SHA-256 digest written as 64 lowercase hexadecimal characters."""


def sha256_hex(data: bytes) -> str:
    """Return the SHA-256 digest of ``data`` as 64 lowercase hexadecimal characters."""
    return hashlib.sha256(data).hexdigest()


def hash_canonical_text(canonical_text: str) -> str:
    """Hash canonical text as R3.1 defines it: SHA-256 over its UTF-8 bytes.

    Raises ``UnicodeEncodeError`` if the text holds a lone surrogate, which has no
    UTF-8 encoding and so can never be canonical text.
    """
    return sha256_hex(canonical_text.encode("utf-8"))
