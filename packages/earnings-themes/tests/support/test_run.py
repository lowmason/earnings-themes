"""Invented sequential coordination and run-level preflight."""

from dataclasses import replace
from datetime import UTC, datetime

import pytest
from earnings_core import digest
from earnings_themes.support.cache import SupportCache
from earnings_themes.support.problems import SupportError
from earnings_themes.support.run import assess_run

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
