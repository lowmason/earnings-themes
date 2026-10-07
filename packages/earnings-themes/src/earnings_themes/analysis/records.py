"""Strict schema-1 analytical contracts and explicit persisted table schemas.

These contracts establish structural bindings only. Current evidence, masks,
policies, cache bytes and rights must be rebound at consumption/publication.
No constructor performs I/O or loads an adapter.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from types import MappingProxyType
from typing import TYPE_CHECKING, Annotated, Literal, Self
from urllib.parse import urlsplit

import polars as pl
from earnings_core import ArtifactRef, RightsStatus, canonical_json, digest
from pydantic import (
    AwareDatetime,
    Field,
    StringConstraints,
    ValidationError,
    field_validator,
    model_validator,
)

from earnings_themes.codebook import Codebook
from earnings_themes.coding.records import (
    AssignmentClaimLink,
    CodingRun,
    NoveltyItem,
    PolicyReference,
)
from earnings_themes.records import NonBlank, Part, Sha256Hex
from earnings_themes.support.records import (
    CodebookReference,
    FileHash,
    StoredSupportRun,
    SupportSources,
)

from .problems import ANALYSIS_REASONS, AnalysisError

if TYPE_CHECKING:
    from earnings_themes.coding.cache import CodingCache
    from earnings_themes.coding.decide import AssignmentPolicy, DecisionSet
    from earnings_themes.support.cache import SupportCache

ANALYSIS_SCHEMA_VERSION = 1
Cik = Annotated[str, StringConstraints(pattern=r"^[0-9]{10}$")]
Count = Annotated[int, Field(ge=0)]
Scope = Literal["fixture", "research"]
Audience = Literal["local", "export"]
DocType = Literal["release", "transcript"]
State = Literal[
    "expected",
    "acquired",
    "parsed",
    "failed",
    "unavailable",
    "restricted",
    "partial",
    "completed",
    "completed-no-theme",
]
EligibilityReason = Literal[
    "period_end_outside_window",
    "no_release_filing",
    "several_release_filings",
    "published_after_cutoff",
    "member_at_publication",
    "not_member_at_publication",
    "same_day_transition",
]


class AnalysisPart(Part):
    """Frozen closed record; all printable values are replaced by one digest."""

    schema_version: Literal[1] = 1

    def __repr__(self) -> str:
        return f"{type(self).__name__}(sha256={digest(self.model_dump(mode='json', warnings=False))})"

    def __str__(self) -> str:
        return self.__repr__()

    @field_validator(
        "schema_version", "fiscal_quarter", mode="before", check_fields=False
    )
    @classmethod
    def _integer_literals(cls, value: object) -> object:
        if value is not None and type(value) is not int:
            raise ValueError("invalid_integer")
        return value

    @model_validator(mode="after")
    def _common_invariants(self) -> Self:
        for name in type(self).model_fields:
            value = getattr(self, name)
            if isinstance(value, datetime) and value.utcoffset().total_seconds() != 0:
                raise ValueError("invalid_utc_time")
            if (
                name in ("reason", "missing_reason", "failure_reason")
                and value is not None
                and value not in ANALYSIS_REASONS
            ):
                raise ValueError("invalid_reason")
            if name in (
                "reasons",
                "missing_reasons",
                "restrictions",
                "missing",
            ) and any(reason not in ANALYSIS_REASONS for reason in value):
                raise ValueError("invalid_reason")
            if name in (
                "mask_ids",
                "original_quote_ids",
                "supported_quote_ids",
                "proposed_theme_ids",
                "event_ids",
                "doc_ids",
            ) and len(value) != len(set(value)):
                raise ValueError("duplicate_reference")
        if hasattr(self, "start") and not 0 <= self.start < self.end:
            raise ValueError("invalid_span")
        return self


class ExpectedEvent(AnalysisPart):
    event_id: NonBlank
    entity_id: NonBlank
    cik: Cik
    period_end: date
    fiscal_year: Count | None
    fiscal_quarter: Literal[1, 2, 3, 4] | None
    eligibility_status: Literal["eligible", "ineligible", "ambiguous"]
    eligibility_reason: EligibilityReason
    membership_assertion_id: NonBlank
    event_manifest_hash: Sha256Hex
    pilot_hash: Sha256Hex

    @model_validator(mode="after")
    def _eligibility(self) -> Self:
        expected = {
            "member_at_publication": "eligible",
            "no_release_filing": "ambiguous",
            "several_release_filings": "ambiguous",
            "same_day_transition": "ambiguous",
        }.get(self.eligibility_reason, "ineligible")
        if self.eligibility_status != expected:
            raise ValueError("invalid_eligibility")
        return self


class AcquisitionStatus(AnalysisPart):
    event_id: NonBlank
    document_id: NonBlank
    state: State
    missing_reason: str | None
    failure_reason: (
        Literal[
            "unsupported_media_type",
            "parse_failed",
            "no_native_text",
            "invalid_elements",
        ]
        | None
    )
    doc_id: NonBlank | None
    source_document_id: NonBlank | None
    raw_hash: Sha256Hex | None
    accession: NonBlank | None
    exhibit: NonBlank | None
    retrieved_at: AwareDatetime | None
    state_run_id: NonBlank
    state_schema_version: Annotated[int, Field(ge=1, le=2)]
    pilot_hash: Sha256Hex

    @model_validator(mode="after")
    def _state(self) -> Self:
        allowed = {
            "expected": {"not_yet_checked"},
            "unavailable": {"not_found", "no_confirmed_release"},
            "restricted": {"rights_restricted"},
            "failed": {"parse_failed", "processing_failed"},
        }
        if self.missing_reason not in allowed.get(self.state, {None}):
            raise ValueError("invalid_state_reason")
        if (self.missing_reason == "parse_failed") != (self.failure_reason is not None):
            raise ValueError("invalid_failure_reason")
        if (
            self.state in ("parsed", "partial", "completed", "completed-no-theme")
            and self.doc_id is None
        ):
            raise ValueError("missing_document")
        return self


class DocumentMetadata(AnalysisPart):
    doc_id: NonBlank
    event_id: NonBlank
    entity_id: NonBlank
    cik: Cik
    doc_type: Literal["release"] = "release"
    publisher: NonBlank = Field(repr=False)
    source_url: NonBlank = Field(repr=False)
    source_document_id: NonBlank
    raw_artifact: ArtifactRef | None = Field(repr=False)
    raw_hash: Sha256Hex
    canonical_hash: Sha256Hex
    canonicalization_version: NonBlank
    parser_version: NonBlank
    canonical_manifest_hash: Sha256Hex
    mask_policy_id: NonBlank
    mask_policy_version: NonBlank
    mask_manifest_hash: Sha256Hex
    filing_at: AwareDatetime | None
    published_at: AwareDatetime | None
    event_at: AwareDatetime | None
    retrieved_at: AwareDatetime
    period_end: date
    fiscal_year: Count | None
    fiscal_quarter: Literal[1, 2, 3, 4] | None
    rights_status: RightsStatus
    rights_basis: NonBlank = Field(repr=False)
    access_status: Literal["available", "unavailable", "restricted"]
    retain_text: bool
    export_text: bool
    retain_raw: bool
    export_raw: bool
    retain_capture: bool

    @model_validator(mode="after")
    def _rights_and_url(self) -> Self:
        url = urlsplit(self.source_url)
        if (
            url.scheme not in ("http", "https")
            or not url.hostname
            or url.username
            or url.password
            or any(c.isspace() for c in self.source_url)
        ):
            raise ValueError("invalid_source_url")
        if (
            self.export_text
            and not self.retain_text
            or self.export_raw
            and not self.retain_raw
        ):
            raise ValueError("invalid_permission")
        if self.rights_status != RightsStatus.REDISTRIBUTABLE and (
            self.export_text or self.export_raw
        ):
            raise ValueError("rights_restricted")
        if (
            self.rights_status == RightsStatus.RESTRICTED
            or self.access_status == "restricted"
        ) and any(
            (
                self.retain_text,
                self.export_text,
                self.retain_raw,
                self.export_raw,
                self.retain_capture,
            )
        ):
            raise ValueError("rights_restricted")
        if self.raw_artifact is not None and (
            self.raw_artifact.content_sha256 != self.raw_hash
            or self.raw_artifact.rights_status != self.rights_status
            or self.raw_artifact.rights_basis != self.rights_basis
            or not self.retain_raw
        ):
            raise ValueError("invalid_raw_binding")
        return self


class CopyAssertion(AnalysisPart):
    copy_id: NonBlank
    event_id: NonBlank
    doc_ids: tuple[NonBlank, ...] = Field(min_length=2)
    documents: tuple[tuple[NonBlank, Sha256Hex], ...]
    method: Literal["same_event_exact_hash", "reviewed_copy"]
    evidence_ref: NonBlank = Field(repr=False)
    rule_version: NonBlank
    actor_id: NonBlank | None
    reviewed_at: AwareDatetime | None

    @model_validator(mode="after")
    def _copy(self) -> Self:
        if (
            tuple(sorted(self.doc_ids)) != self.doc_ids
            or tuple(key for key, _ in self.documents) != self.doc_ids
        ):
            raise ValueError("invalid_copy_bindings")
        if (
            self.method == "same_event_exact_hash"
            and len({h for _, h in self.documents}) != 1
        ):
            raise ValueError("invalid_copy_hash")
        if (self.method == "reviewed_copy") != (
            self.actor_id is not None and self.reviewed_at is not None
        ):
            raise ValueError("invalid_review_binding")
        if self.method == "same_event_exact_hash" and (
            self.actor_id is not None or self.reviewed_at is not None
        ):
            raise ValueError("invalid_review_binding")
        return self


class AnalysisPolicy(AnalysisPart):
    policy_id: Literal["coverage-analysis"] = "coverage-analysis"
    version: Literal["1"] = "1"
    population_id: NonBlank
    event_ids: tuple[NonBlank, ...] = Field(min_length=1)
    population_hash: Sha256Hex
    doc_types: tuple[Literal["release"]] = ("release",)
    speaker_roles: tuple[Literal["not_applicable"]] = ("not_applicable",)
    mask_policy_id: NonBlank
    mask_policy_version: NonBlank
    dedup_rule: Literal["same-event-disclosure/1"] = "same-event-disclosure/1"
    parent_rule: Literal["self-or-descendant/1"] = "self-or-descendant/1"
    headline_unit: Literal["issuer_period"] = "issuer_period"
    window_issuer_rule: Literal["any-complete-period/1"] = "any-complete-period/1"
    include_family_view: bool
    scope: Scope

    @field_validator("version", mode="before")
    @classmethod
    def _string_version(cls, value: object) -> object:
        if type(value) is not str:
            raise ValueError("invalid_version")
        return value

    @model_validator(mode="after")
    def _sorted_events(self) -> Self:
        if tuple(sorted(self.event_ids)) != self.event_ids:
            raise ValueError("invalid_event_order")
        return self

    @property
    def content_hash(self) -> str:
        return digest(self.model_dump(mode="json"))


def family_map_hash(value: ThemeFamilyMap | dict) -> str:
    material = value.model_dump(mode="json") if isinstance(value, Part) else dict(value)
    material.pop("content_hash", None)
    return digest(material)


class ThemeFamilyMap(AnalysisPart):
    mapping_id: NonBlank
    version: Annotated[int, Field(gt=0)]
    content_hash: Sha256Hex
    codebook: CodebookReference
    memberships: tuple[tuple[NonBlank, NonBlank], ...]
    family_labels: tuple[tuple[NonBlank, NonBlank], ...] = Field(repr=False)

    @model_validator(mode="after")
    def _mapping(self) -> Self:
        if tuple(sorted(set(self.memberships))) != self.memberships:
            raise ValueError("invalid_memberships")
        keys = tuple(key for key, _ in self.family_labels)
        if keys != tuple(sorted(set(keys))) or any(
            family not in keys for _, family in self.memberships
        ):
            raise ValueError("invalid_family_labels")
        if self.content_hash != family_map_hash(self):
            raise ValueError("invalid_mapping_hash")
        return self

    def validate_codebook(self, book: Codebook) -> None:
        reference = CodebookReference(
            codebook_id=book.codebook_id,
            codebook_version=book.codebook_version,
            content_hash=book.content_hash,
        )
        if self.codebook != reference:
            raise AnalysisError("mixed_codebook")
        if any(theme not in book.theme_ids() for theme, _ in self.memberships):
            raise AnalysisError("invalid_references")


class NoThemeDeclaration(AnalysisPart):
    doc_id: NonBlank
    canonical_hash: Sha256Hex
    source_run_hash: Sha256Hex
    coding_run_hash: Sha256Hex
    support_run_hash: Sha256Hex
    codebook: CodebookReference
    analysis_policy_hash: Sha256Hex
    assignment_policy: PolicyReference
    actor_id: NonBlank
    declared_at: AwareDatetime
    finding: Literal["no_theme"] = "no_theme"
    policy_scope: Scope

    @model_validator(mode="after")
    def _binding(self) -> Self:
        if self.assignment_policy.codebook != self.codebook:
            raise ValueError("mixed_codebook")
        if self.assignment_policy.kind == "fixture" and self.policy_scope != "fixture":
            raise ValueError("fixture_policy")
        return self


class DocumentCompletion(AnalysisPart):
    doc_id: NonBlank
    event_id: NonBlank
    canonical_hash: Sha256Hex
    source_run_hash: Sha256Hex
    coding_run_hash: Sha256Hex
    support_run_hash: Sha256Hex
    codebook: CodebookReference
    assignment_policy: PolicyReference | None
    analysis_policy_hash: Sha256Hex
    traversal_complete: bool
    classification_complete: bool
    assessment_complete: bool
    decision_complete: bool
    eligible_units: Count
    completed_windows: Count
    failed_windows: Count
    accepted_count: Count
    masked_count: Count
    rejected_count: Count
    review_count: Count
    refused_count: Count
    flagged_count: Count
    incomplete_count: Count
    unmatched_count: Count
    processing_state: State
    reasons: tuple[NonBlank, ...]
    declaration_hash: Sha256Hex | None
    observable: bool
    policy_scope: Scope

    @model_validator(mode="after")
    def _completion(self) -> Self:
        if self.assignment_policy is not None:
            if self.assignment_policy.codebook != self.codebook:
                raise ValueError("mixed_codebook")
            if (
                self.assignment_policy.kind == "fixture"
                and self.policy_scope != "fixture"
            ):
                raise ValueError("fixture_policy")
        complete = (
            all(
                (
                    self.traversal_complete,
                    self.classification_complete,
                    self.assessment_complete,
                    self.decision_complete,
                )
            )
            and self.eligible_units > 0
            and self.failed_windows == 0
        )
        if self.masked_count > self.accepted_count:
            raise ValueError("invalid_masked_count")
        if self.observable:
            if (
                not complete
                or self.assignment_policy is None
                or any(
                    (
                        self.review_count,
                        self.refused_count,
                        self.flagged_count,
                        self.incomplete_count,
                        self.unmatched_count,
                    )
                )
            ):
                raise ValueError("invalid_observable")
            if self.processing_state == "completed-no-theme":
                if (
                    self.declaration_hash is None
                    or self.accepted_count
                    or "explicit_no_theme" not in self.reasons
                ):
                    raise ValueError("invalid_declaration")
            elif self.processing_state != "completed" or not self.accepted_count:
                raise ValueError("invalid_completed")
        if self.processing_state == "completed-no-theme" and (
            not self.observable or self.declaration_hash is None
        ):
            raise ValueError("invalid_declaration")
        return self


class EvidenceViewReference(AnalysisPart):
    evidence_id: NonBlank
    doc_id: NonBlank
    quote_id: NonBlank
    canonical_hash: Sha256Hex
    start: Count
    end: Count
    validator_version: NonBlank
    element_id: NonBlank
    mask_ids: tuple[NonBlank, ...]
    locator_hash: Sha256Hex
    quote_text_hash: Sha256Hex
    source_fragment_url: NonBlank | None = Field(repr=False)
    source_url: NonBlank | None = Field(repr=False)
    raw_artifact: ArtifactRef | None = Field(repr=False)
    canonical_artifact: ArtifactRef | None = Field(repr=False)
    view_artifact: ArtifactRef | None = Field(repr=False)
    anchor_id: NonBlank
    audience: Audience
    rights_status: RightsStatus
    rights_basis: NonBlank = Field(repr=False)
    status: Literal["available", "withheld"]
    reason: str | None
    capture_reference: Sha256Hex | None = None

    @model_validator(mode="after")
    def _view_rights(self) -> Self:
        if (self.status == "available") != (self.reason is None):
            raise ValueError("invalid_view_status")
        private = (
            self.source_fragment_url,
            self.raw_artifact,
            self.canonical_artifact,
            self.view_artifact,
        )
        if self.status == "withheld" and any(item is not None for item in private):
            raise ValueError("rights_restricted")
        if (
            self.audience == "export"
            and self.rights_status != RightsStatus.REDISTRIBUTABLE
            and (
                self.status == "available" or any(item is not None for item in private)
            )
        ):
            raise ValueError("rights_restricted")
        for artifact in (
            self.raw_artifact,
            self.canonical_artifact,
            self.view_artifact,
        ):
            if artifact is not None and (
                artifact.rights_status != self.rights_status
                or artifact.rights_basis != self.rights_basis
            ):
                raise ValueError("rights_restricted")
        return self


class CaptureObservation(AnalysisPart):
    evidence_id: NonBlank
    doc_id: NonBlank
    quote_id: NonBlank
    canonical_hash: Sha256Hex
    start: Count
    end: Count
    utf16_start: Count
    utf16_end: Count
    capture_id: NonBlank | None
    capture_artifact: ArtifactRef | None = Field(repr=False)
    policy_hash: Sha256Hex | None
    environment_hash: Sha256Hex | None
    status: Literal["completed", "partial", "failed", "unavailable", "not_requested"]
    reason: str | None
    screenshots_rights: Literal["local_only"] = "local_only"

    @model_validator(mode="after")
    def _capture(self) -> Self:
        if (
            self.utf16_end <= self.utf16_start
            or self.utf16_start < self.start
            or self.utf16_end < self.end
        ):
            raise ValueError("invalid_browser_span")
        if (
            self.capture_artifact is not None
            and self.capture_artifact.rights_status != RightsStatus.LOCAL_ONLY
        ):
            raise ValueError("rights_restricted")
        if self.status == "completed" and (
            self.capture_id is None
            or self.capture_artifact is None
            or self.policy_hash is None
            or self.environment_hash is None
            or self.reason is not None
        ):
            raise ValueError("invalid_capture_binding")
        return self


class RawCacheVerification(AnalysisPart):
    stage: Literal["extraction", "classifier", "scorer", "judge"]
    status: Literal["verified", "not_supplied", "not_bound"]
    bindings: tuple[FileHash, ...]
    method: NonBlank
    version: NonBlank

    @model_validator(mode="after")
    def _cache(self) -> Self:
        keys = tuple(binding.relative_path for binding in self.bindings)
        if keys != tuple(sorted(set(keys))):
            raise ValueError("invalid_cache_bindings")
        if self.status != "verified" and self.bindings:
            raise ValueError("invalid_cache_status")
        if self.stage == "extraction" and self.status != "not_bound":
            raise ValueError("invalid_extraction_cache_status")
        return self


class QuoteAudit(AnalysisPart):
    doc_id: NonBlank
    quote_id: NonBlank
    canonical_hash: Sha256Hex
    start: Count
    end: Count
    element_id: NonBlank
    validator_version: NonBlank
    mask_ids: tuple[NonBlank, ...]
    source_run_id: NonBlank
    source_run_hash: Sha256Hex
    metadata_ref: Sha256Hex
    quote_text: str | None = Field(repr=False)


class Observation(QuoteAudit):
    event_id: NonBlank
    entity_id: NonBlank
    cik: Cik
    period_end: date
    fiscal_year: Count | None
    fiscal_quarter: Literal[1, 2, 3, 4] | None
    doc_type: Literal["release"] = "release"
    speaker_role: Literal["not_applicable"] = "not_applicable"
    theme_id: NonBlank
    assignment_id: NonBlank
    codebook_id: NonBlank
    codebook_version: Count
    codebook_hash: Sha256Hex
    headline_eligible: bool
    disclosure_group: NonBlank
    policy_kind: Literal["fixture", "calibrated"]
    policy_hash: Sha256Hex
    policy_scope: Scope
    coding_run_id: NonBlank
    coding_run_hash: Sha256Hex
    support_run_id: NonBlank
    support_run_hash: Sha256Hex
    evidence_id: NonBlank
    published_at: AwareDatetime | None
    retrieved_at: AwareDatetime
    extracted_at: AwareDatetime

    @model_validator(mode="after")
    def _observation(self) -> Self:
        if self.policy_kind == "fixture" and self.policy_scope != "fixture":
            raise ValueError("fixture_policy")
        if self.headline_eligible and self.mask_ids:
            raise ValueError("masked_headline")
        return self


class ClaimAudit(AnalysisPart):
    doc_id: NonBlank
    claim_id: NonBlank
    window_id: NonBlank
    attempt_id: NonBlank
    interpretation_hash: Sha256Hex
    interpretation: str | None = Field(repr=False)
    original_quote_ids: tuple[NonBlank, ...]
    source_run_id: NonBlank
    source_run_hash: Sha256Hex


class ClaimEvidence(AnalysisPart):
    doc_id: NonBlank
    claim_id: NonBlank
    quote_id: NonBlank


class ClassificationAudit(AnalysisPart):
    classification_id: NonBlank
    coding_run_id: NonBlank
    doc_id: NonBlank
    claim_id: NonBlank
    input_hash: Sha256Hex
    codebook: CodebookReference
    status: Literal["completed", "refused", "incomplete"]
    reason: str | None
    attempt_ids: tuple[NonBlank, ...]
    proposed_theme_ids: tuple[NonBlank, ...]

    @model_validator(mode="after")
    def _classification(self) -> Self:
        if (
            (self.status == "completed") != (self.reason is None)
            or self.status != "completed"
            and self.proposed_theme_ids
        ):
            raise ValueError("invalid_classification")
        return self


class DecisionAudit(AnalysisPart):
    decision_id: NonBlank
    coding_run_id: NonBlank
    doc_id: NonBlank
    claim_id: NonBlank
    theme_id: NonBlank
    target_id: NonBlank
    codebook: CodebookReference
    policy: PolicyReference | None
    status: Literal["accepted", "rejected", "review", "refused"]
    reason: str
    support_status: Literal["assessed", "refused", "incomplete", "flagged"] | None
    flags: tuple[NonBlank, ...]
    missing: tuple[NonBlank, ...]
    original_quote_ids: tuple[NonBlank, ...]
    supported_quote_ids: tuple[NonBlank, ...]
    proposal_hash: Sha256Hex
    input_hash: Sha256Hex
    support_run_hash: Sha256Hex

    @model_validator(mode="after")
    def _decision(self) -> Self:
        if (self.status == "accepted") != bool(self.supported_quote_ids):
            raise ValueError("invalid_decision")
        if self.status == "accepted" and (
            self.policy is None
            or self.reason != "policy_accept"
            or self.support_status != "assessed"
            or self.flags
            or self.missing
        ):
            raise ValueError("invalid_acceptance")
        if not set(self.supported_quote_ids) <= set(self.original_quote_ids):
            raise ValueError("invalid_quote_references")
        if self.policy is not None and self.policy.codebook != self.codebook:
            raise ValueError("mixed_codebook")
        return self


class RejectionAudit(AnalysisPart):
    source_run_id: NonBlank
    doc_id: NonBlank
    window_id: NonBlank | None
    attempt_id: NonBlank | None
    candidate_index: Count | None
    reason: str
    element_ids: tuple[NonBlank, ...]


class CoverageRow(AnalysisPart):
    event_id: NonBlank
    entity_id: NonBlank
    cik: Cik
    period_end: date
    fiscal_year: Count | None
    fiscal_quarter: Literal[1, 2, 3, 4] | None
    doc_type: DocType
    speaker_role: Literal["not_applicable", "unknown"]
    eligibility_status: Literal["eligible", "ineligible", "ambiguous"]
    eligibility_reason: EligibilityReason
    membership_assertion_id: NonBlank
    expected: bool
    available: bool
    parsed: bool
    observable: bool
    availability: Literal["available", "unavailable", "restricted", "not_yet_checked"]
    document_id: NonBlank | None
    doc_ids: tuple[NonBlank, ...]
    latest_state: State
    state_run_id: NonBlank | None
    state_schema_version: Count | None
    missing_reasons: tuple[NonBlank, ...]
    policy_scope: Scope
    accepted_count: Count
    masked_count: Count
    review_count: Count
    rejected_count: Count
    refused_count: Count
    flagged_count: Count
    incomplete_count: Count
    unmatched_count: Count
    copy_refs: tuple[Sha256Hex, ...]
    metadata_refs: tuple[Sha256Hex, ...]
    completion_refs: tuple[Sha256Hex, ...]

    @model_validator(mode="after")
    def _coverage(self) -> Self:
        if self.doc_type == "release" and self.speaker_role != "not_applicable":
            raise ValueError("invalid_release_role")
        if self.doc_type == "transcript" and (
            self.document_id is not None
            or self.doc_ids
            or self.observable
            or self.availability != "not_yet_checked"
            or self.missing_reasons != ("transcript_not_in_scope",)
        ):
            raise ValueError("invalid_transcript_slot")
        if (
            self.parsed
            and not self.available
            or self.observable
            and (
                not self.parsed
                or self.eligibility_status != "eligible"
                or self.latest_state not in ("completed", "completed-no-theme")
            )
        ):
            raise ValueError("invalid_coverage")
        if self.masked_count > self.accepted_count:
            raise ValueError("invalid_masked_count")
        return self


class PrevalenceRow(AnalysisPart):
    population_hash: Sha256Hex
    period_end: date | None
    window_start: date | None
    window_end: date | None
    doc_type: DocType
    speaker_role: Literal["not_applicable", "unknown"]
    view_kind: Literal["direct", "parent", "family"]
    view_id: NonBlank
    codebook_id: NonBlank
    codebook_version: Count
    codebook_hash: Sha256Hex
    analysis_policy_hash: Sha256Hex
    family_map_hash: Sha256Hex | None
    unit: Literal["issuer_period", "issuer_window", "firm_quarter", "equal_issuer_mean"]
    numerator: Annotated[float, Field(ge=0, allow_inf_nan=False)]
    denominator: Count
    rate: Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)] | None
    reason: Literal["empty_denominator"] | None
    expected_count: Count
    available_count: Count
    parsed_count: Count
    observable_count: Count
    excluded_count: Count
    missing_period_count: Count
    restrictions: tuple[NonBlank, ...]
    policy_scope: Scope

    @field_validator("numerator", "rate", mode="before")
    @classmethod
    def _numeric(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("invalid_numeric")  # noqa: TRY004 - Pydantic collects ValueError
        return value

    @model_validator(mode="after")
    def _prevalence(self) -> Self:
        if self.doc_type == "release" and self.speaker_role != "not_applicable":
            raise ValueError("invalid_release_role")
        if self.unit != "equal_issuer_mean" and not self.numerator.is_integer():
            raise ValueError("invalid_count_numerator")
        if self.numerator > self.denominator:
            raise ValueError("invalid_numerator")
        if self.denominator == 0:
            if self.rate is not None or self.reason != "empty_denominator":
                raise ValueError("invalid_empty_denominator")
        elif (
            self.reason is not None
            or self.rate is None
            or abs(self.rate - self.numerator / self.denominator) > 1e-12
        ):
            raise ValueError("invalid_rate")
        if (self.view_kind == "family") != (self.family_map_hash is not None):
            raise ValueError("invalid_family_view")
        if self.unit == "issuer_period":
            if (
                self.period_end is None
                or self.window_start is not None
                or self.window_end is not None
            ):
                raise ValueError("invalid_period")
        elif (
            self.period_end is not None
            or self.window_start is None
            or self.window_end is None
            or self.window_start > self.window_end
        ):
            raise ValueError("invalid_window")
        return self


class CopyRow(AnalysisPart):
    doc_id: NonBlank
    event_id: NonBlank
    disclosure_group: NonBlank
    representative_doc_id: NonBlank
    canonical_hash: Sha256Hex
    copy_assertion_id: NonBlank | None
    copy_assertion_hash: Sha256Hex | None
    rule_version: NonBlank
    status: Literal["consistent", "copy_processing_conflict"]

    @model_validator(mode="after")
    def _copy_ref(self) -> Self:
        if (self.copy_assertion_id is None) != (self.copy_assertion_hash is None):
            raise ValueError("invalid_copy_binding")
        return self


class AnalysisRunRecord(AnalysisPart):
    run_id: NonBlank
    created_at: AwareDatetime
    scope: Scope
    audience: Audience
    population_hash: Sha256Hex
    event_manifest_hash: Sha256Hex
    pilot_hash: Sha256Hex
    universe_hash: Sha256Hex
    documents: tuple[tuple[NonBlank, Sha256Hex], ...]
    canonical_manifests: tuple[tuple[NonBlank, Sha256Hex], ...]
    mask_manifests: tuple[tuple[NonBlank, Sha256Hex], ...]
    source_run_hash: Sha256Hex
    coding_run_hash: Sha256Hex
    support_run_hash: Sha256Hex
    configuration_hashes: tuple[tuple[NonBlank, Sha256Hex], ...]
    prompt_hashes: tuple[tuple[NonBlank, Sha256Hex], ...]
    identity_hashes: tuple[tuple[NonBlank, Sha256Hex], ...]
    codebook: CodebookReference
    assignment_policy: PolicyReference | None
    analysis_policy: AnalysisPolicy
    family_map: ThemeFamilyMap | None
    completion_hashes: tuple[tuple[NonBlank, Sha256Hex], ...]
    copy_hashes: tuple[tuple[NonBlank, Sha256Hex], ...]
    validator_version: NonBlank
    software: tuple[tuple[NonBlank, NonBlank], ...] = Field(repr=False)
    lock_hash: Sha256Hex
    counts_by_state: tuple[tuple[State, Count], ...]
    counts_by_decision: tuple[
        tuple[Literal["accepted", "rejected", "review", "refused"], Count], ...
    ]
    counts_by_reason: tuple[tuple[NonBlank, Count], ...]
    raw_verification: tuple[RawCacheVerification, ...]
    table_hashes: tuple[tuple[NonBlank, Sha256Hex], ...]
    evidence_hashes: tuple[tuple[NonBlank, Sha256Hex], ...]
    billable_cost: Literal["none, self-hosted"] = "none, self-hosted"
    binding_hash: Sha256Hex

    @model_validator(mode="after")
    def _run(self) -> Self:
        if (
            self.scope != self.analysis_policy.scope
            or self.population_hash != self.analysis_policy.population_hash
        ):
            raise ValueError("policy_mismatch")
        if self.assignment_policy is not None and (
            self.assignment_policy.codebook != self.codebook
            or self.assignment_policy.kind == "fixture"
            and self.scope != "fixture"
        ):
            raise ValueError("policy_mismatch")
        if self.family_map is not None and self.family_map.codebook != self.codebook:
            raise ValueError("mixed_codebook")
        for name in (
            "documents",
            "canonical_manifests",
            "mask_manifests",
            "configuration_hashes",
            "prompt_hashes",
            "identity_hashes",
            "completion_hashes",
            "copy_hashes",
            "software",
            "counts_by_state",
            "counts_by_decision",
            "counts_by_reason",
            "table_hashes",
            "evidence_hashes",
        ):
            values = getattr(self, name)
            keys = tuple(k for k, _ in values)
            if keys != tuple(sorted(set(keys))):
                raise ValueError("invalid_sorted_bindings")
        if any(reason not in ANALYSIS_REASONS for reason, _ in self.counts_by_reason):
            raise ValueError("invalid_reason")
        if len({v.stage for v in self.raw_verification}) != len(self.raw_verification):
            raise ValueError("invalid_raw_verification")
        return self


@dataclass(frozen=True, repr=False)
class CanonicalSnapshot:
    doc_id: str
    data: bytes

    def __post_init__(self) -> None:
        if (
            type(self.doc_id) is not str
            or not self.doc_id.strip()
            or type(self.data) is not bytes
        ):
            raise AnalysisError("malformed_record")


@dataclass(frozen=True, repr=False)
class FixtureAuthorization:
    corpus_id: Literal["djia-synthetic", "stage10-invented"]
    event_manifest_hash: str
    pilot_hash: str
    provenance_hash: str

    def __post_init__(self) -> None:
        if type(self.corpus_id) is not str or self.corpus_id not in (
            "djia-synthetic",
            "stage10-invented",
        ):
            raise AnalysisError("malformed_record")
        for value in (self.event_manifest_hash, self.pilot_hash, self.provenance_hash):
            if (
                type(value) is not str
                or len(value) != 64
                or any(c not in "0123456789abcdef" for c in value)
            ):
                raise AnalysisError("malformed_record")


@dataclass(frozen=True, repr=False)
class RawSnapshot:
    doc_id: str
    artifact: ArtifactRef
    data: bytes

    def __post_init__(self) -> None:
        if (
            type(self.doc_id) is not str
            or not self.doc_id.strip()
            or type(self.artifact) is not ArtifactRef
            or type(self.data) is not bytes
        ):
            raise AnalysisError("malformed_record")


@dataclass(frozen=True, repr=False)
class RawCacheInputs:
    coding: CodingCache | None
    support: SupportCache | None


@dataclass(frozen=True, repr=False)
class AnalysisInputs:
    sources: SupportSources
    support: StoredSupportRun
    coding: CodingRun
    assignment_policy: AssignmentPolicy | None
    expected: tuple[ExpectedEvent, ...]
    acquisition: tuple[AcquisitionStatus, ...]
    metadata: tuple[DocumentMetadata, ...]
    copies: tuple[CopyAssertion, ...]
    no_theme: tuple[NoThemeDeclaration, ...]
    provenance_hash: str
    raw_verification: tuple[RawCacheVerification, ...]
    raw_caches: RawCacheInputs
    raw_snapshots: tuple[RawSnapshot, ...]
    analysis_policy: AnalysisPolicy
    canonical_snapshots: tuple[CanonicalSnapshot, ...]
    fixture_authorization: FixtureAuthorization | None

    def __post_init__(self) -> None:
        containers = (
            ("expected", ExpectedEvent, "event_id"),
            ("acquisition", AcquisitionStatus, "document_id"),
            ("metadata", DocumentMetadata, "doc_id"),
            ("copies", CopyAssertion, "copy_id"),
            ("no_theme", NoThemeDeclaration, "doc_id"),
            ("raw_verification", RawCacheVerification, "stage"),
            ("raw_snapshots", RawSnapshot, "doc_id"),
            ("canonical_snapshots", CanonicalSnapshot, "doc_id"),
        )
        for name, model, key in containers:
            rows = getattr(self, name)
            if (
                type(rows) is not tuple
                or any(type(row) is not model for row in rows)
                or len({getattr(row, key) for row in rows}) != len(rows)
            ):
                raise AnalysisError("malformed_record")
        if (
            type(self.sources) is not SupportSources
            or type(self.support) is not StoredSupportRun
            or type(self.coding) is not CodingRun
            or type(self.analysis_policy) is not AnalysisPolicy
            or (
                self.fixture_authorization is not None
                and type(self.fixture_authorization) is not FixtureAuthorization
            )
            or type(self.raw_caches) is not RawCacheInputs
        ):
            raise AnalysisError("malformed_record")
        if (
            type(self.provenance_hash) is not str
            or len(self.provenance_hash) != 64
            or any(c not in "0123456789abcdef" for c in self.provenance_hash)
        ):
            raise AnalysisError("malformed_record")
        events = {row.event_id: row for row in self.expected}
        documents = {row.doc_id: row for row in self.metadata}
        for metadata in self.metadata:
            event = events.get(metadata.event_id)
            if event is None or (
                metadata.entity_id,
                metadata.cik,
                metadata.period_end,
                metadata.fiscal_year,
                metadata.fiscal_quarter,
            ) != (
                event.entity_id,
                event.cik,
                event.period_end,
                event.fiscal_year,
                event.fiscal_quarter,
            ):
                raise AnalysisError("input_changed")
        canonical = {
            bundle.document.doc_id: bundle.document for bundle in self.sources.bundles
        }
        if len(canonical) != len(self.sources.bundles):
            raise AnalysisError("invalid_references")
        for metadata in self.metadata:
            document = canonical.get(metadata.doc_id)
            if document is None or (
                metadata.source_document_id,
                metadata.canonical_hash,
                metadata.canonicalization_version,
            ) != (
                document.source_document_id,
                document.canonical_hash,
                document.canonicalization_version,
            ):
                raise AnalysisError("input_changed")
        acquisition_docs = {
            row.doc_id: row for row in self.acquisition if row.doc_id is not None
        }
        if len(acquisition_docs) != sum(
            row.doc_id is not None for row in self.acquisition
        ):
            raise AnalysisError("invalid_references")
        for metadata in self.metadata:
            acquired = acquisition_docs.get(metadata.doc_id)
            if acquired is None or (
                acquired.event_id,
                acquired.source_document_id,
                acquired.raw_hash,
                acquired.pilot_hash,
            ) != (
                metadata.event_id,
                metadata.source_document_id,
                metadata.raw_hash,
                events[metadata.event_id].pilot_hash,
            ):
                raise AnalysisError("input_changed")
        if self.provenance_hash != self.sources.provenance_hash:
            raise AnalysisError("input_changed")
        for snapshot in self.raw_snapshots:
            metadata = documents.get(snapshot.doc_id)
            if metadata is None or metadata.raw_artifact != snapshot.artifact:
                raise AnalysisError("input_changed")
        for copy in self.copies:
            members = [documents.get(doc) for doc in copy.doc_ids]
            if (
                any(
                    member is None or member.event_id != copy.event_id
                    for member in members
                )
                or tuple((doc, documents[doc].canonical_hash) for doc in copy.doc_ids)
                != copy.documents
            ):
                raise AnalysisError("input_changed")


@dataclass(frozen=True, repr=False)
class BoundAnalysis:
    inputs: AnalysisInputs
    decisions: DecisionSet
    expected: tuple[ExpectedEvent, ...]
    acquisition: tuple[AcquisitionStatus, ...]
    metadata: tuple[DocumentMetadata, ...]
    copies: tuple[CopyAssertion, ...]
    completions: tuple[DocumentCompletion, ...]
    binding_hash: Sha256Hex


@dataclass(frozen=True, repr=False)
class AnalysisTables:
    frames: Mapping[str, pl.DataFrame]

    def __post_init__(self) -> None:
        if not isinstance(self.frames, Mapping) or set(self.frames) != set(
            TABLE_SCHEMAS
        ):
            raise AnalysisError("malformed_record")
        detached = {}
        for name, schema in TABLE_SCHEMAS.items():
            frame = self.frames[name]
            if type(frame) is not pl.DataFrame or frame.schema != pl.Schema(schema):
                raise AnalysisError("malformed_record")
            try:
                for row in frame.iter_rows(named=True):
                    TABLE_MODELS[name].model_validate_json(canonical_json(row))
            except (ValidationError, ValueError, TypeError, OverflowError):
                raise AnalysisError("malformed_record") from None
            grain = TABLE_GRAINS[name]
            if frame.height and frame.select(grain).is_duplicated().any():
                raise AnalysisError("invalid_references")
            detached[name] = frame.clone()
        _check_table_foreign_keys(detached, complete=False)
        book_bindings = (
            detached["observations"]
            .select("codebook_id", "codebook_version", "codebook_hash")
            .unique()
        )
        if book_bindings.height > 1:
            raise AnalysisError("mixed_codebook")
        policy_bindings = (
            detached["observations"]
            .select("policy_kind", "policy_hash", "policy_scope")
            .unique()
        )
        if policy_bindings.height > 1:
            raise AnalysisError("policy_mismatch")
        object.__setattr__(self, "frames", MappingProxyType(detached))

    @classmethod
    def empty(cls) -> Self:
        return cls(
            {
                name: pl.DataFrame(schema=schema)
                for name, schema in TABLE_SCHEMAS.items()
            }
        )


def _check_table_foreign_keys(
    frames: Mapping[str, pl.DataFrame], *, complete: bool
) -> None:
    for name, foreign_keys in TABLE_FOREIGN_KEYS.items():
        for local, target, remote in foreign_keys:
            # Task 5 produces audit frames before Task 6 adjudicates completion.
            # Only that empty later-stage relation can be deferred; final gates
            # enforce it without inventing a completion row.
            if (
                not complete
                and name == "observations"
                and target == "completions"
                and frames[target].is_empty()
            ):
                continue
            if (
                frames[name]
                .select(local)
                .join(
                    frames[target].select(remote).unique(),
                    left_on=local,
                    right_on=remote,
                    how="anti",
                )
                .height
            ):
                raise AnalysisError("invalid_references")


def validate_analysis_tables(tables: AnalysisTables) -> AnalysisTables:
    """Recheck structural rows/grains and every final FK before storage/export.

    Task 5 may construct intermediate frames with empty completions. Complete
    run containers and future serialization/publication call this full gate.
    Source exactness/current permissions still require the consuming gates.
    """
    if type(tables) is not AnalysisTables:
        raise AnalysisError("malformed_record")
    checked = AnalysisTables(tables.frames)
    _check_table_foreign_keys(checked.frames, complete=True)
    return checked


@dataclass(frozen=True, repr=False)
class AnalysisRun:
    record: AnalysisRunRecord
    tables: AnalysisTables

    def __post_init__(self) -> None:
        object.__setattr__(self, "tables", validate_analysis_tables(self.tables))


@dataclass(frozen=True, repr=False)
class StoredAnalysisRun:
    record: AnalysisRunRecord
    tables: AnalysisTables
    manifest_hash: Sha256Hex
    published_hashes: tuple[tuple[str, Sha256Hex], ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "tables", validate_analysis_tables(self.tables))


@dataclass(frozen=True, repr=False)
class EvidenceView:
    reference: EvidenceViewReference
    html: bytes | None
    canonical_bytes: bytes | None
    raw_bytes: bytes | None

    def __post_init__(self) -> None:
        for payload, artifact in (
            (self.html, self.reference.view_artifact),
            (self.canonical_bytes, self.reference.canonical_artifact),
            (self.raw_bytes, self.reference.raw_artifact),
        ):
            if (
                (payload is None) != (artifact is None)
                or payload is not None
                and (type(payload) is not bytes or not artifact.matches(payload))
            ):
                raise AnalysisError("input_changed")
        if self.reference.status == "withheld" and any(
            value is not None
            for value in (self.html, self.canonical_bytes, self.raw_bytes)
        ):
            raise AnalysisError("rights_restricted")


# Literal Polars types are declared below; no runtime schema inference.

TABLE_MODELS = {
    "observations": Observation,
    "quotes": QuoteAudit,
    "claims": ClaimAudit,
    "claim_evidence": ClaimEvidence,
    "assignment_claims": AssignmentClaimLink,
    "classifications": ClassificationAudit,
    "decisions": DecisionAudit,
    "novelty": NoveltyItem,
    "rejections": RejectionAudit,
    "completions": DocumentCompletion,
    "coverage": CoverageRow,
    "prevalence": PrevalenceRow,
    "copies": CopyRow,
    "evidence": EvidenceViewReference,
}
TABLE_GRAINS = {
    "observations": (
        "entity_id",
        "period_end",
        "doc_type",
        "speaker_role",
        "theme_id",
        "doc_id",
        "quote_id",
        "codebook_id",
        "codebook_version",
    ),
    "quotes": ("doc_id", "quote_id"),
    "claims": ("doc_id", "claim_id"),
    "claim_evidence": ("doc_id", "claim_id", "quote_id"),
    "assignment_claims": (
        "assignment_id",
        "doc_id",
        "claim_id",
        "decision_id",
        "target_id",
    ),
    "classifications": ("classification_id",),
    "decisions": ("decision_id",),
    "novelty": ("novelty_id",),
    "rejections": (
        "source_run_id",
        "doc_id",
        "window_id",
        "attempt_id",
        "candidate_index",
        "reason",
    ),
    "completions": ("doc_id",),
    "coverage": ("event_id", "doc_type", "speaker_role"),
    "prevalence": (
        "population_hash",
        "period_end",
        "window_start",
        "window_end",
        "doc_type",
        "speaker_role",
        "view_kind",
        "view_id",
        "codebook_id",
        "codebook_version",
        "analysis_policy_hash",
        "family_map_hash",
        "unit",
    ),
    "copies": ("doc_id",),
    "evidence": ("doc_id", "quote_id", "audience"),
}
# Each tuple is (local columns, target table, target columns). External manifest
# pointers are documented independently; document qualification is never dropped.
TABLE_FOREIGN_KEYS = {
    "observations": (
        (("doc_id", "quote_id"), "quotes", ("doc_id", "quote_id")),
        (("doc_id",), "completions", ("doc_id",)),
    ),
    "quotes": (),
    "claims": (),
    "claim_evidence": (
        (("doc_id", "claim_id"), "claims", ("doc_id", "claim_id")),
        (("doc_id", "quote_id"), "quotes", ("doc_id", "quote_id")),
    ),
    "assignment_claims": (
        (("doc_id", "claim_id"), "claims", ("doc_id", "claim_id")),
        (
            ("doc_id", "claim_id", "decision_id", "target_id"),
            "decisions",
            ("doc_id", "claim_id", "decision_id", "target_id"),
        ),
    ),
    "classifications": ((("doc_id", "claim_id"), "claims", ("doc_id", "claim_id")),),
    "decisions": ((("doc_id", "claim_id"), "claims", ("doc_id", "claim_id")),),
    "novelty": (
        (("doc_id", "claim_id"), "claims", ("doc_id", "claim_id")),
        (
            ("doc_id", "claim_id", "classification_id"),
            "classifications",
            ("doc_id", "claim_id", "classification_id"),
        ),
    ),
    "rejections": (),
    "completions": (),
    "coverage": (),
    "prevalence": (),
    "copies": (),
    "evidence": ((("doc_id", "quote_id"), "quotes", ("doc_id", "quote_id")),),
}
PUBLIC_NAMES = (
    "AnalysisPart",
    "ExpectedEvent",
    "AcquisitionStatus",
    "DocumentMetadata",
    "CopyAssertion",
    "AnalysisPolicy",
    "ThemeFamilyMap",
    "NoThemeDeclaration",
    "DocumentCompletion",
    "EvidenceViewReference",
    "CaptureObservation",
    "RawCacheVerification",
    "AnalysisRunRecord",
    "RawSnapshot",
    "CanonicalSnapshot",
    "FixtureAuthorization",
    "RawCacheInputs",
    "AnalysisInputs",
    "BoundAnalysis",
    "AnalysisTables",
    "AnalysisRun",
    "StoredAnalysisRun",
    "EvidenceView",
    "Observation",
    "QuoteAudit",
    "ClaimAudit",
    "ClaimEvidence",
    "ClassificationAudit",
    "DecisionAudit",
    "RejectionAudit",
    "CoverageRow",
    "PrevalenceRow",
    "CopyRow",
    "TABLE_MODELS",
    "TABLE_SCHEMAS",
    "TABLE_GRAINS",
    "TABLE_FOREIGN_KEYS",
    "family_map_hash",
    "validate_analysis_tables",
)

TABLE_SCHEMAS = {
    "observations": {
        "schema_version": pl.Int64,
        "doc_id": pl.String,
        "quote_id": pl.String,
        "canonical_hash": pl.String,
        "start": pl.Int64,
        "end": pl.Int64,
        "element_id": pl.String,
        "validator_version": pl.String,
        "mask_ids": pl.List(pl.String),
        "source_run_id": pl.String,
        "source_run_hash": pl.String,
        "metadata_ref": pl.String,
        "quote_text": pl.String,
        "event_id": pl.String,
        "entity_id": pl.String,
        "cik": pl.String,
        "period_end": pl.Date,
        "fiscal_year": pl.Int64,
        "fiscal_quarter": pl.Int64,
        "doc_type": pl.String,
        "speaker_role": pl.String,
        "theme_id": pl.String,
        "assignment_id": pl.String,
        "codebook_id": pl.String,
        "codebook_version": pl.Int64,
        "codebook_hash": pl.String,
        "headline_eligible": pl.Boolean,
        "disclosure_group": pl.String,
        "policy_kind": pl.String,
        "policy_hash": pl.String,
        "policy_scope": pl.String,
        "coding_run_id": pl.String,
        "coding_run_hash": pl.String,
        "support_run_id": pl.String,
        "support_run_hash": pl.String,
        "evidence_id": pl.String,
        "published_at": pl.Datetime("us", "UTC"),
        "retrieved_at": pl.Datetime("us", "UTC"),
        "extracted_at": pl.Datetime("us", "UTC"),
    },
    "quotes": {
        "schema_version": pl.Int64,
        "doc_id": pl.String,
        "quote_id": pl.String,
        "canonical_hash": pl.String,
        "start": pl.Int64,
        "end": pl.Int64,
        "element_id": pl.String,
        "validator_version": pl.String,
        "mask_ids": pl.List(pl.String),
        "source_run_id": pl.String,
        "source_run_hash": pl.String,
        "metadata_ref": pl.String,
        "quote_text": pl.String,
    },
    "claims": {
        "schema_version": pl.Int64,
        "doc_id": pl.String,
        "claim_id": pl.String,
        "window_id": pl.String,
        "attempt_id": pl.String,
        "interpretation_hash": pl.String,
        "interpretation": pl.String,
        "original_quote_ids": pl.List(pl.String),
        "source_run_id": pl.String,
        "source_run_hash": pl.String,
    },
    "claim_evidence": {
        "schema_version": pl.Int64,
        "doc_id": pl.String,
        "claim_id": pl.String,
        "quote_id": pl.String,
    },
    "assignment_claims": {
        "schema_version": pl.Int64,
        "assignment_id": pl.String,
        "doc_id": pl.String,
        "claim_id": pl.String,
        "decision_id": pl.String,
        "target_id": pl.String,
    },
    "classifications": {
        "schema_version": pl.Int64,
        "classification_id": pl.String,
        "coding_run_id": pl.String,
        "doc_id": pl.String,
        "claim_id": pl.String,
        "input_hash": pl.String,
        "codebook": pl.Struct(
            {
                "codebook_id": pl.String,
                "codebook_version": pl.Int64,
                "content_hash": pl.String,
            }
        ),
        "status": pl.String,
        "reason": pl.String,
        "attempt_ids": pl.List(pl.String),
        "proposed_theme_ids": pl.List(pl.String),
    },
    "decisions": {
        "schema_version": pl.Int64,
        "decision_id": pl.String,
        "coding_run_id": pl.String,
        "doc_id": pl.String,
        "claim_id": pl.String,
        "theme_id": pl.String,
        "target_id": pl.String,
        "codebook": pl.Struct(
            {
                "codebook_id": pl.String,
                "codebook_version": pl.Int64,
                "content_hash": pl.String,
            }
        ),
        "policy": pl.Struct(
            {
                "policy_id": pl.String,
                "policy_hash": pl.String,
                "kind": pl.String,
                "codebook": pl.Struct(
                    {
                        "codebook_id": pl.String,
                        "codebook_version": pl.Int64,
                        "content_hash": pl.String,
                    }
                ),
                "classifier_configuration_hash": pl.String,
                "support_configuration_hash": pl.String,
                "calibration_reference": pl.String,
            }
        ),
        "status": pl.String,
        "reason": pl.String,
        "support_status": pl.String,
        "flags": pl.List(pl.String),
        "missing": pl.List(pl.String),
        "original_quote_ids": pl.List(pl.String),
        "supported_quote_ids": pl.List(pl.String),
        "proposal_hash": pl.String,
        "input_hash": pl.String,
        "support_run_hash": pl.String,
    },
    "novelty": {
        "schema_version": pl.Int64,
        "novelty_id": pl.String,
        "coding_run_id": pl.String,
        "classification_id": pl.String,
        "source_run_id": pl.String,
        "doc_id": pl.String,
        "claim_id": pl.String,
        "codebook": pl.Struct(
            {
                "codebook_id": pl.String,
                "codebook_version": pl.Int64,
                "content_hash": pl.String,
            }
        ),
        "input_hash": pl.String,
        "original_quote_ids": pl.List(pl.String),
        "reason": pl.String,
    },
    "rejections": {
        "schema_version": pl.Int64,
        "source_run_id": pl.String,
        "doc_id": pl.String,
        "window_id": pl.String,
        "attempt_id": pl.String,
        "candidate_index": pl.Int64,
        "reason": pl.String,
        "element_ids": pl.List(pl.String),
    },
    "completions": {
        "schema_version": pl.Int64,
        "doc_id": pl.String,
        "event_id": pl.String,
        "canonical_hash": pl.String,
        "source_run_hash": pl.String,
        "coding_run_hash": pl.String,
        "support_run_hash": pl.String,
        "codebook": pl.Struct(
            {
                "codebook_id": pl.String,
                "codebook_version": pl.Int64,
                "content_hash": pl.String,
            }
        ),
        "assignment_policy": pl.Struct(
            {
                "policy_id": pl.String,
                "policy_hash": pl.String,
                "kind": pl.String,
                "codebook": pl.Struct(
                    {
                        "codebook_id": pl.String,
                        "codebook_version": pl.Int64,
                        "content_hash": pl.String,
                    }
                ),
                "classifier_configuration_hash": pl.String,
                "support_configuration_hash": pl.String,
                "calibration_reference": pl.String,
            }
        ),
        "analysis_policy_hash": pl.String,
        "traversal_complete": pl.Boolean,
        "classification_complete": pl.Boolean,
        "assessment_complete": pl.Boolean,
        "decision_complete": pl.Boolean,
        "eligible_units": pl.Int64,
        "completed_windows": pl.Int64,
        "failed_windows": pl.Int64,
        "accepted_count": pl.Int64,
        "masked_count": pl.Int64,
        "rejected_count": pl.Int64,
        "review_count": pl.Int64,
        "refused_count": pl.Int64,
        "flagged_count": pl.Int64,
        "incomplete_count": pl.Int64,
        "unmatched_count": pl.Int64,
        "processing_state": pl.String,
        "reasons": pl.List(pl.String),
        "declaration_hash": pl.String,
        "observable": pl.Boolean,
        "policy_scope": pl.String,
    },
    "coverage": {
        "schema_version": pl.Int64,
        "event_id": pl.String,
        "entity_id": pl.String,
        "cik": pl.String,
        "period_end": pl.Date,
        "fiscal_year": pl.Int64,
        "fiscal_quarter": pl.Int64,
        "doc_type": pl.String,
        "speaker_role": pl.String,
        "eligibility_status": pl.String,
        "eligibility_reason": pl.String,
        "membership_assertion_id": pl.String,
        "expected": pl.Boolean,
        "available": pl.Boolean,
        "parsed": pl.Boolean,
        "observable": pl.Boolean,
        "availability": pl.String,
        "document_id": pl.String,
        "doc_ids": pl.List(pl.String),
        "latest_state": pl.String,
        "state_run_id": pl.String,
        "state_schema_version": pl.Int64,
        "missing_reasons": pl.List(pl.String),
        "policy_scope": pl.String,
        "accepted_count": pl.Int64,
        "masked_count": pl.Int64,
        "review_count": pl.Int64,
        "rejected_count": pl.Int64,
        "refused_count": pl.Int64,
        "flagged_count": pl.Int64,
        "incomplete_count": pl.Int64,
        "unmatched_count": pl.Int64,
        "copy_refs": pl.List(pl.String),
        "metadata_refs": pl.List(pl.String),
        "completion_refs": pl.List(pl.String),
    },
    "prevalence": {
        "schema_version": pl.Int64,
        "population_hash": pl.String,
        "period_end": pl.Date,
        "window_start": pl.Date,
        "window_end": pl.Date,
        "doc_type": pl.String,
        "speaker_role": pl.String,
        "view_kind": pl.String,
        "view_id": pl.String,
        "codebook_id": pl.String,
        "codebook_version": pl.Int64,
        "codebook_hash": pl.String,
        "analysis_policy_hash": pl.String,
        "family_map_hash": pl.String,
        "unit": pl.String,
        "numerator": pl.Float64,
        "denominator": pl.Int64,
        "rate": pl.Float64,
        "reason": pl.String,
        "expected_count": pl.Int64,
        "available_count": pl.Int64,
        "parsed_count": pl.Int64,
        "observable_count": pl.Int64,
        "excluded_count": pl.Int64,
        "missing_period_count": pl.Int64,
        "restrictions": pl.List(pl.String),
        "policy_scope": pl.String,
    },
    "copies": {
        "schema_version": pl.Int64,
        "doc_id": pl.String,
        "event_id": pl.String,
        "disclosure_group": pl.String,
        "representative_doc_id": pl.String,
        "canonical_hash": pl.String,
        "copy_assertion_id": pl.String,
        "copy_assertion_hash": pl.String,
        "rule_version": pl.String,
        "status": pl.String,
    },
    "evidence": {
        "schema_version": pl.Int64,
        "evidence_id": pl.String,
        "doc_id": pl.String,
        "quote_id": pl.String,
        "canonical_hash": pl.String,
        "start": pl.Int64,
        "end": pl.Int64,
        "validator_version": pl.String,
        "element_id": pl.String,
        "mask_ids": pl.List(pl.String),
        "locator_hash": pl.String,
        "quote_text_hash": pl.String,
        "source_fragment_url": pl.String,
        "source_url": pl.String,
        "raw_artifact": pl.Struct(
            {
                "schema_version": pl.Int64,
                "content_sha256": pl.String,
                "media_type": pl.String,
                "storage_ref": pl.String,
                "rights_status": pl.String,
                "rights_basis": pl.String,
            }
        ),
        "canonical_artifact": pl.Struct(
            {
                "schema_version": pl.Int64,
                "content_sha256": pl.String,
                "media_type": pl.String,
                "storage_ref": pl.String,
                "rights_status": pl.String,
                "rights_basis": pl.String,
            }
        ),
        "view_artifact": pl.Struct(
            {
                "schema_version": pl.Int64,
                "content_sha256": pl.String,
                "media_type": pl.String,
                "storage_ref": pl.String,
                "rights_status": pl.String,
                "rights_basis": pl.String,
            }
        ),
        "anchor_id": pl.String,
        "audience": pl.String,
        "rights_status": pl.String,
        "rights_basis": pl.String,
        "status": pl.String,
        "reason": pl.String,
        "capture_reference": pl.String,
    },
}
