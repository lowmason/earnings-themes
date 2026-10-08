"""Ordered fake proposal runs; no support inference or source discovery."""

import importlib
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone

import pytest
from earnings_core import digest
from earnings_themes.coding.adapters import ScriptedClassifier
from earnings_themes.coding.cache import CodingCache
from earnings_themes.coding.records import CodingCeilings, CodingError
from earnings_themes.coding.run import propose_run, refused_input_hash
from earnings_themes.extraction.adapters import ModelReply, Usage

from .cases import make_proposal_job

EMPTY = '{"theme_ids":[],"attributes":{}}'


def run_with(
    sources, policy, classifier, cache, *, order=None, ceilings=None, **metadata
):
    return propose_run(
        metadata.pop("run_id", "invented-coding-run"),
        sources,
        tuple((c.doc_id, c.claim_id) for c in sources.stored_run.claims)
        if order is None
        else order,
        classifier,
        policy,
        ceilings
        or CodingCeilings(
            requests_per_claim=2,
            requests_per_document=20,
            requests_per_run=40,
            tokens_per_document=100000,
            tokens_per_run=200000,
        ),
        cache=cache,
        started_at=metadata.pop("started_at", datetime(2026, 10, 5, tzinfo=UTC)),
        software=metadata.pop("software", {"lock_hash": digest("invented lock")}),
        **metadata,
    )


def test_unmatched_is_final_not_retried(proposal_job):
    run, calls = proposal_job.run(['{"theme_ids":[],"attributes":{}}'])
    assert calls == 1
    assert len(run.novelty) == 1
    assert run.targets == ()
    assert run.classifications[0].status == "completed"


def test_one_invalid_retry_then_typed_multilabel(proposal_job):
    run, calls = proposal_job.run(
        [
            '{"theme_ids":["made_up"],"attributes":{}}',
            '{"theme_ids":["capacity","demand"],"attributes":{}}',
        ]
    )
    assert calls == 2
    assert len(run.targets) == 2
    assert [a.reason for a in run.attempts] == ["invalid_references", None]
    assert run.novelty == ()


def test_exhausted_classification_never_becomes_unmatched(proposal_job):
    run, calls = proposal_job.run(["{", "{"])
    assert calls == 2
    assert run.classifications[0].status == "incomplete"
    assert run.targets == run.novelty == ()


def test_replay_uses_no_dispatch_or_tokenizer(proposal_job):
    first, calls = proposal_job.run(['{"theme_ids":["capacity"],"attributes":{}}'])
    replay, replay_calls = proposal_job.run([], "replay")
    assert (calls, replay_calls) == (1, 0)
    assert replay.proposals == first.proposals
    assert replay.attributes == first.attributes
    assert replay.novelty == first.novelty
    assert replay.record.requests == replay.record.charged_tokens == 0
    assert replay.record.cache_hits == 1


def test_hash_only_policy_and_full_source_bindings(proposal_job, coding_policy):
    run, _ = proposal_job.run([EMPTY])
    record = run.record
    assert "prompt_text" not in type(record.coding_policy).model_fields
    assert record.coding_policy.prompt_hash == coding_policy.prompt_hash
    assert record.documents == tuple(
        sorted(proposal_job.sources.stored_run.record.documents.items())
    )
    assert record.source_run_id == proposal_job.sources.stored_run.record.run_id
    assert record.requested_claim_order == tuple(
        (row.doc_id, row.claim_id) for row in run.classifications
    )
    assert record.charged_tokens == record.reserved_tokens == 69
    assert record.unreported == record.requests == 1


@pytest.mark.parametrize(
    "metadata",
    [
        {"run_id": " "},
        {"started_at": datetime(2026, 10, 5, tzinfo=UTC).replace(tzinfo=None)},
        {"started_at": datetime(2026, 10, 5, tzinfo=timezone(timedelta(hours=1)))},
        {"software": {}},
        {"software": {"lock_hash": "z" * 64}},
        {"software": {"lock_hash": digest("invented lock"), "fixture": True}},
    ],
)
def test_invalid_run_metadata_preflight_calls_nothing(
    coding_case, coding_policy, classifier_identity, tmp_path, metadata
):
    classifier = ScriptedClassifier(
        lambda request: ModelReply(
            text=EMPTY, model=classifier_identity.runtime.model_id
        ),
        lambda request: 5,
        classifier_identity,
    )
    with pytest.raises(CodingError):
        run_with(
            coding_case,
            coding_policy,
            classifier,
            CodingCache(tmp_path, "live"),
            **metadata,
        )
    assert classifier.requests == []


def test_refused_claims_preserve_order_and_use_separate_fingerprint(
    coding_case, coding_policy, classifier_identity, tmp_path
):
    claim = coding_case.stored_run.claims[0]
    order = (
        (claim.doc_id, "unknown-first"),
        (claim.doc_id, claim.claim_id),
        (claim.doc_id, "unknown-last"),
    )
    job = make_proposal_job(coding_case, coding_policy, classifier_identity, tmp_path)
    run, calls = job.run([EMPTY], claim_order=order)
    assert calls == 1
    assert tuple((row.doc_id, row.claim_id) for row in run.classifications) == order
    assert tuple(row.status for row in run.classifications) == (
        "refused",
        "completed",
        "refused",
    )
    refused = run.classifications[0]
    assert refused.input_hash == refused_input_hash(
        run.record.source_run_hash,
        refused.doc_id,
        refused.claim_id,
        run.record.codebook,
    )
    assert refused.input_hash != run.classifications[1].input_hash
    assert refused.attempt_ids == refused.theme_ids == ()
    assert len(run.novelty) == len(run.attributes) == 1


def test_two_claims_keep_requested_order_and_share_request_ceiling(
    coding_case, coding_policy, classifier_identity, tmp_path
):
    claim = coding_case.stored_run.claims[0]
    sources, other = importlib.import_module(
        "packages.earnings-themes.tests.support.cases"
    ).append_fixture_claim(coding_case)
    order = ((other.doc_id, other.claim_id), (claim.doc_id, claim.claim_id))
    limits = CodingCeilings(
        requests_per_claim=2,
        requests_per_document=1,
        requests_per_run=20,
        tokens_per_document=10000,
        tokens_per_run=10000,
    )
    run, calls = make_proposal_job(
        sources, coding_policy, classifier_identity, tmp_path
    ).run([EMPTY], ceilings=limits, claim_order=order)
    assert calls == 1
    assert tuple(row.claim_id for row in run.classifications) == (
        other.claim_id,
        claim.claim_id,
    )
    assert tuple(row.status for row in run.classifications) == (
        "completed",
        "incomplete",
    )
    assert run.classifications[1].reason == "requests_exhausted"
    assert len(run.novelty) == 1


def test_all_claims_are_resolved_before_any_dispatch(
    coding_case, coding_policy, classifier_identity, tmp_path
):
    sources, other = importlib.import_module(
        "packages.earnings-themes.tests.support.cases"
    ).append_fixture_claim(coding_case)

    def mutate(request):
        object.__setattr__(other, "claim", "An altered invented later claim.")
        return ModelReply(text=EMPTY, model=classifier_identity.runtime.model_id)

    classifier = ScriptedClassifier(mutate, lambda request: 5, classifier_identity)
    with pytest.raises(CodingError, match="^input_changed$"):
        run_with(sources, coding_policy, classifier, CodingCache(tmp_path, "live"))
    assert len(classifier.requests) == 1


def test_valid_empty_order_has_no_dispatch(
    coding_case, coding_policy, classifier_identity, tmp_path
):
    def forbidden(request):
        raise AssertionError("fixture_callback_forbidden")

    classifier = ScriptedClassifier(forbidden, forbidden, classifier_identity)
    run = run_with(
        coding_case,
        coding_policy,
        classifier,
        CodingCache(tmp_path, "replay"),
        order=(),
    )
    assert run.classifications == run.targets == run.novelty == ()
    assert (
        run.record.requests == run.record.cache_hits == run.record.charged_tokens == 0
    )


def test_duplicate_order_aborts_before_calls(
    coding_case, coding_policy, classifier_identity, tmp_path
):
    claim = coding_case.stored_run.claims[0]
    classifier = ScriptedClassifier(
        lambda request: ModelReply(text=EMPTY), lambda request: 5, classifier_identity
    )
    with pytest.raises(CodingError):
        run_with(
            coding_case,
            coding_policy,
            classifier,
            CodingCache(tmp_path, "live"),
            order=((claim.doc_id, claim.claim_id),) * 2,
        )
    assert classifier.requests == []


def test_raw_cache_change_at_publication_aborts(
    coding_case, coding_policy, classifier_identity, tmp_path, monkeypatch
):
    import json

    from earnings_themes.coding.cache import raw_reply_hash

    cache = CodingCache(tmp_path, "live")
    original = cache.artifact_hash

    def rewrite(reference):
        path = tmp_path / reference
        data = json.loads(path.read_text())
        data["reply"]["text"] = '{"theme_ids":["demand"],"attributes":{}}'
        data["reply_hash"] = raw_reply_hash(
            ModelReply.model_validate(data["reply"]),
            data["refusal_reason"],
            data["input_tokens"],
        )
        path.write_text(json.dumps(data))
        return original(reference)

    monkeypatch.setattr(cache, "artifact_hash", rewrite)
    classifier = ScriptedClassifier(
        lambda request: ModelReply(
            text=EMPTY, model=classifier_identity.runtime.model_id
        ),
        lambda request: 5,
        classifier_identity,
    )
    with pytest.raises(CodingError, match="^cache_corrupt$"):
        run_with(coding_case, coding_policy, classifier, cache)


@pytest.mark.parametrize("audit", ["artifact_hash", "final_cache_read"])
def test_runtime_change_during_final_raw_audit_aborts_publication(
    coding_case, coding_policy, classifier_identity, tmp_path, monkeypatch, audit
):
    classifier = ScriptedClassifier(
        lambda request: ModelReply(
            text=EMPTY, model=classifier_identity.runtime.model_id
        ),
        lambda request: 5,
        classifier_identity,
    )
    cache = CodingCache(tmp_path, "live")
    original_hash = cache.artifact_hash
    original_get = cache.get
    hash_calls = mutations = 0
    auditing = False

    def change_runtime():
        nonlocal mutations
        mutations += 1
        classifier._identity = classifier.identity.model_copy(
            update={
                "runtime": classifier.identity.runtime.model_copy(
                    update={"revision": "fixture-changed-at-audit"}
                )
            }
        )

    def audit_hash(reference):
        nonlocal hash_calls, auditing
        value = original_hash(reference)
        hash_calls += 1
        auditing = True
        if audit == "artifact_hash":
            change_runtime()
        return value

    def audit_get(request, identity):
        entry = original_get(request, identity)
        if auditing and audit == "final_cache_read":
            change_runtime()
        return entry

    monkeypatch.setattr(cache, "artifact_hash", audit_hash)
    monkeypatch.setattr(cache, "get", audit_get)
    with pytest.raises(CodingError, match="^model_mismatch$"):
        run_with(coding_case, coding_policy, classifier, cache)
    assert hash_calls == mutations == len(classifier.requests) == 1


@pytest.mark.parametrize("entrypoint", ["claim", "run"])
@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("malformed_identity", "model_mismatch"),
        ("policy", "input_changed"),
        ("source", "input_changed"),
    ],
)
def test_final_identity_read_precedes_pure_binding_checks(
    coding_case,
    coding_input,
    coding_policy,
    classifier_identity,
    tmp_path,
    monkeypatch,
    entrypoint,
    mutation,
    reason,
):
    from earnings_themes.coding.classify import CodingAllowance, classify_claim

    class CallbackClassifier:
        def __init__(self):
            self.requests = []
            self.armed = self.changed = False
            self.after_audit_preflights = 0

        @property
        def identity(self):
            if self.armed:
                self.armed = False
                self.changed = True
                if mutation == "malformed_identity":
                    return classifier_identity.model_copy(update={"input_limit": True})
                if mutation == "policy":
                    object.__setattr__(
                        coding_policy.parameters,
                        "seed",
                        coding_policy.parameters.seed + 1,
                    )
                else:
                    object.__setattr__(
                        coding_case.stored_run.claims[0],
                        "claim",
                        "A changed invented claim.",
                    )
            return classifier_identity

        def preflight(self):
            self.after_audit_preflights += self.changed

        def count_tokens(self, request):
            return 5

        def complete(self, request):
            self.requests.append(request)
            return ModelReply(text=EMPTY, model=classifier_identity.runtime.model_id)

    def execute(directory, final_read=None):
        classifier = CallbackClassifier()
        cache = CodingCache(directory, "live")
        original_get = cache.get
        reads = []

        def get(request, identity):
            entry = original_get(request, identity)
            reads.append(entry is not None)
            if len(reads) == final_read:
                classifier.armed = True
            return entry

        monkeypatch.setattr(cache, "get", get)

        def invoke():
            if entrypoint == "run":
                return run_with(coding_case, coding_policy, classifier, cache)
            return classify_claim(
                coding_input,
                classifier,
                coding_policy,
                CodingAllowance(
                    CodingCeilings(
                        requests_per_claim=2,
                        requests_per_document=4,
                        requests_per_run=8,
                        tokens_per_document=100,
                        tokens_per_run=200,
                    ),
                    run_id="invented-run",
                ),
                cache=cache,
            )

        return classifier, reads, invoke

    _, baseline_reads, baseline = execute(tmp_path / "baseline")
    baseline()
    classifier, reads, changed = execute(tmp_path / "changed", len(baseline_reads))
    with pytest.raises(CodingError, match=f"^{reason}$"):
        changed()
    assert classifier.changed and reads[-1]
    assert len(classifier.requests) == 1
    assert classifier.after_audit_preflights == 0


@pytest.mark.parametrize(
    "limit,reason",
    [
        ({"requests_per_run": 1}, "requests_exhausted"),
        ({"tokens_per_document": 100}, "tokens_exhausted"),
        ({"tokens_per_run": 100}, "tokens_exhausted"),
    ],
)
def test_second_claim_crosses_shared_run_and_document_limits(
    coding_case, coding_policy, classifier_identity, tmp_path, limit, reason
):
    sources, _other = importlib.import_module(
        "packages.earnings-themes.tests.support.cases"
    ).append_fixture_claim(coding_case)
    limits = CodingCeilings(
        requests_per_claim=2,
        requests_per_document=20,
        requests_per_run=40,
        tokens_per_document=10000,
        tokens_per_run=10000,
    ).model_copy(update=limit)
    run, calls = make_proposal_job(
        sources, coding_policy, classifier_identity, tmp_path
    ).run([EMPTY], ceilings=limits)
    assert calls == 1
    assert run.classifications[1].reason == reason
    assert len(run.novelty) == 1


def test_known_actual_usage_frees_only_reported_reservation(
    proposal_job, classifier_identity
):
    replies = [
        ModelReply(
            text="{",
            model=classifier_identity.runtime.model_id,
            usage=Usage(prompt_tokens=4, completion_tokens=3),
        ),
        ModelReply(
            text=EMPTY,
            model=classifier_identity.runtime.model_id,
            usage=Usage(prompt_tokens=5, completion_tokens=3),
        ),
    ]
    limits = CodingCeilings(
        requests_per_claim=2,
        requests_per_document=2,
        requests_per_run=2,
        tokens_per_document=76,
        tokens_per_run=76,
    )
    run, calls = proposal_job.run(replies, ceilings=limits)
    assert calls == 2
    assert (
        run.record.prompt_tokens,
        run.record.completion_tokens,
        run.record.reserved_tokens,
        run.record.charged_tokens,
        run.record.unreported,
    ) == (9, 6, 138, 15, 0)


@pytest.mark.parametrize("kind", ["family", "input_limit", "prompt", "ceilings"])
def test_invalid_runtime_policy_preflight_has_zero_calls(
    coding_case, coding_policy, classifier_identity, tmp_path, kind
):
    class Classifier:
        identity = classifier_identity

        def __init__(self):
            self.calls = []

        def count_tokens(self, request):
            self.calls.append("count")
            return 5

        def complete(self, request):
            self.calls.append("complete")
            return ModelReply(text=EMPTY)

    classifier = Classifier()
    policy = coding_policy
    limits = None
    if kind == "family":
        classifier.identity = classifier_identity.model_copy(update={"family": " "})
    elif kind == "input_limit":
        classifier.identity = classifier_identity.model_copy(
            update={"input_limit": True}
        )
    elif kind == "prompt":
        policy = coding_policy.model_copy(
            update={"prompt_hash": digest("wrong invented prompt")}
        )
    else:
        limits = CodingCeilings.model_construct(
            requests_per_claim=True,
            requests_per_document=2,
            requests_per_run=2,
            tokens_per_document=100,
            tokens_per_run=100,
        )
    with pytest.raises(CodingError):
        run_with(
            coding_case,
            policy,
            classifier,
            CodingCache(tmp_path, "live"),
            ceilings=limits,
        )
    assert classifier.calls == []


def test_wrong_source_configuration_is_visible_refusal(
    proposal_job, coding_case, coding_policy, classifier_identity, tmp_path
):
    damaged = replace(
        coding_case,
        stored_run=replace(
            coding_case.stored_run,
            record=coding_case.stored_run.record.model_copy(
                update={
                    "configuration_hash": digest("wrong invented source configuration")
                }
            ),
        ),
    )
    run, calls = make_proposal_job(
        damaged, coding_policy, classifier_identity, tmp_path
    ).run([])
    assert calls == 0
    assert run.classifications[0].status == "refused"
    assert run.classifications[0].reason == "wrong_source_run"
    assert run.targets == run.attributes == run.novelty == ()


def test_two_documents_with_same_local_quote_id_remain_distinct(
    codebook, template, coding_policy, classifier_identity, tmp_path
):
    from .cases import invented_bundle, invented_codebook, make_sources

    first = invented_bundle("invented-first-document")
    second = invented_bundle("invented-second-document")
    sources = make_sources(
        invented_codebook(codebook), first, template, other_bundles=(second,)
    )
    assert (
        sources.stored_run.quotes[0].quote_id == sources.stored_run.quotes[1].quote_id
    )
    assert (
        sources.stored_run.quotes[0].span.doc_id
        != sources.stored_run.quotes[1].span.doc_id
    )
    answer = '{"theme_ids":["capacity","demand"],"attributes":{}}'
    run, calls = make_proposal_job(
        sources, coding_policy, classifier_identity, tmp_path
    ).run([answer, answer])
    assert calls == 2
    assert len(run.targets) == 4
    assert len({row.classification_id for row in run.classifications}) == 2
    assert {target.doc_id for target in run.targets} == {
        first.document.doc_id,
        second.document.doc_id,
    }


def test_malformed_evidence_container_is_a_visible_source_refusal(
    coding_case, coding_policy, classifier_identity, tmp_path
):
    sources = replace(
        coding_case,
        stored_run=replace(
            coding_case.stored_run, quotes=list(coding_case.stored_run.quotes)
        ),
    )
    run, calls = make_proposal_job(
        sources, coding_policy, classifier_identity, tmp_path
    ).run([])
    assert calls == 0
    assert run.classifications[0].status == "refused"
    assert run.classifications[0].reason == "malformed_record"
    assert run.targets == run.novelty == ()


def test_refused_source_repair_during_later_callback_aborts_publication(
    codebook, template, coding_policy, classifier_identity, tmp_path
):
    from .cases import invented_bundle, invented_codebook, make_sources

    first = invented_bundle("invented-refused-first")
    second = invented_bundle("invented-valid-second")
    sources = make_sources(
        invented_codebook(codebook), first, template, other_bundles=(second,)
    )
    quotes = sources.stored_run.quotes
    damaged = quotes[0].model_copy(
        update={"span": quotes[0].span.model_copy(update={"start": 1})}
    )
    sources = replace(
        sources, stored_run=replace(sources.stored_run, quotes=(damaged, quotes[1]))
    )

    def repair(request):
        object.__setattr__(damaged.span, "start", 0)
        return ModelReply(text=EMPTY, model=classifier_identity.runtime.model_id)

    classifier = ScriptedClassifier(repair, lambda request: 5, classifier_identity)
    with pytest.raises(CodingError, match="^input_changed$"):
        run_with(sources, coding_policy, classifier, CodingCache(tmp_path, "live"))
    assert len(classifier.requests) == 1


def test_cache_mode_is_recorded_and_binds_configuration(proposal_job):
    live, _ = proposal_job.run([EMPTY])
    replay, calls = proposal_job.run([], "replay")
    assert (live.record.cache_mode, replay.record.cache_mode, calls) == (
        "live",
        "replay",
        0,
    )
    assert live.record.configuration_hash != replay.record.configuration_hash
    assert live.proposals == replay.proposals


def test_configuration_hash_reconstructs_from_manifest_fields(proposal_job):
    run, _ = proposal_job.run([EMPTY])
    record = run.record
    configuration = {
        "source_run_id": record.source_run_id,
        "source_run_hash": record.source_run_hash,
        "documents": record.documents,
        "codebook": record.codebook.model_dump(mode="json"),
        "classifier_identity": record.classifier_identity.model_dump(mode="json"),
        "coding_policy": record.coding_policy.model_dump(mode="json"),
        "ceilings": record.ceilings.model_dump(mode="json"),
        "requested_claim_order": record.requested_claim_order,
        "schema_hash": record.schema_hash,
        "coding_version": record.coding_version,
        "validator_version": record.validator_version,
        "cache_mode": record.cache_mode,
    }
    assert digest(configuration) == record.configuration_hash


def test_invalid_cache_mode_preflight_calls_nothing(
    coding_case, coding_policy, classifier_identity, tmp_path
):
    classifier = ScriptedClassifier(
        lambda request: ModelReply(
            text=EMPTY, model=classifier_identity.runtime.model_id
        ),
        lambda request: 5,
        classifier_identity,
    )
    cache = CodingCache(tmp_path, "live")
    cache.mode = "fresh"
    with pytest.raises(CodingError, match="^malformed_record$"):
        run_with(coding_case, coding_policy, classifier, cache)
    assert classifier.requests == []


def test_cache_mode_mutation_aborts_publication(
    coding_case, coding_policy, classifier_identity, tmp_path
):
    cache = CodingCache(tmp_path, "live")

    def change_mode(request):
        cache.mode = "replay"
        return ModelReply(text=EMPTY, model=classifier_identity.runtime.model_id)

    classifier = ScriptedClassifier(change_mode, lambda request: 5, classifier_identity)
    with pytest.raises(CodingError, match="^input_changed$"):
        run_with(coding_case, coding_policy, classifier, cache)
    assert len(classifier.requests) == 1


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("identity", "model_mismatch"),
        ("policy", "input_changed"),
        ("source", "input_changed"),
        ("request", "cache_corrupt"),
    ],
)
def test_final_publication_preflight_cannot_publish_stale_bindings(
    coding_case, coding_policy, classifier_identity, tmp_path, mutation, reason
):
    class PreflightClassifier:
        def __init__(self, trigger=None, action=None):
            self._identity = classifier_identity
            self.preflights = 0
            self.requests = []
            self.trigger = trigger
            self.action = action
            self.changed = False

        @property
        def identity(self):
            return self._identity

        def preflight(self):
            self.preflights += 1
            if self.preflights == self.trigger:
                self.changed = True
                self.action(self)

        def count_tokens(self, request):
            return 5

        def complete(self, request):
            self.requests.append(request)
            return ModelReply(text=EMPTY, model=self.identity.runtime.model_id)

    baseline = PreflightClassifier()
    run_with(
        coding_case, coding_policy, baseline, CodingCache(tmp_path / "baseline", "live")
    )
    cache_root = tmp_path / "changed"

    def change(classifier):
        if mutation == "identity":
            classifier._identity = classifier.identity.model_copy(
                update={
                    "runtime": classifier.identity.runtime.model_copy(
                        update={"revision": "fixture-changed"}
                    )
                }
            )
        elif mutation == "policy":
            object.__setattr__(
                coding_policy.parameters, "seed", coding_policy.parameters.seed + 1
            )
        elif mutation == "source":
            object.__setattr__(
                coding_case.stored_run.claims[0], "claim", "A changed invented claim."
            )
        else:
            import json

            from earnings_themes.coding.cache import coding_key

            path = (
                cache_root
                / f"{coding_key(classifier.requests[0], classifier.identity)}.json"
            )
            raw = json.loads(path.read_text())
            raw["request"]["reply_schema"]["properties"]["theme_ids"]["maxItems"] = 1
            path.write_text(json.dumps(raw))

    classifier = PreflightClassifier(baseline.preflights, change)
    with pytest.raises(CodingError, match=f"^{reason}$"):
        run_with(
            coding_case, coding_policy, classifier, CodingCache(cache_root, "live")
        )
    assert classifier.changed
    assert len(classifier.requests) == 1
