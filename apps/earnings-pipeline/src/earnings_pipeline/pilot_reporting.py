"""Verified local observations produce counts-only feasibility reports and gates."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from earnings_ingestion.events.coverage import build_coverage, load_coverage
from earnings_ingestion.events.states import ProcessingTransition
from earnings_themes.annotation import load_gold_draft, recount
from earnings_themes.coding import validate_proposal_support
from earnings_themes.coding.decide import AssignmentPolicy, decision_inputs
from earnings_themes.coding.records import CodingRun
from earnings_themes.coding.store import read_coding_run, reverify_coding_run
from earnings_themes.evaluation import (
    IndependentFigures,
    PilotReport,
    SupportLabelSet,
    claim_label,
    derive_gates,
    gates_toml,
    joint_label,
    joint_score,
)
from earnings_themes.evaluation.align import unit_index
from earnings_themes.evaluation.report import (
    Accepted,
    EventObservation,
    LabelledTarget,
    compare_readings,
    partition_report,
    stability_figures,
)
from earnings_themes.extraction.store import StoredRun
from earnings_themes.independent import verify_independent
from earnings_themes.records import RecordError, sealed
from earnings_themes.split import Partition
from earnings_themes.support import read_support_run
from earnings_themes.support.records import ReviewStatus
from earnings_themes.support.store import StoredSupportRun

from earnings_pipeline.pilot_calibration import (
    evaluation_path,
    validate_calibration_labels,
)
from earnings_pipeline.pilot_inputs import PilotIntake, require_committed
from earnings_pipeline.pilot_labels import (
    _checked,
    checked_pass,
    committed_labels,
    sample,
)
from earnings_pipeline.pilot_records import (
    PassRecord,
    RunRecord,
    json_bytes,
    read_calibration,
    read_json,
)
from earnings_pipeline.pilot_workflow import (
    LoadedPass,
    bind_policy,
    load_pass,
    phase_path,
    stored_directory,
)
from earnings_pipeline.stage6 import (
    file_stem,
    independent_path,
    kept_drafts,
    read_ledger,
    write_once,
)
from earnings_pipeline.theme_config import WorkflowError, confined_path, read_selected
from earnings_pipeline.theme_workflow import (
    _baseline,
    _checked_history,
    load_workflow_inputs,
    replay_runtime,
    workflow_configuration_hashes,
)


@dataclass(frozen=True, repr=False)
class LoadedRun:
    record: RunRecord
    passed: LoadedPass
    primary: StoredSupportRun
    coding: CodingRun
    policy: AssignmentPolicy | None


def load_run(intake: PilotIntake, path: Path) -> LoadedRun:
    config = intake.config
    path = confined_path(
        config.repo, path.relative_to(config.repo).as_posix(), "data/runs/pilot"
    )
    record = read_json(path, RunRecord, "run")
    if (
        record.partition is not intake.partition
        or record.event_ids != config.selected_event_ids
    ):
        raise WorkflowError("input_changed")
    artifact_path = evaluation_path(intake, "calibration-v1.json")
    require_committed(config.repo, artifact_path, "calibration")
    artifact = read_calibration(artifact_path)
    if artifact.preregistration_hash != intake.preregistration.content_hash:
        raise WorkflowError("input_changed")
    validate_calibration_labels(intake, artifact)
    if (
        record.calibration_hash != artifact.content_hash
        or record.configuration_hash != artifact.configuration_hash
    ):
        raise WorkflowError("input_changed")
    pass_path = confined_path(config.repo, record.pass_record.path, "data/runs/pilot")
    read_selected(config, record.pass_record)
    passed = load_pass(config, read_json(pass_path, PassRecord, "pass"))
    checked_pass(intake, passed, fresh=record.fresh is not None)
    if (
        record.fresh != passed.record.stability_run_id
        or record.status != passed.record.status
    ):
        raise WorkflowError("input_changed")
    policy = bind_policy(config, passed, artifact, replay=record.fresh is None)
    coding_dir = stored_directory(config, record.coding)
    primary = (
        passed.primary
        if record.fresh is not None
        else read_support_run(phase_path(config, coding_dir.parent / "support"))
    )
    if record.fresh is None and (
        primary.record.configuration_hash
        != workflow_configuration_hashes(config, passed.sources)[1]
        or primary.record.cache_mode != "replay"
        or primary.record.stability_run_id is not None
    ):
        raise WorkflowError("input_changed")
    if (
        primary.record.scorer_identity != config.scorer_identity
        or tuple(t.target for t in primary.targets) != passed.proposal.targets
    ):
        raise WorkflowError("input_changed")
    validate_proposal_support(passed.proposal, primary, passed.sources)
    coding = read_coding_run(coding_dir)
    expected_coding = workflow_configuration_hashes(
        config, passed.sources, cache_mode="fresh" if record.fresh else "replay"
    )[0]
    if coding.record.configuration_hash != expected_coding:
        raise WorkflowError("input_changed")
    if coding.record.stability_run_id != record.fresh or coding.record.cache_mode != (
        "fresh" if record.fresh else "replay"
    ):
        raise WorkflowError("input_changed")
    reverify_coding_run(coding, passed.sources, primary, policy)
    return LoadedRun(record, passed, primary, coding, policy)


def quote_retention(extraction: StoredRun, doc_id: str) -> tuple[int, int]:
    kept = sum(len(c.quote_ids) for c in extraction.claims if c.doc_id == doc_id)
    rejected = sum(
        len(r.labels)
        for r in extraction.rejections
        if r.doc_id == doc_id and r.candidate_index is not None
    )
    return kept, kept + rejected


def observations(intake: PilotIntake, run: LoadedRun) -> tuple[EventObservation, ...]:
    checked_pass(intake, run.passed, fresh=run.record.fresh is not None)
    sources = run.passed.sources
    extraction = sources.stored_run
    bundles = {bundle.document.doc_id: bundle for bundle in sources.bundles}
    gold = {record.event_id: record for record in intake.gold}
    quotes = {(q.span.doc_id, q.quote_id): q.span for q in extraction.quotes}
    inputs = load_workflow_inputs(intake.config, replay_runtime(intake.config))
    if inputs.provenance_hash != sources.provenance_hash:
        raise WorkflowError("input_changed")
    history = _checked_history(
        intake.config, confined_path(intake.config.repo, intake.config.states_dir)
    )
    baseline, _ = _baseline(
        intake.config,
        [r for r in history if not isinstance(r, ProcessingTransition)],
        None,
    )
    out = []
    for source in intake.config.sources:
        doc_id = source.doc_id
        bundle = bundles.get(doc_id)
        if bundle is None or source.event_id not in gold:
            raise RecordError("observations", (f"{source.event_id}: missing_document",))
        accepted = tuple(
            Accepted(
                decision.theme_id,
                tuple(
                    (quotes[(doc_id, q)].start, quotes[(doc_id, q)].end)
                    for q in decision.supporting_quote_ids
                ),
            )
            for decision in run.coding.decisions
            if decision.doc_id == doc_id and decision.status == "accepted"
        )
        state = baseline[source.event_id + ":release"]
        if state.doc_id != doc_id or state.to_state.value != "parsed":
            raise RecordError(
                "observations", (f"{source.event_id}: missing_acquisition",)
            )
        kept = [
            a
            for a in state.attempts
            if (a.accession, a.filename, a.artifact_sha256)
            == (state.accession, state.exhibit, state.artifact_sha256)
        ]
        if len(kept) > 1:
            raise RecordError(
                "observations", (f"{source.event_id}: duplicate_attempt",)
            )
        confirmed = bool(kept and kept[0].outcome.value == "confirmed")
        targets = {
            t.target_id for t in run.primary.targets if t.target.doc_id == doc_id
        }
        assessed = sum(
            outcome.target_id in targets and outcome.status is ReviewStatus.ASSESSED
            for outcome in run.primary.outcomes
        )
        out.append(
            EventObservation(
                source.event_id,
                gold[source.event_id],
                unit_index(bundle),
                accepted,
                confirmed,
                quote_retention(extraction, doc_id),
                (
                    sum(
                        d.status == "accepted"
                        for d in run.coding.decisions
                        if d.doc_id == doc_id
                    ),
                    assessed,
                ),
            )
        )
    return tuple(out)


def labelled_targets(
    intake: PilotIntake, run: LoadedRun, labels: SupportLabelSet
) -> tuple[LabelledTarget, ...]:
    own = SupportLabelSet(
        preregistration_hash=labels.preregistration_hash,
        train_extensions=labels.train_extensions,
        labels=labels.of(intake.partition),
    )
    _checked(
        own, intake, run.passed, sample(intake, run.passed, labels.train_extensions)
    )
    primary = decision_inputs(run.primary, run.passed.sources)
    alternative = decision_inputs(run.passed.alternative, run.passed.sources)
    targets = {t.target_id: t for t in run.primary.targets}
    events = {s.doc_id: s.event_id for s in intake.config.sources}
    accepted = {d.target_id for d in run.coding.decisions if d.status == "accepted"}
    return tuple(
        LabelledTarget(
            label.target_id,
            events[targets[label.target_id].target.doc_id],
            claim_label(label),
            joint_label(label),
            label.target_id in accepted,
            {
                "minicheck": joint_score(primary[label.target_id]),
                "deberta": joint_score(alternative[label.target_id]),
            },
            primary[label.target_id].trials,
        )
        for label in own.labels
    )


def recount_all(intake: PilotIntake, run: LoadedRun) -> None:
    bundles = {b.name: b for b in run.passed.sources.bundles}
    for gold in intake.gold:
        draft, working = kept_drafts(intake.layout, gold.event_id)
        paths = [
            confined_path(
                intake.config.repo,
                p.relative_to(intake.config.repo).as_posix(),
                "data/runs/gold/drafts",
            )
            for p in (draft, working)
        ]
        path = intake.pinned.gold_dir / f"{file_stem(gold.event_id)}.toml"
        require_committed(intake.config.repo, path, "gold")
        found = recount(
            path.read_bytes(),
            load_gold_draft(paths[0]),
            load_gold_draft(paths[1]),
            bundle=bundles[gold.event_id],
            pin=intake.pinned.pin,
            split=intake.split,
            codebook=intake.codebook,
        )
        if found:
            raise RecordError(
                "gold", tuple(f"{gold.event_id} {r.subject}: {r.reason}" for r in found)
            )


def independent_figures(
    intake: PilotIntake, loaded: LoadedPass
) -> tuple[IndependentFigures, ...]:
    if intake.partition is not Partition.DEV:
        raise RecordError("partition", ("wrong_partition",))
    checked_pass(intake, loaded)
    require_committed(
        intake.config.repo, intake.pinned.evaluation / "independent-pass.toml", "ledger"
    )
    ledger = read_ledger(intake.pinned)
    bundles = {b.name: b for b in loaded.sources.bundles}
    signed = {g.event_id: g for g in intake.gold}
    out = []
    for event in intake.config.selected_event_ids:
        draft, _ = kept_drafts(intake.layout, event)
        draft = confined_path(
            intake.config.repo,
            draft.relative_to(intake.config.repo).as_posix(),
            "data/runs/gold/drafts",
        )
        local = independent_path(intake.layout, event)
        local = confined_path(
            intake.config.repo,
            local.relative_to(intake.config.repo).as_posix(),
            "data/runs/gold/independent",
        )
        readings = verify_independent(
            event,
            ledger=ledger,
            record=local.read_bytes() if local.is_file() else None,
            drafted=load_gold_draft(draft),
            bundle=bundles[event],
            codebook=intake.codebook,
        )
        if isinstance(readings, list):
            raise RecordError(
                "independent",
                tuple(f"{event} {r.subject}: {r.reason}" for r in readings),
            )
        index = unit_index(bundles[event])
        out.append(
            IndependentFigures(
                event_id=event,
                record_vs_draft=compare_readings(
                    readings.record, readings.draft, index
                ),
                signed_vs_record=compare_readings(
                    signed[event], readings.record, index
                ),
            )
        )
    return tuple(out)


def checked_stability(
    runs: Sequence[LoadedRun],
    events: tuple[str, ...],
    configuration_hash: str,
    calibration_hash: str,
) -> tuple[str, ...]:
    ids = tuple(run.record.fresh for run in runs)
    if (
        len(runs) != 3
        or any(
            run.record.partition is not Partition.DEV
            or run.record.status != "complete"
            or run.record.fresh is None
            or run.record.event_ids != events
            or run.record.configuration_hash != configuration_hash
            or run.record.calibration_hash != calibration_hash
            for run in runs
        )
        or len(set(ids)) != 3
    ):
        raise RecordError("stability", ("complete_fresh_runs",))
    return tuple(str(run_id) for run_id in ids)


def write_report(
    train: PilotIntake,
    dev: PilotIntake,
    train_run: LoadedRun,
    dev_run: LoadedRun,
    fresh: Sequence[LoadedRun],
    *,
    version: int = 1,
) -> Path:
    target = evaluation_path(train, f"report-v{version}.json")
    if (
        train.partition is not Partition.TRAIN
        or dev.partition is not Partition.DEV
        or train.preregistration != dev.preregistration
    ):
        raise RecordError("partition", ("wrong_partition",))
    if (
        train_run.record.fresh is not None
        or dev_run.record.fresh is not None
        or train_run.record.calibration_hash != dev_run.record.calibration_hash
        or train_run.record.configuration_hash != dev_run.record.configuration_hash
    ):
        raise WorkflowError("input_changed")
    ids = checked_stability(
        fresh,
        dev.config.selected_event_ids,
        dev_run.record.configuration_hash,
        dev_run.record.calibration_hash,
    )
    # GS5 is a gate for the whole report, before any shares or output are built.
    coverage_gate(train)
    recount_all(train, train_run)
    recount_all(dev, dev_run)
    labels = committed_labels(train)
    if labels is None:
        raise RecordError("labels", ("missing_labels",))
    plan = train.preregistration.bootstrap
    train_report = partition_report(
        observations(train, train_run),
        labelled_targets(train, train_run, labels),
        train.codebook,
        plan,
        partition=Partition.TRAIN,
    )
    dev_report = partition_report(
        observations(dev, dev_run),
        labelled_targets(dev, dev_run, labels),
        dev.codebook,
        plan,
        partition=Partition.DEV,
    )
    figures = stability_figures(
        tuple(observations(dev, run) for run in fresh), dev.codebook, plan, run_ids=ids
    )
    dev_report = dev_report.model_copy(
        update={"figures": (*dev_report.figures, *figures)}
    )
    report = sealed(
        PilotReport(
            report_version=version,
            preregistration_hash=train.preregistration.content_hash,
            calibration_hash=train_run.record.calibration_hash,
            partitions=(train_report, dev_report),
            independent=independent_figures(dev, dev_run.passed),
            content_hash="0" * 64,
        )
    )
    write_once(target, json_bytes(report), train.layout)
    return target


def write_gates(
    intake: PilotIntake, *, report_version: int = 1, version: int = 1
) -> Path:
    if intake.partition is not Partition.DEV:
        raise RecordError("partition", ("wrong_partition",))
    path = evaluation_path(intake, f"report-v{report_version}.json")
    require_committed(intake.config.repo, path, "report")
    report = read_json(path, PilotReport, "report")
    gates = derive_gates(
        report,
        rule=intake.preregistration.gates,
        judge_floor=intake.preregistration.floor.floor,
        preregistration_hash=intake.preregistration.content_hash,
        version=version,
    )
    target = evaluation_path(intake, f"gates-v{version}.toml")
    write_once(target, gates_toml(gates), intake.layout)
    return target


def coverage_gate(intake: PilotIntake) -> None:
    from earnings_pipeline.pilot_cli import _no_theme
    from earnings_pipeline.stage6 import EVENT_RUNS, transitions

    states = confined_path(intake.config.repo, EVENT_RUNS.as_posix() + "/states")
    _checked_history(intake.config, states)

    first_path = intake.pinned.coverage_file(1)
    second_path = intake.pinned.coverage_file(2)
    require_committed(intake.config.repo, first_path, "coverage")
    require_committed(intake.config.repo, second_path, "coverage")
    first = load_coverage(first_path)
    second = load_coverage(second_path)
    if first.run_ids != second.run_ids:
        raise RecordError("coverage", ("binding_mismatch",))
    rebuilt = build_coverage(
        intake.pinned.pilot,
        intake.pinned.coverage_pin,
        transitions(intake.layout),
        run_ids=first.run_ids,
        version=2,
        no_theme=_no_theme(intake.layout, intake.pinned, first.run_ids),
    )
    if rebuilt != second:
        raise RecordError("coverage", ("binding_mismatch",))
