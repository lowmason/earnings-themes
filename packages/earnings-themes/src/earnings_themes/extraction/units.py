"""The pointer units of a document, and their blocks (the Stage 7 spec, §Units and
§Windows; ES12).

- **Eligible elements.** A narrative element whose span has a narrative home: no
  table, cell, page artifact, or text-bearing ``other`` element overlaps it (P9-19,
  ES9). R10.1 asks that every one be processed.
- **Units.** The pointer targets: each eligible element that is its own
  ``narrative_home`` and holds no other narrative element that P9-19's order ranks
  before it, that is, one inside it with a shorter span, or with the same span and
  an earlier type. So a sentence is a unit, and the paragraph S1 split into it is
  not; a heading is a unit, since S1 never splits one; and where a sentence and its
  paragraph share one span, the sentence is the unit.
- **Blocks.** A sentence's block is its nearest non-sentence narrative ancestor: a
  paragraph, list item, or footnote. Any other unit is its own block.

Everything here reads element types, spans, and parents, never a unit's text. The
only text read is ``narrative_home``'s whitespace test of a container (ES9), which
ranks and selects nothing (R10.2). Call it on a bundle that ``bundle_problems``
accepts.
"""

from collections.abc import Mapping

from earnings_core import DocumentElement, ElementType

from earnings_themes.anchoring import NARRATIVE, Bundle, narrative_home


def _rank(element: DocumentElement) -> tuple[int, int]:
    """P9-19's order: the shorter span first, then the earlier type in ``NARRATIVE``."""
    return (element.span.length, NARRATIVE.index(element.type))


def eligible(bundle: Bundle) -> tuple[DocumentElement, ...]:
    """The bundle's eligible elements, in its order."""
    return tuple(
        element
        for element in bundle.elements
        if element.type in NARRATIVE
        and isinstance(narrative_home(bundle, element.span), DocumentElement)
    )


def units(bundle: Bundle) -> tuple[DocumentElement, ...]:
    """The bundle's units, in document order (ES12)."""
    candidates = eligible(bundle)
    found = []
    for element in candidates:
        home = narrative_home(bundle, element.span)
        if (
            not isinstance(home, DocumentElement)
            or home.element_id != element.element_id
        ):
            continue
        if any(
            other.element_id != element.element_id
            and element.span.contains(other.span)
            and _rank(other) < _rank(element)
            for other in candidates
        ):
            continue
        found.append(element)
    return tuple(sorted(found, key=lambda element: element.span.start))


def block_of(unit: DocumentElement, by_id: Mapping[str, DocumentElement]) -> str:
    """The element ID of the block that ``unit`` belongs to; ``by_id`` maps each of
    the bundle's element IDs to its element."""
    if unit.type is not ElementType.SENTENCE:
        return unit.element_id
    parent = by_id.get(unit.parent_id) if unit.parent_id is not None else None
    while parent is not None:
        if parent.type in NARRATIVE and parent.type is not ElementType.SENTENCE:
            return parent.element_id
        parent = by_id.get(parent.parent_id) if parent.parent_id is not None else None
    return unit.element_id
