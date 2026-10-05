"""Classifier protocol and invented scripted replies; no client startup or I/O."""

from collections.abc import Callable
from typing import Protocol

from earnings_core import digest

from earnings_themes.coding.records import CodingError, CodingRequest, checked
from earnings_themes.extraction.adapters import AdapterError, ModelReply
from earnings_themes.support.records import JudgeIdentity


class Classifier(Protocol):
    @property
    def identity(self) -> JudgeIdentity: ...

    def count_tokens(self, request: CodingRequest) -> int: ...

    def complete(self, request: CodingRequest) -> ModelReply: ...


class CodingTransportError(CodingError):
    """Fixed transport reason with an unprinted raw refusal and its usage."""

    def __init__(self, reason: str, reply: ModelReply | None = None) -> None:
        super().__init__(reason)
        self.reply = reply


def _invoke[T](callback: Callable[[], T]) -> T:
    try:
        return callback()
    except AdapterError as error:
        reply = None if error.reply is None else checked(error.reply, ModelReply)
        raise CodingTransportError(error.problem.value, reply) from None
    except CodingError as error:
        raise error from None
    except Exception:  # noqa: BLE001 - arbitrary callback diagnostics stay local
        raise CodingError("unexpected_error") from None


def _identity_hash(identity: Callable[[], JudgeIdentity]) -> str:
    try:
        return digest(checked(identity(), JudgeIdentity).model_dump(mode="json"))
    except Exception:  # noqa: BLE001 - arbitrary identity diagnostics stay local
        raise CodingError("model_mismatch") from None


def _unchanged_request(request: CodingRequest, expected_hash: str) -> None:
    try:
        current = checked(request, CodingRequest)
        if digest(current.model_dump(mode="json")) != expected_hash:
            raise CodingError("input_changed")
    except CodingError:
        raise CodingError("input_changed") from None


def _count_tokens(
    request: CodingRequest,
    identity: Callable[[], JudgeIdentity],
    counter: Callable[[CodingRequest], int],
) -> int:
    prepared = checked(request, CodingRequest)
    request_hash = digest(prepared.model_dump(mode="json"))
    identity_hash = _identity_hash(identity)
    try:
        tokens = _invoke(lambda: counter(prepared))
    finally:
        _unchanged_request(request, request_hash)
        _unchanged_request(prepared, request_hash)
        if _identity_hash(identity) != identity_hash:
            raise CodingError("model_mismatch")
    if type(tokens) is not int or tokens < 0:
        raise CodingError("malformed_record")
    return tokens


def _complete(
    request: CodingRequest,
    identity: Callable[[], JudgeIdentity],
    counter: Callable[[CodingRequest], int],
    dispatch: Callable[[CodingRequest], ModelReply],
    preflight: Callable[[], None] | None = None,
) -> ModelReply:
    prepared = checked(request, CodingRequest)
    request_hash = digest(prepared.model_dump(mode="json"))
    identity_hash = _identity_hash(identity)
    tokens = _count_tokens(prepared, identity, counter)
    _unchanged_request(request, request_hash)
    _unchanged_request(prepared, request_hash)
    if _identity_hash(identity) != identity_hash:
        raise CodingError("model_mismatch")
    runtime = checked(identity(), JudgeIdentity)
    if (
        prepared.parameters.max_tokens > runtime.output_limit
        or tokens + prepared.parameters.max_tokens > runtime.input_limit
    ):
        raise CodingError("input_too_long")
    if preflight is not None:
        preflight()
    try:
        reply = _invoke(lambda: dispatch(prepared))
    finally:
        _unchanged_request(request, request_hash)
        _unchanged_request(prepared, request_hash)
        if _identity_hash(identity) != identity_hash:
            raise CodingError("model_mismatch")
        if preflight is not None:
            preflight()
    return checked(reply, ModelReply)


class ScriptedClassifier:
    """Caller-supplied scripts keep invented requests local and unprinted."""

    def __init__(
        self,
        script: Callable[[CodingRequest], ModelReply],
        token_counter: Callable[[CodingRequest], int],
        identity: JudgeIdentity,
    ) -> None:
        self.script = script
        self._counter = token_counter
        self._identity = checked(identity, JudgeIdentity)
        if self._identity.hosting != "scripted":
            raise CodingError("model_mismatch")
        self.requests: list[CodingRequest] = []

    @property
    def identity(self) -> JudgeIdentity:
        return self._identity

    def count_tokens(self, request: CodingRequest) -> int:
        return _count_tokens(request, lambda: self.identity, self._counter)

    def complete(self, request: CodingRequest) -> ModelReply:
        def dispatch(prepared: CodingRequest) -> ModelReply:
            self.requests.append(prepared)
            return self.script(prepared)

        return _complete(request, lambda: self.identity, self._counter, dispatch)

    def __repr__(self) -> str:
        return f"ScriptedClassifier(requests={len(self.requests)})"

    __str__ = __repr__
