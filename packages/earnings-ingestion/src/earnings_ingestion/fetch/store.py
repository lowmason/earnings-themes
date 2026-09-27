"""Saved source artifacts under ``data/raw/``: content-addressed, never overwritten.

Each source has a directory, named by its register ``source_id``. An artifact's bytes
are stored once, named by their SHA-256, with one ``Retrieval`` record for each time
they were fetched or registered, named by its time and its own hash. Every write goes to a temporary file and is
hard-linked into place, which fails rather than replace an existing file: writing the
same bytes again is a no-op, and different bytes raise ``FileExistsError`` (the capture
store's rule, plan 5). Reprocessing reads these files and never fetches (A §410).
"""

import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from earnings_core import ArtifactRef, RightsStatus, sha256_hex

from earnings_ingestion.fetch.records import SOURCE_ID_PATTERN, Retrieval

EXTENSIONS = {
    "application/json": ".json",
    "application/pdf": ".pdf",
    "application/xml": ".xml",
    "text/html": ".html",
    "text/plain": ".txt",
    "text/xml": ".xml",
}
_SOURCE_ID = re.compile(SOURCE_ID_PATTERN)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class StoredArtifact:
    """An artifact's bytes, its reference, and every retrieval of it, oldest first."""

    ref: ArtifactRef
    body: bytes
    retrievals: tuple[Retrieval, ...]


class ArtifactStore:
    """``root`` lies under ``repo``'s ``data/raw/``; references are repo-relative."""

    def __init__(self, root: Path, repo: Path) -> None:
        self.root = root
        self.repo = repo

    def put(
        self,
        source_id: str,
        body: bytes,
        retrieval: Retrieval,
        *,
        rights_status: RightsStatus,
        rights_basis: str,
    ) -> ArtifactRef:
        """Store ``body`` and its retrieval record; return the artifact's reference."""
        if retrieval.sha256 != sha256_hex(body) or retrieval.byte_count != len(body):
            raise ValueError("the retrieval record describes other bytes")
        path = self._artifact_path(source_id, retrieval.sha256, retrieval.media_type)
        write_new(path, body)
        data = retrieval.model_dump_json().encode("utf-8")
        stamp = retrieval.retrieved_at.strftime("%Y%m%dT%H%M%S%fZ")
        name = f"{stamp}-{sha256_hex(data)[:12]}.json"
        write_new(self._retrieval_dir(source_id, retrieval.sha256) / name, data)
        return self._ref(path, body, retrieval, rights_status, rights_basis)

    def retrievals(self, source_id: str, sha256: str) -> tuple[Retrieval, ...]:
        """Every retrieval of the artifact, oldest first; empty if none is stored."""
        folder = self._retrieval_dir(source_id, sha256)
        if not folder.is_dir():
            return ()
        records = [
            Retrieval.model_validate_json(path.read_text(encoding="utf-8"))
            for path in folder.glob("*.json")
        ]
        return tuple(sorted(records, key=lambda record: record.retrieved_at))

    def get(
        self,
        source_id: str,
        sha256: str,
        *,
        rights_status: RightsStatus,
        rights_basis: str,
    ) -> StoredArtifact:
        """The stored artifact; ``FileNotFoundError`` if absent, ``ValueError`` if its
        bytes no longer hash to its name."""
        retrievals = self.retrievals(source_id, sha256)
        if not retrievals:
            raise FileNotFoundError(
                f"no artifact {sha256} for source {source_id!r} under {self.root}"
            )
        path = self._artifact_path(source_id, sha256, retrievals[0].media_type)
        if not path.is_file():
            raise FileNotFoundError(
                f"no artifact {sha256} for source {source_id!r}: its retrieval records"
                " remain, but its bytes are gone"
            )
        body = path.read_bytes()
        if sha256_hex(body) != sha256:
            raise ValueError(f"{path} no longer hashes to its name")
        ref = self._ref(path, body, retrievals[0], rights_status, rights_basis)
        return StoredArtifact(ref=ref, body=body, retrievals=retrievals)

    def latest(
        self,
        source_id: str,
        url: str,
        *,
        rights_status: RightsStatus,
        rights_basis: str,
    ) -> StoredArtifact | None:
        """The artifact most recently retrieved from ``url``, or ``None``."""
        self._check(source_id, "0" * 64)
        folder = self.root / source_id / "retrievals"
        records = [
            Retrieval.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(folder.glob("*/*.json"))
        ]
        matching = [record for record in records if record.request_url == url]
        if not matching:
            return None
        newest = max(matching, key=lambda record: (record.retrieved_at, record.sha256))
        return self.get(
            source_id,
            newest.sha256,
            rights_status=rights_status,
            rights_basis=rights_basis,
        )

    def _ref(
        self,
        path: Path,
        body: bytes,
        retrieval: Retrieval,
        rights_status: RightsStatus,
        rights_basis: str,
    ) -> ArtifactRef:
        return ArtifactRef.for_bytes(
            body,
            media_type=retrieval.media_type,
            storage_ref=path.relative_to(self.repo).as_posix(),
            rights_status=rights_status,
            rights_basis=rights_basis,
        )

    def _artifact_path(self, source_id: str, sha256: str, media_type: str) -> Path:
        self._check(source_id, sha256)
        return self.root / source_id / f"{sha256}{EXTENSIONS.get(media_type, '.bin')}"

    def _retrieval_dir(self, source_id: str, sha256: str) -> Path:
        self._check(source_id, sha256)
        return self.root / source_id / "retrievals" / sha256

    @staticmethod
    def _check(source_id: str, sha256: str) -> None:
        if not _SOURCE_ID.match(source_id):
            raise ValueError(f"source_id {source_id!r} is not a register slug")
        if not _SHA256.match(sha256):
            raise ValueError(f"{sha256!r} is not a SHA-256 digest")


def write_new(path: Path, data: bytes) -> None:
    """Write ``data`` to a new file at ``path``, atomically; the same bytes again are
    a no-op, and other bytes raise ``FileExistsError``."""
    if path.exists():
        if path.read_bytes() == data:
            return
        raise FileExistsError(f"{path} holds other bytes")
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(handle, "wb") as out:
            out.write(data)
        os.link(temporary, path)
    finally:
        os.unlink(temporary)
