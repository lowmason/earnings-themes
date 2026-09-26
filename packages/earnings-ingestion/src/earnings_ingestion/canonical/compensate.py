"""Compensation C1-C5: predeclared retypes that change types only, never text.

The rules apply in order to each block's N1 text, and a block retyped by one rule is
not considered by a later one. A retype drops the block's level, which only headings
and list items carry. Compensation never retypes a W14 grid table or a list
container.

C5 was amended at the review gate on 2026-09-25 (docs/verification/walker-1.md): it
never retypes a block the walker typed heading, though a heading still counts toward
its text's occurrences.
"""

import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import replace

from earnings_ingestion.canonical.blocks import Block
from earnings_ingestion.canonical.walker import _NUMERIC_CELL, _YEAR, MAX_HEADING_WORDS

RULES = ("C1", "C2", "C3", "C4", "C5")
RETYPE = {
    "C1": "table",
    "C2": "page_artifact",
    "C3": "page_artifact",
    "C4": "page_artifact",
    "C5": "page_artifact",
}

_RULE_LINE = re.compile(r"[-=_ ]*")
_DOT_LEADER = re.compile(r"\.{4,}")
_NUMERIC_FIELD = re.compile(r"\S {2,}(\S+)$")
_EDGAR_HEADER = re.compile(
    r"^EX-\d+(\.\d+)*\s+\d+\s+\S+\.(htm|html|txt)\b", re.IGNORECASE
)
_PAGE_OF = re.compile(r"^(page\s*)?\d{1,4}\s+of\s+\d{1,4}$", re.IGNORECASE)


def is_pre_table(lines: Sequence[str]) -> bool:
    """C1: a rule line, a dot leader, or a line ending in a numeric field.

    Each line is read without its trailing whitespace. A rule line holds only ``-``,
    ``=``, ``_``, and spaces, with at least three rule characters. A numeric field is
    W15's numeric-looking pattern, set off from earlier text on its line by two or
    more spaces.
    """
    for line in lines:
        line = line.rstrip()
        if _RULE_LINE.fullmatch(line) and sum(char in "-=_" for char in line) >= 3:
            return True
        if _DOT_LEADER.search(line):
            return True
        field = _NUMERIC_FIELD.search(line)
        if field is not None and _NUMERIC_CELL.match(field.group(1)):
            return True
    return False


def compensate(
    blocks: Sequence[Block], rules: Sequence[str] = RULES
) -> tuple[list[Block], dict[str, int]]:
    """The blocks with C1-C5's retypes, and the retype count of every rule.

    ``rules`` narrows the pass to some rules, as the harness's re-score does to isolate
    C1. C5 counts whole-block occurrences before any retype.
    """
    occurrences = Counter(
        block.text for block in blocks if block.text and block.type != "table"
    )
    first = next((index for index, block in enumerate(blocks) if block.text), None)
    retypes = dict.fromkeys(RULES, 0)
    out: list[Block] = []
    for index, block in enumerate(blocks):
        rule = None
        if not block.container and block.type != "table":
            rule = _first_rule(block, index == first, occurrences, rules)
        if rule is not None:
            retypes[rule] += 1
            block = replace(block, type=RETYPE[rule], level=None, retyped_by=rule)
        out.append(block)
    return out, retypes


def _first_rule(
    block: Block, first: bool, occurrences: Counter[str], rules: Sequence[str]
) -> str | None:
    text = block.text
    if "C1" in rules and block.pre_lines is not None and is_pre_table(block.pre_lines):
        return "C1"
    if "C2" in rules and first and _EDGAR_HEADER.match(text):
        return "C2"
    if block.type == "other":  # W8: a bare page number, or a year C3 keeps
        if _YEAR.match(text):
            return None
        return "C3" if "C3" in rules else None
    if "C4" in rules and _PAGE_OF.match(text):
        return "C4"
    if (
        "C5" in rules
        and block.type != "heading"
        and len(text.split()) <= MAX_HEADING_WORDS
        and occurrences[text] >= 3
    ):
        return "C5"
    return None
