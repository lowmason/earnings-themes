"""Evidence spans: parse an untrusted candidate, then verify it exactly (R6.1)."""

from collections.abc import Mapping, Sequence
from typing import Self

from pydantic import NonNegativeInt, ValidationError, model_validator

from earnings_core._model import VersionedRecord
from earnings_core.documents import CanonicalDocument, document_integrity_problem
from earnings_core.elements import (
    DocumentElement,
    ElementType,
    TextOrigin,
    derive_element_id,
)
from earnings_core.hashing import Sha256Hex
from earnings_core.locators import SpanLocator, occurrences
from earnings_core.rejections import VALIDATOR_VERSION, Rejection, RejectionReason
from earnings_core.spans import TextSpan


class _EvidenceFields(VersionedRecord):
    """One contiguous range of one document version: noncontiguous evidence is
    separate records, never one stitched record (R5.5)."""

    doc_id: str
    canonical_hash: Sha256Hex
    start: NonNegativeInt
    end: NonNegativeInt
    quote_text: str
    element_id: str
    prefix: str = ""
    suffix: str = ""

    @model_validator(mode="after")
    def _start_before_end(self) -> Self:
        if self.start >= self.end:
            raise ValueError(f"span [{self.start}, {self.end}) is empty or reversed")
        return self

    @property
    def span(self) -> TextSpan:
        return TextSpan(start=self.start, end=self.end)


class SpanCandidate(_EvidenceFields):
    """A proposed evidence span, as it arrives for verification.

    ``element_id`` attributes the span to the section, speaker turn, or other element
    that must contain it. ``prefix`` and ``suffix`` are the words around it, needed
    when ``quote_text`` occurs more than once (R5.4).
    """


class VerifiedSpan(_EvidenceFields):
    """A span that passed every check; ``quote_text`` is sliced from the canonical
    text, never copied from the candidate (A §523)."""

    validator_version: str


def parse_span_candidate(raw: object) -> SpanCandidate | Rejection:
    """Type-check untrusted input, recording a schema failure as a reason.

    ``raw`` is JSON text or bytes, or an already-decoded mapping. A bool, float, or
    numeric string offset (R3.2), a list of ranges (R5.5), a missing field, or any
    extra field is ``malformed_record``.
    """
    try:
        if isinstance(raw, str | bytes):
            return SpanCandidate.model_validate_json(raw)
        if isinstance(raw, Mapping):
            return SpanCandidate.model_validate(dict(raw))
    except ValidationError as error:
        return Rejection(
            reason=RejectionReason.MALFORMED_RECORD, detail=_describe(error)
        )
    return Rejection(
        reason=RejectionReason.MALFORMED_RECORD,
        detail=f"a candidate is a JSON object, not {type(raw).__name__}",
    )


def validate_span(
    document: CanonicalDocument,
    elements: Sequence[DocumentElement],
    candidate: SpanCandidate,
) -> VerifiedSpan | Rejection:
    """Accept one evidence span only if every check holds (R6.1); no tolerance exists.

    The checks run in a fixed order, each presupposing the ones before it, and the
    first failure is the recorded reason. A span over OCR-derived text is refused
    after the speaker-turn check, however exactly it matches (R4.3). Nothing here is
    a threshold (R13.2): text is compared with ``==``, never normalized. Check the
    element set once with ``validate_elements`` before checking spans against it.
    """
    problem = document_integrity_problem(document)
    if problem is not None:
        return _reject(RejectionReason.DOCUMENT_INTEGRITY, problem)
    text = document.canonical_text
    start, end = candidate.start, candidate.end
    if candidate.doc_id != document.doc_id:
        return _reject(
            RejectionReason.WRONG_DOCUMENT,
            f"candidate names {candidate.doc_id}, not {document.doc_id}",
        )
    if candidate.canonical_hash != document.canonical_hash:
        return _reject(
            RejectionReason.CANONICAL_HASH_MISMATCH,
            f"candidate hash {candidate.canonical_hash} is not"
            f" {document.canonical_hash}",
        )
    if not 0 <= start < end <= len(text):
        return _reject(
            RejectionReason.SPAN_OUT_OF_BOUNDS,
            f"[{start}, {end}) is outside a text of length {len(text)}",
        )
    exact = text[start:end]
    if candidate.quote_text != exact:
        return _reject(
            RejectionReason.QUOTE_TEXT_MISMATCH,
            f"quote_text {candidate.quote_text!r} is not the canonical {exact!r}",
        )
    span = candidate.span
    element = _element(document, elements, candidate.element_id)
    if element is None:
        return _reject(
            RejectionReason.UNKNOWN_ELEMENT,
            f"no element {candidate.element_id!r} in {document.doc_id}",
        )
    if not element.span.contains(span):
        return _reject(
            RejectionReason.OUTSIDE_ELEMENT,
            f"[{start}, {end}) is not inside {element.element_id}",
        )
    for turn in _speaker_turns(document, elements):
        if turn.span.overlaps(span) and not turn.span.contains(span):
            return _reject(
                RejectionReason.CROSSES_SPEAKER_TURN,
                f"[{start}, {end}) crosses the boundary of {turn.element_id}",
            )
    for recognized in _ocr_elements(document, elements):
        if recognized.span.overlaps(span):
            return _reject(
                RejectionReason.OCR_DERIVED_TEXT,
                f"[{start}, {end}) overlaps OCR-derived {recognized.element_id}",
            )
    before = text[max(0, start - len(candidate.prefix)) : start]
    after = text[end : end + len(candidate.suffix)]
    if before != candidate.prefix or after != candidate.suffix:
        return _reject(
            RejectionReason.LOCATOR_MISMATCH,
            f"stored context {candidate.prefix!r} / {candidate.suffix!r} is not the"
            f" text around [{start}, {end})",
        )
    locator = SpanLocator(exact=exact, prefix=candidate.prefix, suffix=candidate.suffix)
    count = len(occurrences(text, locator))
    if count > 1:
        return _reject(
            RejectionReason.AMBIGUOUS_OCCURRENCE,
            f"{exact!r} occurs {count} times with this context",
        )
    return VerifiedSpan(
        doc_id=document.doc_id,
        canonical_hash=document.canonical_hash,
        start=start,
        end=end,
        quote_text=exact,
        element_id=element.element_id,
        prefix=candidate.prefix,
        suffix=candidate.suffix,
        validator_version=VALIDATOR_VERSION,
    )


def _reject(reason: RejectionReason, detail: str) -> Rejection:
    return Rejection(reason=reason, detail=detail)


def _genuine(document: CanonicalDocument, element: DocumentElement) -> bool:
    """An element of this document version whose ID still matches its type and span."""
    return element.doc_id == document.doc_id and element.element_id == (
        derive_element_id(element.type, element.span)
    )


def _element(
    document: CanonicalDocument, elements: Sequence[DocumentElement], element_id: str
) -> DocumentElement | None:
    for element in elements:
        if element.element_id == element_id and _genuine(document, element):
            return element
    return None


def _speaker_turns(
    document: CanonicalDocument, elements: Sequence[DocumentElement]
) -> list[DocumentElement]:
    return [
        element
        for element in elements
        if element.type is ElementType.SPEAKER_TURN and _genuine(document, element)
    ]


def _ocr_elements(
    document: CanonicalDocument, elements: Sequence[DocumentElement]
) -> list[DocumentElement]:
    """Genuine elements whose text was recognized from an image (R4.3)."""
    return [
        element
        for element in elements
        if element.text_origin is TextOrigin.OCR and _genuine(document, element)
    ]


def _describe(error: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in item['loc']) or 'record'}: {item['msg']}"
        for item in error.errors()
    )
