"""Why Stage 11's evaluation refused something (the Stage 11 spec, §Failure
handling).

A refusal names its subject by ID and gives a closed reason, never text (GS13).
Checks over a set return ``Refusal`` rows (``earnings_themes.problems``); a
computation that cannot go on raises ``EvaluationError``.
"""

from collections.abc import Iterable
from enum import StrEnum


class EvaluationProblem(StrEnum):
    """Stage 11's evaluation reasons."""

    MALFORMED_RECORD = "malformed_record"
    PARENT_CYCLE = "parent_cycle"
    WRONG_PARTITION = "wrong_partition"
    UNKNOWN_EVENT = "unknown_event"
    UNKNOWN_TARGET = "unknown_target"
    DUPLICATE_TARGET = "duplicate_target"
    TARGET_HASH_MISMATCH = "target_hash_mismatch"
    NOT_SAMPLED = "not_sampled"
    NOT_LABELLED = "not_labelled"
    LABELS_CHANGED = "labels_changed"
    PREREGISTRATION_MISMATCH = "preregistration_mismatch"
    CONTENT_HASH_MISMATCH = "content_hash_mismatch"
    TOO_FEW_LABELS = "too_few_labels"
    NO_CANDIDATE = "no_candidate"
    UNKNOWN_METRIC = "unknown_metric"


class EvaluationError(ValueError):
    """One refusal: its reason, and its subject's ID when it has one."""

    def __init__(self, problem: EvaluationProblem, subject: str = "") -> None:
        super().__init__(f"{subject}: {problem.value}" if subject else problem.value)
        self.problem = problem
        self.subject = subject


def first_duplicate(ids: Iterable[str]) -> str | None:
    """The first ID that ``ids`` repeats, to name a refusal by; ``None`` when none
    repeats."""
    seen: set[str] = set()
    for item in ids:
        if item in seen:
            return item
        seen.add(item)
    return None
