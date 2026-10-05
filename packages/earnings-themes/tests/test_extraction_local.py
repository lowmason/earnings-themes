"""The local adapter, over httpx's ``MockTransport`` (the Stage 7 spec, §The local
adapter, §Verification; R14.1, R14.7, ES19): the host refusal, a request body
without ``tools``, and the tool-call and model-mismatch refusals. No request leaves
the process."""

import json
import socket
from pathlib import Path

import httpx
import pytest
from earnings_themes.extraction.adapters import (
    AdapterError,
    Message,
    ModelRequest,
    RequestSubject,
    Usage,
)
from earnings_themes.extraction.local import (
    LocalAdapter,
    LocalModelConfig,
    load_local_config,
)
from earnings_themes.extraction.prompt import REPLY_SCHEMA
from earnings_themes.extraction.records import (
    AdapterIdentity,
    ExtractionProblem,
    Parameters,
)
from earnings_themes.records import RecordError

HASH = "0" * 64
MODEL = "invented-model"
CONFIG = LocalModelConfig(
    base_url="http://127.0.0.1:8080/v1",
    model_id=MODEL,
    weights_sha256="a" * 64,
    runtime="invented-runtime",
    runtime_version="1.0",
)
SENTINEL = "SENTINEL-BODY-NEVER-PRINTED"


def request(structured: bool = True) -> ModelRequest:
    subject = RequestSubject(
        doc_id="doc",
        canonical_hash=HASH,
        window_id="w-0-9",
        unit_ids=("sentence-0-9",),
        window_budget=4000,
        claim_limit=500,
        prompt_sha256=HASH,
        extractor_version="pointer-traversal/1",
        validator_version="3",
    )
    return ModelRequest(
        messages=(
            Message(role="system", content="Invented system text."),
            Message(role="user", content="[U1] Invented unit."),
        ),
        reply_schema=REPLY_SCHEMA,
        parameters=Parameters(structured=structured),
        subject=subject,
    )


def completion(
    content: str | None = '{"candidates": []}',
    model: str | None = MODEL,
    usage: bool = True,
    **message: object,
) -> dict:
    """A chat completion, as an OpenAI-compatible server returns one."""
    body: dict = {
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content, **message},
                "finish_reason": "stop",
            }
        ],
    }
    if model is not None:
        body["model"] = model
    if usage:
        body["usage"] = {
            "prompt_tokens": 12,
            "completion_tokens": 3,
            "total_tokens": 15,
        }
    return body


def serving(
    reply: dict | httpx.Response, sent: list[httpx.Request] | None = None
) -> LocalAdapter:
    """The adapter over a mock server that answers every request with ``reply``."""

    def handler(incoming: httpx.Request) -> httpx.Response:
        if sent is not None:
            sent.append(incoming)
        if isinstance(reply, httpx.Response):
            return reply
        return httpx.Response(200, json=reply)

    return LocalAdapter(CONFIG, transport=httpx.MockTransport(handler))


@pytest.mark.parametrize(
    "base_url",
    [
        "http://example.com/v1",
        "https://10.0.0.5:8080/v1",
        "http://127.0.0.1.example.com/v1",
        "http://localhost@example.com/v1",
        "http://[::2]:8080/v1",
        "ftp://127.0.0.1/v1",
        "127.0.0.1:8080/v1",
    ],
)
def test_a_host_off_this_machine_is_refused_when_built(base_url: str) -> None:
    config = CONFIG.model_copy(update={"base_url": base_url})
    with pytest.raises(ValueError, match="not on this machine") as refused:
        LocalAdapter(config)
    message = str(refused.value)
    assert base_url not in message


@pytest.mark.parametrize(
    ("base_url", "secret", "reason"),
    [
        (
            "http://invented:INVENTED-SECRET@127.0.0.1:8080/v1",
            "INVENTED-SECRET",
            "carries credentials",
        ),
        ("http://127.0.0.1:INVENTEDPORT/v1", "INVENTEDPORT", "port is not a number"),
        (
            "http://invented:INVENTED-SECRET" + chr(0x2100) + "@127.0.0.1:8080/v1",
            "INVENTED-SECRET",
            "the base URL is not a valid URL",
        ),
    ],
    ids=["credentials", "bad-port", "invalid"],
)
def test_a_url_with_credentials_or_a_bad_port_is_refused_naming_no_value(
    base_url: str, secret: str, reason: str
) -> None:
    """The refusal names no part of the URL: a credential would otherwise be printed.
    urllib's own errors quote a bad port and, for U+2100, which NFKC expands to a
    slash, the whole netloc, so none is the cause or shown as the context (GS13)."""
    config = CONFIG.model_copy(update={"base_url": base_url})
    with pytest.raises(ValueError, match=reason) as refused:
        LocalAdapter(config)
    message = str(refused.value)
    assert secret not in message
    assert refused.value.__cause__ is None
    assert refused.value.__context__ is None or refused.value.__suppress_context__


@pytest.mark.parametrize(
    "base_url",
    ["http://127.0.0.1:8080/v1", "http://localhost:11434/v1/", "http://[::1]:8000/v1"],
)
def test_a_loopback_host_is_accepted(base_url: str, no_network) -> None:
    sent: list[httpx.Request] = []
    config = CONFIG.model_copy(update={"base_url": base_url})
    adapter = LocalAdapter(
        config,
        transport=httpx.MockTransport(
            lambda r: sent.append(r) or httpx.Response(200, json=completion())
        ),
    )
    adapter.complete(request())
    (incoming,) = sent
    assert str(incoming.url) == f"{base_url.rstrip('/')}/chat/completions"
    assert no_network == []


@pytest.mark.parametrize("structured", [True, False])
def test_the_body_carries_no_tools_and_no_key(structured: bool, no_network) -> None:
    sent: list[httpx.Request] = []
    serving(completion(), sent).complete(request(structured))
    (incoming,) = sent
    body = json.loads(incoming.content)
    expected = {"model", "messages", "temperature", "seed", "max_tokens"}
    assert set(body) == expected | ({"response_format"} if structured else set())
    assert (incoming.method, "authorization" in incoming.headers) == ("POST", False)
    assert body["messages"] == [
        {"role": "system", "content": "Invented system text."},
        {"role": "user", "content": "[U1] Invented unit."},
    ]
    assert (body["temperature"], body["seed"], body["max_tokens"]) == (0.0, 0, 2048)
    if structured:
        assert body["response_format"] == {
            "type": "json_schema",
            "json_schema": {"name": "reply", "strict": True, "schema": REPLY_SCHEMA},
        }
    assert no_network == []


def test_a_reply_brings_its_text_usage_and_model(no_network) -> None:
    reply = serving(completion('{"candidates": []}')).complete(request())
    assert (reply.text, reply.usage, reply.model, reply.tool_calls) == (
        '{"candidates": []}',
        Usage(prompt_tokens=12, completion_tokens=3),
        MODEL,
        False,
    )
    unreported = serving(completion(usage=False)).complete(request())
    assert unreported.usage is None


@pytest.mark.parametrize(
    "message",
    [
        {"tool_calls": [{"id": "1", "type": "function", "function": {"name": "x"}}]},
        {"function_call": {"name": "x", "arguments": "{}"}},
    ],
    ids=["tool_calls", "function_call"],
)
def test_a_tool_call_is_refused_with_its_usage(message: dict) -> None:
    """R14.7: no tool exists, so a reply that calls one is refused; its usage rides
    on the error, so it still counts."""
    with pytest.raises(AdapterError) as refused:
        serving(completion(content=None, **message)).complete(request())
    assert refused.value.problem is ExtractionProblem.TOOL_CALL_REFUSED
    assert refused.value.reply is not None
    assert refused.value.reply.usage == Usage(prompt_tokens=12, completion_tokens=3)


@pytest.mark.parametrize("model", ["another-model", None], ids=["another", "none"])
def test_a_reply_from_another_model_is_refused(model: str | None) -> None:
    with pytest.raises(AdapterError) as refused:
        serving(completion(model=model)).complete(request())
    assert refused.value.problem is ExtractionProblem.MODEL_MISMATCH


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(500, text=SENTINEL),
        httpx.Response(307, headers={"location": "http://example.com/v1"}),
        httpx.Response(200, text=SENTINEL),
        httpx.Response(200, json={"choices": [], "detail": SENTINEL}),
    ],
    ids=["error-status", "redirect", "not-json", "no-choice"],
)
def test_a_reply_that_is_not_a_completion_is_a_transport_error(
    response: httpx.Response,
) -> None:
    """A redirect is never followed. The error quotes nothing of the body (GS13)."""
    sent: list[httpx.Request] = []
    with pytest.raises(AdapterError) as refused:
        serving(response, sent).complete(request())
    assert refused.value.problem is ExtractionProblem.TRANSPORT_ERROR
    assert len(sent) == 1
    assert SENTINEL not in str(refused.value)
    assert SENTINEL not in str(refused.value.__cause__)
    assert refused.value.__cause__ is not None or refused.value.__suppress_context__


def test_a_connection_error_is_a_transport_error() -> None:
    def refuse(incoming: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=incoming)

    adapter = LocalAdapter(CONFIG, transport=httpx.MockTransport(refuse))
    with pytest.raises(AdapterError) as refused:
        adapter.complete(request())
    assert refused.value.problem is ExtractionProblem.TRANSPORT_ERROR


def test_no_proxy_is_read_from_the_environment(
    monkeypatch: pytest.MonkeyPatch, no_network
) -> None:
    """With the environment trusted, the request would go to the proxy these name.
    httpx reads no proxy when a test transport replaces its own, so this runs the
    real transport, whose connection is refused here before any packet is sent."""
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "all_proxy"):
        monkeypatch.setenv(name, "http://proxy.invalid:9")
    for name in ("NO_PROXY", "no_proxy"):
        monkeypatch.delenv(name, raising=False)
    tried: list[object] = []

    def refuse(address: object, *args: object, **kwargs: object) -> object:
        tried.append(address)
        raise ConnectionRefusedError("the network is blocked here")

    monkeypatch.setattr(socket, "create_connection", refuse)
    with pytest.raises(AdapterError) as refused:
        LocalAdapter(CONFIG).complete(request())
    assert refused.value.problem is ExtractionProblem.TRANSPORT_ERROR
    assert (tried, no_network) == ([("127.0.0.1", 8080)], [])


def test_the_identity_comes_from_configuration() -> None:
    assert LocalAdapter(CONFIG).identity == AdapterIdentity(
        adapter_kind="local",
        model_id=MODEL,
        weights_sha256="a" * 64,
        runtime="invented-runtime",
        runtime_version="1.0",
    )


def test_the_configuration_is_read_from_toml(tmp_path: Path) -> None:
    path = tmp_path / "local-model.toml"
    path.write_text(
        'base_url = "http://127.0.0.1:8080/v1"\n'
        f'model_id = "{MODEL}"\n'
        f'weights_sha256 = "{"a" * 64}"\n'
        'runtime = "invented-runtime"\n'
        'runtime_version = "1.0"\n',
        encoding="utf-8",
    )
    assert load_local_config(path) == CONFIG
    path.write_text(path.read_text(encoding="utf-8") + f'api_key = "{SENTINEL}"\n')
    with pytest.raises(RecordError) as refused:
        load_local_config(path)
    assert refused.value.problems == ("<key>: Extra inputs are not permitted",)
    assert SENTINEL not in str(refused.value)
