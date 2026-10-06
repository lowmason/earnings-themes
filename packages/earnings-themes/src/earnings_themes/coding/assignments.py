"""Unique quote–theme projection, without inference, aggregation, or policy votes."""

from collections.abc import Sequence
from typing import Literal

import polars as pl
from earnings_core import digest

from earnings_themes.coding.decide import (
    DecisionSet,
    eligible_quote_ids,
    proposal_run_hash,
    support_run_hash,
)
from earnings_themes.coding.input import resolve_coding_input
from earnings_themes.coding.records import (
    Assignment,
    AssignmentClaimLink,
    AssignmentDecision,
    CodingError,
    PolicyReference,
    checked,
)
from earnings_themes.support import reverify_support_run
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import StoredSupportRun, SupportSources

ASSIGNMENT_SCHEMA = {
    "schema_version": pl.Int64,
    "assignment_id": pl.String,
    "coding_run_id": pl.String,
    "doc_id": pl.String,
    "quote_id": pl.String,
    "theme_id": pl.String,
    "codebook": pl.Struct(
        {
            "codebook_id": pl.String,
            "codebook_version": pl.Int64,
            "content_hash": pl.String,
        }
    ),
    "canonical_hash": pl.String,
    "start": pl.Int64,
    "end": pl.Int64,
    "validator_version": pl.String,
    "mask_ids": pl.List(pl.String),
    "support_run_hash": pl.String,
    "policy_hash": pl.String,
    "policy_kind": pl.String,
}


def assignment_key(
    decision: AssignmentDecision | Assignment, quote_id: str
) -> tuple[str, str, int, str, str, str]:
    book = decision.codebook
    return (
        decision.coding_run_id,
        book.codebook_id,
        book.codebook_version,
        decision.doc_id,
        decision.theme_id,
        quote_id,
    )


def assignment_id(key: tuple[str, str, int, str, str, str]) -> str:
    return "assignment-" + digest(key)


def merge_assignment(
    rows: dict, links: dict, key: tuple, row: Assignment, link: AssignmentClaimLink
) -> None:
    previous = rows.get(key)
    if previous is not None and previous != row:
        raise CodingError("invalid_references")
    rows[key] = row
    links[(link.assignment_id, link.doc_id, link.claim_id, link.decision_id)] = link


def _bound_decisions(
    decisions: DecisionSet, support: StoredSupportRun
) -> tuple[AssignmentDecision, ...]:
    """Check saved provenance and safety; external policy recomputation is downstream."""
    if (
        type(decisions) is not DecisionSet
        or type(decisions.decisions) is not tuple
        or type(decisions.sources) is not SupportSources
    ):
        raise CodingError("malformed_record")
    if (
        type(support) is not StoredSupportRun
        or type(decisions.support) is not StoredSupportRun
        or decisions.support != support
    ):
        raise CodingError("invalid_references")
    proposals, sources = decisions.proposals, decisions.sources
    source_hash = digest(
        {
            "record": sources.stored_run.record.model_dump(mode="json"),
            "provenance_hash": sources.provenance_hash,
        }
    )
    if (
        proposal_run_hash(proposals) != decisions.proposal_hash
        or support_run_hash(support) != decisions.support_run_hash
        or source_hash != decisions.source_run_hash
        or source_hash != proposals.record.source_run_hash
        or source_hash != support.record.source_run_hash
        or proposals.record.source_run_id != support.record.source_run_id
        or proposals.record.source_run_id != sources.stored_run.record.run_id
        or proposals.record.documents != support.record.documents
        or proposals.record.codebook != support.record.codebook
    ):
        raise CodingError("input_changed")
    outcomes = {row.target_id: row for row in reverify_support_run(support, sources)}
    policy = (
        checked(decisions.policy, PolicyReference)
        if decisions.policy is not None
        else None
    )
    if policy is not None and (
        policy.codebook != proposals.record.codebook
        or policy.classifier_configuration_hash != proposals.record.configuration_hash
        or policy.support_configuration_hash != support.record.configuration_hash
    ):
        raise CodingError("policy_mismatch")
    stored = {
        digest(row.target.model_dump(mode="json")): row for row in support.targets
    }
    proposed, inputs = {}, {}
    for proposal in proposals.proposals:
        target = proposal.target
        key = digest(target.model_dump(mode="json"))
        if key in proposed:
            raise CodingError("invalid_references")
        claim_key = (target.doc_id, target.claim_id)
        if claim_key not in inputs:
            inputs[claim_key] = resolve_coding_input(sources, *claim_key)
        current = inputs[claim_key]
        matches = [
            probe.record for probe in current.probes if probe.record.target == target
        ]
        if (
            len(matches) != 1
            or proposal.input_hash != current.input_hash
            or proposal.coding_run_id != proposals.record.run_id
        ):
            raise CodingError("input_changed")
        proposed[key] = (proposal, stored.get(key, matches[0]))
    if not set(stored) <= set(proposed):
        raise CodingError("invalid_references")
    by_id = {
        target.target_id: (proposal, target) for proposal, target in proposed.values()
    }
    rows = tuple(checked(row, AssignmentDecision) for row in decisions.decisions)
    if (
        len(by_id) != len(proposed)
        or len(rows) != len(by_id)
        or len({row.decision_id for row in rows}) != len(rows)
        or {row.target_id for row in rows} != set(by_id)
    ):
        raise CodingError("invalid_references")
    for row in rows:
        proposal, target = by_id[row.target_id]
        if (
            row.coding_run_id != proposals.record.run_id
            or (row.doc_id, row.claim_id, row.theme_id)
            != (
                proposal.target.doc_id,
                proposal.target.claim_id,
                proposal.target.theme_id,
            )
            or row.codebook != proposal.target.codebook
            or row.input_hash != proposal.input_hash
            or row.proposal_hash != decisions.proposal_hash
            or row.support_run_hash != decisions.support_run_hash
            or row.policy != policy
        ):
            raise CodingError("invalid_references")
        outcome = outcomes.get(row.target_id)
        if outcome is None:
            if (row.reason, row.support_status, row.flags, row.missing) != (
                "missing_assessment",
                None,
                (),
                ("missing_assessment",),
            ):
                raise CodingError("invalid_references")
        elif (row.support_status, row.flags, row.missing) != (
            outcome.status,
            outcome.flags,
            outcome.missing,
        ):
            raise CodingError("invalid_references")
        if row.status == "accepted":
            evidence = tuple(
                e for e in support.evidence if e.target_id == row.target_id
            )
            trials = tuple(t for t in support.trials if t.target_id == row.target_id)
            if not set(row.supporting_quote_ids) <= set(
                eligible_quote_ids(evidence, trials)
            ):
                raise CodingError("invalid_contribution")
    return rows


def project_assignments(
    decisions: DecisionSet, support: StoredSupportRun
) -> tuple[tuple[Assignment, ...], tuple[AssignmentClaimLink, ...]]:
    """Project accepted saved decisions after current deterministic evidence checks."""
    try:
        bound = _bound_decisions(decisions, support)
        evidence = {
            (reference.target_id, reference.doc_id, reference.quote_id): reference
            for reference in support.evidence
        }
        rows, links = {}, {}
        for decision in bound:
            if decision.status != "accepted":
                continue
            for quote_id in decision.supporting_quote_ids:
                reference = evidence.get(
                    (decision.target_id, decision.doc_id, quote_id)
                )
                if reference is None:
                    raise CodingError("invalid_references")
                key = assignment_key(decision, quote_id)
                row = Assignment(
                    assignment_id=assignment_id(key),
                    coding_run_id=decision.coding_run_id,
                    doc_id=decision.doc_id,
                    quote_id=quote_id,
                    theme_id=decision.theme_id,
                    codebook=decision.codebook,
                    canonical_hash=reference.canonical_hash,
                    start=reference.start,
                    end=reference.end,
                    validator_version=reference.validator_version,
                    mask_ids=reference.mask_ids,
                    support_run_hash=decision.support_run_hash,
                    policy_hash=decision.policy.policy_hash,
                    policy_kind=decision.policy.kind,
                )
                link = AssignmentClaimLink(
                    assignment_id=row.assignment_id,
                    doc_id=decision.doc_id,
                    claim_id=decision.claim_id,
                    decision_id=decision.decision_id,
                    target_id=decision.target_id,
                )
                merge_assignment(rows, links, key, row, link)
        return (
            tuple(rows[key] for key in sorted(rows)),
            tuple(links[key] for key in sorted(links)),
        )
    except CodingError:
        raise
    except SupportError as error:
        raise CodingError(str(error)) from None
    except Exception:  # noqa: BLE001 - never expose arbitrary source-bearing diagnostics
        raise CodingError("unexpected_error") from None


def assignment_frame(
    rows: Sequence[Assignment],
    *,
    scope: Literal["production", "fixture"] = "production",
) -> pl.DataFrame:
    """Validate one codebook/scope and unique grain before a typed Polars frame."""
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise CodingError("malformed_record")
    rows = tuple(checked(row, Assignment) for row in rows)
    books = {
        (
            row.codebook.codebook_id,
            row.codebook.codebook_version,
            row.codebook.content_hash,
        )
        for row in rows
    }
    if len(books) > 1:
        raise CodingError("mixed_codebook")
    expected = (
        {"production": "calibrated", "fixture": "fixture"}.get(scope)
        if type(scope) is str
        else None
    )
    if expected is None or any(row.policy_kind != expected for row in rows):
        raise CodingError("fixture_policy")
    keys = [assignment_key(row, row.quote_id) for row in rows]
    if len(keys) != len(set(keys)) or len({row.assignment_id for row in rows}) != len(
        rows
    ):
        raise CodingError("invalid_references")
    try:
        return pl.DataFrame(
            [row.model_dump(mode="json") for row in rows],
            schema=ASSIGNMENT_SCHEMA,
            orient="row",
        )
    except (pl.exceptions.PolarsError, OverflowError, TypeError, ValueError):
        raise CodingError("malformed_record") from None
