"""Caller-supplied scripted/local classifiers use invented requests only."""

import json
import traceback
from datetime import date

import httpx
import pytest
from earnings_themes.coding.adapters import CodingTransportError, ScriptedClassifier
from earnings_themes.coding.local import ClassifierBinding
from earnings_themes.coding.records import CodingError
from earnings_themes.extraction.adapters import AdapterError, ModelReply, Usage
from earnings_themes.extraction.local import LocalAdapter, LocalModelConfig
from earnings_themes.extraction.records import AdapterIdentity, ExtractionProblem
from earnings_themes.support.records import FileHash, WeightLicense

PRIVATE = "INVENTED_PRIVATE_TRANSPORT_SENTINEL"


class RecordingTransport:
    def __init__(self, identity, script):
        self.identity = identity
        self.script = script
        self.requests = []

    def complete(self, request):
        self.requests.append(request)
        return self.script(request)


def scripted_transport(identity, script=None):
    return RecordingTransport(
        AdapterIdentity(adapter_kind="scripted", model_id=identity.runtime.model_id),
        script
        or (lambda request: ModelReply(model=identity.runtime.model_id, text="{}")),
    )


def local_identity(identity):
    runtime = identity.runtime.model_copy(
        update={
            "files": (FileHash(relative_path="invented.gguf", sha256="a" * 64),),
            "runtime": "invented-runtime",
        }
    )
    return identity.model_copy(
        update={
            "hosting": "local",
            "runtime": runtime,
            "weight_license": WeightLicense(
                source_url="https://example.invalid/invented-weights",
                terms_reference="invented-permissive-terms",
                intended_use="invented-test",
                verified_on=date(2026, 10, 5),
                permits_use=True,
            ),
        }
    )


def local_transport(identity):
    return RecordingTransport(
        AdapterIdentity(
            adapter_kind="local",
            model_id=identity.runtime.model_id,
            weights_sha256="a" * 64,
            runtime=identity.runtime.runtime,
            runtime_version=identity.runtime.runtime_version,
        ),
        lambda request: ModelReply(model=identity.runtime.model_id, text="{}"),
    )


def test_scripted_classifier_counts_and_retains_requests(
    coding_request, classifier_identity
):
    counted = []
    classifier = ScriptedClassifier(
        lambda request: ModelReply(
            model=classifier_identity.runtime.model_id, text=PRIVATE
        ),
        lambda request: counted.append(request) or 5,
        classifier_identity,
    )
    assert classifier.identity == classifier_identity
    assert classifier.count_tokens(coding_request) == 5
    assert classifier.complete(coding_request).text == PRIVATE
    assert counted == [coding_request, coding_request]
    assert classifier.requests == [coding_request]
    assert str(classifier) == repr(classifier) == "ScriptedClassifier(requests=1)"
    assert PRIVATE not in repr(classifier)


@pytest.mark.parametrize("kind", ["scripted", "binding"])
@pytest.mark.parametrize("tokens", [True, -1, 5.0, "5", None])
def test_counter_values_are_strict_and_dispatch_is_zero(
    coding_request, classifier_identity, kind, tokens
):
    dispatched = []
    script = lambda request: dispatched.append(request) or ModelReply(text="{}")
    classifier = (
        ScriptedClassifier(script, lambda request: tokens, classifier_identity)
        if kind == "scripted"
        else ClassifierBinding(
            classifier_identity,
            scripted_transport(classifier_identity, script),
            lambda request: tokens,
        )
    )
    with pytest.raises(CodingError, match="^malformed_record$"):
        classifier.complete(coding_request)
    assert dispatched == []


@pytest.mark.parametrize("kind", ["scripted", "binding"])
@pytest.mark.parametrize("limit", ["input", "output"])
def test_context_and_output_limits_refuse_before_dispatch(
    coding_request, classifier_identity, kind, limit
):
    identity = classifier_identity.model_copy(
        update={"input_limit": 68} if limit == "input" else {"output_limit": 63}
    )
    dispatched = []
    script = lambda request: dispatched.append(request) or ModelReply(text="{}")
    classifier = (
        ScriptedClassifier(script, lambda request: 5, identity)
        if kind == "scripted"
        else ClassifierBinding(
            identity, scripted_transport(identity, script), lambda request: 5
        )
    )
    with pytest.raises(CodingError, match="^input_too_long$"):
        classifier.complete(coding_request)
    assert dispatched == []


def test_exact_context_and_output_limits_are_permitted(
    coding_request, classifier_identity
):
    identity = classifier_identity.model_copy(
        update={"input_limit": 69, "output_limit": 64}
    )
    transport = scripted_transport(identity)
    classifier = ClassifierBinding(identity, transport, lambda request: 5)
    assert classifier.complete(coding_request).text == "{}"
    assert len(transport.requests) == 1
    assert str(classifier) == repr(classifier) == "ClassifierBinding()"


@pytest.mark.parametrize(
    "field,value",
    [
        ("adapter_kind", "scripted"),
        ("model_id", "other"),
        ("weights_sha256", "b" * 64),
        ("runtime", "other"),
        ("runtime_version", "other"),
    ],
)
def test_local_transport_mismatches_refuse_without_dispatch(
    classifier_identity, field, value
):
    identity = local_identity(classifier_identity)
    transport = local_transport(identity)
    transport.identity = transport.identity.model_copy(update={field: value})
    with pytest.raises(CodingError, match="^model_mismatch$"):
        ClassifierBinding(identity, transport, lambda request: 5)
    assert transport.requests == []


def test_local_identity_requires_license_and_weight_files(classifier_identity):
    identity = local_identity(classifier_identity)
    for invalid in (
        identity.model_copy(update={"weight_license": None}),
        identity.model_copy(
            update={"runtime": identity.runtime.model_copy(update={"files": ()})}
        ),
        identity.model_copy(
            update={
                "weight_license": identity.weight_license.model_copy(
                    update={"permits_use": False}
                )
            }
        ),
    ):
        with pytest.raises(CodingError):
            ClassifierBinding(invalid, local_transport(identity), lambda request: 5)


def test_scripted_classifier_refuses_local_identity(classifier_identity):
    with pytest.raises(CodingError, match="^model_mismatch$"):
        ScriptedClassifier(
            lambda request: ModelReply(text="{}"),
            lambda request: 5,
            local_identity(classifier_identity),
        )


@pytest.mark.parametrize("mutation", ["schema", "parameter", "subject", "message"])
@pytest.mark.parametrize("stage", ["counter", "transport"])
@pytest.mark.parametrize("kind", ["scripted", "binding"])
def test_callback_request_mutations_cannot_publish_reply(
    coding_request, classifier_identity, mutation, stage, kind
):
    dispatched = []

    def mutate(request):
        if mutation == "schema":
            request.reply_schema[PRIVATE] = True
        elif mutation == "parameter":
            object.__setattr__(request.parameters, "max_tokens", 1)
        elif mutation == "subject":
            object.__setattr__(request.subject, "input_hash", "0" * 64)
        else:
            object.__setattr__(request.messages[0], "content", PRIVATE)

    def counter(request):
        if stage == "counter":
            mutate(request)
        return 5

    def script(request):
        dispatched.append(request)
        if stage == "transport":
            mutate(request)
        return ModelReply(text=PRIVATE, model=classifier_identity.runtime.model_id)

    classifier = (
        ScriptedClassifier(script, counter, classifier_identity)
        if kind == "scripted"
        else ClassifierBinding(
            classifier_identity,
            scripted_transport(classifier_identity, script),
            counter,
        )
    )
    before = coding_request.model_dump(mode="json")
    with pytest.raises(CodingError, match="^input_changed$"):
        classifier.complete(coding_request)
    assert coding_request.model_dump(mode="json") == before
    assert len(dispatched) == (0 if stage == "counter" else 1)


@pytest.mark.parametrize("stage", ["counter", "transport"])
def test_callback_external_request_mutation_is_detected(
    coding_request, classifier_identity, stage
):
    transport = scripted_transport(classifier_identity)

    def counter(request):
        if stage == "counter":
            coding_request.reply_schema[PRIVATE] = True
        return 5

    def script(request):
        if stage == "transport":
            coding_request.reply_schema[PRIVATE] = True
        return ModelReply(text="{}", model=classifier_identity.runtime.model_id)

    transport.script = script
    binding = ClassifierBinding(classifier_identity, transport, counter)
    with pytest.raises(CodingError, match="^input_changed$"):
        binding.complete(coding_request)
    assert len(transport.requests) == (0 if stage == "counter" else 1)


@pytest.mark.parametrize("stage", ["counter", "transport"])
def test_transport_identity_mutation_refuses_publication(
    coding_request, classifier_identity, stage
):
    transport = scripted_transport(classifier_identity)

    def counter(request):
        if stage == "counter":
            transport.identity = transport.identity.model_copy(
                update={"model_id": PRIVATE}
            )
        return 5

    def script(request):
        if stage == "transport":
            transport.identity = transport.identity.model_copy(
                update={"model_id": PRIVATE}
            )
        return ModelReply(text="{}", model=classifier_identity.runtime.model_id)

    transport.script = script
    binding = ClassifierBinding(classifier_identity, transport, counter)
    with pytest.raises(CodingError, match="^model_mismatch$"):
        binding.complete(coding_request)
    assert len(transport.requests) == (0 if stage == "counter" else 1)


@pytest.mark.parametrize("kind", ["scripted", "binding"])
@pytest.mark.parametrize("stage", ["counter", "transport"])
def test_classifier_identity_mutation_refuses_publication(
    coding_request, classifier_identity, kind, stage
):
    dispatched = []

    def counter(request):
        if stage == "counter":
            object.__setattr__(classifier.identity, "family", PRIVATE)
        return 5

    def script(request):
        dispatched.append(request)
        if stage == "transport":
            object.__setattr__(classifier.identity, "family", PRIVATE)
        return ModelReply(text="{}", model=classifier_identity.runtime.model_id)

    classifier = (
        ScriptedClassifier(script, counter, classifier_identity)
        if kind == "scripted"
        else ClassifierBinding(
            classifier_identity,
            scripted_transport(classifier_identity, script),
            counter,
        )
    )
    with pytest.raises(CodingError, match="^model_mismatch$"):
        classifier.complete(coding_request)
    assert len(dispatched) == (0 if stage == "counter" else 1)


@pytest.mark.parametrize(
    "problem",
    [
        ExtractionProblem.MODEL_MISMATCH,
        ExtractionProblem.TOOL_CALL_REFUSED,
        ExtractionProblem.TRANSPORT_ERROR,
    ],
)
def test_transport_refusal_keeps_raw_reply_and_usage(
    coding_request, classifier_identity, problem
):
    reply = ModelReply(
        text=PRIVATE,
        model="wrong-model",
        usage=Usage(prompt_tokens=5, completion_tokens=2),
    )

    def refuse(request):
        raise AdapterError(problem, reply)

    binding = ClassifierBinding(
        classifier_identity,
        scripted_transport(classifier_identity, refuse),
        lambda request: 5,
    )
    with pytest.raises(CodingTransportError, match=f"^{problem.value}$") as caught:
        binding.complete(coding_request)
    assert caught.value.reply == reply
    assert caught.value.reply.usage == reply.usage
    assert PRIVATE not in "".join(traceback.format_exception(caught.value))


@pytest.mark.parametrize("kind", ["counter", "transport"])
def test_callback_errors_are_fixed_and_redacted(
    coding_request, classifier_identity, kind
):
    def fail(request):
        raise RuntimeError(PRIVATE)

    binding = ClassifierBinding(
        classifier_identity,
        scripted_transport(classifier_identity, fail if kind == "transport" else None),
        fail if kind == "counter" else lambda request: 5,
    )
    with pytest.raises(CodingError, match="^unexpected_error$") as caught:
        binding.complete(coding_request)
    assert PRIVATE not in "".join(traceback.format_exception(caught.value))


def test_local_binding_uses_complete_multifile_weights_manifest(classifier_identity):
    from earnings_themes.support.judges import transport_weights_hash

    identity = local_identity(classifier_identity)
    identity = identity.model_copy(
        update={
            "runtime": identity.runtime.model_copy(
                update={
                    "files": (
                        FileHash(relative_path="part-b", sha256="b" * 64),
                        FileHash(relative_path="part-a", sha256="a" * 64),
                    )
                }
            )
        }
    )
    transport = local_transport(identity)
    transport.identity = transport.identity.model_copy(
        update={"weights_sha256": transport_weights_hash(identity)}
    )
    assert (
        ClassifierBinding(identity, transport, lambda request: 5).identity == identity
    )


@pytest.mark.parametrize("response_kind", ["valid", "redirect", "tools", "model"])
def test_supplied_local_adapter_keeps_request_loopback_and_tool_free(
    coding_request, classifier_identity, no_network, response_kind
):
    identity = local_identity(classifier_identity)
    observed = []

    def handler(request):
        observed.append(request)
        assert request.url.host == "127.0.0.1"
        assert request.url.path == "/v1/chat/completions"
        body = json.loads(request.content)
        assert (
            "tools" not in body and "tool_choice" not in body and "subject" not in body
        )
        assert body["messages"] == [
            message.model_dump(mode="json") for message in coding_request.messages
        ]
        assert (
            body["response_format"]["json_schema"]["schema"]
            == coding_request.reply_schema
        )
        assert "authorization" not in request.headers
        if response_kind == "redirect":
            return httpx.Response(
                302, headers={"location": "https://example.invalid/forbidden"}
            )
        message = {"content": "{}"}
        if response_kind == "tools":
            message["tool_calls"] = [{"function": {"name": "forbidden"}}]
        return httpx.Response(
            200,
            json={
                "model": "wrong-model"
                if response_kind == "model"
                else identity.runtime.model_id,
                "choices": [{"message": message}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 2},
            },
        )

    adapter = LocalAdapter(
        LocalModelConfig(
            base_url="http://127.0.0.1:8080/v1",
            model_id=identity.runtime.model_id,
            weights_sha256="a" * 64,
            runtime=identity.runtime.runtime,
            runtime_version=identity.runtime.runtime_version,
        ),
        transport=httpx.MockTransport(handler),
    )
    binding = ClassifierBinding(identity, adapter, lambda request: 5)
    if response_kind == "valid":
        assert binding.complete(coding_request).usage == Usage(
            prompt_tokens=5, completion_tokens=2
        )
    else:
        reason = {
            "redirect": "transport_error",
            "tools": "tool_call_refused",
            "model": "model_mismatch",
        }[response_kind]
        with pytest.raises(CodingTransportError, match=f"^{reason}$"):
            binding.complete(coding_request)
    assert len(observed) == 1
    assert no_network == []


@pytest.mark.parametrize(
    "url",
    [
        "https://example.invalid/v1",
        "http://user:password@localhost/v1",
        " http://localhost/v1",
        "http://localhost:wrong/v1",
    ],
)
def test_supplied_local_adapter_refuses_nonlocal_or_invalid_endpoints(
    classifier_identity, url
):
    identity = local_identity(classifier_identity)
    with pytest.raises(ValueError):
        LocalAdapter(
            LocalModelConfig(
                base_url=url,
                model_id=identity.runtime.model_id,
                weights_sha256="a" * 64,
                runtime=identity.runtime.runtime,
                runtime_version=identity.runtime.runtime_version,
            )
        )
