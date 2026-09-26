"""earnings-core: the contracts and exactness checks every other package builds on.

Contract schema version 2; docs/data-dictionary.md documents every field.
"""

from earnings_core._model import SCHEMA_VERSION
from earnings_core.artifacts import ArtifactRef, RightsStatus
from earnings_core.chunks import TextChunk
from earnings_core.documents import (
    CanonicalDocument,
    derive_doc_id,
    document_integrity_problem,
)
from earnings_core.elements import (
    LEVELED_TYPES,
    DocumentElement,
    ElementType,
    TableCellContext,
    TextOrigin,
    derive_element_id,
)
from earnings_core.evidence import (
    SpanCandidate,
    VerifiedSpan,
    parse_span_candidate,
    validate_span,
)
from earnings_core.hashing import hash_canonical_text, sha256_hex
from earnings_core.locators import (
    SpanLocator,
    make_locator,
    occurrences,
    resolve_locator,
)
from earnings_core.masks import MaskCategory, MaskedDocument, OverlayMask, apply_masks
from earnings_core.rejections import VALIDATOR_VERSION, Rejection, RejectionReason
from earnings_core.spans import TextSpan
from earnings_core.structure import resolve_pointer, validate_elements

__all__ = [
    "LEVELED_TYPES",
    "SCHEMA_VERSION",
    "VALIDATOR_VERSION",
    "ArtifactRef",
    "CanonicalDocument",
    "DocumentElement",
    "ElementType",
    "MaskCategory",
    "MaskedDocument",
    "OverlayMask",
    "Rejection",
    "RejectionReason",
    "RightsStatus",
    "SpanCandidate",
    "SpanLocator",
    "TableCellContext",
    "TextChunk",
    "TextOrigin",
    "TextSpan",
    "VerifiedSpan",
    "apply_masks",
    "derive_doc_id",
    "derive_element_id",
    "document_integrity_problem",
    "hash_canonical_text",
    "make_locator",
    "occurrences",
    "parse_span_candidate",
    "resolve_locator",
    "resolve_pointer",
    "sha256_hex",
    "validate_elements",
    "validate_span",
]
