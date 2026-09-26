"""Boilerplate masks M1-M5, policy ``boilerplate`` version ``1`` (R3.4, SC6).

Masks cover whole headings, paragraphs, list items, and footnotes, one mask per
element, with the category of the first rule that matches, in rule order. Matching is
case-insensitive, over the element's canonical text. Masks never change canonical text,
and masked elements stay in extraction's traversal: excluding them from headline
prevalence is Stage 10's job.
"""

import re
from collections.abc import Sequence

from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    MaskCategory,
    MaskedDocument,
    OverlayMask,
    apply_masks,
)

POLICY_ID = "boilerplate"
POLICY_VERSION = "1"
MASKED_TYPES = frozenset(
    {
        ElementType.HEADING,
        ElementType.PARAGRAPH,
        ElementType.LIST_ITEM,
        ElementType.FOOTNOTE,
    }
)
_SAFE_HARBOR_HEADING = re.compile(
    "forward-looking statements|forward-looking information|safe harbor"
    "|cautionary statement|cautionary note",
    re.IGNORECASE,
)
_NON_GAAP = "non-gaap"


def boilerplate_masks(
    document: CanonicalDocument, elements: Sequence[DocumentElement]
) -> MaskedDocument:
    """M1-M5 over ``elements``, through ``apply_masks``."""
    text = document.canonical_text
    extents = _heading_extents(text, elements)
    masks = []
    for element in elements:
        if element.type not in MASKED_TYPES:
            continue
        block = element.span.slice_of(text)
        category = extents.get(element.element_id) or _block_category(block)
        if category is not None:
            masks.append(
                OverlayMask(
                    doc_id=document.doc_id,
                    canonical_hash=document.canonical_hash,
                    span=element.span,
                    category=category,
                    policy_id=POLICY_ID,
                    policy_version=POLICY_VERSION,
                )
            )
    return apply_masks(
        document, masks, policy_id=POLICY_ID, policy_version=POLICY_VERSION
    )


def _heading_extents(
    text: str, elements: Sequence[DocumentElement]
) -> dict[str, MaskCategory]:
    """M1 and M2: a matching heading, and the narrative blocks after it up to the next
    heading or table. Page artifacts and ``other`` elements are skipped, not stopped
    at; sentences and cells are never blocks."""
    extents: dict[str, MaskCategory] = {}
    active: MaskCategory | None = None
    for element in elements:
        if element.type is ElementType.HEADING:
            active = _heading_category(element.span.slice_of(text))
        elif element.type is ElementType.TABLE:
            active = None
        if active is not None and element.type in MASKED_TYPES:
            extents[element.element_id] = active
    return extents


def _heading_category(heading: str) -> MaskCategory | None:
    if _SAFE_HARBOR_HEADING.search(heading):
        return MaskCategory.SAFE_HARBOR  # M1
    if _NON_GAAP in heading.casefold():
        return MaskCategory.NON_GAAP_DISCLAIMER  # M2
    return None


def _block_category(block: str) -> MaskCategory | None:
    folded = block.casefold()
    if "private securities litigation reform act" in folded or (
        "forward-looking statements" in folded
        and _any(folded, "risks", "uncertainties", "undue reliance", "actual results")
    ):
        return MaskCategory.SAFE_HARBOR  # M3
    if _NON_GAAP in folded and _any(
        folded,
        "in accordance with",
        "substitute for",
        "in isolation",
        "not be considered",
    ):
        return MaskCategory.NON_GAAP_DISCLAIMER  # M4
    if (
        _any(folded, "registered trademark", "trademarks of")
        or ("shall not be deemed" in folded and "filed" in folded)
        or _any(
            folded,
            "does not constitute an offer",
            "where to find it",
            "participants in the solicitation",
        )
    ):
        return MaskCategory.REPEATED_LEGAL  # M5
    return None


def _any(folded: str, *phrases: str) -> bool:
    return any(phrase in folded for phrase in phrases)
