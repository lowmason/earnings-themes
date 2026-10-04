"""What an extraction run records (the Stage 7 spec, §Records; ES6, ES11, ES21,
ES22).

- **Versions.** Each stored record carries ``EXTRACTION_SCHEMA_VERSION``, apart
  from ``THEMES_SCHEMA_VERSION``, so an extraction change never re-versions the gold
  or the codebook (ES22). ``EXTRACTOR_VERSION`` names the unit rule, the planner,
  the labels, the reply contract, and the retry policy.
- **Quotes and claims.** A quote is one whole unit, verified: earnings-core's
  ``VerifiedSpan``, with the boilerplate masks over it. A cited unit gives one quote
  per document, never a copy, so the same quote keeps its ID in every run on the
  same document version (R9.9). A claim is the model's words and its quote IDs,
  with no theme (ES11).
- **Rejections.** Each pairs its subject with exactly one of a core ``Rejection`` or
  an extraction problem, so ``Rejection`` gains no field (ES6). Its detail may quote
  text, so it stays local, and ``str`` of one gives its reason and IDs only (GS13).
- **Coverage.** One visit per unit is R10.1's evidence that every eligible element
  was processed.
- **Configuration.** The adapter's identity, the policy, the ceilings, and the
  prompt and schema hashes: what every request of a run shares (R14.6).
"""

from enum import StrEnum
from typing import Annotated, Literal, Self

from earnings_core import Rejection, RejectionReason, VerifiedSpan
from pydantic import (
    AwareDatetime,
    Field,
    NonNegativeInt,
    PositiveInt,
    model_validator,
)

from earnings_themes.records import IdPart, NonBlank, Part, Sha256Hex

EXTRACTION_SCHEMA_VERSION = 1
EXTRACTOR_VERSION = "pointer-traversal/1"
"""Names the unit rule, the planner, the labels, the reply contract, and the retry
policy: change any of them, and this changes (the Stage 7 spec, §The cache key)."""
BILLABLE_COST = "none, self-hosted"


class ExtractionProblem(StrEnum):
    """Why the extractor refused a reply, a candidate, or a dispatch (§Records)."""

    MALFORMED_REPLY = "malformed_reply"
    """The reply is not JSON, or breaks the reply's schema."""
    TOOL_CALL_REFUSED = "tool_call_refused"
    """The reply carries a tool call, though no tool exists (R14.7)."""
    MODEL_MISMATCH = "model_mismatch"
    """The reply names a model other than the configured one, or none."""
    TRANSPORT_ERROR = "transport_error"
    """The reply never arrived."""
    REPLAY_MISS = "replay_miss"
    """Replay found no stored reply, and called nothing."""
    BUDGET_EXHAUSTED = "budget_exhausted"
    """A ceiling stopped the dispatch (ES21)."""
    UNKNOWN_LABEL = "unknown_label"
    """A label names no unit of the window."""
    DUPLICATE_LABEL = "duplicate_label"
    """A candidate repeats a label."""
    BLANK_CLAIM = "blank_claim"
    """A claim holds no non-space character."""
    CLAIM_TOO_LONG = "claim_too_long"
    """A claim is longer than the policy's claim limit."""


class WindowOutcome(StrEnum):
    COMPLETED = "completed"
    """At least one attempt brought a usable reply."""
    FAILED = "failed"
    """No attempt did."""


class DocumentOutcome(StrEnum):
    """R1.4's words for a document's extraction."""

    COMPLETED = "completed"
    """Every window completed, or the document has none."""
    PARTIAL = "partial"
    """Some windows failed."""
    FAILED = "failed"
    """Every window failed, or ``bundle_problems`` refused the document."""


class Parameters(Part):
    """A request's parameters; the defaults are provisional (§The adapter protocol)."""

    temperature: float = 0.0
    seed: int = 0
    max_tokens: PositiveInt = 2048
    structured: bool = True
    """Whether to ask for a JSON-schema response format (ES19)."""


class AdapterIdentity(Part):
    """Who answers a request, as the cache key and the run record name it (R14.6)."""

    adapter_kind: NonBlank
    model_id: NonBlank
    weights_sha256: Sha256Hex | None = None
    runtime: NonBlank | None = None
    runtime_version: NonBlank | None = None


class ExtractionPolicy(Part):
    """How a run extracts; each value is provisional, not a quality threshold."""

    parameters: Parameters = Parameters()
    window_budget: PositiveInt | None = 4000
    """Characters of unit text per window; ``None`` packs one window (ES13)."""
    claim_limit: PositiveInt = 500
    """The longest claim, in characters."""


class Ceilings(Part):
    """A run's ceilings, each passed explicitly: none has a default (ES21; A §691)."""

    requests_per_document: PositiveInt
    requests_per_run: PositiveInt
    tokens_per_run: PositiveInt


class RunConfiguration(Part):
    """What every request of a run shares: the key components common to it."""

    identity: AdapterIdentity
    policy: ExtractionPolicy
    ceilings: Ceilings
    prompt_sha256: Sha256Hex
    reply_schema_sha256: Sha256Hex
    extractor_version: NonBlank
    validator_version: NonBlank
    codebook_hash: Sha256Hex | None = None
    """Null under codebook-free extraction (ES11)."""


class ExtractionRecord(Part):
    """A stored record, which carries its schema version (ES22)."""

    schema_version: Literal[1] = EXTRACTION_SCHEMA_VERSION


class Quote(ExtractionRecord):
    """One cited unit, verified exactly (R6.1)."""

    quote_id: NonBlank
    span: VerifiedSpan
    mask_ids: tuple[NonBlank, ...] = ()

    @model_validator(mode="after")
    def _id_is_the_span(self) -> Self:
        expected = f"q-{self.span.start}-{self.span.end}"
        if self.quote_id != expected:
            raise ValueError(f"quote_id {self.quote_id!r} is not {expected!r}")
        return self


class Claim(ExtractionRecord):
    """A candidate that verified: the model's words and the quotes they rest on."""

    claim_id: NonBlank
    doc_id: NonBlank
    window_id: NonBlank
    attempt: PositiveInt
    claim: NonBlank
    quote_ids: Annotated[tuple[NonBlank, ...], Field(min_length=1)]


class ExtractionRejection(ExtractionRecord):
    """A refusal and its subject: a core ``Rejection`` from verification or
    ``bundle_problems``, or an extraction problem, never both (ES6)."""

    doc_id: NonBlank
    window_id: NonBlank | None = None
    attempt: PositiveInt | None = None
    candidate_index: NonNegativeInt | None = None
    labels: tuple[str, ...] = ()
    """As the reply gave them, which may hold any text."""
    element_ids: tuple[NonBlank, ...] = ()
    rejection: Rejection | None = None
    problem: ExtractionProblem | None = None
    detail: str = ""
    """A problem's field paths, never a value."""

    @model_validator(mode="after")
    def _one_reason(self) -> Self:
        if (self.rejection is None) == (self.problem is None):
            raise ValueError("a rejection holds exactly one of rejection and problem")
        return self

    @property
    def reason(self) -> str:
        """The core rejection's reason, or the problem."""
        if self.rejection is not None:
            return self.rejection.reason.value
        return str(self.problem)

    def __str__(self) -> str:
        """Its IDs and reason, never a detail or a label, which may quote text."""
        subject = [self.doc_id]
        if self.window_id is not None:
            subject.append(self.window_id)
        if self.attempt is not None:
            subject.append(f"attempt {self.attempt}")
        if self.candidate_index is not None:
            subject.append(f"candidate {self.candidate_index}")
        subject += self.element_ids
        return f"{' '.join(subject)}: {self.reason}"


class Visit(ExtractionRecord):
    """One unit's visit, R10.1's coverage evidence."""

    doc_id: NonBlank
    element_id: NonBlank
    window_id: NonBlank
    outcome: WindowOutcome
    reason: ExtractionProblem | None = None
    """Why its window failed."""

    @model_validator(mode="after")
    def _reason_when_failed(self) -> Self:
        if (self.outcome is WindowOutcome.FAILED) != (self.reason is not None):
            raise ValueError("a failed visit has a reason, and a completed one none")
        return self


class WindowRecord(ExtractionRecord):
    """One window: its plan, its attempts, and what it spent."""

    doc_id: NonBlank
    window_id: NonBlank
    start: NonNegativeInt
    end: NonNegativeInt
    unit_ids: Annotated[tuple[NonBlank, ...], Field(min_length=1)]
    """In label order: ``U1`` names the first."""
    context_id: NonBlank | None = None
    attempts: NonNegativeInt
    """Dispatched attempts: requests, cache hits, and replay misses."""
    outcome: WindowOutcome
    reason: ExtractionProblem | None = None
    requests: NonNegativeInt
    cache_hits: NonNegativeInt
    prompt_tokens: NonNegativeInt
    completion_tokens: NonNegativeInt
    unreported: NonNegativeInt
    """Requests whose reply reported no usage."""
    latency_ms: NonNegativeInt
    exhausted: bool
    """Whether a ceiling stopped one of its dispatches."""

    @model_validator(mode="after")
    def _reason_when_failed(self) -> Self:
        if (self.outcome is WindowOutcome.FAILED) != (self.reason is not None):
            raise ValueError("a failed window has a reason, and a completed one none")
        return self


class DocumentRecord(ExtractionRecord):
    """One document's outcome and counts."""

    doc_id: NonBlank
    canonical_hash: Sha256Hex
    outcome: DocumentOutcome
    units: NonNegativeInt
    windows: NonNegativeInt
    windows_failed: NonNegativeInt
    candidates: NonNegativeInt
    quotes: NonNegativeInt
    claims: NonNegativeInt
    rejections: NonNegativeInt


REASONS = frozenset(
    {reason.value for reason in RejectionReason}
    | {problem.value for problem in ExtractionProblem}
)


class RunRecord(ExtractionRecord):
    """One run: its configuration, its documents, its counts, and what it spent."""

    run_id: IdPart
    started_at: AwareDatetime
    configuration: RunConfiguration
    configuration_hash: Sha256Hex
    documents: dict[NonBlank, Sha256Hex]
    """Each document's ``doc_id`` and canonical hash."""
    units: NonNegativeInt
    windows: NonNegativeInt
    candidates: NonNegativeInt
    quotes: NonNegativeInt
    claims: NonNegativeInt
    rejections_by_reason: dict[NonBlank, PositiveInt]
    requests: NonNegativeInt
    cache_hits: NonNegativeInt
    prompt_tokens: NonNegativeInt
    completion_tokens: NonNegativeInt
    unreported: NonNegativeInt
    exhausted: bool
    software: dict[NonBlank, NonBlank]
    """The software identity the caller passes."""
    billable_cost: Literal["none, self-hosted"] = BILLABLE_COST
    exactness_rate: float | None
    """1.0 over the retained quotes, each verified; none when no quote is retained
    (R6.2, R12.8)."""

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        unknown = sorted(set(self.rejections_by_reason) - REASONS)
        if unknown:
            raise ValueError(f"unknown rejection reasons {unknown}")
        expected = 1.0 if self.quotes else None
        if self.exactness_rate != expected:
            raise ValueError(f"exactness_rate is {expected} over {self.quotes} quotes")
        return self
