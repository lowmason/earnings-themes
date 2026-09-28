"""``release-content/1``: whether an exhibit is its slot's release (the Stage 5 spec,
§Content confirmation; plan 8, P8-9).

An exhibit that ``walker-1`` canonicalized is confirmed when both hold:

- **The period.** Its whole canonical text states the slot's period as
  ``release-id/1`` reads a statement: a full date after "ended" or "ending" that is
  the period end, or a fiscal period that matches the slot's labels, judged only for
  ``Q1``, ``Q2``, ``Q3``, and ``FY`` (``release.states_period``). The whole text is
  read, since a release's tables often carry the date.
- **The announcement.** Its opening, the first 12 heading, paragraph, and list-item
  elements joined by spaces, announces results: "report", "announce", "post", or
  "deliver", in a form the pattern lists, followed within 160 characters, with no
  full stop between, by "results", "earnings", "net income", "net earnings", "net
  loss", "net sales", "revenue", "sales", "profit", or "EPS", in any case.

Stage 1's 168 saved exhibits fixed the vocabulary. It rejects the six that are not
releases, V2's AMC pro forma overview among them, and confirms 156 of the 162
releases; every one of the 168 states some period in its whole text. Stage 1's eight
committed releases and the synthetic exhibits pin it in the default suite.
"""

import re
from dataclasses import dataclass
from datetime import date

from earnings_core import ElementType

from earnings_ingestion.canonical.records import Canonicalized
from earnings_ingestion.events.release import states_period

CONTENT_POLICY = "release-content/1"
OPENING = 12
"""How many heading, paragraph, and list-item elements make the opening."""
_BLOCKS = frozenset({ElementType.HEADING, ElementType.PARAGRAPH, ElementType.LIST_ITEM})
_VERB = (
    r"\b(?:report(?:s|ed|ing)?|announce(?:s|d|ing)?|post(?:s|ed)?|deliver(?:s|ed)?)\b"
)
_NOUN = (
    r"\b(?:results?|earnings|net\s+(?:income|earnings|loss|sales)|revenues?|sales"
    r"|profit|eps)\b"
)
_ANNOUNCES = re.compile(rf"{_VERB}[^.]{{0,160}}?{_NOUN}", re.IGNORECASE)


@dataclass(frozen=True)
class Confirmation:
    period: bool
    """The text states the slot's period."""
    announced: bool
    """The opening announces results."""
    detail: str | None
    """What it lacks; ``None`` when confirmed."""

    @property
    def confirmed(self) -> bool:
        return self.period and self.announced


def opening(result: Canonicalized) -> str:
    """The first ``OPENING`` heading, paragraph, and list-item elements' text."""
    text = result.document.canonical_text
    blocks = [
        text[element.span.start : element.span.end]
        for element in result.elements
        if element.type in _BLOCKS
    ][:OPENING]
    return " ".join(" ".join(block.split()) for block in blocks)


def confirm(
    result: Canonicalized,
    period_end: date,
    fiscal_year: int | None,
    fiscal_period: str | None,
) -> Confirmation:
    """Whether ``result`` is the release of the slot ending ``period_end``, with the
    fiscal labels ``fiscal_year`` and ``fiscal_period``."""
    stated = states_period(
        result.document.canonical_text, period_end, fiscal_year, fiscal_period
    )
    announced = _ANNOUNCES.search(opening(result)) is not None
    lacks = []
    if not stated:
        labelled = fiscal_year is not None and fiscal_period is not None
        also = f", and no {fiscal_period} {fiscal_year}" if labelled else ""
        lacks.append(f"it states no period ended {period_end}{also}")
    if not announced:
        lacks.append("its opening announces no results")
    return Confirmation(stated, announced, "; ".join(lacks) or None)
