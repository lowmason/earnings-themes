"""The canonicalizer's records: its result, its manifest, and its failure (Stage 3).

These are ingestion records, not core contracts, with their own schema version.
docs/data-dictionary.md documents every field.
"""

from enum import StrEnum
from typing import Literal, Self

from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    MaskedDocument,
    Rejection,
)
from earnings_core.documents import IdPart
from earnings_core.hashing import Sha256Hex
from pydantic import BaseModel, ConfigDict, NonNegativeInt, model_validator

INGESTION_SCHEMA_VERSION = 1
"""The version of every ingestion record; any field change bumps it."""


class IngestionRecord(BaseModel):
    """Immutable, closed, strictly typed, like every earnings-core contract."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    schema_version: Literal[1] = INGESTION_SCHEMA_VERSION


class CanonicalizationManifest(IngestionRecord):
    """How one canonical document version was made.

    It holds no timestamp and no path, so it regenerates byte for byte; operational run
    metadata belongs to the application that calls the canonicalizer (A §412).
    """

    canonicalization_version: IdPart
    components: dict[str, str]
    lxml_version: str
    libxml2_version: str
    python_version: str
    source_document_id: IdPart
    raw_sha256: Sha256Hex
    raw_bytes: NonNegativeInt
    encoding: str
    encoding_basis: str
    element_counts: dict[str, NonNegativeInt]
    image_count: NonNegativeInt
    replacement_characters: NonNegativeInt
    retypes: dict[str, NonNegativeInt]
    limitations: tuple[str, ...]
    mask_policy_id: IdPart
    mask_policy_version: IdPart
    mask_count: NonNegativeInt


class FailureReason(StrEnum):
    """Why no canonical document was made; ``canonicalize`` never raises on input."""

    UNSUPPORTED_MEDIA_TYPE = "unsupported_media_type"
    """The media type's essence is not ``text/html``."""
    PARSE_FAILED = "parse_failed"
    """Decoding, lxml, or the walker raised on input it cannot read, or libxml2 logged a
    fatal error, such as excessive nesting depth."""
    NO_NATIVE_TEXT = "no_native_text"
    """Nothing is left after N1: image-only input lands here (R4.3, SC7)."""
    INVALID_ELEMENTS = "invalid_elements"
    """``validate_elements`` found problems: a canonicalizer defect, never the input's."""


class CanonicalizationFailure(IngestionRecord):
    """A document the canonicalizer refused, with nothing partial (Stage 3 spec: Failures).

    ``image_count`` is recorded exactly for ``no_native_text``, and ``rejections``
    exactly for ``invalid_elements``.
    """

    source_document_id: IdPart
    raw_sha256: Sha256Hex
    canonicalization_version: IdPart
    reason: FailureReason
    detail: str
    image_count: NonNegativeInt | None = None
    rejections: tuple[Rejection, ...] = ()

    @model_validator(mode="after")
    def _evidence_matches_the_reason(self) -> Self:
        if (self.image_count is not None) != (
            self.reason is FailureReason.NO_NATIVE_TEXT
        ):
            raise ValueError("image_count is recorded exactly for no_native_text")
        if bool(self.rejections) != (self.reason is FailureReason.INVALID_ELEMENTS):
            raise ValueError("rejections are recorded exactly for invalid_elements")
        return self


class Canonicalized(BaseModel):
    """A canonical document with its elements, masks, and manifest.

    ``elements`` are in document order, each parent before its children.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    document: CanonicalDocument
    elements: tuple[DocumentElement, ...]
    masked: MaskedDocument
    manifest: CanonicalizationManifest

    @model_validator(mode="after")
    def _parts_agree(self) -> Self:
        if self.masked.document != self.document:
            raise ValueError("the masks belong to another document")
        if any(element.doc_id != self.document.doc_id for element in self.elements):
            raise ValueError("an element belongs to another document")
        if (
            self.manifest.source_document_id,
            self.manifest.canonicalization_version,
        ) != (
            self.document.source_document_id,
            self.document.canonicalization_version,
        ):
            raise ValueError("the manifest describes another document")
        return self
