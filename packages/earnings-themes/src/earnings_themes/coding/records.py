"""Closed immutable deductive coding contracts, separate from source evidence."""

import json
import math
from enum import StrEnum
from typing import Any, Literal, Self

from earnings_core import digest
from pydantic import Field, ValidationError, field_validator, model_validator

from earnings_themes.extraction.adapters import Message
from earnings_themes.extraction.records import Parameters
from earnings_themes.records import NonBlank, Part, Sha256Hex
from earnings_themes.support.problems import REASONS as SUPPORT_REASONS
from earnings_themes.support.records import CodebookReference, Target

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


class CodingCeilings(CodingPart):
    requests_per_claim: int = Field(ge=0)
    requests_per_document: int = Field(ge=0)
    requests_per_run: int = Field(ge=0)
    tokens_per_document: int = Field(ge=0)
    tokens_per_run: int = Field(ge=0)


class PolicyReference(CodingPart):
    policy_id: NonBlank
    policy_hash: Sha256Hex
    kind: Literal["fixture", "calibrated"]
    codebook: CodebookReference
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
