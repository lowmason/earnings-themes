"""A8's strict configuration and local checkpoints; metadata checkpoints carry IDs and hashes; proposal snapshots stay local."""

import json
from pathlib import Path
from typing import Literal, Self

from earnings_core import canonical_json
from earnings_themes.coding.records import (
    AttributeRecord,
    ClassificationRecord,
    CodingAttempt,
    NoveltyItem,
    ProposalRecord,
    ProposalRunRecord,
)
from earnings_themes.coding.run import ProposalRun
from earnings_themes.evaluation import CalibrationArtifact
from earnings_themes.records import (
    IdPart,
    Part,
    RecordError,
    Sha256Hex,
    ThemesRecord,
    checked,
    parse,
)
from earnings_themes.split import Partition
from earnings_themes.support.records import ScorerIdentity
from pydantic import model_validator

from earnings_pipeline.theme_config import (
    FileSelection,
    StoredSelection,
    WorkflowError,
    confined_path,
)


class PilotSettings(Part):
    """Two explicit workflow selections and the B1 runtime manifest."""

    train: FileSelection
    dev: FileSelection
    runtime_manifest: FileSelection
    alternative_scorer: ScorerIdentity


class ProposalSnapshot(Part):
    """Local classifier output, persisted before any assignment decision exists."""

    record: ProposalRunRecord
    classifications: tuple[ClassificationRecord, ...]
    attempts: tuple[CodingAttempt, ...]
    proposals: tuple[ProposalRecord, ...]
    attributes: tuple[AttributeRecord, ...]
    novelty: tuple[NoveltyItem, ...]

    @classmethod
    def of(cls, run: ProposalRun) -> Self:
        return cls(**{name: getattr(run, name) for name in cls.model_fields})

    def run(self) -> ProposalRun:
        return ProposalRun(
            **{name: getattr(self, name) for name in type(self).model_fields}
        )


class PassRecord(ThemesRecord):
    """A local pass with stored extraction, proposals and both support runs."""

    partition: Partition
    mode: Literal["live", "fresh"]
    stability_run_id: IdPart | None
    event_ids: tuple[IdPart, ...]
    configuration_hash: Sha256Hex
    extraction: StoredSelection
    proposals: FileSelection
    primary: StoredSelection
    alternative: StoredSelection
    status: Literal["complete", "partial"]
    content_hash: Sha256Hex

    @model_validator(mode="after")
    def _partition_and_mode(self) -> Self:
        if self.partition not in (Partition.TRAIN, Partition.DEV):
            raise ValueError("wrong_partition")
        if (self.mode == "fresh") != (self.stability_run_id is not None):
            raise ValueError("malformed_record")
        if self.mode == "fresh" and self.partition is not Partition.DEV:
            raise ValueError("wrong_partition")
        if tuple(sorted(set(self.event_ids))) != self.event_ids:
            raise ValueError("malformed_record")
        return self


class RunRecord(ThemesRecord):
    """A local frozen-policy run, referencing its pass and coding decisions."""

    partition: Partition
    fresh: IdPart | None
    event_ids: tuple[IdPart, ...]
    pass_record: FileSelection
    coding: StoredSelection
    calibration_hash: Sha256Hex
    configuration_hash: Sha256Hex
    status: Literal["complete", "partial"]
    content_hash: Sha256Hex

    @model_validator(mode="after")
    def _partition(self) -> Self:
        if self.partition not in (Partition.TRAIN, Partition.DEV):
            raise ValueError("wrong_partition")
        if self.fresh is not None and self.partition is not Partition.DEV:
            raise ValueError("wrong_partition")
        if tuple(sorted(set(self.event_ids))) != self.event_ids:
            raise ValueError("malformed_record")
        return self


def load_settings(path: Path, *, repo: Path) -> PilotSettings:
    settings = read_json(path, PilotSettings, "settings", seal=False)
    for selected in (settings.train, settings.dev, settings.runtime_manifest):
        confined_path(repo, selected.path)
    if settings.alternative_scorer.kind != "deberta":
        raise WorkflowError("model_mismatch")
    return settings


def read_json[M: Part](
    path: Path, model: type[M], name: str, *, seal: bool = True
) -> M:
    """Closed reader; names are caller-owned field paths, never untrusted filenames."""
    try:
        value = json.loads(path.read_bytes())
    except (OSError, ValueError):
        raise RecordError(name, ("malformed_record",)) from None
    result = parse(value, model, name)
    return checked(result, name) if seal else result


def read_calibration(path: Path) -> CalibrationArtifact:
    return read_json(path, CalibrationArtifact, "calibration")


def json_bytes(record: Part) -> bytes:
    return canonical_json(record.model_dump(mode="json"))
