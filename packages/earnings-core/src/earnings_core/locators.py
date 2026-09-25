"""Span locators: exact text plus the context that singles out one occurrence (R5.4)."""

import re
from typing import Annotated

from pydantic import StringConstraints

from earnings_core._model import ContractModel
from earnings_core.documents import CanonicalDocument, document_integrity_problem
from earnings_core.rejections import Rejection, RejectionReason
from earnings_core.spans import TextSpan

_WORD = re.compile(r"\S+")


class SpanLocator(ContractModel):
    """Exact text with the words just before and after it (R5.4, R7.1).

    Modeled on a text-quote selector: ``prefix`` ends where ``exact`` starts and
    ``suffix`` starts where it ends. Both are empty when ``exact`` occurs once.
    """

    exact: Annotated[str, StringConstraints(min_length=1)]
    prefix: str = ""
    suffix: str = ""


def occurrences(text: str, locator: SpanLocator) -> list[int]:
    """Every start offset of ``exact`` whose surrounding text matches the context.

    Overlapping occurrences count: ``"aa"`` occurs twice in ``"aaa"``.
    """
    found: list[int] = []
    width = len(locator.exact)
    position = text.find(locator.exact)
    while position != -1:
        before = text[max(0, position - len(locator.prefix)) : position]
        after = text[position + width : position + width + len(locator.suffix)]
        if before == locator.prefix and after == locator.suffix:
            found.append(position)
        position = text.find(locator.exact, position + 1)
    return found


def make_locator(document: CanonicalDocument, span: TextSpan) -> SpanLocator:
    """The fewest whole words of context that make ``span``'s occurrence unique.

    Plan decision, 2026-09-25: context grows by one whitespace-delimited word on each
    side at a time, so Stage 10's text-fragment links can reuse it. A word cut by the
    span's edge counts as one word. Full context always suffices, so this terminates.
    """
    text = document.canonical_text
    exact = span.slice_of(text)
    word_starts = [match.start() for match in _WORD.finditer(text, 0, span.start)]
    word_ends = [match.end() for match in _WORD.finditer(text, span.end)]
    words = 0
    while True:
        prefix = _before(text, span.start, word_starts, words)
        suffix = _after(text, span.end, word_ends, words)
        locator = SpanLocator(exact=exact, prefix=prefix, suffix=suffix)
        if occurrences(text, locator) == [span.start]:
            return locator
        words += 1


def resolve_locator(
    document: CanonicalDocument, locator: SpanLocator
) -> TextSpan | Rejection:
    """The one span a locator identifies; never a guess at the first match (R5.4)."""
    problem = document_integrity_problem(document)
    if problem is not None:
        return Rejection(reason=RejectionReason.DOCUMENT_INTEGRITY, detail=problem)
    starts = occurrences(document.canonical_text, locator)
    if not starts:
        return Rejection(
            reason=RejectionReason.LOCATOR_NOT_FOUND,
            detail=f"{locator.exact!r} does not occur with this context",
        )
    if len(starts) > 1:
        return Rejection(
            reason=RejectionReason.AMBIGUOUS_OCCURRENCE,
            detail=f"{locator.exact!r} occurs {len(starts)} times with this context,"
            f" at {starts}",
        )
    return TextSpan(start=starts[0], end=starts[0] + len(locator.exact))


def _before(text: str, start: int, word_starts: list[int], words: int) -> str:
    if words == 0:
        return ""
    if words > len(word_starts):
        return text[:start]
    return text[word_starts[-words] : start]


def _after(text: str, end: int, word_ends: list[int], words: int) -> str:
    if words == 0:
        return ""
    if words > len(word_ends):
        return text[end:]
    return text[end : word_ends[words - 1]]
