"""layout-1's records: its element stream over one document, and each alignment failure.

These are ingestion records, not core contracts. docs/data-dictionary.md documents
every field.
"""

from typing import Literal, Self

from earnings_core import DocumentElement, RejectionReason
from earnings_core.documents import IdPart
from pydantic import NonNegativeInt, model_validator

from earnings_ingestion.canonical.records import IngestionRecord

ALIGNMENT_REASONS = frozenset(
    {RejectionReason.LOCATOR_NOT_FOUND, RejectionReason.AMBIGUOUS_OCCURRENCE}
)


class AlignmentFailure(IngestionRecord):
    """One layout-1 unit that maps onto no single canonical span (SC13).

    ``reason`` is core's ``locator_not_found`` when the unit's text occurs nowhere,
    and ``ambiguous_occurrence`` when it occurs more than once and no neighbour
    decides, or when its one place is out of order.
    """

    status: Literal["alignment_failed"] = "alignment_failed"
    reason: RejectionReason
    unit_type: str
    text: str
    detail: str

    @model_validator(mode="after")
    def _reason(self) -> Self:
        if self.reason not in ALIGNMENT_REASONS:
            raise ValueError(f"{self.reason.value} is not an alignment reason")
        return self


class LayoutExtraction(IngestionRecord):
    """layout-1's element stream over one canonical document, and every failure.

    ``units`` counts what was aligned: each block, and each cell of a table.
    """

    layout_version: IdPart
    mapping_policy: IdPart
    capture_id: str
    doc_id: str
    units: NonNegativeInt
    retypes: dict[str, NonNegativeInt]
    elements: tuple[DocumentElement, ...]
    failures: tuple[AlignmentFailure, ...]
