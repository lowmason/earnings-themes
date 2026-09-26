"""Structure-aware canonicalization of saved release HTML (Stage 3, walker-1).

``canonicalize`` is the entry point; every module below it is one pipeline stage.
"""

from earnings_ingestion.canonical.pipeline import CANONICALIZATION_VERSION, canonicalize
from earnings_ingestion.canonical.records import (
    INGESTION_SCHEMA_VERSION,
    CanonicalizationFailure,
    CanonicalizationManifest,
    Canonicalized,
    FailureReason,
)

__all__ = [
    "CANONICALIZATION_VERSION",
    "INGESTION_SCHEMA_VERSION",
    "CanonicalizationFailure",
    "CanonicalizationManifest",
    "Canonicalized",
    "FailureReason",
    "canonicalize",
]
