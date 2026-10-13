"""The train calibration boundary: sample, source and exact-label-byte bindings."""

import re
import subprocess
from pathlib import Path

from earnings_core import sha256_hex
from earnings_themes import tomlfile
from earnings_themes.coding import validate_proposal_support
from earnings_themes.coding.decide import decision_inputs
from earnings_themes.evaluation import (
    CalibrationArtifact,
    SupportLabelSet,
    calibrate,
    frozen_configuration,
    joint_score,
)
from earnings_themes.records import RecordError, parse
from earnings_themes.split import Partition

from earnings_pipeline.pilot_inputs import PilotIntake, require_committed
from earnings_pipeline.pilot_labels import _checked, checked_pass, sample
from earnings_pipeline.pilot_records import json_bytes, read_calibration
from earnings_pipeline.pilot_workflow import LoadedPass
from earnings_pipeline.stage6 import write_once
from earnings_pipeline.theme_config import confined_path


def read_label_bytes(path: Path) -> tuple[SupportLabelSet, bytes]:
    try:
        data = path.read_bytes()
    except OSError:
        raise RecordError("labels", ("malformed_record",)) from None
    return parse(tomlfile.loads(data, "labels"), SupportLabelSet, "labels"), data


def calibrate_pilot(intake: PilotIntake, loaded: LoadedPass) -> Path:
    if intake.partition is not Partition.TRAIN:
        raise RecordError("partition", ("wrong_partition",))
    checked_pass(intake, loaded)
    path = intake.pinned.evaluation / "labels/support-labels-v1.toml"
    require_committed(intake.config.repo, path, "labels")
    labels, data = read_label_bytes(path)
    own = SupportLabelSet(
        preregistration_hash=labels.preregistration_hash,
        train_extensions=labels.train_extensions,
        labels=labels.of(Partition.TRAIN),
    )
    _checked(own, intake, loaded, sample(intake, loaded, labels.train_extensions))
    validate_proposal_support(loaded.proposal, loaded.primary, loaded.sources)
    validate_proposal_support(loaded.proposal, loaded.alternative, loaded.sources)
    views = decision_inputs(loaded.primary, loaded.sources)
    alternative = decision_inputs(loaded.alternative, loaded.sources)
    events = {s.doc_id: s.event_id for s in intake.config.sources}
    artifact = calibrate(
        intake.preregistration,
        labels,
        labels_hash=sha256_hex(data),
        views=views,
        alternative={target: joint_score(view) for target, view in alternative.items()},
        events={t.target_id: events[t.target.doc_id] for t in loaded.primary.targets},
        configuration=frozen_configuration(
            loaded.sources.stored_run.record,
            loaded.proposal.record,
            loaded.primary.record,
            intake.config.support_policy,
        ),
    )
    target = evaluation_path(intake, "calibration-v1.json")
    write_once(target, json_bytes(artifact), intake.layout)
    return target


def checked_calibration(intake: PilotIntake) -> CalibrationArtifact:
    path = evaluation_path(intake, "calibration-v1.json")
    require_committed(intake.config.repo, path, "calibration")
    artifact = read_calibration(path)
    if artifact.preregistration_hash != intake.preregistration.content_hash:
        raise RecordError("calibration", ("preregistration_mismatch",))
    validate_calibration_labels(intake, artifact)
    return artifact


def validate_calibration_labels(
    intake: PilotIntake, artifact: CalibrationArtifact
) -> None:
    path = intake.pinned.evaluation / "labels/support-labels-v1.toml"
    require_committed(intake.config.repo, path, "labels")
    current, data = read_label_bytes(path)
    if current.preregistration_hash != artifact.preregistration_hash:
        raise RecordError("labels", ("preregistration_mismatch",))
    relative = path.relative_to(intake.config.repo).as_posix()
    original = data if sha256_hex(data) == artifact.labels_hash else None
    if original is None:
        try:
            history = subprocess.run(
                ["git", "rev-list", "HEAD", "--", relative],
                cwd=intake.config.repo,
                capture_output=True,
                check=False,
            )
            if history.returncode == 0:
                for revision in history.stdout.decode(
                    "ascii", errors="ignore"
                ).splitlines():
                    if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
                        raise RecordError("labels", ("labels_changed",))
                    result = subprocess.run(
                        ["git", "show", revision + ":" + relative],
                        cwd=intake.config.repo,
                        capture_output=True,
                        check=False,
                    )
                    if (
                        result.returncode == 0
                        and sha256_hex(result.stdout) == artifact.labels_hash
                    ):
                        original = result.stdout
                        break
        except OSError:
            raise RecordError("labels", ("labels_changed",)) from None
    if original is None:
        raise RecordError("labels", ("labels_changed",))
    old = parse(tomlfile.loads(original, "labels"), SupportLabelSet, "labels")
    if (
        old.preregistration_hash != current.preregistration_hash
        or old.train_extensions != current.train_extensions
        or old.of(Partition.TRAIN) != current.of(Partition.TRAIN)
    ):
        raise RecordError("labels", ("labels_changed",))


def evaluation_path(intake: PilotIntake, name: str) -> Path:
    root = intake.pinned.evaluation.relative_to(intake.config.repo).as_posix()
    return confined_path(intake.config.repo, root + "/" + name, root)
