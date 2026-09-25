"""ArtifactRef: a content-addressed pointer to a stored artifact and its rights."""

from enum import StrEnum
from typing import Annotated, Self

from pydantic import StringConstraints, field_validator

from earnings_core._model import VersionedRecord
from earnings_core.hashing import Sha256Hex, sha256_hex

NonBlankStr = Annotated[str, StringConstraints(pattern=r"\S")]
"""A string holding at least one non-whitespace character."""

MediaType = Annotated[
    str,
    StringConstraints(
        pattern=r"^[a-z0-9.+-]+/[a-z0-9.+-]+(; ?[a-z0-9-]+=[A-Za-z0-9._-]+)*$"
    ),
]
"""A lowercase media type with optional parameters, e.g. ``text/plain; charset=utf-8``."""


class RightsStatus(StrEnum):
    """What may be done with an artifact's content (A §58, A §242, R2.1).

    Record unclear rights as ``LOCAL_ONLY``: they keep an artifact local and restrict
    its export (specs/point-in-time-djia-cohort.md, §Failure handling).
    """

    REDISTRIBUTABLE = "redistributable"
    """A recorded basis permits committing and exporting the content."""
    LOCAL_ONLY = "local_only"
    """Retain locally for processing; never commit or export the content."""
    RESTRICTED = "restricted"
    """Terms forbid redistributing the text; keep locators and local features (R2.1)."""


class ArtifactRef(VersionedRecord):
    """A stored artifact, identified by the SHA-256 of its bytes.

    ``storage_ref`` is a repository-relative path or a non-file URI. An absolute local
    path would make otherwise identical records differ between machines (A §413) and
    would publish a home directory from this public repository.
    """

    content_sha256: Sha256Hex
    media_type: MediaType
    storage_ref: NonBlankStr
    rights_status: RightsStatus
    rights_basis: NonBlankStr

    @field_validator("storage_ref")
    @classmethod
    def _portable(cls, value: str) -> str:
        if value.startswith(("/", "~", "file:")) or "\\" in value:
            raise ValueError(
                f"storage_ref {value!r} must be a repository-relative path"
                " or a non-file URI"
            )
        return value

    @classmethod
    def for_bytes(
        cls,
        data: bytes,
        *,
        media_type: str,
        storage_ref: str,
        rights_status: RightsStatus,
        rights_basis: str,
    ) -> Self:
        """The reference for ``data``, with its SHA-256 computed here."""
        return cls(
            content_sha256=sha256_hex(data),
            media_type=media_type,
            storage_ref=storage_ref,
            rights_status=rights_status,
            rights_basis=rights_basis,
        )

    def matches(self, data: bytes) -> bool:
        """True when ``data`` is exactly the artifact this reference names."""
        return sha256_hex(data) == self.content_sha256
