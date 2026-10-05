"""Sequential independent raw signals and categorical review, without acceptance."""

from collections.abc import Callable

from earnings_core import digest, sha256_hex

from earnings_themes.extraction.adapters import Message, ModelReply, Usage
from earnings_themes.support.allowance import Allowance
from earnings_themes.support.cache import SupportCache, judge_key, scorer_key
from earnings_themes.support.judges import (
    Judge,
    JudgeRequest,
    SupportTransportError,
    parse_answer,
    validate_panel,
)
from earnings_themes.support.problems import SupportError, unexpected_error
from earnings_themes.support.prompt import render_judge
from earnings_themes.support.records import (
    AssessmentResult,
    EntailmentSignal,
    JudgeAttempt,
    JudgeIdentity,
    JudgeTrial,
    Presentation,
    RefusedTarget,
    ResolvedInput,
    ReviewOutcome,
    ScorerIdentity,
    SignalStatus,
    SupportPolicy,
    UsageRecord,
)
from earnings_themes.support.resolve import _validated, reverify_input
from earnings_themes.support.scorers import (
    EntailmentScorer,
    ScoreReply,
    ScoreRequest,
    evaluate_score,
    score_requests,
)

_PRESENTATIONS = (Presentation.EVIDENCE_FIRST, Presentation.CLAIM_THEME_FIRST)
_UNUSABLE = frozenset(
    {
        "malformed_reply",
        "invalid_references",
        "tool_call_refused",
        "model_mismatch",
        "transport_error",
    }
)


def _count[Request](counter: Callable[[Request], int], request: Request) -> int:
    count = counter(request)
    if type(count) is not int or count < 0:
        raise SupportError("malformed_reply")
    return count


def _signal(
    input: ResolvedInput,
    identity: ScorerIdentity,
    quote_id: str | None,
    request: ScoreRequest,
    reply: ScoreReply,
    cached: bool,
) -> EntailmentSignal:
    evaluation_id = digest(
        {
            "target": input.record.target_id,
            "identity": identity.model_dump(mode="json"),
            "input": request.input_hash,
            "quote": quote_id,
            "scope": "joint" if quote_id is None else "quote",
        }
    )
    scope = "joint" if quote_id is None else "quote"
    return EntailmentSignal(
        signal_id=digest(
            {"evaluation": evaluation_id, "scope": scope, "quote": quote_id}
        ),
        target_id=input.record.target_id,
        scope=scope,
        quote_id=quote_id,
        evaluation_id=evaluation_id,
        identity=identity,
        input_hash=request.input_hash,
        status=SignalStatus.AVAILABLE
        if reply.score is not None
        else SignalStatus.UNAVAILABLE,
        score=reply.score,
        reason=reply.reason,
        input_tokens=reply.input_tokens,
        latency_ms=reply.latency_ms,
        cached=cached,
    )


def _cached_usage(
    input: ResolvedInput,
    operation_id: str,
    kind: str,
    usage: Usage | None,
    latency: int,
) -> UsageRecord:
    return UsageRecord(
        target_id=input.record.target_id,
        doc_id=input.record.target.doc_id,
        operation_id=operation_id,
        kind=kind,
        reserved_tokens=0,
        actual_prompt_tokens=None if usage is None else usage.prompt_tokens,
        actual_completion_tokens=None if usage is None else usage.completion_tokens,
        unreported=usage is None,
        cached=True,
        latency_ms=latency,
    )


def _settled_usage(allowance: Allowance, operation: str, latency: int) -> UsageRecord:
    row = next(r for r in allowance.snapshot() if r.operation_id == operation)
    return row.model_copy(update={"latency_ms": latency})


def _raw_reply(raw: ModelReply) -> ModelReply:
    try:
        return _validated(raw, ModelReply)
    except SupportError:
        raise SupportError("malformed_reply") from None


def _require_current(input: ResolvedInput) -> None:
    if isinstance(reverify_input(input), RefusedTarget):
        # Initial refusal is a zero-dispatch result. Changes during assessment
        # abort publication instead, retaining completed raw cache/accounting.
        raise SupportError("input_changed") from None


def _score_signals(
    input: ResolvedInput,
    scorer: EntailmentScorer,
    policy: SupportPolicy,
    allowance: Allowance,
    cache: SupportCache,
) -> tuple[tuple[EntailmentSignal, ...], tuple[UsageRecord, ...]]:
    identity = _validated(scorer.identity, ScorerIdentity)
    signals = []
    usage_rows = []
    for quote_id, request in score_requests(input):
        _require_current(input)
        key = scorer_key(input, request, identity, policy)
        tokens = None
        cached = False
        try:
            raw = cache.lookup(key, "scorer")
            if raw is not None:
                reply = raw
                cached = True
                usage = (
                    None
                    if raw.input_tokens is None
                    else Usage(prompt_tokens=raw.input_tokens, completion_tokens=0)
                )
                usage_rows.append(
                    _cached_usage(
                        input,
                        digest({"cached_score": str(key)}),
                        "scorer",
                        usage,
                        raw.latency_ms,
                    )
                )
            elif cache.mode == "replay":
                raise SupportError("replay_miss")
            else:
                tokens = _count(scorer.count_tokens, request)
                if tokens > identity.input_limit:
                    raise SupportError("input_too_long")
                operation = allowance.reserve_scorer(
                    input.record.target_id, input.record.target.doc_id
                )
                try:
                    reply = evaluate_score(scorer, request)
                except Exception:
                    allowance.settle(operation, None)
                    raise
                usage = (
                    None
                    if reply.input_tokens is None
                    else Usage(prompt_tokens=reply.input_tokens, completion_tokens=0)
                )
                allowance.settle(operation, usage)
                usage_rows.append(
                    _settled_usage(allowance, operation, reply.latency_ms)
                )
                cache.put(key, reply)
        except SupportError as error:
            if str(error) not in {
                "replay_miss",
                "input_too_long",
                "scorer_exhausted",
                "cache_corrupt",
                "malformed_reply",
                "scorer_failed",
                "transport_error",
            }:
                raise
            reply = ScoreReply(
                score=None,
                reason=str(error),
                input_tokens=tokens,
                latency_ms=0,
                identity=identity,
                input_hash=request.input_hash,
            )
        signals.append(_signal(input, identity, quote_id, request, reply, cached))
    if len(input.evidence) == 1:
        first = signals[0]
        signals.append(
            first.model_copy(
                update={
                    "scope": "joint",
                    "quote_id": None,
                    "signal_id": digest(
                        {
                            "evaluation": first.evaluation_id,
                            "scope": "joint",
                            "quote": None,
                        }
                    ),
                }
            )
        )
    return tuple(signals), tuple(usage_rows)


def _retry_request(original: JudgeRequest, reason: str) -> JudgeRequest:
    # Only trusted vocabulary enters feedback; raw unusable text is never echoed.
    feedback = Message(
        role="user",
        content=f"Reply validation failed: {reason}. Return the closed answer schema with exactly the supplied quote_assessments references.",
    )
    return original.model_copy(update={"messages": (*original.messages, feedback)})


def _judge_attempt(
    input: ResolvedInput,
    judge: Judge,
    identity: JudgeIdentity,
    request: JudgeRequest,
    ordinal: int,
    trial_id: str,
    policy: SupportPolicy,
    allowance: Allowance,
    cache: SupportCache,
) -> tuple[JudgeAttempt, UsageRecord | None]:
    _require_current(input)
    request_hash = digest(request.model_dump(mode="json"))
    key = judge_key(input, request, identity, policy)
    raw = None
    raw_ref = None
    cached = False
    tokens = 0
    reserved = 0
    problem = None
    answer = None
    cached_usage = None
    transport_problem = None
    try:
        raw = cache.lookup(key, "judge")
        if raw is not None:
            cached = True
            raw_ref = cache.raw_ref(key)
            transport_problem = cache.refusal_reason(key)
        elif cache.mode == "replay":
            raise SupportError("replay_miss")
        else:
            tokens = _count(judge.count_tokens, request)
            completion = request.parameters.max_tokens
            if (
                completion > identity.output_limit
                or tokens + completion > identity.input_limit
            ):
                raise SupportError("input_too_long")
            operation = allowance.reserve_judge(
                input.record.target_id, input.record.target.doc_id, tokens, completion
            )
            reserved = tokens + completion
            try:
                raw = _raw_reply(judge.complete(request))
            except SupportTransportError as error:
                transport_problem = str(error)
                if error.reply is not None:
                    try:
                        raw = _raw_reply(error.reply)
                    except SupportError:
                        transport_problem = "malformed_reply"
            except SupportError as error:
                if str(error) not in _UNUSABLE | {"input_too_long"}:
                    allowance.settle(operation, None)
                    raise
                transport_problem = str(error)
            except Exception:
                allowance.settle(operation, None)
                raise
            allowance.settle(operation, None if raw is None else raw.usage)
            cached_usage = _settled_usage(
                allowance, operation, 0 if raw is None else raw.latency_ms
            )
            if raw is not None:
                raw_ref = cache.put(key, raw, refusal_reason=transport_problem)
        if raw is not None:
            if cached:
                cached_usage = _cached_usage(
                    input,
                    digest({"cached_judge": str(key)}),
                    "judge",
                    raw.usage,
                    raw.latency_ms,
                )
                tokens = 0 if raw.usage is None else raw.usage.prompt_tokens
            try:
                answer = parse_answer(raw, input, identity)
            except SupportError:
                if transport_problem is None:
                    raise
        if transport_problem is not None:
            answer = None
            raise SupportError(transport_problem)
        if raw is None:
            raise SupportError("transport_error")
    except SupportError as error:
        if str(error) not in _UNUSABLE | {
            "input_too_long",
            "replay_miss",
            "cache_corrupt",
            "judge_exhausted",
            "tokens_exhausted",
        }:
            raise
        problem = str(error)
    usage = None if raw is None else raw.usage
    attempt = JudgeAttempt(
        attempt_id=digest(
            {"trial": trial_id, "attempt": ordinal, "request": request_hash}
        ),
        trial_id=trial_id,
        attempt=ordinal,
        request_hash=request_hash,
        prompt_hash=request.subject.prompt_hash,
        schema_hash=request.subject.schema_hash,
        input_tokens=tokens,
        reserved_tokens=reserved,
        actual_prompt_tokens=None if usage is None else usage.prompt_tokens,
        actual_completion_tokens=None if usage is None else usage.completion_tokens,
        latency_ms=0 if raw is None else raw.latency_ms,
        cached=cached,
        raw_ref=raw_ref,
        problem=problem,
        answer=answer,
    )
    return attempt, cached_usage


def _judge_trials(
    input: ResolvedInput,
    judges: tuple[Judge, Judge],
    identities: tuple[JudgeIdentity, JudgeIdentity],
    originals: dict[Presentation, JudgeRequest],
    policy: SupportPolicy,
    allowance: Allowance,
    cache: SupportCache,
) -> tuple[tuple[JudgeTrial, ...], tuple[JudgeAttempt, ...], list[UsageRecord]]:
    trials = []
    attempts = []
    cached_usage = []
    for judge, identity in zip(judges, identities, strict=True):
        for presentation in _PRESENTATIONS:
            original = originals[presentation]
            trial_id = digest(
                {
                    "target": input.record.target_id,
                    "identity": identity.model_dump(mode="json"),
                    "presentation": presentation,
                }
            )
            request = original
            retained = []
            for ordinal in (1, 2):
                attempt, usage = _judge_attempt(
                    input,
                    judge,
                    identity,
                    request,
                    ordinal,
                    trial_id,
                    policy,
                    allowance,
                    cache,
                )
                retained.append(attempt)
                if usage is not None:
                    cached_usage.append(usage)
                if attempt.answer is not None or attempt.problem not in _UNUSABLE:
                    break
                request = _retry_request(original, attempt.problem)
            final = retained[-1]
            trials.append(
                JudgeTrial(
                    trial_id=trial_id,
                    target_id=input.record.target_id,
                    identity=identity,
                    presentation=presentation,
                    attempt_ids=tuple(a.attempt_id for a in retained),
                    status=SignalStatus.AVAILABLE
                    if final.answer is not None
                    else SignalStatus.UNAVAILABLE,
                    answer=final.answer,
                    reason=final.problem,
                )
            )
            attempts.extend(retained)
    return tuple(trials), tuple(attempts), cached_usage


def derive_outcome(
    target_id: str,
    entailment: tuple[EntailmentSignal, ...],
    trials: tuple[JudgeTrial, ...],
    evidence_ids: tuple[str, ...],
) -> ReviewOutcome:
    """Categorical objections survive unavailable signals; scores never gate."""
    signals = tuple(_validated(s, EntailmentSignal) for s in entailment)
    trials = tuple(_validated(t, JudgeTrial) for t in trials)
    missing = {s.reason for s in signals if s.status == SignalStatus.UNAVAILABLE}
    missing.update(t.reason for t in trials if t.status == SignalStatus.UNAVAILABLE)
    quote_ids = set(evidence_ids)
    family_presentations: dict[str, set[Presentation]] = {}
    for trial in trials:
        family_presentations.setdefault(trial.identity.family, set()).add(
            trial.presentation
        )
    if (
        any(s.target_id != target_id for s in signals)
        or any(t.target_id != target_id for t in trials)
        or {s.quote_id for s in signals if s.scope == "quote"} != quote_ids
        or len([s for s in signals if s.scope == "joint"]) != 1
        or len(signals) != len(quote_ids) + 1
        or len(trials) != 4
        or len(family_presentations) != 2
        or any(
            presentations != set(_PRESENTATIONS)
            for presentations in family_presentations.values()
        )
    ):
        missing.add("invalid_references")
    flags = set()
    categories = set()
    for trial in trials:
        answer = trial.answer
        if answer is None:
            continue
        supplied = {q.quote_id for q in answer.quote_assessments}
        if supplied != quote_ids:
            missing.add("invalid_references")
        flags.update(c.value for c in answer.reason_codes)
        if answer.claim_support != "supported":
            flags.add(f"claim_support_{answer.claim_support}")
        if answer.theme_fit != "fits":
            flags.add(f"theme_fit_{answer.theme_fit}")
        for quote in answer.quote_assessments:
            if quote.contribution in {"irrelevant", "contradicting", "uncertain"}:
                flags.add(f"quote_{quote.contribution}")
        categories.add(
            (
                answer.claim_support,
                answer.theme_fit,
                tuple(
                    sorted(
                        (q.quote_id, q.contribution) for q in answer.quote_assessments
                    )
                ),
            )
        )
    if len(categories) > 1:
        flags.add("category_disagreement")
    status = "incomplete" if missing else "flagged" if flags else "assessed"
    return _validated(
        ReviewOutcome.model_construct(
            target_id=target_id,
            status=status,
            flags=tuple(sorted(flags)),
            missing=tuple(sorted(missing)),
            signal_ids=tuple(s.signal_id for s in signals),
            trial_ids=tuple(t.trial_id for t in trials),
        ),
        ReviewOutcome,
    )


def _refused_result(refused: RefusedTarget) -> AssessmentResult:
    return AssessmentResult(refused.record, (), (), (), (), (), (), refused.outcome)


def assess_target(
    input: ResolvedInput,
    scorer: EntailmentScorer,
    judges: tuple[Judge, Judge],
    policy: SupportPolicy,
    allowance: Allowance,
    *,
    cache: SupportCache,
    extractor_family: str,
) -> AssessmentResult:
    """Preflight lineage/identity, reverify exact evidence, then assess sequentially.

    The explicit lineage argument is required because extraction identities store
    model aliases, which cannot establish the extractor's family.
    """
    try:
        policy = _validated(policy, SupportPolicy)
        if sha256_hex(policy.prompt_text.encode("utf-8")) != policy.prompt_hash:
            raise SupportError("input_changed")
        _validated(scorer.identity, ScorerIdentity)
        identities = validate_panel(extractor_family, tuple(j.identity for j in judges))
        for judge in judges:
            preflight = getattr(judge, "_preflight", None)
            if preflight is not None:
                preflight()
        checked = reverify_input(input)
        if isinstance(checked, RefusedTarget):
            return _refused_result(checked)
        originals = {p: render_judge(checked, policy, p) for p in _PRESENTATIONS}
        signals, scorer_usage = _score_signals(
            checked, scorer, policy, allowance, cache
        )
        trials, attempts, judge_usage = _judge_trials(
            checked, judges, identities, originals, policy, allowance, cache
        )
        _require_current(checked)
        outcome = derive_outcome(
            checked.record.target_id, signals, trials, checked.record.evidence_ids
        )
        usage = scorer_usage + tuple(judge_usage)
        return AssessmentResult(
            checked.record,
            checked.evidence,
            checked.contexts,
            signals,
            trials,
            attempts,
            usage,
            outcome,
        )
    except SupportError:
        raise
    except Exception as error:  # noqa: BLE001 - redact arbitrary adapter diagnostics
        raise unexpected_error(error) from None
