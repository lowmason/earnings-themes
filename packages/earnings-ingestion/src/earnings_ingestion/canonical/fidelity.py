"""R3.5's comparators: canonical text checked against independent references.

The references come from the rendered source and from the standard library's
``html.parser``, never from lxml or the walker. Every comparison runs in NFC with
whitespace runs collapsed, never in NFKC, which would hide the Unicode and superscript
differences the check exists to find. The comparators count and list; they set no
threshold (R13.1). Stage 5 reruns them on its pilot releases.
"""

import re
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser

from earnings_core import SpanLocator, occurrences

SCALE_PHRASES = ("in millions", "in thousands", "in billions", "except per share")
SUP_CLASSES = (
    "ordinal_suffix",
    "parenthesized_marker",
    "symbol",
    "empty",
    "bare_digits",
    "other",
)
"""R3.5's five classes, and ``other`` for a run that fits none of them."""

_PARENTHESIZED = re.compile(r"\(\$?\d[\d,]*(?:\.\d+)?%?\)")
_W10_MARKER = re.compile(r"\(\d{1,2}\)")
_LEADING_SIGN = re.compile(
    r"(?<![\w.,)])[-+\N{EN DASH}\N{MINUS SIGN}]\$?\d[\d,]*(?:\.\d+)?%?"
)
_ORDINAL = re.compile(r"st|nd|rd|th", re.IGNORECASE)
_MARKER = re.compile(r"(?:\(\s*[0-9A-Za-z]{1,3}\s*\))+")
_ASCII_DIGITS = re.compile(r"[0-9]+")
_WORD = re.compile(r"\S+")


def comparison_space(text: str) -> str:
    """NFC, with every whitespace run collapsed to one space and the ends stripped."""
    return " ".join(unicodedata.normalize("NFC", text).split())


def non_ascii(text: str) -> list[str]:
    """``text``'s non-ASCII characters, in order, repeats included."""
    return [char for char in text if not char.isascii()]


def signed_figures(text: str) -> list[str]:
    """Figures written with a sign: parentheses, or a leading hyphen, en dash, minus
    sign, or plus.

    ``(1)`` to ``(99)`` are W10's footnote markers, so they are not figures. A hyphen
    after a letter, digit, or closing parenthesis joins a range, not a sign.
    """
    parenthesized = [
        figure
        for figure in _PARENTHESIZED.findall(text)
        if not _W10_MARKER.fullmatch(figure)
    ]
    return parenthesized + _LEADING_SIGN.findall(text)


def scale_counts(text: str) -> dict[str, int]:
    """How often each scale phrase occurs in ``text``, case-insensitively."""
    folded = text.casefold()
    return {phrase: folded.count(phrase) for phrase in SCALE_PHRASES}


@dataclass(frozen=True)
class SourceText:
    """A source's visible text as ``html.parser`` reads it, in comparison space, with
    the ``[start, end)`` extent of every outermost ``<sup>`` run."""

    text: str
    sup_runs: tuple[tuple[int, int], ...]


class _Reader(HTMLParser):
    _SKIPPED = frozenset({"script", "style", "title"})
    _BREAKS = frozenset(
        {
            "address", "article", "blockquote", "br", "caption", "center", "dd",
            "div", "dl", "dt", "footer", "h1", "h2", "h3", "h4", "h5", "h6",
            "header", "hr", "li", "ol", "p", "pre", "section", "table", "td", "th",
            "tr", "ul",
        }
    )  # fmt: skip

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.chars: list[str] = []
        self.runs: list[tuple[int, int]] = []
        self._space = False
        self._skip = 0
        self._sup = 0
        self._sup_start = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._SKIPPED:
            self._skip += 1
        elif tag in self._BREAKS:
            self._space = True
        elif tag == "sup" and not self._skip:
            if not self._sup:
                self._sup_start = len(self.chars)
            self._sup += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIPPED:
            self._skip = max(0, self._skip - 1)
        elif tag in self._BREAKS:
            self._space = True
        elif tag == "sup" and self._sup:
            self._sup -= 1
            if not self._sup:
                self.runs.append((self._sup_start, len(self.chars)))

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        for char in unicodedata.normalize("NFC", data):
            if char.isspace():
                self._space = True
                continue
            if self._space and self.chars:
                self.chars.append(" ")
            self._space = False
            self.chars.append(char)


def read_source(html: str) -> SourceText:
    """The visible text of decoded HTML, outside ``<script>``, ``<style>``, and
    ``<title>``, with a space at every block boundary, as the canonical text has."""
    reader = _Reader()
    reader.feed(html)
    reader.close()
    text = "".join(reader.chars)
    runs = []
    for start, end in reader.runs:
        while start < end and text[start] == " ":
            start += 1
        runs.append((start, end))
    return SourceText(text=text, sup_runs=tuple(runs))


def classify_run(run: str) -> str:
    """A ``<sup>`` run's class: one of ``SUP_CLASSES``.

    A run of consecutive markers, such as ``(1)(2)``, is a parenthesized marker.
    """
    run = run.strip()
    if not run:
        return "empty"
    if _ORDINAL.fullmatch(run):
        return "ordinal_suffix"
    if _MARKER.fullmatch(run):
        return "parenthesized_marker"
    if _ASCII_DIGITS.fullmatch(run):
        return "bare_digits"
    if not any(char.isalnum() for char in run):
        return "symbol"
    return "other"


def locate_run(canonical: str, source: SourceText, start: int, end: int) -> int | None:
    """Where ``source.text[start:end]`` sits in ``canonical``, or None.

    Both texts are in comparison space. Context from the source grows by one
    whitespace-delimited word on each side at a time, as ``make_locator``'s does (D-4),
    until exactly one occurrence remains; a word cut by the run's edge counts as one
    word. A run that no context singles out is None, never a first match.
    """
    text = source.text
    exact = text[start:end]
    if not exact:
        return None
    word_starts = [match.start() for match in _WORD.finditer(text, 0, start)]
    word_ends = [match.end() for match in _WORD.finditer(text, end)]
    words = 0
    while True:
        prefix, suffix = _context(text, start, end, word_starts, word_ends, words)
        found = occurrences(
            canonical, SpanLocator(exact=exact, prefix=prefix, suffix=suffix)
        )
        if len(found) == 1:
            return found[0]
        if not found or (words > len(word_starts) and words > len(word_ends)):
            return None
        words += 1


def _context(
    text: str,
    start: int,
    end: int,
    word_starts: list[int],
    word_ends: list[int],
    words: int,
) -> tuple[str, str]:
    if words == 0:
        return "", ""
    prefix = (
        text[:start] if words > len(word_starts) else text[word_starts[-words] : start]
    )
    suffix = text[end:] if words > len(word_ends) else text[end : word_ends[words - 1]]
    return prefix, suffix


def joined_to_text(canonical: str, position: int) -> bool:
    """True when a run located at ``position`` directly follows a letter or digit, as
    a raised "1" after "million" does."""
    return position > 0 and canonical[position - 1].isalnum()
