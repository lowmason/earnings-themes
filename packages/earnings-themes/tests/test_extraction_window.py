"""One window's extraction (the Stage 7 spec, §Retries, §Ceilings, §Span
verification; ES16, ES20, ES21), over the synthetic document. Its one window's
labels are U1 the heading, U2 and U3 the two sentences, U4 the paragraph that repeats
U2's text, U5 the paragraph recognized from an image, and U6 the masked one."""

import json
from collections.abc import Callable, Sequence
from pathlib import Path

import pytest
from earnings_core import VALIDATOR_VERSION, RejectionReason
from earnings_themes.extraction.adapters import (
    AdapterError,
    Message,
    ModelReply,
    ModelRequest,
    ScriptedAdapter,
    Usage,
)
from earnings_themes.extraction.cache import CachedAdapter, CacheMode
from earnings_themes.extraction.extract import (
    Allowance,
    WindowJob,
    WindowResult,
    extract_window,
)
from earnings_themes.extraction.prompt import (
    REPLY_SCHEMA,
    refused_feedback,
    render_messages,
    unusable_feedback,
)
from earnings_themes.extraction.records import (
    ExtractionPolicy,
    ExtractionProblem,
    WindowOutcome,
)
from earnings_themes.extraction.windows import plan_windows

POLICY = ExtractionPolicy()


def job(synthetic, template, requests: int = 8, tokens: int = 10_000) -> WindowJob:
    (window,) = plan_windows(synthetic.bundle, POLICY.window_budget)
    return WindowJob(synthetic.bundle, window, template, Allowance(requests, tokens))


def reply(*candidates: tuple[Sequence[str], str], **fields) -> ModelReply:
    text = json.dumps(
        {"candidates": [{"quote_labels": list(q), "claim": c} for q, c in candidates]}
    )
    return ModelReply(text=text, model="scripted", **fields)


def scripted(*answers: ModelReply | ExtractionProblem) -> ScriptedAdapter:
    """Answers each request with the next reply, or raises the next problem."""
    queue = list(answers)

    def script(_: ModelRequest) -> ModelReply:
        answer = queue.pop(0)
        if isinstance(answer, ExtractionProblem):
            raise AdapterError(answer)
        return answer

    return ScriptedAdapter(script)


def ids(synthetic, *names: str) -> tuple[str, ...]:
    by_span = {e.span: e.element_id for e in synthetic.bundle.elements}
    return tuple(by_span[synthetic.spans[name]] for name in names)


def test_a_verified_candidate_becomes_a_claim_and_its_quotes(
    synthetic, template
) -> None:
    work = job(synthetic, template)
    result = extract_window(
        work, scripted(reply((["U2", "U3"], "Sales rose."))), POLICY
    )
    window = work.window
    s1, s2 = synthetic.spans["sentence 1"], synthetic.spans["sentence 2"]
    (claim,) = result.claims
    assert (claim.claim_id, claim.attempt, claim.claim, claim.quote_ids) == (
        f"c-{window.start}-{window.end}-1-0",
        1,
        "Sales rose.",
        (f"q-{s1.start}-{s1.end}", f"q-{s2.start}-{s2.end}"),
    )
    assert [q.span.quote_text for q in result.quotes] == [
        synthetic.text("sentence 1"),
        synthetic.text("sentence 2"),
    ]
    assert {q.span.validator_version for q in result.quotes} == {VALIDATOR_VERSION}
    record = result.record
    assert (record.outcome, record.attempts, record.requests, result.rejections) == (
        WindowOutcome.COMPLETED,
        1,
        1,
        (),
    )
    assert [(v.element_id, v.outcome) for v in result.visits] == [
        (unit_id, WindowOutcome.COMPLETED) for unit_id in window.unit_ids
    ]


def test_a_candidate_stands_only_if_every_label_verifies(synthetic, template) -> None:
    """ES20: U5 is OCR text, which ``validate_span`` refuses, so the candidate that
    also cites U2 is rejected whole, with the first reason, and keeps no quote."""
    adapter = scripted(reply((["U2", "U5"], "Two units.")))
    result = extract_window(job(synthetic, template), adapter, POLICY)
    (refused,) = result.rejections
    assert (result.claims, result.quotes, len(adapter.requests)) == ((), (), 1)
    assert refused.rejection is not None
    assert (refused.rejection.reason, refused.labels, refused.element_ids) == (
        RejectionReason.OCR_DERIVED_TEXT,
        ("U2", "U5"),
        ids(synthetic, "sentence 1", "scanned"),
    )
    assert result.record.outcome is WindowOutcome.COMPLETED


def test_a_quote_records_its_masks_and_repeated_text_its_context(
    synthetic, template
) -> None:
    """A masked quote is kept, with its mask's ID (R3.4). U4's text is also U2's, so
    its quote carries the context that makes its occurrence unique; U6's is unique,
    so its quote needs none."""
    adapter = scripted(reply((["U6"], "Boilerplate."), (["U4"], "A repeat.")))
    harbor, repeat = extract_window(job(synthetic, template), adapter, POLICY).quotes
    span = synthetic.spans["harbor"]
    assert (harbor.mask_ids, repeat.mask_ids) == (
        (f"safe_harbor-{span.start}-{span.end}",),
        (),
    )
    assert (harbor.span.prefix, harbor.span.suffix) == ("", "")
    assert repeat.span.quote_text == synthetic.text("repeat")
    assert synthetic.text("sentence 1") == synthetic.text("repeat")
    assert repeat.span.prefix or repeat.span.suffix


def test_every_refused_candidate_is_a_rejection_and_the_retry_asks_again(
    synthetic, template
) -> None:
    first = reply(
        (["U9"], "Unknown."),
        (["U2", "U2"], "Repeated."),
        (["U3"], "   "),
        (["U3"], "x" * 501),
        (["U1"], "Valid."),
    )
    adapter = scripted(first, reply((["U2"], "Corrected.")))
    result = extract_window(job(synthetic, template), adapter, POLICY)
    assert [
        (r.attempt, r.candidate_index, r.labels, r.problem) for r in result.rejections
    ] == [
        (1, 0, ("U9",), ExtractionProblem.UNKNOWN_LABEL),
        (1, 1, ("U2", "U2"), ExtractionProblem.DUPLICATE_LABEL),
        (1, 2, ("U3",), ExtractionProblem.BLANK_CLAIM),
        (1, 3, ("U3",), ExtractionProblem.CLAIM_TOO_LONG),
    ]
    assert [(c.attempt, c.claim) for c in result.claims] == [
        (1, "Valid."),
        (2, "Corrected."),
    ]
    feedback = refused_feedback(
        [
            (0, ("U9",), ExtractionProblem.UNKNOWN_LABEL),
            (1, ("U2", "U2"), ExtractionProblem.DUPLICATE_LABEL),
            (2, ("U3",), ExtractionProblem.BLANK_CLAIM),
            (3, ("U3",), ExtractionProblem.CLAIM_TOO_LONG),
        ],
        units=6,
        claim_limit=500,
    )
    first_request, second_request = adapter.requests
    assert second_request.messages == (
        *first_request.messages,
        Message(role="assistant", content=first.text),
        Message(role="user", content=feedback),
    )
    assert (result.candidates, result.record.attempts) == (6, 2)


def test_a_malformed_reply_is_answered_with_its_problems_by_field(
    synthetic, template
) -> None:
    broken = ModelReply(text="not JSON", model="scripted")
    adapter = scripted(broken, reply((["U1"], "Now valid.")))
    result = extract_window(job(synthetic, template), adapter, POLICY)
    (refused,) = result.rejections
    problems = ("record: Invalid JSON: expected ident at line 1 column 2",)
    assert (refused.problem, refused.detail) == (
        ExtractionProblem.MALFORMED_REPLY,
        problems[0],
    )
    assert adapter.requests[1].messages[2:] == (
        Message(role="assistant", content="not JSON"),
        Message(role="user", content=unusable_feedback(problems)),
    )
    assert result.record.outcome is WindowOutcome.COMPLETED


def test_a_reply_that_never_arrived_is_sent_again_unchanged(
    synthetic, template
) -> None:
    adapter = scripted(ExtractionProblem.TRANSPORT_ERROR, reply((["U1"], "Valid.")))
    result = extract_window(job(synthetic, template), adapter, POLICY)
    first, second = adapter.requests
    assert first == second
    assert [(r.attempt, r.problem) for r in result.rejections] == [
        (1, ExtractionProblem.TRANSPORT_ERROR)
    ]
    assert (result.record.requests, len(result.claims)) == (2, 1)


@pytest.mark.parametrize(
    ("answers", "reason"),
    [
        (
            [ModelReply(text="", model="scripted", tool_calls=True)] * 2,
            ExtractionProblem.TOOL_CALL_REFUSED,
        ),
        (
            [ModelReply(text='{"candidates": []}', model="another-model")] * 2,
            ExtractionProblem.MODEL_MISMATCH,
        ),
        (
            [ModelReply(text='{"candidates": []}')] * 2,
            ExtractionProblem.MODEL_MISMATCH,
        ),
        (
            [ExtractionProblem.TRANSPORT_ERROR, ModelReply(text="[", model="scripted")],
            ExtractionProblem.MALFORMED_REPLY,
        ),
    ],
    ids=["tool-calls", "another-model", "no-model", "transport-then-malformed"],
)
def test_a_window_with_no_usable_reply_fails_with_its_last_problem(
    synthetic, template, answers, reason
) -> None:
    result = extract_window(job(synthetic, template), scripted(*answers), POLICY)
    record = result.record
    assert (record.outcome, record.reason, record.attempts) == (
        WindowOutcome.FAILED,
        reason,
        2,
    )
    assert {(v.outcome, v.reason) for v in result.visits} == {
        (WindowOutcome.FAILED, reason)
    }
    assert (result.claims, result.quotes) == ((), ())


def test_a_refused_reply_counts_with_its_usage(synthetic, template) -> None:
    """A reply an adapter refused, such as the local adapter's tool-call refusal, is
    a request, and its reported usage counts toward the ceilings."""
    usage = Usage(prompt_tokens=30, completion_tokens=10)
    refused = ModelReply(text="", model="scripted", tool_calls=True, usage=usage)

    def script(_: ModelRequest) -> ModelReply:
        raise AdapterError(ExtractionProblem.TOOL_CALL_REFUSED, refused)

    record = extract_window(job(synthetic, template), ScriptedAdapter(script), POLICY)
    spent = (record.record.requests, record.record.prompt_tokens, record.record.reason)
    assert spent == (2, 60, ExtractionProblem.TOOL_CALL_REFUSED)


def test_a_replay_miss_is_never_a_request(synthetic, template, tmp_path: Path) -> None:
    adapter = ScriptedAdapter(lambda _: pytest.fail("replay called the model"))
    replay = CachedAdapter(adapter, tmp_path, CacheMode.REPLAY)
    record = extract_window(job(synthetic, template), replay, POLICY).record
    assert (record.outcome, record.reason, record.attempts, record.requests) == (
        WindowOutcome.FAILED,
        ExtractionProblem.REPLAY_MISS,
        2,
        0,
    )


def test_a_cache_hit_is_not_a_request(synthetic, template, tmp_path: Path) -> None:
    usage = Usage(prompt_tokens=40, completion_tokens=10)
    live = CachedAdapter(
        scripted(reply((["U2"], "A claim."), usage=usage, latency_ms=7)),
        tmp_path,
        CacheMode.LIVE,
    )
    first = extract_window(job(synthetic, template), live, POLICY)
    replay = CachedAdapter(scripted(), tmp_path, CacheMode.REPLAY)
    second = extract_window(job(synthetic, template), replay, POLICY)
    spent = [
        (r.requests, r.cache_hits, r.prompt_tokens, r.completion_tokens, r.latency_ms)
        for r in (first.record, second.record)
    ]
    assert spent == [(1, 0, 40, 10, 7), (0, 1, 0, 0, 0)]
    assert second.claims == first.claims
    assert second.quotes == first.quotes


def test_a_reply_without_usage_is_unreported(synthetic, template) -> None:
    result = extract_window(job(synthetic, template), scripted(reply()), POLICY)
    record = result.record
    assert (record.unreported, record.prompt_tokens, record.completion_tokens) == (
        1,
        0,
        0,
    )


def counting(answer: Callable[[], ModelReply]) -> ScriptedAdapter:
    return ScriptedAdapter(lambda _: answer())


def test_no_allowance_sends_nothing_and_fails_the_window(synthetic, template) -> None:
    adapter = counting(lambda: pytest.fail("a dispatch was not checked first"))
    result = extract_window(job(synthetic, template, requests=0), adapter, POLICY)
    record = result.record
    assert (record.outcome, record.reason, record.attempts, record.exhausted) == (
        WindowOutcome.FAILED,
        ExtractionProblem.BUDGET_EXHAUSTED,
        0,
        True,
    )
    assert [(r.attempt, r.problem) for r in result.rejections] == [
        (1, ExtractionProblem.BUDGET_EXHAUSTED)
    ]


@pytest.mark.parametrize(
    ("requests", "tokens"), [(1, 10_000), (8, 50)], ids=["requests", "tokens"]
)
def test_a_ceiling_stops_the_retry(synthetic, template, requests, tokens) -> None:
    """The first reply is usable but refuses a candidate; the retry is blocked, so
    the window completes with what it kept, and records the blocked dispatch."""
    usage = Usage(prompt_tokens=40, completion_tokens=10)
    first = reply((["U9"], "Unknown."), (["U1"], "Valid."), usage=usage)
    adapter = scripted(first)
    result = extract_window(job(synthetic, template, requests, tokens), adapter, POLICY)
    record = result.record
    assert (record.outcome, record.reason, record.attempts, record.exhausted) == (
        WindowOutcome.COMPLETED,
        None,
        1,
        True,
    )
    assert [(r.attempt, r.problem) for r in result.rejections] == [
        (1, ExtractionProblem.UNKNOWN_LABEL),
        (2, ExtractionProblem.BUDGET_EXHAUSTED),
    ]


def test_the_request_names_its_window_policy_and_prompt(synthetic, template) -> None:
    work = job(synthetic, template)
    adapter = scripted(reply())
    result: WindowResult = extract_window(work, adapter, POLICY)
    (request,) = adapter.requests
    subject = request.subject
    assert (
        subject.doc_id,
        subject.canonical_hash,
        subject.window_id,
        subject.unit_ids,
        subject.window_budget,
        subject.claim_limit,
        subject.prompt_sha256,
        subject.extractor_version,
        subject.validator_version,
        subject.codebook_hash,
    ) == (
        synthetic.bundle.document.doc_id,
        synthetic.bundle.document.canonical_hash,
        work.window.window_id,
        work.window.unit_ids,
        4000,
        500,
        template.sha256,
        "pointer-traversal/1",
        VALIDATOR_VERSION,
        None,
    )
    system, user = render_messages(
        template, synthetic.bundle, work.window, structured=True
    )
    assert request.messages == (
        Message(role="system", content=system),
        Message(role="user", content=user),
    )
    assert (request.reply_schema, request.parameters) == (
        REPLY_SCHEMA,
        POLICY.parameters,
    )
    assert result.record.window_id == work.window.window_id
