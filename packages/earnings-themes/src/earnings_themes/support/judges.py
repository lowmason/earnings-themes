"""Typed, independent judges over caller-supplied local or scripted transports."""

import json
from collections.abc import Callable
from typing import Any, Literal, Protocol

from earnings_core import digest
from pydantic import Field

from earnings_themes.extraction.adapters import AdapterError, Message, ModelReply
from earnings_themes.extraction.records import AdapterIdentity, Parameters
from earnings_themes.records import NonBlank, Sha256Hex
from earnings_themes.support.problems import SupportError, unexpected_error
from earnings_themes.support.records import (
    SUPPORT_VERSION,
    JudgeAnswer,
    JudgeIdentity,
    Presentation,
    ResolvedInput,
    SafePart,
    parse_support,
)
from earnings_themes.support.resolve import _validated


class JudgeSubject(SafePart):
    target_id: NonBlank
    input_hash: Sha256Hex
    codebook_hash: Sha256Hex
    presentation: Presentation
    prompt_hash: Sha256Hex
    schema_hash: Sha256Hex
    support_version: Literal["semantic-support/1"] = SUPPORT_VERSION
    validator_version: NonBlank


class JudgeRequest(SafePart):
    messages: tuple[Message, ...] = Field(min_length=2, repr=False)
    reply_schema: dict[str, Any] = Field(repr=False)
    parameters: Parameters
    subject: JudgeSubject


class Judge(Protocol):
    @property
    def identity(self) -> JudgeIdentity: ...

    def count_tokens(self, request: JudgeRequest) -> int: ...

    def complete(self, request: JudgeRequest) -> ModelReply: ...


def validate_panel(
    extractor_family: str, identities: tuple[JudgeIdentity, ...]
) -> tuple[JudgeIdentity, JudgeIdentity]:
    """Require explicit family lineage; model aliases never establish lineage."""
    try:
        if not isinstance(extractor_family, str) or not extractor_family.strip():
            raise SupportError("invalid_panel")
        checked = tuple(_validated(i, JudgeIdentity) for i in identities)
        if (
            len(checked) != 2
            or checked[0].family == checked[1].family
            or all(i.family == extractor_family for i in checked)
        ):
            raise SupportError("invalid_panel")
        return checked[0], checked[1]
    except (SupportError, TypeError, AttributeError):
        raise SupportError("invalid_panel") from None


def parse_answer(
    reply: ModelReply, input: ResolvedInput, identity: JudgeIdentity
) -> JudgeAnswer:
    """A closed answer with exactly one contribution for each original quote."""
    try:
        reply = ModelReply.model_validate_json(reply.model_dump_json())
    except (ValueError, TypeError, AttributeError):
        raise SupportError("malformed_reply") from None
    identity = _validated(identity, JudgeIdentity)
    if reply.tool_calls:
        raise SupportError("tool_call_refused")
    if reply.model != identity.runtime.model_id:
        raise SupportError("model_mismatch")
    try:
        data = json.loads(reply.text)
        answer = parse_support(data, JudgeAnswer)
    except (ValueError, TypeError):
        raise SupportError("malformed_reply") from None
    supplied = [ref.quote_id for ref in input.evidence]
    returned = [entry.quote_id for entry in answer.quote_assessments]
    if len(returned) != len(set(returned)) or set(returned) != set(supplied):
        raise SupportError("invalid_references")
    return answer


class SupportTransportError(SupportError):
    """Fixed transport refusal carrying local usage without printable reply text."""

    def __init__(self, reason: str, reply: ModelReply | None = None) -> None:
        super().__init__(reason)
        self.reply = reply


def transport_weights_hash(identity: JudgeIdentity) -> str:
    """Bind Stage 7's one weights hash to Stage 8's explicit file manifest.

    One file uses that file's SHA-256. Multiple files use the canonical digest of
    path/hash records sorted by relative path. An empty local manifest is refused.
    """
    files = identity.runtime.files
    if not files:
        raise SupportError("model_mismatch")
    if len(files) == 1:
        return files[0].sha256
    return digest(
        [
            f.model_dump(mode="json")
            for f in sorted(files, key=lambda f: f.relative_path)
        ]
    )


class JudgeBinding:
    """Caller-supplied complete tokenizer/chat-template counter for this runtime.

    The input limit is the total context ceiling: full prompt plus reserved output.
    The output limit separately bounds max_tokens. No heuristic or clipping occurs.
    """

    def __init__(
        self,
        identity: JudgeIdentity,
        transport: Any,
        token_counter: Callable[[JudgeRequest], int],
    ) -> None:
        self._identity = _validated(identity, JudgeIdentity)
        self._transport = transport
        self._token_counter = token_counter
        self._preflight()

    @property
    def identity(self) -> JudgeIdentity:
        return self._identity

    def _preflight(self) -> None:
        try:
            runtime = self.identity.runtime
            transport = _validated(self._transport.identity, AdapterIdentity)
            if self.identity.hosting == "local":
                if (
                    transport.adapter_kind != "local"
                    or transport.model_id != runtime.model_id
                    or transport.weights_sha256 != transport_weights_hash(self.identity)
                    or transport.runtime != runtime.runtime
                    or transport.runtime_version != runtime.runtime_version
                ):
                    raise SupportError("model_mismatch")
            elif (
                transport.adapter_kind != "scripted"
                or transport.model_id != runtime.model_id
            ):
                raise SupportError("model_mismatch")
        except Exception:  # noqa: BLE001 - arbitrary transport diagnostics stay local
            raise SupportError("model_mismatch") from None

    def count_tokens(self, request: JudgeRequest) -> int:
        try:
            tokens = self._token_counter(_validated(request, JudgeRequest))
        except SupportError as error:
            raise error from None
        except Exception as error:  # noqa: BLE001 - tokenizer diagnostics stay local
            raise unexpected_error(error) from None
        if type(tokens) is not int or tokens < 0:
            raise SupportError("malformed_reply")
        return tokens

    def complete(self, request: JudgeRequest) -> ModelReply:
        self._preflight()
        request = _validated(request, JudgeRequest)
        tokens = self.count_tokens(request)
        if (
            request.parameters.max_tokens > self.identity.output_limit
            or tokens + request.parameters.max_tokens > self.identity.input_limit
        ):
            raise SupportError("input_too_long")
        try:
            return self._transport.complete(request)
        except AdapterError as error:
            raise SupportTransportError(error.problem.value, error.reply) from None
        except SupportError as error:
            raise error from None
        except Exception as error:  # noqa: BLE001 - transport diagnostics stay local
            raise unexpected_error(error) from None

    def __repr__(self) -> str:
        return "JudgeBinding()"

    __str__ = __repr__


class ScriptedJudge:
    """Test-only trials; scripts and requests remain local and unprinted."""

    def __init__(
        self,
        script: Callable[[JudgeRequest], ModelReply],
        token_counter: Callable[[JudgeRequest], int],
        identity: JudgeIdentity,
    ) -> None:
        self.script = script
        self._token_counter = token_counter
        self._identity = _validated(identity, JudgeIdentity)
        if self._identity.hosting != "scripted":
            raise SupportError("invalid_panel")
        self.requests: list[JudgeRequest] = []

    @property
    def identity(self) -> JudgeIdentity:
        return self._identity

    def count_tokens(self, request: JudgeRequest) -> int:
        return self._token_counter(request)

    def complete(self, request: JudgeRequest) -> ModelReply:
        self.requests.append(request)
        return self.script(request)

    def __repr__(self) -> str:
        return f"ScriptedJudge(requests={len(self.requests)})"

    __str__ = __repr__
