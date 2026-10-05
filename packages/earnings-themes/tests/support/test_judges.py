"""Closed offline judge trials and explicit lineage/preflight checks."""

import json
from datetime import date

import pytest
from earnings_themes.extraction.adapters import AdapterError, ModelReply, Usage
from earnings_themes.extraction.records import AdapterIdentity, ExtractionProblem
from earnings_themes.support import judges
from earnings_themes.support.problems import SupportError
from earnings_themes.support.prompt import render_judge
from earnings_themes.support.records import (
    JudgeIdentity,
    RuntimeIdentity,
    WeightLicense,
)

from .cases import resolved_case
from .test_prompt import (
    policy as policy,  # noqa: PLC0414 - explicit pytest fixture re-export
)


@pytest.fixture
def identity():
    return JudgeIdentity(
        family="invented-family-a",
        input_limit=10000,
        output_limit=2048,
        hosting="scripted",
        weight_license=None,
        runtime=RuntimeIdentity(
            model_id="alias",
            revision="1",
            files=(),
            runtime="scripted",
            runtime_version="1",
            device="cpu",
            precision="float32",
            encoding_version="1",
        ),
    )


def answer(resolved):
    return {
        "claim_support": "unsupported",
        "theme_fit": "uncertain",
        "joint_support_score": 0.1,
        "quote_assessments": [
            {"quote_id": r.quote_id, "contribution": "uncertain"}
            for r in resolved.evidence
        ],
        "reason_codes": ["insufficient_evidence"],
        "summary": "Invented uncertainty.",
    }


def test_valid_negative_and_uncertain_are_final_signals(case, identity):
    resolved = resolved_case(*case)
    reply = ModelReply(text=json.dumps(answer(resolved)), model="alias")
    result = judges.parse_answer(reply, resolved, identity)
    assert result.claim_support == "unsupported"
    assert result.theme_fit == "uncertain"
    assert "Invented uncertainty" not in repr(result)


@pytest.mark.parametrize(
    "bad",
    [
        "missing",
        "duplicate",
        "unknown",
        "keys",
        "edited",
        "accepted",
        "tools",
        "model",
        "json",
        "summary",
        "nested",
    ],
)
def test_unusable_replies(case, identity, bad):
    resolved = resolved_case(*case)
    body = answer(resolved)
    kw = {"model": "alias"}
    if bad == "missing":
        body["quote_assessments"].pop()
    elif bad == "duplicate":
        body["quote_assessments"].append(body["quote_assessments"][0])
    elif bad == "unknown":
        body["quote_assessments"][0]["quote_id"] = "unknown"
    elif bad == "keys":
        body["unknown-secret-key"] = "SECRET"
    elif bad == "edited":
        body["quote_text"] = "Changed evidence."
    elif bad == "accepted":
        body["accepted"] = True
    elif bad == "tools":
        kw["tool_calls"] = True
    elif bad == "model":
        kw["model"] = "wrong"
    elif bad == "summary":
        body["summary"] = " " * 501
    elif bad == "nested":
        body["quote_assessments"][0]["text"] = "Changed evidence."
    reply = ModelReply(text="SECRET" if bad == "json" else json.dumps(body), **kw)
    with pytest.raises(SupportError) as err:
        judges.parse_answer(reply, resolved, identity)
    assert "SECRET" not in str(err.value)
    assert err.value.__suppress_context__ or err.value.__context__ is None


@pytest.mark.parametrize(
    "extractor,families",
    [
        ("x", ()),
        ("", ("a", "b")),
        ("x", ("a", "a")),
        ("a", ("a", "a")),
        ("x", ("", "b")),
    ],
)
def test_invalid_panel_precedes_dispatch(identity, extractor, families):
    panel = tuple(identity.model_copy(update={"family": f}) for f in families)
    with pytest.raises(SupportError, match="invalid_panel"):
        judges.validate_panel(extractor, panel)


def test_alias_is_never_lineage(identity):
    second = identity.model_copy(update={"family": "invented-family-b"})
    assert judges.validate_panel("alias", (identity, second)) == (identity, second)


def test_scripted_counter_is_explicit(case, policy, identity):
    request = render_judge(resolved_case(*case), policy, "evidence_first")
    judge = judges.ScriptedJudge(
        lambda r: ModelReply(text="{}", model="alias"), lambda r: 7, identity
    )
    assert judge.count_tokens(request) == 7
    assert judge.requests == []
    judge.complete(request)
    assert judge.requests == [request]
    assert judge.script is not None
    assert "Orion" not in repr(judge)


class Transport:
    def __init__(self, identity):
        self.identity = identity
        self.requests = []

    def complete(self, request):
        self.requests.append(request)
        return ModelReply(text="{}", model="alias")


@pytest.fixture
def local_identity(identity):
    return identity.model_copy(
        update={
            "hosting": "local",
            "weight_license": WeightLicense(
                source_url="https://example.invalid/weights",
                terms_reference="invented terms",
                intended_use="tests",
                verified_on=date(2026, 10, 5),
                permits_use=True,
            ),
            "runtime": identity.runtime.model_copy(
                update={
                    "files": ({"relative_path": "weights.bin", "sha256": "a" * 64},)
                }
            ),
        }
    )


def transport_identity():
    return AdapterIdentity(
        adapter_kind="local",
        model_id="alias",
        weights_sha256="a" * 64,
        runtime="scripted",
        runtime_version="1",
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("model_id", "other"),
        ("weights_sha256", "b" * 64),
        ("runtime", "other"),
        ("runtime_version", "2"),
        ("adapter_kind", "hosted"),
    ],
)
def test_binding_refuses_identity_mismatch(local_identity, field, value):
    transport = Transport(transport_identity().model_copy(update={field: value}))
    with pytest.raises(SupportError, match="model_mismatch"):
        judges.JudgeBinding(local_identity, transport, lambda r: 1)
    assert transport.requests == []


@pytest.mark.parametrize(
    "count,max_tokens,reason",
    [
        (10001, 100, "input_too_long"),
        (9901, 100, "input_too_long"),
        (100, 2049, "input_too_long"),
        (True, 100, "malformed_reply"),
        (-1, 100, "malformed_reply"),
    ],
)
def test_binding_complete_count_and_reservation(
    case, policy, local_identity, count, max_tokens, reason
):
    transport = Transport(transport_identity())
    binding = judges.JudgeBinding(local_identity, transport, lambda r: count)
    request = render_judge(
        resolved_case(*case),
        policy.model_copy(
            update={
                "parameters": policy.parameters.model_copy(
                    update={"max_tokens": max_tokens}
                )
            }
        ),
        "evidence_first",
    )
    with pytest.raises(SupportError, match=reason):
        binding.complete(request)
    assert transport.requests == []


def test_binding_transport_error_retains_usage_and_redacts(
    case, policy, local_identity
):
    class Failing(Transport):
        def complete(self, request):
            raise AdapterError(
                ExtractionProblem.TOOL_CALL_REFUSED,
                ModelReply(
                    text="SECRET",
                    model="alias",
                    usage=Usage(prompt_tokens=7, completion_tokens=3),
                ),
            ) from ValueError("SECRET")

    binding = judges.JudgeBinding(
        local_identity, Failing(transport_identity()), lambda r: 1
    )
    with pytest.raises(SupportError, match="tool_call_refused") as err:
        binding.complete(render_judge(resolved_case(*case), policy, "evidence_first"))
    assert err.value.reply.usage.prompt_tokens == 7
    assert "SECRET" not in repr(err.value)
    assert err.value.__suppress_context__


def test_binding_boundary_fits_without_clipping(case, policy, local_identity):
    transport = Transport(transport_identity())
    binding = judges.JudgeBinding(local_identity, transport, lambda r: 7952)
    request = render_judge(resolved_case(*case), policy, "evidence_first")
    binding.complete(request)
    assert transport.requests == [request]
    transport.identity = transport.identity.model_copy(update={"model_id": "changed"})
    with pytest.raises(SupportError, match="model_mismatch"):
        binding.complete(request)
    assert transport.requests == [request]


def test_multiple_file_hash_is_sorted_and_bound(local_identity):
    from earnings_core import digest

    files = [
        {"relative_path": "b.bin", "sha256": "b" * 64},
        {"relative_path": "a.bin", "sha256": "a" * 64},
    ]
    identity = local_identity.model_copy(
        update={
            "runtime": local_identity.runtime.model_copy(update={"files": tuple(files)})
        }
    )
    expected = digest(sorted(files, key=lambda f: f["relative_path"]))
    transport = Transport(
        transport_identity().model_copy(update={"weights_sha256": expected})
    )
    binding = judges.JudgeBinding(identity, transport, lambda r: 1)
    assert judges.transport_weights_hash(binding.identity) == expected
    empty = local_identity.model_copy(
        update={"runtime": local_identity.runtime.model_copy(update={"files": ()})}
    )
    with pytest.raises(SupportError, match="model_mismatch"):
        judges.JudgeBinding(empty, transport, lambda r: 1)


def test_request_and_schema_are_closed_and_safe(case, policy):
    request = render_judge(resolved_case(*case), policy, "evidence_first")
    assert "Orion" not in str(request)
    assert "Orion" not in repr(request)
    assert request.reply_schema["additionalProperties"] is False
    assert (
        request.reply_schema["$defs"]["QuoteAssessment"]["additionalProperties"]
        is False
    )
    for value in ("accepted", "quote_text", "offsets", "theme_definition"):
        assert value not in request.reply_schema["properties"]
    bad = request.model_copy(
        update={"subject": request.subject.model_copy(update={"window_id": "secret"})}
    )
    with pytest.raises(SupportError):
        judges._validated(bad, judges.JudgeRequest)
