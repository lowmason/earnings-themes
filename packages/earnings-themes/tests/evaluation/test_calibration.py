"""Calibration over invented decision views, with hand-computed known answers (the
Stage 11 spec, A5 and §Calibration; R8.4, R8.6; D19-1, D19-5)."""

from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from earnings_core import digest, sha256_hex
from earnings_themes.evaluation.align import unit_index
from earnings_themes.evaluation.calibration import (
    ScorerCutoff,
    accepts,
    calibrate,
    configuration_hash,
    frozen_configuration,
    joint_score,
)
from earnings_themes.evaluation.labels import (
    ClaimAnswer,
    FitAnswer,
    SupportLabel,
    SupportLabelSet,
    claim_label,
    joint_label,
)
from earnings_themes.evaluation.preregistration import freeze_preregistration
from earnings_themes.evaluation.problems import EvaluationError
from earnings_themes.evaluation.records import Metric
from earnings_themes.evaluation.report import (
    EventObservation,
    LabelledTarget,
    partition_report,
)
from earnings_themes.extraction.records import Parameters
from earnings_themes.split import Partition
from earnings_themes.support.records import SupportPolicy, support_configuration

from .cases import decision_view, example, gold
from .test_preregistration import fields
from .test_report import BOOK

REPO = Path(__file__).resolve().parents[4]
YES, NO = ("supported", "fits"), ("unsupported", "fits")
PREREG = freeze_preregistration(fields())


def build(rows):
    """Views, train labels, events and DeBERTa scores for ``rows``, 5 targets to an
    event. A row is ``(joint score, f1's answer, joint label)``: f0 always answers
    ``supported`` and ``fits``."""
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


def population():
    """60 targets in 12 events, 5 each. Assessed: 20 at 0.95 labelled 1, 10 at 0.6
    labelled 1, 10 at 0.6 labelled 0. Flagged (f1 opposes): 10 at 0.3 labelled 1,
    10 at 0.3 labelled 0."""
    return build(
        [(0.95, YES, 1)] * 20
        + [(0.6, YES, 1)] * 10
        + [(0.6, YES, 0)] * 10
        + [(0.3, NO, 1)] * 10
        + [(0.3, NO, 0)] * 10
    )


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
    with pytest.raises(EvaluationError, match="too_few_labels") as refused:
        run(labels=fewer)
    assert refused.value.subject == "labels"


def test_labels_must_bind_the_preregistration() -> None:
    _, label_set, _, _ = population()
    other = label_set.model_copy(update={"preregistration_hash": "d" * 64})
    with pytest.raises(EvaluationError, match="preregistration_mismatch") as refused:
        run(labels=other)
    assert refused.value.subject == "labels"


def test_a_changed_target_input_is_refused() -> None:
    _, label_set, _, _ = population()
    first = label_set.labels[0].model_copy(update={"target_input_hash": "e" * 64})
    changed = label_set.model_copy(update={"labels": (first, *label_set.labels[1:])})
    with pytest.raises(EvaluationError, match="target_hash_mismatch"):
        run(labels=changed)


def test_an_edited_preregistration_is_refused() -> None:
    edited = PREREG.model_copy(update={"preregistration_version": 2})
    with pytest.raises(EvaluationError, match="preregistration_mismatch") as refused:
        run(edited)
    assert refused.value.subject == "content_hash"


def rebound(preregistration, label_set):
    """``label_set``, bound to ``preregistration``."""
    return label_set.model_copy(
        update={"preregistration_hash": preregistration.content_hash}
    )


def menu_of(*candidates):
    """A preregistration whose menu is ``(candidate_id, signals, grid)`` scorer-cutoff
    candidates, in that order."""
    data = fields()
    menu = [
        {
            "candidate_id": candidate_id,
            "rule": "scorer_cutoff",
            "signal": "minicheck_joint",
            "signals": signals,
            "grid": list(grid),
        }
        for candidate_id, signals, grid in candidates
    ]
    return freeze_preregistration({**data, "menu": menu})


def test_exactly_the_preregistered_minimum_of_usable_labels_is_enough() -> None:
    """R8.4: the first 50 labels are t00 to t49, every one with a joint label (a
    supported or unsupported claim that fits), so 50 usable and 50 is not below 50.
    Over them 40 are positive (t00-t29 and t40-t49) and 10 negative (t30-t39).
    Cutoff 0.9 accepts t00-t19: precision 20/20 = 1.0, recall 20/40 = 0.5, which
    meets rho = 0.5; cutoffs 0.0 and 0.5 accept t00-t39: precision 30/40 = 0.75."""
    _, label_set, _, _ = population()
    fifty = label_set.model_copy(update={"labels": label_set.labels[:50]})
    artifact = run(labels=fifty)
    assert (artifact.train_labels, artifact.usable_labels) == (50, 50)
    assert artifact.outcome == "selected"
    assert artifact.selection.cutoff == 0.9
    assert [g.precision for g in artifact.candidates[0].grid] == [0.75, 0.75, 1.0]


def test_an_unsure_label_is_not_usable() -> None:
    """t00's claim answer is ``unsure`` (fit ``fits``), so it has no joint label.
    Among the first 50 labels that leaves 49 usable and the run is refused, though
    50 labels were supplied. Among the first 51 it leaves t01-t50: 51 labels, 50
    usable, and t00 is outside the population. Cutoff 0.0 then accepts the assessed
    t01-t39, which is 39 (40 assessed, less t00). Of those 29 are positive (t01-t29)
    and the population holds 39 positives (t01-t29 and t40-t49), so precision and
    recall are both 29/39."""
    _, label_set, _, _ = population()
    unsure = label_set.labels[0].model_copy(
        update={"claim_support": ClaimAnswer.UNSURE}
    )
    short = label_set.model_copy(update={"labels": (unsure, *label_set.labels[1:50])})
    with pytest.raises(EvaluationError, match="too_few_labels"):
        run(labels=short)
    enough = label_set.model_copy(update={"labels": (unsure, *label_set.labels[1:51])})
    artifact = run(labels=enough)
    assert (artifact.train_labels, artifact.usable_labels) == (51, 50)
    figure = artifact.candidates[0].grid[0]
    assert (figure.cutoff, figure.accepted) == (0.0, 39)
    assert figure.precision == pytest.approx(29 / 39)
    assert figure.recall == pytest.approx(29 / 39)


@pytest.mark.parametrize(
    ("menu", "fitted", "chosen"),
    [
        pytest.param(
            [("plenty", 3, [0.9]), ("frugal", 1, [0.0, 0.5])],
            {"plenty": 0.9, "frugal": 0.0},
            ("plenty", 0.9),
            id="higher-precision-beats-fewer-signals",
        ),
        pytest.param(
            [("pair", 2, [0.7]), ("solo", 1, [0.9])],
            {"pair": 0.7, "solo": 0.9},
            ("solo", 0.9),
            id="tied-precision-fewer-signals-beats-lower-cutoff",
        ),
        pytest.param(
            [("high", 1, [0.9]), ("low", 1, [0.7])],
            {"high": 0.9, "low": 0.7},
            ("low", 0.7),
            id="tied-signals-lower-cutoff",
        ),
        pytest.param(
            [("b-twin", 1, [0.9]), ("a-twin", 1, [0.9])],
            {"b-twin": 0.9, "a-twin": 0.9},
            ("a-twin", 0.9),
            id="all-tied-lower-candidate-id",
        ),
        pytest.param(
            [("never", 1, [1.0]), ("ok", 5, [0.9])],
            {"never": None, "ok": 0.9},
            ("ok", 0.9),
            id="a-candidate-without-a-cutoff-is-skipped",
        ),
    ],
)
def test_selection_orders_candidates_by_precision_signals_cutoff_and_id(
    menu, fitted, chosen
) -> None:
    """Over the 60 targets of ``population()``. Any cutoff above 0.6 up to 0.95
    accepts exactly the 20 targets scored 0.95, all positive: precision 20/20 = 1.0
    and recall 20/40 = 0.5, which meets rho = 0.5. Any cutoff up to 0.6 accepts the 40
    assessed targets, of which 30 are positive: precision 30/40 = 0.75 and recall
    30/40 = 0.75, a tie that goes to the lower cutoff within a candidate. Cutoff 1.0
    accepts nothing (0.95 < 1.0): no labelled accepted target, so no precision, and
    recall 0/40 does not meet rho. Across candidates the key is (-precision, signals,
    cutoff, candidate_id), each case below decided by one successive term."""
    preregistration = menu_of(*menu)
    _, label_set, _, _ = population()
    artifact = run(preregistration, rebound(preregistration, label_set))
    assert [f.candidate_id for f in artifact.candidates] == [m[0] for m in menu]
    assert {f.candidate_id: f.cutoff for f in artifact.candidates} == fitted
    assert (artifact.selection.candidate_id, artifact.selection.cutoff) == chosen


def test_agreement_known_answers_by_family() -> None:
    """Over ``population()``'s 60 (family verdict, joint label) pairs, with 40 labels
    of 1. f0 supports every target (verdict 1), so it agrees on the 40 positives:
    observed 40/60 = 2/3, shares 1 and 2/3. kappa chance = 1 * 2/3 + 0 = 2/3, so
    kappa = 0. AC1 mean = 5/6, chance = 2 * 5/6 * 1/6 = 5/18, so AC1 = (2/3 - 5/18) /
    (1 - 5/18) = (7/18) / (13/18) = 7/13. f1 supports t00-t39 and opposes t40-t59:
    pairs (1,1) x30, (1,0) x10, (0,1) x10, (0,0) x10, so observed = 40/60 = 2/3,
    both shares 2/3. kappa chance = 4/9 + 1/9 = 5/9, kappa = (2/3 - 5/9) / (4/9) =
    1/4. AC1 chance = 2 * 2/3 * 1/3 = 4/9, so AC1 = (2/3 - 4/9) / (5/9) = 2/5.
    Neither family meets the 0.4 floor: f0's kappa is 0 and f1's 0.25, and a 5%
    lower percentile of resamples centred near the point would have to sit 0.15
    above it (the exact case is the next test)."""
    by_family = {f.family: f for f in run().families}
    assert by_family["f0"].ac1.point == pytest.approx(7 / 13)
    assert by_family["f1"].ac1.point == pytest.approx(0.4)
    assert by_family["f1"].kappa.point == pytest.approx(0.25)
    assert not by_family["f0"].meets_floor
    assert not by_family["f1"].meets_floor
    assert all(f.labels == 60 for f in by_family.values())


def test_a_family_that_always_agrees_meets_the_floor_exactly() -> None:
    """Target n is labelled n % 2, so each event of 5 holds both labels (n = 0..4 is
    0, 1, 0, 1, 0), and f1 answers as the label does while f0 always supports. In
    any resample both labels occur and f1's verdict equals the label, so observed
    agreement is 1 and chance 1 - 2p(1 - p) is under 1: kappa = AC1 = x / x = 1 in
    every resample, and the interval is 1.0 to 1.0 with none undefined. f0's verdict
    is always 1, so observed agreement equals the label share p and so does chance:
    kappa = 0 in every resample. The floor is 0.4: f1 meets it, f0 does not."""
    views, label_set, events, alternative = build(
        [(0.9, YES if n % 2 else NO, n % 2) for n in range(60)]
    )
    artifact = calibrate(
        PREREG,
        label_set,
        labels_hash="c" * 64,
        views=views,
        alternative=alternative,
        events=events,
        configuration={},
    )
    by_family = {f.family: f for f in artifact.families}
    agreeing, constant = by_family["f1"], by_family["f0"]
    interval = agreeing.kappa.interval
    assert (agreeing.kappa.point, interval.lower, interval.upper) == (1.0, 1.0, 1.0)
    assert interval.undefined == 0 and agreeing.ac1.point == 1.0
    assert agreeing.meets_floor and agreeing.uncertain == 0
    assert (constant.kappa.point, constant.kappa.interval.lower) == (0.0, 0.0)
    assert not constant.meets_floor


UNSURE = ("uncertain", "fits")


def judged():
    """65 train targets in 13 events, 5 each. f0 always answers ``supported`` and
    ``fits``. f1: t00-t29 the same, labelled 1; t30-t39 the same, labelled 0;
    t40-t49 ``unsupported``, labelled 1; t50-t59 ``uncertain``, labelled 0. t60-t64
    (event e12) answer as t00 does, but their claim answer is ``unsure``, so they
    have no joint label and e12 holds none."""
    rows = (
        [(YES, ClaimAnswer.SUPPORTED)] * 30
        + [(YES, ClaimAnswer.UNSUPPORTED)] * 10
        + [(NO, ClaimAnswer.SUPPORTED)] * 10
        + [(UNSURE, ClaimAnswer.UNSUPPORTED)] * 10
        + [(YES, ClaimAnswer.UNSURE)] * 5
    )
    views, labels, events = {}, [], {}
    for n, (second, answer) in enumerate(rows):
        target_id = f"t{n:02}"
        views[target_id] = decision_view(target_id, 0.95, YES, second)
        events[target_id] = f"e{n // 5:02}"
        labels.append(
            SupportLabel(
                target_id=target_id,
                target_input_hash=views[target_id].target.input_hash,
                partition=Partition.TRAIN,
                claim_support=answer,
                theme_fit=FitAnswer.FITS,
                labelled_on=date(2026, 10, 20),
            )
        )
    label_set = SupportLabelSet(
        preregistration_hash=PREREG.content_hash, labels=tuple(labels)
    )
    return views, label_set, events


def test_an_uncertain_family_consensus_is_counted() -> None:
    """Over ``judged()``'s 60 joint labels. f1's pairs (verdict, label): (1, 1) x30,
    (1, 0) x10, (0, 1) x10 and (0, 0) x10, an ``uncertain`` consensus counting as
    0. Observed 40/60 = 2/3, both shares 2/3: κ chance = 4/9 + 1/9 = 5/9, κ = (2/3 -
    5/9) / (4/9) = 1/4; AC1 chance = 2 * 2/3 * 1/3 = 4/9, AC1 = (2/3 - 4/9) / (5/9) =
    2/5. Its uncertain count is t50-t59: 10. f0 supports all 60: κ = 0, AC1 = 7/13
    (as in ``test_agreement_known_answers_by_family``), none uncertain. t60-t64 have
    no joint label, so 60 of 65 train labels are usable."""
    views, label_set, events = judged()
    artifact = calibrate(
        PREREG,
        label_set,
        labels_hash="c" * 64,
        views=views,
        alternative={},
        events=events,
        configuration={},
    )
    assert (artifact.train_labels, artifact.usable_labels) == (65, 60)
    by_family = {f.family: f for f in artifact.families}
    assert by_family["f1"].kappa.point == pytest.approx(1 / 4)
    assert by_family["f1"].ac1.point == pytest.approx(2 / 5)
    assert (by_family["f1"].labels, by_family["f1"].uncertain) == (60, 10)
    assert by_family["f0"].kappa.point == pytest.approx(0.0)
    assert by_family["f0"].ac1.point == pytest.approx(7 / 13)
    assert (by_family["f0"].labels, by_family["f0"].uncertain) == (60, 0)


def test_the_report_and_the_artifact_agree_on_each_family() -> None:
    """The report's family figures over train's labels are the artifact's
    ``FamilyAgreement``: the same point, the same interval (both resample e00-e11,
    the events holding a joint label, never e12) and the same uncertain count, as
    ``test_an_uncertain_family_consensus_is_counted`` derives them."""
    views, label_set, events = judged()
    artifact = calibrate(
        PREREG,
        label_set,
        labels_hash="c" * 64,
        views=views,
        alternative={},
        events=events,
        configuration={},
    )
    source, base = example()
    observed = tuple(
        EventObservation(
            event_id=event_id,
            gold=gold(event_id, base, partition="train"),
            index=unit_index(source),
            accepted=(),
            release_confirmed=True,
            quotes=(1, 1),
            targets=(0, 1),
        )
        for event_id in sorted(set(events.values()))
    )
    labelled = tuple(
        LabelledTarget(
            label.target_id,
            events[label.target_id],
            claim_label(label),
            joint_label(label),
            False,
            {},
            views[label.target_id].trials,
        )
        for label in label_set.labels
    )
    report = partition_report(
        observed, labelled, BOOK, PREREG.bootstrap, partition=Partition.TRAIN
    )
    for family in artifact.families:
        for metric, expected in (
            (Metric.JUDGE_KAPPA, family.kappa),
            (Metric.JUDGE_AC1, family.ac1),
        ):
            figure = report.figure(metric, family.family)
            assert figure.point == expected.point
            assert figure.interval == expected.interval
            assert dict(figure.counts) == {
                "labels": family.labels,
                "uncertain": family.uncertain,
            }
    assert {f.family: f.uncertain for f in artifact.families} == {"f0": 0, "f1": 10}


def test_the_configuration_hash_helper_is_what_the_artifact_stores() -> None:
    """The composition is the digest of the configuration and the selection's JSON
    (or null), written out here independently of the helper."""
    configuration = {"invented": "configuration"}
    selected = run()
    assert selected.configuration_hash == digest(
        {
            "configuration": configuration,
            "selection": selected.selection.model_dump(mode="json"),
        }
    )
    assert configuration_hash(configuration, selected.selection) == (
        selected.configuration_hash
    )
    strict = freeze_preregistration(
        {**fields(), "selection": {**fields()["selection"], "recall_floor": 0.8}}
    )
    _, label_set, _, _ = population()
    none = run(strict, rebound(strict, label_set))
    assert none.selection is None
    assert configuration_hash(configuration, None) == none.configuration_hash
    assert none.configuration_hash == digest(
        {"configuration": configuration, "selection": None}
    )
    assert none.configuration_hash != selected.configuration_hash
    assert configuration_hash({"invented": "other"}, selected.selection) != (
        selected.configuration_hash
    )


def keys(value) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {k for v in value.values() for k in keys(v)}
    if isinstance(value, list):
        return {k for v in value for k in keys(v)}
    return set()


def invented_policy() -> SupportPolicy:
    """The support policy the invented assessed case ran under."""
    prompt = (REPO / "prompts" / "support" / "judge-1.md").read_text(encoding="utf-8")
    return SupportPolicy(
        support_version="semantic-support/1",
        prompt_text=prompt,
        prompt_hash=sha256_hex(prompt.encode("utf-8")),
        parameters=Parameters(max_tokens=64),
    )


def records_of(case):
    """The assessed case's extraction, proposals and support run records."""
    return (
        case.sources.stored_run.record,
        case.proposals.record,
        case.support.record,
    )


def rehashed(support, policy, **changes):
    """``support`` with ``changes``, its ``configuration_hash`` recomputed from its
    own bound parts as Stage 8 computes it."""
    record = support.model_copy(update=changes)
    return record.model_copy(
        update={
            "configuration_hash": digest(
                support_configuration(
                    policy,
                    record.ceilings,
                    record.scorer_identity,
                    record.judge_identities,
                    record.extractor_family,
                    record.cache_mode,
                )
            )
        }
    )


def test_runs_that_differ_only_in_identity_freeze_the_same_configuration(
    assessed_case,
) -> None:
    """D19-14: a dev run reproduces the calibrated configuration. The second record
    set changes every run-identity field the three records hold: run ID, start time,
    documents, source run, stability run, claim order and cache mode. Cache mode is
    part of Stage 8's own configuration hash, so the second support record is
    re-hashed, and the two records then really differ in it."""
    policy = invented_policy()
    extraction, proposals, support = records_of(assessed_case)
    later = datetime(2026, 10, 30, tzinfo=UTC)
    identity = {
        "started_at": later,
        "documents": (("other-doc", "a" * 64),),
        "stability_run_id": "other-stability",
        "cache_mode": "replay",
    }
    other = (
        extraction.model_copy(
            update={
                "run_id": "other-extraction",
                "started_at": later,
                "documents": {"other-doc": "a" * 64},
            }
        ),
        proposals.model_copy(
            update={
                **identity,
                "run_id": "other-proposals",
                "source_run_id": "other-extraction",
                "source_run_hash": "b" * 64,
                "requested_claim_order": (("other-doc", "other-claim"),),
            }
        ),
        rehashed(
            support,
            policy,
            **identity,
            run_id="other-support",
            source_run_id="other-extraction",
            source_run_hash="b" * 64,
        ),
    )
    assert other[2].cache_mode != support.cache_mode
    assert other[2].configuration_hash != support.configuration_hash
    assert digest(frozen_configuration(*other, policy)) == digest(
        frozen_configuration(extraction, proposals, support, policy)
    )


@pytest.mark.parametrize(
    "change",
    [
        "support policy",
        "support ceiling",
        "extractor family",
        "extraction configuration",
        "coding ceiling",
    ],
)
def test_a_bound_component_changes_the_frozen_configuration(
    assessed_case, change
) -> None:
    """D19-14: what a calibrated policy is frozen with (the support policy and
    ceilings, the extractor family, the extraction configuration and the coding
    ceilings) is bound: changing any one changes the hash. A changed support
    component is re-hashed with the record, so only the frozen digest differs."""
    policy = invented_policy()
    extraction, proposals, support = records_of(assessed_case)
    baseline = digest(frozen_configuration(extraction, proposals, support, policy))
    match change:
        case "support policy":
            policy = policy.model_copy(update={"parameters": Parameters(max_tokens=65)})
            support = rehashed(support, policy)
        case "support ceiling":
            ceilings = support.ceilings
            support = rehashed(
                support,
                policy,
                ceilings=ceilings.model_copy(
                    update={"tokens_per_run": ceilings.tokens_per_run + 1}
                ),
            )
        case "extractor family":
            support = rehashed(support, policy, extractor_family="other-family")
        case "extraction configuration":
            configuration = extraction.configuration
            extraction = extraction.model_copy(
                update={
                    "configuration": configuration.model_copy(
                        update={"extractor_version": "other-extractor"}
                    )
                }
            )
        case "coding ceiling":
            ceilings = proposals.ceilings
            proposals = proposals.model_copy(
                update={
                    "ceilings": ceilings.model_copy(
                        update={"requests_per_run": ceilings.requests_per_run + 1}
                    )
                }
            )
    changed = frozen_configuration(extraction, proposals, support, policy)
    assert digest(changed) != baseline


def test_the_frozen_configuration_binds_no_run(assessed_case) -> None:
    policy = invented_policy()
    records = records_of(assessed_case)
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
