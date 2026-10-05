"""Evidence-only raw scorer seam; no pooling, assignment, or concrete model import."""

from collections.abc import Callable
from typing import Protocol, Self

from earnings_core import digest
from pydantic import Field, NonNegativeInt, model_validator

from earnings_themes.records import Sha256Hex
from earnings_themes.support.problems import SupportError
from earnings_themes.support.prompt import evidence_text, joint_premise
from earnings_themes.support.records import (
    SUPPORT_VERSION,
    RefusedTarget,
    ResolvedInput,
    SafePart,
    Score,
    ScorerIdentity,
)
from earnings_themes.support.resolve import _validated, reverify_input


class ScoreRequest(SafePart):
    premise: str = Field(repr=False)
    hypothesis: str = Field(repr=False)
    input_hash: Sha256Hex


class ScoreReply(SafePart):
    score: Score | None
    reason: str | None
    input_tokens: NonNegativeInt | None
    latency_ms: NonNegativeInt
    identity: ScorerIdentity
    input_hash: Sha256Hex

    @model_validator(mode="after")
    def _availability(self) -> Self:
        if (self.score is not None) != (self.reason is None):
            raise ValueError("invalid_availability")
        if self.score is not None and self.input_tokens is None:
            raise ValueError("missing_usage")
        return self


class EntailmentScorer(Protocol):
    @property
    def identity(self) -> ScorerIdentity: ...

    def count_tokens(self, request: ScoreRequest) -> int: ...

    def score(self, request: ScoreRequest) -> ScoreReply: ...


def _request(premise: str, hypothesis: str) -> ScoreRequest:
    return ScoreRequest(
        premise=premise,
        hypothesis=hypothesis,
        input_hash=digest(
            {"encoding": SUPPORT_VERSION, "premise": premise, "hypothesis": hypothesis}
        ),
    )


def score_requests(input: ResolvedInput) -> tuple[tuple[str | None, ScoreRequest], ...]:
    """Reverify every original link, then plan separate per-quote/joint evaluations.

    One quote aliases its joint evaluation downstream. Multiple quotes always
    receive a separate joint request with explicit passage boundaries.
    """
    checked = reverify_input(input)
    if isinstance(checked, RefusedTarget):
        raise SupportError(checked.outcome.missing[0])
    requests = [
        (ref.quote_id, _request(evidence_text(checked, ref), checked.claim))
        for ref in checked.evidence
    ]
    if len(checked.evidence) > 1:
        requests.append((None, _request(joint_premise(checked), checked.claim)))
    return tuple(requests)


def evaluate_score(scorer: EntailmentScorer, request: ScoreRequest) -> ScoreReply:
    """Count complete input before dispatch and validate the returned bindings.

    Known scorer/transport failures remain unavailable. Unexpected adapter errors
    abort with a fixed reason, suppressing their source-bearing exception chain.
    """
    try:
        adapter_identity = scorer.identity
    except Exception:  # noqa: BLE001 - redact arbitrary adapter diagnostics
        raise SupportError("unexpected_error") from None
    identity = _validated(adapter_identity, ScorerIdentity)
    request = _validated(request, ScoreRequest)
    if request.input_hash != _request(request.premise, request.hypothesis).input_hash:
        raise SupportError("input_changed")
    tokens = None

    def unavailable(reason: str) -> ScoreReply:
        return ScoreReply(
            score=None,
            reason=reason,
            input_tokens=tokens,
            latency_ms=0,
            identity=identity,
            input_hash=request.input_hash,
        )

    try:
        count = scorer.count_tokens(request)
        if type(count) is not int or count < 0:
            return unavailable("malformed_reply")
        tokens = count
        if tokens > identity.input_limit:
            return unavailable("input_too_long")
        raw = scorer.score(request)
    except SupportError as error:
        if str(error) in {"scorer_failed", "transport_error", "input_too_long"}:
            return unavailable(str(error))
        raise SupportError("unexpected_error") from None
    except Exception:  # noqa: BLE001 - redact arbitrary adapter diagnostics
        raise SupportError("unexpected_error") from None
    try:
        if (
            type(raw) is not ScoreReply
            or isinstance(raw.score, bool)
            or (raw.input_tokens is not None and type(raw.input_tokens) is not int)
        ):
            return unavailable("malformed_reply")
        result = _validated(raw, ScoreReply)
    except SupportError:
        return unavailable("malformed_reply")
    if result.identity != identity:
        return unavailable("model_mismatch")
    if result.input_hash != request.input_hash:
        return unavailable("input_changed")
    return result


class ScriptedScorer:
    """Injected offline scorer; requests remain local and representations are safe."""

    def __init__(
        self,
        script: Callable[[ScoreRequest], ScoreReply],
        token_counter: Callable[[ScoreRequest], int],
        identity: ScorerIdentity,
    ) -> None:
        self._script = script
        self._token_counter = token_counter
        self._identity = _validated(identity, ScorerIdentity)
        self.requests: list[ScoreRequest] = []

    @property
    def identity(self) -> ScorerIdentity:
        return self._identity

    def count_tokens(self, request: ScoreRequest) -> int:
        return self._token_counter(request)

    def score(self, request: ScoreRequest) -> ScoreReply:
        self.requests.append(request)
        return self._script(request)

    def __repr__(self) -> str:
        return f"ScriptedScorer(requests={len(self.requests)})"

    __str__ = __repr__
