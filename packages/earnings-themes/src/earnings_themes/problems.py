"""Why a Stage 6 check refused something, as an item and a reason (the Stage 6 spec,
§Refusals).

A refusal names its subject by ID or field path and gives its reason, which is a
``Problem`` or one of earnings-core's ``RejectionReason`` values. It never carries a
quote, a claim, or a detail, since a detail may quote a release (GS13).
"""

from dataclasses import dataclass
from enum import StrEnum


class Problem(StrEnum):
    """Stage 6's own reasons; span checks give earnings-core's ``RejectionReason``."""

    MALFORMED = "malformed"
    NOT_NARRATIVE = "not_narrative"
    ELEMENT_MISMATCH = "element_mismatch"
    QUOTE_HASH_MISMATCH = "quote_hash_mismatch"
    CONTEXT_HASH_MISMATCH = "context_hash_mismatch"
    MASKS_MISMATCH = "masks_mismatch"
    WRONG_PIN = "wrong_pin"
    WRONG_SPLIT = "wrong_split"
    WRONG_PARTITION = "wrong_partition"
    EXCLUDED_EVENT = "excluded_event"
    WRONG_CODEBOOK = "wrong_codebook"
    CODEBOOK_NOT_APPROVED = "codebook_not_approved"
    UNSIGNED = "unsigned"
    NO_THEME_MISMATCH = "no_theme_mismatch"
    COUNTS_MISMATCH = "counts_mismatch"
    DUPLICATE_ID = "duplicate_id"
    UNKNOWN_QUOTE = "unknown_quote"
    UNKNOWN_CLAIM = "unknown_claim"
    UNKNOWN_THEME = "unknown_theme"
    UNKNOWN_DOCUMENT = "unknown_document"
    UNREFERENCED = "unreferenced"
    TIE_GROUP = "tie_group"
    SOURCE_WORDING = "source_wording"
    OUTSIDE_TRAINING = "outside_training"
    SYNTHETIC_UNFLAGGED = "synthetic_unflagged"
    PARENT_CYCLE = "parent_cycle"
    DISCOVERY_CORPUS = "discovery_corpus"
    CONTENT_HASH_MISMATCH = "content_hash_mismatch"
    NEGATIVE_KINDS = "negative_kinds"
    ADR_NOT_CITED = "adr_not_cited"


@dataclass(frozen=True, order=True)
class Refusal:
    """One refused item: its ID or field path, and the reason."""

    subject: str
    reason: str

    def __str__(self) -> str:
        return f"{self.subject}: {self.reason}"
