"""F20's rule for Stage 6's committed files (the Stage 6 spec, §Wording guard; GS3).

No 40-character window of a committed string, with dates masked, may occur in a
release's canonical text, also with dates masked. The rule and its date mask are
``tests/integration/test_corpus_quotes.py``'s. A Markdown file is read a paragraph
at a time, its lines joined, so a phrase copied across a wrapped line is still
caught.

``shared`` names each string by its label and each text by its ID, and returns
those pairs only, never the strings or the texts: a check over pilot documents
must never print their text (GS13).
"""

import re
from collections.abc import Iterable

WIDTH = 40
MONTH = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?"
    r"|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)
DATE = re.compile(rf"\b{MONTH}\.?\s+\d{{1,2}},?\s+\d{{4}}\b")
_BLANK_LINE = re.compile(r"\n\s*\n")


def masked(text: str) -> str:
    """``text`` with each full date replaced by a NUL, which no release holds."""
    return DATE.sub("\0", text)


def labelled_strings(value: object, label: str = "") -> list[tuple[str, str]]:
    """Every string leaf of parsed JSON or TOML, with its path as its label."""
    if isinstance(value, str):
        return [(label or "value", value)]
    if isinstance(value, dict):
        return [
            pair
            for key, item in value.items()
            for pair in labelled_strings(item, f"{label}.{key}" if label else key)
        ]
    if isinstance(value, list | tuple):
        return [
            pair
            for index, item in enumerate(value)
            for pair in labelled_strings(item, f"{label}[{index}]")
        ]
    return []


def markdown_paragraphs(text: str, label: str) -> list[tuple[str, str]]:
    """Each paragraph of a Markdown file, its lines stripped and joined by a space."""
    paragraphs = []
    for number, block in enumerate(_BLANK_LINE.split(text), start=1):
        joined = " ".join(line.strip() for line in block.splitlines() if line.strip())
        if joined:
            paragraphs.append((f"{label} paragraph {number}", joined))
    return paragraphs


def shared(
    strings: Iterable[tuple[str, str]], texts: Iterable[tuple[str, str]]
) -> set[tuple[str, str]]:
    """Each ``(label, text_id)`` where a window of the labelled string occurs in the
    text, both with dates masked."""
    windows: dict[str, set[str]] = {}
    for label, string in strings:
        text = masked(string)
        for start in range(len(text) - WIDTH + 1):
            windows.setdefault(text[start : start + WIDTH], set()).add(label)
    found: set[tuple[str, str]] = set()
    if not windows:
        return found
    for text_id, text in texts:
        text = masked(text)
        for start in range(len(text) - WIDTH + 1):
            labels = windows.get(text[start : start + WIDTH])
            if labels:
                found.update((label, text_id) for label in labels)
    return found
