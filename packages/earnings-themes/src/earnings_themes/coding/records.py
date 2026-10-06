"""Closed immutable deductive coding contracts, separate from source evidence."""

import json
import math
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal, Self

from earnings_core import digest
from pydantic import (
    AwareDatetime,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from earnings_themes.extraction.adapters import Message
from earnings_themes.extraction.records import Parameters
from earnings_themes.records import NonBlank, Part, Sha256Hex
from earnings_themes.support.problems import REASONS as SUPPORT_REASONS
from earnings_themes.support.records import (
    CodebookReference,
    JudgeIdentity,
    ReviewStatus,
    Target,
)

CODING_SCHEMA_VERSION = 1
CODING_VERSION = "deductive-coding/1"


class CodingProblem(StrEnum):
    MALFORMED_RECORD = "malformed_record"
    MALFORMED_REPLY = "malformed_reply"
    INVALID_REFERENCES = "invalid_references"
    HIERARCHY_CONFLICT = "hierarchy_conflict"
    INPUT_CHANGED = "input_changed"
    INPUT_TOO_LONG = "input_too_long"
    MODEL_MISMATCH = "model_mismatch"
    TOOL_CALL_REFUSED = "tool_call_refused"
    TRANSPORT_ERROR = "transport_error"
    CACHE_CORRUPT = "cache_corrupt"
    REPLAY_MISS = "replay_miss"
    REQUESTS_EXHAUSTED = "requests_exhausted"
    TOKENS_EXHAUSTED = "tokens_exhausted"
    CALIBRATION_REQUIRED = "calibration_required"
    POLICY_MISMATCH = "policy_mismatch"
    POLICY_ACCEPT = "policy_accept"
    POLICY_REJECT = "policy_reject"
    POLICY_REVIEW = "policy_review"
    ASSESSMENT_REFUSED = "assessment_refused"
    ASSESSMENT_INCOMPLETE = "assessment_incomplete"
    ASSESSMENT_FLAGGED = "assessment_flagged"
    MISSING_ASSESSMENT = "missing_assessment"
    INVALID_CONTRIBUTION = "invalid_contribution"
    NO_THEME_FIT = "no_theme_fit"
    MIXED_CODEBOOK = "mixed_codebook"
    FIXTURE_POLICY = "fixture_policy"
    STORAGE_CORRUPT = "storage_corrupt"
    UNEXPECTED_ERROR = "unexpected_error"


REASONS = SUPPORT_REASONS | {problem.value for problem in CodingProblem}


class CodingError(ValueError):
    """A fixed refusal reason; caller-provided text never enters diagnostics."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            reason if type(reason) is str and reason in REASONS else "unexpected_error"
        )


class CodingPart(Part):
    """Strict frozen part with fixed reasons and content-hash-only diagnostics."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}(sha256={digest(self.model_dump(mode='json', warnings=False))})"

    def __str__(self) -> str:
        return self.__repr__()

    @field_validator(
        "schema_version", "max_attempts", "attempt", mode="before", check_fields=False
    )
    @classmethod
    def _integer_literals(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("invalid_integer")
        return value

    @field_validator("reason", mode="before", check_fields=False)
    @classmethod
    def _fixed_reason(cls, value: object) -> object:
        if value is not None and (type(value) is not str or value not in REASONS):
            raise ValueError("invalid_reason")
        return value


class CodingRecord(CodingPart):
    schema_version: Literal[1] = CODING_SCHEMA_VERSION


def checked[M: Part](value: object, model: type[M]) -> M:
    """Reparse JSON mode at untrusted boundaries without input-bearing errors."""
    try:
        if isinstance(value, Part):
            # JSON serialization can turn an invalid bool into int before validation.
            validated = model.model_validate(value.model_dump(warnings=False))
            data = validated.model_dump(mode="json", warnings=False)
        else:
            data = value
        return model.model_validate_json(json.dumps(data, allow_nan=False))
    except (
        ValidationError,
        ValueError,
        TypeError,
        AttributeError,
        OverflowError,
        RecursionError,
    ):
        raise CodingError("malformed_record") from None


class CodingAttributes(CodingPart):
    topic: NonBlank | None = Field(default=None, repr=False)
    sentiment: Literal["positive", "negative", "neutral", "mixed", "unknown"] | None = (
        None
    )
    direction: (
        Literal["increase", "decrease", "unchanged", "mixed", "unknown"] | None
    ) = None
    event_type: NonBlank | None = Field(default=None, repr=False)


class CodingReply(CodingPart):
    theme_ids: tuple[NonBlank, ...]
    attributes: CodingAttributes

    @model_validator(mode="after")
    def _distinct(self) -> Self:
        if len(self.theme_ids) != len(set(self.theme_ids)):
            raise ValueError("duplicate_reference")
        return self


class CodingSubject(CodingPart):
    doc_id: NonBlank
    claim_id: NonBlank
    input_hash: Sha256Hex
    codebook: CodebookReference
    prompt_hash: Sha256Hex
    schema_hash: Sha256Hex
    coding_version: Literal["deductive-coding/1"] = CODING_VERSION
    validator_version: NonBlank


class CodingRequest(CodingPart):
    """Transport data; mutable schema dictionaries require detached boundary checks."""

    messages: tuple[Message, ...] = Field(min_length=2, repr=False)
    reply_schema: dict[str, Any] = Field(repr=False)
    parameters: Parameters
    subject: CodingSubject

    @field_validator("reply_schema", mode="before")
    @classmethod
    def _json_schema(cls, value: object) -> object:
        def json_value(item: object) -> bool:
            if item is None or type(item) in (str, bool, int):
                return True
            if type(item) is float:
                return math.isfinite(item)
            if type(item) is list:
                return all(json_value(part) for part in item)
            if type(item) is dict:
                return all(
                    type(key) is str and json_value(part) for key, part in item.items()
                )
            return False

        if type(value) is not dict or not json_value(value):
            raise ValueError("invalid_json_schema")
        return value


class ProposalRecord(CodingRecord):
    proposal_id: NonBlank
    coding_run_id: NonBlank
    classification_id: NonBlank
    target: Target
    input_hash: Sha256Hex


class AttributeRecord(CodingRecord):
    coding_run_id: NonBlank
    doc_id: NonBlank
    claim_id: NonBlank
    input_hash: Sha256Hex
    attributes: CodingAttributes


class NoveltyItem(CodingRecord):
    novelty_id: NonBlank
    coding_run_id: NonBlank
    classification_id: NonBlank
    source_run_id: NonBlank
    doc_id: NonBlank
    claim_id: NonBlank
    codebook: CodebookReference
    input_hash: Sha256Hex
    original_quote_ids: tuple[NonBlank, ...]
    reason: Literal["no_theme_fit"] = "no_theme_fit"


class CodingPolicy(CodingPart):
    coding_version: Literal["deductive-coding/1"] = CODING_VERSION
    prompt_text: NonBlank = Field(repr=False)
    prompt_hash: Sha256Hex
    parameters: Parameters
    max_attempts: Literal[2] = 2


class CodingPolicySnapshot(CodingPart):
    """Manifest policy binding; source-bearing prompt text stays in the raw cache."""

    coding_version: Literal["deductive-coding/1"] = CODING_VERSION
    prompt_hash: Sha256Hex
    parameters: Parameters
    max_attempts: Literal[2] = 2


class CodingCeilings(CodingPart):
    requests_per_claim: int = Field(ge=0)
    requests_per_document: int = Field(ge=0)
    requests_per_run: int = Field(ge=0)
    tokens_per_document: int = Field(ge=0)
    tokens_per_run: int = Field(ge=0)


class ClassificationRecord(CodingRecord):
    classification_id: NonBlank
    coding_run_id: NonBlank
    doc_id: NonBlank
    claim_id: NonBlank
    input_hash: Sha256Hex
    codebook: CodebookReference
    status: Literal["completed", "refused", "incomplete"]
    reason: str | None
    attempt_ids: tuple[NonBlank, ...]
    theme_ids: tuple[NonBlank, ...]

    @model_validator(mode="after")
    def _outcome(self) -> Self:
        if (self.status == "completed") != (self.reason is None):
            raise ValueError("invalid_classification_reason")
        if len(self.attempt_ids) > 2 or len(set(self.attempt_ids)) != len(
            self.attempt_ids
        ):
            raise ValueError("invalid_attempt_references")
        if tuple(sorted(set(self.theme_ids))) != self.theme_ids:
            raise ValueError("invalid_theme_references")
        if self.status != "completed" and self.theme_ids:
            raise ValueError("invalid_classification_themes")
        if self.status == "refused" and self.attempt_ids:
            raise ValueError("invalid_refused_attempts")
        return self


class CodingAttempt(CodingRecord):
    attempt_id: NonBlank
    classification_id: NonBlank
    doc_id: NonBlank
    claim_id: NonBlank
    attempt: Literal[1, 2]
    request_hash: Sha256Hex
    prompt_hash: Sha256Hex
    schema_hash: Sha256Hex
    input_hash: Sha256Hex
    input_tokens: int = Field(ge=0)
    reserved_tokens: int = Field(ge=0)
    actual_prompt_tokens: int | None = Field(ge=0)
    actual_completion_tokens: int | None = Field(ge=0)
    unreported: bool
    cached: bool
    latency_ms: int = Field(ge=0)
    raw_ref: NonBlank | None
    raw_hash: Sha256Hex | None
    reason: str | None

    @model_validator(mode="after")
    def _raw_accounting(self) -> Self:
        if (self.raw_ref is None) != (self.raw_hash is None):
            raise ValueError("invalid_raw_binding")
        if self.raw_ref is not None and not re.fullmatch(
            r"[0-9a-f]{64}\.json", self.raw_ref
        ):
            raise ValueError("invalid_raw_reference")
        if (self.actual_prompt_tokens is None) != (
            self.actual_completion_tokens is None
        ):
            raise ValueError("invalid_usage_binding")
        if self.cached and (self.raw_ref is None or self.reserved_tokens):
            raise ValueError("invalid_cached_attempt")
        if self.unreported != (
            self.actual_prompt_tokens is None
            and (self.cached or self.reserved_tokens > 0)
        ):
            raise ValueError("invalid_unreported_usage")
        return self


class ProposalRunRecord(CodingRecord):
    run_id: NonBlank
    started_at: AwareDatetime
    source_run_id: NonBlank
    source_run_hash: Sha256Hex
    documents: tuple[tuple[NonBlank, Sha256Hex], ...]
    codebook: CodebookReference
    classifier_identity: JudgeIdentity
    coding_policy: CodingPolicySnapshot
    ceilings: CodingCeilings
    cache_mode: Literal["live", "replay"]
    configuration_hash: Sha256Hex
    requested_claim_order: tuple[tuple[NonBlank, NonBlank], ...]
    schema_hash: Sha256Hex
    coding_version: Literal["deductive-coding/1"] = CODING_VERSION
    validator_version: NonBlank
    software: tuple[tuple[NonBlank, NonBlank], ...] = Field(repr=False)
    counts_by_status: tuple[
        tuple[Literal["completed", "refused", "incomplete"], int], ...
    ]
    counts_by_reason: tuple[tuple[NonBlank, int], ...]
    requests: int = Field(ge=0)
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    reserved_tokens: int = Field(ge=0)
    charged_tokens: int = Field(ge=0)
    unreported: int = Field(ge=0)
    cache_hits: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    billable_cost: Literal["none, self-hosted"]
    artifact_hashes: tuple[tuple[NonBlank, Sha256Hex], ...]

    @model_validator(mode="after")
    def _bindings(self) -> Self:
        if self.started_at.utcoffset().total_seconds() != 0:
            raise ValueError("invalid_utc_time")
        for name in (
            "documents",
            "software",
            "counts_by_status",
            "counts_by_reason",
            "artifact_hashes",
        ):
            values = getattr(self, name)
            keys = [key for key, _ in values]
            if keys != sorted(set(keys)):
                raise ValueError("invalid_sorted_bindings")
        if not re.fullmatch(r"[0-9a-f]{64}", dict(self.software).get("lock_hash", "")):
            raise ValueError("missing_lock_hash")
        if len(set(self.requested_claim_order)) != len(self.requested_claim_order):
            raise ValueError("duplicate_claim_order")
        for name in ("counts_by_status", "counts_by_reason"):
            if any(
                type(count) is not int or count < 0 for _, count in getattr(self, name)
            ):
                raise ValueError("invalid_count")
        if any(reason not in REASONS for reason, _ in self.counts_by_reason):
            raise ValueError("invalid_reason")
        return self


class PolicyReference(CodingPart):
    policy_id: NonBlank
    policy_hash: Sha256Hex
    kind: Literal["fixture", "calibrated"]
    codebook: CodebookReference
    classifier_configuration_hash: Sha256Hex
    support_configuration_hash: Sha256Hex
    calibration_reference: Sha256Hex | None

    @model_validator(mode="after")
    def _calibration_binding(self) -> Self:
        if (self.kind == "calibrated") != (self.calibration_reference is not None):
            raise ValueError("invalid_calibration_binding")
        return self


class PolicyVote(CodingPart):
    action: Literal["accept", "reject", "review"]
    supporting_quote_ids: tuple[NonBlank, ...] = ()

    @model_validator(mode="after")
    def _references(self) -> Self:
        ids = self.supporting_quote_ids
        if len(ids) != len(set(ids)) or ((self.action == "accept") != bool(ids)):
            raise ValueError("invalid_policy_references")
        return self


class AssignmentDecision(CodingRecord):
    """One proposal target's decision, retaining separate assessment provenance."""

    coding_run_id: NonBlank
    decision_id: NonBlank
    doc_id: NonBlank
    claim_id: NonBlank
    theme_id: NonBlank
    codebook: CodebookReference
    target_id: NonBlank
    support_run_hash: Sha256Hex
    support_status: ReviewStatus | None
    flags: tuple[NonBlank, ...]
    missing: tuple[NonBlank, ...]
    status: Literal["accepted", "rejected", "review", "refused"]
    reason: str
    policy: PolicyReference | None
    supporting_quote_ids: tuple[NonBlank, ...]
    proposal_hash: Sha256Hex
    input_hash: Sha256Hex

    @model_validator(mode="after")
    def _decision_binding(self) -> Self:
        expected_id = "decision-" + digest(
            {
                "target_id": self.target_id,
                "proposal_hash": self.proposal_hash,
                "support_run_hash": self.support_run_hash,
                "policy": self.policy.model_dump(mode="json")
                if self.policy is not None
                else None,
            }
        )
        if self.decision_id != expected_id:
            raise ValueError("invalid_decision_id")
        if tuple(sorted(set(self.supporting_quote_ids))) != self.supporting_quote_ids:
            raise ValueError("invalid_quote_references")
        for values in (self.flags, self.missing):
            if tuple(sorted(set(values))) != values:
                raise ValueError("invalid_outcome_references")
        if any(reason not in REASONS for reason in self.missing):
            raise ValueError("invalid_missing_reason")
        expected = {
            "policy_accept": ("accepted", "assessed"),
            "policy_reject": ("rejected", "assessed"),
            "policy_review": ("review", "assessed"),
            "calibration_required": ("review", "assessed"),
            "assessment_refused": ("refused", "refused"),
            "assessment_incomplete": ("review", "incomplete"),
            "assessment_flagged": ("review", "flagged"),
            "missing_assessment": ("review", None),
        }
        if expected.get(self.reason) != (self.status, self.support_status):
            raise ValueError("invalid_decision_reason")
        if (self.status == "accepted") != bool(self.supporting_quote_ids):
            raise ValueError("invalid_accepted_evidence")
        if self.reason.startswith("policy_") and self.policy is None:
            raise ValueError("missing_policy")
        if self.reason == "calibration_required" and self.policy is not None:
            raise ValueError("unexpected_policy")
        if self.support_status == "assessed" and (self.flags or self.missing):
            raise ValueError("invalid_assessed_outcome")
        if self.policy is not None and self.policy.codebook != self.codebook:
            raise ValueError("invalid_policy_codebook")
        return self


class Assignment(CodingRecord):
    """One document-qualified quote–theme row with unchanged evidence pointers."""

    assignment_id: NonBlank
    coding_run_id: NonBlank
    doc_id: NonBlank
    quote_id: NonBlank
    theme_id: NonBlank
    codebook: CodebookReference
    canonical_hash: Sha256Hex
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    validator_version: NonBlank
    mask_ids: tuple[NonBlank, ...]
    support_run_hash: Sha256Hex
    policy_hash: Sha256Hex
    policy_kind: Literal["fixture", "calibrated"]

    @model_validator(mode="after")
    def _evidence(self) -> Self:
        if self.end <= self.start:
            raise ValueError("invalid_span")
        if len(set(self.mask_ids)) != len(self.mask_ids):
            raise ValueError("duplicate_reference")
        return self


class AssignmentClaimLink(CodingRecord):
    assignment_id: NonBlank
    doc_id: NonBlank
    claim_id: NonBlank
    decision_id: NonBlank
    target_id: NonBlank


class CodingRunRecord(ProposalRunRecord):
    """Coding manifest; original proposal identity survives table publication."""

    proposal_hash: Sha256Hex
    support_run_id: NonBlank
    support_run_hash: Sha256Hex
    support_configuration_hash: Sha256Hex
    policy: PolicyReference | None
    counts_by_decision: tuple[
        tuple[Literal["accepted", "rejected", "review", "refused"], int], ...
    ]
    counts_by_decision_reason: tuple[tuple[NonBlank, int], ...]

    @model_validator(mode="after")
    def _decision_counts(self) -> Self:
        for name in ("counts_by_decision", "counts_by_decision_reason"):
            values = getattr(self, name)
            keys = [key for key, _ in values]
            if keys != sorted(set(keys)) or any(
                type(count) is not int or count < 0 for _, count in values
            ):
                raise ValueError("invalid_count")
        if any(reason not in REASONS for reason, _ in self.counts_by_decision_reason):
            raise ValueError("invalid_reason")
        return self


@dataclass(frozen=True, repr=False)
class CodingRun:
    """Eight immutable analytical row tuples and their coding manifest."""

    record: CodingRunRecord
    classifications: tuple[ClassificationRecord, ...]
    attempts: tuple[CodingAttempt, ...]
    proposals: tuple[ProposalRecord, ...]
    attributes: tuple[AttributeRecord, ...]
    decisions: tuple[AssignmentDecision, ...]
    assignments: tuple[Assignment, ...]
    assignment_claims: tuple[AssignmentClaimLink, ...]
    novelty: tuple[NoveltyItem, ...]
