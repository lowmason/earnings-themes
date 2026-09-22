"""The two matching spaces for gold anchors (spec: Gold annotation > Matching space).

``primary_space`` is the spec's m(s); ``fallback_space`` is its m2(s). All Stage 1
matching is exact substring search in one of these spaces; nothing is fuzzy.
"""

from __future__ import annotations

import unicodedata


def primary_space(s: str) -> str:
    """m(s): NFKC, then delete whitespace (``str.isspace``) and format characters (Cf)."""
    return "".join(
        ch
        for ch in unicodedata.normalize("NFKC", s)
        if not ch.isspace() and unicodedata.category(ch) != "Cf"
    )


def fallback_space(s: str) -> str:
    """m2(s): NFKD, then keep only letters and digits (L*, N*), which drops combining marks."""
    return "".join(
        ch
        for ch in unicodedata.normalize("NFKD", s)
        if unicodedata.category(ch)[0] in "LN"
    )


def find_all(haystack: str, needle: str) -> list[int]:
    """Start offsets of every occurrence of ``needle``, overlapping occurrences included."""
    if not needle:
        raise ValueError("cannot search for an empty string")
    hits: list[int] = []
    start = haystack.find(needle)
    while start != -1:
        hits.append(start)
        start = haystack.find(needle, start + 1)
    return hits
