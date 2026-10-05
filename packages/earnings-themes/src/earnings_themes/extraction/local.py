"""The local adapter: one OpenAI-compatible chat endpoint on this machine, over httpx
(the Stage 7 spec, §The local adapter; R14.1, R14.7, ES15, ES19).

- **Hosts.** Construction refuses a base URL whose host is not 127.0.0.1, ::1, or
  localhost, so no hosted, billable endpoint is reachable (R14.1). It refuses one
  that carries credentials, since the adapter sends no key, one whose port is not a
  number from 0 to 65535, and one that does not parse. No refusal names any part of
  the URL, so a credential typed into it is never printed. The client reads no proxy
  from the environment and follows no redirect, so no request leaves the machine.
- **The request.** A POST to ``<base>/chat/completions`` with the messages and the
  parameters, and in structured mode a strict ``response_format`` JSON schema
  (ES19). It never sends ``tools`` or ``tool_choice``, and sends no API key.
- **The reply.** One that carries a tool call is ``tool_call_refused``, and one that
  names a model other than the configured one, or none, is ``model_mismatch``, so a
  swapped model is never cached under another model's identity. The refused reply
  rides on the error, so its usage still counts. A connection error, a timeout, an
  error status, or a body that is not a chat completion is ``transport_error``.
- **Identity.** The model ID, the weights' SHA-256, and the runtime's name and
  version come from configuration, as ADR 0004 records them. This is the only themes
  module that imports httpx, behind the ``local-model`` extra, and no other themes
  module imports it (ES15).
"""

import time
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeInt,
    PositiveFloat,
    ValidationError,
)

from earnings_themes.extraction.adapters import (
    AdapterError,
    ModelReply,
    ModelRequest,
    Usage,
)
from earnings_themes.extraction.records import AdapterIdentity, ExtractionProblem
from earnings_themes.records import NonBlank, Part, Sha256Hex, parse
from earnings_themes.tomlfile import read

LOOPBACK = frozenset({"127.0.0.1", "::1", "localhost"})
ADAPTER_KIND = "local"


class LocalModelConfig(Part):
    """The local model's endpoint and identity, as ADR 0004 records them."""

    base_url: NonBlank
    """The server's OpenAI-compatible root, such as ``http://127.0.0.1:8080/v1``."""
    model_id: NonBlank
    """The model the server names in each reply."""
    weights_sha256: Sha256Hex
    runtime: NonBlank
    runtime_version: NonBlank
    structured: bool = True
    """Whether the runtime honors a strict JSON-schema ``response_format``; a run over
    this model sets its ``Parameters.structured`` from it (ES19)."""
    timeout_s: PositiveFloat = 300.0


def load_local_config(path: Path) -> LocalModelConfig:
    """The configuration in the TOML file at ``path``; a refusal is a
    ``RecordError``."""
    return parse(read(path), LocalModelConfig, path.name)


def loopback_url(base_url: str) -> str:
    """``base_url`` without a trailing slash. Raises ``ValueError``, naming no part
    of the URL, unless its scheme is http or https, its host is a loopback name
    (R14.1), it carries no credentials, and its port, if it has one, is a number
    from 0 to 65535."""
    try:
        parts = urlsplit(base_url)
    except ValueError:
        # Its message may quote the netloc, userinfo included.
        raise ValueError("the base URL is not a valid URL") from None
    if parts.scheme not in {"http", "https"} or parts.hostname not in LOOPBACK:
        raise ValueError(
            "the base URL is not on this machine: the local adapter reaches only"
            f" {sorted(LOOPBACK)}"
        )
    if parts.username is not None or parts.password is not None:
        raise ValueError(
            "the base URL carries credentials: the local adapter sends no key"
        )
    try:
        _ = parts.port  # urllib's own message quotes a bad port
    except ValueError:
        raise ValueError(
            "the base URL's port is not a number from 0 to 65535"
        ) from None
    return base_url.rstrip("/")


class _Lenient(BaseModel):
    """A server's JSON, read for the fields the adapter needs, ignoring the rest."""

    model_config = ConfigDict(extra="ignore", frozen=True)


class _Usage(_Lenient):
    prompt_tokens: NonNegativeInt
    completion_tokens: NonNegativeInt


class _Message(_Lenient):
    content: str | None = None
    tool_calls: list[Any] | None = None
    function_call: Any = None


class _Choice(_Lenient):
    message: _Message


class _Completion(_Lenient):
    model: str | None = None
    choices: list[_Choice] = Field(min_length=1)
    usage: _Usage | None = None


class LocalAdapter:
    """The adapter over a local OpenAI-compatible server. ``transport`` replaces
    httpx's own, for tests."""

    def __init__(
        self,
        config: LocalModelConfig,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._url = f"{loopback_url(config.base_url)}/chat/completions"
        self._config = config
        self._transport = transport
        self._identity = AdapterIdentity(
            adapter_kind=ADAPTER_KIND,
            model_id=config.model_id,
            weights_sha256=config.weights_sha256,
            runtime=config.runtime,
            runtime_version=config.runtime_version,
        )

    @property
    def identity(self) -> AdapterIdentity:
        return self._identity

    def body(self, request: ModelRequest) -> dict[str, Any]:
        """The JSON body sent for ``request``: never ``tools`` or ``tool_choice``."""
        parameters = request.parameters
        body: dict[str, Any] = {
            "model": self._config.model_id,
            "messages": [message.model_dump() for message in request.messages],
            "temperature": parameters.temperature,
            "seed": parameters.seed,
            "max_tokens": parameters.max_tokens,
        }
        if parameters.structured:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "reply",
                    "strict": True,
                    "schema": request.reply_schema,
                },
            }
        return body

    def complete(self, request: ModelRequest) -> ModelReply:
        started = time.monotonic()
        try:
            with httpx.Client(
                transport=self._transport,
                timeout=self._config.timeout_s,
                trust_env=False,
                follow_redirects=False,
            ) as client:
                response = client.post(self._url, json=self.body(request))
                response.raise_for_status()
        except httpx.HTTPError as error:
            raise AdapterError(ExtractionProblem.TRANSPORT_ERROR) from error
        try:
            completion = _Completion.model_validate_json(response.content)
        except ValidationError:
            # Its message quotes the body, which may quote a document (GS13).
            raise AdapterError(ExtractionProblem.TRANSPORT_ERROR) from None
        message = completion.choices[0].message
        usage = completion.usage
        reply = ModelReply(
            text=message.content or "",
            usage=None if usage is None else Usage(**usage.model_dump()),
            model=completion.model,
            tool_calls=bool(message.tool_calls) or message.function_call is not None,
            latency_ms=round((time.monotonic() - started) * 1000),
        )
        if reply.tool_calls:
            raise AdapterError(ExtractionProblem.TOOL_CALL_REFUSED, reply)
        if reply.model != self._identity.model_id:
            raise AdapterError(ExtractionProblem.MODEL_MISMATCH, reply)
        return reply
