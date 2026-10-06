"""Immutable coding publication over invented, round-tripped Stage 8 evidence."""

import json
from dataclasses import replace

import polars as pl
import pytest
from earnings_core import digest, sha256_hex
from earnings_themes.coding.decide import proposal_run_hash
from earnings_themes.coding.records import CodingError, PolicyVote, ProposalRunRecord
from earnings_themes.coding.run import ProposalRun
from earnings_themes.coding.store import (
    SCHEMAS,
    read_coding_run,
    reverify_coding_run,
    write_coding_run,
)

from .cases import FixturePolicy, make_assessed_case, make_coding_run, make_proposal_job


def original_proposals(result):
    material = {
        name: getattr(result.record, name) for name in ProposalRunRecord.model_fields
    }
    material["artifact_hashes"] = tuple(
        pair for pair in material["artifact_hashes"] if pair[0].startswith("raw/")
    )
    return ProposalRun(
        ProposalRunRecord(**material),
        result.classifications,
        result.attempts,
        result.proposals,
        result.attributes,
        result.novelty,
    )


def replace_manifest(path, mutation):
    manifest = json.loads((path / "run.json").read_bytes())
    mutation(manifest)
    (path / "run.json").write_text(json.dumps(manifest), encoding="utf-8")


def rewrite_table(path, name, mutation):
    target = path / f"{name}.parquet"
    frame = pl.read_parquet(target)
    rows = frame.to_dicts()
    mutation(rows)
    pl.DataFrame(rows, schema=frame.schema, orient="row").write_parquet(target)
    replace_manifest(
        path,
        lambda record: record.update(
            artifact_hashes=sorted(
                {
                    **dict(record["artifact_hashes"]),
                    target.name: sha256_hex(target.read_bytes()),
                }.items()
            )
        ),
    )


def test_round_trip_repeats_consuming_gate(tmp_path, complete_coding_case):
    result, sources, support, policy = complete_coding_case
    path = write_coding_run(tmp_path / "coding", result, sources, support, policy)
    stored = read_coding_run(path)
    assert stored.assignments == result.assignments
    assert stored.novelty == result.novelty
    assert (
        reverify_coding_run(stored, sources, support, policy).decisions
        == stored.decisions
    )
    assert not (path / "raw").exists()
    assert proposal_run_hash(original_proposals(stored)) == result.record.proposal_hash
    assert stored.record.configuration_hash == result.record.configuration_hash


def test_changed_evidence_prevents_publication(tmp_path, complete_coding_case):
    result, sources, support, policy = complete_coding_case
    bundle = sources.bundles[0]
    broken = replace(
        sources,
        bundles=(
            replace(
                bundle,
                document=bundle.document.model_copy(
                    update={"canonical_text": "Invented drift"}
                ),
            ),
        ),
    )
    with pytest.raises(CodingError):
        write_coding_run(tmp_path / "coding", result, broken, support, policy)
    assert not (tmp_path / "coding").exists()
    assert list(tmp_path.glob(".coding-*")) == []


@pytest.mark.parametrize("name", tuple(SCHEMAS))
def test_exact_schemas_and_corrupt_table_bytes(tmp_path, complete_coding_case, name):
    result, sources, support, policy = complete_coding_case
    path = write_coding_run(tmp_path / "coding", result, sources, support, policy)
    model, schema = SCHEMAS[name]
    assert isinstance(schema, pl.Schema)
    assert set(model.model_fields) == set(schema)
    assert pl.read_parquet(path / f"{name}.parquet").schema == schema
    (path / f"{name}.parquet").write_bytes(b"invented corruption")
    with pytest.raises(CodingError, match="^storage_corrupt$"):
        read_coding_run(path)


@pytest.mark.parametrize("name", tuple(SCHEMAS))
def test_wrong_schema_even_when_byte_hash_matches(tmp_path, complete_coding_case, name):
    result, sources, support, policy = complete_coding_case
    path = write_coding_run(tmp_path / "coding", result, sources, support, policy)
    target = path / f"{name}.parquet"
    pl.read_parquet(target).with_columns(
        pl.col("schema_version").cast(pl.Boolean)
    ).write_parquet(target)
    replace_manifest(
        path,
        lambda record: record.update(
            artifact_hashes=sorted(
                {
                    **dict(record["artifact_hashes"]),
                    target.name: sha256_hex(target.read_bytes()),
                }.items()
            )
        ),
    )
    with pytest.raises(CodingError, match="^storage_corrupt$"):
        read_coding_run(path)


@pytest.mark.parametrize(
    "field,value",
    [
        ("requests", 9),
        ("reserved_tokens", 1),
        ("charged_tokens", 1),
        ("prompt_tokens", 1),
        ("completion_tokens", 1),
        ("cache_hits", 1),
        ("unreported", 0),
        ("latency_ms", 3),
        ("counts_by_status", []),
        ("counts_by_decision", []),
        ("counts_by_decision_reason", []),
        ("counts_by_reason", [["no_theme_fit", 1]]),
        ("schema_version", 2),
        ("schema_version", True),
        ("started_at", "2026-10-05T00:00:00"),
        ("software", [["lock_hash", "wrong"]]),
        ("source_run_hash", "1" * 64),
        ("support_run_hash", "1" * 64),
        ("support_configuration_hash", "1" * 64),
        ("configuration_hash", "1" * 64),
        ("proposal_hash", "1" * 64),
        ("validator_version", "changed"),
        ("schema_hash", "1" * 64),
        ("cache_mode", "fresh"),
        ("policy", None),
    ],
)
def test_manifest_mutations_refuse(tmp_path, complete_coding_case, field, value):
    result, sources, support, policy = complete_coding_case
    path = write_coding_run(tmp_path / "coding", result, sources, support, policy)
    replace_manifest(path, lambda record: record.update({field: value}))
    with pytest.raises(CodingError, match="^storage_corrupt$"):
        read_coding_run(path)


@pytest.mark.parametrize(
    "name,mutation",
    [
        ("classifications", lambda rows: rows.append(rows[0])),
        ("classifications", lambda rows: rows[0].update(theme_ids=[])),
        ("classifications", lambda rows: rows[0].update(attempt_ids=[])),
        ("attempts", lambda rows: rows[0].update(raw_ref="../invented.json")),
        ("attempts", lambda rows: rows[0].update(raw_hash=None)),
        ("attempts", lambda rows: rows[0].update(attempt=2)),
        ("attempts", lambda rows: rows[0].update(input_tokens=99999)),
        ("proposals", lambda rows: rows[0]["target"].update(source_run_id="changed")),
        ("attributes", lambda rows: rows.clear()),
        ("decisions", lambda rows: rows[0].update(input_hash="1" * 64)),
        ("decisions", lambda rows: rows[0].update(supporting_quote_ids=["foreign"])),
        ("assignments", lambda rows: rows.append(rows[0])),
        ("assignments", lambda rows: rows[0].update(quote_id="foreign")),
        ("assignments", lambda rows: rows[0].update(canonical_hash="1" * 64)),
        ("assignment_claims", lambda rows: rows.append(rows[0])),
        ("assignment_claims", lambda rows: rows[0].update(claim_id="foreign")),
        ("assignment_claims", lambda rows: rows[0].update(target_id="foreign")),
    ],
    ids=[f"row-corruption-{i}" for i in range(17)],
)
def test_rehashed_row_corruption_refuses(
    tmp_path, complete_coding_case, name, mutation
):
    result, sources, support, policy = complete_coding_case
    path = write_coding_run(tmp_path / "coding", result, sources, support, policy)
    rewrite_table(path, name, mutation)
    with pytest.raises(CodingError, match="^storage_corrupt$"):
        read_coding_run(path)


@pytest.mark.parametrize("field,value", [("start", 1), ("mask_ids", ["invented-mask"])])
def test_consumption_catches_structurally_valid_evidence_corruption(
    tmp_path, complete_coding_case, field, value
):
    result, sources, support, policy = complete_coding_case
    path = write_coding_run(tmp_path / "coding", result, sources, support, policy)
    rewrite_table(path, "assignments", lambda rows: rows[0].update({field: value}))
    stored = read_coding_run(path)
    with pytest.raises(CodingError):
        reverify_coding_run(stored, sources, support, policy)


def test_consumer_recomputes_actual_policy_not_saved_status(complete_coding_case):
    result, sources, support, policy = complete_coding_case

    class RejectingPolicy:
        reference = policy.reference

        def evaluate(self, view):
            return PolicyVote(action="reject")

    for changed in (None, RejectingPolicy()):
        with pytest.raises(CodingError):
            reverify_coding_run(result, sources, support, changed)
    changed = FixturePolicy(original_proposals(result), support)
    changed.reference = changed.reference.model_copy(
        update={"policy_hash": digest("changed")}
    )
    with pytest.raises(CodingError, match="^policy_mismatch$"):
        reverify_coding_run(result, sources, support, changed)


def test_external_support_identity_is_checked_at_consumption(
    tmp_path, complete_coding_case
):
    result, sources, support, policy = complete_coding_case
    path = write_coding_run(tmp_path / "coding", result, sources, support, policy)
    replace_manifest(path, lambda record: record.update(support_run_id="changed"))
    stored = read_coding_run(path)
    with pytest.raises(CodingError, match="^input_changed$"):
        reverify_coding_run(stored, sources, support, policy)


def test_policy_callback_cannot_drift_unmatched_claim(
    proposal_job, coding_policy, classifier_identity, template, tmp_path
):
    from .cases import invented_bundle, make_sources

    sources = make_sources(
        proposal_job.sources.codebook,
        invented_bundle(),
        template,
        claim_texts=("An invented fitting claim.", "An invented unmatched claim."),
    )
    job = make_proposal_job(
        sources, coding_policy, classifier_identity, tmp_path / "mixed"
    )
    proposals, _ = job.run(
        [
            {"theme_ids": ["capacity"], "attributes": {}},
            {"theme_ids": [], "attributes": {}},
        ]
    )
    case = make_assessed_case(proposals, sources, tmp_path / "assembled")
    policy = FixturePolicy(proposals, case.support)
    result = make_coding_run(case, policy)

    class DriftingPolicy:
        reference = policy.reference

        def evaluate(self, view):
            object.__setattr__(
                sources.stored_run.claims[1],
                "claim",
                "Invented changed unmatched claim.",
            )
            return policy.evaluate(view)

    with pytest.raises(CodingError, match="^input_changed$"):
        reverify_coding_run(result, sources, case.support, DriftingPolicy())


def test_model_copy_bypass_cannot_publish(tmp_path, complete_coding_case):
    result, sources, support, policy = complete_coding_case
    bad = replace(
        result, attempts=(result.attempts[0].model_copy(update={"attempt": True}),)
    )
    with pytest.raises(CodingError, match="^storage_corrupt$"):
        write_coding_run(tmp_path / "coding", bad, sources, support, policy)
    assert not (tmp_path / "coding").exists()


@pytest.mark.parametrize("kind", ["container", "record", "rows"])
def test_consuming_boundary_has_fixed_closed_errors(complete_coding_case, kind):
    result, sources, support, policy = complete_coding_case
    malformed = {
        "container": object(),
        "record": replace(
            result, record=result.record.model_copy(update={"artifact_hashes": None})
        ),
        "rows": replace(result, attempts=list(result.attempts)),
    }[kind]
    with pytest.raises(CodingError, match="^storage_corrupt$"):
        reverify_coding_run(malformed, sources, support, policy)


def test_reader_checks_bindings_without_opening_absent_raw_cache(
    tmp_path, complete_coding_case, monkeypatch
):
    from pathlib import Path

    result, sources, support, policy = complete_coding_case
    path = write_coding_run(tmp_path / "coding", result, sources, support, policy)
    original = Path.read_bytes
    opened = []

    def published_only(target):
        assert target.parent == path
        opened.append(target.name)
        return original(target)

    monkeypatch.setattr(Path, "read_bytes", published_only)
    stored = read_coding_run(path)
    assert set(opened) == {"run.json", *(f"{name}.parquet" for name in SCHEMAS)}
    assert proposal_run_hash(original_proposals(stored)) == result.record.proposal_hash


def test_extra_or_missing_raw_bindings_refuse(tmp_path, complete_coding_case):
    result, sources, support, policy = complete_coding_case
    for name, hashes in (
        ("missing", ()),
        (
            "extra",
            (*result.record.artifact_hashes, (f"raw/{'0' * 64}.json", digest("extra"))),
        ),
    ):
        changed = replace(
            result,
            record=result.record.model_copy(
                update={"artifact_hashes": tuple(sorted(hashes))}
            ),
        )
        with pytest.raises(CodingError, match="^storage_corrupt$"):
            write_coding_run(tmp_path / name, changed, sources, support, policy)
        assert not (tmp_path / name).exists()


def rebind_proposal_hash(result):
    return replace(
        result,
        record=result.record.model_copy(
            update={
                "proposal_hash": proposal_run_hash(original_proposals(result)),
            }
        ),
    )


def test_self_consistent_wrong_refused_fingerprint_is_rejected(
    tmp_path, proposal_job, coding_policy, classifier_identity
):
    from earnings_themes.coding.classify import classification_id

    sources = replace(
        proposal_job.sources,
        stored_run=replace(
            proposal_job.sources.stored_run,
            record=proposal_job.sources.stored_run.record.model_copy(
                update={
                    "configuration_hash": digest("wrong invented source configuration"),
                }
            ),
        ),
    )
    job = make_proposal_job(
        sources, coding_policy, classifier_identity, tmp_path / "refused"
    )
    proposals, calls = job.run([])
    assert calls == 0
    case = make_assessed_case(proposals, sources, tmp_path / "assembled")
    result = make_coding_run(case, None)
    row = result.classifications[0]
    wrong_hash = digest("a fingerprint with the wrong recipe")
    altered = replace(
        result,
        classifications=(
            row.model_copy(
                update={
                    "input_hash": wrong_hash,
                    "classification_id": classification_id(
                        row.coding_run_id, row.doc_id, row.claim_id, wrong_hash
                    ),
                }
            ),
        ),
    )
    altered = rebind_proposal_hash(altered)
    with pytest.raises(CodingError, match="^storage_corrupt$"):
        write_coding_run(tmp_path / "coding", altered, sources, case.support, None)
    assert not (tmp_path / "coding").exists()


@pytest.mark.parametrize("mutation", ["novelty", "attribute", "reservation"])
def test_self_consistent_proposal_hash_does_not_waive_row_graph_or_accounting(
    tmp_path, proposal_job, mutation
):
    proposals, _ = proposal_job.run([{"theme_ids": [], "attributes": {}}])
    case = make_assessed_case(proposals, proposal_job.sources, tmp_path / "assembled")
    result = make_coding_run(case, None)
    if mutation == "novelty":
        changed = replace(result, novelty=())
    elif mutation == "attribute":
        changed = replace(result, attributes=())
    else:
        attempt = result.attempts[0]
        changed = replace(
            result,
            attempts=(
                attempt.model_copy(
                    update={"reserved_tokens": attempt.reserved_tokens + 1}
                ),
            ),
        )
        changed = replace(
            changed,
            record=changed.record.model_copy(
                update={
                    "reserved_tokens": changed.record.reserved_tokens + 1,
                    "charged_tokens": changed.record.charged_tokens + 1,
                }
            ),
        )
    changed = rebind_proposal_hash(changed)
    with pytest.raises(CodingError, match="^storage_corrupt$"):
        write_coding_run(tmp_path / "coding", changed, case.sources, case.support, None)
    assert not (tmp_path / "coding").exists()


def test_truthful_actual_usage_and_replay_do_not_rebill(
    tmp_path, proposal_job, coding_policy, classifier_identity
):
    from earnings_themes.extraction.adapters import ModelReply, Usage

    reply = ModelReply(
        text=json.dumps({"theme_ids": ["capacity"], "attributes": {}}),
        model=classifier_identity.runtime.model_id,
        usage=Usage(prompt_tokens=7, completion_tokens=80),
        latency_ms=13,
    )
    proposals, _ = proposal_job.run([reply])
    for mode in ("live", "replay"):
        if mode == "replay":
            proposals, calls = proposal_job.run([], "replay")
            assert calls == 0
        case = make_assessed_case(proposals, proposal_job.sources, tmp_path / mode)
        policy = FixturePolicy(proposals, case.support)
        result = make_coding_run(case, policy)
        path = write_coding_run(
            tmp_path / f"coding-{mode}", result, case.sources, case.support, policy
        )
        stored = read_coding_run(path)
        record = stored.record
        if mode == "live":
            assert (
                record.requests,
                record.prompt_tokens,
                record.completion_tokens,
                record.reserved_tokens,
                record.charged_tokens,
                record.latency_ms,
                record.unreported,
            ) == (1, 7, 80, 69, 87, 13, 0)
        else:
            assert (
                record.requests,
                record.prompt_tokens,
                record.completion_tokens,
                record.reserved_tokens,
                record.charged_tokens,
                record.latency_ms,
                record.unreported,
                record.cache_hits,
            ) == (0, 0, 0, 0, 0, 0, 0, 1)
            assert (
                stored.attempts[0].actual_prompt_tokens,
                stored.attempts[0].actual_completion_tokens,
            ) == (7, 80)


@pytest.mark.parametrize(
    "mode", ["default-review", "rejected", "retry", "exhausted", "budget"]
)
def test_real_outcomes_round_trip_without_promoting_processing_status(
    tmp_path, proposal_job, mode
):
    from earnings_themes.coding.records import CodingCeilings

    kwargs = {}
    replies = [{"theme_ids": ["capacity"], "attributes": {}}]
    if mode == "retry":
        replies.insert(0, "malformed invented reply")
    elif mode == "exhausted":
        replies = ["malformed invented reply", "another malformed invented reply"]
    elif mode == "budget":
        replies = []
        kwargs["ceilings"] = CodingCeilings(
            requests_per_claim=0,
            requests_per_document=0,
            requests_per_run=0,
            tokens_per_document=0,
            tokens_per_run=0,
        )
    proposals, _ = proposal_job.run(replies, **kwargs)
    case = make_assessed_case(proposals, proposal_job.sources, tmp_path / "assembled")
    fixture = FixturePolicy(proposals, case.support)

    class RejectingPolicy:
        reference = fixture.reference

        def evaluate(self, view):
            return PolicyVote(action="reject")

    policy = (
        RejectingPolicy()
        if mode == "rejected"
        else fixture
        if mode == "retry"
        else None
    )
    result = make_coding_run(case, policy)
    path = write_coding_run(
        tmp_path / "coding", result, case.sources, case.support, policy
    )
    stored = read_coding_run(path)
    assert (
        reverify_coding_run(stored, case.sources, case.support, policy).decisions
        == result.decisions
    )
    if mode == "default-review":
        assert stored.decisions[0].status == "review"
        assert stored.decisions[0].reason == "calibration_required"
        assert stored.decisions[0].policy is None
        assert not stored.assignments
    elif mode == "rejected":
        assert stored.decisions[0].status == "rejected"
        assert not stored.assignments
    elif mode == "retry":
        assert len(stored.attempts) == 2
        assert stored.assignments
    else:
        assert stored.classifications[0].status == "incomplete"
        assert not any(
            (stored.proposals, stored.attributes, stored.novelty, stored.assignments)
        )


def test_base_exception_cleanup(tmp_path, complete_coding_case, monkeypatch):
    result, sources, support, policy = complete_coding_case

    def interrupt(frame, *args, **kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(pl.DataFrame, "write_parquet", interrupt)
    with pytest.raises(KeyboardInterrupt):
        write_coding_run(tmp_path / "coding", result, sources, support, policy)
    assert not (tmp_path / "coding").exists()
    assert list(tmp_path.glob(".coding-*")) == []


def test_existing_destination_is_immutable(tmp_path, complete_coding_case):
    result, sources, support, policy = complete_coding_case
    path = write_coding_run(tmp_path / "coding", result, sources, support, policy)
    before = {p.name: p.read_bytes() for p in path.iterdir()}
    with pytest.raises(FileExistsError, match="^coding_destination_exists$"):
        write_coding_run(path, result, sources, support, policy)
    assert before == {p.name: p.read_bytes() for p in path.iterdir()}


def test_midwrite_failure_cleans_unique_sibling(
    tmp_path, complete_coding_case, monkeypatch
):
    result, sources, support, policy = complete_coding_case
    original = pl.DataFrame.write_parquet
    calls = 0

    def fail_second(frame, *args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("invented unsafe diagnostic")
        return original(frame, *args, **kwargs)

    monkeypatch.setattr(pl.DataFrame, "write_parquet", fail_second)
    with pytest.raises(CodingError, match="^storage_corrupt$"):
        write_coding_run(tmp_path / "coding", result, sources, support, policy)
    assert not (tmp_path / "coding").exists()
    assert list(tmp_path.glob(".coding-*")) == []


@pytest.mark.parametrize("name", ["run.json", *(f"{name}.parquet" for name in SCHEMAS)])
def test_reader_refuses_symlinks(tmp_path, complete_coding_case, name):
    result, sources, support, policy = complete_coding_case
    path = write_coding_run(tmp_path / "coding", result, sources, support, policy)
    target = path / name
    relocated = tmp_path / f"moved-{name}"
    target.rename(relocated)
    target.symlink_to(relocated)
    with pytest.raises(CodingError, match="^storage_corrupt$"):
        read_coding_run(path)


@pytest.mark.parametrize(
    "mode", ["empty", "novelty", "replay", "refused", "incomplete"]
)
def test_empty_novelty_replay_and_refused_round_trips(
    tmp_path, proposal_job, coding_policy, classifier_identity, mode
):
    sources = proposal_job.sources
    if mode == "refused":
        sources = replace(
            sources,
            stored_run=replace(
                sources.stored_run,
                record=sources.stored_run.record.model_copy(
                    update={
                        "configuration_hash": digest(
                            "wrong invented source configuration"
                        )
                    }
                ),
            ),
        )
        job = make_proposal_job(
            sources, coding_policy, classifier_identity, tmp_path / "refused"
        )
        proposals, calls = job.run([])
        assert calls == 0
    elif mode == "empty":
        proposals, _ = proposal_job.run([], claim_order=())
    elif mode == "incomplete":
        proposals, _ = proposal_job.run([], "replay")
    elif mode == "replay":
        proposal_job.run([{"theme_ids": ["capacity"], "attributes": {}}])
        proposals, calls = proposal_job.run([], "replay")
        assert calls == 0
    else:
        proposals, _ = proposal_job.run([{"theme_ids": [], "attributes": {}}])
    case = make_assessed_case(proposals, sources, tmp_path / "assembled")
    policy = FixturePolicy(proposals, case.support) if proposals.proposals else None
    result = make_coding_run(case, policy)
    path = write_coding_run(tmp_path / "coding", result, sources, case.support, policy)
    stored = read_coding_run(path)
    for name, (_, schema) in SCHEMAS.items():
        assert pl.read_parquet(path / f"{name}.parquet").schema == schema
    assert (
        reverify_coding_run(stored, sources, case.support, policy).decisions
        == result.decisions
    )
    if mode == "novelty":
        assert len(stored.novelty) == 1
    if mode == "refused":
        # The fingerprint remains unresolved; repaired evidence changes the boundary.
        with pytest.raises(CodingError):
            reverify_coding_run(stored, proposal_job.sources, case.support, policy)


def zero_target_case(proposal_job, tmp_path):
    sources = proposal_job.sources
    proposals, calls = proposal_job.run([], claim_order=())
    assert calls == 0
    case = make_assessed_case(proposals, sources, tmp_path / "zero-targets")
    assert case.support.targets == ()
    return case


def changed_book(book, mutation):
    from earnings_themes.codebook import CodebookStatus, codebook_hash

    if mutation == "id":
        changed = book.model_copy(update={"codebook_id": "different-invented-book"})
    elif mutation == "version":
        changed = book.model_copy(
            update={"codebook_version": book.codebook_version + 1}
        )
    elif mutation == "hash":
        return book.model_copy(update={"content_hash": digest("wrong invented hash")})
    elif mutation == "draft":
        return book.model_copy(
            update={"status": CodebookStatus.DRAFT, "approval": None}
        )
    elif mutation == "invalid-approval":
        return book.model_copy(update={"approval": None})
    elif mutation == "bool-version":
        return book.model_copy(update={"codebook_version": True})
    elif mutation == "hash-drift":
        return book.model_copy(
            update={
                "rules": book.rules.model_copy(
                    update={"multi_label": "Invented changed rule."}
                )
            }
        )
    else:
        return book.model_dump(mode="json")
    return changed.model_copy(update={"content_hash": codebook_hash(changed)})


@pytest.mark.parametrize(
    "mutation",
    [
        "id",
        "version",
        "hash",
        "draft",
        "invalid-approval",
        "bool-version",
        "hash-drift",
        "untyped",
    ],
)
def test_empty_run_strictly_binds_current_approved_book_before_publication(
    tmp_path, proposal_job, mutation
):
    case = zero_target_case(proposal_job, tmp_path)
    result = make_coding_run(case, None)
    assert result.classifications == ()
    broken = replace(
        case.sources, codebook=changed_book(case.sources.codebook, mutation)
    )
    with pytest.raises(CodingError):
        reverify_coding_run(result, broken, case.support, None)
    with pytest.raises(CodingError, match="^storage_corrupt$"):
        write_coding_run(tmp_path / "coding", result, broken, case.support, None)
    assert not (tmp_path / "coding").exists()
    assert list(tmp_path.glob(".coding-*")) == []


@pytest.mark.parametrize("when", [1, 4])
@pytest.mark.parametrize("operation", ["consume", "publish"])
def test_empty_run_final_gate_detects_book_drift_after_policy_properties(
    tmp_path, proposal_job, when, operation
):
    case = zero_target_case(proposal_job, tmp_path)
    fixture = FixturePolicy(case.proposals, case.support)
    result = make_coding_run(case, fixture)

    class DriftingPolicy:
        accesses = 0

        @property
        def reference(self):
            self.accesses += 1
            if self.accesses == when:
                object.__setattr__(
                    case.sources, "codebook", changed_book(case.sources.codebook, "id")
                )
            return fixture.reference

        def evaluate(self, view):
            pytest.fail("zero-target policy was evaluated")

    if operation == "consume":
        with pytest.raises(CodingError, match="^input_changed$"):
            reverify_coding_run(result, case.sources, case.support, DriftingPolicy())
    else:
        with pytest.raises(CodingError, match="^storage_corrupt$"):
            write_coding_run(
                tmp_path / "coding",
                result,
                case.sources,
                case.support,
                DriftingPolicy(),
            )
        assert not (tmp_path / "coding").exists()
        assert list(tmp_path.glob(".coding-*")) == []


@pytest.mark.parametrize("when", [1, 4])
def test_policy_property_exceptions_preserve_fixed_task6_reason(
    tmp_path, proposal_job, when
):
    case = zero_target_case(proposal_job, tmp_path)
    fixture = FixturePolicy(case.proposals, case.support)
    result = make_coding_run(case, fixture)

    class BrokenPolicy:
        accesses = 0

        @property
        def reference(self):
            self.accesses += 1
            if self.accesses == when:
                raise RuntimeError("invented unsafe property diagnostic")
            return fixture.reference

        def evaluate(self, view):
            pytest.fail("zero-target policy was evaluated")

    with pytest.raises(CodingError, match="^unexpected_error$"):
        reverify_coding_run(result, case.sources, case.support, BrokenPolicy())


@pytest.mark.parametrize("mutation", ["id", "draft"])
def test_all_refused_run_still_requires_current_approved_book(
    tmp_path, proposal_job, coding_policy, classifier_identity, mutation
):
    sources = replace(
        proposal_job.sources,
        stored_run=replace(
            proposal_job.sources.stored_run,
            record=proposal_job.sources.stored_run.record.model_copy(
                update={
                    "configuration_hash": digest("wrong invented source configuration"),
                }
            ),
        ),
    )
    job = make_proposal_job(
        sources, coding_policy, classifier_identity, tmp_path / "refused"
    )
    proposals, calls = job.run([])
    assert calls == 0
    assert all(row.status == "refused" for row in proposals.classifications)
    case = make_assessed_case(proposals, sources, tmp_path / "assembled")
    assert case.support.targets == ()
    result = make_coding_run(case, None)
    assert reverify_coding_run(result, sources, case.support, None).decisions == ()
    broken = replace(sources, codebook=changed_book(sources.codebook, mutation))
    with pytest.raises(CodingError, match="^input_changed$"):
        reverify_coding_run(result, broken, case.support, None)
    with pytest.raises(CodingError, match="^storage_corrupt$"):
        write_coding_run(tmp_path / "coding", result, broken, case.support, None)
    assert not (tmp_path / "coding").exists()
    assert list(tmp_path.glob(".coding-*")) == []
