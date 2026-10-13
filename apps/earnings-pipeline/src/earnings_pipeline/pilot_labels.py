"""Deterministic support labels: local views, user answers, checked append-only merge."""

import subprocess
from datetime import date
from pathlib import Path

from earnings_themes.evaluation import (
    SupportLabel,
    SupportLabelSet,
    check_labels,
    label_pool,
    label_views,
    labels_toml,
    load_labels,
    merge_labels,
    sample_targets,
)
from earnings_themes.evaluation.labels import ClaimAnswer, FitAnswer
from earnings_themes.records import RecordError
from earnings_themes.split import Partition
from earnings_themes.support import reverify_support_run

from earnings_pipeline.pilot_inputs import PilotIntake, require_committed
from earnings_pipeline.pilot_workflow import LoadedPass
from earnings_pipeline.stage6 import replace
from earnings_pipeline.theme_config import WorkflowError, confined_path

TEMPLATE = (
    "# Working labels: read every view, edit both answers, and deliberately confirm labelled_on.\n"
    "# unsure is a real answer, not a blank. Finish the whole sample before labels check.\n"
    "# Existing committed labels cannot be edited; a train extension adds new targets.\n"
)


def checked_pass(
    intake: PilotIntake, loaded: LoadedPass, *, fresh: bool = False
) -> None:
    if (
        loaded.record.partition is not intake.partition
        or loaded.record.event_ids != intake.config.selected_event_ids
        or loaded.alternative.record.scorer_identity
        != intake.settings.alternative_scorer
        or (not fresh and loaded.record.mode != "live")
    ):
        raise WorkflowError("input_changed")


def local_path(intake: PilotIntake, path: Path) -> Path:
    return confined_path(
        intake.config.repo,
        path.relative_to(intake.config.repo).as_posix(),
        "data/runs/pilot",
    )


def sample(intake: PilotIntake, loaded: LoadedPass, extensions: int) -> tuple[str, ...]:
    checked_pass(intake, loaded)
    if type(extensions) is not int or extensions < 0:
        raise RecordError("train_extensions", ("malformed_record",))
    outcomes = reverify_support_run(loaded.primary, loaded.sources)
    events = {source.doc_id: source.event_id for source in intake.config.sources}
    pool = label_pool(loaded.primary.targets, outcomes, events)
    plan = intake.preregistration.sampling
    train = intake.partition is Partition.TRAIN
    size = (
        plan.train_size + extensions * plan.extension_step if train else plan.dev_size
    )
    cap = plan.train_cap if train else plan.dev_cap
    return sample_targets(pool, seed=plan.seed, size=size, cap=cap)


def working_path(intake: PilotIntake) -> Path:
    return local_path(
        intake, intake.local / "labels" / f"{intake.partition.value}-working.toml"
    )


def committed_labels(intake: PilotIntake) -> SupportLabelSet | None:
    path = confined_path(
        intake.config.repo,
        (intake.pinned.evaluation / "labels" / "support-labels-v1.toml")
        .relative_to(intake.config.repo)
        .as_posix(),
    )
    if not path.is_file():
        # Only a genuinely absent HEAD entry permits first promotion. A deleted
        # committed base must still pass the authoritative byte comparison.
        try:
            result = subprocess.run(
                [
                    "git",
                    "ls-tree",
                    "-z",
                    "HEAD",
                    "--",
                    path.relative_to(intake.config.repo).as_posix(),
                ],
                cwd=intake.config.repo,
                capture_output=True,
                check=False,
            )
        except OSError:
            raise RecordError("labels", ("not_committed",)) from None
        if result.returncode != 0:
            raise RecordError("labels", ("not_committed",))
        if not result.stdout:
            return None
    require_committed(intake.config.repo, path, "labels")
    record = load_labels(path)
    if record.preregistration_hash != intake.preregistration.content_hash:
        raise RecordError("labels", ("preregistration_mismatch",))
    return record


def _checked(
    record: SupportLabelSet,
    intake: PilotIntake,
    loaded: LoadedPass,
    drawn: tuple[str, ...],
) -> None:
    found = check_labels(
        record,
        partition=intake.partition,
        sample=drawn,
        input_hashes={t.target_id: t.input_hash for t in loaded.primary.targets},
        preregistration_hash=intake.preregistration.content_hash,
    )
    if found:
        raise RecordError(
            "labels", tuple(f"labels.target_id: {r.reason}" for r in found)
        )


def write_view(
    intake: PilotIntake, loaded: LoadedPass, extensions: int, labelled_on: date
) -> tuple[Path, Path]:
    drawn = sample(intake, loaded, extensions)
    working = working_path(intake)
    old = load_labels(working) if working.is_file() else committed_labels(intake)
    kept = {} if old is None else {l.target_id: l for l in old.of(intake.partition)}
    if old is not None:
        own = SupportLabelSet(
            preregistration_hash=old.preregistration_hash,
            train_extensions=old.train_extensions,
            labels=tuple(kept.values()),
        )
        _checked(own, intake, loaded, tuple(kept))
        if not set(kept) <= set(drawn):
            raise RecordError("labels", ("not_sampled",))
    hashes = {t.target_id: t.input_hash for t in loaded.primary.targets}
    labels = tuple(
        kept.get(target)
        or SupportLabel(
            target_id=target,
            target_input_hash=hashes[target],
            partition=intake.partition,
            claim_support=ClaimAnswer.UNSURE,
            theme_fit=FitAnswer.UNSURE,
            labelled_on=labelled_on,
        )
        for target in drawn
    )
    committed = committed_labels(intake)
    train_extensions = (
        extensions
        if intake.partition is Partition.TRAIN
        else (committed.train_extensions if committed else 0)
    )
    record = SupportLabelSet(
        preregistration_hash=intake.preregistration.content_hash,
        train_extensions=train_extensions,
        labels=labels,
    )
    view = local_path(
        intake, intake.local / "labels/views" / f"{intake.partition.value}.md"
    )
    # sample() reverifies before the library renderer is called (H1).
    replace(view, label_views(loaded.primary, loaded.sources, drawn))
    replace(working, TEMPLATE + labels_toml(record))
    return view, working


def check_working(intake: PilotIntake, loaded: LoadedPass, extensions: int) -> Path:
    working = load_labels(working_path(intake))
    drawn = sample(intake, loaded, extensions)
    _checked(working, intake, loaded, drawn)
    committed = committed_labels(intake)
    expected = (
        extensions
        if intake.partition is Partition.TRAIN
        else (committed.train_extensions if committed else 0)
    )
    if working.train_extensions != expected:
        raise RecordError("train_extensions", ("labels_changed",))
    if (
        committed is not None
        and extensions > committed.train_extensions
        and intake.partition is Partition.TRAIN
        and len(working.of(Partition.TRAIN)) <= len(committed.of(Partition.TRAIN))
    ):
        raise RecordError("train_extensions", ("labels_changed",))
    merged = merge_labels(committed, working, intake.partition)
    target = confined_path(
        intake.config.repo,
        (intake.pinned.evaluation / "labels/support-labels-v1.toml")
        .relative_to(intake.config.repo)
        .as_posix(),
    )
    # This named file is append-only through merge_labels, unlike immutable versioned artifacts.
    replace(target, labels_toml(merged))
    return target
