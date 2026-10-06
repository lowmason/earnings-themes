"""Identity and context checks over caller-supplied local/scripted transports."""

from collections.abc import Callable
from typing import Any

from earnings_themes.coding.adapters import (
    CodingTransportError,
    _complete,
    _count_tokens,
)
from earnings_themes.coding.records import CodingError, CodingRequest, checked
from earnings_themes.extraction.adapters import ModelReply
from earnings_themes.extraction.records import AdapterIdentity
from earnings_themes.support.judges import transport_weights_hash
from earnings_themes.support.records import JudgeIdentity

__all__ = ["ClassifierBinding", "CodingTransportError"]


class ClassifierBinding:
    """Complete tokenizer/chat-template/schema counting belongs to the caller.

    The input ceiling includes the full prompt plus reserved output; no clipping
    or heuristic tokenizer is supplied. Construction chooses no model or client.
    """

    def __init__(
        self,
        identity: JudgeIdentity,
        transport: Any,
        token_counter: Callable[[CodingRequest], int],
    ) -> None:
        self._identity = checked(identity, JudgeIdentity)
        self._transport = transport
        self._counter = token_counter
        self.preflight()

    @property
    def identity(self) -> JudgeIdentity:
        return self._identity

    def preflight(self) -> None:
        try:
            identity = checked(self.identity, JudgeIdentity)
            transport = checked(self._transport.identity, AdapterIdentity)
            runtime = identity.runtime
            if identity.hosting == "local":
                valid = (
                    transport.adapter_kind == "local"
                    and transport.model_id == runtime.model_id
                    and transport.weights_sha256 == transport_weights_hash(identity)
                    and transport.runtime == runtime.runtime
                    and transport.runtime_version == runtime.runtime_version
                )
            else:
                valid = (
                    transport.adapter_kind == "scripted"
                    and transport.model_id == runtime.model_id
                )
            if not valid:
                raise CodingError("model_mismatch")
        except Exception:  # noqa: BLE001 - arbitrary transport diagnostics stay local
            raise CodingError("model_mismatch") from None

    def count_tokens(self, request: CodingRequest) -> int:
        self.preflight()
        try:
            return _count_tokens(request, lambda: self.identity, self._counter)
        finally:
            self.preflight()

    def complete(self, request: CodingRequest) -> ModelReply:
        self.preflight()
        return _complete(
            request,
            lambda: self.identity,
            self._counter,
            self._transport.complete,
            self.preflight,
        )

    def __repr__(self) -> str:
        return "ClassifierBinding()"

    __str__ = __repr__
