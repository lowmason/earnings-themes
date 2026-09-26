"""Retrieval metadata for one saved source artifact (Stage 4).

Stage 2 left retrieval metadata to Stage 4 (plan 3, Handoffs to Stage 4): core records
no source URL, retrieval time, or request. ``Retrieval`` is ingestion's record of one
retrieval of one artifact. The identity sent as the User-Agent is never recorded.
docs/data-dictionary.md documents every field.
"""

from datetime import timedelta
from enum import StrEnum
from typing import Annotated, Self

from earnings_core.artifacts import MediaType, NonBlankStr
from earnings_core.hashing import Sha256Hex
from pydantic import AwareDatetime, NonNegativeInt, StringConstraints, model_validator

from earnings_ingestion.canonical.records import IngestionRecord

SOURCE_ID_PATTERN = r"^[a-z0-9][a-z0-9-]*$"
SourceId = Annotated[str, StringConstraints(pattern=SOURCE_ID_PATTERN)]
"""A source register key: a lowercase slug, safe as a directory name."""


class RetrievalMethod(StrEnum):
    """How an artifact's bytes reached the store."""

    HTTP = "http"
    """Fetched by this package's client, under its access policy."""
    SAVED_BY_USER = "saved_by_user"
    """Saved by a person in a browser and registered by hash; nothing was fetched."""


class Retrieval(IngestionRecord):
    """One retrieval: where the bytes came from, when, and what they hash to."""

    request_url: NonBlankStr
    final_url: NonBlankStr
    retrieved_at: AwareDatetime
    retrieval_method: RetrievalMethod
    http_status: int | None
    media_type: MediaType
    content_type: str
    byte_count: NonNegativeInt
    sha256: Sha256Hex

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.retrieved_at.utcoffset() != timedelta(0):
            raise ValueError("retrieved_at must be in UTC")
        if (self.retrieval_method is RetrievalMethod.HTTP) != (
            self.http_status is not None
        ):
            raise ValueError("http_status is recorded exactly for an HTTP retrieval")
        return self
