"""Immutable typed coding tables with separate structural and consuming gates."""

import io
import json
import os
import shutil
import tempfile
from collections import Counter
from pathlib import Path

import polars as pl
from earnings_core import VALIDATOR_VERSION, canonical_json, digest, sha256_hex

from earnings_themes.codebook import Codebook, CodebookStatus, codebook_hash
from earnings_themes.coding.assignments import (
    ASSIGNMENT_SCHEMA,
    assignment_id,
    assignment_key,
    project_assignments,
)
from earnings_themes.coding.classify import classification_id
from earnings_themes.coding.decide import (
    AssignmentPolicy,
    DecisionSet,
    decide_assignments,
    proposal_run_hash,
    support_run_hash,
)
from earnings_themes.coding.input import resolve_coding_input
from earnings_themes.coding.prompt import check_hierarchy, novelty_for
from earnings_themes.coding.records import (
    Assignment,
    AssignmentClaimLink,
    AssignmentDecision,
    AttributeRecord,
    ClassificationRecord,
    CodingAttempt,
    CodingError,
    CodingReply,
    CodingRun,
    CodingRunRecord,
    NoveltyItem,
    PolicyReference,
    ProposalRecord,
    ProposalRunRecord,
    checked,
)
from earnings_themes.coding.run import ProposalRun, refused_input_hash
from earnings_themes.extraction.records import RunRecord
from earnings_themes.records import record_json
from earnings_themes.support import reverify_support_run
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import (
    CodebookReference,
    StoredSupportRun,
    SupportSources,
)

IDS = pl.List(pl.String)
BOOK = pl.Struct(
    {"codebook_id": pl.String, "codebook_version": pl.Int64, "content_hash": pl.String}
)
TARGET = pl.Struct(
    {
        "source_run_id": pl.String,
        "doc_id": pl.String,
        "claim_id": pl.String,
        "theme_id": pl.String,
        "codebook": BOOK,
    }
)
ATTRIBUTES = pl.Struct(
    {name: pl.String for name in ("topic", "sentiment", "direction", "event_type")}
)
POLICY = pl.Struct(
    {
        "policy_id": pl.String,
        "policy_hash": pl.String,
        "kind": pl.String,
        "codebook": BOOK,
        "classifier_configuration_hash": pl.String,
        "support_configuration_hash": pl.String,
        "calibration_reference": pl.String,
    }
)
SCHEMAS = {
    "classifications": (
        ClassificationRecord,
        pl.Schema(
            {
                "schema_version": pl.Int64,
                "classification_id": pl.String,
                "coding_run_id": pl.String,
                "doc_id": pl.String,
                "claim_id": pl.String,
                "input_hash": pl.String,
                "codebook": BOOK,
                "status": pl.String,
                "reason": pl.String,
                "attempt_ids": IDS,
                "theme_ids": IDS,
            }
        ),
    ),
    "attempts": (
        CodingAttempt,
        pl.Schema(
            {
                "schema_version": pl.Int64,
                "attempt_id": pl.String,
                "classification_id": pl.String,
                "doc_id": pl.String,
                "claim_id": pl.String,
                "attempt": pl.Int64,
                "request_hash": pl.String,
                "prompt_hash": pl.String,
                "schema_hash": pl.String,
                "input_hash": pl.String,
                "input_tokens": pl.Int64,
                "reserved_tokens": pl.Int64,
                "actual_prompt_tokens": pl.Int64,
                "actual_completion_tokens": pl.Int64,
                "unreported": pl.Boolean,
                "cached": pl.Boolean,
                "latency_ms": pl.Int64,
                "raw_ref": pl.String,
                "raw_hash": pl.String,
                "reason": pl.String,
            }
        ),
    ),
    "proposals": (
        ProposalRecord,
        pl.Schema(
            {
                "schema_version": pl.Int64,
                "proposal_id": pl.String,
                "coding_run_id": pl.String,
                "classification_id": pl.String,
                "target": TARGET,
                "input_hash": pl.String,
            }
        ),
    ),
    "attributes": (
        AttributeRecord,
        pl.Schema(
            {
                "schema_version": pl.Int64,
                "coding_run_id": pl.String,
                "doc_id": pl.String,
                "claim_id": pl.String,
                "input_hash": pl.String,
                "attributes": ATTRIBUTES,
            }
        ),
    ),
    "decisions": (
        AssignmentDecision,
        pl.Schema(
            {
                "schema_version": pl.Int64,
                "coding_run_id": pl.String,
                "decision_id": pl.String,
                "doc_id": pl.String,
                "claim_id": pl.String,
                "theme_id": pl.String,
                "codebook": BOOK,
                "target_id": pl.String,
                "support_run_hash": pl.String,
                "support_status": pl.String,
                "flags": IDS,
                "missing": IDS,
                "status": pl.String,
                "reason": pl.String,
                "policy": POLICY,
                "supporting_quote_ids": IDS,
                "proposal_hash": pl.String,
                "input_hash": pl.String,
            }
        ),
    ),
    "assignments": (Assignment, pl.Schema(ASSIGNMENT_SCHEMA)),
    "assignment_claims": (
        AssignmentClaimLink,
        pl.Schema(
            {
                "schema_version": pl.Int64,
                "assignment_id": pl.String,
                "doc_id": pl.String,
                "claim_id": pl.String,
                "decision_id": pl.String,
                "target_id": pl.String,
            }
        ),
    ),
    "novelty": (
        NoveltyItem,
        pl.Schema(
            {
                "schema_version": pl.Int64,
                "novelty_id": pl.String,
                "coding_run_id": pl.String,
                "classification_id": pl.String,
                "source_run_id": pl.String,
                "doc_id": pl.String,
                "claim_id": pl.String,
                "codebook": BOOK,
                "input_hash": pl.String,
                "original_quote_ids": IDS,
                "reason": pl.String,
            }
        ),
    ),
}
RETRYABLE = {
    "malformed_reply",
    "invalid_references",
    "hierarchy_conflict",
    "tool_call_refused",
    "model_mismatch",
    "transport_error",
}
BLOCKED = {"replay_miss", "input_too_long", "requests_exhausted", "tokens_exhausted"}
CONFIGURATION_FIELDS = (
    "source_run_id",
    "source_run_hash",
    "documents",
    "codebook",
    "classifier_identity",
    "coding_policy",
    "ceilings",
    "requested_claim_order",
    "schema_hash",
    "coding_version",
    "validator_version",
    "cache_mode",
)


def _require(condition: bool) -> None:
    if not condition:
        raise CodingError("storage_corrupt")


def _unique(rows, key) -> None:
    _require(len({key(row) for row in rows}) == len(rows))


def _json_rows(rows) -> bytes:
    return canonical_json([row.model_dump(mode="json") for row in rows])


def _proposals(stored: CodingRun) -> ProposalRun:
    """Reconstruct the exact pre-publication manifest beneath decision identity."""
    manifest = stored.record.model_dump(mode="json")
    material = {name: manifest[name] for name in ProposalRunRecord.model_fields}
    material["artifact_hashes"] = tuple(
        pair for pair in stored.record.artifact_hashes if pair[0].startswith("raw/")
    )
    return ProposalRun(
        checked(material, ProposalRunRecord),
        stored.classifications,
        stored.attempts,
        stored.proposals,
        stored.attributes,
        stored.novelty,
    )


def _check_classifications(stored: CodingRun) -> None:
    record = stored.record
    _unique(stored.classifications, lambda row: row.classification_id)
    _unique(stored.attempts, lambda row: row.attempt_id)
    _unique(stored.proposals, lambda row: row.proposal_id)
    _unique(stored.proposals, lambda row: digest(row.target.model_dump(mode="json")))
    _unique(stored.attributes, lambda row: (row.doc_id, row.claim_id))
    _unique(stored.novelty, lambda row: row.novelty_id)
    _require(
        tuple((row.doc_id, row.claim_id) for row in stored.classifications)
        == record.requested_claim_order
    )
    attempts, proposals, attributes, novelty = [], [], [], []
    for classification in stored.classifications:
        cid = classification.classification_id
        _require(
            classification.coding_run_id == record.run_id
            and classification.codebook == record.codebook
            and cid
            == classification_id(
                record.run_id,
                classification.doc_id,
                classification.claim_id,
                classification.input_hash,
            )
        )
        current_attempts = tuple(
            row for row in stored.attempts if row.classification_id == cid
        )
        current_proposals = tuple(
            row for row in stored.proposals if row.classification_id == cid
        )
        current_attributes = tuple(
            row
            for row in stored.attributes
            if (row.doc_id, row.claim_id)
            == (classification.doc_id, classification.claim_id)
        )
        current_novelty = tuple(
            row for row in stored.novelty if row.classification_id == cid
        )
        attempts.extend(current_attempts)
        proposals.extend(current_proposals)
        attributes.extend(current_attributes)
        novelty.extend(current_novelty)
        _require(
            classification.attempt_ids
            == tuple(row.attempt_id for row in current_attempts)
        )
        if classification.status == "refused":
            _require(
                not any(
                    (
                        current_attempts,
                        current_proposals,
                        current_attributes,
                        current_novelty,
                    )
                )
            )
            _require(
                classification.input_hash
                == refused_input_hash(
                    record.source_run_hash,
                    classification.doc_id,
                    classification.claim_id,
                    record.codebook,
                )
            )
            continue
        _require(
            classification.doc_id in dict(record.documents) and bool(current_attempts)
        )
        for ordinal, attempt in enumerate(current_attempts, 1):
            _require(
                attempt.attempt == ordinal
                and attempt.attempt_id == f"{cid}-attempt-{ordinal}"
                and (attempt.doc_id, attempt.claim_id, attempt.input_hash)
                == (
                    classification.doc_id,
                    classification.claim_id,
                    classification.input_hash,
                )
                and attempt.prompt_hash == record.coding_policy.prompt_hash
                and attempt.schema_hash == record.schema_hash
            )
            if ordinal == 2:
                _require(current_attempts[0].reason in RETRYABLE)
            if attempt.reason is None:
                _require(
                    attempt == current_attempts[-1] and attempt.raw_ref is not None
                )
            else:
                _require(attempt.reason in RETRYABLE | BLOCKED)
        if classification.status == "incomplete":
            _require(not any((current_proposals, current_attributes, current_novelty)))
            _require(classification.reason == current_attempts[-1].reason)
            _require(len(current_attempts) == 2 or classification.reason in BLOCKED)
            continue
        _require(current_attempts[-1].reason is None and len(current_attributes) == 1)
        _require(
            tuple(row.target.theme_id for row in current_proposals)
            == classification.theme_ids
        )
        for proposal in current_proposals:
            target = proposal.target
            _require(
                proposal.coding_run_id == record.run_id
                and proposal.input_hash == classification.input_hash
                and (target.doc_id, target.claim_id)
                == (classification.doc_id, classification.claim_id)
                and target.source_run_id == record.source_run_id
                and target.codebook == record.codebook
                and proposal.proposal_id
                == "proposal-"
                + digest(
                    {"classification_id": cid, "target": target.model_dump(mode="json")}
                )
            )
        attribute = current_attributes[0]
        _require(
            attribute.coding_run_id == record.run_id
            and attribute.input_hash == classification.input_hash
        )
        _require(len(current_novelty) == (0 if classification.theme_ids else 1))
        if current_novelty:
            item = current_novelty[0]
            _require(
                item.novelty_id
                == "novelty-"
                + digest(
                    {
                        "coding_run_id": record.run_id,
                        "classification_id": cid,
                        "input_hash": classification.input_hash,
                        "reason": "no_theme_fit",
                    }
                )
                and (
                    item.coding_run_id,
                    item.source_run_id,
                    item.doc_id,
                    item.claim_id,
                    item.codebook,
                    item.input_hash,
                )
                == (
                    record.run_id,
                    record.source_run_id,
                    classification.doc_id,
                    classification.claim_id,
                    record.codebook,
                    classification.input_hash,
                )
                and bool(item.original_quote_ids)
                and len(set(item.original_quote_ids)) == len(item.original_quote_ids)
            )
    for name, rows in (
        ("attempts", attempts),
        ("proposals", proposals),
        ("attributes", attributes),
        ("novelty", novelty),
    ):
        _require(tuple(rows) == getattr(stored, name))


def _check_accounting(stored: CodingRun) -> None:
    record = stored.record
    fresh = [row for row in stored.attempts if row.reserved_tokens > 0]
    _require(
        record.counts_by_status
        == tuple(sorted(Counter(row.status for row in stored.classifications).items()))
    )
    _require(
        record.counts_by_reason
        == tuple(
            sorted(
                Counter(
                    row.reason
                    for row in stored.classifications
                    if row.reason is not None
                ).items()
            )
        )
    )
    charge = lambda row: (
        row.reserved_tokens
        if row.unreported
        else (row.actual_prompt_tokens or 0) + (row.actual_completion_tokens or 0)
    )
    totals = {
        "requests": len(fresh),
        "prompt_tokens": sum(row.actual_prompt_tokens or 0 for row in fresh),
        "completion_tokens": sum(row.actual_completion_tokens or 0 for row in fresh),
        "reserved_tokens": sum(row.reserved_tokens for row in fresh),
        "charged_tokens": sum(charge(row) for row in fresh),
        "unreported": sum(row.unreported for row in fresh),
        "cache_hits": sum(row.cached for row in stored.attempts),
        "latency_ms": sum(row.latency_ms for row in fresh),
    }
    _require(all(getattr(record, name) == value for name, value in totals.items()))
    requests, document_requests, claim_requests, tokens, document_tokens = (
        0,
        Counter(),
        Counter(),
        0,
        Counter(),
    )
    ceilings = record.ceilings
    for row in stored.attempts:
        claim_key = (row.doc_id, row.claim_id)
        if row.cached:
            continue
        if row.reserved_tokens == 0:
            _require(
                row.reason in BLOCKED
                and row.raw_ref is None
                and row.actual_prompt_tokens is None
                and row.latency_ms == 0
            )
            if row.reason == "replay_miss":
                _require(record.cache_mode == "replay")
            elif row.reason == "input_too_long":
                _require(
                    row.input_tokens + record.coding_policy.parameters.max_tokens
                    > record.classifier_identity.input_limit
                    or record.coding_policy.parameters.max_tokens
                    > record.classifier_identity.output_limit
                )
            elif row.reason == "requests_exhausted":
                _require(
                    requests >= ceilings.requests_per_run
                    or document_requests[row.doc_id] >= ceilings.requests_per_document
                    or claim_requests[claim_key] >= ceilings.requests_per_claim
                )
            else:
                reserved = row.input_tokens + record.coding_policy.parameters.max_tokens
                _require(
                    tokens + reserved > ceilings.tokens_per_run
                    or document_tokens[row.doc_id] + reserved
                    > ceilings.tokens_per_document
                )
            continue
        _require(record.cache_mode == "live" and not row.cached)
        _require(
            row.reserved_tokens
            == row.input_tokens + record.coding_policy.parameters.max_tokens
        )
        _require(
            row.reserved_tokens <= record.classifier_identity.input_limit
            and record.coding_policy.parameters.max_tokens
            <= record.classifier_identity.output_limit
        )
        _require(
            requests < ceilings.requests_per_run
            and document_requests[row.doc_id] < ceilings.requests_per_document
            and claim_requests[claim_key] < ceilings.requests_per_claim
        )
        _require(
            tokens + row.reserved_tokens <= ceilings.tokens_per_run
            and document_tokens[row.doc_id] + row.reserved_tokens
            <= ceilings.tokens_per_document
        )
        requests += 1
        document_requests[row.doc_id] += 1
        claim_requests[claim_key] += 1
        tokens += charge(row)
        document_tokens[row.doc_id] += charge(row)
        if row.raw_ref is None:
            _require(
                row.reason == "transport_error"
                and row.actual_prompt_tokens is None
                and row.latency_ms == 0
            )


def _check_decisions(stored: CodingRun) -> None:
    record = stored.record
    _unique(stored.decisions, lambda row: row.decision_id)
    _unique(stored.decisions, lambda row: row.target_id)
    _require(len(stored.decisions) == len(stored.proposals))
    policy = record.policy
    if policy is not None:
        _require(
            policy.codebook == record.codebook
            and policy.classifier_configuration_hash == record.configuration_hash
            and policy.support_configuration_hash == record.support_configuration_hash
        )
    for proposal, decision in zip(stored.proposals, stored.decisions, strict=True):
        target = proposal.target
        _require(
            (
                decision.coding_run_id,
                decision.doc_id,
                decision.claim_id,
                decision.theme_id,
                decision.codebook,
                decision.input_hash,
            )
            == (
                record.run_id,
                target.doc_id,
                target.claim_id,
                target.theme_id,
                target.codebook,
                proposal.input_hash,
            )
            and decision.proposal_hash == record.proposal_hash
            and decision.support_run_hash == record.support_run_hash
            and decision.policy == policy
        )
    _require(
        record.counts_by_decision
        == tuple(sorted(Counter(row.status for row in stored.decisions).items()))
    )
    _require(
        record.counts_by_decision_reason
        == tuple(sorted(Counter(row.reason for row in stored.decisions).items()))
    )
    _unique(stored.assignments, lambda row: row.assignment_id)
    _unique(stored.assignments, lambda row: assignment_key(row, row.quote_id))
    by_key = {assignment_key(row, row.quote_id): row for row in stored.assignments}
    expected, links = {}, {}
    for decision in stored.decisions:
        for quote_id in decision.supporting_quote_ids:
            key = assignment_key(decision, quote_id)
            row = by_key.get(key)
            _require(row is not None)
            _require(
                row.assignment_id == assignment_id(key)
                and row.codebook == record.codebook
                and row.canonical_hash == dict(record.documents)[row.doc_id]
                and row.validator_version == record.validator_version
                and row.support_run_hash == record.support_run_hash
                and row.policy_hash == policy.policy_hash
                and row.policy_kind == policy.kind
            )
            expected[key] = row
            link = AssignmentClaimLink(
                assignment_id=row.assignment_id,
                doc_id=decision.doc_id,
                claim_id=decision.claim_id,
                decision_id=decision.decision_id,
                target_id=decision.target_id,
            )
            links[
                (link.assignment_id, link.doc_id, link.claim_id, link.decision_id)
            ] = link
    _require(stored.assignments == tuple(expected[key] for key in sorted(expected)))
    _require(stored.assignment_claims == tuple(links[key] for key in sorted(links)))


def _validate(stored: CodingRun, *, published: bool | None) -> CodingRun:
    """Strict schemas, original proposal hash, row graph and dispatch accounting."""
    try:
        _require(type(stored) is CodingRun)
        record = checked(stored.record, CodingRunRecord)
        if published is None:
            published = any(
                name.endswith(".parquet") for name, _ in record.artifact_hashes
            )
        tables = {}
        for name, (model, _) in SCHEMAS.items():
            _require(type(getattr(stored, name)) is tuple)
            tables[name] = tuple(checked(row, model) for row in getattr(stored, name))
        stored = CodingRun(record, **tables)
        material = record.model_dump(mode="json")
        _require(
            digest({name: material[name] for name in CONFIGURATION_FIELDS})
            == record.configuration_hash
        )
        _require(
            record.validator_version == VALIDATOR_VERSION
            and record.schema_hash == digest(CodingReply.model_json_schema())
        )
        raw_refs = {row.raw_ref for row in stored.attempts if row.raw_ref is not None}
        expected = {f"raw/{reference}" for reference in raw_refs}
        if published:
            expected |= {f"{name}.parquet" for name in SCHEMAS}
        _require(set(dict(record.artifact_hashes)) == expected)
        raw_bindings = {}
        for row in stored.attempts:
            if row.raw_ref is not None:
                binding = (row.request_hash, row.raw_hash, row.input_tokens)
                _require(
                    row.raw_ref not in raw_bindings
                    or raw_bindings[row.raw_ref] == binding
                )
                raw_bindings[row.raw_ref] = binding
        _check_classifications(stored)
        _check_accounting(stored)
        _require(proposal_run_hash(_proposals(stored)) == record.proposal_hash)
        _check_decisions(stored)
        return stored
    except Exception:  # noqa: BLE001 - validation may contain source-bearing data
        raise CodingError("storage_corrupt") from None


def _current_inputs(stored: CodingRun, sources: SupportSources) -> None:
    """Check every requested boundary, including unmatched and refused claims."""
    record = stored.record
    # Empty/all-refused runs must bind the supplied book without target resolution.
    try:
        if type(sources.codebook) is not Codebook:
            raise CodingError("input_changed")
        book = checked(sources.codebook, Codebook)
        reference = CodebookReference(
            codebook_id=book.codebook_id,
            codebook_version=book.codebook_version,
            content_hash=book.content_hash,
        )
        if (
            book.status is not CodebookStatus.APPROVED
            or codebook_hash(book) != book.content_hash
            or reference != record.codebook
        ):
            raise CodingError("input_changed")
    except CodingError:
        raise CodingError("input_changed") from None
    for classification in stored.classifications:
        try:
            current = resolve_coding_input(
                sources, classification.doc_id, classification.claim_id
            )
        except CodingError as error:
            if (
                classification.status != "refused"
                or str(error) != classification.reason
            ):
                raise CodingError("input_changed") from None
            continue
        if (
            classification.status == "refused"
            or current.input_hash != classification.input_hash
        ):
            raise CodingError("input_changed")
        allowed = {probe.record.target.theme_id for probe in current.probes}
        if not set(classification.theme_ids) <= allowed:
            raise CodingError("invalid_references")
        check_hierarchy(current, classification.theme_ids)
        if classification.status == "completed" and not classification.theme_ids:
            attribute = next(
                row
                for row in stored.attributes
                if (row.doc_id, row.claim_id)
                == (classification.doc_id, classification.claim_id)
            )
            expected = novelty_for(
                current,
                CodingReply(theme_ids=(), attributes=attribute.attributes),
                coding_run_id=record.run_id,
                classification_id=classification.classification_id,
            )
            actual = next(
                row
                for row in stored.novelty
                if row.classification_id == classification.classification_id
            )
            if record_json(expected) != record_json(actual):
                raise CodingError("input_changed")


def reverify_coding_run(
    stored: CodingRun,
    sources: SupportSources,
    support: StoredSupportRun,
    policy: AssignmentPolicy | None,
) -> DecisionSet:
    """Repeat current evidence and the actual pure policy, without model dispatch."""
    stored = _validate(stored, published=None)
    try:
        if type(sources) is not SupportSources or type(support) is not StoredSupportRun:
            raise CodingError("malformed_record")
        reverify_support_run(support, sources)
        record = stored.record
        source = checked(sources.stored_run.record, RunRecord)
        if (
            record.source_run_id != source.run_id
            or record.source_run_hash
            != digest(
                {
                    "record": source.model_dump(mode="json"),
                    "provenance_hash": sources.provenance_hash,
                }
            )
            or record.documents != tuple(sorted(source.documents.items()))
            or record.support_run_id != support.record.run_id
            or record.support_run_hash != support_run_hash(support)
            or record.support_configuration_hash != support.record.configuration_hash
            or record.codebook != support.record.codebook
        ):
            raise CodingError("input_changed")
        _current_inputs(stored, sources)
        try:
            raw_reference = policy.reference if policy is not None else None
        except Exception:  # noqa: BLE001 - match Task 6's external-property contract
            raise CodingError("unexpected_error") from None
        reference = (
            checked(raw_reference, PolicyReference) if policy is not None else None
        )
        if reference != record.policy:
            raise CodingError("policy_mismatch")
        decisions = decide_assignments(_proposals(stored), support, sources, policy)
        rows, links = project_assignments(decisions, support)
        if decisions.policy != record.policy or any(
            _json_rows(actual) != _json_rows(expected)
            for actual, expected in (
                (stored.decisions, decisions.decisions),
                (stored.assignments, rows),
                (stored.assignment_claims, links),
            )
        ):
            raise CodingError("input_changed")
        # External pure-policy properties/evaluation finish before this final gate.
        _current_inputs(stored, sources)
        return decisions
    except CodingError:
        raise
    except SupportError as error:
        raise CodingError(str(error)) from None
    except Exception:  # noqa: BLE001 - never leak source, policy or callback diagnostics
        raise CodingError("input_changed") from None


def _publish(directory: Path, stored: CodingRun) -> Path:
    if directory.exists() or directory.is_symlink():
        raise FileExistsError("coding_destination_exists")
    partial = None
    try:
        directory.parent.mkdir(parents=True, exist_ok=True)
        partial = Path(
            tempfile.mkdtemp(dir=directory.parent, prefix=f".{directory.name}-")
        )
        hashes = dict(stored.record.artifact_hashes)
        for name, (_, schema) in SCHEMAS.items():
            path = partial / f"{name}.parquet"
            pl.DataFrame(
                [row.model_dump(mode="json") for row in getattr(stored, name)],
                schema=schema,
                orient="row",
            ).write_parquet(path)
            hashes[path.name] = sha256_hex(path.read_bytes())
        record = checked(
            stored.record.model_copy(
                update={"artifact_hashes": tuple(sorted(hashes.items()))}
            ),
            CodingRunRecord,
        )
        (partial / "run.json").write_bytes(record_json(record))
        if directory.exists() or directory.is_symlink():
            raise FileExistsError("coding_destination_exists")
        os.rename(partial, directory)
        return directory
    except BaseException:
        if partial is not None:
            shutil.rmtree(partial, ignore_errors=True)
        raise


def write_coding_run(
    directory: Path,
    result: CodingRun,
    sources: SupportSources,
    support: StoredSupportRun,
    policy: AssignmentPolicy | None,
) -> Path:
    """Finish all structural/current-evidence/policy gates before filesystem I/O."""
    try:
        stored = _validate(result, published=False)
        reverify_coding_run(stored, sources, support, policy)
        return _publish(directory, stored)
    except FileExistsError as error:
        if str(error) == "coding_destination_exists":
            raise FileExistsError("coding_destination_exists") from None
        raise CodingError("storage_corrupt") from None
    except Exception:  # noqa: BLE001 - filesystem/Polars/source-bearing errors are fixed
        raise CodingError("storage_corrupt") from None


def read_coding_run(directory: Path) -> CodingRun:
    """Verify exactly nine published files; never open external raw-cache bytes."""
    try:
        _require(not directory.is_symlink())
        manifest = directory / "run.json"
        _require(not manifest.is_symlink())
        record = checked(json.loads(manifest.read_bytes()), CodingRunRecord)
        hashes = dict(record.artifact_hashes)
        tables = {}
        for name, (model, schema) in SCHEMAS.items():
            path = directory / f"{name}.parquet"
            _require(not path.is_symlink())
            payload = path.read_bytes()
            _require(hashes.get(path.name) == sha256_hex(payload))
            frame = pl.read_parquet(io.BytesIO(payload))
            _require(frame.schema == schema)
            tables[name] = tuple(
                checked(row, model) for row in frame.iter_rows(named=True)
            )
        return _validate(CodingRun(record, **tables), published=True)
    except Exception:  # noqa: BLE001 - never print external filesystem/validation text
        raise CodingError("storage_corrupt") from None
