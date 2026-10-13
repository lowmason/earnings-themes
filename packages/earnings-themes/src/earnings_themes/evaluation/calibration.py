"""Calibration (the Stage 11 spec, A5 and §Calibration; FP9, FP10, FP21; R8.4,
R8.6).

- **The labels** are train's, and at least the preregistered number must have a
  joint label (R8.4).
- **The floor test.** Each judge family's binary verdict against the joint label:
  Cohen's κ with its event-clustered bootstrap lower bound against the preregistered
  floor, and Gwet's AC1 beside it. It is reported and changes no decision (D19-1).
- **Fitting.** Each candidate's cutoff is the grid value with the highest train
  labelled precision whose label recall is at least ρ; a tie goes to the lower
  cutoff. A target counts as accepted exactly when Stage 9's ``decision_vote``
  accepts it under that cutoff, so a flagged, incomplete or refused target never
  is, and calibration decides as ``decide_assignments`` will (D19-5).
- **Selection.** The fitted candidate with the highest precision; a tie goes to the
  one reading fewer signals, then the lower cutoff. When none meets ρ, the outcome is
  ``no_candidate``: a feasibility finding, not an error.
- **AUC** for MiniCheck and DeBERTa against the claim label (R8.6, FP21).
- **The frozen configuration** binds the models, prompts, policies and ceilings,
  never a run's IDs, documents, claim order, cache mode or stability run, so a dev
  run reproduces it.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, Self

from earnings_core import digest
from pydantic import NonNegativeInt, PositiveInt, model_validator

from earnings_themes.coding.decide import DecisionInput, decision_vote
from earnings_themes.coding.records import PolicyVote, ProposalRunRecord
from earnings_themes.evaluation.agreement import judge_agreement
from earnings_themes.evaluation.bootstrap import Estimate
from earnings_themes.evaluation.labels import (
    SupportLabelSet,
    claim_label,
    human_labels,
    joint_label,
)
from earnings_themes.evaluation.preregistration import Preregistration
from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
from earnings_themes.evaluation.records import Real, sealed
from earnings_themes.evaluation.verdicts import families, family_judgement
from earnings_themes.extraction.records import RunRecord
from earnings_themes.records import (
    IdPart,
    NonBlank,
    Part,
    Sha256Hex,
    ThemesRecord,
    hash_matches,
)
from earnings_themes.split import Partition
from earnings_themes.support.metrics import (
    Acceptance,
    ContinuousSignal,
    MetricReport,
    accepted_claim_precision,
    accepted_claim_recall,
    auc_roc,
)
from earnings_themes.support.records import (
    SignalStatus,
    SupportPolicy,
    SupportRunRecord,
    support_configuration,
)


def joint_score(view: DecisionInput) -> float | None:
    """The target's available joint entailment score, or ``None``."""
    return next(
        (
            signal.score
            for signal in view.entailment
            if signal.scope == "joint" and signal.status is SignalStatus.AVAILABLE
        ),
        None,
    )


@dataclass(frozen=True)
class ScorerCutoff:
    """The scorer-cutoff rule (D19-1): accept with the eligible quotes when the
    joint score is at least ``cutoff``; otherwise review."""

    cutoff: float

    def vote(self, view: DecisionInput) -> PolicyVote:
        score = joint_score(view)
        if score is not None and score >= self.cutoff and view.eligible_quote_ids:
            return PolicyVote(
                action="accept", supporting_quote_ids=view.eligible_quote_ids
            )
        return PolicyVote(action="review")


@dataclass(frozen=True)
class _Trial:
    """A rule in the shape ``decision_vote`` calls; it reads no reference."""

    rule: ScorerCutoff

    def evaluate(self, view: DecisionInput) -> PolicyVote:
        return self.rule.vote(view)


def accepts(rule: ScorerCutoff, view: DecisionInput) -> bool:
    """Whether Stage 9 accepts ``view`` under ``rule``."""
    return decision_vote(view, _Trial(rule))[0] == "accepted"


class CutoffFigure(Part):
    """One grid cutoff's train figures."""

    cutoff: Real
    precision: Real | None
    recall: Real | None
    accepted: NonNegativeInt


class CandidateFit(Part):
    """One candidate's fitted cutoff, or ``None`` when no cutoff meets ρ."""

    candidate_id: IdPart
    signals: Literal[1]
    cutoff: Real | None
    precision: Real | None
    recall: Real | None
    grid: tuple[CutoffFigure, ...]


class FamilyAgreement(Part):
    """One judge family against the joint label (R8.4): reported, never gating a
    decision (D19-1)."""

    family: NonBlank
    kappa: Estimate
    ac1: Estimate
    labels: NonNegativeInt
    uncertain: NonNegativeInt
    meets_floor: bool


class ScorerAuc(Part):
    """One scorer's AUC-ROC against the claim label (R8.6)."""

    scorer: Literal["minicheck", "deberta"]
    report: MetricReport


class Selection(Part):
    """The selected candidate and its cutoff."""

    candidate_id: IdPart
    rule: Literal["scorer_cutoff"]
    signal: Literal["minicheck_joint"]
    cutoff: Real


class CalibrationArtifact(ThemesRecord):
    """``calibration-v<N>.json``: no text (§Calibration)."""

    calibration_version: PositiveInt
    preregistration_hash: Sha256Hex
    labels_hash: Sha256Hex
    configuration_hash: Sha256Hex
    train_labels: NonNegativeInt
    usable_labels: NonNegativeInt
    families: tuple[FamilyAgreement, ...]
    candidates: tuple[CandidateFit, ...]
    outcome: Literal["selected", "no_candidate"]
    selection: Selection | None
    scorers: tuple[ScorerAuc, ...]
    content_hash: Sha256Hex

    @model_validator(mode="after")
    def _selected_exactly_when_chosen(self) -> Self:
        if (self.outcome == "selected") != (self.selection is not None):
            raise ValueError("a selection exactly when the outcome is selected")
        return self


def frozen_configuration(
    extraction: RunRecord,
    proposals: ProposalRunRecord,
    support: SupportRunRecord,
    support_policy: SupportPolicy,
) -> dict[str, object]:
    """The models, prompts, policies and ceilings a calibrated policy is frozen
    with; ``support_policy`` must be the one ``support`` ran under."""
    ran_with = support_configuration(
        support_policy,
        support.ceilings,
        support.scorer_identity,
        support.judge_identities,
        support.extractor_family,
        support.cache_mode,
    )
    if digest(ran_with) != support.configuration_hash:
        raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, "support_policy")
    # A cache mode is how a run went, not what it is frozen with.
    bound = {name: value for name, value in ran_with.items() if name != "cache_mode"}
    return {
        "extraction": extraction.configuration.model_dump(mode="json"),
        "coding": {
            "codebook": proposals.codebook.model_dump(mode="json"),
            "classifier_identity": proposals.classifier_identity.model_dump(
                mode="json"
            ),
            "coding_policy": proposals.coding_policy.model_dump(mode="json"),
            "ceilings": proposals.ceilings.model_dump(mode="json"),
            "schema_hash": proposals.schema_hash,
            "coding_version": proposals.coding_version,
            "validator_version": proposals.validator_version,
        },
        "support": {
            **bound,
            "codebook": support.codebook.model_dump(mode="json"),
            "support_version": support.support_version,
            "validator_version": support.validator_version,
        },
    }


def configuration_hash(
    configuration: Mapping[str, object], selection: Selection | None
) -> str:
    """The artifact's ``configuration_hash`` (D19-14): the digest of the frozen
    configuration together with the selection it was calibrated to, or ``None``."""
    return digest(
        {
            "configuration": dict(configuration),
            "selection": None
            if selection is None
            else selection.model_dump(mode="json"),
        }
    )


def _family(
    preregistration: Preregistration,
    family: str,
    joint: Mapping[str, int],
    views: Mapping[str, DecisionInput],
    events: Mapping[str, str],
) -> FamilyAgreement:
    kappa, ac1, labels, uncertain = judge_agreement(
        (
            (
                events[target_id],
                label,
                *family_judgement(views[target_id].trials, family),
            )
            for target_id, label in joint.items()
        ),
        preregistration.bootstrap,
    )
    lower = kappa.interval.lower
    return FamilyAgreement(
        family=family,
        kappa=kappa,
        ac1=ac1,
        labels=labels,
        uncertain=uncertain,
        meets_floor=lower is not None and lower >= preregistration.floor.floor,
    )


def calibrate(
    preregistration: Preregistration,
    labels: SupportLabelSet,
    *,
    labels_hash: str,
    views: Mapping[str, DecisionInput],
    alternative: Mapping[str, float | None],
    events: Mapping[str, str],
    configuration: Mapping[str, object],
    version: int = 1,
) -> CalibrationArtifact:
    """Calibrate on train's labels: the floor test, the fit, the selection and AUC.
    ``views`` are the MiniCheck support run's ``decision_inputs``; ``alternative``
    is DeBERTa's joint score by target; ``events`` maps each target to its event;
    ``configuration`` is ``frozen_configuration``'s."""
    if not hash_matches(preregistration):
        raise EvaluationError(
            EvaluationProblem.PREREGISTRATION_MISMATCH, "content_hash"
        )
    if labels.preregistration_hash != preregistration.content_hash:
        raise EvaluationError(EvaluationProblem.PREREGISTRATION_MISMATCH, "labels")
    train = labels.of(Partition.TRAIN)
    for label in train:
        view = views.get(label.target_id)
        if view is None:
            raise EvaluationError(EvaluationProblem.UNKNOWN_TARGET, label.target_id)
        if view.target.input_hash != label.target_input_hash:
            raise EvaluationError(
                EvaluationProblem.TARGET_HASH_MISMATCH, label.target_id
            )
        if label.target_id not in events:
            raise EvaluationError(EvaluationProblem.UNKNOWN_EVENT, label.target_id)
    joint = {
        label.target_id: value
        for label in train
        if (value := joint_label(label)) is not None
    }
    if len(joint) < preregistration.sampling.minimum_usable:
        raise EvaluationError(EvaluationProblem.TOO_FEW_LABELS, "labels")
    agreement = tuple(
        _family(preregistration, family, joint, views, events)
        for family in families(t for i in joint for t in views[i].trials)
    )
    population = sorted(joint)
    human = human_labels(
        [label for label in train if label.target_id in joint], "joint_support"
    )
    rho = preregistration.selection.recall_floor
    fits = []
    for candidate in preregistration.menu:
        grid = []
        for cutoff in candidate.grid:
            decisions = [
                Acceptance(
                    target_id=t,
                    task="joint_support",
                    accepted=accepts(ScorerCutoff(cutoff), views[t]),
                )
                for t in population
            ]
            p = accepted_claim_precision(
                population, human, decisions, task="joint_support"
            )
            r = accepted_claim_recall(
                population, human, decisions, task="joint_support"
            )
            grid.append(
                CutoffFigure(
                    cutoff=cutoff,
                    precision=p.value,
                    recall=r.value,
                    accepted=p.accepted_count,
                )
            )
        meeting = [
            g
            for g in grid
            if g.precision is not None and g.recall is not None and g.recall >= rho
        ]
        best = min(meeting, key=lambda g: (-g.precision, g.cutoff), default=None)
        fits.append(
            CandidateFit(
                candidate_id=candidate.candidate_id,
                signals=candidate.signals,
                cutoff=None if best is None else best.cutoff,
                precision=None if best is None else best.precision,
                recall=None if best is None else best.recall,
                grid=tuple(grid),
            )
        )
    chosen = min(
        (f for f in fits if f.cutoff is not None),
        key=lambda f: (-f.precision, f.signals, f.cutoff, f.candidate_id),
        default=None,
    )
    selection = (
        None
        if chosen is None
        else Selection(
            candidate_id=chosen.candidate_id,
            rule="scorer_cutoff",
            signal="minicheck_joint",
            cutoff=chosen.cutoff,
        )
    )
    claimed = [label for label in train if claim_label(label) is not None]
    ids = sorted(label.target_id for label in train)
    claims = human_labels(claimed, "claim_support")
    scorers = tuple(
        ScorerAuc(
            scorer=scorer,
            report=auc_roc(
                ids,
                claims,
                [
                    ContinuousSignal(
                        target_id=t, task="claim_support", view=view, score=score(t)
                    )
                    for t in ids
                ],
                task="claim_support",
                view=view,
            ),
        )
        for scorer, view, score in (
            ("minicheck", "minicheck_joint", lambda t: joint_score(views[t])),
            ("deberta", "deberta_joint", lambda t: alternative.get(t)),
        )
    )
    return sealed(
        CalibrationArtifact(
            calibration_version=version,
            preregistration_hash=preregistration.content_hash,
            labels_hash=labels_hash,
            configuration_hash=configuration_hash(configuration, selection),
            train_labels=len(train),
            usable_labels=len(joint),
            families=agreement,
            candidates=tuple(fits),
            outcome="no_candidate" if selection is None else "selected",
            selection=selection,
            scorers=scorers,
            content_hash="0" * 64,
        )
    )
