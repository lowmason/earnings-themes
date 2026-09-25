"""CanonicalDocument: one immutable, hashed version of a source document's text."""

from typing import Annotated, Self

from pydantic import StringConstraints, model_validator

from earnings_core._model import VersionedRecord
from earnings_core.artifacts import ArtifactRef
from earnings_core.hashing import Sha256Hex, hash_canonical_text

IdPart = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9._:-]+$")]
"""One component of a derived identifier: letters, digits, and ``. _ : -`` only."""


def derive_doc_id(
    source_document_id: str, canonicalization_version: str, canonical_hash: str
) -> str:
    """The ID of one canonical version of a source document.

    It embeds the first 16 hex characters of the canonical hash, so changed text is
    always a new ``doc_id`` (R3.3). Plan decision, 2026-09-25: derived and readable.
    """
    return f"{source_document_id}@{canonicalization_version}#{canonical_hash[:16]}"


class CanonicalDocument(VersionedRecord):
    """Canonical text, its SHA-256, and the version that produced it (R3.1, R3.3).

    ``canonicalization_version`` names the whole policy (parser, rules, and
    normalization); parser and library versions belong to Stage 3's run manifest.
    The text is always held here, because the validators are pure functions of it;
    ``text_artifact`` optionally records where the same UTF-8 bytes are stored.
    """

    doc_id: str
    source_document_id: IdPart
    canonicalization_version: IdPart
    canonical_text: Annotated[str, StringConstraints(min_length=1)]
    canonical_hash: Sha256Hex
    text_artifact: ArtifactRef | None = None

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        problem = document_integrity_problem(self)
        if problem is not None:
            raise ValueError(problem)
        return self

    @classmethod
    def create(
        cls,
        *,
        source_document_id: str,
        canonicalization_version: str,
        canonical_text: str,
        text_artifact: ArtifactRef | None = None,
    ) -> Self:
        """Build a version from its text, deriving ``canonical_hash`` and ``doc_id``."""
        try:
            canonical_hash = hash_canonical_text(canonical_text)
        except UnicodeEncodeError as error:
            raise ValueError(
                "canonical text holds a lone surrogate and has no UTF-8 encoding"
            ) from error
        return cls(
            doc_id=derive_doc_id(
                source_document_id, canonicalization_version, canonical_hash
            ),
            source_document_id=source_document_id,
            canonicalization_version=canonicalization_version,
            canonical_text=canonical_text,
            canonical_hash=canonical_hash,
            text_artifact=text_artifact,
        )


def document_integrity_problem(document: CanonicalDocument) -> str | None:
    """Recheck a document's stored hash and ``doc_id`` against its text (R6.1, R3.3).

    Validators call this rather than trust construction, because
    ``model_copy(update=...)`` skips validation. Returns ``None`` when consistent.
    """
    if not document.canonical_text:
        return "canonical text is empty"
    try:
        actual = hash_canonical_text(document.canonical_text)
    except UnicodeEncodeError:
        return "canonical text holds a lone surrogate and has no UTF-8 encoding"
    if actual != document.canonical_hash:
        return (
            f"stored canonical_hash {document.canonical_hash} is not the text's"
            f" SHA-256 {actual}"
        )
    expected = derive_doc_id(
        document.source_document_id, document.canonicalization_version, actual
    )
    if document.doc_id != expected:
        return f"doc_id {document.doc_id!r} is not the derived {expected!r}"
    artifact = document.text_artifact
    if artifact is not None and artifact.content_sha256 != actual:
        return (
            f"text_artifact {artifact.storage_ref!r} holds other bytes"
            f" (SHA-256 {artifact.content_sha256})"
        )
    return None
