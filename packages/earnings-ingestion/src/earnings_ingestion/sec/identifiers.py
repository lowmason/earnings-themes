"""SEC Central Index Keys: 10-character zero-padded text in every record (A §264).

``pad_cik`` makes the canonical form from any representation SEC serves, and
``unpad_cik`` makes the unpadded form that EDGAR's archive paths use.
"""

import re
from typing import Annotated

from pydantic import StringConstraints

Cik = Annotated[str, StringConstraints(pattern=r"^[0-9]{10}$")]
"""A CIK written as exactly 10 ASCII decimal digits, zero-padded. ``\\d`` would also
admit other scripts' digits, such as fullwidth or Arabic-Indic ones."""

_DIGITS = re.compile(r"^[0-9]{1,10}$")


def pad_cik(value: int | str) -> str:
    """The 10-character zero-padded form; ``ValueError`` if ``value`` is no CIK."""
    text = "" if isinstance(value, bool) else str(value).strip()
    if not _DIGITS.match(text) or int(text) == 0:
        raise ValueError(f"not a CIK: {value!r}")
    return text.zfill(10)


def unpad_cik(cik: str) -> str:
    """The unpadded form, for EDGAR archive paths."""
    return str(int(pad_cik(cik)))
