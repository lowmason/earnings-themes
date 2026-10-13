"""Calibration over invented decision views, with hand-computed known answers (the
Stage 11 spec, A5 and §Calibration; R8.4, R8.6; D19-1, D19-5)."""

from datetime import date
from pathlib import Path

import pytest
from earnings_core import sha256_hex
from earnings_themes.evaluation.calibration import (
    ScorerCutoff,
    accepts,
    calibrate,
    frozen_configuration,
    joint_score,
)
from earnings_themes.evaluation.labels import (
    ClaimAnswer,
    FitAnswer,
    SupportLabel,
    SupportLabelSet,
)
from earnings_themes.evaluation.preregistration import freeze_preregistration
from earnings_themes.evaluation.problems import EvaluationError
from earnings_themes.extraction.records import Parameters
from earnings_themes.split import Partition
from earnings_themes.support.records import SupportPolicy

from .cases import decision_view
from .test_preregistration import fields

REPO = Path(__file__).resolve().parents[4]
YES, NO = ("supported", "fits"), ("unsupported", "fits")
PREREG = freeze_preregistration(fields())


def population():
    """60 targets in 12 events, 5 each. Assessed: 20 at 0.95 labelled 1, 10 at 0.6
    labelled 1, 10 at 0.6 labelled 0. Flagged (f1 opposes): 10 at 0.3 labelled 1,
    10 at 0.3 labelled 0."""
    rows = (
        [(0.95, YES, 1)] * 20
        + [(0.6, YES, 1)] * 10
        + [(0.6, YES, 0)] * 10
        + [(0.3, NO, 1)] * 10
        + [(0.3, NO, 0)] * 10
    )
    views, labels, events = {}, [], {}
    for n, (score, second, value) in enumerate(rows):
        target_id = f"t{n:02}"
        view = decision_view(target_id, score, YES, second)
        views[target_id] = view
        events[target_id] = f"e{n // 5:02}"
        labels.append(
            SupportLabel(
                target_id=target_id,
                target_input_hash=view.target.input_hash,
                partition=Partition.TRAIN,
                claim_support=ClaimAnswer.SUPPORTED
                if value
                else ClaimAnswer.UNSUPPORTED,
                theme_fit=FitAnswer.FITS,
                labelled_on=date(2026, 10, 20),
            )
        )
    label_set = SupportLabelSet(
        preregistration_hash=PREREG.content_hash, labels=tuple(labels)
    )
    alternative = {t: 1 - joint_score(v) for t, v in views.items()}
    return views, label_set, events, alternative


def run(preregistration=PREREG, labels=None):
    views, label_set, events, alternative = population()
    return calibrate(
        preregistration,
        labels or label_set,
        labels_hash="c" * 64,
        views=views,
        alternative=alternative,
        events=events,
        configuration={"invented": "configuration"},
    )


def test_assessed_and_flagged_views_are_genuine() -> None:
    views, *_ = population()
    assert views["t00"].outcome.status == "assessed"
    assert views["t45"].outcome.status == "flagged"
    assert views["t00"].eligible_quote_ids == ("q1",)
    assert accepts(ScorerCutoff(0.9), views["t00"])
    assert not accepts(ScorerCutoff(0.9), views["t25"])
    assert not accepts(ScorerCutoff(0.0), views["t45"])


def test_the_fit_and_selection_known_answer() -> None:
    artifact = run()
    fit = artifact.candidates[0]
    assert [(g.cutoff, g.precision, g.recall, g.accepted) for g in fit.grid] == [
        (0.0, 0.75, 0.75, 40),
        (0.5, 0.75, 0.75, 40),
        (0.9, 1.0, 0.5, 20),
    ]
    assert (fit.cutoff, fit.precision, fit.recall) == (0.9, 1.0, 0.5)
    assert artifact.outcome == "selected"
    assert artifact.selection.cutoff == 0.9
    assert (artifact.train_labels, artifact.usable_labels) == (60, 60)


def test_a_precision_tie_goes_to_the_lower_cutoff() -> None:
    data = fields()
    tighter = freeze_preregistration(
        {**data, "selection": {**data["selection"], "recall_floor": 0.6}}
    )
    _, label_set, _, _ = population()
    labels = label_set.model_copy(update={"preregistration_hash": tighter.content_hash})
    artifact = run(tighter, labels)
    assert artifact.selection.cutoff == 0.0


def test_no_cutoff_meeting_rho_is_no_candidate() -> None:
    data = fields()
    strict = freeze_preregistration(
        {**data, "selection": {**data["selection"], "recall_floor": 0.8}}
    )
    _, label_set, _, _ = population()
    labels = label_set.model_copy(update={"preregistration_hash": strict.content_hash})
    artifact = run(strict, labels)
    assert artifact.outcome == "no_candidate" and artifact.selection is None
    assert artifact.candidates[0].cutoff is None


def test_the_floor_test_is_reported_by_family() -> None:
    artifact = run()
    by_family = {f.family: f for f in artifact.families}
    assert by_family["f0"].kappa.point == pytest.approx(0.0)
    assert by_family["f1"].kappa.point == pytest.approx(0.25)
    assert by_family["f1"].uncertain == 0
    assert not by_family["f0"].meets_floor
    assert by_family["f1"].kappa.interval.resamples == PREREG.bootstrap.resamples


def test_auc_for_both_scorers_against_the_claim_label() -> None:
    by_scorer = {s.scorer: s.report for s in run().scorers}
    assert by_scorer["minicheck"].value == pytest.approx(0.75)
    assert by_scorer["deberta"].value == pytest.approx(0.25)
    assert by_scorer["minicheck"].task == "claim_support"


def test_the_artifact_is_deterministic_and_hashed() -> None:
    assert run() == run()
    assert run().content_hash != "0" * 64


def test_too_few_usable_labels_are_refused() -> None:
    _, label_set, _, _ = population()
    fewer = label_set.model_copy(update={"labels": label_set.labels[:49]})
    with pytest.raises(EvaluationError, match="too_few_labels"):
        run(labels=fewer)


def test_labels_must_bind_the_preregistration() -> None:
    _, label_set, _, _ = population()
    other = label_set.model_copy(update={"preregistration_hash": "d" * 64})
    with pytest.raises(EvaluationError, match="preregistration_mismatch"):
        run(labels=other)


def test_a_changed_target_input_is_refused() -> None:
    _, label_set, _, _ = population()
    first = label_set.labels[0].model_copy(update={"target_input_hash": "e" * 64})
    changed = label_set.model_copy(update={"labels": (first, *label_set.labels[1:])})
    with pytest.raises(EvaluationError, match="target_hash_mismatch"):
        run(labels=changed)


def test_an_edited_preregistration_is_refused() -> None:
    edited = PREREG.model_copy(update={"preregistration_version": 2})
    with pytest.raises(EvaluationError, match="preregistration_mismatch"):
        run(edited)


def keys(value) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {k for v in value.values() for k in keys(v)}
    if isinstance(value, list):
        return {k for v in value for k in keys(v)}
    return set()


def test_the_frozen_configuration_binds_no_run(assessed_case) -> None:
    prompt = (REPO / "prompts" / "support" / "judge-1.md").read_text(encoding="utf-8")
    policy = SupportPolicy(
        support_version="semantic-support/1",
        prompt_text=prompt,
        prompt_hash=sha256_hex(prompt.encode("utf-8")),
        parameters=Parameters(max_tokens=64),
    )
    case = assessed_case
    records = (
        case.sources.stored_run.record,
        case.proposals.record,
        case.support.record,
    )
    frozen = frozen_configuration(*records, policy)
    assert set(frozen) == {"extraction", "coding", "support"}
    assert not keys(frozen) & {
        "run_id",
        "source_run_id",
        "documents",
        "cache_mode",
        "stability_run_id",
        "requested_claim_order",
        "started_at",
    }
    other = policy.model_copy(update={"parameters": Parameters(max_tokens=65)})
    with pytest.raises(EvaluationError, match="malformed_record"):
        frozen_configuration(*records, other)
