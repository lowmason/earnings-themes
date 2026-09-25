"""A small, fully structured call transcript shared by the earnings-core tests.

Two sections, four speaker turns, and a sentence the CEO and the CFO both say, over
text with a euro sign, an emoji outside the Basic Multilingual Plane, and an accent.
The three are written as escapes so no editor can silently normalize them.
"""

from dataclasses import dataclass

import pytest
from earnings_core.documents import CanonicalDocument
from earnings_core.elements import DocumentElement, ElementType
from earnings_core.evidence import SpanCandidate
from earnings_core.locators import make_locator
from earnings_core.spans import TextSpan

EURO = "\u20ac"
CHART = "\U0001f4c8"  # outside the Basic Multilingual Plane: two UTF-16 code units
E_ACUTE = "\u00e9"  # precomposed (NFC)
REVENUE = f"Revenue rose 5% to {EURO}2.1 billion {CHART}."
LINES = (
    "Prepared remarks",
    "Operator: Welcome to the call.",
    f"CEO: {REVENUE} Results are preliminary.",
    "Questions and answers",
    f"Analyst: How did the caf{E_ACUTE} segment do?",
    "CFO: Results are preliminary. Margins held at last year's level.",
)
SAMPLE_TEXT = "\n".join(LINES) + "\n"


@dataclass(frozen=True)
class Sample:
    document: CanonicalDocument
    elements: tuple[DocumentElement, ...]

    @property
    def text(self) -> str:
        return self.document.canonical_text

    def span_of(self, needle: str, occurrence: int = 0) -> TextSpan:
        """The span of one occurrence of ``needle``; occurrence 0 is the first."""
        start = -1
        for _ in range(occurrence + 1):
            start = self.text.index(needle, start + 1)
        return TextSpan(start=start, end=start + len(needle))

    def element(
        self, element_type: ElementType, needle: str, occurrence: int = 0
    ) -> DocumentElement:
        """The element of ``element_type`` that holds that occurrence of ``needle``."""
        span = self.span_of(needle, occurrence)
        return next(
            element
            for element in self.elements
            if element.type is element_type and element.span.contains(span)
        )

    def innermost(self, span: TextSpan) -> DocumentElement:
        """The smallest element that contains ``span``."""
        holders = [element for element in self.elements if element.span.contains(span)]
        return min(holders, key=lambda element: element.span.length)

    def candidate(
        self, needle: str, occurrence: int = 0, **changes: object
    ) -> SpanCandidate:
        """A valid candidate for one occurrence of ``needle``, with ``changes`` applied.

        It is attributed to the innermost element holding it, and carries the context
        ``make_locator`` chooses.
        """
        span = self.span_of(needle, occurrence)
        locator = make_locator(self.document, span)
        fields: dict[str, object] = {
            "doc_id": self.document.doc_id,
            "canonical_hash": self.document.canonical_hash,
            "start": span.start,
            "end": span.end,
            "quote_text": needle,
            "element_id": self.innermost(span).element_id,
            "prefix": locator.prefix,
            "suffix": locator.suffix,
        }
        fields.update(changes)
        return SpanCandidate(**fields)

    def raw(self, needle: str, occurrence: int = 0, **changes: object) -> dict:
        """That valid candidate as a decoded JSON object, with ``changes`` applied."""
        return {**self.candidate(needle, occurrence).model_dump(), **changes}


def build_sample() -> Sample:
    document = CanonicalDocument.create(
        source_document_id="sample-call",
        canonicalization_version="test-1",
        canonical_text=SAMPLE_TEXT,
    )
    line_spans: list[TextSpan] = []
    start = 0
    for line in LINES:
        line_spans.append(TextSpan(start=start, end=start + len(line)))
        start += len(line) + 1
    elements: list[DocumentElement] = []

    def add(
        element_type: ElementType,
        span: TextSpan,
        parent: DocumentElement | None = None,
        level: int | None = None,
    ) -> DocumentElement:
        element = DocumentElement.create(
            document,
            element_type,
            span,
            parent_id=None if parent is None else parent.element_id,
            level=level,
        )
        elements.append(element)
        return element

    def sentence(turn: DocumentElement, text: str) -> None:
        start = SAMPLE_TEXT.index(text, turn.span.start)
        add(ElementType.SENTENCE, TextSpan(start=start, end=start + len(text)), turn)

    for first in (0, 3):
        heading, *turn_lines = line_spans[first : first + 3]
        section = add(
            ElementType.SECTION,
            TextSpan(start=heading.start, end=turn_lines[-1].end),
            level=1,
        )
        add(ElementType.HEADING, heading, section, level=1)
        turns = [add(ElementType.SPEAKER_TURN, span, section) for span in turn_lines]
        if first == 0:
            sentence(turns[1], REVENUE)
            sentence(turns[1], "Results are preliminary.")
        else:
            sentence(turns[1], "Results are preliminary.")
            sentence(turns[1], "Margins held at last year's level.")
    return Sample(document=document, elements=tuple(elements))


@pytest.fixture(scope="session")
def sample() -> Sample:
    return build_sample()
