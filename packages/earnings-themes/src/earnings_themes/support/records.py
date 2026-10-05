"""Closed immutable Stage 8 contracts; local JSON retains data, repr only hashes.

Evidence references never duplicate source text. Signals are diagnostic and carry
no assignment acceptance. JSON-mode parsing is the safe untrusted-data boundary.
"""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Annotated, Literal, Self

from earnings_core import canonical_json, digest
from pydantic import (
    AwareDatetime,
    Field,
    NonNegativeInt,
    PositiveInt,
    ValidationError,
    field_validator,
    model_validator,
)

from earnings_themes.anchoring import Bundle
from earnings_themes.codebook import Codebook
from earnings_themes.extraction.records import Parameters
from earnings_themes.extraction.store import StoredRun
from earnings_themes.records import NonBlank, Part, Sha256Hex
from earnings_themes.support.problems import REASONS, SupportError

SUPPORT_SCHEMA_VERSION = 1
SUPPORT_VERSION = "semantic-support/1"
Score = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]


class SafePart(Part):
    """Strict frozen record with no source-bearing printable fields."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}(sha256={digest(self.model_dump(mode='json'))})"

    def __str__(self) -> str:
        return self.__repr__()

    @field_validator(
        "schema_version", "attempt", "max_attempts", mode="before", check_fields=False
    )
    @classmethod
    def _strict_integer_literals(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("invalid_integer")
        return value

    @field_validator("score", "joint_support_score", mode="before", check_fields=False)
    @classmethod
    def _strict_scores(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("invalid_score")  # noqa: TRY004 - Pydantic collects ValueError
        return value

    @model_validator(mode="after")
    def _distinct_references_and_fixed_reasons(self) -> Self:
        for name in (
            "mask_ids",
            "original_quote_ids",
            "evidence_ids",
            "attempt_ids",
            "signal_ids",
            "trial_ids",
            "flags",
            "missing",
            "reason_codes",
        ):
            values = getattr(self, name, ())
            if len(values) != len(set(values)):
                raise ValueError("duplicate_reference")
        for name in ("reason", "problem"):
            value = getattr(self, name, None)
            if value is not None and value not in REASONS:
                raise ValueError("invalid_reason")
        if any(value not in REASONS for value in getattr(self, "missing", ())):
            raise ValueError("invalid_reason")
        return self


class SupportRecord(SafePart):
    schema_version: Literal[1] = SUPPORT_SCHEMA_VERSION


def parse_support[M: SafePart](data: object, model: type[M]) -> M:
    """Revalidate JSON mode and suppress source-bearing validation diagnostics."""
    try:
        return model.model_validate_json(canonical_json(data))
    except (ValidationError, ValueError, TypeError, OverflowError):
        raise SupportError("malformed_record") from None


class CodebookReference(SafePart):
    codebook_id: NonBlank
    codebook_version: NonNegativeInt
    content_hash: Sha256Hex


class Target(SafePart):
    source_run_id: NonBlank
    doc_id: NonBlank
    claim_id: NonBlank
    theme_id: NonBlank
    codebook: CodebookReference


class ThemeSnapshot(SafePart):
    codebook: CodebookReference
    theme_id: NonBlank
    label: NonBlank = Field(repr=False)
    definition: NonBlank = Field(repr=False)
    parent_id: str | None
    inclusion_rules: tuple[NonBlank, ...] = Field(repr=False)
    exclusion_rules: tuple[NonBlank, ...] = Field(repr=False)


class EvidenceReference(SupportRecord):
    target_id: NonBlank
    quote_id: NonBlank
    doc_id: NonBlank
    canonical_hash: Sha256Hex
    element_id: NonBlank
    start: NonNegativeInt
    end: NonNegativeInt
    text_hash: Sha256Hex
    validator_version: NonBlank
    mask_ids: tuple[NonBlank, ...]

    @model_validator(mode="after")
    def _nonempty_span(self) -> Self:
        if self.start >= self.end:
            raise ValueError("invalid_span")
        return self


class ContextReference(SupportRecord):
    target_id: NonBlank
    doc_id: NonBlank
    canonical_hash: Sha256Hex
    element_id: NonBlank
    start: NonNegativeInt
    end: NonNegativeInt
    text_hash: Sha256Hex
    kind: Literal["block", "heading"]

    @model_validator(mode="after")
    def _nonempty_span(self) -> Self:
        if self.start >= self.end:
            raise ValueError("invalid_span")
        return self


class TargetRecord(SupportRecord):
    target_id: NonBlank
    target: Target
    source_run_hash: Sha256Hex
    claim_hash: Sha256Hex
    input_hash: Sha256Hex
    original_quote_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    theme: ThemeSnapshot | None


class FileHash(SafePart):
    relative_path: NonBlank = Field(repr=False)
    sha256: Sha256Hex

    @model_validator(mode="after")
    def _confined_path(self) -> Self:
        path = self.relative_path
        if (
            PurePosixPath(path).is_absolute()
            or "\\" in path
            or ":" in path
            or path.startswith("~")
            or any(part in ("", ".", "..") for part in path.split("/"))
        ):
            raise ValueError("invalid_model_path")
        return self


class RuntimeIdentity(SafePart):
    model_id: NonBlank = Field(repr=False)
    revision: NonBlank
    files: tuple[FileHash, ...]
    runtime: NonBlank
    runtime_version: NonBlank
    device: NonBlank
    precision: NonBlank
    encoding_version: NonBlank

    @model_validator(mode="after")
    def _unique_files(self) -> Self:
        paths = [file.relative_path for file in self.files]
        if len(paths) != len(set(paths)):
            raise ValueError("duplicate_model_file")
        return self


class WeightLicense(SafePart):
    source_url: NonBlank = Field(repr=False)
    terms_reference: NonBlank = Field(repr=False)
    intended_use: NonBlank = Field(repr=False)
    verified_on: date
    permits_use: Literal[True]

    @field_validator("permits_use", mode="before")
    @classmethod
    def _strict_permission(cls, value: object) -> object:
        if type(value) is not bool:
            raise ValueError("invalid_permission")
        return value


class ScorerIdentity(SafePart):
    kind: Literal["scripted", "minicheck", "deberta"]
    runtime: RuntimeIdentity
    input_limit: PositiveInt


class JudgeIdentity(SafePart):
    family: NonBlank
    runtime: RuntimeIdentity
    input_limit: PositiveInt
    output_limit: PositiveInt
    hosting: Literal["scripted", "local"]
    weight_license: WeightLicense | None

    @model_validator(mode="after")
    def _licensed_local_weights(self) -> Self:
        if self.hosting == "local" and self.weight_license is None:
            raise ValueError("missing_weight_license")
        return self


class SignalStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class Presentation(StrEnum):
    EVIDENCE_FIRST = "evidence_first"
    CLAIM_THEME_FIRST = "claim_theme_first"


class ReviewStatus(StrEnum):
    REFUSED = "refused"
    INCOMPLETE = "incomplete"
    FLAGGED = "flagged"
    ASSESSED = "assessed"


class ReasonCode(StrEnum):
    WRONG_ATTRIBUTION = "wrong_attribution"
    WRONG_PERIOD = "wrong_period"
    NEGATION = "negation"
    SCOPE_MISMATCH = "scope_mismatch"
    PARTIAL_SUPPORT = "partial_support"
    THEME_MISMATCH = "theme_mismatch"
    EXCLUSION_CONFLICT = "exclusion_conflict"
    CONTEXT_ONLY_SUPPORT = "context_only_support"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    COMPOUND_CLAIM = "compound_claim"


class EntailmentSignal(SupportRecord):
    signal_id: NonBlank
    target_id: NonBlank
    scope: Literal["quote", "joint"]
    quote_id: str | None
    evaluation_id: NonBlank
    identity: ScorerIdentity
    input_hash: Sha256Hex
    status: SignalStatus
    score: Score | None
    reason: str | None
    input_tokens: NonNegativeInt | None
    latency_ms: NonNegativeInt
    cached: bool

    @model_validator(mode="after")
    def _availability_and_scope(self) -> Self:
        available = self.status == SignalStatus.AVAILABLE
        if available != (self.score is not None) or available != (self.reason is None):
            raise ValueError("invalid_availability")
        if (self.scope == "quote") != (self.quote_id is not None):
            raise ValueError("invalid_scope")
        return self


class QuoteAssessment(SafePart):
    quote_id: NonBlank
    contribution: Literal[
        "supporting", "contextual", "irrelevant", "contradicting", "uncertain"
    ]


class JudgeAnswer(SafePart):
    claim_support: Literal["supported", "unsupported", "uncertain"]
    theme_fit: Literal["fits", "does_not_fit", "uncertain"]
    joint_support_score: Score
    quote_assessments: tuple[QuoteAssessment, ...]
    reason_codes: tuple[ReasonCode, ...]
    summary: Annotated[NonBlank, Field(max_length=500, repr=False)]

    @model_validator(mode="after")
    def _distinct_quote_assessments(self) -> Self:
        ids = [assessment.quote_id for assessment in self.quote_assessments]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate_quote")
        return self


class JudgeAttempt(SupportRecord):
    attempt_id: NonBlank
    trial_id: NonBlank
    attempt: Literal[1, 2]
    request_hash: Sha256Hex
    prompt_hash: Sha256Hex
    schema_hash: Sha256Hex
    input_tokens: NonNegativeInt
    reserved_tokens: NonNegativeInt
    actual_prompt_tokens: NonNegativeInt | None
    actual_completion_tokens: NonNegativeInt | None
    latency_ms: NonNegativeInt
    cached: bool
    raw_ref: str | None = Field(repr=False)
    problem: str | None
    answer: JudgeAnswer | None


class JudgeTrial(SupportRecord):
    trial_id: NonBlank
    target_id: NonBlank
    identity: JudgeIdentity
    presentation: Presentation
    attempt_ids: tuple[NonBlank, ...]
    status: SignalStatus
    answer: JudgeAnswer | None
    reason: str | None

    @model_validator(mode="after")
    def _availability(self) -> Self:
        available = self.status == SignalStatus.AVAILABLE
        if available != (self.answer is not None) or available != (self.reason is None):
            raise ValueError("invalid_availability")
        return self


class ReviewOutcome(SupportRecord):
    target_id: NonBlank
    status: ReviewStatus
    flags: tuple[NonBlank, ...]
    missing: tuple[NonBlank, ...]
    signal_ids: tuple[NonBlank, ...]
    trial_ids: tuple[NonBlank, ...]


class SupportCeilings(SafePart):
    scorer_per_target: NonNegativeInt
    scorer_per_document: NonNegativeInt
    scorer_per_run: NonNegativeInt
    judge_per_target: NonNegativeInt
    judge_per_document: NonNegativeInt
    judge_per_run: NonNegativeInt
    tokens_per_document: NonNegativeInt
    tokens_per_run: NonNegativeInt


class UsageRecord(SupportRecord):
    target_id: NonBlank
    doc_id: NonBlank
    operation_id: NonBlank
    kind: Literal["scorer", "judge"]
    reserved_tokens: NonNegativeInt
    actual_prompt_tokens: NonNegativeInt | None
    actual_completion_tokens: NonNegativeInt | None
    unreported: bool
    cached: bool
    latency_ms: NonNegativeInt


class SupportPolicy(SafePart):
    support_version: Literal["semantic-support/1"]
    prompt_text: NonBlank = Field(repr=False)
    prompt_hash: Sha256Hex
    parameters: Parameters
    max_attempts: Literal[2] = 2


class SupportRunRecord(SupportRecord):
    run_id: NonBlank
    started_at: AwareDatetime
    source_run_id: NonBlank
    source_run_hash: Sha256Hex
    documents: tuple[tuple[NonBlank, Sha256Hex], ...]
    codebook: CodebookReference
    configuration_hash: Sha256Hex
    extractor_family: NonBlank
    scorer_identity: ScorerIdentity
    judge_identities: tuple[JudgeIdentity, JudgeIdentity]
    support_version: Literal["semantic-support/1"]
    validator_version: NonBlank
    software: tuple[tuple[NonBlank, NonBlank], ...] = Field(repr=False)
    ceilings: SupportCeilings
    counts_by_status: tuple[tuple[ReviewStatus, NonNegativeInt], ...]
    counts_by_reason: tuple[tuple[NonBlank, NonNegativeInt], ...]
    evaluations: NonNegativeInt
    requests: NonNegativeInt
    prompt_tokens: NonNegativeInt
    completion_tokens: NonNegativeInt
    reserved_tokens: NonNegativeInt
    unreported: NonNegativeInt
    cache_hits: NonNegativeInt
    billable_cost: Literal["none, self-hosted"]
    artifact_hashes: tuple[tuple[NonBlank, Sha256Hex], ...]

    @model_validator(mode="after")
    def _run_bindings(self) -> Self:
        if self.started_at.utcoffset().total_seconds() != 0:
            raise ValueError("invalid_utc_time")
        for name in (
            "documents",
            "software",
            "artifact_hashes",
            "counts_by_status",
            "counts_by_reason",
        ):
            values = getattr(self, name)
            keys = [key for key, _ in values]
            if keys != sorted(set(keys)):
                raise ValueError("invalid_sorted_bindings")
        software = dict(self.software)
        if (
            "lock_hash" not in software
            or len(software["lock_hash"]) != 64
            or any(c not in "0123456789abcdef" for c in software["lock_hash"])
        ):
            raise ValueError("missing_lock_hash")
        if any(
            reason not in REASONS | {code.value for code in ReasonCode}
            for reason, _ in self.counts_by_reason
        ):
            raise ValueError("invalid_reason")
        return self


@dataclass(frozen=True, repr=False)
class SupportSources:
    stored_run: StoredRun
    bundles: tuple[Bundle, ...]
    codebook: Codebook
    provenance_hash: str


@dataclass(frozen=True, repr=False)
class ResolvedInput:
    record: TargetRecord
    evidence: tuple[EvidenceReference, ...]
    contexts: tuple[ContextReference, ...]
    claim: str
    sources: SupportSources


@dataclass(frozen=True, repr=False)
class RefusedTarget:
    record: TargetRecord
    outcome: ReviewOutcome


@dataclass(frozen=True, repr=False)
class AssessmentResult:
    target: TargetRecord
    evidence: tuple[EvidenceReference, ...]
    contexts: tuple[ContextReference, ...]
    entailment: tuple[EntailmentSignal, ...]
    trials: tuple[JudgeTrial, ...]
    attempts: tuple[JudgeAttempt, ...]
    usage: tuple[UsageRecord, ...]
    outcome: ReviewOutcome


@dataclass(frozen=True, repr=False)
class SupportRunResult:
    record: SupportRunRecord
    assessments: tuple[AssessmentResult, ...]


@dataclass(frozen=True, repr=False)
class StoredSupportRun:
    record: SupportRunRecord
    targets: tuple[TargetRecord, ...]
    evidence: tuple[EvidenceReference, ...]
    contexts: tuple[ContextReference, ...]
    entailment: tuple[EntailmentSignal, ...]
    trials: tuple[JudgeTrial, ...]
    attempts: tuple[JudgeAttempt, ...]
    usage: tuple[UsageRecord, ...]
    outcomes: tuple[ReviewOutcome, ...]
