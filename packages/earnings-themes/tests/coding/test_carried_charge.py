"""A resumed fresh run charges the replies its own earlier process wrote (D21-38).

Invented data only. A process that stops in the middle of a run leaves its replies in
the run's own cache directory. The next process reads them back. The run's rows,
counters and cut set must equal those of a run that was never stopped."""

import json
from datetime import UTC, datetime

import pytest
from earnings_core import digest
from earnings_themes.coding.adapters import CodingTransportError, ScriptedClassifier
from earnings_themes.coding.cache import CodingCache, coding_key
from earnings_themes.coding.records import CodingCeilings
from earnings_themes.coding.run import propose_run
from earnings_themes.coding.store import read_coding_run, write_coding_run
from earnings_themes.extraction.adapters import ModelReply, Usage

from .cases import (
    FixturePolicy,
    forbidden_replay_callback,
    invented_bundle,
    invented_codebook,
    make_assessed_case,
    make_coding_run,
    make_proposal_job,
    make_sources,
)

MODEL = "invented-classifier"
REPLY = {"theme_ids": ["capacity"], "attributes": {}}
COUNTED = 5
"""Tokens that ``make_proposal_job``'s counter reports for each request."""
MAX_TOKENS = 64
"""The ``coding_policy`` fixture's reply limit, reserved with each request."""
RESERVED = COUNTED + MAX_TOKENS


def measured(*, prompt=11, completion=3, latency=7):
    """A reply that reports usage and latency, so a charge is told from a reserve."""
    return ModelReply(
        model=MODEL,
        text=json.dumps(REPLY),
        usage=Usage(prompt_tokens=prompt, completion_tokens=completion),
        latency_ms=latency,
    )


def limits(**changes):
    values = {
        "requests_per_claim": 2,
        "requests_per_document": 20,
        "requests_per_run": 40,
        "tokens_per_document": 100000,
        "tokens_per_run": 200000,
    }
    return CodingCeilings(**(values | changes))


@pytest.fixture
def make_job(codebook, template, coding_policy, classifier_identity, tmp_path):
    def make(claims, documents=1):
        sources = make_sources(
            invented_codebook(codebook),
            invented_bundle("invented-first"),
            template,
            other_bundles=tuple(
                invented_bundle(f"invented-{i}") for i in range(1, documents)
            ),
            claim_texts=tuple(
                f"An invented operating claim {i}." for i in range(claims)
            ),
        )
        return make_proposal_job(sources, coding_policy, classifier_identity, tmp_path)

    return make


def fresh(job, run_id, replies, **kwargs):
    """One process: a fresh run under ``run_id``, which resumes the run's own cache."""
    return job.run(replies, "fresh", stability_run_id=run_id, **kwargs)


def stopped(job, run_id, replies, **kwargs):
    """One process that dies on a ``KeyboardInterrupt`` in its reply queue."""
    with pytest.raises(KeyboardInterrupt):
        fresh(job, run_id, replies, **kwargs)


def same_run(resumed, whole, resumed_id):
    """Rows, records and totals of ``resumed`` equal those of ``whole``, which was
    never stopped. Only the stability run ID differs."""
    assert resumed.attempts == whole.attempts
    assert resumed.classifications == whole.classifications
    assert resumed.proposals == whole.proposals
    assert resumed.attributes == whole.attributes
    assert resumed.novelty == whole.novelty
    assert resumed.record == whole.record.model_copy(
        update={"stability_run_id": resumed_id}
    )


def round_trips(run, job, root):
    """The store's accounting check accepts the run: write it and read it back."""
    case = make_assessed_case(run, job.sources, root / "assessed")
    policy = FixturePolicy(case.proposals, case.support)
    result = make_coding_run(case, policy)
    path = write_coding_run(root / "coding", result, case.sources, case.support, policy)
    return read_coding_run(path)


def test_resumed_fresh_run_records_the_same_rows_and_totals_as_an_uninterrupted_run(
    make_job, tmp_path
):
    job = make_job(4)
    whole, _ = fresh(job, "a", [measured()] * 4)
    assert (
        whole.record.requests,
        whole.record.cache_hits,
        whole.record.reserved_tokens,
        whole.record.charged_tokens,
        whole.record.latency_ms,
    ) == (4, 0, 4 * RESERVED, 4 * 14, 4 * 7)
    stopped(job, "b", [measured(), measured(), KeyboardInterrupt()])
    resumed, calls_in_second_process = fresh(job, "b", [measured()] * 4)
    assert calls_in_second_process == 2
    assert resumed.attempts == whole.attempts
    assert (
        resumed.record.requests,
        resumed.record.cache_hits,
        resumed.record.reserved_tokens,
        resumed.record.charged_tokens,
        resumed.record.latency_ms,
    ) == (
        4,
        0,
        whole.record.reserved_tokens,
        whole.record.charged_tokens,
        whole.record.latency_ms,
    )
    assert resumed.classifications == whole.classifications
    assert resumed.proposals == whole.proposals
    same_run(resumed, whole, "b")
    stored = round_trips(resumed, job, tmp_path / "resumed")
    assert stored.attempts == resumed.attempts


def test_a_pause_after_a_cut_keeps_the_cut_set(make_job, tmp_path):
    job = make_job(5, documents=2)
    ceilings = limits(requests_per_document=3)
    whole, _ = fresh(job, "a", [REPLY] * 6, ceilings=ceilings)
    stopped(job, "b", [REPLY] * 3 + [KeyboardInterrupt()], ceilings=ceilings)
    resumed, calls = fresh(job, "b", [REPLY] * 6, ceilings=ceilings)
    assert calls == 3

    def cut(run):
        return [
            (row.doc_id, row.claim_id)
            for row in run.classifications
            if row.reason == "requests_exhausted"
        ]

    assert cut(resumed) == cut(whole) and len(cut(whole)) == 4
    assert resumed.record.requests == whole.record.requests == 6
    same_run(resumed, whole, "b")
    round_trips(resumed, job, tmp_path / "resumed")


def test_consume_carried_is_true_once_for_a_reply_an_earlier_process_wrote(
    coding_request, classifier_identity, tmp_path
):
    key = coding_key(coding_request, classifier_identity)
    other = classifier_identity.model_copy(update={"family": "another-family"})
    other_key = coding_key(coding_request, other)
    assert key != other_key
    reply = ModelReply(model=MODEL, text=json.dumps(REPLY))
    earlier = CodingCache(tmp_path, "fresh", stability_run_id="s-1")
    earlier.put(coding_request, classifier_identity, reply, input_tokens=COUNTED)
    earlier.put(coding_request, other, reply, input_tokens=COUNTED)
    # The process that wrote a reply never counts it as carried.
    assert earlier.consume_carried(key) is False
    assert earlier.consume_carried(other_key) is False
    cache = CodingCache(tmp_path, "fresh", stability_run_id="s-1")
    assert cache.consume_carried(key) is True
    assert cache.consume_carried(key) is False  # duplicate-key hit: not charged
    assert cache.consume_carried(other_key) is True  # each key is charged once
    assert cache.consume_carried(other_key) is False
    # A new instance is a new process: it reads the same reply as carried again.
    assert (
        CodingCache(tmp_path, "fresh", stability_run_id="s-1").consume_carried(key)
        is True
    )
    # A key this instance writes after an earlier read is still its own.
    later = CodingCache(tmp_path, "fresh", stability_run_id="s-2")
    assert later.consume_carried(key) is True
    later.put(coding_request, classifier_identity, reply, input_tokens=COUNTED)
    assert later.consume_carried(key) is False


@pytest.mark.parametrize("mode", ["live", "replay"])
def test_consume_carried_is_false_outside_fresh_mode(
    coding_request, classifier_identity, tmp_path, mode
):
    key = coding_key(coding_request, classifier_identity)
    CodingCache(tmp_path, "live").put(
        coding_request,
        classifier_identity,
        ModelReply(model=MODEL, text=json.dumps(REPLY)),
        input_tokens=COUNTED,
    )
    cache = CodingCache(tmp_path, mode)
    assert cache.consume_carried(key) is False
    assert cache.consume_carried(key) is False


def test_live_and_replay_hits_stay_cached_and_uncharged(make_job):
    job = make_job(3)
    first, calls = job.run([measured()] * 3)
    assert (calls, first.record.requests) == (3, 3)
    for mode in ("live", "replay"):
        again, calls = job.run([], mode)
        assert calls == 0
        assert again.record.requests == again.record.reserved_tokens == 0
        assert again.record.charged_tokens == again.record.latency_ms == 0
        assert again.record.cache_hits == 3
        assert all(row.cached and row.reserved_tokens == 0 for row in again.attempts)


@pytest.mark.parametrize(
    "ceiling,value,reason",
    [
        ("requests_per_document", 1, "requests_exhausted"),
        ("tokens_per_document", RESERVED, "tokens_exhausted"),
    ],
)
def test_a_carried_reply_that_no_longer_fits_a_ceiling_is_cut_not_a_crash(
    make_job, tmp_path, ceiling, value, reason
):
    job = make_job(3)
    fresh(job, "s", [REPLY] * 3, ceilings=limits(requests_per_document=3))
    tight = limits(**{ceiling: value})
    resumed, calls = fresh(job, "s", [], ceilings=tight)
    assert calls == 0
    first, *cut = resumed.attempts
    assert (first.cached, first.reserved_tokens) == (False, RESERVED)
    assert len(cut) == 2
    for row in cut:
        assert (
            row.cached,
            row.input_tokens,
            row.reserved_tokens,
            row.raw_ref,
            row.raw_hash,
            row.actual_prompt_tokens,
            row.actual_completion_tokens,
            row.unreported,
            row.latency_ms,
            row.reason,
        ) == (False, COUNTED, 0, None, None, None, None, False, 0, reason)
    assert [row.status for row in resumed.classifications] == [
        "completed",
        "incomplete",
        "incomplete",
    ]
    assert resumed.record.requests == 1
    # A cut carried row is the row a never-stopped run records for a cut claim.
    whole, _ = fresh(job, "w", [REPLY], ceilings=tight)
    assert resumed.attempts == whole.attempts
    round_trips(resumed, job, tmp_path / "resumed")


@pytest.mark.parametrize(
    "stops",
    [(1,), (3,), (1, 1), (2, 1), (1, 1, 1)],
    ids=lambda stops: "stops-" + "-".join(map(str, stops)),
)
def test_a_pause_at_any_point_leaves_the_run_an_uninterrupted_run_would(
    make_job, stops
):
    """Each process dispatches ``stops[i]`` claims, then stops. The next one resumes."""
    job = make_job(4)
    whole, _ = fresh(job, "a", [measured()] * 4)
    for count in stops:
        stopped(job, "b", [measured()] * count + [KeyboardInterrupt()])
    resumed, calls = fresh(job, "b", [measured()] * 4)
    assert calls == 4 - sum(stops)
    same_run(resumed, whole, "b")


def test_a_carried_retry_and_stored_refusal_match_an_uninterrupted_run(make_job):
    """A stored refusal and the retry that follows it are each charged once."""
    job = make_job(2)

    def refusal():
        return CodingTransportError(
            "tool_call_refused",
            ModelReply(
                model=MODEL,
                text="{}",
                tool_calls=True,
                usage=Usage(prompt_tokens=9, completion_tokens=2),
                latency_ms=4,
            ),
        )

    whole, _ = fresh(job, "a", [refusal(), measured(), measured()])
    assert [row.reason for row in whole.attempts] == ["tool_call_refused", None, None]
    stopped(job, "b", [refusal(), measured(), KeyboardInterrupt()])
    resumed, calls = fresh(job, "b", [measured()])
    assert calls == 1
    assert [row.cached for row in resumed.attempts] == [False, False, False]
    same_run(resumed, whole, "b")


def test_a_second_read_of_a_carried_reply_in_one_cache_is_a_cached_duplicate(
    proposal_job, coding_policy, classifier_identity
):
    """One cache serves two runs in a process. Only the first read of a reply that an
    earlier process wrote is charged. The second is a duplicate-key hit."""
    fresh(proposal_job, "s-1", [measured()])
    claims = proposal_job.sources.stored_run.claims
    cache = CodingCache(
        proposal_job.root / "classifier-cache", "fresh", stability_run_id="s-1"
    )

    def run_again():
        classifier = ScriptedClassifier(
            forbidden_replay_callback, forbidden_replay_callback, classifier_identity
        )
        run = propose_run(
            "invented-coding-run",
            proposal_job.sources,
            tuple((c.doc_id, c.claim_id) for c in claims),
            classifier,
            coding_policy,
            limits(),
            cache=cache,
            started_at=datetime(2026, 10, 5, tzinfo=UTC),
            software={"fixture": "1", "lock_hash": digest("invented lock")},
        )
        assert classifier.requests == []
        return run

    carried, duplicate = run_again(), run_again()
    (carried_row,) = carried.attempts
    (duplicate_row,) = duplicate.attempts
    assert (carried_row.cached, carried_row.reserved_tokens) == (False, RESERVED)
    assert (carried.record.requests, carried.record.cache_hits) == (1, 0)
    assert (duplicate_row.cached, duplicate_row.reserved_tokens) == (True, 0)
    assert (duplicate.record.requests, duplicate.record.cache_hits) == (0, 1)
    assert duplicate_row.raw_ref == carried_row.raw_ref


def test_a_carried_reply_whose_stored_count_cannot_fit_the_model_is_not_charged(
    proposal_job, coding_request, classifier_identity, tmp_path
):
    """A dispatch checks the model's limits before it reserves. A carried reply is
    checked the same way, so no row holds a reservation the store refuses."""
    CodingCache(
        proposal_job.root / "classifier-cache", "fresh", stability_run_id="s-1"
    ).put(
        coding_request,
        classifier_identity,
        ModelReply(model=MODEL, text=json.dumps(REPLY)),
        input_tokens=classifier_identity.input_limit,
    )
    run, calls = fresh(proposal_job, "s-1", [])
    assert calls == 0
    (row,) = run.attempts
    assert (
        row.cached,
        row.input_tokens,
        row.reserved_tokens,
        row.raw_ref,
        row.raw_hash,
        row.latency_ms,
        row.reason,
    ) == (False, classifier_identity.input_limit, 0, None, None, 0, "input_too_long")
    assert run.record.requests == 0
    round_trips(run, proposal_job, tmp_path / "resumed")
