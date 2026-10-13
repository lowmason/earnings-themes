"""Metadata-only partition and visibility gates precede every A8 source read."""

import subprocess
from dataclasses import dataclass
from pathlib import Path

from earnings_core import sha256_hex
from earnings_themes.annotation import check_countable
from earnings_themes.codebook import Codebook
from earnings_themes.evaluation import Preregistration, load_preregistration
from earnings_themes.gold import CodebookRef, Gold, load_gold
from earnings_themes.independent import ledger_check
from earnings_themes.records import RecordError
from earnings_themes.split import Partition, SplitManifest

from earnings_pipeline.codebook_cli import pinned_codebook, pinned_split
from earnings_pipeline.pilot_records import PilotSettings, load_settings
from earnings_pipeline.stage6 import (
    CODEBOOK_FILE,
    Layout,
    Pinned,
    derive_split,
    documents,
    file_stem,
    independent_path,
    load_pinned,
    read_ledger,
)
from earnings_pipeline.theme_config import (
    FileSelection,
    WorkflowConfig,
    WorkflowError,
    confined_path,
    parse_workflow_config,
)


@dataclass(frozen=True, repr=False)
class PilotIntake:
    layout: Layout
    pinned: Pinned
    split: SplitManifest
    codebook: Codebook
    preregistration: Preregistration
    settings: PilotSettings
    config: WorkflowConfig
    partition: Partition
    gold: tuple[Gold, ...]

    @property
    def local(self) -> Path:
        return confined_path(self.layout.repo, "data/runs/pilot", "data/runs/pilot")


def require_committed(repo: Path, path: Path, name: str) -> None:
    """A signed metadata file must be identical to HEAD before it opens a source."""
    path = confined_path(repo, path.relative_to(repo).as_posix())
    try:
        result = subprocess.run(
            ["git", "show", "HEAD:" + path.relative_to(repo).as_posix()],
            cwd=repo,
            capture_output=True,
            check=False,
        )
        committed = result.returncode == 0 and result.stdout == path.read_bytes()
    except OSError:
        raise RecordError(name, ("not_committed",)) from None
    if not committed:
        raise RecordError(name, ("not_committed",))


def _configuration(repo: Path, selected: FileSelection) -> WorkflowConfig:
    path = confined_path(repo, selected.path)
    if sha256_hex(path.read_bytes()) != selected.sha256:
        raise WorkflowError("input_changed")
    return parse_workflow_config(path, repo=repo)


def open_pilot(
    layout: Layout, settings_path: Path, partition: Partition
) -> PilotIntake:
    if partition not in (Partition.TRAIN, Partition.DEV):
        raise WorkflowError("malformed_record")
    pinned = load_pinned(layout)
    split = pinned_split(layout, pinned)
    if split != derive_split(layout, pinned):
        raise RecordError("split", ("binding_mismatch",))
    if pinned.events.definition.corpus_id == "djia-2024q3-2026q2" and (
        len(split.events_in(Partition.TRAIN)) != 20
        or len(split.events_in(Partition.DEV)) != 8
    ):
        raise RecordError("visibility", ("partition_count_mismatch",))
    codebook = pinned_codebook(layout)
    selected = tuple(
        sorted((*split.events_in(Partition.TRAIN), *split.events_in(Partition.DEV)))
    )
    # A missing signature is detected before acquisition metadata or settings can open a source.
    missing = [
        event
        for event in selected
        if not (pinned.gold_dir / f"{file_stem(event)}.toml").is_file()
    ]
    if missing:
        raise RecordError(
            "visibility", tuple(f"{event}: not_signed" for event in missing)
        )
    doc_ids = documents(layout, pinned)
    gold = []
    for event in selected:
        path = pinned.gold_dir / f"{file_stem(event)}.toml"
        require_committed(layout.repo, path, "gold")
        record = load_gold(path)
        if record.doc_id != doc_ids.get(event):
            raise RecordError("visibility", (f"{event}: document_mismatch",))
        if refusals := check_countable(
            record,
            event_id=event,
            pin=pinned.pin,
            split=split,
            codebook=codebook,
            doc_id=doc_ids[event],
        ):
            raise RecordError(
                "visibility",
                tuple(f"{event} {r.subject}: {r.reason}" for r in refusals),
            )
        gold.append(record)
    require_committed(
        layout.repo, pinned.evaluation / "independent-pass.toml", "ledger"
    )
    ledger = read_ledger(pinned)
    for event in split.events_in(Partition.DEV):
        selected_path = independent_path(layout, event)
        path = confined_path(
            layout.repo,
            selected_path.relative_to(layout.repo).as_posix(),
            "data/runs/gold/independent",
        )
        data = path.read_bytes() if path.is_file() else None
        if problem := ledger_check(ledger, event, data):
            raise RecordError("visibility", (f"{event}: {problem.value}",))
    require_committed(
        layout.repo, pinned.evaluation / "preregistration-v1.toml", "preregistration"
    )
    preregistration = load_preregistration(
        pinned.evaluation / "preregistration-v1.toml"
    )
    book_ref = CodebookRef(
        codebook_id=codebook.codebook_id,
        codebook_version=codebook.codebook_version,
        content_hash=codebook.content_hash,
    )
    if (
        preregistration.pin != pinned.pin
        or preregistration.split_hash != split.content_hash
        or preregistration.codebook != book_ref
    ):
        raise RecordError("preregistration", ("binding_mismatch",))
    settings = load_settings(settings_path, repo=layout.repo)
    configs = {
        Partition.TRAIN: _configuration(layout.repo, settings.train),
        Partition.DEV: _configuration(layout.repo, settings.dev),
    }
    book_hash = sha256_hex((layout.repo / CODEBOOK_FILE).read_bytes())
    for part, config in configs.items():
        if config.codebook.sha256 != book_hash or {
            source.event_id: source.doc_id for source in config.sources
        } != {event: doc_ids[event] for event in split.events_in(part)}:
            raise RecordError("settings", ("source_binding_mismatch",))
        if (
            config.scope != "research"
            or config.selected_event_ids != tuple(sorted(split.events_in(part)))
            or config.pilot_hash != pinned.pin.pilot_hash
            or config.policy_reference is not None
            or config.assignment_policy is not None
            or any(
                value is not None
                for value in (
                    config.stored_extraction,
                    config.stored_coding,
                    config.stored_support,
                    config.stored_analysis,
                )
            )
        ):
            raise WorkflowError("malformed_record")
        for reference in (
            config.extraction_cache,
            config.coding_cache,
            config.support_cache,
            config.output_dir,
        ):
            confined_path(layout.repo, reference, "data/runs/pilot")
    a, b = configs[Partition.TRAIN], configs[Partition.DEV]
    for field in (
        "extraction_identity",
        "extractor_family",
        "extraction_policy",
        "extraction_ceilings",
        "classifier_identity",
        "coding_policy",
        "coding_ceilings",
        "scorer_identity",
        "judge_identities",
        "support_policy",
        "support_ceilings",
        "codebook",
        "extraction_prompt",
        "coding_prompt",
        "support_prompt",
    ):
        if getattr(a, field) != getattr(b, field):
            raise RecordError("settings", (f"{field}: configuration_mismatch",))
    return PilotIntake(
        layout,
        pinned,
        split,
        codebook,
        preregistration,
        settings,
        configs[partition],
        partition,
        tuple(g for g in gold if g.partition is partition),
    )
