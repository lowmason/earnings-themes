"""A family's consensus and each trial's verdict (the Stage 11 spec, §Calibration;
FP21)."""

import pytest
from earnings_themes.evaluation.verdicts import (
    consensus,
    families,
    family_verdict,
    trial_verdict,
)

from .cases import panel, trial

YES = ("supported", "fits")


@pytest.mark.parametrize(
    ("first", "consensus_value"),
    [
        (YES, "supports"),
        (("unsupported", "fits"), "opposes"),
        (("supported", "does_not_fit"), "opposes"),
        (("uncertain", "fits"), "uncertain"),
        (("supported", "uncertain"), "uncertain"),
    ],
)
def test_a_familys_consensus(first, consensus_value) -> None:
    trials = panel("t1", first, YES)
    assert consensus(trials, "f0") == consensus_value
    assert family_verdict(trials, "f0") == (1 if consensus_value == "supports" else 0)
    assert families(trials) == ("f0", "f1")


def test_split_presentations_are_uncertain() -> None:
    mixed = (
        trial("t1", "f0", "evidence_first", *YES),
        trial("t1", "f0", "claim_theme_first", "unsupported", "fits"),
    )
    assert consensus(mixed, "f0") == "uncertain"
    assert consensus(mixed[:1], "f0") == "uncertain"
    assert consensus((), "f0") == "uncertain"


def test_a_trials_verdict_and_uncertainty() -> None:
    assert trial_verdict(trial("t1", "f0", "evidence_first", *YES)) == (1, False)
    unsure = trial("t1", "f0", "evidence_first", "uncertain", "fits")
    assert trial_verdict(unsure) == (0, True)
    against = trial("t1", "f0", "evidence_first", "supported", "does_not_fit")
    assert trial_verdict(against) == (0, False)
