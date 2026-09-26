"""Overlay masks: boilerplate marked over canonical text, never cut from it (R3.4)."""

from collections.abc import Sequence
from enum import StrEnum
from typing import Self

from pydantic import model_validator

from earnings_core._model import ContractModel, VersionedRecord
from earnings_core.documents import (
    CanonicalDocument,
    IdPart,
    document_integrity_problem,
)
from earnings_core.hashing import Sha256Hex
from earnings_core.spans import TextSpan


class MaskCategory(StrEnum):
    """R3.4's boilerplate kinds."""

    SAFE_HARBOR = "safe_harbor"
    NON_GAAP_DISCLAIMER = "non_gaap_disclaimer"
    REPEATED_LEGAL = "repeated_legal"


class OverlayMask(VersionedRecord):
    """One boilerplate span, marked by one version of a boilerplate policy (R3.4).

    A masked span stays in the canonical text and keeps its offsets: it is excluded
    from headline prevalence and retained for audit.
    """

    doc_id: str
    canonical_hash: Sha256Hex
    span: TextSpan
    category: MaskCategory
    policy_id: IdPart
    policy_version: IdPart


class MaskedDocument(ContractModel):
    """A document with the masks one policy version computed over it.

    An empty ``masks`` still records which policy ran and found nothing. Construction
    refuses a document whose hash or ``doc_id`` disagrees with its text, a mask of
    another document or version, a mask past the text, and a mask from another
    policy: one policy version per document keeps every comparison period under the
    same rule (A §591).
    """

    document: CanonicalDocument
    policy_id: IdPart
    policy_version: IdPart
    masks: tuple[OverlayMask, ...]

    @model_validator(mode="after")
    def _masks_fit_the_document(self) -> Self:
        document = self.document
        problem = document_integrity_problem(document)
        if problem is not None:
            raise ValueError(problem)
        for mask in self.masks:
            where = f"mask over [{mask.span.start}, {mask.span.end})"
            if (mask.doc_id, mask.canonical_hash) != (
                document.doc_id,
                document.canonical_hash,
            ):
                raise ValueError(
                    f"{where} belongs to {mask.doc_id}, not {document.doc_id}"
                )
            if mask.span.end > len(document.canonical_text):
                raise ValueError(f"{where} runs past the text")
            if (mask.policy_id, mask.policy_version) != (
                self.policy_id,
                self.policy_version,
            ):
                raise ValueError(
                    f"{where} comes from policy {mask.policy_id} {mask.policy_version},"
                    f" not under policy {self.policy_id} {self.policy_version}"
                )
        return self

    def masks_overlapping(self, span: TextSpan) -> tuple[OverlayMask, ...]:
        """The masks sharing at least one code point with ``span``."""
        return tuple(mask for mask in self.masks if mask.span.overlaps(span))


def apply_masks(
    document: CanonicalDocument,
    masks: Sequence[OverlayMask],
    *,
    policy_id: str,
    policy_version: str,
) -> MaskedDocument:
    """Overlay ``masks`` on ``document`` without touching its text or hash (R3.4).

    Raises ``ValueError`` for anything ``MaskedDocument`` refuses. Pydantic's
    ``ValidationError`` is a ``ValueError``, so callers need not import it.
    """
    return MaskedDocument(
        document=document,
        policy_id=policy_id,
        policy_version=policy_version,
        masks=tuple(masks),
    )
