"""Immutable raw coding cache bindings and failure behavior; invented data only."""

import json
import traceback
import warnings
from datetime import date
from pathlib import Path

import pytest
from earnings_core import canonical_json, digest
from earnings_themes.coding import cache as cache_module
from earnings_themes.coding.cache import (
    CodingCache,
    CodingCacheEntry,
    coding_key,
    raw_reply_hash,
)
from earnings_themes.coding.records import CodingError, checked
from earnings_themes.extraction.adapters import ModelReply, Usage
from earnings_themes.support.records import FileHash, WeightLicense

PRIVATE = "INVENTED_PRIVATE_REPLY"


def test_raw_reply_round_trip_retains_transport_refusal(
    coding_request, classifier_identity, tmp_path
):
    cache = CodingCache(tmp_path, "live")
    reply = ModelReply(text=PRIVATE, model="wrong-model")
    ref = cache.put(
        coding_request,
        classifier_identity,
        reply,
        input_tokens=5,
        refusal_reason="model_mismatch",
    )
    entry = CodingCache(tmp_path, "replay").get(coding_request, classifier_identity)
    assert entry.reply == reply
    assert entry.refusal_reason == "model_mismatch"
    assert entry.input_tokens == 5
    assert len(cache.artifact_hash(ref)) == 64
    assert PRIVATE not in repr(entry) and PRIVATE not in str(cache)
    assert (tmp_path / ref).read_bytes() == canonical_json(
        entry.model_dump(mode="json")
    )


def test_identical_binding_hits_changed_input_misses(
    coding_request, classifier_identity, tmp_path
):
    cache = CodingCache(tmp_path, "live")
    cache.put(
        coding_request,
        classifier_identity,
        ModelReply(
            model=classifier_identity.runtime.model_id,
            text='{"theme_ids":[],"attributes":{}}',
        ),
        input_tokens=5,
    )
    assert cache.get(coding_request, classifier_identity) is not None
    changed = coding_request.model_copy(
        update={
            "subject": coding_request.subject.model_copy(
                update={"input_hash": "0" * 64}
            )
        }
    )
    assert cache.get(changed, classifier_identity) is None


REQUEST_MUTATIONS = [
    ("subject", "doc_id", "other-document"),
    ("subject", "claim_id", "other-claim"),
    ("subject", "input_hash", "0" * 64),
    ("subject", "prompt_hash", "0" * 64),
    ("subject", "schema_hash", "0" * 64),
    ("subject", "validator_version", "next"),
    ("codebook", "codebook_id", "other-book"),
    ("codebook", "codebook_version", 1),
    ("codebook", "content_hash", "0" * 64),
    ("parameters", "temperature", 0.5),
    ("parameters", "seed", 18),
    ("parameters", "max_tokens", 65),
    ("parameters", "structured", False),
    ("messages", "system", PRIVATE),
    ("messages", "user", PRIVATE),
    ("messages", "append", PRIVATE),
    ("reply_schema", "extra", PRIVATE),
]


def changed_request(request, area, field, value):
    if area == "codebook":
        book = request.subject.codebook.model_copy(update={field: value})
        return request.model_copy(
            update={"subject": request.subject.model_copy(update={"codebook": book})}
        )
    if area in {"subject", "parameters"}:
        return request.model_copy(
            update={area: getattr(request, area).model_copy(update={field: value})}
        )
    if area == "reply_schema":
        return request.model_copy(
            update={"reply_schema": dict(request.reply_schema, **{field: value})}
        )
    messages = list(request.messages)
    if field == "append":
        messages.append(messages[1].model_copy(update={"content": value}))
    else:
        index = 0 if field == "system" else 1
        messages[index] = messages[index].model_copy(update={"content": value})
    return request.model_copy(update={"messages": tuple(messages)})


@pytest.mark.parametrize("area,field,value", REQUEST_MUTATIONS)
def test_every_request_component_changes_cache_binding(
    coding_request, classifier_identity, tmp_path, area, field, value
):
    cache = CodingCache(tmp_path, "live")
    cache.put(
        coding_request, classifier_identity, ModelReply(text=PRIVATE), input_tokens=5
    )
    changed = changed_request(coding_request, area, field, value)
    assert coding_key(changed, classifier_identity) != coding_key(
        coding_request, classifier_identity
    )
    assert cache.get(changed, classifier_identity) is None


@pytest.mark.parametrize(
    "area,field,value",
    [
        ("identity", "family", "other-family"),
        ("identity", "input_limit", 9999),
        ("identity", "output_limit", 2047),
        ("runtime", "model_id", "other-model"),
        ("runtime", "revision", "other-revision"),
        ("runtime", "runtime", "other-runtime"),
        ("runtime", "runtime_version", "next"),
        ("runtime", "device", "other-device"),
        ("runtime", "precision", "other-precision"),
        ("runtime", "encoding_version", "next"),
    ],
)
def test_every_identity_component_changes_cache_binding(
    coding_request, classifier_identity, tmp_path, area, field, value
):
    cache = CodingCache(tmp_path, "live")
    cache.put(
        coding_request, classifier_identity, ModelReply(text=PRIVATE), input_tokens=5
    )
    changed = (
        classifier_identity.model_copy(update={field: value})
        if area == "identity"
        else classifier_identity.model_copy(
            update={
                "runtime": classifier_identity.runtime.model_copy(update={field: value})
            }
        )
    )
    assert cache.get(coding_request, changed) is None


@pytest.mark.parametrize(
    "area,field,value",
    [
        ("identity", "hosting", "scripted"),
        ("file", "relative_path", "other.gguf"),
        ("file", "sha256", "b" * 64),
        ("runtime", "files", ()),
        ("license", "source_url", "https://example.invalid/other"),
        ("license", "terms_reference", "other-terms"),
        ("license", "intended_use", "other-use"),
        ("license", "verified_on", date(2026, 10, 4)),
    ],
)
def test_local_hosting_files_and_license_change_cache_binding(
    coding_request, classifier_identity, tmp_path, area, field, value
):
    identity = classifier_identity.model_copy(
        update={
            "hosting": "local",
            "runtime": classifier_identity.runtime.model_copy(
                update={
                    "files": (FileHash(relative_path="invented.gguf", sha256="a" * 64),)
                }
            ),
            "weight_license": WeightLicense(
                source_url="https://example.invalid/weights",
                terms_reference="invented-terms",
                intended_use="invented-test",
                verified_on=date(2026, 10, 5),
                permits_use=True,
            ),
        }
    )
    cache = CodingCache(tmp_path, "live")
    cache.put(coding_request, identity, ModelReply(text=PRIVATE), input_tokens=5)
    if area == "identity":
        changed = identity.model_copy(update={field: value})
    elif area == "license":
        changed = identity.model_copy(
            update={
                "weight_license": identity.weight_license.model_copy(
                    update={field: value}
                )
            }
        )
    else:
        update = (
            {field: value}
            if area == "runtime"
            else {
                "files": (identity.runtime.files[0].model_copy(update={field: value}),)
            }
        )
        changed = identity.model_copy(
            update={"runtime": identity.runtime.model_copy(update=update)}
        )
    assert cache.get(coding_request, changed) is None


@pytest.mark.parametrize(
    "refusal_reason,model,tools",
    [
        ("transport_error", None, False),
        ("model_mismatch", "wrong-model", False),
        ("tool_call_refused", "invented-classifier", True),
    ],
)
def test_raw_refusals_replay_usage_without_accepted_verdict(
    coding_request, classifier_identity, tmp_path, refusal_reason, model, tools
):
    cache = CodingCache(tmp_path, "live")
    reply = ModelReply(
        text=PRIVATE,
        model=model,
        tool_calls=tools,
        usage=Usage(prompt_tokens=8, completion_tokens=3),
        latency_ms=2,
    )
    cache.put(
        coding_request,
        classifier_identity,
        reply,
        input_tokens=5,
        refusal_reason=refusal_reason,
    )
    entry = CodingCache(tmp_path, "replay").get(coding_request, classifier_identity)
    assert entry.reply == reply and entry.reply.usage == reply.usage
    assert entry.refusal_reason == refusal_reason
    assert set(entry.model_dump()) == {
        "schema_version",
        "key",
        "request",
        "identity",
        "input_tokens",
        "reply",
        "reply_hash",
        "refusal_reason",
    }
    assert entry.reply_hash == raw_reply_hash(reply, refusal_reason, 5)


@pytest.mark.parametrize("mode", ["fresh", "LIVE", "", None, True])
def test_invalid_modes_refuse_before_io(tmp_path, mode):
    with pytest.raises(CodingError, match="^malformed_record$"):
        CodingCache(tmp_path / "unused", mode)
    assert list(tmp_path.iterdir()) == []


def test_constructor_and_missing_lookup_have_no_write_side_effect(
    coding_request, classifier_identity, tmp_path
):
    directory = tmp_path / "unused"
    cache = CodingCache(directory, "replay")
    assert cache.get(coding_request, classifier_identity) is None
    assert not directory.exists()


@pytest.mark.parametrize("input_tokens", [True, -1, 5.0, "5", None])
def test_invalid_counters_refuse_before_cache_write(
    coding_request, classifier_identity, tmp_path, input_tokens
):
    with pytest.raises(CodingError, match="^malformed_record$"):
        CodingCache(tmp_path, "live").put(
            coding_request,
            classifier_identity,
            ModelReply(text=PRIVATE),
            input_tokens=input_tokens,
        )
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("reason", [PRIVATE, "policy_accept", "accepted", 1])
def test_nontransport_refusal_reasons_cannot_enter_cache(
    coding_request, classifier_identity, tmp_path, reason
):
    with pytest.raises(CodingError, match="^malformed_record$"):
        CodingCache(tmp_path, "live").put(
            coding_request,
            classifier_identity,
            ModelReply(text=PRIVATE),
            input_tokens=5,
            refusal_reason=reason,
        )
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "mutation",
    [
        "json",
        "deep_json",
        "key",
        "request",
        "identity",
        "reply_hash",
        "reply",
        "refusal",
        "counter",
        "schema_version",
        "counter_type",
        "extra",
    ],
)
def test_corrupt_cache_entries_refuse_lookup_and_artifact_hash(
    coding_request, classifier_identity, tmp_path, mutation
):
    cache = CodingCache(tmp_path, "live")
    ref = cache.put(
        coding_request, classifier_identity, ModelReply(text=PRIVATE), input_tokens=5
    )
    path = tmp_path / ref
    record = json.loads(path.read_bytes())
    if mutation == "json":
        payload = PRIVATE.encode()
    elif mutation == "deep_json":
        payload = b"[" * 10000 + b"0" + b"]" * 10000
    else:
        if mutation == "key":
            record["key"] = "0" * 64
        elif mutation == "request":
            record["request"]["subject"]["doc_id"] = PRIVATE
        elif mutation == "identity":
            record["identity"]["family"] = PRIVATE
        elif mutation == "reply_hash":
            record["reply_hash"] = "0" * 64
        elif mutation == "reply":
            record["reply"]["text"] = "other"
        elif mutation == "refusal":
            record["refusal_reason"] = "model_mismatch"
        elif mutation == "counter":
            record["input_tokens"] = 6
        elif mutation == "schema_version":
            record["schema_version"] = True
        elif mutation == "counter_type":
            record["input_tokens"] = True
        else:
            record[PRIVATE] = PRIVATE
        payload = canonical_json(record)
    path.write_bytes(payload)
    for call in (
        lambda: cache.get(coding_request, classifier_identity),
        lambda: cache.artifact_hash(ref),
    ):
        with pytest.raises(CodingError, match="^cache_corrupt$") as caught:
            call()
        assert PRIVATE not in "".join(traceback.format_exception(caught.value))


def test_renamed_entry_does_not_match_new_binding(
    coding_request, classifier_identity, tmp_path
):
    cache = CodingCache(tmp_path, "live")
    ref = cache.put(
        coding_request, classifier_identity, ModelReply(text=PRIVATE), input_tokens=5
    )
    changed = changed_request(coding_request, "subject", "doc_id", "other-document")
    renamed = coding_key(changed, classifier_identity) + ".json"
    (tmp_path / ref).rename(tmp_path / renamed)
    with pytest.raises(CodingError, match="^cache_corrupt$"):
        cache.get(changed, classifier_identity)
    with pytest.raises(CodingError, match="^cache_corrupt$"):
        cache.artifact_hash(renamed)


@pytest.mark.parametrize("dangling", [False, True])
def test_symlinked_entries_are_refused_even_when_target_is_missing(
    coding_request, classifier_identity, tmp_path, dangling
):
    cache = CodingCache(tmp_path, "live")
    ref = cache.put(
        coding_request, classifier_identity, ModelReply(text=PRIVATE), input_tokens=5
    )
    path = tmp_path / ref
    target = tmp_path / "target"
    path.rename(target)
    if dangling:
        target.unlink()
    path.symlink_to(target)
    for call in (
        lambda: cache.get(coding_request, classifier_identity),
        lambda: cache.artifact_hash(ref),
        lambda: cache.put(
            coding_request,
            classifier_identity,
            ModelReply(text=PRIVATE),
            input_tokens=5,
        ),
    ):
        with pytest.raises(CodingError, match="^cache_corrupt$"):
            call()
    assert path.is_symlink()


@pytest.mark.parametrize(
    "reference",
    [
        "../" + "a" * 64 + ".json",
        "/" + "a" * 64 + ".json",
        "A" * 64 + ".json",
        "a" * 64 + ".json/",
        "a" * 64,
        PRIVATE,
        None,
    ],
)
def test_artifact_references_are_exact_confined_filenames(tmp_path, reference):
    with pytest.raises(CodingError, match="^cache_corrupt$") as caught:
        CodingCache(tmp_path, "live").artifact_hash(reference)
    assert PRIVATE not in "".join(traceback.format_exception(caught.value))


def test_identical_existing_entry_is_reused_without_rewrite(
    coding_request, classifier_identity, tmp_path, monkeypatch
):
    cache = CodingCache(tmp_path, "live")
    reply = ModelReply(text=PRIVATE)
    ref = cache.put(coding_request, classifier_identity, reply, input_tokens=5)
    before = (tmp_path / ref).read_bytes()

    def forbidden(*args, **kwargs):
        raise AssertionError("existing_entry_must_not_rewrite")

    monkeypatch.setattr(cache_module.tempfile, "NamedTemporaryFile", forbidden)
    assert cache.put(coding_request, classifier_identity, reply, input_tokens=5) == ref
    assert (tmp_path / ref).read_bytes() == before


@pytest.mark.parametrize("difference", ["reply", "counter", "refusal"])
def test_conflicting_existing_content_is_immutable(
    coding_request, classifier_identity, tmp_path, difference
):
    cache = CodingCache(tmp_path, "live")
    reply = ModelReply(text=PRIVATE)
    ref = cache.put(coding_request, classifier_identity, reply, input_tokens=5)
    before = (tmp_path / ref).read_bytes()
    with pytest.raises(CodingError, match="^cache_corrupt$"):
        cache.put(
            coding_request,
            classifier_identity,
            reply.model_copy(update={"text": "other"})
            if difference == "reply"
            else reply,
            input_tokens=6 if difference == "counter" else 5,
            refusal_reason="transport_error" if difference == "refusal" else None,
        )
    assert (tmp_path / ref).read_bytes() == before
    assert list(tmp_path.iterdir()) == [tmp_path / ref]


def test_partial_write_failure_cleans_temporary_file(
    coding_request, classifier_identity, tmp_path, monkeypatch
):
    real_temporary = cache_module.tempfile.NamedTemporaryFile

    class FailedWrite:
        def __init__(self, **kwargs):
            self.file = real_temporary(**kwargs)
            self.name = self.file.name

        def __enter__(self):
            return self

        def write(self, payload):
            self.file.write(payload[:10])
            raise OSError(PRIVATE)

        def __exit__(self, *args):
            self.file.close()

    monkeypatch.setattr(cache_module.tempfile, "NamedTemporaryFile", FailedWrite)
    with pytest.raises(CodingError, match="^storage_corrupt$") as caught:
        CodingCache(tmp_path, "live").put(
            coding_request,
            classifier_identity,
            ModelReply(text=PRIVATE),
            input_tokens=5,
        )
    assert list(tmp_path.iterdir()) == []
    assert PRIVATE not in "".join(traceback.format_exception(caught.value))


def test_failed_publication_cleans_temporary_file(
    coding_request, classifier_identity, tmp_path, monkeypatch
):
    def fail(source, destination):
        raise OSError(PRIVATE)

    monkeypatch.setattr(cache_module.os, "link", fail)
    with pytest.raises(CodingError, match="^storage_corrupt$"):
        CodingCache(tmp_path, "live").put(
            coding_request,
            classifier_identity,
            ModelReply(text=PRIVATE),
            input_tokens=5,
        )
    assert list(tmp_path.iterdir()) == []


def test_publication_never_replaces_entry_created_after_lookup(
    coding_request, classifier_identity, tmp_path, monkeypatch
):
    real_link = cache_module.os.link
    other = CodingCacheEntry(
        key=coding_key(coding_request, classifier_identity),
        request=coding_request,
        identity=classifier_identity,
        reply=ModelReply(text="other"),
        input_tokens=5,
        reply_hash=raw_reply_hash(ModelReply(text="other"), None, 5),
    )
    payload = canonical_json(other.model_dump(mode="json"))

    def publish_after_other(source, destination):
        Path(destination).write_bytes(payload)
        real_link(source, destination)

    monkeypatch.setattr(cache_module.os, "link", publish_after_other)
    cache = CodingCache(tmp_path, "live")
    with pytest.raises(CodingError, match="^cache_corrupt$"):
        cache.put(
            coding_request,
            classifier_identity,
            ModelReply(text=PRIVATE),
            input_tokens=5,
        )
    ref = other.key + ".json"
    assert (tmp_path / ref).read_bytes() == payload
    assert list(tmp_path.iterdir()) == [tmp_path / ref]


@pytest.mark.parametrize("boundary", ["key", "get", "put"])
def test_copied_invalid_request_and_identity_are_strict_at_boundaries(
    coding_request, classifier_identity, tmp_path, boundary
):
    malformed = coding_request.model_copy(
        update={
            "parameters": coding_request.parameters.model_copy(
                update={"max_tokens": True}
            )
        }
    )
    forged_identity = classifier_identity.model_copy(update={"input_limit": True})
    cache = CodingCache(tmp_path, "live")
    with warnings.catch_warnings(record=True) as emitted:
        for request, identity in (
            (malformed, classifier_identity),
            (coding_request, forged_identity),
        ):
            with pytest.raises(CodingError, match="^malformed_record$"):
                if boundary == "key":
                    coding_key(request, identity)
                elif boundary == "get":
                    cache.get(request, identity)
                else:
                    cache.put(
                        request, identity, ModelReply(text=PRIVATE), input_tokens=5
                    )
    assert emitted == []
    assert list(tmp_path.iterdir()) == []


def test_cache_key_and_raw_hash_use_complete_versioned_material(
    coding_request, classifier_identity
):
    assert coding_key(coding_request, classifier_identity) == digest(
        {
            "coding_schema": 1,
            "coding_version": "deductive-coding/1",
            "request": coding_request.model_dump(mode="json"),
            "identity": classifier_identity.model_dump(mode="json"),
        }
    )
    reply = ModelReply(text=PRIVATE)
    assert raw_reply_hash(reply, None, 5) == digest(
        {
            "reply": reply.model_dump(mode="json"),
            "refusal_reason": None,
            "input_tokens": 5,
        }
    )
    assert raw_reply_hash(reply, None, 5) != raw_reply_hash(reply, None, 6)


def test_cache_entry_has_strict_safe_contract(coding_request, classifier_identity):
    entry = CodingCacheEntry(
        key=coding_key(coding_request, classifier_identity),
        request=coding_request,
        identity=classifier_identity,
        input_tokens=5,
        reply=ModelReply(text=PRIVATE),
        reply_hash=raw_reply_hash(ModelReply(text=PRIVATE), None, 5),
    )
    assert checked(entry, CodingCacheEntry) == entry
    assert PRIVATE not in str(entry) and PRIVATE not in repr(entry)
    assert entry.model_config == {"frozen": True, "extra": "forbid", "strict": True}
    with pytest.raises(CodingError, match="^malformed_record$"):
        checked(
            entry.model_copy(update={"refusal_reason": "policy_accept"}),
            CodingCacheEntry,
        )


@pytest.mark.parametrize(
    "schema",
    [
        {1: "invented"},
        {"nested": {False: "invented"}},
        {"nested": ("invented",)},
        {"nested": object()},
        {"nested": float("nan")},
    ],
)
def test_nonjson_schema_values_cannot_be_coerced_into_key(
    coding_request, classifier_identity, schema
):
    with pytest.raises(CodingError, match="^malformed_record$"):
        coding_key(
            coding_request.model_copy(update={"reply_schema": schema}),
            classifier_identity,
        )


def test_cyclic_mutable_schema_has_fixed_boundary_diagnostics(
    coding_request, classifier_identity
):
    schema = {}
    schema[PRIVATE] = schema
    with pytest.raises(CodingError, match="^malformed_record$") as caught:
        coding_key(
            coding_request.model_copy(update={"reply_schema": schema}),
            classifier_identity,
        )
    assert PRIVATE not in "".join(traceback.format_exception(caught.value))


@pytest.mark.parametrize("boundary", ["put", "raw_hash"])
@pytest.mark.parametrize("field", ["input_tokens", "refusal_reason"])
@pytest.mark.parametrize(
    "value_kind", ["object", "private_type", "cyclic_list", "cyclic_dict"]
)
def test_raw_accounting_invalid_scalars_are_private_and_publish_nothing(
    coding_request, classifier_identity, tmp_path, boundary, field, value_kind
):
    private_type_name = "INVENTED_PRIVATE_SCALAR_TYPE"
    if value_kind == "object":
        value = object()
    elif value_kind == "private_type":
        value = type(private_type_name, (), {})()
    elif value_kind == "cyclic_list":
        value = []
        value.append(value)
    else:
        value = {}
        value[PRIVATE] = value
    arguments = {"input_tokens": 5, "refusal_reason": None}
    arguments[field] = value
    directory = tmp_path / "unused"
    cache = CodingCache(directory, "live")
    with pytest.raises(CodingError, match="^malformed_record$") as caught:
        if boundary == "put":
            cache.put(
                coding_request,
                classifier_identity,
                ModelReply(text=PRIVATE),
                **arguments,
            )
        else:
            raw_reply_hash(ModelReply(text=PRIVATE), **arguments)
    diagnostic = "".join(traceback.format_exception(caught.value))
    assert PRIVATE not in diagnostic and private_type_name not in diagnostic
    assert caught.value.__context__ is None or caught.value.__suppress_context__
    assert not directory.exists()
    assert list(tmp_path.iterdir()) == []
