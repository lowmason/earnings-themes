"""R3.5's comparators: canonical text checked against independent references.

The references come from the rendered source and from the standard library's
``html.parser``, never from lxml or the walker. Every comparison runs in NFC with
whitespace runs collapsed, never in NFKC, which would hide the Unicode and superscript
differences the check exists to find. The comparators count and list; they set no
threshold (R13.1). Stage 5 reruns them on its pilot releases.
"""

import difflib
import re
import unicodedata
from collections.abc import Collection
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


HUNK_CATEGORIES = (
    "unicode",
    "numeric_signs",
    "scale",
    "superscripts",
    "footnotes",
    "table_headings",
    "other",
)
"""R3.5's six categories, in the report's order, and ``other`` (plan 5's leg)."""
_SIGN_CHARACTERS = "()+-\N{EN DASH}\N{MINUS SIGN}"
_LEADING_FOOTNOTE = re.compile(
    r"(?:\(\d{1,2}\)|\([a-z]\)|\*{1,3}|[\N{DAGGER}\N{DOUBLE DAGGER}])(?:\s|$)"
)


def token_hunks(canonical: str, rendered: str) -> list[tuple[str, str]]:
    """Each differing hunk of a whitespace-insensitive token diff between the canonical
    text and a browser's text of the same source, both in comparison space, as
    ``(canonical side, rendered side)``; either side may be empty. difflib aligns the
    tokens with its junk heuristic off."""
    left = comparison_space(canonical).split()
    right = comparison_space(rendered).split()
    matcher = difflib.SequenceMatcher(None, left, right, autojunk=False)
    return [
        (" ".join(left[i1:i2]), " ".join(right[j1:j2]))
        for tag, i1, i2, j1, j2 in matcher.get_opcodes()
        if tag != "equal"
    ]


def hunk_category(
    canonical: str,
    rendered: str,
    sup_runs: Collection[str],
    headers: Collection[str],
) -> str:
    """The category of a differing hunk: the first of these tests it passes.

    ``sup_runs`` are the source's non-empty ``<sup>`` run texts and ``headers`` the
    gold's table header texts, all in comparison space.

    1. unicode: a non-ASCII character on either side;
    2. scale: a scale phrase on either side;
    3. superscripts: a side that is a run, or sides equal without spaces where a side
       starts or ends with a run: a raised marker joined or split;
    4. footnotes: a side that starts with a W10 marker;
    5. numeric_signs: a signed figure on either side, or sides equal once
       parentheses, plus, hyphen, en dash, and minus sign are removed;
    6. table_headings: a side inside a header text;
    7. other.
    """
    sides = [side for side in (canonical, rendered) if side]
    if any(non_ascii(side) for side in sides):
        return "unicode"
    if any(any(scale_counts(side).values()) for side in sides):
        return "scale"
    joined = _strip(canonical, " ") == _strip(rendered, " ")
    bare = [side.replace(" ", "") for side in sides]
    if any(side in sup_runs for side in sides) or (
        joined
        and any(
            side.startswith(run) or side.endswith(run)
            for side in bare
            for run in sup_runs
        )
    ):
        return "superscripts"
    if any(_LEADING_FOOTNOTE.match(side) for side in sides):
        return "footnotes"
    if any(signed_figures(side) for side in sides) or _strip(
        canonical, _SIGN_CHARACTERS
    ) == _strip(rendered, _SIGN_CHARACTERS):
        return "numeric_signs"
    if any(side in header for side in sides for header in headers):
        return "table_headings"
    return "other"


def _strip(text: str, characters: str) -> str:
    return "".join(char for char in text if char not in characters)
