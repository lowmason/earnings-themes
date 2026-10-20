"""SHA-256 helpers: the one hash every contract uses."""

import hashlib
from typing import Annotated

from pydantic import StringConstraints

Sha256Hex = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
"""A SHA-256 digest written as 64 lowercase hexadecimal characters."""


def sha256_hex(data: bytes) -> str:
    """Return the SHA-256 digest of ``data`` as 64 lowercase hexadecimal characters.

    Parameters
    ----------
    data : bytes
        The bytes to hash.

    Returns
    -------
    str
        The digest, as 64 lowercase hexadecimal characters.
    """
    return hashlib.sha256(data).hexdigest()


def hash_canonical_text(canonical_text: str) -> str:
    """Hash canonical text as R3.1 defines it: SHA-256 over its UTF-8 bytes.

    Raises ``UnicodeEncodeError`` if the text holds a lone surrogate, which has no
    UTF-8 encoding and so can never be canonical text.

    Parameters
    ----------
    canonical_text : str
        The canonical text to hash.

    Returns
    -------
    str
        The SHA-256 digest of the text's UTF-8 bytes, as lowercase hexadecimal.

    Raises
    ------
    UnicodeEncodeError
        If the text holds a lone surrogate.
    """
    return sha256_hex(canonical_text.encode("utf-8"))
