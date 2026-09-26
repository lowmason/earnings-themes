"""Checks over one document's element set, and pointer resolution (R4.1, R5.1)."""

from collections.abc import Sequence

from earnings_core.documents import CanonicalDocument, document_integrity_problem
from earnings_core.elements import (
    LEVELED_TYPES,
    DocumentElement,
    ElementType,
    derive_element_id,
)
from earnings_core.rejections import Rejection, RejectionReason
from earnings_core.spans import TextSpan


def validate_elements(
    document: CanonicalDocument, elements: Sequence[DocumentElement]
) -> tuple[Rejection, ...]:
    """Every structural problem in ``elements``; empty when the set is valid (R4.1).

    Rechecks each stored ID, span, and invariant rather than trust construction,
    because ``model_copy(update=...)`` skips validation. Parents must precede their
    children, and any two spans must nest or be disjoint: every crossing pair is
    reported.
    """
    problem = document_integrity_problem(document)
    if problem is not None:
        return (Rejection(reason=RejectionReason.DOCUMENT_INTEGRITY, detail=problem),)
    known: dict[str, DocumentElement] = {}
    for element in elements:
        known.setdefault(element.element_id, element)
    problems: list[Rejection] = []
    earlier: dict[str, DocumentElement] = {}
    for element in elements:
        problems.extend(_own_problems(document, element, earlier, known))
        earlier.setdefault(element.element_id, element)
    for element in elements:
        problems.extend(_table_problems(element, known))
    problems.extend(_crossings(elements))
    return tuple(problems)


def resolve_pointer(
    document: CanonicalDocument, elements: Sequence[DocumentElement], element_id: str
) -> TextSpan | Rejection:
    """The span of the element a model pointed at: code, not the model, supplies offsets.

    Only an element of this document version resolves; anything else is an invalid
    pointer with a recorded reason (R5.1, V9).
    """
    problem = document_integrity_problem(document)
    if problem is not None:
        return Rejection(reason=RejectionReason.DOCUMENT_INTEGRITY, detail=problem)
    for element in elements:
        if element.element_id != element_id:
            continue
        if element.doc_id != document.doc_id:
            return Rejection(
                reason=RejectionReason.WRONG_DOCUMENT,
                detail=f"element {element_id} belongs to {element.doc_id},"
                f" not {document.doc_id}",
            )
        if derive_element_id(element.type, element.span) != element_id:
            return Rejection(
                reason=RejectionReason.ELEMENT_ID_MISMATCH,
                detail=f"element {element_id} does not match its type and span",
            )
        return element.span
    return Rejection(
        reason=RejectionReason.UNKNOWN_ELEMENT,
        detail=f"no element {element_id!r} in {document.doc_id}",
    )


def _own_problems(
    document: CanonicalDocument,
    element: DocumentElement,
    earlier: dict[str, DocumentElement],
    known: dict[str, DocumentElement],
) -> list[Rejection]:
    found: list[Rejection] = []
    name = element.element_id

    def reject(reason: RejectionReason, detail: str) -> None:
        found.append(Rejection(reason=reason, detail=f"{name}: {detail}"))

    if element.doc_id != document.doc_id:
        reject(RejectionReason.WRONG_DOCUMENT, f"belongs to {element.doc_id}")
    if name != derive_element_id(element.type, element.span):
        reject(RejectionReason.ELEMENT_ID_MISMATCH, "ID is not its type and span")
    if element.span.end > len(document.canonical_text):
        reject(
            RejectionReason.SPAN_OUT_OF_BOUNDS,
            f"ends at {element.span.end}, past {len(document.canonical_text)}",
        )
    if name in earlier:
        reject(RejectionReason.DUPLICATE_ELEMENT, "appears twice")
    if element.level is not None and element.type not in LEVELED_TYPES:
        reject(
            RejectionReason.MALFORMED_RECORD,
            f"a {element.type.value} element carries level {element.level}",
        )
    if (element.type is ElementType.TABLE_CELL) != (element.table_cell is not None):
        reject(
            RejectionReason.MALFORMED_RECORD,
            "table_cell context is required on table cells and forbidden elsewhere",
        )
    if element.parent_id == name:
        reject(RejectionReason.MALFORMED_RECORD, "is its own parent")
    elif element.parent_id is not None:
        parent = known.get(element.parent_id)
        if parent is None:
            reject(RejectionReason.UNKNOWN_PARENT, f"parent {element.parent_id}")
        elif element.parent_id not in earlier:
            reject(RejectionReason.PARENT_ORDER, f"precedes parent {element.parent_id}")
        elif not parent.span.contains(element.span):
            reject(RejectionReason.OUTSIDE_PARENT, f"not inside {parent.element_id}")
    return found


def _table_problems(
    element: DocumentElement, known: dict[str, DocumentElement]
) -> list[Rejection]:
    """A cell's parent and header references; a misplaced context is malformed instead."""
    context = element.table_cell
    if context is None or element.type is not ElementType.TABLE_CELL:
        return []
    name = element.element_id
    parent = known.get(element.parent_id) if element.parent_id is not None else None
    if parent is None or parent.type is not ElementType.TABLE:
        return [
            Rejection(
                reason=RejectionReason.TABLE_CELL_PARENT,
                detail=f"{name}: parent {element.parent_id} is not a table",
            )
        ]
    found: list[Rejection] = []
    for header_id in context.header_cell_ids:
        header = known.get(header_id)
        if (
            header is None
            or header.table_cell is None
            or not header.table_cell.is_header
            or header.parent_id != element.parent_id
        ):
            found.append(
                Rejection(
                    reason=RejectionReason.INVALID_HEADER_REFERENCE,
                    detail=f"{name}: {header_id} is not a header cell of"
                    f" {element.parent_id}",
                )
            )
    return found


def _crossings(elements: Sequence[DocumentElement]) -> list[Rejection]:
    """Every pair of spans that overlap without nesting, in one sweep by start.

    Each element is compared with every span still open where it starts, so each
    crossing pair is reported once, against the element that starts first.
    """
    ordered = sorted(
        elements, key=lambda element: (element.span.start, -element.span.end)
    )
    open_spans: list[DocumentElement] = []
    found: list[Rejection] = []
    for element in ordered:
        open_spans = [
            other for other in open_spans if other.span.end > element.span.start
        ]
        for other in open_spans:
            if not other.span.contains(element.span):
                found.append(
                    Rejection(
                        reason=RejectionReason.CROSSING_ELEMENTS,
                        detail=f"{element.element_id} overlaps"
                        f" {other.element_id} without nesting",
                    )
                )
        open_spans.append(element)
    return found
