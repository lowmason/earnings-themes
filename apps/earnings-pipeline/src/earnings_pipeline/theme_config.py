"""Strict explicit selections for the offline theme workflow; no source discovery."""

import re
from datetime import datetime
from pathlib import Path
from typing import Literal, Self

from earnings_core import sha256_hex
from earnings_themes.analysis import (
    ANALYSIS_REASONS,
    AnalysisPart,
    AnalysisPolicy,
    CopyAssertion,
    NoThemeDeclaration,
    ThemeFamilyMap,
)
from earnings_themes.coding.records import CodingCeilings, CodingPolicy, PolicyReference
from earnings_themes.extraction.records import (
    AdapterIdentity,
    Ceilings,
    ExtractionPolicy,
)
from earnings_themes.support.records import (
    JudgeIdentity,
    ScorerIdentity,
    SupportCeilings,
    SupportPolicy,
)
from pydantic import Field, PrivateAttr, model_validator

WORKFLOW_REASONS = ANALYSIS_REASONS | {
    "state_not_processable",
    "state_storage_corrupt",
    "state_run_conflict",
    "state_history_invalid",
    "state_predecessor_mismatch",
    "state_record_invalid",
    "state_schema_invalid",
    "storage_corrupt",
    "malformed_record",
    "replay_miss",
}
SAFE_COMPONENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]*")
CANONICAL_ID = re.compile(r"[A-Za-z0-9._:-]+@[A-Za-z0-9._:-]+#[a-f0-9]{16}")


class WorkflowError(ValueError):
    """Only closed reasons leave application boundaries."""

    def __init__(self, reason: str) -> None:
        self.reason = (
            reason
            if type(reason) is str and reason in WORKFLOW_REASONS
            else "unexpected_error"
        )
        super().__init__(self.reason)


class FileSelection(AnalysisPart):
    path: str = Field(repr=False)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class StoredSelection(AnalysisPart):
    directory: str = Field(repr=False)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class SourceSelection(AnalysisPart):
    event_id: str
    doc_id: str
    canonical: FileSelection
    metadata: FileSelection
    raw: FileSelection | None

    @model_validator(mode="after")
    def _identities(self) -> Self:
        if (
            SAFE_COMPONENT.fullmatch(self.event_id) is None
            or CANONICAL_ID.fullmatch(self.doc_id) is None
        ):
            raise ValueError("malformed_record")
        return self


class WorkflowConfig(AnalysisPart):
    run_id: str
    scope: Literal["fixture", "research"]
    mode: Literal["replay"]
    fixture_started_at: datetime | None
    input_root: str = Field(repr=False)
    universe: FileSelection
    universe_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    events: FileSelection
    event_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    pilot: FileSelection
    pilot_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    selected_event_ids: tuple[str, ...]
    states_dir: str = Field(repr=False)
    acquisition_files: tuple[FileSelection, ...]
    sources: tuple[SourceSelection, ...]
    codebook: FileSelection
    extraction_prompt: FileSelection
    coding_prompt: FileSelection
    support_prompt: FileSelection
    extraction_policy: ExtractionPolicy
    extraction_ceilings: Ceilings
    extraction_identity: AdapterIdentity
    extractor_family: str
    coding_policy: CodingPolicy
    coding_ceilings: CodingCeilings
    classifier_identity: JudgeIdentity
    support_policy: SupportPolicy
    support_ceilings: SupportCeilings
    scorer_identity: ScorerIdentity
    judge_identities: tuple[JudgeIdentity, JudgeIdentity]
    extraction_run_id: str
    coding_run_id: str
    support_run_id: str
    extraction_cache: str = Field(repr=False)
    coding_cache: str = Field(repr=False)
    support_cache: str = Field(repr=False)
    stored_extraction: StoredSelection | None
    stored_support: StoredSelection | None
    stored_coding: StoredSelection | None
    stored_analysis: StoredSelection | None
    assignment_policy: Literal["fixture-supporting/1"] | None
    policy_reference: PolicyReference | None
    analysis_policy: AnalysisPolicy
    families: ThemeFamilyMap | None
    copies: tuple[CopyAssertion, ...]
    no_theme: tuple[NoThemeDeclaration, ...]
    audience: Literal["local", "export"]
    output_dir: str = Field(repr=False)
    capture: bool
    capture_policy: dict | None = Field(repr=False)
    installed_binary_reference: FileSelection | None
    software: dict[str, str] = Field(repr=False)
    lockfile: FileSelection
    _repo: Path = PrivateAttr()

    @model_validator(mode="after")
    def _selections(self) -> Self:
        if any(
            SAFE_COMPONENT.fullmatch(v) is None or v in {".", ".."}
            for v in (
                self.run_id,
                self.extraction_run_id,
                self.coding_run_id,
                self.support_run_id,
                *self.selected_event_ids,
            )
        ):
            raise ValueError("malformed_record")
        if (
            tuple(sorted(set(self.selected_event_ids))) != self.selected_event_ids
            or self.selected_event_ids != self.analysis_policy.event_ids
        ):
            raise ValueError("malformed_record")
        if (
            self.analysis_policy.scope != self.scope
            or self.analysis_policy.population_hash != self.pilot_hash
        ):
            raise ValueError("malformed_record")
        if self.fixture_started_at is not None and (
            self.scope != "fixture"
            or self.fixture_started_at.tzinfo is None
            or self.fixture_started_at.utcoffset().total_seconds() != 0
        ):
            raise ValueError("malformed_record")
        if self.scope == "research" and self.assignment_policy is not None:
            raise ValueError("malformed_record")
        if self.scope == "fixture" and self.analysis_policy.population_id not in {
            "djia-synthetic",
            "stage10-invented",
        }:
            raise ValueError("malformed_record")
        if self.assignment_policy is not None and self.policy_reference is not None:
            raise ValueError("malformed_record")
        if self.stored_analysis is not None and any(
            v is None
            for v in (self.stored_extraction, self.stored_support, self.stored_coding)
        ):
            raise ValueError("malformed_record")
        if (
            len({s.event_id for s in self.sources}) != len(self.sources)
            or len({s.doc_id for s in self.sources}) != len(self.sources)
            or any(s.event_id not in self.selected_event_ids for s in self.sources)
        ):
            raise ValueError("malformed_record")
        if self.capture != (
            self.capture_policy is not None
            and self.installed_binary_reference is not None
        ):
            raise ValueError("malformed_record")
        if self.software.get("lock_hash") != self.lockfile.sha256:
            raise ValueError("malformed_record")
        return self

    @property
    def repo(self) -> Path:
        return self._repo


def confined_path(repo: Path, reference: str, root: str = ".") -> Path:
    """Reject absolute/traversing/symlinked paths without opening their contents."""
    if (
        type(reference) is not str
        or not reference
        or "\\" in reference
        or Path(reference).is_absolute()
        or any(v in {".", ".."} for v in reference.split("/"))
    ):
        raise WorkflowError("malformed_record")
    path = repo / reference
    intended = repo if root == "." else repo / root
    if not path.resolve().is_relative_to(
        repo.resolve()
    ) or not path.resolve().is_relative_to(intended.resolve()):
        raise WorkflowError("malformed_record")
    if any(p.is_symlink() for p in (path, *path.parents) if p != repo.parent):
        raise WorkflowError("malformed_record")
    return path


def validate_paths(config: WorkflowConfig, *, repo: Path) -> None:
    confined_path(repo, config.input_root)
    for selected in (
        config.universe,
        config.events,
        config.pilot,
        config.codebook,
        config.extraction_prompt,
        config.coding_prompt,
        config.support_prompt,
    ):
        confined_path(repo, selected.path, config.input_root)
    for source in config.sources:
        for selected in (source.canonical, source.metadata, source.raw):
            if selected is not None:
                confined_path(repo, selected.path, config.input_root)
    for reference in (
        config.states_dir,
        config.output_dir,
        config.extraction_cache,
        config.coding_cache,
        config.support_cache,
    ):
        confined_path(repo, reference, "data/runs")
    for selected in config.acquisition_files:
        confined_path(repo, selected.path, config.states_dir)
    for selected in (
        config.stored_extraction,
        config.stored_support,
        config.stored_coding,
        config.stored_analysis,
    ):
        if selected is not None:
            confined_path(repo, selected.directory, "data/runs")
    confined_path(repo, config.lockfile.path)
    if config.installed_binary_reference is not None:
        confined_path(repo, config.installed_binary_reference.path, config.input_root)
    # Fixture authorization cannot turn this checkout's protected tree into input.
    project = Path(__file__).resolve().parents[4]
    if (
        repo.resolve() == project
        and config.scope == "fixture"
        and config.input_root.startswith("data/")
    ):
        raise WorkflowError("malformed_record")
    config._repo = repo.resolve()


def load_workflow_config(path: Path, *, repo: Path) -> WorkflowConfig:
    """Read this JSON only, confine every selection before any source loading."""
    try:
        config = WorkflowConfig.model_validate_json(path.read_bytes())
        validate_paths(config, repo=repo)
        if config.policy_reference is not None:
            raise WorkflowError("policy_unavailable")
        return config
    except WorkflowError:
        raise
    except Exception:  # noqa: BLE001 - metadata-only boundary; never expose parser details.
        raise WorkflowError("malformed_record") from None


def read_selected(config: WorkflowConfig, selected: FileSelection) -> bytes:
    data = confined_path(config.repo, selected.path).read_bytes()
    if sha256_hex(data) != selected.sha256:
        raise WorkflowError("input_changed")
    return data
