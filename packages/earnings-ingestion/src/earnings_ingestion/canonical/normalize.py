"""Normalization N1: NFC, deletion of named invisible characters, whitespace collapse.

N1 never applies a compatibility mapping (NFKC) and never folds dashes, minus signs,
quotes, apostrophes, digits, or case: R3.5 checks exactly those characters.
"""

import unicodedata

DELETED = frozenset(
    "\N{SOFT HYPHEN}\N{ZERO WIDTH SPACE}\N{WORD JOINER}\N{ZERO WIDTH NO-BREAK SPACE}"
)
"""U+00AD, U+200B, U+2060, and U+FEFF, which N1 deletes wherever they occur."""


def normalize(text: str) -> str:
    """N1 over one block or cell text; an empty result drops the unit (N1 step 4).

    The steps run in the spec's order: NFC, then deletion, then collapse. A deleted
    character between a base letter and a combining mark leaves the two uncomposed.
    """
    composed = unicodedata.normalize("NFC", text)
    kept = "".join(
        char
        for char in composed
        if char not in DELETED
        and not (unicodedata.category(char) == "Cc" and not char.isspace())
    )
    return " ".join(kept.split())
