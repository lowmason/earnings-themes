"""Raw scorer contracts use invented input and guarded sockets."""

from dataclasses import replace

import pytest
from earnings_core import digest
from earnings_themes.support.problems import SupportError
from earnings_themes.support.prompt import evidence_text, joint_premise
from earnings_themes.support.scorers import (
    ScoreReply,
    ScriptedScorer,
    evaluate_score,
    score_requests,
)

from .cases import resolved_case


def reply(request, identity, score=0.7, reason=None):
    return ScoreReply(
        score=score,
        reason=reason,
        input_tokens=4,
        latency_ms=0,
        identity=identity,
        input_hash=request.input_hash,
    )


def test_single_quote_joint_alias_costs_one_evaluation(one_quote):
    requests = score_requests(one_quote)
    assert len(requests) == 1
    scope, request = requests[0]
    assert scope == one_quote.evidence[0].quote_id
    assert request.hypothesis == one_quote.claim
    assert request.premise == evidence_text(one_quote, one_quote.evidence[0])
    assert "INVENTED_CONTEXT_ONLY_ASSERTION" not in request.premise
    assert request.input_hash == digest(
        {
            "encoding": "semantic-support/1",
            "premise": request.premise,
            "hypothesis": one_quote.claim,
        }
    )


def test_distributed_compound_evidence_keeps_three_raw_evaluations(
    case, scorer_identity
):
    resolved = resolved_case(*case)
    requests = score_requests(resolved)
    assert tuple(scope for scope, _ in requests) == (
        *resolved.record.evidence_ids,
        None,
    )
    assert len({r.input_hash for _, r in requests}) == 3
    assert all(r.hypothesis == resolved.claim for _, r in requests)
    assert requests[-1][1].premise == joint_premise(resolved)
    fake = ScriptedScorer(
        lambda r: reply(r, scorer_identity, 0.99), lambda r: 4, scorer_identity
    )
    results = tuple(evaluate_score(fake, r) for _, r in requests)
    assert len(results) == len(fake.requests) == 3
    assert all(r.score == 0.99 for r in results)
    assert all("accepted" not in type(r).model_fields for r in results)


@pytest.mark.parametrize("changed", ["claim", "evidence"])
def test_planner_rechecks_entire_input(one_quote, changed):
    bad = replace(
        one_quote, **({"claim": "CHANGED"} if changed == "claim" else {"evidence": ()})
    )
    with pytest.raises(SupportError, match="input_changed"):
        score_requests(bad)


def test_failure_is_null_not_zero(one_quote, scorer_identity):
    def failed(r):
        raise SupportError("scorer_failed")

    fake = ScriptedScorer(failed, lambda r: 4, scorer_identity)
    result = evaluate_score(fake, score_requests(one_quote)[0][1])
    assert result.score is None and result.reason == "scorer_failed"


@pytest.mark.parametrize("score", [float("nan"), float("inf"), -0.1, 1.1, True])
def test_malformed_score_unavailable(one_quote, scorer_identity, score):
    request = score_requests(one_quote)[0][1]
    raw = reply(request, scorer_identity).model_copy(update={"score": score})
    fake = ScriptedScorer(lambda r: raw, lambda r: 4, scorer_identity)
    result = evaluate_score(fake, request)
    assert result.score is None and result.reason == "malformed_reply"


@pytest.mark.parametrize("binding", ["identity", "input_hash"])
def test_reply_binding_mismatch(one_quote, scorer_identity, binding):
    request = score_requests(one_quote)[0][1]
    value = (
        scorer_identity.model_copy(update={"input_limit": 999})
        if binding == "identity"
        else digest("wrong")
    )
    raw = reply(request, scorer_identity).model_copy(update={binding: value})
    fake = ScriptedScorer(lambda r: raw, lambda r: 4, scorer_identity)
    result = evaluate_score(fake, request)
    assert result.score is None
    assert result.reason == (
        "model_mismatch" if binding == "identity" else "input_changed"
    )


def test_full_input_count_precedes_dispatch(one_quote, scorer_identity):
    request = score_requests(one_quote)[0][1]
    counted = []

    def count(r):
        counted.append(r)
        return scorer_identity.input_limit + 1

    fake = ScriptedScorer(lambda r: reply(r, scorer_identity), count, scorer_identity)
    result = evaluate_score(fake, request)
    assert counted == [request] and fake.requests == []
    assert result.score is None and result.reason == "input_too_long"
    assert result.input_tokens == scorer_identity.input_limit + 1


@pytest.mark.parametrize("count", [True, -1, 1.5])
def test_invalid_token_count_never_dispatches(one_quote, scorer_identity, count):
    fake = ScriptedScorer(
        lambda r: reply(r, scorer_identity), lambda r: count, scorer_identity
    )
    result = evaluate_score(fake, score_requests(one_quote)[0][1])
    assert result.reason == "malformed_reply" and fake.requests == []


def test_unexpected_failure_aborts_safely(one_quote, scorer_identity):
    def crash(r):
        raise RuntimeError("SECRET_SENTINEL")

    fake = ScriptedScorer(crash, lambda r: 4, scorer_identity)
    with pytest.raises(SupportError, match="unexpected_error") as caught:
        evaluate_score(fake, score_requests(one_quote)[0][1])
    assert caught.value.__suppress_context__
    assert "SECRET_SENTINEL" not in str(caught.value)


def test_safe_representations(one_quote, scorer_identity):
    request = score_requests(one_quote)[0][1]
    fake = ScriptedScorer(
        lambda r: reply(r, scorer_identity), lambda r: 4, scorer_identity
    )
    result = evaluate_score(fake, request)
    for value in (request, result, fake):
        assert request.premise not in str(value)
        assert request.hypothesis not in repr(value)


def test_null_reply_requires_fixed_reason(scorer_identity):
    from earnings_themes.support.records import parse_support

    with pytest.raises(SupportError, match="malformed_record"):
        parse_support(
            {
                "score": None,
                "reason": None,
                "input_tokens": None,
                "latency_ms": 0,
                "identity": scorer_identity.model_dump(mode="json"),
                "input_hash": digest("invented"),
            },
            ScoreReply,
        )


@pytest.mark.parametrize("field", ["input_tokens", "latency_ms"])
def test_reply_boolean_counts_unavailable(one_quote, scorer_identity, field):
    request = score_requests(one_quote)[0][1]
    raw = reply(request, scorer_identity).model_copy(update={field: True})
    fake = ScriptedScorer(lambda r: raw, lambda r: 4, scorer_identity)
    assert evaluate_score(fake, request).reason == "malformed_reply"


def test_request_hash_mismatch_prevents_dispatch(one_quote, scorer_identity):
    request = score_requests(one_quote)[0][1].model_copy(
        update={"input_hash": digest("wrong")}
    )
    fake = ScriptedScorer(
        lambda r: reply(r, scorer_identity), lambda r: 4, scorer_identity
    )
    with pytest.raises(SupportError, match="input_changed"):
        evaluate_score(fake, request)
    assert fake.requests == []


def test_available_reply_requires_usage(scorer_identity):
    from earnings_themes.support.records import parse_support

    with pytest.raises(SupportError, match="malformed_record"):
        parse_support(
            {
                "score": 0.5,
                "reason": None,
                "input_tokens": None,
                "latency_ms": 0,
                "identity": scorer_identity.model_dump(mode="json"),
                "input_hash": digest("invented"),
            },
            ScoreReply,
        )


def test_unexpected_identity_failure_aborts_safely(one_quote):
    class BrokenIdentity:
        @property
        def identity(self):
            raise RuntimeError("SECRET_SENTINEL")

    with pytest.raises(SupportError, match="unexpected_error") as caught:
        evaluate_score(BrokenIdentity(), score_requests(one_quote)[0][1])
    assert caught.value.__suppress_context__
