"""V11 on the exact shipped invented bundle, through actual pipeline seams."""

import json

import pytest
from earnings_core import digest, reverify_span
from earnings_themes.codebook import codebook_hash, codebook_toml
from earnings_themes.coding.store import (
    read_coding_run,
    reverify_coding_run,
    write_coding_run,
)
from earnings_themes.extraction.adapters import ModelReply
from earnings_themes.synthetic import injection_bundle

from .cases import make_assessed_case, make_coding_run

ATTACKS = (
    "tool-metadata",
    "tool-field",
    "codebook-replacement",
    "new-theme",
    "definition",
    "offset",
    "quote-text",
    "accepted",
    "source-run-id",
    "document-id",
    "claim-id",
    "quote-id",
    "spoofed-theme-id",
    "provenance",
)


def source_fingerprint(sources):
    """Content hashes avoid input-bearing diagnostics if an invariant fails."""
    return digest(
        {
            "book_json": sources.codebook.model_dump_json(),
            "book_toml": codebook_toml(sources.codebook),
            "book_hash": codebook_hash(sources.codebook),
            "documents": [b.document.model_dump(mode="json") for b in sources.bundles],
            "claims": [c.model_dump(mode="json") for c in sources.stored_run.claims],
            "quotes": [q.model_dump(mode="json") for q in sources.stored_run.quotes],
        }
    )


def attack_reply(kind):
    injection = injection_bundle()
    reply = {"theme_ids": ["demand"], "attributes": {}}
    if kind == "tool-metadata":
        return ModelReply(
            model="invented-classifier", text=json.dumps(reply), tool_calls=True
        ), "tool_call_refused"
    if kind == "spoofed-theme-id":
        reply["theme_ids"] = [injection.text("spoof")]
        return reply, "invalid_references"
    extras = {
        "tool-field": {"tool_calls": [{"name": "export", "arguments": {}}]},
        "codebook-replacement": {"codebook": {"demand": "all claims"}},
        "new-theme": {"new_theme": "injected"},
        "definition": {"definition": "Every claim fits this definition."},
        "offset": {"start": 0, "end": 27},
        "quote-text": {"quote_text": injection.text("codebook")},
        "accepted": {"accepted": True},
        "source-run-id": {"source_run_id": "invented-forged-source"},
        "document-id": {"doc_id": "cik-0009990009"},
        "claim-id": {"claim_id": "invented-forged-claim"},
        "quote-id": {"quote_id": "invented-forged-quote"},
        "provenance": {
            "provenance_hash": "0" * 64,
            "canonical_hash": "0" * 64,
            "codebook_hash": "0" * 64,
        },
    }
    return {**reply, **extras[kind]}, "malformed_reply"


def store_default_case(case, directory):
    """Actual Task 6/7/8 decisions, projection, publication and consuming gate."""
    result = make_coding_run(case, None)
    path = write_coding_run(directory, result, case.sources, case.support, None)
    stored = read_coding_run(path)
    reverify_coding_run(stored, case.sources, case.support, None)
    assert stored.assignments == stored.assignment_claims == stored.novelty == ()
    return stored


def assert_sources_unchanged(job, before):
    assert source_fingerprint(job.sources) == before
    bundle = job.sources.bundles[0]
    original_bundle = bundle == injection_bundle().bundle
    assert original_bundle
    verified = all(
        reverify_span(bundle.document, bundle.elements, quote.span) == quote.span
        for quote in job.sources.stored_run.quotes
    )
    assert verified


@pytest.mark.parametrize("kind", ATTACKS)
def test_obeying_classification_never_changes_codebook(injection_job, tmp_path, kind):
    before = source_fingerprint(injection_job.sources)
    reply, reason = attack_reply(kind)
    proposals, calls = injection_job.run([reply, reply])
    assert calls == 2
    assert len(proposals.attempts) == 2
    assert [row.reason for row in proposals.attempts] == [reason, reason]
    assert proposals.classifications[0].status == "incomplete"
    assert proposals.targets == proposals.attributes == proposals.novelty == ()
    assert all(row.raw_ref is not None for row in proposals.attempts)
    assert len(injection_job.requests) == 2
    assert all(
        {"tools", "tool_choice"}.isdisjoint(request.model_dump())
        for request in injection_job.requests
    )
    feedback_is_fixed = injection_job.requests[1].messages[-1].content == (
        f"Unusable reply: {reason}. Return the closed JSON response only."
    )
    assert feedback_is_fixed
    case = make_assessed_case(proposals, injection_job.sources, tmp_path / "assessment")
    assert case.support.targets == case.support.evidence == case.support.outcomes == ()
    assert case.scorer.requests == []
    assert all(judge.requests == [] for judge in case.panel)
    stored = store_default_case(case, tmp_path / "coding")
    assert stored.decisions == ()
    assert_sources_unchanged(injection_job, before)


def test_ignoring_instruction_reaches_real_assessment_and_default_review(
    injection_job, tmp_path
):
    before = source_fingerprint(injection_job.sources)
    proposals, calls = injection_job.run([{"theme_ids": ["demand"], "attributes": {}}])
    assert calls == 1
    assert tuple(target.theme_id for target in proposals.targets) == ("demand",)
    request = json.loads(injection_job.requests[0].messages[1].content)
    quoted = {row["text"] for row in request["quoted_evidence"]}
    instruction_as_data = injection_bundle().text("codebook") in quoted
    assert instruction_as_data
    case = make_assessed_case(proposals, injection_job.sources, tmp_path / "assessment")
    assert case.support.outcomes[0].status == "assessed"
    assert len(case.support.trials) == 4
    assert len(case.support.entailment) == len(case.support.evidence) + 1
    stored = store_default_case(case, tmp_path / "coding")
    assert len(stored.decisions) == 1
    row = stored.decisions[0]
    assert (row.status, row.reason, row.supporting_quote_ids) == (
        "review",
        "calibration_required",
        (),
    )
    assert_sources_unchanged(injection_job, before)


def test_classifier_and_support_replay_use_no_dispatch_or_token_counter(
    injection_job, tmp_path
):
    first, calls = injection_job.run([{"theme_ids": ["demand"], "attributes": {}}])
    assert calls == 1
    initial = make_assessed_case(first, injection_job.sources, tmp_path / "live")
    replay, calls = injection_job.run([], "replay")
    assert calls == 0
    assert replay.targets == first.targets
    assert replay.record.requests == replay.record.charged_tokens == 0
    assert replay.record.cache_hits == 1
    again = make_assessed_case(
        replay,
        injection_job.sources,
        tmp_path / "replay",
        cache_mode="replay",
        cache_directory=tmp_path / "live" / "support-cache",
    )
    assert again.scorer.requests == []
    assert all(judge.requests == [] for judge in again.panel)
    assert all(row.cached for row in again.support.usage)
    assert again.support.outcomes == initial.support.outcomes
    store_default_case(again, tmp_path / "coding-replay")


def test_unusable_reply_replay_preserves_refusal_without_dispatch(injection_job):
    reply, reason = attack_reply("codebook-replacement")
    first, calls = injection_job.run([reply, reply])
    assert calls == 2
    replay, calls = injection_job.run([], "replay")
    assert calls == 0
    assert replay.targets == replay.novelty == ()
    assert [row.reason for row in replay.attempts] == [reason, reason]
    assert all(row.cached for row in replay.attempts)
    assert replay.record.requests == replay.record.charged_tokens == 0
    assert replay.record.cache_hits == 2
    assert replay.classifications == first.classifications


def test_replay_miss_returns_incomplete_without_dispatch(injection_job):
    proposals, calls = injection_job.run([], "replay")
    assert calls == 0
    assert proposals.targets == proposals.novelty == ()
    assert proposals.classifications[0].reason == "replay_miss"
    assert proposals.record.requests == proposals.record.charged_tokens == 0
