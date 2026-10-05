"""Bound attribution views by the nearest independent section and speaker turn."""

from earnings_core import DocumentElement, ElementType

from earnings_themes.anchoring import Bundle
from earnings_themes.support.problems import SupportError

NARRATIVE_BLOCKS = frozenset(
    {ElementType.PARAGRAPH, ElementType.LIST_ITEM, ElementType.FOOTNOTE}
)


def context_elements(
    bundle: Bundle, quote_element_id: str
) -> tuple[DocumentElement, ...]:
    """Return the preceding in-bound heading, if any, and containing block.

    The resolver validates the bundle first. Walking includes the quote element;
    a narrative ancestor beyond either nearest boundary cannot expand context.
    """
    by_id = {element.element_id: element for element in bundle.elements}
    chain: list[DocumentElement] = []
    current = quote_element_id
    seen: set[str] = set()
    while current is not None:
        if current in seen or current not in by_id:
            raise SupportError("input_changed")
        seen.add(current)
        element = by_id[current]
        chain.append(element)
        current = element.parent_id
    bounds = tuple(
        next((e for e in chain if e.type is kind), None)
        for kind in (ElementType.SECTION, ElementType.SPEAKER_TURN)
    )

    def contained(element: DocumentElement) -> bool:
        return all(
            bound is None or bound.span.contains(element.span) for bound in bounds
        )

    block = next(
        (e for e in chain if e.type in NARRATIVE_BLOCKS and contained(e)), chain[0]
    )
    headings = [
        e
        for e in bundle.elements
        if e.type is ElementType.HEADING
        and e.span.end <= block.span.start
        and contained(e)
    ]
    if not headings:
        return (block,)
    heading = min(headings, key=lambda e: (-e.span.end, -e.span.start, e.element_id))
    return heading, block
