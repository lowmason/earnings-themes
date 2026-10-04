"""The adapter protocol, and the scripted fake (the Stage 7 spec, §Seams and §The
adapter protocol; ES10).

- **The protocol.** An adapter has an ``identity`` and ``complete(request) ->
  reply``: messages and settings in, text and usage out. A PydanticAI-backed or a
  hosted adapter can sit behind it, in an extra (Stages 14 and 16).
- **The request.** The messages, with the earlier turns on a retry; the reply's JSON
  schema; and the parameters: what an adapter sends. Its ``subject`` holds the rest
  of the R14.6 key, which no adapter sends.
- **The reply.** Its text, its usage when the server reports it, the model the server
  names, whether it carries tool calls, its latency, and whether the cache returned
  it.
- **Failures.** An adapter raises ``AdapterError`` with an extraction problem, never
  text: a transport failure is ``transport_error``, which the window records. A
  reply the adapter refused rides on the error, so its usage still counts.
"""

from collections.abc import Callable
from typing import Annotated, Any, Literal, Protocol

from pydantic import Field, NonNegativeInt, PositiveInt

from earnings_themes.extraction.records import (
    AdapterIdentity,
    ExtractionProblem,
    Parameters,
)
from earnings_themes.records import NonBlank, Part, Sha256Hex


class Message(Part):
    role: Literal["system", "user", "assistant"]
    content: str


class RequestSubject(Part):
    """What a request is about: the R14.6 key's components beyond the rendered
    request and the adapter's identity."""

    doc_id: NonBlank
    canonical_hash: Sha256Hex
    window_id: NonBlank
    unit_ids: tuple[NonBlank, ...]
    window_budget: PositiveInt | None
    claim_limit: PositiveInt
    prompt_sha256: Sha256Hex
    extractor_version: NonBlank
    validator_version: NonBlank
    codebook_hash: Sha256Hex | None = None


class ModelRequest(Part):
    messages: Annotated[tuple[Message, ...], Field(min_length=2)]
    reply_schema: dict[str, Any]
    parameters: Parameters
    subject: RequestSubject


class Usage(Part):
    prompt_tokens: NonNegativeInt
    completion_tokens: NonNegativeInt


class ModelReply(Part):
    text: str
    usage: Usage | None = None
    """None when the server reports no usage."""
    model: str | None = None
    """The model the server names."""
    tool_calls: bool = False
    latency_ms: NonNegativeInt = 0
    cached: bool = False


class AdapterError(Exception):
    """An adapter's failure or refusal, as an extraction problem, with the refused
    reply, if one arrived."""

    def __init__(
        self, problem: ExtractionProblem, reply: ModelReply | None = None
    ) -> None:
        super().__init__(problem.value)
        self.problem = problem
        self.reply = reply


class ModelAdapter(Protocol):
    @property
    def identity(self) -> AdapterIdentity: ...

    def complete(self, request: ModelRequest) -> ModelReply: ...


SCRIPTED = AdapterIdentity(adapter_kind="scripted", model_id="scripted")


class ScriptedAdapter:
    """Replies from a script, for tests: ``script(request)`` returns the reply, or
    raises ``AdapterError``. It keeps every request it receives."""

    def __init__(
        self,
        script: Callable[[ModelRequest], ModelReply],
        identity: AdapterIdentity = SCRIPTED,
    ) -> None:
        self._script = script
        self._identity = identity
        self.requests: list[ModelRequest] = []

    @property
    def identity(self) -> AdapterIdentity:
        return self._identity

    def complete(self, request: ModelRequest) -> ModelReply:
        self.requests.append(request)
        return self._script(request)
