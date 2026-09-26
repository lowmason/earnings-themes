"""Sentences S1: in-house rules that prefer under-splitting (Stage 3 spec: Sentences S1).

A sentence that really ends in a listed abbreviation merges with the next one: a longer
pointer quote is safer than a claim cut in half. Any change to these rules or to the
abbreviation list is S2, and so a new canonicalization version.
"""

import re
from collections.abc import Sequence

from earnings_core import CanonicalDocument, DocumentElement, ElementType, TextSpan

from earnings_ingestion.canonical.walker import _FOOTNOTE_MARKER, BULLETS

SPLIT_TYPES = frozenset(
    {ElementType.PARAGRAPH, ElementType.LIST_ITEM, ElementType.FOOTNOTE}
)
ABBREVIATIONS = (
    *("Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "Sr.", "Jr.", "St."),
    *("Inc.", "Corp.", "Co.", "Cos.", "Ltd.", "Bros.", "L.P.", "L.L.C."),
    *("N.A.", "N.V.", "S.A.", "P.C."),
    *("U.S.", "U.K.", "U.N.", "E.U.", "N.Y.", "D.C."),
    *("Jan.", "Feb.", "Mar.", "Apr.", "Jun.", "Jul.", "Aug.", "Sep.", "Sept."),
    *("Oct.", "Nov.", "Dec."),
    *("No.", "Nos.", "vs.", "v.", "approx.", "est.", "e.g.", "i.e.", "etc."),
    *("a.m.", "p.m.", "Fig.", "Vol.", "Ph.D.", "Ave.", "Blvd."),
)
"""Case-sensitive; each must start the text or follow a character that is not a
letter or digit."""

_MARKER = re.compile(rf"(?:[{BULLETS}]|{_FOOTNOTE_MARKER})\s*")
_CANDIDATE = re.compile(
    r"[.!?][\"')\]\N{RIGHT DOUBLE QUOTATION MARK}\N{RIGHT SINGLE QUOTATION MARK}]*"
    r"(?=\s+(\S))"
)
_OPENERS = frozenset(
    "\"'([\N{LEFT DOUBLE QUOTATION MARK}\N{LEFT SINGLE QUOTATION MARK}"
)
_DIGITS = frozenset("0123456789")
_ENUMERATOR = re.compile(r"(?:\d{1,2}|[a-z]|[ivx]{1,4})\.", re.IGNORECASE)
"""W13's enumerators: ``1.``, ``a.``, ``iv.``."""


def sentence_spans(text: str) -> list[tuple[int, int]]:
    """S1's sentences in one unit's text, as ``[start, end)`` offsets into it.

    ``text`` is a block's canonical text, so N1 has collapsed its whitespace. A
    leading W9 bullet glyph or W10 textual marker, with the space after it, belongs to
    no sentence; a unit with nothing after its marker has none. A unit with no
    boundary is one sentence.
    """
    marker = _MARKER.match(text)
    first = marker.end() if marker is not None else 0
    if first == len(text):
        return []
    spans: list[tuple[int, int]] = []
    start = first
    for candidate in _CANDIDATE.finditer(text, first):
        following = candidate.group(1)
        if not (following.isupper() or following in _DIGITS or following in _OPENERS):
            continue
        stop = candidate.start() + 1  # just after the terminal punctuation
        if text[stop - 1] == "." and _continues(text, start, stop, start == first):
            continue
        spans.append((start, candidate.end()))
        start = candidate.start(1)
    spans.append((start, len(text)))
    return spans


def _continues(text: str, start: int, stop: int, opens_the_unit: bool) -> bool:
    """True when the period at ``stop - 1`` ends no sentence."""
    for abbreviation in ABBREVIATIONS:
        begins = stop - len(abbreviation)
        if (
            begins >= 0
            and text.startswith(abbreviation, begins)
            and (begins == 0 or not text[begins - 1].isalnum())
        ):
            return True
    if (
        stop >= 2
        and text[stop - 2].isupper()
        and (stop == 2 or not text[stop - 3].isalpha())
    ):
        return True  # an initial, as in "J.P. Morgan"
    return opens_the_unit and _ENUMERATOR.fullmatch(text, start, stop) is not None


def with_sentences(
    document: CanonicalDocument, elements: Sequence[DocumentElement]
) -> list[DocumentElement]:
    """``elements`` with each paragraph, list item, and footnote followed by its
    sentences, whose parent it is."""
    text = document.canonical_text
    out: list[DocumentElement] = []
    for element in elements:
        out.append(element)
        if element.type not in SPLIT_TYPES:
            continue
        offset = element.span.start
        for start, end in sentence_spans(element.span.slice_of(text)):
            out.append(
                DocumentElement.create(
                    document,
                    ElementType.SENTENCE,
                    TextSpan(start=offset + start, end=offset + end),
                    parent_id=element.element_id,
                    source_type="sentence",
                )
            )
    return out
