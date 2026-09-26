"""Cite evidence in a saved artifact, and verify a citation, without its wording.

Two locator kinds exist (plan 6, P6-9):

- ``text_span``: code-point offsets into the walker-1 canonical text of an HTML
  artifact. The locator records the canonicalization version and the canonical text's
  hash, so a different text can never silently move the span.
- ``json_pointer``: an RFC 6901 pointer into a JSON artifact.

``cited_sha256`` hashes the cited content: the span's text as UTF-8, or the canonical
JSON of the value at the pointer. Verification recomputes it from the saved bytes.
The cited content itself never enters a committed file; ``ArtifactText.cited`` returns
it for a person's terminal.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from functools import cached_property

from earnings_core import ArtifactRef, sha256_hex

from earnings_ingestion.canonical import (
    CANONICALIZATION_VERSION,
    CanonicalizationFailure,
    canonicalize,
)
from earnings_ingestion.cohort.digests import canonical_json
from earnings_ingestion.cohort.records import Citation, EvidenceLocator, LocatorKind


class LocatorError(ValueError):
    """A locator that does not identify the content it claims to."""


def _essence(media_type: str) -> str:
    return media_type.partition(";")[0].strip().lower()


def resolve_json_pointer(document: object, pointer: str) -> object:
    """The value at an RFC 6901 pointer; ``LocatorError`` if there is none."""
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise LocatorError(f"{pointer!r} is not a JSON pointer")
    value = document
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict) and token in value:
            value = value[token]
        elif (
            isinstance(value, list)
            and token.isdigit()
            and (token == "0" or not token.startswith("0"))
            and int(token) < len(value)
        ):
            value = value[int(token)]
        else:
            raise LocatorError(f"{pointer!r} names nothing in the document")
    return value


class ArtifactText:
    """One saved artifact, read once: canonical text if HTML, parsed data if JSON."""

    def __init__(self, body: bytes, media_type: str) -> None:
        self.body = body
        self.media_type = _essence(media_type)

    @cached_property
    def canonical(self) -> tuple[str, str]:
        """walker-1's canonical text and its hash."""
        if self.media_type != "text/html":
            raise LocatorError(f"a text span needs HTML, not {self.media_type}")
        result = canonicalize(
            self.body, source_document_id="cohort-evidence", media_type="text/html"
        )
        if isinstance(result, CanonicalizationFailure):
            raise LocatorError(f"walker-1 cannot read it: {result.detail}")
        return result.document.canonical_text, result.document.canonical_hash

    @cached_property
    def data(self) -> object:
        if self.media_type != "application/json":
            raise LocatorError(f"a JSON pointer needs JSON, not {self.media_type}")
        try:
            return json.loads(self.body)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LocatorError(f"it is not JSON: {exc}") from exc

    def span(self, start: int, end: int) -> EvidenceLocator:
        text, text_hash = self.canonical
        if not 0 <= start < end <= len(text):
            raise LocatorError(f"[{start}, {end}) is outside [0, {len(text)})")
        return EvidenceLocator(
            kind=LocatorKind.TEXT_SPAN,
            canonicalization_version=CANONICALIZATION_VERSION,
            canonical_sha256=text_hash,
            start=start,
            end=end,
            cited_sha256=sha256_hex(text[start:end].encode("utf-8")),
        )

    def find(self, needle: str, occurrence: int = 1) -> EvidenceLocator:
        """The span of the ``occurrence``-th (1-based) appearance of ``needle``."""
        text, _ = self.canonical
        start = -1
        for _ in range(occurrence):
            start = text.find(needle, start + 1)
            if start == -1:
                count = "" if occurrence == 1 else f" {occurrence} times"
                raise LocatorError(f"{needle!r} does not occur{count}")
        return self.span(start, start + len(needle))

    def line(self, needle: str, occurrence: int = 1) -> EvidenceLocator:
        """The span of the whole line holding the ``occurrence``-th ``needle``.
        walker-1 writes a table row as one line of tab-separated cells, so this
        cites a roster row with every cell in it."""
        found = self.find(needle, occurrence)
        text, _ = self.canonical
        start = text.rfind("\n", 0, found.start) + 1
        end = text.find("\n", found.end)
        return self.span(start, len(text) if end == -1 else end)

    def pointer(self, pointer: str) -> EvidenceLocator:
        value = resolve_json_pointer(self.data, pointer)
        return EvidenceLocator(
            kind=LocatorKind.JSON_POINTER,
            pointer=pointer,
            cited_sha256=sha256_hex(canonical_json(value)),
        )

    def cited(self, locator: EvidenceLocator) -> str:
        """The content ``locator`` cites, once it has been verified."""
        self.verify(locator)
        if locator.kind is LocatorKind.TEXT_SPAN:
            return self.canonical[0][locator.start : locator.end]
        value = resolve_json_pointer(self.data, locator.pointer)
        return canonical_json(value).decode("utf-8")

    def verify(self, locator: EvidenceLocator) -> None:
        """Raise ``LocatorError`` unless ``locator`` still cites what it hashed."""
        if locator.kind is LocatorKind.TEXT_SPAN:
            if locator.canonicalization_version != CANONICALIZATION_VERSION:
                raise LocatorError(
                    f"the span was made under {locator.canonicalization_version},"
                    f" not {CANONICALIZATION_VERSION}"
                )
            if self.canonical[1] != locator.canonical_sha256:
                raise LocatorError("the artifact's canonical text is not the one cited")
            fresh = self.span(locator.start, locator.end)
        else:
            fresh = self.pointer(locator.pointer)
        if fresh.cited_sha256 != locator.cited_sha256:
            raise LocatorError("the cited content no longer hashes to cited_sha256")


@dataclass(frozen=True)
class CitableArtifact:
    """A stored artifact with what a citation of it records."""

    source_id: str
    url: str
    artifact: ArtifactRef
    retrieved_at: datetime
    text: ArtifactText

    def cite(self, *locators: EvidenceLocator) -> Citation:
        return Citation(
            source_id=self.source_id,
            url=self.url,
            artifact=self.artifact,
            retrieved_at=self.retrieved_at,
            locators=locators,
        )
