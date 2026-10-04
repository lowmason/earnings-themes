"""Exact spans for Stage 6's quotes and codebook examples (the Stage 6 spec,
§Anchoring and validation; GS11, GS15).

- **The anchor.** A draft names a quote by its text, with the words around it when
  the text repeats. The text must occur exactly once with that context. Its span is
  attributed to ``narrative_home``, the most specific narrative element that holds
  it, and the span is then built through ``parse_span_candidate`` and checked by
  ``validate_span``: code is the authority on exactness, and no offset comes from a
  browser.
- **Narrative only.** A quote never overlaps a ``table``, ``table_cell``,
  ``page_artifact``, or ``other`` element (R4.2, GS15), except a transparent
  container: an ``other`` element with children and no non-space character outside
  them, which walker-1 makes from a list (ES9). A quote under a boilerplate mask is
  allowed, and its masks are recorded.
- **The committed pointer.** Offsets, the element, and hashes, never text: the
  quote's SHA-256, and, when the text repeats, the SHA-256 of ``make_locator``'s
  prefix and suffix (GS3). The check recomputes each from the local document.

Every refusal is a reason, never a detail: ``Rejection.detail`` may quote the text.
"""

import json
from dataclasses import dataclass
from typing import Self

from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    OverlayMask,
    Rejection,
    RejectionReason,
    SpanLocator,
    TextSpan,
    VerifiedSpan,
    make_locator,
    occurrences,
    parse_span_candidate,
    sha256_hex,
    validate_elements,
    validate_span,
)
from pydantic import NonNegativeInt, model_validator

from earnings_themes.problems import Problem
from earnings_themes.records import NonBlank, Part, Sha256Hex

NARRATIVE = (
    ElementType.SENTENCE,
    ElementType.LIST_ITEM,
    ElementType.FOOTNOTE,
    ElementType.HEADING,
    ElementType.PARAGRAPH,
    ElementType.SPEAKER_TURN,
    ElementType.SECTION,
)
"""The elements a quote may sit in, most specific first (R4.2, GS15)."""


@dataclass(frozen=True)
class Bundle:
    """One document to annotate: a pilot event's release, or a Stage 1 fixture."""

    name: str
    document: CanonicalDocument
    elements: tuple[DocumentElement, ...]
    masks: tuple[OverlayMask, ...]


class SpanPointer(Part):
    """Where a quote is, and hashes that recheck it, without its text."""

    start: NonNegativeInt
    end: NonNegativeInt
    element_id: NonBlank
    quote_sha256: Sha256Hex
    context_sha256: Sha256Hex | None = None
    mask_ids: tuple[NonBlank, ...] = ()

    @model_validator(mode="after")
    def _start_before_end(self) -> Self:
        if self.start >= self.end:
            raise ValueError(f"span [{self.start}, {self.end}) is empty or reversed")
        return self


def mask_id(mask: OverlayMask) -> str:
    """A mask's ID, derived as an element's is: its category and span."""
    return f"{mask.category.value}-{mask.span.start}-{mask.span.end}"


def quote_hash(text: str) -> str:
    """The SHA-256 of a quote's UTF-8 text."""
    return sha256_hex(text.encode("utf-8"))


def context_hash(prefix: str, suffix: str) -> str:
    """The SHA-256 of a locator's prefix and suffix, as a compact two-item JSON array
    in UTF-8 with ``ensure_ascii=False``: the byte format the committed gold stores,
    which a known-answer test pins (T6-M3)."""
    pair = json.dumps([prefix, suffix], ensure_ascii=False, separators=(",", ":"))
    return sha256_hex(pair.encode("utf-8"))


def bundle_problems(bundle: Bundle) -> list[str]:
    """Why a bundle's elements or masks cannot anchor anything, once per reason."""
    reasons = [
        r.reason.value for r in validate_elements(bundle.document, bundle.elements)
    ]
    document = bundle.document
    for mask in bundle.masks:
        if (mask.doc_id, mask.canonical_hash) != (
            document.doc_id,
            document.canonical_hash,
        ) or mask.span.end > len(document.canonical_text):
            reasons.append(RejectionReason.WRONG_DOCUMENT.value)
    return list(dict.fromkeys(reasons))


def _genuine(bundle: Bundle) -> list[DocumentElement]:
    return [e for e in bundle.elements if e.doc_id == bundle.document.doc_id]


def _transparent(
    element: DocumentElement, elements: list[DocumentElement], text: str
) -> bool:
    """An ``other`` element with at least one child and no non-space character of
    its span outside its children's spans (ES9)."""
    if element.type is not ElementType.OTHER:
        return False
    children = sorted(
        (e for e in elements if e.parent_id == element.element_id),
        key=lambda e: e.span.start,
    )
    if not children:
        return False
    own, position = [], element.span.start
    for child in children:
        own.append(text[position : child.span.start])
        position = max(position, child.span.end)
    own.append(text[position : element.span.end])
    return not "".join(own).strip()


def _outside_narrative(
    elements: list[DocumentElement], span: TextSpan, text: str
) -> bool:
    return any(
        e.type not in NARRATIVE
        and e.span.overlaps(span)
        and not _transparent(e, elements, text)
        for e in elements
    )


def narrative_home(bundle: Bundle, span: TextSpan) -> DocumentElement | str:
    """The most specific narrative element that holds ``span``, by P9-19's order:
    the shortest, then the earliest type in ``NARRATIVE``. Or why none does:
    ``not_narrative`` when a non-narrative element overlaps it, a transparent
    container excepted (ES9), and ``outside_element`` when no narrative element
    holds it whole."""
    elements = _genuine(bundle)
    if _outside_narrative(elements, span, bundle.document.canonical_text):
        return Problem.NOT_NARRATIVE.value
    holding = [e for e in elements if e.type in NARRATIVE and e.span.contains(span)]
    if not holding:
        return RejectionReason.OUTSIDE_ELEMENT.value
    return min(holding, key=lambda e: (e.span.length, NARRATIVE.index(e.type)))


def _verify(
    bundle: Bundle, span: TextSpan, element_id: str, locator: SpanLocator
) -> VerifiedSpan | Rejection:
    document = bundle.document
    candidate = parse_span_candidate(
        {
            "doc_id": document.doc_id,
            "canonical_hash": document.canonical_hash,
            "start": span.start,
            "end": span.end,
            "quote_text": document.canonical_text[span.start : span.end],
            "element_id": element_id,
            "prefix": locator.prefix,
            "suffix": locator.suffix,
        }
    )
    if isinstance(candidate, Rejection):
        return candidate
    return validate_span(document, bundle.elements, candidate)


def _masks_over(bundle: Bundle, span: TextSpan) -> tuple[str, ...]:
    return tuple(sorted(mask_id(m) for m in bundle.masks if m.span.overlaps(span)))


def _context(locator: SpanLocator) -> str | None:
    if not locator.prefix and not locator.suffix:
        return None
    return context_hash(locator.prefix, locator.suffix)


def anchor(
    bundle: Bundle, exact: str, prefix: str = "", suffix: str = ""
) -> SpanPointer | str:
    """The pointer for the one occurrence of ``exact`` with this context, or why not."""
    if not exact:
        return Problem.MALFORMED.value
    text = bundle.document.canonical_text
    starts = occurrences(text, SpanLocator(exact=exact, prefix=prefix, suffix=suffix))
    if not starts:
        return RejectionReason.LOCATOR_NOT_FOUND.value
    if len(starts) > 1:
        return RejectionReason.AMBIGUOUS_OCCURRENCE.value
    span = TextSpan(start=starts[0], end=starts[0] + len(exact))
    home = narrative_home(bundle, span)
    if isinstance(home, str):
        return home
    locator = make_locator(bundle.document, span)
    verdict = _verify(bundle, span, home.element_id, locator)
    if isinstance(verdict, Rejection):
        return verdict.reason.value
    return SpanPointer(
        start=span.start,
        end=span.end,
        element_id=home.element_id,
        quote_sha256=quote_hash(verdict.quote_text),
        context_sha256=_context(locator),
        mask_ids=_masks_over(bundle, span),
    )


def check_pointer(bundle: Bundle, pointer: SpanPointer) -> list[str]:
    """Why a committed pointer does not hold in its local document; empty when it
    does. Each hash and mask is recomputed, and the span checked again."""
    text = bundle.document.canonical_text
    if pointer.end > len(text):
        return [RejectionReason.SPAN_OUT_OF_BOUNDS.value]
    span = TextSpan(start=pointer.start, end=pointer.end)
    reasons = []
    if quote_hash(text[span.start : span.end]) != pointer.quote_sha256:
        reasons.append(Problem.QUOTE_HASH_MISMATCH.value)
    locator = make_locator(bundle.document, span)
    if pointer.context_sha256 != _context(locator):
        reasons.append(Problem.CONTEXT_HASH_MISMATCH.value)
    elements = _genuine(bundle)
    named = [e for e in elements if e.element_id == pointer.element_id]
    if any(e.type not in NARRATIVE for e in named) or _outside_narrative(
        elements, span, text
    ):
        reasons.append(Problem.NOT_NARRATIVE.value)
    home = narrative_home(bundle, span)
    if (
        any(e.type in NARRATIVE and e.span.contains(span) for e in named)
        and isinstance(home, DocumentElement)
        and home.element_id != pointer.element_id
    ):
        reasons.append(Problem.ELEMENT_MISMATCH.value)
    verdict = _verify(bundle, span, pointer.element_id, locator)
    if isinstance(verdict, Rejection):
        reasons.append(verdict.reason.value)
    if pointer.mask_ids != _masks_over(bundle, span):
        reasons.append(Problem.MASKS_MISMATCH.value)
    return list(dict.fromkeys(reasons))
