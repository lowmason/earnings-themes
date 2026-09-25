"""Position-mapped matching-space text, and the validator's independent document text.

``build_space_text`` joins a dump's element texts in one matching space and remembers,
for every character of the result, which element and which offset it came from, so
the scorer can compare positions as (element index, offset within the element).

``extract_document_text`` is the gold validator's own extraction: the standard
library's ``html.parser``, independent of every candidate.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Literal

from pf_space import fallback_space, primary_space

Space = Literal["primary", "fallback"]
_SPACES: dict[str, Callable[[str], str]] = {
    "primary": primary_space,
    "fallback": fallback_space,
}


@dataclass(frozen=True)
class SpaceText:
    text: str
    origins: tuple[
        tuple[int, int], ...
    ]  # per character: (piece index, offset in piece)


def build_space_text(pieces: Sequence[str], space: Space) -> SpaceText:
    to_space = _SPACES[space]
    chars: list[str] = []
    origins: list[tuple[int, int]] = []
    for index, piece in enumerate(pieces):
        for offset, form in _map_piece(piece, to_space):
            chars.append(form)
            origins.extend((index, offset) for _ in form)
    return SpaceText("".join(chars), tuple(origins))


def _clusters(piece: str) -> Iterator[tuple[int, str]]:
    """Split before every character with canonical combining class 0."""
    start = 0
    for index in range(1, len(piece) + 1):
        if index == len(piece) or unicodedata.combining(piece[index]) == 0:
            yield start, piece[start:index]
            start = index


def _map_piece(piece: str, to_space: Callable[[str], str]) -> list[tuple[int, str]]:
    mapped = [(offset, to_space(cluster)) for offset, cluster in _clusters(piece)]
    whole = to_space(piece)
    if "".join(form for _, form in mapped) != whole:
        # Normalization composed across a cluster boundary (Hangul jamo, some Indic
        # vowel signs). Matching stays exact; positions fall back to the piece start.
        return [(0, whole)]
    return mapped


class _DocumentText(HTMLParser):
    _SKIPPED = frozenset({"script", "style", "title"})
    _HEAD_CONTENT = frozenset(
        {"base", "link", "meta", "noscript", "script", "style", "template", "title"}
    )

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0
        self._in_head = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "head":
            self._in_head = True
        elif tag == "body" or (self._in_head and tag not in self._HEAD_CONTENT):
            self._in_head = (
                False  # a body tag, or body content, closes an unclosed head
            )
        if tag in self._SKIPPED:
            self._skip_depth += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "body" or (self._in_head and tag not in self._HEAD_CONTENT):
            self._in_head = False

    def handle_endtag(self, tag: str) -> None:
        if tag == "head":
            self._in_head = False
        elif tag in self._SKIPPED and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_head and data.strip():
            self._in_head = False  # text in an unclosed head starts the body
        if not self._in_head:
            self.parts.append(data)


def extract_document_text(html: str, joiner: str = "") -> str:
    """All text outside ``<head>``, ``<script>``, and ``<style>``, entities decoded.

    ``joiner`` goes between text chunks; the validator keeps the default, which adds nothing.
    """
    parser = _DocumentText()
    parser.feed(html)
    parser.close()
    return joiner.join(parser.parts)
