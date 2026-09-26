"""The point-in-time DJIA cohort's records (Stage 4; P §Data contracts).

- **The universe.** ``UniverseDefinition`` is P's universe definition.
- **Membership.** ``MembershipAssertion`` is P's membership assertion, one per
  security and evidence item, and ``MembershipInterval`` is a derived effective
  interval.
- **Identity.** ``IssuerMapping`` and ``Issuer`` carry each security to its issuer and
  a 10-character CIK.
- **The whole.** ``UniverseManifest`` is the frozen cohort, with its
  ``CohortReport``.

These are ingestion records, not core contracts, and they join ingestion schema
version 1. Committed records carry facts and citations, never source wording: a
citation is a URL, the raw bytes' hash, and locators that hash the cited text (the
user's decision, 2026-09-26). docs/data-dictionary.md documents every field and value.
"""

from datetime import date
from enum import StrEnum
from typing import Literal, Self

from earnings_core import ArtifactRef, RightsStatus
from earnings_core.artifacts import NonBlankStr
from earnings_core.documents import IdPart
from earnings_core.hashing import Sha256Hex
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    NonNegativeInt,
    PositiveInt,
    model_validator,
)

from earnings_ingestion.canonical.records import IngestionRecord
from earnings_ingestion.fetch.records import Retrieval, SourceId
from earnings_ingestion.sec.identifiers import Cik


class _Part(BaseModel):
    """A nested part of a cohort record: immutable, closed, strictly typed."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class EvidenceClass(StrEnum):
    """What kind of source an item comes from (P §Membership evidence)."""

    OFFICIAL = "official"
    """The index provider's own statement."""
    SECONDARY = "secondary"
    """A dated third-party roster, labeled as secondary evidence."""
    ETF_PROXY = "etf_proxy"
    """A tracking fund's holdings: corroboration only, never the roster."""
    USER_SUPPLIED = "user_supplied"
    """A list the user supplied: a check, never evidence."""


class SourceRole(StrEnum):
    """What a registered source may be used for."""

    ANCHOR = "anchor"
    """The dated snapshot that the intervals start from."""
    CHANGE = "change"
    """Addition and removal announcements."""
    CORROBORATION = "corroboration"
    """A dated snapshot that the reconstruction must reproduce."""
    CHECK = "check"
    """A snapshot compared and reported, never holding the freeze."""


class LocatorKind(StrEnum):
    TEXT_SPAN = "text_span"
    """Half-open code-point offsets into an HTML artifact's canonical text."""
    JSON_POINTER = "json_pointer"
    """An RFC 6901 pointer into a JSON artifact."""


class BoundTiming(StrEnum):
    """When on its date a change takes effect, as the evidence states it."""

    BEFORE_OPEN = "before_open"
    AFTER_CLOSE = "after_close"
    UNSPECIFIED = "unspecified"


class BoundBasis(StrEnum):
    """What establishes an interval's start."""

    ANNOUNCED = "announced"
    """An official effective date."""
    ANCHOR_SNAPSHOT = "anchor_snapshot"
    """The anchor's date: a lower bound, never an entry date."""


class AssertedAction(StrEnum):
    """What one evidence item says about one security."""

    MEMBER_AT = "member_at"
    """A snapshot lists it as a member on the snapshot's date."""
    ADDED = "added"
    REMOVED = "removed"


class AssertionStatus(StrEnum):
    """An assertion's standing (plan 6, P6-6)."""

    SUPPORTED = "supported"
    """Consistent with the security's other evidence, and part of an interval."""
    CONFLICTING = "conflicting"
    """The security's evidence does not form one consistent sequence."""
    AMBIGUOUS = "ambiguous"
    """An addition and a removal of the security share an effective date."""
    WITHHELD = "withheld"
    """First published after the cutoff: kept, never applied (P-C4)."""


class ResolutionStatus(StrEnum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    """No SEC candidate is confirmed."""
    CONFLICTING = "conflicting"
    """More than one CIK is confirmed."""
    RETAINED_UNRESOLVED = "retained_unresolved"
    """A reviewer kept it unresolved and excluded it, with a reason."""


class ResolutionMethod(StrEnum):
    SEC_TICKER_AND_NAME = "sec_ticker_and_name"
    """SEC's ticker list proposed the CIK, and SEC's record for it lists the cited
    ticker under a name that covers the cited name (P6-8)."""
    OVERRIDE = "override"


class OverrideKind(StrEnum):
    REJECT_ASSERTION = "reject_assertion"
    """Set aside one conflicting or ambiguous assertion; it stays, marked."""
    SET_ISSUER = "set_issuer"
    """Name a security's CIK."""
    RETAIN_UNRESOLVED = "retain_unresolved"
    """Keep a security unresolved, excluded from the candidate issuers."""
    ACKNOWLEDGE = "acknowledge"
    """Accept one reviewed finding, bound to its digest."""
    HOLDING_ALIAS = "holding_alias"
    """Match a fund holding's name to a security."""


class FindingKind(StrEnum):
    MISSING_ANCHOR = "missing_anchor"
    MEMBERSHIP_CONFLICT = "membership_conflict"
    MEMBERSHIP_AMBIGUITY = "membership_ambiguity"
    IDENTITY = "identity"
    """An in-scope security without exactly one confirmed CIK."""
    MEMBER_COUNT = "member_count"
    """The reconstructed roster's size differs from the expected count."""
    DIFFERENCE = "difference"
    """A snapshot disagrees with the reconstruction on its date."""
    GAP = "gap"
    """A calendar quarter with no corroborating snapshot."""
    WITHHELD = "withheld"
    SUPERSEDED = "superseded"
    """A fund filing replaced by a later filing for the same report date."""


class EvidenceLocator(_Part):
    """Where cited evidence sits in an artifact, and the hash of what it says."""

    kind: LocatorKind
    canonicalization_version: IdPart | None = None
    canonical_sha256: Sha256Hex | None = None
    start: NonNegativeInt | None = None
    end: NonNegativeInt | None = None
    pointer: str | None = None
    cited_sha256: Sha256Hex

    @model_validator(mode="after")
    def _shape(self) -> Self:
        text = (self.canonicalization_version, self.canonical_sha256, self.start)
        if self.kind is LocatorKind.TEXT_SPAN:
            if None in (*text, self.end) or self.pointer is not None:
                raise ValueError("a text span has a version, a text hash, and offsets")
            if self.end <= self.start:
                raise ValueError("a text span needs start < end")
        elif self.pointer is None or any(v is not None for v in (*text, self.end)):
            raise ValueError("a JSON pointer locator has a pointer and nothing else")
        elif self.pointer and not self.pointer.startswith("/"):
            raise ValueError("a JSON pointer is empty or starts with '/'")
        return self


class Citation(_Part):
    """Evidence in one stored artifact: its source, bytes, and the places in it."""

    source_id: SourceId
    url: NonBlankStr
    artifact: ArtifactRef
    retrieved_at: AwareDatetime
    locators: tuple[EvidenceLocator, ...]


class SourceRights(_Part):
    """A source's class and rights, copied from its register entry."""

    source_id: SourceId
    evidence_class: EvidenceClass | None
    rights_status: RightsStatus
    rights_basis: NonBlankStr


class CitedIdentity(_Part):
    """A security's name and ticker as one evidence row states them, on its date."""

    evidence_id: IdPart
    observed_on: date
    name: NonBlankStr
    ticker: NonBlankStr


class SecurityRecord(_Part):
    """One security, with every name and ticker the evidence gives it, by date."""

    security_id: IdPart
    identities: tuple[CitedIdentity, ...]


class MembershipAssertion(_Part):
    """One evidence item's statement about one security (P §Data contracts).

    ``effective_from`` and ``effective_to`` are the interval the item supports; they
    are null unless ``status`` is ``supported``.
    """

    membership_assertion_id: IdPart
    universe_id: IdPart
    security_id: IdPart
    issuer_id: IdPart | None
    cik: Cik | None
    asserted_action: AssertedAction
    asserted_date: date
    asserted_timing: BoundTiming
    effective_from: date | None
    effective_from_basis: BoundBasis | None
    effective_from_timing: BoundTiming | None
    effective_to: date | None
    effective_to_timing: BoundTiming | None
    announcement_date: date | None
    source_snapshot_date: date | None
    publication_date: date
    publication_time: AwareDatetime | None
    retrieved_at: AwareDatetime
    source_id: SourceId
    evidence_id: IdPart
    url: NonBlankStr
    evidence_locators: tuple[EvidenceLocator, ...]
    raw_content_hash: Sha256Hex
    rights_status: RightsStatus
    status: AssertionStatus
    resolved_by: IdPart | None

    @model_validator(mode="after")
    def _interval(self) -> Self:
        start = (
            self.effective_from,
            self.effective_from_basis,
            self.effective_from_timing,
        )
        if self.status is AssertionStatus.SUPPORTED:
            if None in start:
                raise ValueError("a supported assertion has its interval's start")
            if self.effective_to is not None and self.effective_to <= start[0]:
                raise ValueError("effective_to must be after effective_from")
            if (self.effective_to is None) != (self.effective_to_timing is None):
                raise ValueError("effective_to and its timing come together")
        elif any(v is not None for v in (*start, self.effective_to)):
            raise ValueError("only a supported assertion carries an interval")
        if (self.issuer_id is None) != (self.cik is None):
            raise ValueError("issuer_id and cik come together")
        return self


class MembershipInterval(_Part):
    """A derived effective interval, ``[effective_from, effective_to)``."""

    security_id: IdPart
    effective_from: date
    effective_from_basis: BoundBasis
    effective_from_timing: BoundTiming
    effective_to: date | None
    effective_to_timing: BoundTiming | None
    assertion_ids: tuple[IdPart, ...]

    def contains(self, day: date) -> bool:
        """Membership on ``day`` at day precision; bound timings decide nothing here."""
        return self.effective_from <= day and (
            self.effective_to is None or day < self.effective_to
        )

    def overlaps(self, start: date, stop: date) -> bool:
        """True if the interval meets ``[start, stop)``."""
        return self.effective_from < stop and (
            self.effective_to is None or self.effective_to > start
        )


class IssuerCandidate(_Part):
    """A CIK that SEC's ticker list proposed for one cited ticker, and its check."""

    evidence_id: IdPart
    cited_name: NonBlankStr
    ticker: NonBlankStr
    cik: Cik
    sec_name: NonBlankStr
    ticker_listed: bool
    matched_name: str | None
    confirmed: bool
    citations: tuple[Citation, ...]

    @model_validator(mode="after")
    def _confirmed(self) -> Self:
        if self.confirmed != (self.ticker_listed and self.matched_name is not None):
            raise ValueError("confirmed means the ticker is listed and a name matched")
        return self


class IssuerMapping(_Part):
    """One security's issuer and CIK, or why it has none."""

    security_id: IdPart
    status: ResolutionStatus
    method: ResolutionMethod | None
    issuer_id: IdPart | None
    cik: Cik | None
    candidates: tuple[IssuerCandidate, ...]
    override_id: IdPart | None
    reason: str | None

    @model_validator(mode="after")
    def _resolved(self) -> Self:
        resolved = self.status is ResolutionStatus.RESOLVED
        fields = (self.method, self.issuer_id, self.cik)
        if resolved and None in fields:
            raise ValueError("a resolved mapping has a method, an issuer, and a CIK")
        if not resolved and any(v is not None for v in fields):
            raise ValueError("only a resolved mapping has an issuer and a CIK")
        by_override = self.method is ResolutionMethod.OVERRIDE or (
            self.status is ResolutionStatus.RETAINED_UNRESOLVED
        )
        if by_override != (self.override_id is not None):
            raise ValueError("an override_id is recorded exactly when one decided")
        if self.status is ResolutionStatus.RETAINED_UNRESOLVED and not self.reason:
            raise ValueError("a retained mapping records its reason")
        return self


class Issuer(_Part):
    """The derived issuer view: one row per CIK, however many securities it has."""

    issuer_id: IdPart
    cik: Cik
    sec_name: NonBlankStr
    former_names: tuple[str, ...]
    security_ids: tuple[IdPart, ...]


class OverrideCitation(_Part):
    """Evidence an override relies on; an artifact and locator when one is stored."""

    source_id: NonBlankStr
    url: NonBlankStr
    artifact_sha256: Sha256Hex | None = None
    locator: EvidenceLocator | None = None

    @model_validator(mode="after")
    def _artifact(self) -> Self:
        if self.locator is not None and self.artifact_sha256 is None:
            raise ValueError("a locator needs the artifact it points into")
        return self


_TARGETS = {
    OverrideKind.REJECT_ASSERTION: ("membership_assertion_id",),
    OverrideKind.SET_ISSUER: ("security_id", "cik"),
    OverrideKind.RETAIN_UNRESOLVED: ("security_id",),
    OverrideKind.ACKNOWLEDGE: ("finding_id", "finding_digest"),
    OverrideKind.HOLDING_ALIAS: ("security_id", "holding_name"),
}
_TARGET_FIELDS = sorted({name for names in _TARGETS.values() for name in names})


class Override(_Part):
    """A reviewed manual decision: evidence, rationale, reviewer, and effective
    dates (P §Issuer resolution). Never a parser branch."""

    override_id: IdPart
    kind: OverrideKind
    membership_assertion_id: IdPart | None = None
    security_id: IdPart | None = None
    cik: Cik | None = None
    finding_id: IdPart | None = None
    finding_digest: Sha256Hex | None = None
    holding_name: NonBlankStr | None = None
    citations: tuple[OverrideCitation, ...]
    rationale: NonBlankStr
    reviewer: NonBlankStr
    recorded_on: date
    effective_from: date
    effective_to: date | None = None

    @model_validator(mode="after")
    def _targets(self) -> Self:
        needs = _TARGETS[self.kind]
        present = {name for name in _TARGET_FIELDS if getattr(self, name) is not None}
        if present != set(needs):
            raise ValueError(f"a {self.kind} override sets exactly {list(needs)}")
        if self.kind is OverrideKind.SET_ISSUER and not self.citations:
            raise ValueError("a set_issuer override cites its evidence")
        if self.effective_to is not None and self.effective_to <= self.effective_from:
            raise ValueError("effective_to must be after effective_from")
        return self


class Finding(_Part):
    """One item of the coverage and conflict report."""

    finding_id: IdPart
    kind: FindingKind
    blocking: bool
    security_id: IdPart | None
    detail: NonBlankStr
    evidence_ids: tuple[str, ...]
    digest: Sha256Hex
    """SHA-256 of what the finding says, to which an acknowledgement is bound."""
    resolved_by: tuple[IdPart, ...]

    @property
    def holds_freeze(self) -> bool:
        return self.blocking and not self.resolved_by


class SnapshotReconciliation(_Part):
    """A dated snapshot compared with the reconstructed roster on its date."""

    snapshot_id: IdPart
    source_id: SourceId
    evidence_class: EvidenceClass
    as_of: date
    published_on: date
    withheld: bool
    matched: tuple[IdPart, ...]
    reconstructed_only: tuple[IdPart, ...]
    snapshot_only: tuple[IdPart, ...]
    unmatched: tuple[str, ...]
    citation: Citation | None

    @property
    def agrees(self) -> bool:
        return not (self.reconstructed_only or self.snapshot_only or self.unmatched)


class CohortReport(_Part):
    """The coverage and conflict report (P-A4)."""

    universe_id: IdPart
    anchor_evidence_id: IdPart | None
    limitations: tuple[str, ...]
    findings: tuple[Finding, ...]
    reconciliations: tuple[SnapshotReconciliation, ...]

    @property
    def blocking(self) -> tuple[Finding, ...]:
        """The findings that hold the freeze."""
        return tuple(finding for finding in self.findings if finding.holds_freeze)


class UniverseDefinition(_Part):
    """P §Data contracts, universe definition."""

    universe_id: IdPart
    universe_version: PositiveInt
    universe_name: IdPart
    period_end_start: date
    period_end_stop: date
    public_information_cutoff: date
    membership_reference: Literal["first_publication_time"]
    expected_member_count: PositiveInt
    source_register_version: Sha256Hex
    selection_policy_version: NonBlankStr
    content_hash: Sha256Hex
    created_at: AwareDatetime

    @model_validator(mode="after")
    def _window(self) -> Self:
        if not self.period_end_start < self.period_end_stop:
            raise ValueError("the window is empty")
        if self.public_information_cutoff < self.period_end_stop:
            raise ValueError("the cutoff falls inside the window")
        return self


class UniverseManifest(IngestionRecord):
    """The frozen cohort: everything Stage 5 joins against, with its report."""

    definition: UniverseDefinition
    sources: tuple[SourceRights, ...]
    securities: tuple[SecurityRecord, ...]
    assertions: tuple[MembershipAssertion, ...]
    intervals: tuple[MembershipInterval, ...]
    mappings: tuple[IssuerMapping, ...]
    issuers: tuple[Issuer, ...]
    candidate_issuer_ids: tuple[IdPart, ...]
    overrides: tuple[Override, ...]
    report: CohortReport


class LiveCheck(_Part):
    """One request of the opt-in live verification, and what it found."""

    source_id: SourceId
    purpose: Literal["terms", "evidence"]
    url: NonBlankStr
    outcome: Literal["unchanged", "changed", "refused", "failed"]
    detail: NonBlankStr
    retrieval: Retrieval | None


class LiveVerification(IngestionRecord):
    """The opt-in live verification's result (P-VL)."""

    checked_at: AwareDatetime
    checks: tuple[LiveCheck, ...]
    build_problems: tuple[str, ...]
    rebuilt_content_hash: Sha256Hex | None
    frozen_content_hash: Sha256Hex | None
    blocking_finding_ids: tuple[IdPart, ...]
