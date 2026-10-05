"""Raw offline cache, normative binding changes, integrity and safe errors."""

import json
from dataclasses import replace

import pytest
from earnings_core import digest
from earnings_themes.extraction.adapters import Message, ModelReply
from earnings_themes.support.cache import SupportCache, judge_key, scorer_key
from earnings_themes.support.problems import SupportError
from earnings_themes.support.prompt import render_judge
from earnings_themes.support.scorers import ScriptedScorer, score_requests

from .test_judges import identity as identity  # noqa: PLC0414
from .test_prompt import policy as policy  # noqa: PLC0414
from .test_scorers import reply


def test_raw_replay_miss_hit_and_no_dispatch(
    tmp_path, one_quote, scorer_identity, policy
):
    cache = SupportCache(tmp_path, "replay")
    request = score_requests(one_quote)[0][1]
    scorer = ScriptedScorer(
        lambda r: reply(r, scorer_identity), lambda r: 4, scorer_identity
    )
    key = scorer_key(one_quote, request, scorer.identity, policy)
    assert cache.lookup(key, "scorer") is None
    assert scorer.requests == []
    raw = reply(request, scorer_identity)
    ref = cache.put(key, raw)
    assert cache.lookup(key, "scorer") == raw
    assert ref == cache.raw_ref(key)
    assert scorer.requests == []
    assert len(str(key)) == 64 and "Orion" not in repr(key)


@pytest.mark.parametrize("kind", ["scorer", "judge"])
def test_corruption_and_incompatible_existing_refused(
    tmp_path, one_quote, scorer_identity, identity, policy, kind
):
    request = (
        score_requests(one_quote)[0][1]
        if kind == "scorer"
        else render_judge(one_quote, policy, "evidence_first")
    )
    key = (
        scorer_key(one_quote, request, scorer_identity, policy)
        if kind == "scorer"
        else judge_key(one_quote, request, identity, policy)
    )
    raw = (
        reply(request, scorer_identity)
        if kind == "scorer"
        else ModelReply(text="INVENTED_SECRET_REPLY", model=identity.runtime.model_id)
    )
    cache = SupportCache(tmp_path, "live")
    cache.put(key, raw)
    assert cache.lookup(key, kind) == raw
    path = tmp_path / cache.raw_ref(key)
    body = json.loads(path.read_text())
    body["reply_hash"] = digest("SECRET_KEY")
    path.write_text(json.dumps(body))
    with pytest.raises(SupportError, match="^cache_corrupt$"):
        cache.lookup(key, kind)
    with pytest.raises(SupportError, match="^cache_corrupt$"):
        cache.put(key, raw)


@pytest.mark.parametrize(
    "field", ["doc_id", "claim_hash", "input_hash", "source_run_hash", "target_id"]
)
def test_target_binding_changes_key(one_quote, scorer_identity, policy, field):
    request = score_requests(one_quote)[0][1]
    base = scorer_key(one_quote, request, scorer_identity, policy)
    record = one_quote.record
    if field == "doc_id":
        record = record.model_copy(
            update={"target": record.target.model_copy(update={field: "different"})}
        )
    else:
        record = record.model_copy(update={field: digest("different")})
    assert (
        scorer_key(replace(one_quote, record=record), request, scorer_identity, policy)
        != base
    )


@pytest.mark.parametrize(
    "field",
    [
        "model_id",
        "revision",
        "files",
        "runtime",
        "runtime_version",
        "device",
        "precision",
        "encoding_version",
    ],
)
def test_runtime_material_changes_key(one_quote, scorer_identity, policy, field):
    from earnings_themes.support.records import FileHash

    runtime = scorer_identity.runtime
    value = (
        (FileHash(relative_path="weights", sha256=digest("weights")),)
        if field == "files"
        else "changed"
    )
    changed = scorer_identity.model_copy(
        update={"runtime": runtime.model_copy(update={field: value})}
    )
    request = score_requests(one_quote)[0][1]
    assert scorer_key(one_quote, request, changed, policy) != scorer_key(
        one_quote, request, scorer_identity, policy
    )


@pytest.mark.parametrize(
    "changed",
    [
        "claim",
        "evidence",
        "contexts",
        "provenance",
        "theme",
        "limits",
        "prompt",
        "parameters",
    ],
)
def test_normative_material_changes_key(one_quote, scorer_identity, policy, changed):
    request = score_requests(one_quote)[0][1]
    baseline = scorer_key(one_quote, request, scorer_identity, policy)
    value, ident, pol = one_quote, scorer_identity, policy
    if changed == "claim":
        value = replace(value, claim="Different invented claim")
    elif changed == "evidence":
        value = replace(
            value,
            evidence=(
                value.evidence[0].model_copy(
                    update={"start": 1, "mask_ids": ("mask",)}
                ),
            ),
        )
    elif changed == "contexts":
        value = replace(value, contexts=())
    elif changed == "provenance":
        value = replace(
            value, sources=replace(value.sources, provenance_hash=digest("changed"))
        )
    elif changed == "theme":
        value = replace(
            value,
            record=value.record.model_copy(
                update={
                    "theme": value.record.theme.model_copy(
                        update={"definition": "Changed invented definition"}
                    )
                }
            ),
        )
    elif changed == "limits":
        ident = ident.model_copy(update={"input_limit": 1001})
    elif changed == "prompt":
        pol = pol.model_copy(update={"prompt_text": "Changed invented prompt"})
    elif changed == "parameters":
        pol = pol.model_copy(
            update={"parameters": pol.parameters.model_copy(update={"seed": 20})}
        )
    assert scorer_key(value, request, ident, pol) != baseline


@pytest.mark.parametrize(
    "changed",
    ["messages", "schema", "presentation", "family", "output_limit", "input_limit"],
)
def test_judge_invocation_changes_key(one_quote, identity, policy, changed):
    request = render_judge(one_quote, policy, "evidence_first")
    base = judge_key(one_quote, request, identity, policy)
    ident = identity
    if changed == "messages":
        request = request.model_copy(
            update={
                "messages": request.messages
                + (Message(role="user", content="Invented retry feedback"),)
            }
        )
    elif changed == "schema":
        request = request.model_copy(
            update={"reply_schema": {"INVENTED_SECRET_KEY": "changed"}}
        )
    elif changed == "presentation":
        request = render_judge(one_quote, policy, "claim_theme_first")
    elif changed == "family":
        ident = ident.model_copy(update={"family": "different"})
    elif changed == "output_limit":
        ident = ident.model_copy(update={"output_limit": 2000})
    else:
        ident = ident.model_copy(update={"input_limit": 11000})
    assert judge_key(one_quote, request, ident, policy) != base


def test_forged_bindings_wrong_reply_and_plain_digest_refused(
    tmp_path, one_quote, scorer_identity, policy
):
    cache = SupportCache(tmp_path, "replay")
    request = score_requests(one_quote)[0][1]
    key = scorer_key(one_quote, request, scorer_identity, policy)
    with pytest.raises(SupportError, match="malformed_record"):
        cache.lookup(str(key), "scorer")
    with pytest.raises((AttributeError, TypeError)):
        key.material = "SECRET"
    with pytest.raises(SupportError, match="input_changed"):
        cache.put(
            key,
            reply(request, scorer_identity).model_copy(
                update={"input_hash": digest("wrong")}
            ),
        )
    with pytest.raises(SupportError, match="malformed_record"):
        cache.lookup("SECRET_SENTINEL", "SECRET_MAP_KEY")
    assert "SECRET" not in repr(cache)


def test_binding_dictionary_cannot_mutate_and_forged_key_refused(
    tmp_path, one_quote, scorer_identity, policy
):
    from earnings_themes.support.cache import SupportCacheKey

    key = scorer_key(
        one_quote, score_requests(one_quote)[0][1], scorer_identity, policy
    )
    with pytest.raises(TypeError):
        key.__dict__["_material"] = "SECRET_SENTINEL"
    forged = SupportCacheKey('{"kind":"scorer"}')
    with pytest.raises(SupportError, match="malformed_record"):
        SupportCache(tmp_path, "replay").lookup(forged, "scorer")


@pytest.mark.parametrize(
    "field,value",
    [
        ("quote_id", "changed"),
        ("canonical_hash", digest("changed")),
        ("element_id", "changed"),
        ("start", 1),
        ("end", 3),
        ("text_hash", digest("changed")),
        ("validator_version", "changed"),
        ("mask_ids", ("changed",)),
    ],
)
def test_every_evidence_field_changes_digest(
    one_quote, scorer_identity, policy, field, value
):
    request = score_requests(one_quote)[0][1]
    if field == "end":
        value = one_quote.evidence[0].end + 1
    changed = replace(
        one_quote, evidence=(one_quote.evidence[0].model_copy(update={field: value}),)
    )
    assert scorer_key(changed, request, scorer_identity, policy) != scorer_key(
        one_quote, request, scorer_identity, policy
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("theme_id", "changed"),
        ("label", "Changed"),
        ("definition", "Changed definition"),
        ("parent_id", "changed"),
        ("inclusion_rules", ("Changed rule",)),
        ("exclusion_rules", ("Changed rule",)),
    ],
)
def test_every_theme_field_changes_digest(
    one_quote, scorer_identity, policy, field, value
):
    request = score_requests(one_quote)[0][1]
    changed = replace(
        one_quote,
        record=one_quote.record.model_copy(
            update={"theme": one_quote.record.theme.model_copy(update={field: value})}
        ),
    )
    assert scorer_key(changed, request, scorer_identity, policy) != scorer_key(
        one_quote, request, scorer_identity, policy
    )


def test_wrong_model_raw_is_cached_under_expected_binding(
    tmp_path, one_quote, identity, policy
):
    request = render_judge(one_quote, policy, "evidence_first")
    key = judge_key(one_quote, request, identity, policy)
    cache = SupportCache(tmp_path, "live")
    raw = ModelReply(text="INVENTED_SECRET_REPLY", model="wrong")
    cache.put(key, raw)
    assert SupportCache(tmp_path, "replay").lookup(key, "judge") == raw
    from earnings_themes.support.judges import parse_answer

    with pytest.raises(SupportError, match="model_mismatch"):
        parse_answer(raw, one_quote, identity)


@pytest.mark.parametrize("field", ["record", "policy", "source_run"])
def test_unknown_binding_keys_refused_safely(
    tmp_path, one_quote, scorer_identity, policy, field
):
    from earnings_core import canonical_json
    from earnings_themes.support.cache import SupportCacheKey

    key = scorer_key(
        one_quote, score_requests(one_quote)[0][1], scorer_identity, policy
    )
    material = json.loads(key.material)
    material[field]["SECRET_SENTINEL_KEY"] = "SECRET_SENTINEL_VALUE"
    forged = SupportCacheKey(canonical_json(material).decode())
    with pytest.raises(SupportError, match="^malformed_record$") as caught:
        SupportCache(tmp_path, "replay").lookup(forged, "scorer")
    assert "SECRET" not in str(caught.value)


@pytest.mark.parametrize(
    "field,value",
    [
        ("codebook_id", "changed"),
        ("codebook_version", 2),
        ("content_hash", digest("changed")),
    ],
)
def test_codebook_binding_changes_digest(
    one_quote, scorer_identity, policy, field, value
):
    request = score_requests(one_quote)[0][1]
    theme = one_quote.record.theme
    changed = replace(
        one_quote,
        record=one_quote.record.model_copy(
            update={
                "theme": theme.model_copy(
                    update={
                        "codebook": theme.codebook.model_copy(update={field: value})
                    }
                )
            }
        ),
    )
    assert scorer_key(changed, request, scorer_identity, policy) != scorer_key(
        one_quote, request, scorer_identity, policy
    )


@pytest.mark.parametrize(
    "field", ["start", "end", "element_id", "text_hash", "canonical_hash", "kind"]
)
def test_context_bounds_and_locator_material_change_key(
    one_quote, scorer_identity, policy, field
):
    request = score_requests(one_quote)[0][1]
    context = one_quote.contexts[0]
    value = (
        (context.start + 1 if field == "start" else context.end + 1)
        if field in ("start", "end")
        else (
            ("block" if context.kind == "heading" else "heading")
            if field == "kind"
            else digest("changed")
        )
    )
    changed = replace(
        one_quote,
        contexts=(context.model_copy(update={field: value}), *one_quote.contexts[1:]),
    )
    assert scorer_key(changed, request, scorer_identity, policy) != scorer_key(
        one_quote, request, scorer_identity, policy
    )


@pytest.mark.parametrize(
    "field,value",
    [("temperature", 0.5), ("seed", 3), ("max_tokens", 32), ("structured", False)],
)
def test_all_judge_model_settings_change_key(one_quote, identity, policy, field, value):
    request = render_judge(one_quote, policy, "evidence_first")
    changed = request.model_copy(
        update={"parameters": request.parameters.model_copy(update={field: value})}
    )
    assert judge_key(one_quote, changed, identity, policy) != judge_key(
        one_quote, request, identity, policy
    )


def test_material_digest_and_low_level_tamper_refused(
    tmp_path, one_quote, scorer_identity, policy
):
    key = scorer_key(
        one_quote, score_requests(one_quote)[0][1], scorer_identity, policy
    )
    assert str(key) == digest(json.loads(key.material))
    object.__getattribute__(key, "__dict__")["_material"] = '{"SECRET":"SECRET"}'
    with pytest.raises(SupportError, match="^malformed_record$"):
        SupportCache(tmp_path, "replay").lookup(key, "scorer")


@pytest.mark.parametrize("field", ["prefix", "suffix", "quote_text"])
def test_original_quote_locator_changes_key(one_quote, scorer_identity, policy, field):
    request = score_requests(one_quote)[0][1]
    source = one_quote.sources
    quote = source.stored_run.quotes[0]
    changed_quote = quote.model_copy(
        update={
            "span": quote.span.model_copy(update={field: "Changed invented locator"})
        }
    )
    changed = replace(
        one_quote,
        sources=replace(
            source, stored_run=replace(source.stored_run, quotes=(changed_quote,))
        ),
    )
    assert scorer_key(changed, request, scorer_identity, policy) != scorer_key(
        one_quote, request, scorer_identity, policy
    )


@pytest.mark.parametrize("field", ["doc_id", "canonical_hash", "canonical_text"])
def test_full_source_document_changes_key(one_quote, scorer_identity, policy, field):
    request = score_requests(one_quote)[0][1]
    source = one_quote.sources
    bundle = source.bundles[0]
    from earnings_core import CanonicalDocument

    document = CanonicalDocument.create(
        source_document_id=(
            "changed-source"
            if field == "doc_id"
            else bundle.document.source_document_id
        ),
        canonicalization_version=bundle.document.canonicalization_version,
        canonical_text=(
            bundle.document.canonical_text
            if field == "doc_id"
            else "Changed invented document"
        ),
    )
    changed_bundle = replace(bundle, document=document)
    changed = replace(one_quote, sources=replace(source, bundles=(changed_bundle,)))
    assert scorer_key(changed, request, scorer_identity, policy) != scorer_key(
        one_quote, request, scorer_identity, policy
    )


def test_structure_bounds_change_key(one_quote, scorer_identity, policy):
    request = score_requests(one_quote)[0][1]
    source = one_quote.sources
    bundle = source.bundles[0]
    element = bundle.elements[0]
    changed_bundle = replace(
        bundle,
        elements=(
            element.model_copy(
                update={
                    "span": element.span.model_copy(
                        update={"end": element.span.end - 1}
                    ),
                    "element_id": f"{element.type.value}-{element.span.start}-{element.span.end - 1}",
                }
            ),
            *bundle.elements[1:],
        ),
    )
    changed = replace(one_quote, sources=replace(source, bundles=(changed_bundle,)))
    assert scorer_key(changed, request, scorer_identity, policy) != scorer_key(
        one_quote, request, scorer_identity, policy
    )


@pytest.mark.parametrize(
    "field,value", [("schema_version", 2), ("support_version", "semantic-support/2")]
)
def test_incompatible_policy_versions_refused(
    tmp_path, one_quote, scorer_identity, policy, field, value
):
    from earnings_core import canonical_json
    from earnings_themes.support.cache import SupportCacheKey

    key = scorer_key(
        one_quote, score_requests(one_quote)[0][1], scorer_identity, policy
    )
    material = json.loads(key.material)
    material[field] = value
    with pytest.raises(SupportError, match="malformed_record"):
        SupportCache(tmp_path, "replay").lookup(
            SupportCacheKey(canonical_json(material).decode()), "scorer"
        )


@pytest.mark.parametrize("publication_fails", [True, False])
def test_cleanup_failure_keeps_fixed_storage_error(
    tmp_path, one_quote, scorer_identity, policy, monkeypatch, publication_fails
):
    from pathlib import Path

    from earnings_themes.support import cache as cache_module

    request = score_requests(one_quote)[0][1]
    key = scorer_key(one_quote, request, scorer_identity, policy)
    original_replace = cache_module.os.replace
    events = []

    def publish(source, destination):
        events.append("publication")
        if publication_fails:
            raise OSError("SECRET_PUBLICATION_PATH")
        original_replace(source, destination)

    def cleanup(path, *, missing_ok=False):
        events.append("cleanup")
        raise OSError("SECRET_CLEANUP_PATH")

    monkeypatch.setattr(cache_module.os, "replace", publish)
    monkeypatch.setattr(Path, "unlink", cleanup)
    caught = None
    try:
        SupportCache(tmp_path, "live").put(key, reply(request, scorer_identity))
    except Exception as error:  # noqa: BLE001 - inspect type before printable text
        caught = error
    assert events == ["publication", "cleanup"]
    assert type(caught).__name__ == "SupportError"
    assert str(caught) == "storage_corrupt"
    assert caught.__suppress_context__


def test_refusal_metadata_closed_integrity_and_immutable(
    tmp_path, one_quote, identity, policy
):
    request = render_judge(one_quote, policy, "evidence_first")
    key = judge_key(one_quote, request, identity, policy)
    cache = SupportCache(tmp_path, "live")
    raw = ModelReply(text="INVENTED_REPLY", model=identity.runtime.model_id)
    cache.put(key, raw, refusal_reason="transport_error")
    assert cache.lookup(key, "judge") == raw
    assert cache.refusal_reason(key) == "transport_error"
    with pytest.raises(SupportError, match="cache_corrupt"):
        cache.put(key, raw)
    body = json.loads((tmp_path / cache.raw_ref(key)).read_text())
    body["refusal_reason"] = "model_mismatch"
    (tmp_path / cache.raw_ref(key)).write_text(json.dumps(body))
    with pytest.raises(SupportError, match="cache_corrupt"):
        cache.refusal_reason(key)


@pytest.mark.parametrize(
    "reason", ["SECRET_REASON", "wrong_attribution", "input_too_long"]
)
def test_refusal_metadata_refuses_arbitrary_and_semantic_reasons(
    tmp_path, one_quote, identity, policy, reason
):
    request = render_judge(one_quote, policy, "evidence_first")
    key = judge_key(one_quote, request, identity, policy)
    cache = SupportCache(tmp_path, "live")
    with pytest.raises(SupportError, match="malformed_record"):
        cache.put(
            key,
            ModelReply(text="INVENTED_REPLY", model=identity.runtime.model_id),
            refusal_reason=reason,
        )


def test_artifact_hash_is_confined_and_checks_entry(tmp_path):
    from earnings_themes.support.problems import SupportError

    cache = SupportCache(tmp_path, "live")
    reference = "a" * 64 + ".json"
    with pytest.raises(SupportError):
        cache.artifact_hash("../" + reference)
    with pytest.raises(SupportError):
        cache.artifact_hash(reference)
    (tmp_path / reference).write_text("INVENTED_PRIVATE")
    with pytest.raises(SupportError, match="^cache_corrupt$"):
        cache.artifact_hash(reference)
