"""Freeze the event manifest, with its evidence record beside it (the Stage 5 spec,
§The event manifest; P6-14).

- Freezing refuses while anything holds the freeze, and names each: an unanswered
  blocking finding, a stale override, and an ``ambiguous`` row no override retains.
- Content that matches a frozen manifest *is* that version, and nothing is written,
  whatever the evidence says: a re-fetch with the same facts writes nothing. New
  content is the next version.
- ``events-v<N>.evidence.json`` is written first and ``events-v<N>.json`` second, each
  to a temporary file linked into place: a manifest never appears without its
  evidence, and neither is ever replaced.
- A directory holds one corpus's versions: freezing refuses a build of another, and
  loading refuses a directory that holds two. Listing them also refuses two versions
  of one content, and a manifest whose evidence record is missing (PR #6's review,
  F22); loading one file checks neither, since the pilot's chain check reads it
  alone.
- Loading reads the committed JSON alone and rechecks the content hash and the name.
  An evidence record loads only with its manifest: the same ``corpus_id``, version,
  and content hash, and one citation per row, in the rows' order.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from earnings_ingestion.cohort.freeze import repeated_content
from earnings_ingestion.events.build import EventBuild
from earnings_ingestion.events.evidence import evidence_of
from earnings_ingestion.events.records import (
    EventEvidence,
    EventManifest,
    content_hash,
)
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.fetch.store import write_new


class EventFreezeRefused(ValueError):
    """The build still holds the freeze; the message names each reason."""

    def __init__(self, build: EventBuild) -> None:
        self.reasons = tuple(
            [f"{f.finding_id}: {f.detail}" for f in build.blocking]
            + [f"{o}: a stale override" for o in build.stale_overrides]
            + [
                f"{row.event_id}: {row.eligibility_reason}, not retained"
                for row in build.unretained
            ]
        )
        super().__init__("; ".join(self.reasons))


@dataclass(frozen=True)
class FrozenEvents:
    manifest: EventManifest
    path: Path
    evidence_path: Path
    created: bool
    """False when an existing version already held this content."""


def manifest_path(directory: Path, version: int) -> Path:
    return directory / f"events-v{version}.json"


def evidence_path(directory: Path, version: int) -> Path:
    return directory / f"events-v{version}.evidence.json"


def serialize(record: BaseModel) -> bytes:
    """Indented JSON with sorted keys, for a readable diff between versions."""
    data = record.model_dump(mode="json")
    text = json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False)
    return f"{text}\n".encode()


def load_event_manifest(path: Path) -> EventManifest:
    """A committed event manifest, refused if its name or content hash disagrees."""
    manifest = EventManifest.model_validate_json(path.read_bytes())
    definition = manifest.definition
    if content_hash(manifest) != definition.content_hash:
        raise ValueError(f"{path} does not hash to its content_hash")
    if path.name != manifest_path(path.parent, definition.event_manifest_version).name:
        raise ValueError(f"{path} holds version {definition.event_manifest_version}")
    return manifest


def load_event_evidence(path: Path, manifest: EventManifest) -> EventEvidence:
    """A committed evidence record, refused if its name disagrees, or unless it is
    ``manifest``'s: the same ``corpus_id``, version, and content hash, and one
    citation per row, in the rows' order."""
    evidence = EventEvidence.model_validate_json(path.read_bytes())
    if path.name != evidence_path(path.parent, evidence.event_manifest_version).name:
        raise ValueError(f"{path} holds version {evidence.event_manifest_version}")
    definition = manifest.definition
    if content_hash(manifest) != definition.content_hash:
        raise ValueError(f"{path}: its manifest does not hash to its content_hash")
    for field, found, expected in (
        ("corpus_id", evidence.corpus_id, definition.corpus_id),
        (
            "event_manifest_version",
            evidence.event_manifest_version,
            definition.event_manifest_version,
        ),
        ("event_manifest_hash", evidence.event_manifest_hash, definition.content_hash),
    ):
        if found != expected:
            raise ValueError(
                f"{path}: {field} {found} is not the manifest's {expected}"
            )
    cited = [citations.event_id for citations in evidence.events]
    if cited != [row.event_id for row in manifest.rows]:
        raise ValueError(
            f"{path}: the event_ids of its events are not the manifest's rows, in order"
        )
    return evidence


def frozen_event_manifests(directory: Path) -> list[EventManifest]:
    """Every frozen version in ``directory``, oldest first, refused if they name more
    than one corpus (a file names its version, not its corpus), if two hold one
    content, or if a manifest's evidence record is missing."""
    manifests = sorted(
        (
            load_event_manifest(path)
            for path in directory.glob("events-v*.json")
            if not path.name.endswith(".evidence.json")
        ),
        key=lambda m: m.definition.event_manifest_version,
    )
    if len(corpora := sorted({m.definition.corpus_id for m in manifests})) > 1:
        raise ValueError(f"{directory} holds more than one corpus: {corpora}")
    versions = [m.definition.event_manifest_version for m in manifests]
    repeated_content(
        [
            (manifest_path(directory, version).name, m.definition.content_hash)
            for version, m in zip(versions, manifests, strict=True)
        ]
    )
    for version in versions:
        if not evidence_path(directory, version).exists():
            raise ValueError(
                f"{manifest_path(directory, version).name} has no"
                f" {evidence_path(directory, version).name}"
            )
    return manifests


def freeze_events(
    build: EventBuild, saved: SavedResponses, directory: Path, *, now: datetime
) -> FrozenEvents:
    """Freeze ``build`` into ``directory``, or return the version that holds it.
    Refused if ``directory`` holds another corpus."""
    if build.holds_freeze:
        raise EventFreezeRefused(build)
    existing = frozen_event_manifests(directory)
    if existing and (held := existing[0].definition.corpus_id) != build.corpus_id:
        raise ValueError(f"{directory} holds corpus {held}, not {build.corpus_id}")
    for manifest in existing:
        if manifest.definition.content_hash == build.content_hash:
            version = manifest.definition.event_manifest_version
            return FrozenEvents(
                manifest=manifest,
                path=manifest_path(directory, version),
                evidence_path=evidence_path(directory, version),
                created=False,
            )
    version = 1 + max(
        (m.definition.event_manifest_version for m in existing), default=0
    )
    manifest = build.manifest(version, now)
    evidence = evidence_of(build, manifest, saved)
    directory.mkdir(parents=True, exist_ok=True)
    write_new(evidence_path(directory, version), serialize(evidence))
    write_new(manifest_path(directory, version), serialize(manifest))
    return FrozenEvents(
        manifest=manifest,
        path=manifest_path(directory, version),
        evidence_path=evidence_path(directory, version),
        created=True,
    )
