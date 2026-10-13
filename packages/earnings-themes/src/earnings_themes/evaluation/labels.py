"""The user's support labels (the Stage 11 spec, A4 and §Labels; FP8, FP17, FP21;
R8.4).

- **Two answers per target** (FP21): does the cited evidence support the claim,
  and does the claim fit the theme? Either may be ``unsure``.
- **Derived labels.** The claim label is the first answer, ``unsure`` left out. The
  joint label is 1 when both answers are positive, 0 when either is negative, and
  left out otherwise. A label left out is counted, never a negative.
- **Committed as IDs, hashes and answers** (FP17): no free-text field exists, so the
  file cannot hold a release's words (GS3).
- **The working file.** The user writes one partition's labels into a local file of
  the same shape; ``check_labels`` checks it against the sample and the support run,
  and ``merge_labels`` adds it to the committed file.
"""

from collections.abc import Mapping, Sequence
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Literal, Self

from pydantic import NonNegativeInt, model_validator

from earnings_themes import tomlfile
from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
from earnings_themes.problems import Refusal
from earnings_themes.records import NonBlank, Part, Sha256Hex, ThemesRecord, parse
from earnings_themes.split import Partition
from earnings_themes.support.metrics import HumanLabel, LabelTask

LABELLED = (Partition.TRAIN, Partition.DEV)
HEADER = (
    "Stage 11 support labels (FP8, FP17, FP21): target IDs, input hashes and the"
    " user's answers, never text. Written by `earnings-pipeline pilot labels check`."
)


class ClaimAnswer(StrEnum):
    """Does the cited evidence support the claim, with its attribution, time,
    scope and polarity?"""

    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNSURE = "unsure"


class FitAnswer(StrEnum):
    """Does the claim fit the theme's definition and its rules?"""

    FITS = "fits"
    DOES_NOT_FIT = "does_not_fit"
    UNSURE = "unsure"


class SupportLabel(Part):
    """One target's two answers, bound to the input the support run assessed."""

    target_id: NonBlank
    target_input_hash: Sha256Hex
    partition: Partition
    claim_support: ClaimAnswer
    theme_fit: FitAnswer
    labelled_on: date

    @model_validator(mode="after")
    def _train_or_dev(self) -> Self:
        if self.partition not in LABELLED:
            raise ValueError("only train and dev targets are labelled")
        return self


class SupportLabelSet(ThemesRecord):
    """``labels/support-labels-v1.toml``, or a working file of one partition."""

    preregistration_hash: Sha256Hex
    train_extensions: NonNegativeInt = 0
    labels: tuple[SupportLabel, ...] = ()

    @model_validator(mode="after")
    def _one_label_per_target(self) -> Self:
        ids = [label.target_id for label in self.labels]
        if len(ids) != len(set(ids)):
            raise ValueError("one label per target")
        return self

    def of(self, partition: Partition) -> tuple[SupportLabel, ...]:
        return tuple(label for label in self.labels if label.partition is partition)


def claim_label(label: SupportLabel) -> Literal[0, 1] | None:
    """The claim-support label; ``unsure`` is left out."""
    return {ClaimAnswer.SUPPORTED: 1, ClaimAnswer.UNSUPPORTED: 0}.get(
        label.claim_support
    )


def joint_label(label: SupportLabel) -> Literal[0, 1] | None:
    """1 when both answers are positive, 0 when either is negative, else left out."""
    claim, fit = label.claim_support, label.theme_fit
    if claim is ClaimAnswer.UNSUPPORTED or fit is FitAnswer.DOES_NOT_FIT:
        return 0
    if claim is ClaimAnswer.SUPPORTED and fit is FitAnswer.FITS:
        return 1
    return None


def human_labels(
    labels: Sequence[SupportLabel], task: LabelTask
) -> tuple[HumanLabel, ...]:
    """``labels`` as Stage 8's ``HumanLabel`` for ``task``, those left out omitted."""
    derive = claim_label if task == "claim_support" else joint_label
    return tuple(
        HumanLabel(target_id=label.target_id, task=task, supported=value)
        for label in labels
        if (value := derive(label)) is not None
    )


def usable(labels: Sequence[SupportLabel]) -> int:
    """How many labels have a joint label (R8.4: calibration needs 50 from train)."""
    return sum(joint_label(label) is not None for label in labels)


def _order(label: SupportLabel) -> tuple[int, str]:
    return LABELLED.index(label.partition), label.target_id


def labels_toml(labels: SupportLabelSet) -> str:
    """The committed file: train then dev, each by target ID."""
    ordered = labels.model_copy(
        update={"labels": tuple(sorted(labels.labels, key=_order))}
    )
    return tomlfile.dumps(ordered.model_dump(mode="python"), header=HEADER)


def load_labels(path: Path) -> SupportLabelSet:
    return parse(tomlfile.read(path), SupportLabelSet, path.name)


def check_labels(
    working: SupportLabelSet,
    *,
    partition: Partition,
    sample: Sequence[str],
    input_hashes: Mapping[str, str],
    preregistration_hash: str,
) -> list[Refusal]:
    """Why ``working`` is not ``partition``'s labels for ``sample``: each refusal
    names a target ID and a reason, never an answer (§Labels)."""
    refusals = []
    if working.preregistration_hash != preregistration_hash:
        refusals.append(Refusal("labels", EvaluationProblem.PREREGISTRATION_MISMATCH))
    sampled = set(sample)
    for label in working.labels:
        subject = label.target_id
        if label.partition is not partition:
            refusals.append(Refusal(subject, EvaluationProblem.WRONG_PARTITION))
        elif subject not in sampled:
            refusals.append(Refusal(subject, EvaluationProblem.NOT_SAMPLED))
        elif subject not in input_hashes:
            refusals.append(Refusal(subject, EvaluationProblem.UNKNOWN_TARGET))
        elif input_hashes[subject] != label.target_input_hash:
            refusals.append(Refusal(subject, EvaluationProblem.TARGET_HASH_MISMATCH))
    labelled = {label.target_id for label in working.labels}
    refusals += [
        Refusal(target_id, EvaluationProblem.NOT_LABELLED)
        for target_id in sample
        if target_id not in labelled
    ]
    return sorted(refusals)


def merge_labels(
    committed: SupportLabelSet | None,
    working: SupportLabelSet,
    partition: Partition,
) -> SupportLabelSet:
    """``committed`` with ``working``'s ``partition`` labels added. A partition
    already committed changes only when train is extended (§Failure handling): its
    committed labels kept as they are, and more extensions. A refusal names the
    committed labels the working file drops or changes, by ID, or, when it only adds
    labels, the added ones."""
    new = working.of(partition)
    if committed is None:
        return working.model_copy(update={"labels": new})
    if committed.preregistration_hash != working.preregistration_hash:
        raise EvaluationError(EvaluationProblem.PREREGISTRATION_MISMATCH, "labels")
    old = committed.of(partition)
    extensions = committed.train_extensions
    if old and set(old) != set(new):
        extended = (
            partition is Partition.TRAIN
            and set(old) <= set(new)
            and working.train_extensions > committed.train_extensions
        )
        if not extended:
            dropped = {label.target_id for label in set(old) - set(new)}
            added = {label.target_id for label in set(new) - set(old)}
            raise EvaluationError(
                EvaluationProblem.LABELS_CHANGED, ", ".join(sorted(dropped or added))
            )
    if partition is Partition.TRAIN:
        extensions = max(extensions, working.train_extensions)
    kept = tuple(
        label for label in committed.labels if label.partition is not partition
    )
    return committed.model_copy(
        update={"labels": (*kept, *new), "train_extensions": extensions}
    )
