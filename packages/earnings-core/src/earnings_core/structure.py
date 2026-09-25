"""Checks over one document's element set, and pointer resolution (R4.1, R5.1)."""

from collections.abc import Sequence

from earnings_core.documents import CanonicalDocument, document_integrity_problem
from earnings_core.elements import DocumentElement, ElementType, derive_element_id
from earnings_core.rejections import Rejection, RejectionReason
from earnings_core.spans import TextSpan


def validate_elements(
    document: CanonicalDocument, elements: Sequence[DocumentElement]
) -> tuple[Rejection, ...]:
    """Every structural problem in ``elements``; empty when the set is valid (R4.1).

    Rechecks each stored ID and span rather than trust construction. Parents must
    precede their children, and any two spans must nest or be disjoint.
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
    if element.parent_id is not None:
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
    context = element.table_cell
    if context is None:
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
    """Spans that overlap without nesting, found by one sweep in document order."""
    ordered = sorted(
        elements, key=lambda element: (element.span.start, -element.span.end)
    )
    open_spans: list[DocumentElement] = []
    found: list[Rejection] = []
    for element in ordered:
        while open_spans and open_spans[-1].span.end <= element.span.start:
            open_spans.pop()
        if open_spans and not open_spans[-1].span.contains(element.span):
            found.append(
                Rejection(
                    reason=RejectionReason.CROSSING_ELEMENTS,
                    detail=f"{element.element_id} overlaps"
                    f" {open_spans[-1].element_id} without nesting",
                )
            )
            continue
        open_spans.append(element)
    return found
