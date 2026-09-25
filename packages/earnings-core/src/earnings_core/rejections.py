"""Rejection: the recorded reason a record failed a check (R6.2: rejections stay auditable)."""

from enum import StrEnum

from earnings_core._model import VersionedRecord

VALIDATOR_VERSION = "1"
"""Bump when any check changes: caches key on the verifier version (R14.6)."""


class RejectionReason(StrEnum):
    """Every reason a check can refuse a record, one per failure class."""

    MALFORMED_RECORD = "malformed_record"
    """Wrong types, missing or extra fields, or a non-integer offset (R3.2, R5.5)."""
    DOCUMENT_INTEGRITY = "document_integrity"
    """The document's own hash or doc_id disagrees with its text (R6.1, R3.3)."""
    WRONG_DOCUMENT = "wrong_document"
    """The record names another document, or another version of it (R6.1, R3.3)."""
    CANONICAL_HASH_MISMATCH = "canonical_hash_mismatch"
    """The record's stored hash is not the document's (R6.1)."""
    SPAN_OUT_OF_BOUNDS = "span_out_of_bounds"
    """The span runs past the canonical text (R6.1)."""
    QUOTE_TEXT_MISMATCH = "quote_text_mismatch"
    """``quote_text`` is not exactly ``canonical_text[start:end]`` (R6.1, R5.5, R13.2)."""
    UNKNOWN_ELEMENT = "unknown_element"
    """A pointer or attribution names no element of this document (R5.1, V9)."""
    OUTSIDE_ELEMENT = "outside_element"
    """The span is not inside the element it is attributed to (R6.1)."""
    CROSSES_SPEAKER_TURN = "crosses_speaker_turn"
    """The span runs across a speaker-turn boundary (A §585, V9)."""
    LOCATOR_MISMATCH = "locator_mismatch"
    """The stored prefix or suffix is not the text around the span (R5.4)."""
    AMBIGUOUS_OCCURRENCE = "ambiguous_occurrence"
    """Repeated text whose context does not single out one occurrence (R5.4)."""
    LOCATOR_NOT_FOUND = "locator_not_found"
    """No occurrence of the text matches the locator (R5.4)."""
    OUTSIDE_CHUNK = "outside_chunk"
    """A chunk-local span runs past its chunk (A §508, V9)."""
    ELEMENT_ID_MISMATCH = "element_id_mismatch"
    """An element's ID is not derived from its type and span (R4.1)."""
    DUPLICATE_ELEMENT = "duplicate_element"
    """Two elements share an ID, so the same type and span (R4.1)."""
    UNKNOWN_PARENT = "unknown_parent"
    """A parent ID names no element of the set (R4.1)."""
    PARENT_ORDER = "parent_order"
    """A child precedes its parent in the element sequence (R4.1)."""
    OUTSIDE_PARENT = "outside_parent"
    """A child's span is not inside its parent's span (R4.1)."""
    CROSSING_ELEMENTS = "crossing_elements"
    """Two spans overlap without one containing the other (R4.1)."""
    TABLE_CELL_PARENT = "table_cell_parent"
    """A table cell's parent is not a table element (R4.1, R4.2)."""
    INVALID_HEADER_REFERENCE = "invalid_header_reference"
    """A header reference names no header cell of the same table (R4.2)."""


class Rejection(VersionedRecord):
    """Why a check refused a record, and which validator version said so."""

    reason: RejectionReason
    detail: str
    validator_version: str = VALIDATOR_VERSION
