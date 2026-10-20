"""TextChunk: a view of one document whose local offsets convert back (A §508)."""

from typing import Self

from pydantic import model_validator

from earnings_core._model import VersionedRecord
from earnings_core.documents import CanonicalDocument
from earnings_core.hashing import Sha256Hex
from earnings_core.rejections import Rejection, RejectionReason
from earnings_core.spans import TextSpan


class TextChunk(VersionedRecord):
    """A slice of a canonical document, handed to a model or a parser as a unit.

    A chunk never re-normalizes its text: ``text`` is exactly the document's
    characters over ``span``, so a local span converts back by adding one offset.
    Convert before storing evidence (A §508).
    """

    doc_id: str
    canonical_hash: Sha256Hex
    span: TextSpan
    text: str

    @model_validator(mode="after")
    def _text_fills_span(self) -> Self:
        if len(self.text) != self.span.length:
            raise ValueError(
                f"chunk text has {len(self.text)} characters for a span of"
                f" {self.span.length}"
            )
        return self

    @classmethod
    def of(cls, document: CanonicalDocument, span: TextSpan) -> Self:
        """The chunk of ``document`` over ``span``; raises if it runs past the text.

        Parameters
        ----------
        document : CanonicalDocument
            The document to slice.
        span : TextSpan
            The range of the document's text that the chunk covers.

        Returns
        -------
        TextChunk
            The chunk, with its text sliced from the document.

        Raises
        ------
        ValueError
            If ``span`` runs past the document's text.
        """
        return cls(
            doc_id=document.doc_id,
            canonical_hash=document.canonical_hash,
            span=span,
            text=span.slice_of(document.canonical_text),
        )

    def to_document_span(self, local: TextSpan) -> TextSpan | Rejection:
        """Convert a span over ``self.text`` into the document's coordinates.

        Parameters
        ----------
        local : TextSpan
            A span in offsets local to ``text``.

        Returns
        -------
        TextSpan or Rejection
            The span in document offsets, or an ``OUTSIDE_CHUNK`` rejection if ``local`` runs past the chunk.
        """
        if local.end > len(self.text):
            return Rejection(
                reason=RejectionReason.OUTSIDE_CHUNK,
                detail=f"local span [{local.start}, {local.end}) runs past a chunk"
                f" of {len(self.text)} characters",
            )
        return TextSpan(
            start=self.span.start + local.start, end=self.span.start + local.end
        )
