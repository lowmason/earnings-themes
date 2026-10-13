"""Phase-by-phase passes and frozen-policy runs. No pass or fresh run changes state."""

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

from earnings_core import digest, sha256_hex
from earnings_ingestion.fetch.store import write_new
from earnings_themes.coding import validate_proposal_support
from earnings_themes.coding.cache import CodingCache
from earnings_themes.coding.decide import AssignmentPolicy
from earnings_themes.coding.records import ClassificationRecord
from earnings_themes.coding.run import ProposalRun, propose_run
from earnings_themes.coding.store import (
    read_coding_run,
    write_coding_run,
)
from earnings_themes.evaluation import (
    CalibratedPolicy,
    CalibrationArtifact,
    EvaluationError,
    EvaluationProblem,
    frozen_configuration,
)
from earnings_themes.evaluation.calibration import configuration_hash
from earnings_themes.extraction.cache import CachedAdapter
from earnings_themes.extraction.records import ExtractionRejection
from earnings_themes.extraction.run import extract_run
from earnings_themes.extraction.store import StoredRun, read_run, write_run
from earnings_themes.records import checked, sealed
from earnings_themes.split import Partition
from earnings_themes.support import (
    assess_run,
    read_support_run,
    write_support_run,
)
from earnings_themes.support.cache import SupportCache
from earnings_themes.support.records import (
    EntailmentSignal,
    JudgeTrial,
    SupportSources,
    support_configuration,
)
from earnings_themes.support.scorers import EntailmentScorer
from earnings_themes.support.store import StoredSupportRun

from earnings_pipeline.pilot_records import (
    PassRecord,
    ProposalSnapshot,
    RunRecord,
    json_bytes,
    read_json,
)
from earnings_pipeline.theme_config import (
    FileSelection,
    StoredSelection,
    WorkflowConfig,
    WorkflowError,
    confined_path,
    read_selected,
    validate_paths,
)
from earnings_pipeline.theme_workflow import (
    WorkflowRuntime,
    finalize_coding,
    load_workflow_inputs,
    replay_runtime,
    run_theme_workflow,
    validate_workflow_policy,
    verify_extraction_configuration,
    workflow_configuration_hashes,
)


@dataclass(frozen=True, repr=False)
class LoadedPass:
    record: PassRecord
    sources: SupportSources
    proposal: ProposalRun
    primary: StoredSupportRun
    alternative: StoredSupportRun


def selected_file(config: WorkflowConfig, path: Path) -> FileSelection:
    return FileSelection(
        path=path.relative_to(config.repo).as_posix(),
        sha256=sha256_hex(path.read_bytes()),
    )


def selected_run(config: WorkflowConfig, path: Path) -> StoredSelection:
    return StoredSelection(
        directory=path.relative_to(config.repo).as_posix(),
        sha256=sha256_hex((path / "run.json").read_bytes()),
    )


def pilot_path(config: WorkflowConfig, path: Path) -> Path:
    return confined_path(
        config.repo, path.relative_to(config.repo).as_posix(), "data/runs/pilot"
    )


def phase_path(config: WorkflowConfig, path: Path) -> Path:
    path = pilot_path(config, path)
    if path.is_dir():
        for child in path.iterdir():
            pilot_path(config, child)
    return path


def stored_directory(config: WorkflowConfig, selected: StoredSelection) -> Path:
    path = phase_path(
        config, confined_path(config.repo, selected.directory, "data/runs/pilot")
    )
    if sha256_hex((path / "run.json").read_bytes()) != selected.sha256:
        raise WorkflowError("input_changed")
    # Every child is checked before a public reader can open it.
    for child in path.iterdir():
        confined_path(
            config.repo, child.relative_to(config.repo).as_posix(), "data/runs/pilot"
        )
    return path


def load_pass(config: WorkflowConfig, record: PassRecord) -> LoadedPass:
    checked(record, "pass")
    if record.configuration_hash != digest(config.model_dump(mode="json")):
        raise WorkflowError("input_changed")
    if record.event_ids != config.selected_event_ids:
        raise WorkflowError("input_changed")
    loaded = load_workflow_inputs(config, replay_runtime(config))
    extraction = read_run(stored_directory(config, record.extraction))
    verify_extraction_configuration(config, extraction, loaded.bundles, loaded.template)
    if (
        extraction.record.cache_mode != record.mode
        or extraction.record.stability_run_id != record.stability_run_id
    ):
        raise WorkflowError("input_changed")
    _integrity(extraction.rejections)
    sources = SupportSources(
        extraction, loaded.bundles, loaded.codebook, loaded.provenance_hash
    )
    path = confined_path(config.repo, record.proposals.path, "data/runs/pilot")
    read_selected(config, record.proposals)
    proposal = read_json(path, ProposalSnapshot, "proposals", seal=False).run()
    primary = read_support_run(stored_directory(config, record.primary))
    alternative = read_support_run(stored_directory(config, record.alternative))
    if primary.record.scorer_identity != config.scorer_identity or any(
        run.record.cache_mode != record.mode
        or run.record.stability_run_id != record.stability_run_id
        for run in (primary, alternative)
    ):
        raise WorkflowError("input_changed")
    if (
        proposal.record.configuration_hash
        != workflow_configuration_hashes(config, sources, cache_mode=record.mode)[0]
        or proposal.record.run_id != config.coding_run_id
        or proposal.record.stability_run_id != record.stability_run_id
    ):
        raise WorkflowError("input_changed")
    for run in (primary, alternative):
        expected = digest(
            support_configuration(
                config.support_policy,
                config.support_ceilings,
                run.record.scorer_identity,
                config.judge_identities,
                config.extractor_family,
                record.mode,
            )
        )
        if run.record.configuration_hash != expected:
            raise WorkflowError("input_changed")
    _integrity(proposal.classifications)
    _integrity(
        (
            *primary.entailment,
            *primary.trials,
            *alternative.entailment,
            *alternative.trials,
        )
    )
    validate_proposal_support(proposal, primary, sources)
    validate_proposal_support(proposal, alternative, sources)
    if tuple(t.target_id for t in primary.targets) != tuple(
        t.target_id for t in alternative.targets
    ):
        raise WorkflowError("input_changed")
    expected_status = (
        "complete"
        if _complete(extraction, proposal, primary, alternative)
        else "partial"
    )
    if record.status != expected_status:
        raise WorkflowError("input_changed")
    return LoadedPass(record, sources, proposal, primary, alternative)


def _complete(
    extraction: StoredRun, proposal: ProposalRun, *support: StoredSupportRun
) -> bool:
    return (
        all(d.outcome.value == "completed" for d in extraction.documents)
        and all(c.status == "completed" for c in proposal.classifications)
        and all(
            tuple(t.target for t in run.targets) == proposal.targets for run in support
        )
        and not any(
            o.status.value in {"incomplete", "refused"}
            for run in support
            for o in run.outcomes
        )
    )


def _integrity(
    rows: Iterable[
        ExtractionRejection | ClassificationRecord | EntailmentSignal | JudgeTrial
    ],
) -> None:
    for row in rows:
        reason = getattr(row, "reason", None)
        reason = getattr(reason, "value", reason)
        if reason in {
            "cache_corrupt",
            "input_changed",
            "model_mismatch",
            "malformed_record",
        }:
            raise WorkflowError(reason)


def check_cache_paths(config: WorkflowConfig, fresh: str | None) -> None:
    for reference in (
        config.extraction_cache,
        config.coding_cache,
        config.support_cache,
    ):
        path = confined_path(config.repo, reference, "data/runs/pilot")
        if fresh is not None:
            path = confined_path(
                config.repo, reference + "/fresh/" + fresh, "data/runs/pilot"
            )
        for child in path.glob("*.json"):
            pilot_path(config, child)


def make_pass(
    config: WorkflowConfig,
    runtime: WorkflowRuntime,
    alternative: EntailmentScorer,
    *,
    partition: Partition,
    directory: Path,
    fresh: str | None,
    support_ready: Callable[[], None],
    now: Callable[[], datetime],
) -> PassRecord:
    if partition not in (Partition.TRAIN, Partition.DEV) or (
        fresh and partition is not Partition.DEV
    ):
        raise WorkflowError("malformed_record")
    directory = confined_path(
        config.repo, directory.relative_to(config.repo).as_posix(), "data/runs/pilot"
    )
    check_cache_paths(config, fresh)
    mode = "fresh" if fresh is not None else "live"
    if fresh is not None:
        for cache in (
            config.extraction_cache,
            config.coding_cache,
            config.support_cache,
        ):
            confined_path(config.repo, cache + "/fresh/" + fresh, "data/runs/pilot")
    if fresh is not None and (
        directory.exists()
        or any(
            (confined_path(config.repo, cache) / "fresh" / fresh).exists()
            for cache in (
                config.extraction_cache,
                config.coding_cache,
                config.support_cache,
            )
        )
    ):
        raise WorkflowError("state_run_conflict")
    manifest = pilot_path(config, directory / "pass.json")
    if manifest.exists():
        record = read_json(manifest, PassRecord, "pass")
        load_pass(config, record)
        return record
    for name in ("extraction", "support", "alternative", "proposals.json", "pass.json"):
        phase_path(config, directory / name)
    loaded = load_workflow_inputs(config, runtime)
    directory.mkdir(parents=True, exist_ok=True)
    started = config.fixture_started_at or now()
    extract_dir = phase_path(config, directory / "extraction")
    if not extract_dir.exists():
        result = extract_run(
            loaded.bundles,
            CachedAdapter(
                runtime.extractor,
                confined_path(config.repo, config.extraction_cache),
                mode,
                stability_run_id=fresh,
            ),
            config.extraction_policy,
            loaded.template,
            config.extraction_ceilings,
            run_id=config.extraction_run_id,
            started_at=started,
            software=config.software,
        )
        write_run(extract_dir, StoredRun.of(result), loaded.bundles)
    extraction = read_run(extract_dir)
    verify_extraction_configuration(config, extraction, loaded.bundles, loaded.template)
    if (
        extraction.record.cache_mode != mode
        or extraction.record.stability_run_id != fresh
    ):
        raise WorkflowError("input_changed")
    _integrity(extraction.rejections)
    sources = SupportSources(
        extraction, loaded.bundles, loaded.codebook, loaded.provenance_hash
    )
    snapshot = pilot_path(config, directory / "proposals.json")
    if snapshot.exists():
        proposal = read_json(snapshot, ProposalSnapshot, "proposals", seal=False).run()
    else:
        proposal = propose_run(
            config.coding_run_id,
            sources,
            tuple((c.doc_id, c.claim_id) for c in extraction.claims),
            runtime.classifier,
            config.coding_policy,
            config.coding_ceilings,
            cache=CodingCache(
                confined_path(config.repo, config.coding_cache),
                mode,
                stability_run_id=fresh,
            ),
            started_at=extraction.record.started_at,
            software=config.software,
        )
        write_new(snapshot, json_bytes(ProposalSnapshot.of(proposal)))
    if (
        proposal.record.configuration_hash
        != workflow_configuration_hashes(config, sources, cache_mode=mode)[0]
        or proposal.record.run_id != config.coding_run_id
        or proposal.record.stability_run_id != fresh
    ):
        raise WorkflowError("input_changed")
    _integrity(proposal.classifications)
    # The local server operator performs this checkpoint; adapters cannot unload servers.
    support_ready()
    supports = []
    for kind, scorer in (("support", runtime.scorer), ("alternative", alternative)):
        path = phase_path(config, directory / kind)
        if not path.exists():
            support = assess_run(
                config.support_run_id
                + ("-alternative" if kind == "alternative" else ""),
                sources,
                proposal.targets,
                scorer,
                runtime.judges,
                config.support_policy,
                config.support_ceilings,
                extractor_family=config.extractor_family,
                cache=SupportCache(
                    confined_path(config.repo, config.support_cache),
                    mode,
                    stability_run_id=fresh,
                ),
                started_at=extraction.record.started_at,
                software=config.software,
            )
            write_support_run(path, support, sources)
        support = read_support_run(path)
        if (
            support.record.scorer_identity != scorer.identity
            or support.record.cache_mode != mode
            or support.record.stability_run_id != fresh
        ):
            raise WorkflowError("input_changed")
        expected = digest(
            support_configuration(
                config.support_policy,
                config.support_ceilings,
                scorer.identity,
                config.judge_identities,
                config.extractor_family,
                mode,
            )
        )
        if support.record.configuration_hash != expected:
            raise WorkflowError("input_changed")
        _integrity((*support.entailment, *support.trials))
        validate_proposal_support(proposal, support, sources)
        supports.append(support)
    status = "complete" if _complete(extraction, proposal, *supports) else "partial"
    record = sealed(
        PassRecord(
            partition=partition,
            mode=mode,
            stability_run_id=fresh,
            event_ids=config.selected_event_ids,
            configuration_hash=digest(config.model_dump(mode="json")),
            extraction=selected_run(config, extract_dir),
            proposals=selected_file(config, snapshot),
            primary=selected_run(config, directory / "support"),
            alternative=selected_run(config, directory / "alternative"),
            status=status,
            content_hash="0" * 64,
        )
    )
    write_new(manifest, json_bytes(record))
    return record


def bind_policy(
    config: WorkflowConfig,
    loaded: LoadedPass,
    artifact: CalibrationArtifact,
    *,
    replay: bool,
) -> AssignmentPolicy | None:
    checked(artifact, "calibration")
    frozen = frozen_configuration(
        loaded.sources.stored_run.record,
        loaded.proposal.record,
        loaded.primary.record,
        config.support_policy,
    )
    if configuration_hash(frozen, artifact.selection) != artifact.configuration_hash:
        raise WorkflowError("input_changed")
    if replay:
        coding_hash, support_hash = workflow_configuration_hashes(
            config, loaded.sources
        )
    else:
        coding_hash, support_hash = (
            loaded.proposal.record.configuration_hash,
            loaded.primary.record.configuration_hash,
        )
    try:
        return CalibratedPolicy(
            artifact,
            codebook=loaded.primary.record.codebook,
            classifier_configuration_hash=coding_hash,
            support_configuration_hash=support_hash,
        )
    except EvaluationError as error:
        if error.problem is EvaluationProblem.NO_CANDIDATE:
            return None
        raise


def verify_replay_cache(config: WorkflowConfig, loaded: LoadedPass) -> None:
    """Exercise every primary replay request before publication or state changes."""
    check_cache_paths(config, None)
    runtime = replay_runtime(config)
    proposal = propose_run(
        config.coding_run_id,
        loaded.sources,
        tuple((c.doc_id, c.claim_id) for c in loaded.sources.stored_run.claims),
        runtime.classifier,
        config.coding_policy,
        config.coding_ceilings,
        cache=CodingCache(confined_path(config.repo, config.coding_cache), "replay"),
        started_at=loaded.sources.stored_run.record.started_at,
        software=config.software,
    )
    for row in proposal.classifications:
        if row.reason in {"replay_miss", "replay_dispatch_forbidden"}:
            raise WorkflowError("replay_miss")
        if row.reason in {
            "cache_corrupt",
            "input_changed",
            "model_mismatch",
            "malformed_record",
        }:
            raise WorkflowError(row.reason)
    support = assess_run(
        config.support_run_id,
        loaded.sources,
        proposal.targets,
        runtime.scorer,
        runtime.judges,
        config.support_policy,
        config.support_ceilings,
        extractor_family=config.extractor_family,
        cache=SupportCache(confined_path(config.repo, config.support_cache), "replay"),
        started_at=loaded.sources.stored_run.record.started_at,
        software=config.software,
    )
    for assessment in support.assessments:
        for row in (*assessment.entailment, *assessment.trials):
            if row.reason in {"replay_miss", "replay_dispatch_forbidden"}:
                raise WorkflowError("replay_miss")
            if row.reason in {
                "cache_corrupt",
                "input_changed",
                "model_mismatch",
                "malformed_record",
            }:
                raise WorkflowError(row.reason)


def make_run(
    config: WorkflowConfig,
    loaded: LoadedPass,
    artifact: CalibrationArtifact,
    *,
    directory: Path,
    now: Callable[[], datetime],
) -> RunRecord:
    directory = confined_path(
        config.repo, directory.relative_to(config.repo).as_posix(), "data/runs/pilot"
    )
    fresh = loaded.record.stability_run_id
    if fresh is None and loaded.record.mode != "live":
        raise WorkflowError("input_changed")
    policy = bind_policy(config, loaded, artifact, replay=fresh is None)
    coding_dir = phase_path(config, directory / "coding")
    if fresh is not None:
        coding = finalize_coding(
            loaded.proposal, loaded.primary, loaded.sources, policy
        )
        write_coding_run(coding_dir, coding, loaded.sources, loaded.primary, policy)
    else:
        verify_replay_cache(config, loaded)
        fields = config.model_dump(mode="json")
        fields.update(
            output_dir=directory.relative_to(config.repo).as_posix(),
            stored_extraction=loaded.record.extraction.model_dump(mode="json"),
            stored_coding=None,
            stored_support=None,
            stored_analysis=None,
            policy_reference=None
            if policy is None
            else policy.reference.model_dump(mode="json"),
        )
        replay_config = WorkflowConfig.model_validate_json(json.dumps(fields))
        validate_paths(replay_config, repo=config.repo)
        runtime = replace(replay_runtime(replay_config), assignment_policy=policy)
        validate_workflow_policy(replay_config, policy)
        result = run_theme_workflow(replay_config, runtime, now=now)
        if result.status == "failed" or result.reason in {
            "replay_miss",
            "replay_dispatch_forbidden",
        }:
            raise WorkflowError(result.reason or "processing_failed")
    coding = read_coding_run(coding_dir)
    # Cache misses can be represented as refused/incomplete stage rows; none is a successful replay.
    if fresh is None and any(
        reason in {"replay_miss", "replay_dispatch_forbidden"}
        for reason, _ in (
            *coding.record.counts_by_reason,
            *coding.record.counts_by_decision_reason,
        )
    ):
        raise WorkflowError("replay_miss")
    pass_path = (
        confined_path(
            config.repo, loaded.record.extraction.directory, "data/runs/pilot"
        ).parent
        / "pass.json"
    )
    record = sealed(
        RunRecord(
            partition=loaded.record.partition,
            fresh=fresh,
            event_ids=loaded.record.event_ids,
            pass_record=selected_file(config, pass_path),
            coding=selected_run(config, coding_dir),
            calibration_hash=artifact.content_hash,
            configuration_hash=artifact.configuration_hash,
            status=loaded.record.status,
            content_hash="0" * 64,
        )
    )
    write_new(pilot_path(config, directory / "run-record.json"), json_bytes(record))
    return record
