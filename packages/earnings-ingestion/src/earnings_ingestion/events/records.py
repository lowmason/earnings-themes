"""Stage 5's records: the event manifest, its evidence record, the overrides, and the
pilot manifest (the Stage 5 spec, §The event manifest, §Review overrides, and §Pilot
selection).

- **Rows.** An ``EventRow`` is one slot: an issuer's period end, the periodic report
  that made it, the release filing that first published its results, and its
  eligibility. One row serves as P's expected event and Stage 15's ledger entry.
- **The manifest.** ``EventManifest`` holds the definition, the rows, the findings,
  and the overrides applied. Its content hash covers them, less the definition's
  version, hash, creation time, and ``universe_version`` (plan 7, P7-2).
- **Evidence.** ``EventEvidence`` sits beside a frozen manifest, outside its hash, and
  cites what each row rests on (EV11). A re-fetch changes it and nothing else.
- **Overrides.** ``EventOverride`` is a reviewer's signed decision, read strictly from
  ``overrides.toml`` like Stage 4's (P6-18).
- **The pilot.** ``PilotManifest`` is ``djia-pilot/1``'s frozen selection: its rows in
  the order taken, each with its reason, and the transitions it could not cover. Its
  content hash leaves out the same fields as the event manifest's.

These are ingestion records and join ingestion schema version 1 (P6-5). A committed
record carries facts, URLs, hashes, and locators, never a source's wording (P6-3).
Rows, findings, and overrides carry facts only, never a retrieval time or a pointer
into one saved file, so a re-fetch never re-versions a manifest.
docs/data-dictionary.md documents every field and value.
"""

from collections import Counter
from datetime import date, timedelta
from enum import StrEnum
from typing import Annotated, Literal, Self

from earnings_core.artifacts import NonBlankStr
from earnings_core.documents import IdPart
from earnings_core.hashing import Sha256Hex
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    NonNegativeInt,
    PositiveInt,
    StringConstraints,
    model_validator,
)

from earnings_ingestion.canonical.records import IngestionRecord
from earnings_ingestion.cohort.digests import digest
from earnings_ingestion.cohort.records import Citation, OverrideCitation
from earnings_ingestion.events.acceptance import Convention
from earnings_ingestion.sec.identifiers import Cik

Accession = Annotated[str, StringConstraints(pattern=r"^[0-9]{10}-[0-9]{2}-[0-9]{6}$")]
PeriodicForm = Literal["10-Q", "10-K", "10-QT", "10-KT"]


class _Part(BaseModel):
    """A nested part of an event record: immutable, closed, strictly typed."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class EventStatus(StrEnum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    AMBIGUOUS = "ambiguous"


class EventReason(StrEnum):
    """Why an event has its status: the first of ``eligibility/1``'s checks that
    applies decides (S §Eligibility)."""

    PERIOD_END_OUTSIDE_WINDOW = "period_end_outside_window"
    NO_RELEASE_FILING = "no_release_filing"
    SEVERAL_RELEASE_FILINGS = "several_release_filings"
    PUBLISHED_AFTER_CUTOFF = "published_after_cutoff"
    MEMBER_AT_PUBLICATION = "member_at_publication"
    NOT_MEMBER_AT_PUBLICATION = "not_member_at_publication"
    SAME_DAY_TRANSITION = "same_day_transition"


STATUS_OF = {
    EventReason.PERIOD_END_OUTSIDE_WINDOW: EventStatus.INELIGIBLE,
    EventReason.NO_RELEASE_FILING: EventStatus.AMBIGUOUS,
    EventReason.SEVERAL_RELEASE_FILINGS: EventStatus.AMBIGUOUS,
    EventReason.PUBLISHED_AFTER_CUTOFF: EventStatus.INELIGIBLE,
    EventReason.MEMBER_AT_PUBLICATION: EventStatus.ELIGIBLE,
    EventReason.NOT_MEMBER_AT_PUBLICATION: EventStatus.INELIGIBLE,
    EventReason.SAME_DAY_TRANSITION: EventStatus.AMBIGUOUS,
}
UNIDENTIFIED = frozenset(
    {EventReason.NO_RELEASE_FILING, EventReason.SEVERAL_RELEASE_FILINGS}
)
DECIDED_BY_MEMBERSHIP = frozenset(
    {
        EventReason.MEMBER_AT_PUBLICATION,
        EventReason.NOT_MEMBER_AT_PUBLICATION,
        EventReason.SAME_DAY_TRANSITION,
    }
)


class IdentificationMethod(StrEnum):
    """How the release filing was identified (``release-id/1``)."""

    STATED_PERIOD = "stated_period"
    """The one candidate left, whose Item 2.02 text states the slot's period."""
    SOLE_CANDIDATE = "sole_candidate"
    """The one candidate left, whose text states no period that is judged."""
    OVERRIDE = "override"
    """A reviewer's ``set_release_filing``."""


class EventFindingKind(StrEnum):
    PERIOD_GAP = "period_gap"
    """An in-window period end may be missing (S §Slots)."""
    NO_SLOTS = "no_slots"
    """A candidate issuer with no slot."""
    FISCAL_LABELS_UNKNOWN = "fiscal_labels_unknown"
    """Companyfacts gives the periodic report no agreeing ``fy`` and ``fp``."""
    ACCEPTANCE_TIME_MISMATCH = "acceptance_time_mismatch"
    """A submissions ``acceptanceDateTime`` follows neither convention (EV10)."""
    ACCEPTANCE_TIME_UNKNOWN = "acceptance_time_unknown"
    """A filing whose side of the cutoff, or whose range, turns on a convention its
    file does not establish, or on a missing value (plan 7, P7-8)."""


BLOCKING = frozenset(
    {
        EventFindingKind.PERIOD_GAP,
        EventFindingKind.NO_SLOTS,
        EventFindingKind.ACCEPTANCE_TIME_MISMATCH,
        EventFindingKind.ACCEPTANCE_TIME_UNKNOWN,
    }
)
ACKNOWLEDGEABLE = frozenset({EventFindingKind.PERIOD_GAP, EventFindingKind.NO_SLOTS})


class EventOverrideKind(StrEnum):
    SET_RELEASE_FILING = "set_release_filing"
    """Name an event's release filing, citing it."""
    RETAIN_UNRESOLVED = "retain_unresolved"
    """Keep an ``ambiguous`` event with its reason, excluded from the pilot."""
    ACKNOWLEDGE = "acknowledge"
    """Accept one ``period_gap`` or ``no_slots`` finding, bound to its digest."""


class EventRow(_Part):
    """One slot: an issuer's period end, its release filing, and its eligibility."""

    event_id: IdPart
    issuer_id: IdPart
    cik: Cik
    period_end: date
    reported_fiscal_year: int | None
    reported_fiscal_quarter: NonBlankStr | None
    periodic_accession: Accession
    periodic_form: PeriodicForm
    release_accession: Accession | None
    candidate_accessions: tuple[Accession, ...]
    identification_method: IdentificationMethod | None
    filing_acceptance_time: AwareDatetime | None
    first_publication_time: AwareDatetime | None
    source_timezone: Literal["America/New_York"]
    first_publication_source_id: Literal["sec-edgar"] | None
    membership_assertion_id: IdPart | None
    eligibility_status: EventStatus
    eligibility_reason: EventReason
    retained: bool
    override_ids: tuple[IdPart, ...]

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.event_id != f"{self.issuer_id}:{self.period_end.isoformat()}":
            raise ValueError("event_id is <issuer_id>:<period_end>")
        labels = (self.reported_fiscal_year, self.reported_fiscal_quarter)
        if (labels[0] is None) != (labels[1] is None):
            raise ValueError("the fiscal labels are known or unknown together")
        release = (
            self.release_accession,
            self.identification_method,
            self.filing_acceptance_time,
            self.first_publication_time,
            self.first_publication_source_id,
        )
        if len({value is None for value in release}) != 1:
            raise ValueError("a release filing comes with its method and its times")
        if len(set(self.candidate_accessions)) != len(self.candidate_accessions):
            raise ValueError("candidate_accessions name each candidate once")
        if self.first_publication_time != self.filing_acceptance_time:
            raise ValueError("first publication is the filing's acceptance (EV9)")
        acceptance = self.filing_acceptance_time
        if acceptance is not None and acceptance.utcoffset() != timedelta(0):
            raise ValueError("times are stored as UTC instants")
        if STATUS_OF[self.eligibility_reason] is not self.eligibility_status:
            raise ValueError(f"{self.eligibility_reason} gives another status")
        if (self.eligibility_reason in UNIDENTIFIED) != (
            self.release_accession is None
            and self.eligibility_reason is not EventReason.PERIOD_END_OUTSIDE_WINDOW
        ):
            raise ValueError("only an unidentified release filing lacks one")
        if self.retained and self.eligibility_status is not EventStatus.AMBIGUOUS:
            raise ValueError("only an ambiguous event is retained")
        decided = self.eligibility_reason in DECIDED_BY_MEMBERSHIP
        if decided != (self.membership_assertion_id is not None):
            raise ValueError(
                "membership_assertion_id names the assertion that decided membership,"
                " and is null when an earlier check decided"
            )
        return self


class EventFinding(_Part):
    """One item of the event build's report."""

    finding_id: IdPart
    kind: EventFindingKind
    blocking: bool
    issuer_id: IdPart | None
    detail: NonBlankStr
    digest: Sha256Hex
    """SHA-256 of what the finding says, to which an acknowledgement is bound."""
    resolved_by: tuple[IdPart, ...]

    @property
    def holds_freeze(self) -> bool:
        return self.blocking and not self.resolved_by


def event_finding(
    kind: EventFindingKind,
    subject: str,
    detail: str,
    *,
    issuer_id: str | None = None,
) -> EventFinding:
    """A finding with id ``<kind>:<subject>`` and the digest of its content."""
    blocking = kind in BLOCKING
    content = {
        "kind": kind.value,
        "subject": subject,
        "detail": detail,
        "blocking": blocking,
        "issuer_id": issuer_id,
    }
    return EventFinding(
        finding_id=f"{kind.value}:{subject}",
        kind=kind,
        blocking=blocking,
        issuer_id=issuer_id,
        detail=detail,
        digest=digest(content),
        resolved_by=(),
    )


_TARGETS = {
    EventOverrideKind.SET_RELEASE_FILING: ("event_id", "accession"),
    EventOverrideKind.RETAIN_UNRESOLVED: ("event_id", "reason"),
    EventOverrideKind.ACKNOWLEDGE: ("finding_id", "finding_digest"),
}
_TARGET_FIELDS = sorted({name for names in _TARGETS.values() for name in names})


class EventOverride(_Part):
    """A reviewer's decision about one event or finding (S §Review overrides)."""

    override_id: IdPart
    kind: EventOverrideKind
    event_id: IdPart | None = None
    accession: Accession | None = None
    reason: EventReason | None = None
    finding_id: IdPart | None = None
    finding_digest: Sha256Hex | None = None
    citations: tuple[OverrideCitation, ...] = ()
    rationale: NonBlankStr
    reviewer: NonBlankStr
    recorded_on: date

    @model_validator(mode="after")
    def _targets(self) -> Self:
        needs = _TARGETS[self.kind]
        present = {name for name in _TARGET_FIELDS if getattr(self, name) is not None}
        if present != set(needs):
            raise ValueError(f"a {self.kind} override sets exactly {list(needs)}")
        if self.kind is EventOverrideKind.SET_RELEASE_FILING and not self.citations:
            raise ValueError("a set_release_filing override cites the filing")
        if (
            self.kind is EventOverrideKind.RETAIN_UNRESOLVED
            and STATUS_OF[self.reason] is not EventStatus.AMBIGUOUS
        ):
            raise ValueError("retain_unresolved keeps an ambiguous reason")
        return self


class EventOverridesFile(_Part):
    """``config/corpus/<corpus_id>/overrides.toml``."""

    schema_version: Literal[1]
    overrides: tuple[EventOverride, ...] = ()

    @model_validator(mode="after")
    def _distinct(self) -> Self:
        ids = Counter(override.override_id for override in self.overrides)
        if repeated := sorted(name for name, count in ids.items() if count > 1):
            raise ValueError(f"override_id repeated: {repeated}")
        events = Counter(
            (override.event_id, override.kind.value)
            for override in self.overrides
            if override.event_id is not None
        )
        repeated = [f"{event} ({kind})" for (event, kind), n in events.items() if n > 1]
        if repeated:
            raise ValueError(f"event_id repeated in one kind: {sorted(repeated)}")
        return self


class EventManifestDefinition(_Part):
    """The event manifest's definition (S §The event manifest)."""

    corpus_id: IdPart
    event_manifest_version: PositiveInt
    universe_id: IdPart
    universe_version: PositiveInt
    universe_operative_hash: Sha256Hex
    discovery_policy_version: NonBlankStr
    eligibility_policy_version: NonBlankStr
    public_information_cutoff: date
    content_hash: Sha256Hex
    created_at: AwareDatetime


UNHASHED = frozenset(
    {"event_manifest_version", "universe_version", "content_hash", "created_at"}
)


class EventManifest(IngestionRecord):
    """The frozen event manifest: P's expected events and Stage 15's ledger."""

    definition: EventManifestDefinition
    rows: tuple[EventRow, ...]
    findings: tuple[EventFinding, ...]
    overrides: tuple[EventOverride, ...]

    @model_validator(mode="after")
    def _sorted(self) -> Self:
        for name, keys in (
            ("rows", [row.event_id for row in self.rows]),
            ("findings", [finding.finding_id for finding in self.findings]),
            ("overrides", [override.override_id for override in self.overrides]),
        ):
            if keys != sorted(set(keys)):
                raise ValueError(f"{name} are unique and sorted by id")
        return self


def content_hash(manifest: EventManifest) -> str:
    """SHA-256 of the canonical JSON of the definition, less ``UNHASHED``, with the
    rows, the findings, and the overrides."""
    definition = manifest.definition.model_dump(mode="json", exclude=set(UNHASHED))
    return digest(
        {
            "definition": definition,
            "rows": [row.model_dump(mode="json") for row in manifest.rows],
            "findings": [f.model_dump(mode="json") for f in manifest.findings],
            "overrides": [o.model_dump(mode="json") for o in manifest.overrides],
        }
    )


class FileEvidence(_Part):
    """A submissions file or older page the build read, and its convention."""

    url: NonBlankStr
    sha256: Sha256Hex
    retrieved_at: AwareDatetime
    convention: Convention | None
    """``None`` when no row was cross-checked, or its rows follow both conventions."""
    rows_cross_checked: NonNegativeInt


class SkippedPage(_Part):
    """An older page the build did not read, and the dates that left it out."""

    url: NonBlankStr
    filing_from: date
    filing_to: date


class EventCitations(_Part):
    """What one event rests on (S §The event manifest, the evidence record)."""

    event_id: IdPart
    periodic_row: Citation
    """The periodic report's submissions row."""
    labels: Citation | None
    """Its companyfacts ``fy`` and ``fp``; ``None`` when unknown."""
    candidates: tuple[Citation, ...]
    """Each candidate's index page, at its Accepted value."""
    amendments: tuple[Citation, ...]
    """Each 8-K/A in the slot's range, recorded and never chosen by the rule."""
    release: Citation | None
    """The release filing's index page, at its Accepted value."""
    item_text: Citation | None
    """The release's Item 2.02 text, in its primary document's walker-1 text."""
    cross_check: Citation | None
    """The release's submissions row, at ``acceptanceDateTime``."""


class EventEvidence(IngestionRecord):
    """``events-v<N>.evidence.json``: the citations beside a frozen manifest (EV11)."""

    corpus_id: IdPart
    event_manifest_version: PositiveInt
    event_manifest_hash: Sha256Hex
    limitations: tuple[NonBlankStr, ...]
    files: tuple[FileEvidence, ...]
    skipped_pages: tuple[SkippedPage, ...]
    events: tuple[EventCitations, ...]


class SelectionReason(StrEnum):
    """Why ``djia-pilot/1`` took an event (S §Pilot selection)."""

    ISSUER_COVERAGE = "issuer_coverage"
    """Step 1: the issuer's event from the quarter with the fewest selections."""
    MEMBERSHIP_BOUNDARY = "membership_boundary"
    """Step 2: the nearest eligible event on a transition's member side."""
    QUARTER_COVERAGE = "quarter_coverage"
    """Step 3: an event of a quarter that had no selection."""
    LONGITUDINAL_FILL = "longitudinal_fill"
    """Step 5: the event farthest from its issuer's nearest selected period end."""


class TransitionKind(StrEnum):
    ENTRY = "entry"
    """The issuer's membership starts."""
    EXIT = "exit"
    """The issuer's membership ends."""


class PilotRow(_Part):
    """One selected event."""

    event_id: IdPart
    selection_order: PositiveInt
    selection_reason: SelectionReason


class MembershipTransition(_Part):
    """An issuer-level entry or exit (S §Pilot selection, step 2)."""

    issuer_id: IdPart
    kind: TransitionKind
    effective_date: date
    assertion_ids: tuple[IdPart, ...]
    """The assertions that set the bound."""


class PilotDefinition(_Part):
    """The pilot manifest's definition (S §Pilot selection)."""

    pilot_id: IdPart
    pilot_version: PositiveInt
    universe_version: PositiveInt
    universe_operative_hash: Sha256Hex
    event_manifest_version: PositiveInt
    eligible_event_manifest_hash: Sha256Hex
    selection_policy_version: NonBlankStr
    selection_seed: Sha256Hex
    target: PositiveInt
    underfilled: bool
    content_hash: Sha256Hex
    created_at: AwareDatetime


PILOT_UNHASHED = frozenset(
    {"pilot_version", "universe_version", "content_hash", "created_at"}
)


class PilotManifest(IngestionRecord):
    """The frozen pilot: the events to acquire, in the order taken."""

    definition: PilotDefinition
    rows: tuple[PilotRow, ...]
    unmatched_transitions: tuple[MembershipTransition, ...]
    """Each transition in scope with no eligible event on its member side, within
    the membership spell it opens or closes."""

    @model_validator(mode="after")
    def _ordered(self) -> Self:
        orders = [row.selection_order for row in self.rows]
        if orders != list(range(1, len(self.rows) + 1)):
            raise ValueError("rows are in selection order, from 1")
        if len({row.event_id for row in self.rows}) != len(self.rows):
            raise ValueError("an event is selected once")
        if len(self.rows) != self.definition.target:
            raise ValueError("the pilot holds its target")
        keys = [
            (t.effective_date, t.issuer_id, t.kind) for t in self.unmatched_transitions
        ]
        if keys != sorted(set(keys)):
            raise ValueError(
                "transitions are unique and sorted by date, issuer, and kind"
            )
        return self


def pilot_content_hash(manifest: PilotManifest) -> str:
    """SHA-256 of the canonical JSON of the definition, less ``PILOT_UNHASHED``, with
    the rows and the unmatched transitions."""
    definition = manifest.definition.model_dump(
        mode="json", exclude=set(PILOT_UNHASHED)
    )
    return digest(
        {
            "definition": definition,
            "rows": [row.model_dump(mode="json") for row in manifest.rows],
            "unmatched_transitions": [
                t.model_dump(mode="json") for t in manifest.unmatched_transitions
            ],
        }
    )
