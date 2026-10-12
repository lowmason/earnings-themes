"""Invented sequential coordination and run-level preflight."""

from dataclasses import replace
from datetime import UTC, datetime

import pytest
from earnings_core import digest
from earnings_themes.support.cache import SupportCache
from earnings_themes.support.problems import SupportError
from earnings_themes.support.run import assess_run
from earnings_themes.support.scorers import ScoreReply, ScriptedScorer

from .cases import append_fixture_claim
from .test_prompt import policy as policy  # noqa: PLC0414


def run(case, scorer, panel, policy, ceilings, path, targets=None, **overrides):
    sources, target = case
    options = {
        "extractor_family": "invented-extractor",
        "cache": SupportCache(path, "live"),
        "started_at": datetime(2026, 10, 5, tzinfo=UTC),
        "software": {"python": "test", "lock_hash": digest("test lock")},
    }
    options.update(overrides)
    return assess_run(
        "invented-run",
        sources,
        (target,) if targets is None else targets,
        scorer,
        panel,
        policy,
        ceilings,
        **options,
    )


def test_coordinates_and_counts(case, scorer, panel, policy, allowance, tmp_path):
    result = run(case, scorer, panel, policy, allowance.ceilings, tmp_path)
    assert result.record.requests == 4
    assert result.record.evaluations == 3
    assert result.record.counts_by_status == (("assessed", 1),)
    assert result.record.extractor_family == "invented-extractor"
    assert len(result.assessments) == 1


def test_caller_order_and_shared_document_ceiling(
    case, scorer, panel, policy, allowance, tmp_path
):
    sources, target = case
    original_id = sources.stored_run.claims[0].claim_id
    sources, claim = append_fixture_claim(sources)
    second = target.model_copy(update={"claim_id": claim.claim_id})
    ceilings = allowance.ceilings.model_copy(
        update={"scorer_per_document": 3, "judge_per_document": 4}
    )
    result = run(
        (sources, target), scorer, panel, policy, ceilings, tmp_path, (second, target)
    )
    assert [a.target.target.claim_id for a in result.assessments] == [
        claim.claim_id,
        original_id,
    ]
    assert result.assessments[1].outcome.status == "incomplete"
    assert set(result.assessments[1].outcome.missing) == {
        "scorer_exhausted",
        "judge_exhausted",
    }
    assert result.record.requests == 4 and result.record.evaluations == 3


@pytest.mark.parametrize(
    "kind",
    [
        "duplicate",
        "panel",
        "family",
        "software",
        "time",
        "policy",
        "source",
        "codebook",
    ],
)
def test_preflight_dispatches_nothing(
    case, scorer, panel, policy, allowance, tmp_path, kind
):
    sources, target = case
    kwargs = {}
    targets = (target,)
    if kind == "duplicate":
        targets = (target, target)
    elif kind == "panel":
        panel = (panel[0], panel[0])
    elif kind == "family":
        kwargs["extractor_family"] = " "
    elif kind == "software":
        kwargs["software"] = {"python": "test"}
    elif kind == "time":
        kwargs["started_at"] = datetime(2026, 10, 5, tzinfo=UTC).replace(tzinfo=None)
    elif kind == "policy":
        policy = policy.model_copy(update={"prompt_hash": digest("changed")})
    elif kind == "source":
        targets = (target.model_copy(update={"source_run_id": "wrong"}),)
    else:
        targets = (
            target.model_copy(
                update={
                    "codebook": target.codebook.model_copy(
                        update={"codebook_version": 99}
                    )
                }
            ),
        )
    with pytest.raises(SupportError):
        run(
            (sources, target),
            scorer,
            panel,
            policy,
            allowance.ceilings,
            tmp_path,
            targets,
            **kwargs,
        )
    assert not scorer.requests and all(not j.requests for j in panel)


def test_refused_row_is_auditable_without_dispatch(
    case, scorer, panel, policy, allowance, tmp_path
):
    sources, target = case
    sources = replace(sources, stored_run=replace(sources.stored_run, quotes=()))
    result = run((sources, target), scorer, panel, policy, allowance.ceilings, tmp_path)
    row = result.assessments[0]
    assert row.outcome.status == "refused" and row.outcome.missing == ("unknown_quote",)
    assert (
        row.evidence == row.contexts == row.trials == row.entailment == row.usage == ()
    )
    assert result.record.requests == result.record.evaluations == 0


def test_replay_rebuilds_outcomes_without_spending(
    case, scorer, panel, policy, allowance, tmp_path
):
    first = run(case, scorer, panel, policy, allowance.ceilings, tmp_path)
    second = run(
        case,
        scorer,
        panel,
        policy,
        allowance.ceilings,
        tmp_path,
        cache=SupportCache(tmp_path, "replay"),
    )
    assert first.assessments[0].outcome == second.assessments[0].outcome
    assert (
        second.record.requests
        == second.record.evaluations
        == second.record.reserved_tokens
        == 0
    )
    assert second.record.cache_hits == 7
    assert len(scorer.requests) == 3 and all(len(j.requests) == 2 for j in panel)


def test_semantic_reason_counts_survive_incomplete(
    case, scorer, panel, policy, allowance, tmp_path
):
    from .cases import negative_reply

    panel[0].script = negative_reply("wrong_attribution")
    ceilings = allowance.ceilings.model_copy(update={"judge_per_run": 2})
    result = run(case, scorer, panel, policy, ceilings, tmp_path)
    assert result.record.counts_by_reason == (
        ("judge_exhausted", 1),
        ("wrong_attribution", 1),
    )


def test_fresh_dispatches_every_request_and_replays_from_its_own_directory(
    case, scorer, panel, policy, allowance, tmp_path
):
    """A1 (plan 18): over a populated cache, fresh dispatches what a live run over an
    empty cache does (here 3 evaluations, 4 judge requests and no hit), and a replay
    over its directory reproduces the assessments."""
    first = run(case, scorer, panel, policy, allowance.ceilings, tmp_path).record
    scored, judged = len(scorer.requests), sum(len(j.requests) for j in panel)
    fresh = run(
        case,
        scorer,
        panel,
        policy,
        allowance.ceilings,
        tmp_path,
        cache=SupportCache(tmp_path, "fresh", stability_run_id="stability-1"),
    )
    record = fresh.record
    assert (record.cache_mode, record.stability_run_id) == ("fresh", "stability-1")
    assert (record.requests, record.evaluations, record.cache_hits) == (
        first.requests,
        first.evaluations,
        first.cache_hits,
    )
    assert record.cache_hits == 0
    assert (record.evaluations, record.requests) == (
        len(scorer.requests) - scored,
        sum(len(j.requests) for j in panel) - judged,
    )
    replay = run(
        case,
        scorer,
        panel,
        policy,
        allowance.ceilings,
        tmp_path,
        cache=SupportCache(tmp_path / "fresh" / "stability-1", "replay"),
    )
    assert (replay.record.evaluations, replay.record.requests) == (0, 0)

    def outcomes(result):
        return [
            (a.outcome.status, a.outcome.flags, a.outcome.missing)
            for a in result.assessments
        ]

    assert outcomes(replay) == outcomes(fresh)


def test_a_second_scorer_reuses_the_judges_replies_in_live_mode(
    case, scorer, scorer_identity, panel, policy, allowance, tmp_path
):
    """A2: SupportPolicy carries no scorer identity, so a second support run with
    another scorer and the same judges hits every judge entry in live mode. This
    pins behaviour that already holds: it passes before this task's code. The
    second scorer gives the first's score, so the judges are asked the same
    questions."""
    first = run(case, scorer, panel, policy, allowance.ceilings, tmp_path)
    runtime = scorer_identity.runtime.model_copy(
        update={"model_id": "invented-scorer-2"}
    )
    other_identity = scorer_identity.model_copy(update={"runtime": runtime})
    other = ScriptedScorer(
        lambda r: ScoreReply(
            score=0.99,
            reason=None,
            input_tokens=5,
            latency_ms=1,
            identity=other_identity,
            input_hash=r.input_hash,
        ),
        lambda r: 5,
        other_identity,
    )
    judged = sum(len(j.requests) for j in panel)
    second = run(case, other, panel, policy, allowance.ceilings, tmp_path)
    assert sum(len(j.requests) for j in panel) == judged
    assert (second.record.requests, second.record.evaluations) == (
        0,
        first.record.evaluations,
    )
    assert len(other.requests) == first.record.evaluations
    assert second.record.cache_hits == first.record.requests + first.record.cache_hits
