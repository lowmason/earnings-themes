"""A judge family's consensus and each trial's verdict on a target (the Stage 11
spec, §Calibration and §Metrics; FP21).

- **Consensus.** A family supports a target when both of its presentations answer
  ``supported`` and ``fits``; it opposes when both answer ``unsupported`` or
  ``does_not_fit``; otherwise it is uncertain, as it is when a presentation is
  missing or unanswered.
- **Verdicts.** A family's binary verdict is 1 exactly when it supports, so an
  uncertain consensus counts as not supporting (§Preregistration). A single trial's
  verdict is 1 when it answers ``supported`` and ``fits``, and it is uncertain when
  either answer is ``uncertain``.
"""

from collections.abc import Iterable
from typing import Literal

from earnings_themes.support.records import JudgeTrial, Presentation

type Consensus = Literal["supports", "opposes", "uncertain"]


def families(trials: Iterable[JudgeTrial]) -> tuple[str, ...]:
    """The judge families in ``trials``, sorted."""
    return tuple(sorted({trial.identity.family for trial in trials}))


def consensus(trials: Iterable[JudgeTrial], family: str) -> Consensus:
    """``family``'s consensus over its two presentations."""
    own = [trial for trial in trials if trial.identity.family == family]
    answers = [trial.answer for trial in own]
    if {trial.presentation for trial in own} != set(Presentation) or len(own) != 2:
        return "uncertain"
    if any(answer is None for answer in answers):
        return "uncertain"
    if all(a.claim_support == "supported" and a.theme_fit == "fits" for a in answers):
        return "supports"
    if all(
        a.claim_support == "unsupported" or a.theme_fit == "does_not_fit"
        for a in answers
    ):
        return "opposes"
    return "uncertain"


def family_judgement(
    trials: Iterable[JudgeTrial], family: str
) -> tuple[Literal[0, 1], bool]:
    """``family``'s binary verdict, and whether its consensus is uncertain: what
    ``trial_verdict`` gives for one trial."""
    said = consensus(trials, family)
    return (1 if said == "supports" else 0), said == "uncertain"


def family_verdict(trials: Iterable[JudgeTrial], family: str) -> Literal[0, 1]:
    """1 when ``family`` supports, else 0."""
    return family_judgement(trials, family)[0]


def trial_verdict(trial: JudgeTrial) -> tuple[Literal[0, 1], bool]:
    """One trial's binary verdict, and whether either of its answers is uncertain."""
    answer = trial.answer
    if answer is None:
        return 0, True
    supports = answer.claim_support == "supported" and answer.theme_fit == "fits"
    unsure = "uncertain" in (answer.claim_support, answer.theme_fit)
    return (1 if supports else 0), unsure
