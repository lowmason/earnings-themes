"""Company-name tokens, and the one matching rule the cohort uses (plan 6, P6-8).

A cited name is *covered* by another name when every token of the cited name,
legal forms and connectives dropped, is a token of the other. There is no fuzzy
score: a name either is covered or is not, and anything else is a reviewer's call,
recorded as an override.
"""

import re
import unicodedata

DROPPED = frozenset(
    {
        "and",
        "co",
        "companies",
        "company",
        "corp",
        "corporation",
        "inc",
        "incorporated",
        "limited",
        "llc",
        "ltd",
        "plc",
        "the",
    }
)
_PARENTHETICAL = re.compile(r"\([^)]*\)")
_TOKEN = re.compile(r"[a-z0-9]+")


def tokens(name: str) -> frozenset[str]:
    """``name``'s tokens: case-folded ASCII words, parentheticals and apostrophes
    removed, split at any other non-alphanumeric character."""
    folded = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    folded = _PARENTHETICAL.sub(" ", folded).casefold()
    folded = folded.replace("'", "").replace("&", " and ")
    return frozenset(_TOKEN.findall(folded))


def covered(cited: str, other: str) -> bool:
    """True when every significant token of ``cited`` is a token of ``other``."""
    significant = tokens(cited) - DROPPED
    return bool(significant) and significant <= tokens(other)
