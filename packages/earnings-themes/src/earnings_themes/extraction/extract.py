"""Pointer extraction over one window (the Stage 7 spec, §Retries, §Ceilings, §Span
verification, and §Records; ES16, ES20, ES21).

- **The window.** ``extract_window`` is a pure function of its job, the adapter, and
  the policy, so a graph node can wrap it unchanged (Stage 15). It makes at most
  ``MAX_ATTEMPTS`` attempts:
  - A reply that never arrived, or that the adapter or the extractor refused
    (``transport_error``, ``replay_miss``, ``tool_call_refused``, or
    ``model_mismatch``), is recorded, and the same messages are sent again. Their
    key is unchanged, so a live run's recovery replays from the cache at once.
  - A reply that is not JSON, or breaks the schema, is ``malformed_reply``. The next
    attempt adds it as a turn, with feedback that names each problem by its field.
  - A candidate with an unknown or repeated label, or a blank or overlong claim, is
    refused. Every refused candidate is a rejection at its attempt, and the next
    attempt asks for corrected versions, which are new candidates: a correction is
    never a patch of the refused one (R6.2).
  - The window completes when an attempt brings a usable reply, and fails otherwise.
- **Verification.** In plain code, after the reply is parsed: each label maps to its
  element, ``resolve_pointer`` gives the span, and the candidate is built from the
  canonical slice with ``make_locator``'s context, then parsed and validated. A
  candidate stands only if every label verifies; otherwise the whole candidate is
  rejected with the first reason, since dropping one quote could change what the
  claim rests on (ES20).
- **Ceilings.** Each dispatch is first checked against what the window may still
  spend. A blocked dispatch is ``budget_exhausted`` and ends the window's attempts.
  A cache hit or a replay miss is not a request. A reply the adapter refused is one,
  with its usage, and a reply that reports no usage binds only the request ceilings
  (ES21; A §691).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from earnings_core import (
    VALIDATOR_VERSION,
    Rejection,
    TextSpan,
    VerifiedSpan,
    make_locator,
    parse_span_candidate,
    resolve_pointer,
    validate_span,
)

from earnings_themes.anchoring import Bundle, mask_id
from earnings_themes.extraction.adapters import (
    AdapterError,
    Message,
    ModelAdapter,
    ModelReply,
    ModelRequest,
    RequestSubject,
)
from earnings_themes.extraction.prompt import (
    REPLY_SCHEMA,
    CandidateReply,
    PromptTemplate,
    Reply,
    parse_reply,
    refused_feedback,
    render_messages,
    unusable_feedback,
)
from earnings_themes.extraction.records import (
    EXTRACTOR_VERSION,
    Claim,
    ExtractionPolicy,
    ExtractionProblem,
    ExtractionRejection,
    Quote,
    Visit,
    WindowOutcome,
    WindowRecord,
)
from earnings_themes.extraction.windows import Window

MAX_ATTEMPTS = 2
"""At most 2 attempts per window, provisional (ES16)."""


@dataclass(frozen=True)
class Allowance:
    """What a window or a document may still spend: requests, and reported tokens."""

    requests: int
    tokens: int


@dataclass(frozen=True)
class WindowJob:
    """One window to extract: its bundle, its plan, the prompt, and its allowance."""

    bundle: Bundle
    window: Window
    template: PromptTemplate
    allowance: Allowance


@dataclass(frozen=True)
class WindowResult:
    """One window's outcome: its record, the claims and quotes it kept, its
    rejections, one visit per unit, and how many candidates its replies held."""

    record: WindowRecord
    claims: tuple[Claim, ...]
    quotes: tuple[Quote, ...]
    rejections: tuple[ExtractionRejection, ...]
    visits: tuple[Visit, ...]
    candidates: int


@dataclass
class _Spent:
    requests: int = 0
    cache_hits: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    unreported: int = 0
    latency_ms: int = 0

    @property
    def tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def add(self, reply: ModelReply) -> None:
        if reply.cached:
            self.cache_hits += 1
            return
        self.requests += 1
        self.latency_ms += reply.latency_ms
        if reply.usage is None:
            self.unreported += 1
        else:
            self.prompt_tokens += reply.usage.prompt_tokens
            self.completion_tokens += reply.usage.completion_tokens


def subject_of(job: WindowJob, policy: ExtractionPolicy) -> RequestSubject:
    """What the window's requests are about: the rest of the R14.6 key."""
    document, window = job.bundle.document, job.window
    return RequestSubject(
        doc_id=document.doc_id,
        canonical_hash=document.canonical_hash,
        window_id=window.window_id,
        unit_ids=window.unit_ids,
        window_budget=policy.window_budget,
        claim_limit=policy.claim_limit,
        prompt_sha256=job.template.sha256,
        extractor_version=EXTRACTOR_VERSION,
        validator_version=VALIDATOR_VERSION,
        codebook_hash=None,
    )


def refusal(
    candidate: CandidateReply, labels: Mapping[str, str], claim_limit: int
) -> ExtractionProblem | None:
    """Why a parsed candidate is refused before verification, or ``None``."""
    given = candidate.quote_labels
    if any(label not in labels for label in given):
        return ExtractionProblem.UNKNOWN_LABEL
    if len(set(given)) != len(given):
        return ExtractionProblem.DUPLICATE_LABEL
    if not candidate.claim.strip():
        return ExtractionProblem.BLANK_CLAIM
    if len(candidate.claim) > claim_limit:
        return ExtractionProblem.CLAIM_TOO_LONG
    return None


def verify(
    bundle: Bundle, element_ids: Sequence[str]
) -> tuple[VerifiedSpan, ...] | Rejection:
    """Each element's span, sliced and verified by code, or the first refusal."""
    document, elements = bundle.document, bundle.elements
    spans = []
    for element_id in element_ids:
        span = resolve_pointer(document, elements, element_id)
        if isinstance(span, Rejection):
            return span
        locator = make_locator(document, span)
        candidate = parse_span_candidate(
            {
                "doc_id": document.doc_id,
                "canonical_hash": document.canonical_hash,
                "start": span.start,
                "end": span.end,
                "quote_text": span.slice_of(document.canonical_text),
                "element_id": element_id,
                "prefix": locator.prefix,
                "suffix": locator.suffix,
            }
        )
        if isinstance(candidate, Rejection):
            return candidate
        verified = validate_span(document, elements, candidate)
        if isinstance(verified, Rejection):
            return verified
        spans.append(verified)
    return tuple(spans)


def masks_over(bundle: Bundle, span: TextSpan) -> tuple[str, ...]:
    """The IDs of the boilerplate masks over ``span``."""
    return tuple(sorted(mask_id(m) for m in bundle.masks if m.span.overlaps(span)))


def extract_window(
    job: WindowJob, adapter: ModelAdapter, policy: ExtractionPolicy
) -> WindowResult:
    """One window's claims, quotes, rejections, and visits. An ``AdapterError`` is
    the window's to record; any other error, such as a cached entry that does not
    read, propagates and ends the run."""
    bundle, window = job.bundle, job.window
    doc_id = bundle.document.doc_id
    labels = window.labels
    system, user = render_messages(
        job.template, bundle, window, structured=policy.parameters.structured
    )
    messages = (
        Message(role="system", content=system),
        Message(role="user", content=user),
    )
    subject = subject_of(job, policy)
    spent = _Spent()
    rejections: list[ExtractionRejection] = []
    claims: list[Claim] = []
    quotes: dict[str, Quote] = {}
    candidates = attempts = 0
    usable, exhausted = False, False
    reason: ExtractionProblem | None = None

    def refuse(
        attempt: int,
        problem: ExtractionProblem,
        index: int | None = None,
        given: tuple[str, ...] = (),
        detail: str = "",
    ) -> None:
        rejections.append(
            ExtractionRejection(
                doc_id=doc_id,
                window_id=window.window_id,
                attempt=attempt,
                candidate_index=index,
                labels=given,
                element_ids=tuple(labels[g] for g in given if g in labels),
                problem=problem,
                detail=detail,
            )
        )

    for attempt in range(1, MAX_ATTEMPTS + 1):
        if (
            spent.requests >= job.allowance.requests
            or spent.tokens >= job.allowance.tokens
        ):
            exhausted = True
            refuse(attempt, ExtractionProblem.BUDGET_EXHAUSTED)
            reason = reason if usable else ExtractionProblem.BUDGET_EXHAUSTED
            break
        request = ModelRequest(
            messages=messages,
            reply_schema=REPLY_SCHEMA,
            parameters=policy.parameters,
            subject=subject,
        )
        attempts += 1
        try:
            reply = adapter.complete(request)
        except AdapterError as error:
            if error.reply is not None:
                spent.add(error.reply)
            elif error.problem is not ExtractionProblem.REPLAY_MISS:
                spent.requests += 1
            refuse(attempt, error.problem)
            reason = reason if usable else error.problem
            continue
        spent.add(reply)
        if reply.tool_calls or reply.model != adapter.identity.model_id:
            problem = (
                ExtractionProblem.TOOL_CALL_REFUSED
                if reply.tool_calls
                else ExtractionProblem.MODEL_MISMATCH
            )
            refuse(attempt, problem)
            reason = reason if usable else problem
            continue
        parsed = parse_reply(reply.text)
        turn = Message(role="assistant", content=reply.text)
        if not isinstance(parsed, Reply):
            refuse(attempt, ExtractionProblem.MALFORMED_REPLY, detail="; ".join(parsed))
            reason = reason if usable else ExtractionProblem.MALFORMED_REPLY
            feedback = Message(role="user", content=unusable_feedback(parsed))
            messages = (*messages, turn, feedback)
            continue
        usable, reason = True, None
        refused = []
        for index, candidate in enumerate(parsed.candidates):
            candidates += 1
            given = candidate.quote_labels
            problem = refusal(candidate, labels, policy.claim_limit)
            if problem is not None:
                refused.append((index, given, problem))
                refuse(attempt, problem, index, given)
                continue
            element_ids = tuple(labels[g] for g in given)
            verified = verify(bundle, element_ids)
            if isinstance(verified, Rejection):
                rejections.append(
                    ExtractionRejection(
                        doc_id=doc_id,
                        window_id=window.window_id,
                        attempt=attempt,
                        candidate_index=index,
                        labels=given,
                        element_ids=element_ids,
                        rejection=verified,
                    )
                )
                continue
            ids = []
            for span in verified:
                quote_id = f"q-{span.start}-{span.end}"
                ids.append(quote_id)
                if quote_id not in quotes:
                    quotes[quote_id] = Quote(
                        quote_id=quote_id,
                        span=span,
                        mask_ids=masks_over(bundle, span.span),
                    )
            claims.append(
                Claim(
                    claim_id=f"c-{window.start}-{window.end}-{attempt}-{index}",
                    doc_id=doc_id,
                    window_id=window.window_id,
                    attempt=attempt,
                    claim=candidate.claim,
                    quote_ids=tuple(ids),
                )
            )
        if not refused:
            break
        feedback = Message(
            role="user",
            content=refused_feedback(
                refused, units=len(labels), claim_limit=policy.claim_limit
            ),
        )
        messages = (*messages, turn, feedback)
    outcome = WindowOutcome.COMPLETED if usable else WindowOutcome.FAILED
    record = WindowRecord(
        doc_id=doc_id,
        window_id=window.window_id,
        start=window.start,
        end=window.end,
        unit_ids=window.unit_ids,
        context_id=window.context_id,
        attempts=attempts,
        outcome=outcome,
        reason=reason,
        requests=spent.requests,
        cache_hits=spent.cache_hits,
        prompt_tokens=spent.prompt_tokens,
        completion_tokens=spent.completion_tokens,
        unreported=spent.unreported,
        latency_ms=spent.latency_ms,
        exhausted=exhausted,
    )
    visits = tuple(
        Visit(
            doc_id=doc_id,
            element_id=unit_id,
            window_id=window.window_id,
            outcome=outcome,
            reason=reason,
        )
        for unit_id in window.unit_ids
    )
    return WindowResult(
        record=record,
        claims=tuple(claims),
        quotes=tuple(quotes.values()),
        rejections=tuple(rejections),
        visits=visits,
        candidates=candidates,
    )
