"""Pure assignment decisions over reverified proposal and support provenance.

Stage 11 supplies calibrated policy artifacts and approval. This module implements
no policy, numeric gate, signal pooling, or calibration-artifact authority.
"""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Protocol

from earnings_core import VALIDATOR_VERSION, digest
from pydantic import BaseModel

from earnings_themes.coding.classify import classification_id
from earnings_themes.coding.input import resolve_coding_input
from earnings_themes.coding.records import (
    AssignmentDecision,
    AttributeRecord,
    ClassificationRecord,
    CodingAttempt,
    CodingError,
    NoveltyItem,
    PolicyReference,
    PolicyVote,
    ProposalRecord,
    ProposalRunRecord,
    checked,
    coding_configuration,
)
from earnings_themes.coding.run import ProposalRun
from earnings_themes.scope import gate, gated, once
from earnings_themes.support import reverify_support_run
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import (
    EntailmentSignal,
    EvidenceReference,
    JudgeTrial,
    ReviewOutcome,
    StoredSupportRun,
    SupportSources,
    TargetRecord,
)

REQUIRED_TRIALS = 4


@dataclass(frozen=True, repr=False)
class DecisionInput:
    target: TargetRecord
    evidence: tuple[EvidenceReference, ...]
    entailment: tuple[EntailmentSignal, ...]
    trials: tuple[JudgeTrial, ...]
    outcome: ReviewOutcome
    eligible_quote_ids: tuple[str, ...]


class AssignmentPolicy(Protocol):
    """Externally bound deterministic policy, never an inference callback."""

    @property
    def reference(self) -> PolicyReference: ...

    def evaluate(self, view: DecisionInput) -> PolicyVote: ...


@dataclass(frozen=True, repr=False)
class DecisionSet:
    decisions: tuple[AssignmentDecision, ...]
    proposals: ProposalRun
    support: StoredSupportRun
    sources: SupportSources
    policy: PolicyReference | None
    proposal_hash: str
    support_run_hash: str
    source_run_hash: str


def proposal_run_hash(proposals: ProposalRun) -> str:
    """Bind the manifest and every immutable proposal-run row, without raw text."""
    if type(proposals) is not ProposalRun:
        raise CodingError("malformed_record")
    models = {
        "classifications": ClassificationRecord,
        "attempts": CodingAttempt,
        "proposals": ProposalRecord,
        "attributes": AttributeRecord,
        "novelty": NoveltyItem,
    }
    material = {
        "record": checked(proposals.record, ProposalRunRecord).model_dump(mode="json")
    }
    for name, model in models.items():
        rows = getattr(proposals, name)
        if type(rows) is not tuple:
            raise CodingError("malformed_record")
        material[name] = [checked(row, model).model_dump(mode="json") for row in rows]
    return digest(material)


def support_run_hash(support: StoredSupportRun) -> str:
    """Hash the support manifest, whose artifact hashes bind its published rows."""
    return digest(support.record.model_dump(mode="json"))


def _support_content_hash(support: StoredSupportRun) -> str:
    """Catch callback mutation anywhere in retained support, including later views."""
    return digest(
        {
            "record": support.record.model_dump(mode="json"),
            **{
                name: [row.model_dump(mode="json") for row in getattr(support, name)]
                for name in (
                    "targets",
                    "evidence",
                    "contexts",
                    "entailment",
                    "trials",
                    "attempts",
                    "usage",
                    "outcomes",
                )
            },
        }
    )


def _dump(row: BaseModel) -> dict:
    return row.model_dump(mode="json", warnings=False)


def _row_hash(row: BaseModel) -> str:
    return digest(_dump(row))


_UNREADABLE = (ValueError, TypeError, AttributeError, OverflowError)


def _recheck_digest[T](compute: Callable[[T], str], value: T) -> str:
    """A re-check's digest of source or proposal rows. A value that no longer
    serializes is a change: base's full re-check refused it as ``input_changed``.
    Support-row digests stay outside this, as base refused those differently."""
    try:
        return compute(value)
    except _UNREADABLE:
        raise CodingError("input_changed") from None


def _view_rows(support: StoredSupportRun, target_id: str) -> tuple[tuple, ...]:
    """One target's evidence, entailment and trial rows, in stored order: the rows
    its decision view reads."""
    return tuple(
        tuple(row for row in getattr(support, name) if row.target_id == target_id)
        for name in ("evidence", "entailment", "trials")
    )


def _view_rows_hash(support: StoredSupportRun, target_id: str) -> str:
    return digest(
        [[_dump(row) for row in rows] for rows in _view_rows(support, target_id)]
    )


def _sources_content_hash(sources: SupportSources) -> str:
    """Catch callback mutation of the sources that one gate's checks read.

    A repeat check inside one gate reuses the gate's first result (plan 23, D23-1),
    so a change made in place since then shows here, not in that result.
    """
    run = sources.stored_run
    return digest(
        {
            "record": _dump(run.record),
            **{
                name: [_dump(row) for row in getattr(run, name)]
                for name in ("documents", "quotes", "claims")
            },
            "bundles": [
                {
                    "document": _dump(bundle.document),
                    "elements": [_dump(element) for element in bundle.elements],
                    "masks": [_dump(mask) for mask in bundle.masks],
                }
                for bundle in sources.bundles
            ],
            "codebook": _dump(sources.codebook),
            "provenance_hash": sources.provenance_hash,
        }
    )


@contextmanager
def _refuse_changes() -> Iterator[None]:
    """A failed re-check refuses as ``input_changed``; a redacted error stays one."""
    try:
        yield
    except CodingError as error:
        if str(error) == "unexpected_error":
            raise CodingError("unexpected_error") from None
        raise CodingError("input_changed") from None
    except SupportError:
        raise CodingError("input_changed") from None


def _current_proposal_inputs(
    proposals: ProposalRun, sources: SupportSources
) -> dict[str, TargetRecord]:
    """``_proposal_inputs``, which one gate computes once (plan 23, D23-1)."""
    return once(
        "proposal_inputs",
        (proposals, sources),
        lambda: _proposal_inputs(proposals, sources),
    )


def _proposal_inputs(
    proposals: ProposalRun, sources: SupportSources
) -> dict[str, TargetRecord]:
    """Recompute all proposed inputs through Task 2's public complete-source gate."""
    record = checked(proposals.record, ProposalRunRecord)
    source_hash = digest(
        {
            "record": sources.stored_run.record.model_dump(mode="json"),
            "provenance_hash": sources.provenance_hash,
        }
    )
    if (
        record.source_run_hash != source_hash
        or record.source_run_id != sources.stored_run.record.run_id
    ):
        raise CodingError("input_changed")
    if record.documents != tuple(sorted(sources.stored_run.record.documents.items())):
        raise CodingError("input_changed")
    configuration = coding_configuration(
        source_run_id=record.source_run_id,
        source_run_hash=record.source_run_hash,
        documents=record.documents,
        codebook=record.codebook,
        classifier_identity=record.classifier_identity,
        coding_policy=record.coding_policy,
        ceilings=record.ceilings,
        requested_claim_order=record.requested_claim_order,
        schema_hash=record.schema_hash,
        coding_version=record.coding_version,
        validator_version=record.validator_version,
        cache_mode=record.cache_mode,
    )
    if (
        digest(configuration) != record.configuration_hash
        or record.validator_version != VALIDATOR_VERSION
    ):
        raise CodingError("input_changed")
    classifications = {
        row.classification_id: checked(row, ClassificationRecord)
        for row in proposals.classifications
    }
    if len(classifications) != len(proposals.classifications):
        raise CodingError("invalid_references")
    if (
        tuple((row.doc_id, row.claim_id) for row in classifications.values())
        != record.requested_claim_order
    ):
        raise CodingError("invalid_references")
    current = {}
    inputs = {}
    for proposal in proposals.proposals:
        proposal = checked(proposal, ProposalRecord)
        target = proposal.target
        key = digest(target.model_dump(mode="json"))
        if key in current:
            raise CodingError("invalid_references")
        claim_key = (target.doc_id, target.claim_id)
        if claim_key not in inputs:
            inputs[claim_key] = resolve_coding_input(sources, *claim_key)
        input = inputs[claim_key]
        matches = [
            probe.record for probe in input.probes if probe.record.target == target
        ]
        classification = classifications.get(proposal.classification_id)
        if (
            len(matches) != 1
            or proposal.input_hash != input.input_hash
            or proposal.coding_run_id != record.run_id
            or classification is None
            or classification.status != "completed"
            or classification.codebook != record.codebook
            or classification.coding_run_id != record.run_id
            or classification.input_hash != input.input_hash
            or (classification.doc_id, classification.claim_id) != claim_key
            or classification.classification_id
            != classification_id(record.run_id, *claim_key, input.input_hash)
            or proposal.proposal_id
            != "proposal-"
            + digest(
                {
                    "classification_id": proposal.classification_id,
                    "target": target.model_dump(mode="json"),
                }
            )
        ):
            raise CodingError("input_changed")
        current[key] = matches[0]
    for classification in classifications.values():
        themes = tuple(
            proposal.target.theme_id
            for proposal in proposals.proposals
            if proposal.classification_id == classification.classification_id
        )
        if themes != classification.theme_ids:
            raise CodingError("invalid_references")
    return current


def _policy_reference(
    policy: AssignmentPolicy | None, proposals: ProposalRun, support: StoredSupportRun
) -> PolicyReference | None:
    if policy is None:
        return None
    try:
        raw = policy.reference
    except Exception:  # noqa: BLE001 - external property failures never print data
        raise CodingError("unexpected_error") from None
    reference = checked(raw, PolicyReference)
    if (
        reference.codebook != proposals.record.codebook
        or reference.codebook != support.record.codebook
        or reference.classifier_configuration_hash
        != proposals.record.configuration_hash
        or reference.support_configuration_hash != support.record.configuration_hash
    ):
        raise CodingError("policy_mismatch")
    return reference


def eligible_quote_ids(
    evidence: tuple[EvidenceReference, ...], trials: tuple[JudgeTrial, ...]
) -> tuple[str, ...]:
    """Complete consistent supporting contributions establish eligibility only."""
    if len(trials) != REQUIRED_TRIALS or any(trial.answer is None for trial in trials):
        raise CodingError("assessment_incomplete")
    expected = {reference.quote_id for reference in evidence}
    answers = []
    for trial in trials:
        contributions = {
            quote.quote_id: quote.contribution
            for quote in trial.answer.quote_assessments
        }
        if set(contributions) != expected or len(contributions) != len(
            trial.answer.quote_assessments
        ):
            raise CodingError("invalid_references")
        answers.append(contributions)
    return tuple(
        sorted(
            quote_id
            for quote_id in expected
            if all(answer[quote_id] == "supporting" for answer in answers)
        )
    )


def decision_input(
    support: StoredSupportRun, target: TargetRecord, outcome: ReviewOutcome
) -> DecisionInput:
    """One stored target's view: its evidence, signals and trials, and, when it is
    ``assessed``, its eligible quotes. ``outcome`` is the reverified outcome."""
    evidence, entailment, trials = _view_rows(support, target.target_id)
    eligible = (
        eligible_quote_ids(evidence, trials) if outcome.status == "assessed" else ()
    )
    return DecisionInput(target, evidence, entailment, trials, outcome, eligible)


def decision_inputs(
    support: StoredSupportRun, sources: SupportSources
) -> dict[str, DecisionInput]:
    """Every stored target's view, by target ID, after the consuming gate
    reverifies the run, as ``decide_assignments`` builds them (Stage 11's
    calibration reads exactly these, plan 19)."""
    try:
        outcomes = {o.target_id: o for o in reverify_support_run(support, sources)}
        return {
            target.target_id: decision_input(
                support, target, outcomes[target.target_id]
            )
            for target in support.targets
        }
    except CodingError:
        raise
    except SupportError as error:
        raise CodingError(str(error)) from None
    except Exception:  # noqa: BLE001 - boundary failures never print source data
        raise CodingError("unexpected_error") from None


def _view_hash(view: DecisionInput) -> str:
    return digest(
        {
            "target": view.target.model_dump(mode="json"),
            "evidence": [row.model_dump(mode="json") for row in view.evidence],
            "entailment": [row.model_dump(mode="json") for row in view.entailment],
            "trials": [row.model_dump(mode="json") for row in view.trials],
            "outcome": view.outcome.model_dump(mode="json"),
            "eligible_quote_ids": view.eligible_quote_ids,
        }
    )


def decision_vote(
    view: DecisionInput, policy: AssignmentPolicy | None
) -> tuple[str, str, tuple[str, ...]]:
    """Safety outcomes precede external policy; raw scores never decide acceptance."""
    if view.outcome.status == "refused":
        return "refused", "assessment_refused", ()
    if view.outcome.status == "incomplete":
        return "review", "assessment_incomplete", ()
    if view.outcome.status == "flagged":
        return "review", "assessment_flagged", ()
    if policy is None:
        return "review", "calibration_required", ()
    before = _view_hash(view)
    try:
        raw = policy.evaluate(view)
    except Exception:  # noqa: BLE001 - external policy failures never print data
        raise CodingError("unexpected_error") from None
    if _view_hash(view) != before:
        raise CodingError("input_changed") from None
    vote = checked(raw, PolicyVote)
    if vote.action == "accept":
        if not set(vote.supporting_quote_ids) <= set(view.eligible_quote_ids):
            raise CodingError("invalid_contribution")
        return "accepted", "policy_accept", tuple(sorted(vote.supporting_quote_ids))
    if vote.action == "reject":
        return "rejected", "policy_reject", ()
    return "review", "policy_review", ()


def _proposal_support_inputs(
    proposals: ProposalRun, support: StoredSupportRun, sources: SupportSources
) -> tuple[tuple[ReviewOutcome, ...], dict[str, TargetRecord], dict[str, TargetRecord]]:
    """The shared reverified gate before calibration or assignment consumption."""
    outcomes = reverify_support_run(support, sources)
    current = _current_proposal_inputs(proposals, sources)
    if (
        support.record.source_run_hash != proposals.record.source_run_hash
        or support.record.source_run_id != proposals.record.source_run_id
        or support.record.codebook != proposals.record.codebook
        or support.record.documents != proposals.record.documents
    ):
        raise CodingError("input_changed")
    stored = {
        digest(row.target.model_dump(mode="json")): row for row in support.targets
    }
    if not set(stored) <= set(current):
        raise CodingError("invalid_references")
    return outcomes, current, stored


@gated
def validate_proposal_support(
    proposals: ProposalRun, support: StoredSupportRun, sources: SupportSources
) -> None:
    """Refuse a proposal/support pair unless both bind the complete current source."""
    try:
        proposal_run_hash(proposals)
        _proposal_support_inputs(proposals, support, sources)
    except CodingError:
        raise
    except SupportError as error:
        raise CodingError(str(error)) from None
    except Exception:  # noqa: BLE001 - boundary failures never print source data
        raise CodingError("unexpected_error") from None


@gated
def decide_assignments(
    proposals: ProposalRun,
    support: StoredSupportRun,
    sources: SupportSources,
    policy: AssignmentPolicy | None,
) -> DecisionSet:
    """One decision per proposal, after current evidence and frozen-policy checks.

    The gate checks its inputs in full before the loop and again, in a fresh scope,
    after it. Per target it compares the policy reference and content digests of the
    target's rows, so a callback that changes another input in place is refused at
    the end of the gate (plan 23, D21-34, D23-1).
    """
    try:
        proposal_hash = proposal_run_hash(proposals)
        outcomes, current, stored = _proposal_support_inputs(
            proposals, support, sources
        )
        support_hash = support_run_hash(support)
        support_content_hash = _support_content_hash(support)
        sources_content_hash = _sources_content_hash(sources)
        # The digests each per-target re-check compares, taken before external code
        # runs. Each key is taken now too, so a later change cannot redirect it.
        outcome_rows = {row.target_id: row for row in support.outcomes}
        rows = tuple(
            (
                proposal,
                digest(proposal.target.model_dump(mode="json")),
                _row_hash(proposal),
            )
            for proposal in proposals.proposals
        )
        target_rows = {
            key: (
                target.target_id,
                outcome_rows[target.target_id],
                _row_hash(target),
                _row_hash(outcome_rows[target.target_id]),
                _view_rows_hash(support, target.target_id),
            )
            for key, target in stored.items()
        }
        reference = _policy_reference(policy, proposals, support)

        def require_current() -> None:
            with _refuse_changes():
                again = _policy_reference(policy, proposals, support)
                if (
                    again != reference
                    or proposal_run_hash(proposals) != proposal_hash
                    or _support_content_hash(support) != support_content_hash
                    or _recheck_digest(_sources_content_hash, sources)
                    != sources_content_hash
                ):
                    raise CodingError("input_changed")
                reverify_support_run(support, sources)
                if _current_proposal_inputs(proposals, sources) != current:
                    raise CodingError("input_changed")

        def require_target(proposal, proposal_row, key, *, voted=False) -> None:
            """One target's re-check by content digest: its proposal, support and
            outcome rows and, before its vote, the evidence, entailment and trial
            rows the vote reads. After a vote, the policy reference too. Anything
            else is checked again at the end of the gate."""
            with _refuse_changes():
                if voted and _policy_reference(policy, proposals, support) != reference:
                    raise CodingError("input_changed")
                if _recheck_digest(_row_hash, proposal) != proposal_row:
                    raise CodingError("input_changed")
                if key not in target_rows:
                    return
                target_id, outcome_row, target_hash, outcome_hash, view_hash = (
                    target_rows[key]
                )
                if (
                    _row_hash(stored[key]) != target_hash
                    or _row_hash(outcome_row) != outcome_hash
                    or (not voted and _view_rows_hash(support, target_id) != view_hash)
                ):
                    raise CodingError("input_changed")

        # Reference properties are external code too; recheck after reading them.
        require_current()
        by_id = {outcome.target_id: outcome for outcome in outcomes}
        decisions = []
        for proposal, key, proposal_row in rows:
            require_target(proposal, proposal_row, key)
            target = stored.get(key)
            if target is None:
                target_id = current[key].target_id
                status, reason, quote_ids = "review", "missing_assessment", ()
                support_status, flags, missing = None, (), ("missing_assessment",)
            else:
                outcome = by_id[target.target_id]
                view = decision_input(support, target, outcome)
                status, reason, quote_ids = decision_vote(view, policy)
                require_target(proposal, proposal_row, key, voted=True)
                target_id = target.target_id
                support_status, flags, missing = (
                    outcome.status,
                    outcome.flags,
                    outcome.missing,
                )
            decisions.append(
                AssignmentDecision(
                    coding_run_id=proposals.record.run_id,
                    decision_id="decision-"
                    + digest(
                        {
                            "target_id": target_id,
                            "proposal_hash": proposal_hash,
                            "support_run_hash": support_hash,
                            "policy": reference.model_dump(mode="json")
                            if reference is not None
                            else None,
                        }
                    ),
                    doc_id=proposal.target.doc_id,
                    claim_id=proposal.target.claim_id,
                    theme_id=proposal.target.theme_id,
                    codebook=proposal.target.codebook,
                    target_id=target_id,
                    support_run_hash=support_hash,
                    support_status=support_status,
                    flags=flags,
                    missing=missing,
                    status=status,
                    reason=reason,
                    policy=reference,
                    supporting_quote_ids=quote_ids,
                    proposal_hash=proposal_hash,
                    input_hash=proposal.input_hash,
                )
            )
        # A fresh scope checks everything again, so a change made in place during
        # the loop is not hidden by a result the gate remembers (D21-34).
        with gate(fresh=True):
            require_current()
        return DecisionSet(
            tuple(decisions),
            proposals,
            support,
            sources,
            reference,
            proposal_hash,
            support_hash,
            proposals.record.source_run_hash,
        )
    except CodingError:
        raise
    except SupportError as error:
        raise CodingError(str(error)) from None
    except Exception:  # noqa: BLE001 - boundary failures never print source data
        raise CodingError("unexpected_error") from None
