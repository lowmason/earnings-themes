"""Bounded sequential proposals with complete request and source integrity."""

from dataclasses import dataclass

from earnings_core import digest, sha256_hex

from earnings_themes.coding import prompt as coding_prompt
from earnings_themes.coding.adapters import Classifier, CodingTransportError
from earnings_themes.coding.cache import CodingCache, coding_key, raw_reply_hash
from earnings_themes.coding.input import CodingInput, reverify_coding_input
from earnings_themes.coding.prompt import (
    novelty_for,
    parse_coding_reply,
    render_coding,
    targets_for,
    unusable_feedback,
)
from earnings_themes.coding.records import (
    AttributeRecord,
    ClassificationRecord,
    CodingAttempt,
    CodingCeilings,
    CodingError,
    CodingPolicy,
    CodingReply,
    CodingRequest,
    NoveltyItem,
    ProposalRecord,
    checked,
)
from earnings_themes.extraction.adapters import Message, ModelReply, Usage
from earnings_themes.support.records import JudgeIdentity

_RETRYABLE = frozenset(
    {
        "malformed_reply",
        "invalid_references",
        "hierarchy_conflict",
        "tool_call_refused",
        "model_mismatch",
        "transport_error",
    }
)
_INCOMPLETE = _RETRYABLE | {
    "replay_miss",
    "input_too_long",
    "requests_exhausted",
    "tokens_exhausted",
}


class CodingAllowance:
    """One shared run budget; missing usage retains its full reservation."""

    def __init__(self, ceilings: CodingCeilings, *, run_id: str) -> None:
        if type(run_id) is not str or not run_id.strip():
            raise CodingError("malformed_record")
        self.run_id = run_id
        self.ceilings = checked(ceilings, CodingCeilings)
        self.claim_requests: dict[tuple[str, str], int] = {}
        self.doc_requests: dict[str, int] = {}
        self.doc_tokens: dict[str, int] = {}
        self.requests = 0
        self.tokens = 0
        self.unreported = 0

    def reserve(
        self, doc_id: str, claim_id: str, input_tokens: int, max_output: int
    ) -> int:
        self._check_counters()
        if any(
            type(value) is not str or not value.strip() for value in (doc_id, claim_id)
        ):
            raise CodingError("malformed_record")
        if any(
            type(value) is not int or value < 0 for value in (input_tokens, max_output)
        ):
            raise CodingError("malformed_record")
        ceilings = checked(self.ceilings, CodingCeilings)
        key = (doc_id, claim_id)
        if (
            self.claim_requests.get(key, 0) >= ceilings.requests_per_claim
            or self.doc_requests.get(doc_id, 0) >= ceilings.requests_per_document
            or self.requests >= ceilings.requests_per_run
        ):
            raise CodingError("requests_exhausted")
        reserved = input_tokens + max_output
        if (
            self.doc_tokens.get(doc_id, 0) + reserved > ceilings.tokens_per_document
            or self.tokens + reserved > ceilings.tokens_per_run
        ):
            raise CodingError("tokens_exhausted")
        self.claim_requests[key] = self.claim_requests.get(key, 0) + 1
        self.doc_requests[doc_id] = self.doc_requests.get(doc_id, 0) + 1
        self.requests += 1
        self.doc_tokens[doc_id] = self.doc_tokens.get(doc_id, 0) + reserved
        self.tokens += reserved
        return reserved

    def reconcile(self, doc_id: str, reserved: int, usage: Usage | None) -> None:
        self._check_counters()
        if type(reserved) is not int or reserved < 0:
            raise CodingError("malformed_record")
        if (
            type(doc_id) is not str
            or doc_id not in self.doc_tokens
            or reserved > self.doc_tokens[doc_id]
            or reserved > self.tokens
        ):
            raise CodingError("malformed_record")
        if usage is None:
            self.unreported += 1
            return
        usage = checked(usage, Usage)
        difference = usage.prompt_tokens + usage.completion_tokens - reserved
        self.doc_tokens[doc_id] += difference
        self.tokens += difference

    def _check_counters(self) -> None:
        for counter in (self.claim_requests, self.doc_requests, self.doc_tokens):
            if type(counter) is not dict or any(
                type(count) is not int or count < 0 for count in counter.values()
            ):
                raise CodingError("malformed_record")
        if any(
            type(count) is not int or count < 0
            for count in (self.requests, self.tokens, self.unreported)
        ):
            raise CodingError("malformed_record")

    def __repr__(self) -> str:
        return f"CodingAllowance(requests={self.requests}, tokens={self.tokens})"

    __str__ = __repr__


@dataclass(frozen=True, repr=False)
class ClassificationResult:
    record: ClassificationRecord
    attempts: tuple[CodingAttempt, ...]
    proposals: tuple[ProposalRecord, ...]
    attribute: AttributeRecord | None
    novelty: NoveltyItem | None


def classification_id(run_id: str, doc_id: str, claim_id: str, input_hash: str) -> str:
    return "classification-" + digest(
        {
            "coding_run_id": run_id,
            "doc_id": doc_id,
            "claim_id": claim_id,
            "input_hash": input_hash,
        }
    )


def _current_identity(classifier: Classifier) -> JudgeIdentity:
    """Strict current runtime read without invoking optional preflight."""
    try:
        return checked(classifier.identity, JudgeIdentity)
    except Exception:  # noqa: BLE001 - arbitrary identity diagnostics are unsafe
        raise CodingError("model_mismatch") from None


def _classifier_identity(classifier: Classifier) -> JudgeIdentity:
    try:
        identity = _current_identity(classifier)
        preflight = getattr(classifier, "preflight", None)
        if preflight is not None:
            preflight()
        after = _current_identity(classifier)
        if after != identity:
            raise CodingError("model_mismatch")
        return after
    except Exception:  # noqa: BLE001 - arbitrary identity diagnostics are unsafe
        raise CodingError("model_mismatch") from None


def _policy(policy: CodingPolicy) -> CodingPolicy:
    current = checked(policy, CodingPolicy)
    if sha256_hex(current.prompt_text.encode("utf-8")) != current.prompt_hash:
        raise CodingError("input_changed")
    return current


def _require_request(
    input: CodingInput,
    classifier: Classifier,
    policy: CodingPolicy,
    request: CodingRequest,
    identity: JudgeIdentity,
    policy_hash: str,
    feedback: str | None,
) -> None:
    """Regenerate the full request; structural cache/type checks are insufficient."""
    if _classifier_identity(classifier) != identity:
        raise CodingError("model_mismatch")
    _require_current_request(
        input, classifier, policy, request, identity, policy_hash, feedback
    )


def _require_current_request(
    input: CodingInput,
    classifier: Classifier,
    policy: CodingPolicy,
    request: CodingRequest,
    identity: JudgeIdentity,
    policy_hash: str,
    feedback: str | None,
) -> None:
    # Identity properties may run callbacks; read before pure source/request checks.
    if _current_identity(classifier) != identity:
        raise CodingError("model_mismatch")
    try:
        reverify_coding_input(input)
    except CodingError:
        raise CodingError("input_changed") from None
    try:
        current_policy = _policy(policy)
    except CodingError:
        raise CodingError("input_changed") from None
    if digest(current_policy.model_dump(mode="json")) != policy_hash:
        raise CodingError("input_changed")
    try:
        current = checked(request, CodingRequest)
        expected = coding_prompt.render_coding(input, current_policy)
        if feedback is not None:
            expected = expected.model_copy(
                update={
                    "messages": (
                        *expected.messages,
                        Message(role="user", content=unusable_feedback(feedback)),
                    )
                }
            )
        schema = CodingReply.model_json_schema()
        if (
            current.reply_schema != schema
            or current.subject.schema_hash != digest(schema)
            or current.model_dump(mode="json") != expected.model_dump(mode="json")
        ):
            raise CodingError("input_changed")
    except CodingError:
        raise CodingError("input_changed") from None


def _attempt(
    input: CodingInput,
    classifier: Classifier,
    policy: CodingPolicy,
    allowance: CodingAllowance,
    cache: CodingCache,
    request: CodingRequest,
    identity: JudgeIdentity,
    policy_hash: str,
    feedback: str | None,
    ordinal: int,
    identifier: str,
) -> tuple[CodingAttempt, CodingReply | None]:
    require = lambda: _require_request(
        input, classifier, policy, request, identity, policy_hash, feedback
    )
    require()
    request_hash = digest(checked(request, CodingRequest).model_dump(mode="json"))
    raw = None
    raw_ref = None
    cached = False
    tokens = reserved = 0
    reason = transport_reason = None
    answer = None
    try:
        entry = cache.get(request, identity)
        require()
        if entry is not None:
            cached = True
            tokens = entry.input_tokens
            raw = entry.reply
            raw_ref = f"{coding_key(request, identity)}.json"
            transport_reason = entry.refusal_reason
        elif cache.mode == "replay":
            raise CodingError("replay_miss")
        else:
            try:
                tokens = classifier.count_tokens(request)
            finally:
                require()
            if type(tokens) is not int or tokens < 0:
                raise CodingError("malformed_record")
            output = request.parameters.max_tokens
            if output > identity.output_limit or tokens + output > identity.input_limit:
                raise CodingError("input_too_long")
            require()
            reserved = allowance.reserve(input.doc_id, input.claim_id, tokens, output)
            try:
                raw = checked(classifier.complete(request), ModelReply)
            except CodingTransportError as error:
                transport_reason = str(error)
                raw = None if error.reply is None else checked(error.reply, ModelReply)
            except CodingError as error:
                if str(error) not in _RETRYABLE:
                    raise
                transport_reason = str(error)
            finally:
                allowance.reconcile(
                    input.doc_id, reserved, None if raw is None else raw.usage
                )
            if raw is not None:
                # Raw transport evidence remains local even when publication later aborts.
                raw_ref = cache.put(
                    request,
                    identity,
                    raw,
                    input_tokens=tokens,
                    refusal_reason=transport_reason,
                )
            require()
        if transport_reason is not None:
            raise CodingError(transport_reason)
        if raw is None:
            raise CodingError("transport_error")
        answer = parse_coding_reply(raw, input, identity.runtime.model_id)
    except CodingError as error:
        if str(error) not in _INCOMPLETE:
            raise
        reason = str(error)
    require()
    usage = None if raw is None else raw.usage
    row = CodingAttempt(
        attempt_id=f"{identifier}-attempt-{ordinal}",
        classification_id=identifier,
        doc_id=input.doc_id,
        claim_id=input.claim_id,
        attempt=ordinal,
        request_hash=request_hash,
        prompt_hash=request.subject.prompt_hash,
        schema_hash=request.subject.schema_hash,
        input_hash=input.input_hash,
        input_tokens=tokens,
        reserved_tokens=reserved,
        actual_prompt_tokens=None if usage is None else usage.prompt_tokens,
        actual_completion_tokens=None if usage is None else usage.completion_tokens,
        unreported=usage is None and (cached or reserved > 0),
        cached=cached,
        latency_ms=0 if raw is None else raw.latency_ms,
        raw_ref=raw_ref,
        raw_hash=None
        if raw is None or raw_ref is None
        else raw_reply_hash(raw, transport_reason, tokens),
        reason=reason,
    )
    return row, answer


def _verify_attempts(
    input: CodingInput,
    policy: CodingPolicy,
    identity: JudgeIdentity,
    attempts: tuple[CodingAttempt, ...],
    cache: CodingCache,
) -> None:
    """Reconstruct transmitted hashes and bind immutable raw audit again."""
    try:
        base = coding_prompt.render_coding(input, _policy(policy))
    except CodingError:
        raise CodingError("input_changed") from None
    request = base
    for row in attempts:
        if (
            row.request_hash != digest(request.model_dump(mode="json"))
            or row.prompt_hash != request.subject.prompt_hash
            or row.schema_hash != request.subject.schema_hash
            or row.input_hash != input.input_hash
        ):
            raise CodingError("input_changed")
        if row.raw_ref is not None:
            entry = cache.get(request, identity)
            if (
                entry is None
                or row.raw_ref != f"{coding_key(request, identity)}.json"
                or row.raw_hash != entry.reply_hash
                or row.input_tokens != entry.input_tokens
            ):
                raise CodingError("cache_corrupt")
        if row.reason in _RETRYABLE:
            request = base.model_copy(
                update={
                    "messages": (
                        *base.messages,
                        Message(role="user", content=unusable_feedback(row.reason)),
                    )
                }
            )


def classify_claim(
    input: CodingInput,
    classifier: Classifier,
    policy: CodingPolicy,
    allowance: CodingAllowance,
    *,
    cache: CodingCache,
) -> ClassificationResult:
    """At most two unusable-reply attempts; an explicit valid empty reply is final."""
    try:
        reverify_coding_input(input)
        if type(allowance) is not CodingAllowance or type(cache) is not CodingCache:
            raise CodingError("malformed_record")
        if type(cache.mode) is not str or cache.mode not in ("live", "replay"):
            raise CodingError("malformed_record")
        allowance._check_counters()
        identity = _classifier_identity(classifier)
        current_policy = _policy(policy)
        policy_hash = digest(current_policy.model_dump(mode="json"))
        base = render_coding(input, current_policy)
        identifier = classification_id(
            allowance.run_id, input.doc_id, input.claim_id, input.input_hash
        )
        request = base
        attempts = []
        answer = None
        feedback = None
        for ordinal in (1, 2):
            row, answer = _attempt(
                input,
                classifier,
                policy,
                allowance,
                cache,
                request,
                identity,
                policy_hash,
                feedback,
                ordinal,
                identifier,
            )
            attempts.append(row)
            if answer is not None or row.reason not in _RETRYABLE or ordinal == 2:
                break
            feedback = row.reason
            request = base.model_copy(
                update={
                    "messages": (
                        *base.messages,
                        Message(role="user", content=unusable_feedback(feedback)),
                    )
                }
            )
        proposals = ()
        attribute = novelty = None
        if answer is not None:
            proposals = tuple(
                ProposalRecord(
                    proposal_id="proposal-"
                    + digest(
                        {
                            "classification_id": identifier,
                            "target": target.model_dump(mode="json"),
                        }
                    ),
                    coding_run_id=allowance.run_id,
                    classification_id=identifier,
                    target=target,
                    input_hash=input.input_hash,
                )
                for target in targets_for(input, answer)
            )
            attribute = AttributeRecord(
                coding_run_id=allowance.run_id,
                doc_id=input.doc_id,
                claim_id=input.claim_id,
                input_hash=input.input_hash,
                attributes=answer.attributes,
            )
            novelty = novelty_for(
                input,
                answer,
                coding_run_id=allowance.run_id,
                classification_id=identifier,
            )
        record = ClassificationRecord(
            classification_id=identifier,
            coding_run_id=allowance.run_id,
            doc_id=input.doc_id,
            claim_id=input.claim_id,
            input_hash=input.input_hash,
            codebook=input.probes[0].record.target.codebook,
            status="completed" if answer is not None else "incomplete",
            reason=None if answer is not None else attempts[-1].reason,
            attempt_ids=tuple(row.attempt_id for row in attempts),
            theme_ids=tuple(p.target.theme_id for p in proposals),
        )
        _require_request(
            input, classifier, policy, request, identity, policy_hash, feedback
        )
        _verify_attempts(input, policy, identity, tuple(attempts), cache)
        _require_current_request(
            input, classifier, policy, request, identity, policy_hash, feedback
        )
        return ClassificationResult(
            record, tuple(attempts), proposals, attribute, novelty
        )
    except CodingError:
        raise
    except Exception:  # noqa: BLE001 - never expose arbitrary callback/source text
        raise CodingError("unexpected_error") from None
