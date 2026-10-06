"""Bounded reservation and truthful actual accounting for fake classification."""

import pytest
from earnings_themes.coding.adapters import CodingTransportError, ScriptedClassifier
from earnings_themes.coding.cache import CodingCache
from earnings_themes.coding.classify import CodingAllowance, classify_claim
from earnings_themes.coding.records import CodingCeilings, CodingError
from earnings_themes.extraction.adapters import Message, ModelReply, Usage


def ceilings(**updates):
    return CodingCeilings(
        requests_per_claim=2,
        requests_per_document=4,
        requests_per_run=8,
        tokens_per_document=100,
        tokens_per_run=200,
    ).model_copy(update=updates)


def test_missing_usage_retains_full_reservation_and_is_counted():
    allowance = CodingAllowance(ceilings(), run_id="invented-run")
    reserved = allowance.reserve("document", "claim", 5, 64)
    allowance.reconcile("document", reserved, None)
    assert (allowance.requests, allowance.tokens, allowance.unreported) == (1, 69, 1)
    with pytest.raises(CodingError, match="^tokens_exhausted$"):
        allowance.reserve("document", "claim", 5, 64)


def test_actual_overspend_is_not_clamped_and_stops_further_calls():
    allowance = CodingAllowance(ceilings(), run_id="invented-run")
    reserved = allowance.reserve("document", "claim", 5, 64)
    allowance.reconcile(
        "document", reserved, Usage(prompt_tokens=150, completion_tokens=10)
    )
    assert (allowance.tokens, allowance.doc_tokens["document"]) == (160, 160)
    with pytest.raises(CodingError, match="^tokens_exhausted$"):
        allowance.reserve("document", "second", 1, 1)


@pytest.mark.parametrize("kind", ["schema", "messages", "parameters", "subject"])
def test_generated_request_is_checked_against_source_before_dispatch(
    coding_input, coding_policy, classifier_identity, tmp_path, monkeypatch, kind
):
    from earnings_themes.coding import classify
    from earnings_themes.extraction.records import Parameters

    original = classify.render_coding

    def forged(input, policy):
        request = original(input, policy)
        if kind == "schema":
            request.reply_schema["properties"]["theme_ids"]["maxItems"] = 1
        elif kind == "messages":
            request = request.model_copy(
                update={
                    "messages": (
                        request.messages[0],
                        Message(role="user", content="{}"),
                    )
                }
            )
        elif kind == "parameters":
            request = request.model_copy(
                update={"parameters": Parameters(max_tokens=32)}
            )
        else:
            request = request.model_copy(
                update={
                    "subject": request.subject.model_copy(
                        update={"claim_id": "forged-claim"}
                    )
                }
            )
        return request

    monkeypatch.setattr(classify, "render_coding", forged)
    classifier = ScriptedClassifier(
        lambda request: ModelReply(
            text='{"theme_ids":[],"attributes":{}}',
            model=classifier_identity.runtime.model_id,
        ),
        lambda request: 5,
        classifier_identity,
    )
    with pytest.raises(CodingError, match="^input_changed$"):
        classify_claim(
            coding_input,
            classifier,
            coding_policy,
            CodingAllowance(ceilings(), run_id="invented-run"),
            cache=CodingCache(tmp_path, "live"),
        )
    assert classifier.requests == []


def test_invalid_source_mutation_during_callback_aborts_publication(
    coding_input, coding_policy, classifier_identity, tmp_path
):
    quote = coding_input.sources.stored_run.quotes[0]

    def mutate(request):
        object.__setattr__(quote.span, "start", quote.span.start + 1)
        return ModelReply(
            text='{"theme_ids":[],"attributes":{}}',
            model=classifier_identity.runtime.model_id,
            usage=Usage(prompt_tokens=7, completion_tokens=1),
        )

    classifier = ScriptedClassifier(mutate, lambda request: 5, classifier_identity)
    allowance = CodingAllowance(ceilings(), run_id="invented-run")
    with pytest.raises(CodingError, match="^input_changed$"):
        classify_claim(
            coding_input,
            classifier,
            coding_policy,
            allowance,
            cache=CodingCache(tmp_path, "live"),
        )
    assert (len(classifier.requests), allowance.requests, allowance.tokens) == (1, 1, 8)


def test_refusal_usage_is_charged_and_raw_refusal_replays(
    coding_input, coding_policy, classifier_identity, tmp_path
):
    reply = ModelReply(
        text='{"theme_ids":[],"attributes":{}}',
        model="invented-wrong-model",
        usage=Usage(prompt_tokens=80, completion_tokens=30),
        latency_ms=11,
    )

    def refuse(request):
        raise CodingTransportError("model_mismatch", reply)

    classifier = ScriptedClassifier(refuse, lambda request: 5, classifier_identity)
    limit = ceilings(tokens_per_document=300, tokens_per_run=300)
    allowance = CodingAllowance(limit, run_id="invented-run")
    result = classify_claim(
        coding_input,
        classifier,
        coding_policy,
        allowance,
        cache=CodingCache(tmp_path, "live"),
    )
    assert result.record.status == "incomplete"
    assert [row.reason for row in result.attempts] == ["model_mismatch"] * 2
    assert allowance.tokens == 220
    assert all(
        row.raw_ref is not None and row.actual_prompt_tokens == 80
        for row in result.attempts
    )

    def forbidden(request):
        raise AssertionError("fixture_callback_forbidden")

    replay_classifier = ScriptedClassifier(forbidden, forbidden, classifier_identity)
    replay_allowance = CodingAllowance(limit, run_id="invented-run")
    replay = classify_claim(
        coding_input,
        replay_classifier,
        coding_policy,
        replay_allowance,
        cache=CodingCache(tmp_path, "replay"),
    )
    assert replay.record == result.record
    assert all(row.cached for row in replay.attempts)
    assert replay_allowance.requests == replay_allowance.tokens == 0


@pytest.mark.parametrize(
    "values,reason",
    [
        ({"requests_per_claim": 0}, "requests_exhausted"),
        ({"requests_per_run": 0}, "requests_exhausted"),
        ({"tokens_per_document": 68}, "tokens_exhausted"),
        ({"tokens_per_run": 0}, "tokens_exhausted"),
    ],
)
def test_zero_and_near_limit_budgets_do_not_dispatch(proposal_job, values, reason):
    run, calls = proposal_job.run([], ceilings=ceilings(**values))
    assert calls == 0
    assert run.classifications[0].reason == reason
    assert run.targets == run.novelty == ()


def test_unreported_retry_reservation_stops_retry(proposal_job):
    run, calls = proposal_job.run(["{"], ceilings=ceilings(tokens_per_document=100))
    assert calls == 1
    assert [row.reason for row in run.attempts] == [
        "malformed_reply",
        "tokens_exhausted",
    ]
    assert (run.record.charged_tokens, run.record.unreported) == (69, 1)


@pytest.mark.parametrize(
    "identity_field,value", [("input_limit", 68), ("output_limit", 63)]
)
def test_full_input_and_output_limits_refuse_without_clipping(
    coding_case, coding_policy, classifier_identity, tmp_path, identity_field, value
):
    from .cases import make_proposal_job

    run, calls = make_proposal_job(
        coding_case,
        coding_policy,
        classifier_identity.model_copy(update={identity_field: value}),
        tmp_path,
    ).run([])
    assert calls == 0
    assert run.classifications[0].reason == "input_too_long"
    assert run.attempts[0].input_tokens == 5
    assert run.record.requests == run.record.charged_tokens == 0


@pytest.mark.parametrize("value", [True, 1.0, "1", -1])
def test_allowance_requires_strict_nonnegative_counters(value):
    with pytest.raises(CodingError, match="^malformed_record$"):
        CodingAllowance(ceilings(requests_per_claim=value), run_id="invented-run")
    allowance = CodingAllowance(ceilings(), run_id="invented-run")
    allowance.doc_tokens["document"] = value
    with pytest.raises(CodingError, match="^malformed_record$"):
        allowance.reserve("document", "claim", 5, 64)


@pytest.mark.parametrize("phase", ["count", "complete", "cache_hit"])
def test_mutable_request_schema_is_rechecked_at_every_boundary(
    coding_input, coding_policy, classifier_identity, tmp_path, monkeypatch, phase
):
    class CallbackClassifier:
        identity = classifier_identity

        def __init__(self):
            self.requests = []

        def count_tokens(self, request):
            if phase == "count":
                request.reply_schema["properties"]["theme_ids"]["maxItems"] = 1
            return 5

        def complete(self, request):
            self.requests.append(request)
            if phase == "complete":
                request.reply_schema["properties"]["theme_ids"]["maxItems"] = 1
            return ModelReply(
                text='{"theme_ids":[],"attributes":{}}',
                model=classifier_identity.runtime.model_id,
            )

    cache = CodingCache(tmp_path, "live")
    if phase == "cache_hit":
        classifier = ScriptedClassifier(
            lambda request: ModelReply(
                text='{"theme_ids":[],"attributes":{}}',
                model=classifier_identity.runtime.model_id,
            ),
            lambda request: 5,
            classifier_identity,
        )
        classify_claim(
            coding_input,
            classifier,
            coding_policy,
            CodingAllowance(ceilings(), run_id="invented-run"),
            cache=cache,
        )
        original = cache.get

        def changed(request, identity):
            entry = original(request, identity)
            request.reply_schema["properties"]["theme_ids"]["maxItems"] = 1
            return entry

        monkeypatch.setattr(cache, "get", changed)
    classifier = CallbackClassifier()
    allowance = CodingAllowance(ceilings(), run_id="invented-run")
    with pytest.raises(CodingError, match="^input_changed$"):
        classify_claim(coding_input, classifier, coding_policy, allowance, cache=cache)
    assert len(classifier.requests) == (1 if phase == "complete" else 0)


def test_replay_miss_is_distinct_from_corrupt_cache(proposal_job):
    run, calls = proposal_job.run([], "replay")
    assert calls == 0
    assert run.classifications[0].reason == "replay_miss"
    first, _ = proposal_job.run(['{"theme_ids":[],"attributes":{}}'])
    reference = first.attempts[0].raw_ref
    (proposal_job.root / "classifier-cache" / reference).write_text("{")
    with pytest.raises(CodingError, match="^cache_corrupt$"):
        proposal_job.run([], "replay")


def test_unexpected_callback_aborts_instead_of_publishing_empty_run(proposal_job):
    with pytest.raises(CodingError, match="^unexpected_error$"):
        proposal_job.run([RuntimeError("invented exception content")])


def test_changed_prompt_and_runtime_bindings_fail_before_dispatch(
    coding_input, coding_policy, classifier_identity, tmp_path
):
    classifier = ScriptedClassifier(
        lambda request: ModelReply(text="{}"), lambda request: 5, classifier_identity
    )
    policy = coding_policy.model_copy(
        update={"prompt_text": "Changed invented instructions."}
    )
    with pytest.raises(CodingError, match="^input_changed$"):
        classify_claim(
            coding_input,
            classifier,
            policy,
            CodingAllowance(ceilings(), run_id="invented-run"),
            cache=CodingCache(tmp_path, "live"),
        )
    assert classifier.requests == []


def test_hierarchy_conflict_retries_without_implicit_parent_assignment(
    coding_case, coding_policy, classifier_identity, tmp_path
):
    from dataclasses import replace

    from earnings_themes.codebook import codebook_hash

    from .cases import make_proposal_job

    book = coding_case.codebook
    book = book.model_copy(
        update={
            "themes": (
                book.themes[0],
                book.themes[1].model_copy(update={"parent_id": "capacity"}),
            )
        }
    )
    book = book.model_copy(update={"content_hash": codebook_hash(book)})
    run, calls = make_proposal_job(
        replace(coding_case, codebook=book),
        coding_policy,
        classifier_identity,
        tmp_path,
    ).run(
        [
            '{"theme_ids":["capacity","demand"],"attributes":{}}',
            '{"theme_ids":["demand"],"attributes":{}}',
        ]
    )
    assert calls == 2
    assert [row.reason for row in run.attempts] == ["hierarchy_conflict", None]
    assert tuple(target.theme_id for target in run.targets) == ("demand",)


@pytest.mark.parametrize(
    "text,reason,tool_calls",
    [
        ("{", "malformed_reply", False),
        ('{"theme_ids":["unknown"],"attributes":{}}', "invalid_references", False),
        ('{"theme_ids":[],"attributes":{}}', "tool_call_refused", True),
    ],
)
def test_retry_feedback_is_only_fixed_reason_and_binds_full_request(
    coding_input, coding_policy, classifier_identity, tmp_path, text, reason, tool_calls
):
    from collections import deque

    from earnings_core import digest

    replies = deque(
        (
            ModelReply(
                text=text,
                model=classifier_identity.runtime.model_id,
                tool_calls=tool_calls,
            ),
            ModelReply(
                text='{"theme_ids":[],"attributes":{}}',
                model=classifier_identity.runtime.model_id,
            ),
        )
    )
    classifier = ScriptedClassifier(
        lambda request: replies.popleft(), lambda request: 5, classifier_identity
    )
    result = classify_claim(
        coding_input,
        classifier,
        coding_policy,
        CodingAllowance(ceilings(tokens_per_document=500), run_id="invented-run"),
        cache=CodingCache(tmp_path, "live"),
    )
    first, second = classifier.requests
    assert len(first.messages) == 2 and len(second.messages) == 3
    assert second.messages[:2] == first.messages
    assert (
        second.messages[2].content
        == f"Unusable reply: {reason}. Return the closed JSON response only."
    )
    assert tuple(row.request_hash for row in result.attempts) == tuple(
        digest(request.model_dump(mode="json")) for request in classifier.requests
    )


def test_transport_failure_without_raw_is_bounded_and_unreported(proposal_job):
    run, calls = proposal_job.run(
        [
            CodingTransportError("transport_error"),
            CodingTransportError("transport_error"),
        ]
    )
    assert calls == 2
    assert run.classifications[0].reason == "transport_error"
    assert run.record.requests == run.record.unreported == 2
    assert run.record.charged_tokens == 138
    assert all(row.raw_ref is None for row in run.attempts)


def test_reconcile_cannot_create_negative_counters():
    allowance = CodingAllowance(ceilings(), run_id="invented-run")
    allowance.reserve("document", "claim", 5, 64)
    with pytest.raises(CodingError, match="^malformed_record$"):
        allowance.reconcile("document", 70, Usage(prompt_tokens=0, completion_tokens=0))
    assert allowance.tokens == allowance.doc_tokens["document"] == 69


def test_malformed_policy_mutation_after_callback_has_fixed_changed_reason(
    coding_input, coding_policy, classifier_identity, tmp_path
):
    def mutate(request):
        object.__setattr__(coding_policy.parameters, "seed", True)
        return ModelReply(
            text='{"theme_ids":[],"attributes":{}}',
            model=classifier_identity.runtime.model_id,
        )

    classifier = ScriptedClassifier(mutate, lambda request: 5, classifier_identity)
    with pytest.raises(CodingError, match="^input_changed$"):
        classify_claim(
            coding_input,
            classifier,
            coding_policy,
            CodingAllowance(ceilings(), run_id="invented-run"),
            cache=CodingCache(tmp_path, "live"),
        )


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("policy", "input_changed"),
        ("source", "input_changed"),
        ("request", "input_changed"),
        ("raw", "cache_corrupt"),
    ],
)
def test_classification_final_preflight_checks_bindings_after_callback(
    coding_input, coding_policy, classifier_identity, tmp_path, mutation, reason
):
    class PreflightClassifier:
        identity = classifier_identity

        def __init__(self, trigger=None):
            self.preflights = 0
            self.trigger = trigger
            self.requests = []
            self.changed = False

        def preflight(self):
            self.preflights += 1
            if self.preflights == self.trigger:
                self.changed = True
                if mutation == "policy":
                    object.__setattr__(
                        coding_policy.parameters,
                        "seed",
                        coding_policy.parameters.seed + 1,
                    )
                elif mutation == "source":
                    object.__setattr__(
                        coding_input.sources.stored_run.claims[0],
                        "claim",
                        "A changed invented claim.",
                    )
                elif mutation == "request":
                    self.requests[0].reply_schema["properties"]["theme_ids"][
                        "maxItems"
                    ] = 1
                else:
                    import json

                    from earnings_themes.coding.cache import (
                        coding_key,
                        raw_reply_hash,
                    )

                    path = (
                        tmp_path
                        / "changed"
                        / f"{coding_key(self.requests[0], self.identity)}.json"
                    )
                    data = json.loads(path.read_text())
                    data["reply"]["text"] = '{"theme_ids":["demand"],"attributes":{}}'
                    data["reply_hash"] = raw_reply_hash(
                        ModelReply.model_validate(data["reply"]),
                        data["refusal_reason"],
                        data["input_tokens"],
                    )
                    path.write_text(json.dumps(data))

        def count_tokens(self, request):
            return 5

        def complete(self, request):
            self.requests.append(request)
            return ModelReply(
                text='{"theme_ids":[],"attributes":{}}',
                model=classifier_identity.runtime.model_id,
            )

    baseline = PreflightClassifier()
    classify_claim(
        coding_input,
        baseline,
        coding_policy,
        CodingAllowance(ceilings(), run_id="invented-run"),
        cache=CodingCache(tmp_path / "baseline", "live"),
    )
    classifier = PreflightClassifier(baseline.preflights)
    with pytest.raises(CodingError, match=f"^{reason}$"):
        classify_claim(
            coding_input,
            classifier,
            coding_policy,
            CodingAllowance(ceilings(), run_id="invented-run"),
            cache=CodingCache(tmp_path / "changed", "live"),
        )
    assert classifier.changed
    assert len(classifier.requests) == 1
