"""The curated cohort files, committed under ``config/universe/<name>/``.

- ``universe.toml``: the universe's definition, and the fund whose holdings
  corroborate it.
- ``evidence.toml``: every snapshot, change, and check list, as facts plus citations.
  A snapshot or change names its artifact by hash, and each fact by the offsets and
  hash of the canonical text that states it; no source wording is written here.
- ``overrides.toml``: the reviewer's decisions (``Override`` records).

Each file is read through canonical JSON into strict models, so a TOML date, string,
or array means exactly what the model says, and an unknown key is refused.
"""

from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal, Self

import tomllib
from earnings_core.artifacts import NonBlankStr
from earnings_core.documents import IdPart
from earnings_core.hashing import Sha256Hex
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    NonNegativeInt,
    PositiveInt,
    model_validator,
)

from earnings_ingestion.cohort.digests import canonical_json
from earnings_ingestion.cohort.records import BoundTiming, Override
from earnings_ingestion.fetch.records import SourceId
from earnings_ingestion.sec.identifiers import Cik

UNIVERSE_DIR = Path("config") / "universe" / "djia"


class _Curated(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class EtfProxy(_Curated):
    """The fund whose N-PORT holdings corroborate the roster (an ETF proxy)."""

    source_id: SourceId
    cik: Cik
    forms: tuple[NonBlankStr, ...] = ("NPORT-P", "NPORT-P/A")


class UniverseConfig(_Curated):
    universe_id: IdPart
    universe_name: IdPart
    period_end_start: date
    period_end_stop: date
    public_information_cutoff: date
    membership_reference: Literal["first_publication_time"]
    selection_policy_version: NonBlankStr
    expected_member_count: PositiveInt
    etf_proxy: EtfProxy | None = None


class Row(_Curated):
    """One security as a snapshot or change states it, and where it says so."""

    security_id: IdPart
    name: NonBlankStr
    ticker: NonBlankStr
    span: tuple[NonNegativeInt, NonNegativeInt]
    cited_sha256: Sha256Hex

    @model_validator(mode="after")
    def _span(self) -> Self:
        if self.span[0] >= self.span[1]:
            raise ValueError(f"span {list(self.span)} is empty or reversed")
        return self


class ChangeRow(Row):
    action: Literal["added", "removed"]


class _Cited(_Curated):
    evidence_id: IdPart
    source_id: SourceId
    url: NonBlankStr
    artifact_sha256: Sha256Hex
    canonical_sha256: Sha256Hex
    published_on: date
    published_at: AwareDatetime | None = None


class SnapshotEvidence(_Cited):
    """A dated roster: the anchor, or a corroborating snapshot."""

    role: Literal["anchor", "corroboration"]
    as_of: date
    members: tuple[Row, ...]


class ChangeEvidence(_Cited):
    """An announcement of additions and removals, with where it states its date."""

    announced_on: date
    effective_on: date
    timing: BoundTiming
    date_span: tuple[NonNegativeInt, NonNegativeInt]
    date_cited_sha256: Sha256Hex
    entries: tuple[ChangeRow, ...]

    @model_validator(mode="after")
    def _span(self) -> Self:
        if self.date_span[0] >= self.date_span[1]:
            raise ValueError(f"date_span {list(self.date_span)} is empty or reversed")
        return self


class CheckMember(_Curated):
    name: NonBlankStr
    ticker: NonBlankStr


class CheckList(_Curated):
    """A list compared with the reconstruction and reported; it decides nothing."""

    evidence_id: IdPart
    source_id: SourceId
    as_of: date
    published_on: date
    members: tuple[CheckMember, ...]


class EvidenceFile(_Curated):
    schema_version: Literal[1]
    snapshots: tuple[SnapshotEvidence, ...] = ()
    changes: tuple[ChangeEvidence, ...] = ()
    checks: tuple[CheckList, ...] = ()

    @model_validator(mode="after")
    def _distinct(self) -> Self:
        ids = [item.evidence_id for item in (*self.snapshots, *self.changes)]
        ids += [check.evidence_id for check in self.checks]
        repeated = sorted(key for key, count in Counter(ids).items() if count > 1)
        if repeated:
            raise ValueError(f"evidence_id repeated: {repeated}")
        if sum(snapshot.role == "anchor" for snapshot in self.snapshots) > 1:
            raise ValueError("at most one snapshot is the anchor")
        for item in (*self.snapshots, *self.changes):
            rows = item.members if isinstance(item, SnapshotEvidence) else item.entries
            keys = [(row.security_id, getattr(row, "action", "")) for row in rows]
            if len(set(keys)) != len(keys):
                raise ValueError(f"{item.evidence_id} states a security twice")
        return self


class OverridesFile(_Curated):
    schema_version: Literal[1]
    overrides: tuple[Override, ...] = ()

    @model_validator(mode="after")
    def _distinct(self) -> Self:
        ids = [override.override_id for override in self.overrides]
        if len(set(ids)) != len(ids):
            raise ValueError("override_id repeated")
        return self


@dataclass(frozen=True)
class CohortConfig:
    universe: UniverseConfig
    evidence: EvidenceFile
    overrides: OverridesFile


def load_toml[M: BaseModel](path: Path, model: type[M]) -> M:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return model.model_validate_json(canonical_json(data))


def load_cohort_config(directory: Path) -> CohortConfig:
    """The three curated files in ``directory``; ``overrides.toml`` may be absent."""
    overrides = directory / "overrides.toml"
    return CohortConfig(
        universe=load_toml(directory / "universe.toml", UniverseConfig),
        evidence=load_toml(directory / "evidence.toml", EvidenceFile),
        overrides=(
            load_toml(overrides, OverridesFile)
            if overrides.exists()
            else OverridesFile(schema_version=1)
        ),
    )
