"""The adapter protocol and the R14.6-keyed cache (the Stage 7 spec, §The adapter
protocol and §The cache key; §Verification, R14.6)."""

import json
from collections.abc import Callable
from pathlib import Path

import pytest
from earnings_core import digest
from earnings_themes.extraction.adapters import (
    AdapterError,
    Message,
    ModelReply,
    ModelRequest,
    RequestSubject,
    ScriptedAdapter,
)
from earnings_themes.extraction.cache import (
    CachedAdapter,
    CacheEntry,
    CacheKey,
    CacheMode,
    cache_key,
)
from earnings_themes.extraction.records import (
    AdapterIdentity,
    ExtractionProblem,
    Parameters,
)
from earnings_themes.records import RecordError

SENTINEL = "SENTINEL-REPLY-NEVER-PRINTED"
IDENTITY = AdapterIdentity(adapter_kind="scripted", model_id="scripted")


def request(**changes) -> ModelRequest:
    subject = RequestSubject(
        doc_id="doc@walker-1#0123456789abcdef",
        canonical_hash="a" * 64,
        window_id="w-0-90",
        unit_ids=("sentence-0-40", "sentence-41-90"),
        window_budget=4000,
        claim_limit=500,
        prompt_sha256="b" * 64,
        extractor_version="pointer-traversal/1",
        validator_version="3",
    )
    fields = {
        "messages": (
            Message(role="system", content="The system text."),
            Message(role="user", content="[U1] One unit.\n[U2] Another unit."),
        ),
        "reply_schema": {"type": "object"},
        "parameters": Parameters(),
        "subject": subject,
    }
    return ModelRequest(**{**fields, **changes})


def subject(**changes) -> Callable:
    def change(req: ModelRequest, identity: AdapterIdentity):
        return (
            req.model_copy(update={"subject": req.subject.model_copy(update=changes)}),
            identity,
        )

    return change


def parameters(**changes) -> Callable:
    def change(req: ModelRequest, identity: AdapterIdentity):
        updated = req.parameters.model_copy(update=changes)
        return req.model_copy(update={"parameters": updated}), identity

    return change


def identity(**changes) -> Callable:
    def change(req: ModelRequest, ident: AdapterIdentity):
        return req, ident.model_copy(update=changes)

    return change


def schema(req: ModelRequest, ident: AdapterIdentity):
    return req.model_copy(update={"reply_schema": {"type": "array"}}), ident


def feedback(req: ModelRequest, ident: AdapterIdentity):
    turns = (
        Message(role="assistant", content="Not JSON."),
        Message(role="user", content="Your reply could not be used."),
    )
    return req.model_copy(update={"messages": req.messages + turns}), ident


CHANGES = {
    "doc_id": subject(doc_id="other@walker-1#0123456789abcdef"),
    "canonical_hash": subject(canonical_hash="c" * 64),
    "window_id": subject(window_id="w-0-41"),
    "unit_ids": subject(unit_ids=("sentence-0-40",)),
    "adapter_kind": identity(adapter_kind="local-openai"),
    "model_id": identity(model_id="another-model"),
    "weights_sha256": identity(weights_sha256="d" * 64),
    "runtime": identity(runtime="a-runtime"),
    "runtime_version": identity(runtime_version="1.0"),
    "structured": parameters(structured=False),
    "temperature": parameters(temperature=0.5),
    "seed": parameters(seed=1),
    "max_tokens": parameters(max_tokens=1024),
    "window_budget": subject(window_budget=None),
    "claim_limit": subject(claim_limit=300),
    "prompt_sha256": subject(prompt_sha256="e" * 64),
    "reply_schema_sha256": schema,
    "request_sha256": feedback,
    "extractor_version": subject(extractor_version="pointer-traversal/2"),
    "validator_version": subject(validator_version="4"),
    "codebook_hash": subject(codebook_hash="f" * 64),
}


def echo(ident: AdapterIdentity, calls: list) -> ScriptedAdapter:
    """A fake that counts its calls and names its own model."""

    def script(req: ModelRequest) -> ModelReply:
        calls.append(req)
        return ModelReply(text='{"candidates": []}', model=ident.model_id)

    return ScriptedAdapter(script, ident)


def test_every_key_component_has_a_case() -> None:
    assert set(CHANGES) == set(CacheKey.model_fields)


@pytest.mark.parametrize("field", sorted(CHANGES))
def test_changing_one_key_component_misses(field: str, tmp_path: Path) -> None:
    """R14.6: changing any one component changes only that field of the key, and the
    inner adapter is called again."""
    changed_request, changed_identity = CHANGES[field](request(), IDENTITY)
    before = cache_key(request(), IDENTITY)
    after = cache_key(changed_request, changed_identity)
    assert [
        f for f in CacheKey.model_fields if getattr(before, f) != getattr(after, f)
    ] == [field]
    calls: list = []
    CachedAdapter(echo(IDENTITY, calls), tmp_path, CacheMode.LIVE).complete(request())
    again = CachedAdapter(echo(changed_identity, calls), tmp_path, CacheMode.LIVE)
    reply = again.complete(changed_request)
    assert (len(calls), reply.cached) == (2, False)


def test_an_identical_key_hits_and_calls_nothing(tmp_path: Path) -> None:
    calls: list = []
    first = CachedAdapter(echo(IDENTITY, calls), tmp_path, CacheMode.LIVE)
    stored = first.complete(request())
    for mode in CacheMode:
        hit = CachedAdapter(echo(IDENTITY, calls), tmp_path, mode).complete(request())
        assert hit == stored.model_copy(update={"cached": True})
    assert len(calls) == 1


def test_a_replay_miss_calls_nothing(tmp_path: Path) -> None:
    calls: list = []
    replay = CachedAdapter(echo(IDENTITY, calls), tmp_path, CacheMode.REPLAY)
    with pytest.raises(AdapterError) as raised:
        replay.complete(request())
    assert (raised.value.problem, calls) == (ExtractionProblem.REPLAY_MISS, [])
    assert list(tmp_path.iterdir()) == []


def test_a_mode_given_as_its_value_reads_as_the_member(tmp_path: Path) -> None:
    """A command passes its mode as a string: ``"replay"`` still calls nothing, and a
    misspelled mode refuses construction rather than calling the model."""
    calls: list = []
    replay = CachedAdapter(echo(IDENTITY, calls), tmp_path, "replay")
    with pytest.raises(AdapterError) as raised:
        replay.complete(request())
    assert (raised.value.problem, calls) == (ExtractionProblem.REPLAY_MISS, [])
    assert list(tmp_path.iterdir()) == []
    with pytest.raises(ValueError):
        CachedAdapter(echo(IDENTITY, calls), tmp_path, "relpay")


def test_the_stored_entry_is_the_raw_reply_under_its_key(tmp_path: Path) -> None:
    calls: list = []
    CachedAdapter(echo(IDENTITY, calls), tmp_path, CacheMode.LIVE).complete(request())
    (path,) = tmp_path.iterdir()
    entry = CacheEntry.model_validate_json(path.read_bytes())
    assert entry.key == cache_key(request(), IDENTITY)
    assert (entry.reply.text, entry.reply.cached) == ('{"candidates": []}', False)


@pytest.mark.parametrize(
    "reply",
    [
        ModelReply(text="", model="scripted", tool_calls=True),
        ModelReply(text='{"candidates": []}', model="another-model"),
        ModelReply(text='{"candidates": []}'),
    ],
    ids=["tool-calls", "another-model", "no-model"],
)
def test_a_reply_with_tool_calls_or_another_model_is_never_stored(
    reply: ModelReply, tmp_path: Path
) -> None:
    adapter = ScriptedAdapter(lambda _: reply)
    assert CachedAdapter(adapter, tmp_path, CacheMode.LIVE).complete(request()) == reply
    assert list(tmp_path.iterdir()) == []


def test_a_transport_error_is_raised_and_nothing_is_stored(tmp_path: Path) -> None:
    def fail(_: ModelRequest) -> ModelReply:
        raise AdapterError(ExtractionProblem.TRANSPORT_ERROR)

    live = CachedAdapter(ScriptedAdapter(fail), tmp_path, CacheMode.LIVE)
    with pytest.raises(AdapterError) as raised:
        live.complete(request())
    assert raised.value.problem is ExtractionProblem.TRANSPORT_ERROR
    assert list(tmp_path.iterdir()) == []


def test_an_entry_that_does_not_read_is_refused_without_its_text(
    tmp_path: Path,
) -> None:
    """GS13: a stored reply may quote a document, so the refusal never prints it."""
    path = tmp_path / f"{digest(cache_key(request(), IDENTITY))}.json"
    path.write_text(json.dumps({"reply": {"text": SENTINEL}}), encoding="utf-8")
    calls: list = []
    replay = CachedAdapter(echo(IDENTITY, calls), tmp_path, CacheMode.REPLAY)
    with pytest.raises(RecordError) as refused:
        replay.complete(request())
    assert (refused.value.name, calls) == (path.name, [])
    assert SENTINEL not in str(refused.value)


def test_an_entry_under_another_key_s_name_is_refused(tmp_path: Path) -> None:
    calls: list = []
    CachedAdapter(echo(IDENTITY, calls), tmp_path, CacheMode.LIVE).complete(request())
    (path,) = tmp_path.iterdir()
    other, _ = CHANGES["seed"](request(), IDENTITY)
    CachedAdapter(echo(IDENTITY, calls), tmp_path, CacheMode.LIVE).complete(other)
    entries = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    swapped = next(name for name in entries if name != path.name)
    path.write_bytes(entries[swapped])
    with pytest.raises(ValueError, match="another key"):
        CachedAdapter(echo(IDENTITY, calls), tmp_path, CacheMode.REPLAY).complete(
            request()
        )


def test_the_scripted_adapter_keeps_its_requests() -> None:
    adapter = ScriptedAdapter(lambda _: ModelReply(text="", model="scripted"))
    adapter.complete(request())
    assert adapter.requests == [request()]
