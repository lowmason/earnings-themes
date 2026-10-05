"""Invented immutable publication, structural loading and consuming gates."""

import json
from dataclasses import replace

import polars as pl
import pytest
from earnings_core import sha256_hex
from earnings_themes.support.problems import SupportError
from earnings_themes.support.store import (
    SCHEMAS,
    read_support_run,
    reverify_support_run,
    write_support_run,
)

from .test_prompt import policy as policy  # noqa: PLC0414
from .test_run import run


@pytest.fixture
def completed(case, scorer, panel, policy, allowance, tmp_path):
    return run(case, scorer, panel, policy, allowance.ceilings, tmp_path / "cache")


def test_round_trip_and_gate(tmp_path, completed, case):
    path = write_support_run(tmp_path / "run", completed, case[0])
    stored = read_support_run(path)
    assert stored.targets == tuple(a.target for a in completed.assessments)
    assert stored.outcomes == tuple(a.outcome for a in completed.assessments)
    for kind in SCHEMAS:
        expected = (
            tuple(r for a in completed.assessments for r in getattr(a, kind))
            if kind not in {"targets", "outcomes"}
            else getattr(stored, kind)
        )
        assert getattr(stored, kind) == expected
    assert reverify_support_run(stored, case[0]) == stored.outcomes
    assert set(dict(stored.record.artifact_hashes)) == {
        f"{kind}.parquet" for kind in SCHEMAS
    } | {f"raw/{a.raw_ref}" for a in stored.attempts}
    assert not (path / "raw").exists()


@pytest.mark.parametrize(
    "kind", ["canonical", "claim", "codebook", "masks", "record", "signal", "context"]
)
def test_publication_rechecks_before_creating_sibling(tmp_path, completed, case, kind):
    sources = case[0]
    bundle = sources.bundles[0]
    if kind == "canonical":
        sources = replace(
            sources,
            bundles=(
                replace(
                    bundle,
                    document=bundle.document.model_copy(
                        update={"canonical_text": "Changed invented text"}
                    ),
                ),
            ),
        )
    elif kind == "claim":
        claim = sources.stored_run.claims[0].model_copy(
            update={"claim": "Changed invented claim."}
        )
        sources = replace(
            sources, stored_run=replace(sources.stored_run, claims=(claim,))
        )
    elif kind == "codebook":
        sources = replace(
            sources,
            codebook=sources.codebook.model_copy(update={"content_hash": "0" * 64}),
        )
    elif kind == "masks":
        quote = sources.stored_run.quotes[0].model_copy(
            update={"mask_ids": ("changed",)}
        )
        sources = replace(
            sources,
            stored_run=replace(
                sources.stored_run, quotes=(quote, *sources.stored_run.quotes[1:])
            ),
        )
    else:
        row = completed.assessments[0]
        if kind == "record":
            row = replace(
                row, target=row.target.model_copy(update={"input_hash": "0" * 64})
            )
        elif kind == "signal":
            signal = row.entailment[0].model_copy(update={"target_id": "wrong"})
            row = replace(row, entailment=(signal, *row.entailment[1:]))
        else:
            row = replace(row, contexts=())
        completed = replace(completed, assessments=(row,))
    with pytest.raises(SupportError):
        write_support_run(tmp_path / "run", completed, sources)
    assert not (tmp_path / "run").exists()
    assert list(tmp_path.glob(".run-*")) == []


def test_existing_destination_is_never_overwritten(tmp_path, completed, case):
    path = tmp_path / "run"
    path.mkdir()
    (path / "sentinel").write_text("invented")
    with pytest.raises(FileExistsError, match="^support_destination_exists$"):
        write_support_run(path, completed, case[0])
    assert (path / "sentinel").read_text() == "invented"


@pytest.mark.parametrize(
    "step,interrupt",
    [("write", False), ("rename", False), ("write", True), ("rename", True)],
)
def test_failed_publication_is_whole_or_absent(
    tmp_path, completed, case, monkeypatch, step, interrupt
):
    from earnings_themes.support import store

    def fail(*args, **kwargs):
        raise KeyboardInterrupt if interrupt else OSError("INVENTED_PRIVATE")

    monkeypatch.setattr(
        pl.DataFrame, "write_parquet", fail
    ) if step == "write" else monkeypatch.setattr(store.os, "rename", fail)
    with pytest.raises(KeyboardInterrupt if interrupt else SupportError):
        write_support_run(tmp_path / "run", completed, case[0])
    assert not (tmp_path / "run").exists()
    assert not list(tmp_path.glob(".run-*"))


def rewrite(path, kind, mutate):
    frame = pl.read_parquet(path / f"{kind}.parquet")
    rows = frame.to_dicts()
    mutate(rows)
    pl.DataFrame(rows, schema=frame.schema).write_parquet(path / f"{kind}.parquet")
    manifest = json.loads((path / "run.json").read_bytes())
    bindings = dict(manifest["artifact_hashes"])
    bindings[f"{kind}.parquet"] = sha256_hex((path / f"{kind}.parquet").read_bytes())
    manifest["artifact_hashes"] = sorted(bindings.items())
    (path / "run.json").write_text(json.dumps(manifest))


@pytest.mark.parametrize(
    "kind",
    [
        "hash",
        "schema",
        "target",
        "duplicate",
        "evidence",
        "trial",
        "attempt",
        "identity",
        "outcome",
        "counts",
        "raw_ref",
        "raw_hash",
        "usage",
    ],
)
def test_reader_rejects_corrupt_artifacts(tmp_path, completed, case, kind):
    path = write_support_run(tmp_path / "run", completed, case[0])
    if kind == "hash":
        with (path / "targets.parquet").open("ab") as stream:
            stream.write(b"corrupt")
    elif kind == "schema":
        pl.DataFrame({"wrong": [1]}).write_parquet(path / "targets.parquet")
    elif kind in {"counts", "raw_hash"}:
        manifest = json.loads((path / "run.json").read_bytes())
        if kind == "counts":
            manifest["requests"] += 1
        else:
            manifest["artifact_hashes"] = [
                b for b in manifest["artifact_hashes"] if not b[0].startswith("raw/")
            ]
        (path / "run.json").write_text(json.dumps(manifest))
    else:
        table, field, value = {
            "target": ("targets", "source_run_hash", "0" * 64),
            "evidence": ("evidence", "quote_id", "wrong"),
            "trial": ("trials", "presentation", "claim_theme_first"),
            "attempt": ("attempts", "trial_id", "wrong"),
            "identity": ("entailment", "input_hash", "0" * 64),
            "outcome": ("outcomes", "status", "flagged"),
            "raw_ref": ("attempts", "raw_ref", "../wrong.json"),
            "usage": ("usage", "target_id", "wrong"),
            "duplicate": ("targets", None, None),
        }[kind]
        rewrite(
            path,
            table,
            lambda rows: (
                rows.append(rows[0])
                if field is None
                else rows[0].__setitem__(field, value)
            ),
        )
    with pytest.raises(SupportError, match="^storage_corrupt$"):
        read_support_run(path)


def test_consuming_gate_detects_changed_sources(tmp_path, completed, case):
    path = write_support_run(tmp_path / "run", completed, case[0])
    sources = case[0]
    claim = sources.stored_run.claims[0].model_copy(
        update={"claim": "Changed invented claim."}
    )
    sources = replace(sources, stored_run=replace(sources.stored_run, claims=(claim,)))
    with pytest.raises(SupportError):
        reverify_support_run(read_support_run(path), sources)


def test_refused_rows_and_empty_tables_round_trip(
    tmp_path, case, scorer, panel, policy, allowance
):
    sources, target = case
    sources = replace(sources, stored_run=replace(sources.stored_run, quotes=()))
    result = run(
        (sources, target), scorer, panel, policy, allowance.ceilings, tmp_path / "cache"
    )
    path = write_support_run(tmp_path / "run", result, sources)
    stored = read_support_run(path)
    assert stored.outcomes[0].status == "refused"
    assert reverify_support_run(stored, sources) == stored.outcomes
    for kind in ("evidence", "contexts", "entailment", "trials", "attempts", "usage"):
        assert pl.read_parquet(path / f"{kind}.parquet").schema == SCHEMAS[kind][1]
        assert getattr(stored, kind) == ()


def test_one_quote_joint_alias_round_trips(
    one_quote, scorer, panel, policy, allowance, tmp_path
):
    result = run(
        (one_quote.sources, one_quote.record.target),
        scorer,
        panel,
        policy,
        allowance.ceilings,
        tmp_path / "cache",
    )
    path = write_support_run(tmp_path / "run", result, one_quote.sources)
    stored = read_support_run(path)
    assert stored.record.evaluations == 1
    assert reverify_support_run(stored, one_quote.sources) == stored.outcomes


def test_empty_run_has_declared_schemas(
    case, scorer, panel, policy, allowance, tmp_path
):
    result = run(
        case, scorer, panel, policy, allowance.ceilings, tmp_path / "cache", ()
    )
    stored = read_support_run(write_support_run(tmp_path / "run", result, case[0]))
    assert stored.targets == () and stored.record.counts_by_status == ()


def test_unknown_document_refusal_remains_auditable(
    case, scorer, panel, policy, allowance, tmp_path
):
    sources, target = case
    target = target.model_copy(update={"doc_id": "invented-absent"})
    result = run(
        (sources, target), scorer, panel, policy, allowance.ceilings, tmp_path / "cache"
    )
    stored = read_support_run(write_support_run(tmp_path / "run", result, sources))
    assert stored.outcomes[0].missing == ("wrong_document",)


def test_actual_usage_overspend_remains_visible(
    case, scorer, panel, policy, allowance, tmp_path
):
    from earnings_themes.extraction.adapters import Usage

    from .cases import judge_reply

    original = judge_reply()
    panel[0].script = lambda request: original(request).model_copy(
        update={"usage": Usage(prompt_tokens=10000, completion_tokens=10)}
    )
    ceilings = allowance.ceilings.model_copy(update={"tokens_per_run": 6000})
    result = run(case, scorer, panel, policy, ceilings, tmp_path / "cache")
    assert result.record.prompt_tokens > ceilings.tokens_per_run
    stored = read_support_run(write_support_run(tmp_path / "run", result, case[0]))
    assert stored.outcomes[0].missing == ("tokens_exhausted",)


@pytest.mark.parametrize(
    "field,value",
    [("schema_hash", "0" * 64), ("prompt_hash", "0" * 64), ("reserved_tokens", 1)],
)
def test_reader_rechecks_attempt_bindings(tmp_path, completed, case, field, value):
    path = write_support_run(tmp_path / "run", completed, case[0])
    rewrite(path, "attempts", lambda rows: rows[0].__setitem__(field, value))
    with pytest.raises(SupportError, match="^storage_corrupt$"):
        read_support_run(path)


def test_reader_rechecks_usage_binding(tmp_path, completed, case):
    path = write_support_run(tmp_path / "run", completed, case[0])
    rewrite(path, "usage", lambda rows: rows[0].__setitem__("operation_id", "wrong"))
    with pytest.raises(SupportError, match="^storage_corrupt$"):
        read_support_run(path)


def test_one_quote_joint_alias_cannot_change_raw_signal(
    one_quote, scorer, panel, policy, allowance, tmp_path
):
    result = run(
        (one_quote.sources, one_quote.record.target),
        scorer,
        panel,
        policy,
        allowance.ceilings,
        tmp_path / "cache",
    )
    path = write_support_run(tmp_path / "run", result, one_quote.sources)
    rewrite(path, "entailment", lambda rows: rows[1].__setitem__("score", 0.1))
    with pytest.raises(SupportError, match="^storage_corrupt$"):
        read_support_run(path)


def test_available_answer_requires_raw_reference(tmp_path, completed, case):
    path = write_support_run(tmp_path / "run", completed, case[0])
    rewrite(path, "attempts", lambda rows: rows[0].__setitem__("raw_ref", None))
    manifest = json.loads((path / "run.json").read_bytes())
    removed = "raw/" + completed.assessments[0].attempts[0].raw_ref
    manifest["artifact_hashes"] = [
        binding for binding in manifest["artifact_hashes"] if binding[0] != removed
    ]
    (path / "run.json").write_text(json.dumps(manifest))
    with pytest.raises(SupportError, match="^storage_corrupt$"):
        read_support_run(path)


def rewrite_complete_assessment(path, assessment):
    """Tamper all dependent local tables/counts together, retaining valid schemas."""
    from earnings_core import digest
    from earnings_themes.support.run import accounting

    ordinal = 0
    usage = []
    for row in assessment.usage:
        if not row.cached:
            row = row.model_copy(
                update={
                    "operation_id": digest(
                        {
                            "ordinal": ordinal,
                            "kind": row.kind,
                            "target": row.target_id,
                            "document": row.doc_id,
                        }
                    )
                }
            )
            ordinal += 1
        usage.append(row)
    assessment = replace(assessment, usage=tuple(usage))
    manifest = json.loads((path / "run.json").read_bytes())
    hashes = dict(manifest["artifact_hashes"])
    for kind in ("entailment", "usage", "outcomes"):
        records = (
            (assessment.outcome,) if kind == "outcomes" else getattr(assessment, kind)
        )
        artifact = path / f"{kind}.parquet"
        pl.DataFrame(
            [row.model_dump(mode="json") for row in records],
            schema=SCHEMAS[kind][1],
            orient="row",
        ).write_parquet(artifact)
        hashes[artifact.name] = sha256_hex(artifact.read_bytes())
    manifest.update(accounting((assessment,), assessment.usage))
    manifest["artifact_hashes"] = sorted(hashes.items())
    (path / "run.json").write_text(json.dumps(manifest))


@pytest.mark.parametrize("kind", ["missing_joint", "missing_quote", "duplicate_quote"])
def test_reader_rejects_inconsistent_signal_slots_with_rebuilt_manifest(
    tmp_path, completed, case, kind
):
    from earnings_core import digest
    from earnings_themes.support.assess import derive_outcome

    path = write_support_run(tmp_path / "run", completed, case[0])
    assessment = completed.assessments[0]
    signals = list(assessment.entailment)
    usage = list(assessment.usage)
    if kind == "missing_joint":
        signals.pop(2)
        usage.pop(2)
    elif kind == "missing_quote":
        signals.pop(0)
        usage.pop(0)
    else:
        first = signals[0]
        changed_hash = digest("invented duplicate-slot input")
        evaluation = digest(
            {
                "target": first.target_id,
                "identity": first.identity.model_dump(mode="json"),
                "input": changed_hash,
                "quote": first.quote_id,
                "scope": first.scope,
            }
        )
        signals[1] = first.model_copy(
            update={
                "input_hash": changed_hash,
                "evaluation_id": evaluation,
                "signal_id": digest(
                    {
                        "evaluation": evaluation,
                        "scope": first.scope,
                        "quote": first.quote_id,
                    }
                ),
            }
        )
    outcome = derive_outcome(
        assessment.target.target_id,
        tuple(signals),
        assessment.trials,
        assessment.target.evidence_ids,
    )
    assert outcome.status == "incomplete" and outcome.missing == ("invalid_references",)
    assessment = replace(
        assessment, entailment=tuple(signals), usage=tuple(usage), outcome=outcome
    )
    rewrite_complete_assessment(path, assessment)
    with pytest.raises(SupportError, match="^storage_corrupt$"):
        read_support_run(path)
