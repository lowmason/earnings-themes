"""Documents and runs (the Stage 7 spec, §Units, §Ceilings, §Records; R10.1, R10.2,
ES21; T6-M4), over Stage 1's eight canonical fixtures and the synthetic document,
with scripted adapters only, and the network blocked."""

import socket
from collections import Counter
from dataclasses import replace
from datetime import UTC, datetime

import pytest
from earnings_core import (
    VALIDATOR_VERSION,
    CanonicalDocument,
    OverlayMask,
    RejectionReason,
    VerifiedSpan,
    digest,
    reverify_span,
)
from earnings_themes.anchoring import NARRATIVE, Bundle
from earnings_themes.extraction.adapters import ScriptedAdapter, Usage
from earnings_themes.extraction.extract import MAX_ATTEMPTS, Allowance
from earnings_themes.extraction.prompt import REPLY_SCHEMA
from earnings_themes.extraction.records import (
    Ceilings,
    DocumentOutcome,
    ExtractionPolicy,
    ExtractionProblem,
    RunConfiguration,
    WindowOutcome,
)
from earnings_themes.extraction.run import (
    BUNDLE_PROBLEM,
    RunResult,
    extract_document,
    extract_run,
)

POLICY = ExtractionPolicy()
WIDE = Ceilings(
    requests_per_document=1_000, requests_per_run=10_000, tokens_per_run=10**9
)
SOFTWARE = {"earnings-themes": "0.1.0"}
STARTED = datetime(2026, 10, 4, 12, tzinfo=UTC)


def run(bundles, adapter, template, ceilings: Ceilings = WIDE) -> RunResult:
    return extract_run(
        list(bundles),
        adapter,
        POLICY,
        template,
        ceilings,
        run_id="run-1",
        started_at=STARTED,
        software=SOFTWARE,
    )


def test_the_guard_blocks_and_records_every_connection(no_network) -> None:
    with pytest.raises(ConnectionRefusedError):
        socket.create_connection(("127.0.0.1", 9))
    with pytest.raises(ConnectionRefusedError):
        socket.getaddrinfo("localhost", 80)
    assert no_network == ["socket.create_connection", "socket.getaddrinfo"]


PINNED: dict = {
    "requests": 61,
    "candidates": 549,
    "claims": 537,
    "quotes": 525,
    "reasons": {
        "blank_claim": 6,
        "malformed_reply": 6,
        "tool_call_refused": 12,
        "transport_error": 6,
        "unknown_label": 6,
    },
    "windows": {WindowOutcome.COMPLETED: 31, WindowOutcome.FAILED: 6},
    "documents": {DocumentOutcome.PARTIAL: 6, DocumentOutcome.COMPLETED: 2},
}
"""The mixed run's counts. Its 37 windows are 7 of kind 0 and 6 of each other
kind, so 7 + 4 * 12 + 6 = 61 requests, of which the 6 that never arrived bring no
reply, and so 55 replies report no usage. Kinds 0 to 3 keep a quote of each of
their 525 units; kind 1's 12 corrections cite a unit already quoted, so 537 claims;
and each kind-1 window refuses two candidates, so 549 candidates."""


def test_a_mixed_scripted_run_over_the_fixtures(
    fixtures, template, mixed, no_network
) -> None:
    """Every window of the eight fixtures, with replies of six kinds. Each parsed
    candidate ends as one claim or one rejection, each window makes at most two
    attempts, and every retained quote verifies again (R6.1)."""
    bundles = list(fixtures.values())
    adapter = ScriptedAdapter(mixed(bundles, POLICY.window_budget))
    result = run(bundles, adapter, template)
    record = result.record
    assert no_network == []
    assert (record.units, record.windows, record.requests, record.cache_hits) == (
        797,
        37,
        PINNED["requests"],
        0,
    )
    assert (record.candidates, record.claims, record.quotes) == (
        PINNED["candidates"],
        PINNED["claims"],
        PINNED["quotes"],
    )
    assert record.rejections_by_reason == PINNED["reasons"]
    assert Counter(w.outcome for w in result.windows) == PINNED["windows"]
    assert Counter(d.outcome for d in result.document_records) == PINNED["documents"]
    assert max(w.attempts for w in result.windows) == MAX_ATTEMPTS
    candidate_rejections = [
        r for r in result.rejections if r.candidate_index is not None
    ]
    assert record.candidates == record.claims + len(candidate_rejections)
    by_doc = {bundle.document.doc_id: bundle for bundle in bundles}
    for quote in result.quotes:
        bundle = by_doc[quote.span.doc_id]
        again = reverify_span(bundle.document, bundle.elements, quote.span)
        assert isinstance(again, VerifiedSpan)
        assert again == quote.span
    quote_ids = {(q.span.doc_id, q.quote_id) for q in result.quotes}
    assert all(
        (claim.doc_id, quote_id) in quote_ids
        for claim in result.claims
        for quote_id in claim.quote_ids
    )
    assert (record.exactness_rate, record.unreported) == (1.0, 55)


def test_citing_every_label_keeps_every_unit(
    fixtures, template, cite, no_network
) -> None:
    """R10.1, R10.2: every unit of the eight fixtures is visited, once, and each
    verifies as a quote of its own."""
    bundles = list(fixtures.values())
    adapter = ScriptedAdapter(lambda request: cite(request, model="scripted"))
    result = run(bundles, adapter, template)
    record = result.record
    assert no_network == []
    assert (record.quotes, record.claims, record.rejections_by_reason) == (
        797,
        797,
        {},
    )
    assert (record.requests, len(adapter.requests)) == (37, 37)
    assert Counter(v.outcome for v in result.visits) == {WindowOutcome.COMPLETED: 797}
    assert len({(v.doc_id, v.element_id) for v in result.visits}) == 797
    assert {d.outcome for d in result.document_records} == {DocumentOutcome.COMPLETED}


def foreign_mask(bundle: Bundle) -> Bundle:
    """``bundle`` with its one mask moved to another document (T6-M4)."""
    other = CanonicalDocument.create(
        source_document_id="0009990002-25-000001_ex991.htm",
        canonicalization_version="walker-1",
        canonical_text="Invented text.\n",
    )
    (mask,) = bundle.masks
    fields = {name: getattr(mask, name) for name in OverlayMask.model_fields}
    fields |= {"doc_id": other.doc_id, "canonical_hash": other.canonical_hash}
    return replace(bundle, masks=(OverlayMask(**fields),))


def test_a_document_bundle_problems_refuses_fails_and_calls_nothing(
    synthetic, template
) -> None:
    """T6-M4: Stage 7 is ``bundle_problems``' first production caller."""
    adapter = ScriptedAdapter(lambda _: pytest.fail("a refused document was sent"))
    allowance = Allowance(requests=8, tokens=10_000)
    result = extract_document(
        foreign_mask(synthetic.bundle), adapter, POLICY, template, allowance
    )
    (refused,) = result.rejections
    assert refused.rejection is not None
    assert (refused.rejection.reason, refused.rejection.detail, refused.window_id) == (
        RejectionReason.WRONG_DOCUMENT,
        BUNDLE_PROBLEM,
        None,
    )
    assert str(refused) == f"{synthetic.bundle.document.doc_id}: wrong_document"
    assert (result.record.outcome, result.record.units, result.windows) == (
        DocumentOutcome.FAILED,
        0,
        (),
    )


def test_a_document_with_no_unit_completes_with_no_window(synthetic, template) -> None:
    bundle = synthetic.bundle
    bare = replace(
        bundle, elements=tuple(e for e in bundle.elements if e.type not in NARRATIVE)
    )
    adapter = ScriptedAdapter(lambda _: pytest.fail("a document with no unit sent"))
    result = run([bare], adapter, template)
    (document,) = result.document_records
    assert (document.outcome, document.units, document.windows) == (
        DocumentOutcome.COMPLETED,
        0,
        0,
    )
    assert (result.record.quotes, result.record.exactness_rate) == (0, None)


def test_the_ceilings_bind_across_documents(fixtures, template, cite) -> None:
    """ES21: each document may spend the lesser of its own ceiling and what the run
    has left. The first three fixtures have 9, 5, and 7 windows; with 3 requests per
    document and 5 per run, they send 3, 2, and none."""
    bundles = list(fixtures.values())[:3]
    adapter = ScriptedAdapter(lambda request: cite(request, model="scripted"))
    ceilings = Ceilings(
        requests_per_document=3, requests_per_run=5, tokens_per_run=10**9
    )
    result = run(bundles, adapter, template, ceilings)
    record = result.record
    sent = [d.requests for d in result.documents]
    assert (sent, record.requests, record.exhausted) == ([3, 2, 0], 5, True)
    assert [d.outcome for d in result.document_records] == [
        DocumentOutcome.PARTIAL,
        DocumentOutcome.PARTIAL,
        DocumentOutcome.FAILED,
    ]
    assert record.rejections_by_reason == {"budget_exhausted": 6 + 3 + 7}
    assert {w.reason for w in result.windows if w.outcome is WindowOutcome.FAILED} == {
        ExtractionProblem.BUDGET_EXHAUSTED
    }


def test_only_reported_tokens_bind_the_token_ceiling(fixtures, template, cite) -> None:
    """A reply that reports no usage binds only the request ceilings (ES21). One that
    does is counted, and the dispatch after the ceiling is reached is blocked: the
    reply that crosses it is kept."""
    (bundle, *_) = fixtures.values()
    usage = Usage(prompt_tokens=30, completion_tokens=10)
    reported = ScriptedAdapter(
        lambda request: cite(request, model="scripted", usage=usage)
    )
    unreported = ScriptedAdapter(lambda request: cite(request, model="scripted"))
    ceilings = Ceilings(
        requests_per_document=1_000, requests_per_run=10_000, tokens_per_run=100
    )
    counted = run([bundle], reported, template, ceilings).record
    uncounted = run([bundle], unreported, template, ceilings).record
    assert (counted.requests, counted.prompt_tokens, counted.exhausted) == (
        3,
        90,
        True,
    )
    assert (uncounted.requests, uncounted.unreported, uncounted.exhausted) == (
        9,
        9,
        False,
    )


def test_a_run_holds_each_document_once(synthetic, template) -> None:
    adapter = ScriptedAdapter(lambda _: pytest.fail("a duplicate run was sent"))
    with pytest.raises(ValueError, match="each document once"):
        run([synthetic.bundle, synthetic.bundle], adapter, template)


def test_the_run_record_names_its_configuration(synthetic, template, cite) -> None:
    adapter = ScriptedAdapter(lambda request: cite(request, model="scripted"))
    record = run([synthetic.bundle], adapter, template).record
    configuration = RunConfiguration(
        identity=adapter.identity,
        policy=POLICY,
        ceilings=WIDE,
        prompt_sha256=template.sha256,
        reply_schema_sha256=digest(REPLY_SCHEMA),
        extractor_version="pointer-traversal/1",
        validator_version=VALIDATOR_VERSION,
        codebook_hash=None,
    )
    document = synthetic.bundle.document
    assert (record.configuration, record.configuration_hash) == (
        configuration,
        digest(configuration),
    )
    assert (record.documents, record.software, record.started_at) == (
        {document.doc_id: document.canonical_hash},
        SOFTWARE,
        STARTED,
    )
    assert (record.billable_cost, record.exactness_rate) == ("none, self-hosted", 1.0)
