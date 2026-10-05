"""Invented offline assessment, independent trial retries, and raw replay."""

from dataclasses import replace

import pytest
from earnings_themes.extraction.adapters import ModelReply, Usage
from earnings_themes.support.assess import assess_target, derive_outcome
from earnings_themes.support.cache import SupportCache
from earnings_themes.support.judges import SupportTransportError
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import SignalStatus

from .cases import judge_reply, negative_reply
from .test_prompt import policy as policy  # noqa: PLC0414


def assess(resolved, scorer, panel, policy, allowance, path, mode="live"):
    return assess_target(
        resolved,
        scorer,
        panel,
        policy,
        allowance,
        cache=SupportCache(path, mode),
        extractor_family="invented-extractor",
    )


def test_positive_assessed_independent_signals(
    resolved, scorer, panel, policy, allowance, tmp_path
):
    result = assess(resolved, scorer, panel, policy, allowance, tmp_path)
    assert result.outcome.status == "assessed"
    assert not hasattr(result.outcome, "accepted")
    assert len(result.entailment) == 3
    assert len(result.trials) == len(result.attempts) == 4
    assert len({t.trial_id for t in result.trials}) == 4
    assert len(result.usage) == 7
    assert all(len(j.requests) == 2 for j in panel)
    assert all(len(r.messages) == 2 for j in panel for r in j.requests)
    assert result.evidence == resolved.evidence


def test_semantic_objection_is_final_not_retried(
    resolved, scorer, panel, policy, allowance, tmp_path
):
    panel[0].script = negative_reply("wrong_attribution")
    result = assess(resolved, scorer, panel, policy, allowance, tmp_path)
    assert result.outcome.status == "flagged"
    assert "wrong_attribution" in result.outcome.flags
    assert all(len(t.attempt_ids) == 1 for t in result.trials)
    assert all(s.score == 0.99 for s in result.entailment)


def test_uncertain_is_final(resolved, scorer, panel, policy, allowance, tmp_path):
    panel[0].script = judge_reply(
        claim_support="uncertain", theme_fit="uncertain", contribution="uncertain"
    )
    result = assess(resolved, scorer, panel, policy, allowance, tmp_path)
    assert result.outcome.status == "flagged"
    assert len(panel[0].requests) == 2


def test_missing_signal_preserves_objections(
    resolved, scorer, panel, policy, allowance, tmp_path
):
    scorer._script = lambda r: (_ for _ in ()).throw(SupportError("scorer_failed"))
    panel[0].script = negative_reply("theme_mismatch")
    result = assess(resolved, scorer, panel, policy, allowance, tmp_path)
    assert result.outcome.status == "incomplete"
    assert "scorer_failed" in result.outcome.missing
    assert "theme_mismatch" in result.outcome.flags


def test_invalid_evidence_refuses_zero_dispatch(
    resolved, scorer, panel, policy, allowance, tmp_path
):
    changed = replace(resolved, claim="Invented changed claim.")
    result = assess(changed, scorer, panel, policy, allowance, tmp_path)
    assert result.outcome.status == "refused"
    assert not result.evidence and not result.entailment and not result.trials
    assert not scorer.requests and all(not j.requests for j in panel)
    assert allowance.snapshot() == ()


@pytest.mark.parametrize("family", [None, "", " ", 1])
def test_family_preflight_zero_dispatch(
    resolved, scorer, panel, policy, allowance, tmp_path, family
):
    with pytest.raises(SupportError, match="invalid_panel"):
        assess_target(
            resolved,
            scorer,
            panel,
            policy,
            allowance,
            cache=SupportCache(tmp_path, "live"),
            extractor_family=family,
        )
    assert not scorer.requests and all(not j.requests for j in panel)


def test_missing_family_required(resolved, scorer, panel, policy, allowance, tmp_path):
    with pytest.raises(TypeError):
        assess_target(
            resolved,
            scorer,
            panel,
            policy,
            allowance,
            cache=SupportCache(tmp_path, "live"),
        )
    assert not scorer.requests


def test_policy_preflight_zero_dispatch(
    resolved, scorer, panel, policy, allowance, tmp_path
):
    with pytest.raises(SupportError, match="input_changed"):
        assess(
            resolved,
            scorer,
            panel,
            policy.model_copy(update={"prompt_hash": "0" * 64}),
            allowance,
            tmp_path,
        )
    assert not scorer.requests and all(not j.requests for j in panel)


@pytest.mark.parametrize("failure", ["schema", "model", "tools", "transport"])
def test_unusable_first_cached_then_valid_second_replays(
    resolved, scorer, panel, policy, allowance, tmp_path, failure
):
    positive = judge_reply()

    def script(request):
        if len(request.messages) == 2:
            raw = ModelReply(
                text="INVENTED_PRIVATE_REPLY",
                model="wrong" if failure == "model" else "invented-judge",
                tool_calls=failure == "tools",
                usage=Usage(prompt_tokens=7, completion_tokens=4),
            )
            if failure == "transport":
                raise SupportTransportError("tool_call_refused", raw)
            return raw
        assert "INVENTED_PRIVATE_REPLY" not in request.messages[-1].content
        return positive(request)

    panel[0].script = script
    first = assess(resolved, scorer, panel, policy, allowance, tmp_path)
    assert first.outcome.status == "assessed"
    assert [len(t.attempt_ids) for t in first.trials] == [2, 2, 1, 1]
    assert first.attempts[0].actual_prompt_tokens == 7
    assert first.attempts[0].actual_completion_tokens == 4
    counts = (len(scorer.requests), *(len(j.requests) for j in panel))
    before = allowance.snapshot()
    second = assess(resolved, scorer, panel, policy, allowance, tmp_path, "replay")
    assert second.outcome == first.outcome
    assert all(a.cached for a in second.attempts)
    assert allowance.snapshot() == before
    assert counts == (len(scorer.requests), *(len(j.requests) for j in panel))
    assert all(u.cached for u in second.usage)


def test_failed_trials_at_most_two_independent_requests(
    resolved, scorer, panel, policy, allowance, tmp_path
):
    panel[0].script = lambda r: ModelReply(
        text="INVENTED_PRIVATE_REPLY", model="invented-judge"
    )
    result = assess(resolved, scorer, panel, policy, allowance, tmp_path)
    assert result.outcome.status == "incomplete"
    assert [len(t.attempt_ids) for t in result.trials] == [2, 2, 1, 1]
    assert len(panel[0].requests) == 4
    assert len(panel[1].requests) == 2
    assert len(panel[0].requests[2].messages) == 2
    assert all(
        "INVENTED_PRIVATE_REPLY" not in r.messages[-1].content
        for j in panel
        for r in j.requests
    )


def test_token_exhaustion_retains_previous_trial(
    resolved, scorer, panel, policy, allowance, tmp_path
):
    allowance.ceilings = allowance.ceilings.model_copy(
        update={"tokens_per_run": 2058, "tokens_per_document": 2058}
    )
    panel[0].script = lambda r: judge_reply()(r).model_copy(update={"usage": None})
    result = assess(resolved, scorer, panel, policy, allowance, tmp_path)
    assert result.trials[0].status == SignalStatus.AVAILABLE
    assert [t.reason for t in result.trials[1:]] == ["tokens_exhausted"] * 3
    assert result.outcome.status == "incomplete"
    assert len(panel[0].requests) == 1 and not panel[1].requests


def test_limits_before_reservation(
    resolved, scorer, panel, policy, allowance, tmp_path
):
    scorer._token_counter = lambda r: 1001
    panel[0]._token_counter = lambda r: 10000
    result = assess(resolved, scorer, panel, policy, allowance, tmp_path)
    assert all(s.reason == "input_too_long" for s in result.entailment)
    assert all(t.reason == "input_too_long" for t in result.trials[:2])
    assert not scorer.requests and not panel[0].requests
    assert len(result.usage) == 2


def test_one_quote_aliases_evaluation(
    one_quote, scorer, panel, policy, allowance, tmp_path
):
    result = assess(one_quote, scorer, panel, policy, allowance, tmp_path)
    assert len(result.entailment) == 2 and len(scorer.requests) == 1
    assert len({s.evaluation_id for s in result.entailment}) == 1
    assert len({s.signal_id for s in result.entailment}) == 2


def test_replay_misses_no_dispatch(
    resolved, scorer, panel, policy, allowance, tmp_path
):
    result = assess(resolved, scorer, panel, policy, allowance, tmp_path, "replay")
    assert result.outcome.status == "incomplete"
    assert result.outcome.missing == ("replay_miss",)
    assert not result.usage and allowance.snapshot() == ()
    assert not scorer.requests and all(not j.requests for j in panel)


def test_numeric_differences_alone_not_flags(
    resolved, scorer, panel, policy, allowance, tmp_path
):
    from earnings_themes.support.scorers import ScoreReply

    scorer._script = lambda r: ScoreReply(
        score=0.0,
        reason=None,
        input_tokens=5,
        latency_ms=0,
        identity=scorer.identity,
        input_hash=r.input_hash,
    )
    panel[0].script = lambda r: judge_reply()(r).model_copy(
        update={"text": judge_reply()(r).text.replace("0.9", "0.01")}
    )
    result = assess(resolved, scorer, panel, policy, allowance, tmp_path)
    assert result.outcome.status == "assessed" and not result.outcome.flags


def test_quote_order_not_disagreement(
    resolved, scorer, panel, policy, allowance, tmp_path
):
    result = assess(resolved, scorer, panel, policy, allowance, tmp_path)
    trial = result.trials[0]
    reversed_answer = trial.answer.model_copy(
        update={"quote_assessments": tuple(reversed(trial.answer.quote_assessments))}
    )
    trials = (trial.model_copy(update={"answer": reversed_answer}), *result.trials[1:])
    outcome = derive_outcome(
        resolved.record.target_id,
        result.entailment,
        trials,
        resolved.record.evidence_ids,
    )
    assert not outcome.flags


def test_contextual_quote_permitted_context_only_assertion_flagged(
    resolved, scorer, panel, policy, allowance, tmp_path
):
    panel[0].script = judge_reply(contribution="contextual")
    panel[1].script = judge_reply(contribution="contextual")
    result = assess(resolved, scorer, panel, policy, allowance, tmp_path)
    assert result.outcome.status == "assessed"
    panel[0].script = judge_reply(reasons=("context_only_support",))
    changed = assess(resolved, scorer, panel, policy, allowance, tmp_path / "changed")
    assert "context_only_support" in changed.outcome.flags


def test_unexpected_exception_redacted_completed_calls_cached(
    resolved, scorer, panel, policy, allowance, tmp_path
):
    panel[1].script = lambda r: (_ for _ in ()).throw(
        RuntimeError("INVENTED_PRIVATE_EXCEPTION")
    )
    with pytest.raises(SupportError, match="^unexpected_error$") as error:
        assess(resolved, scorer, panel, policy, allowance, tmp_path)
    assert error.value.__suppress_context__
    assert "INVENTED_PRIVATE_EXCEPTION" not in repr(error.value)
    assert error.value.diagnostic == "RuntimeError"
    panel[1].script = judge_reply()
    result = assess(resolved, scorer, panel, policy, allowance, tmp_path)
    assert all(s.cached for s in result.entailment)
    assert all(a.cached for a in result.attempts[:2])


@pytest.mark.parametrize(
    "reason", ["transport_error", "tool_call_refused", "model_mismatch"]
)
def test_otherwise_valid_refused_transport_reply_retained_on_replay(
    resolved, scorer, panel, policy, allowance, tmp_path, reason
):
    def script(request):
        raw = judge_reply()(request)
        if len(request.messages) == 2:
            raise SupportTransportError(reason, raw)
        assert reason in request.messages[-1].content
        return raw

    panel[0].script = script
    first = assess(resolved, scorer, panel, policy, allowance, tmp_path)
    assert first.attempts[0].problem == reason
    assert first.attempts[0].answer is None
    assert first.attempts[0].actual_completion_tokens == 3
    assert len(first.attempts) == 6
    counts = tuple(len(j.requests) for j in panel)
    second = assess(resolved, scorer, panel, policy, allowance, tmp_path, "replay")
    assert tuple(len(j.requests) for j in panel) == counts
    assert second.attempts[0].problem == reason and second.attempts[0].answer is None
    assert [a.request_hash for a in first.attempts] == [
        a.request_hash for a in second.attempts
    ]
    assert first.outcome == second.outcome


@pytest.mark.parametrize(
    "reason", ["transport_error", "model_mismatch", "malformed_reply"]
)
def test_errors_without_raw_still_two_attempts(
    resolved, scorer, panel, policy, allowance, tmp_path, reason
):
    panel[0].script = lambda r: (_ for _ in ()).throw(SupportError(reason))
    result = assess(resolved, scorer, panel, policy, allowance, tmp_path)
    assert len(panel[0].requests) == 4
    assert all(a.answer is None and a.problem == reason for a in result.attempts[:4])
    assert all(u.unreported for u in result.usage[3:7])


def test_same_family_panel_refuses_before_scorer(
    resolved, scorer, panel, policy, allowance, tmp_path
):
    panel[1]._identity = panel[0].identity
    with pytest.raises(SupportError, match="invalid_panel"):
        assess(resolved, scorer, panel, policy, allowance, tmp_path)
    assert not scorer.requests and all(not j.requests for j in panel)


def test_missing_required_rows_incomplete_not_assessed():
    result = derive_outcome("invented-target", (), (), ("invented-q",))
    assert result.status == "incomplete" and result.missing == ("invalid_references",)


@pytest.mark.parametrize("category", ["irrelevant", "contradicting", "uncertain"])
def test_quote_objections_are_fixed_flags(
    resolved, scorer, panel, policy, allowance, tmp_path, category
):
    panel[0].script = judge_reply(contribution=category)
    result = assess(resolved, scorer, panel, policy, allowance, tmp_path)
    assert f"quote_{category}" in result.outcome.flags
    assert "category_disagreement" in result.outcome.flags


@pytest.mark.parametrize("custom", [False, True])
def test_unexpected_scorer_type_only_safe_diagnostic(
    resolved, scorer, panel, policy, allowance, tmp_path, custom
):
    error_type = (
        type("INVENTED_PRIVATE_CLASS", (RuntimeError,), {}) if custom else RuntimeError
    )
    scorer._script = lambda r: (_ for _ in ()).throw(
        error_type("INVENTED_PRIVATE_EXCEPTION")
    )
    with pytest.raises(SupportError, match="^unexpected_error$") as caught:
        assess(resolved, scorer, panel, policy, allowance, tmp_path)
    assert caught.value.diagnostic == ("Exception" if custom else "RuntimeError")
    assert (
        "INVENTED_PRIVATE"
        not in str(caught.value) + repr(caught.value) + caught.value.diagnostic
    )
    assert caught.value.__suppress_context__


def test_malformed_typed_reply_retries_with_unreported_usage(
    resolved, scorer, panel, policy, allowance, tmp_path
):
    panel[0].script = lambda r: ModelReply.model_construct(
        text="INVENTED_REPLY",
        usage=Usage.model_construct(prompt_tokens=True, completion_tokens=1),
        model="invented-judge",
        tool_calls=False,
        latency_ms=0,
        cached=False,
    )
    result = assess(resolved, scorer, panel, policy, allowance, tmp_path)
    assert len(panel[0].requests) == 4
    assert [t.reason for t in result.trials[:2]] == [
        "malformed_reply",
        "malformed_reply",
    ]
    assert all(u.unreported for u in result.usage[3:7])


def test_live_usage_preserves_reported_latency(
    resolved, scorer, panel, policy, allowance, tmp_path
):
    result = assess(resolved, scorer, panel, policy, allowance, tmp_path)
    assert [u.latency_ms for u in result.usage] == [1, 1, 1, 2, 2, 2, 2]


def test_mutated_canonical_after_dispatch_aborts_and_keeps_completed_raw(
    resolved, scorer, panel, policy, allowance, tmp_path
):
    original = scorer._script
    document = resolved.sources.bundles[0].document

    def mutate(request):
        reply = original(request)
        object.__setattr__(
            document, "canonical_text", "Invented mutated canonical text."
        )
        return reply

    scorer._script = mutate
    with pytest.raises(SupportError) as caught:
        assess(resolved, scorer, panel, policy, allowance, tmp_path)
    assert str(caught.value) in {
        "input_changed",
        "invalid_bundle",
        "canonical_hash_mismatch",
    }
    assert caught.value.__suppress_context__
    assert len(list(tmp_path.glob("*.json"))) == 1
    assert len(allowance.snapshot()) == 1
    assert len(scorer.requests) == 1 and all(not j.requests for j in panel)


def test_three_family_panel_missing_presentation_is_incomplete(
    resolved, scorer, panel, policy, allowance, tmp_path
):
    result = assess(resolved, scorer, panel, policy, allowance, tmp_path)
    fourth = result.trials[3]
    malformed = (
        *result.trials[:3],
        fourth.model_copy(
            update={
                "identity": fourth.identity.model_copy(
                    update={"family": "invented-family-third"}
                ),
                "presentation": "evidence_first",
            }
        ),
    )
    outcome = derive_outcome(
        resolved.record.target_id,
        result.entailment,
        malformed,
        resolved.record.evidence_ids,
    )
    assert outcome.status == "incomplete"
    assert outcome.missing == ("invalid_references",)
