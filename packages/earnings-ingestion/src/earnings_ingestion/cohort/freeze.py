"""Freeze a cohort build into a versioned, content-hashed manifest (P-A4).

- Freezing refuses while any blocking finding is unresolved, or any
  acknowledgement no longer matches its finding, and names each one.
- The content hash covers everything except the version, the hash itself, and the
  creation time. A build whose content matches the latest frozen manifest *is* that
  version, and nothing is written; different content is the next version. Every
  consumer reads a universe's latest version, so a build that holds an older
  version's content is refused: a universe is never reverted (PR #6's review, F4;
  plan 8, P8-4).
- The manifest is written to a temporary file and linked into place, so a partial
  manifest never appears and an existing one is never replaced.
- Loading reads the committed JSON alone, with no saved artifact, and rechecks the
  content hash.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from earnings_ingestion.cohort.build import CohortBuild, content_hash
from earnings_ingestion.cohort.config import UNIVERSE_DIR
from earnings_ingestion.cohort.records import Finding, UniverseManifest
from earnings_ingestion.fetch.store import write_new

MANIFESTS = UNIVERSE_DIR / "manifests"


class FreezeRefused(ValueError):
    """The build still holds blocking findings or stale acknowledgements."""

    def __init__(self, blocking: tuple[Finding, ...], stale: tuple[str, ...]) -> None:
        self.blocking = blocking
        self.stale = stale
        reasons = [f"{f.finding_id}: {f.detail}" for f in blocking]
        reasons += [f"{o}: acknowledges a finding that has changed" for o in stale]
        super().__init__("; ".join(reasons))


@dataclass(frozen=True)
class Frozen:
    manifest: UniverseManifest
    path: Path
    created: bool
    """False when an existing version already held this content."""


def manifest_path(directory: Path, universe_id: str, version: int) -> Path:
    return directory / f"{universe_id}-v{version}.json"


def serialize(manifest: UniverseManifest) -> bytes:
    """Indented JSON with sorted keys, for a readable diff between versions."""
    data = manifest.model_dump(mode="json")
    text = json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False)
    return f"{text}\n".encode()


def load_manifest(path: Path) -> UniverseManifest:
    """A committed manifest, refused if its name or content hash disagrees."""
    manifest = UniverseManifest.model_validate_json(path.read_bytes())
    definition = manifest.definition
    if content_hash(manifest) != definition.content_hash:
        raise ValueError(f"{path} does not hash to its content_hash")
    expected = manifest_path(
        path.parent, definition.universe_id, definition.universe_version
    )
    if path.name != expected.name:
        raise ValueError(f"{path} holds version {definition.universe_version}")
    return manifest


def repeated_content(named: list[tuple[str, str]]) -> None:
    """Refuse two frozen files, named in ``(name, content hash)`` pairs, that hold one
    content: a version is its content (P6-14), so a copy renumbered by hand would load
    beside it, and a consumer taking the latest version would read the copy (PR #6's
    review, F22)."""
    first: dict[str, str] = {}
    for name, digest in named:
        if digest in first:
            raise ValueError(f"{first[digest]} and {name} hold one content, {digest}")
        first[digest] = name


def frozen_manifests(directory: Path, universe_id: str) -> list[UniverseManifest]:
    """Every frozen version of ``universe_id``, oldest first; refused if two hold one
    content."""
    manifests = sorted(
        (load_manifest(path) for path in directory.glob(f"{universe_id}-v*.json")),
        key=lambda m: m.definition.universe_version,
    )
    repeated_content(
        [
            (
                manifest_path(
                    directory, universe_id, m.definition.universe_version
                ).name,
                m.definition.content_hash,
            )
            for m in manifests
        ]
    )
    return manifests


def freeze(build: CohortBuild, directory: Path, *, now: datetime) -> Frozen:
    blocking = build.report.blocking
    if blocking or build.stale_acknowledgements:
        raise FreezeRefused(blocking, build.stale_acknowledgements)
    universe_id = build.config.universe.universe_id
    existing = frozen_manifests(directory, universe_id)
    target = build.content_hash
    newest = max((m.definition.universe_version for m in existing), default=0)
    for manifest in existing:
        if manifest.definition.content_hash == target:
            path = manifest_path(
                directory, universe_id, manifest.definition.universe_version
            )
            if manifest.definition.universe_version != newest:
                raise ValueError(
                    f"the build is {path.name}'s content, but v{newest} is newer:"
                    " every consumer reads a universe's latest version, so a revert"
                    " is refused"
                )
            return Frozen(manifest=manifest, path=path, created=False)
    version = 1 + newest
    manifest = build.manifest(version, now)
    path = manifest_path(directory, universe_id, version)
    write_new(path, serialize(manifest))
    return Frozen(manifest=manifest, path=path, created=True)
