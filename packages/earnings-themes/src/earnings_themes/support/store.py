"""Immutable local support tables and structural/source consuming gates.

Raw artifacts stay in the caller's cache. Manifest raw/<digest>.json bindings
record their content hashes; reading this store never accesses that external cache.
Loading verifies structure, while consuming also re-verifies canonical evidence.
"""

import json
import os
import shutil
import tempfile
from collections.abc import Sequence
from pathlib import Path

import polars as pl
from earnings_core import VALIDATOR_VERSION, digest, sha256_hex

from earnings_themes.records import record_json
from earnings_themes.support.assess import derive_outcome
from earnings_themes.support.judges import validate_panel
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import (
    AssessmentResult,
    ContextReference,
    EntailmentSignal,
    EvidenceReference,
    JudgeAnswer,
    JudgeAttempt,
    JudgeTrial,
    RefusedTarget,
    ReviewOutcome,
    ReviewStatus,
    StoredSupportRun,
    SupportRunRecord,
    SupportRunResult,
    SupportSources,
    TargetRecord,
    UsageRecord,
    parse_support,
)
from earnings_themes.support.resolve import _source_hash, _validated, resolve_target
from earnings_themes.support.run import accounting
from earnings_themes.support.scorers import score_requests

IDS = pl.List(pl.String)
CODEBOOK = pl.Struct(
    {"codebook_id": pl.String, "codebook_version": pl.Int64, "content_hash": pl.String}
)
TARGET = pl.Struct(
    {
        "source_run_id": pl.String,
        "doc_id": pl.String,
        "claim_id": pl.String,
        "theme_id": pl.String,
        "codebook": CODEBOOK,
    }
)
THEME = pl.Struct(
    {
        "codebook": CODEBOOK,
        "theme_id": pl.String,
        "label": pl.String,
        "definition": pl.String,
        "parent_id": pl.String,
        "inclusion_rules": IDS,
        "exclusion_rules": IDS,
    }
)
RUNTIME = pl.Struct(
    {
        "model_id": pl.String,
        "revision": pl.String,
        "files": pl.List(pl.Struct({"relative_path": pl.String, "sha256": pl.String})),
        "runtime": pl.String,
        "runtime_version": pl.String,
        "device": pl.String,
        "precision": pl.String,
        "encoding_version": pl.String,
    }
)
SCORER = pl.Struct({"kind": pl.String, "runtime": RUNTIME, "input_limit": pl.Int64})
LICENSE = pl.Struct(
    {
        "source_url": pl.String,
        "terms_reference": pl.String,
        "intended_use": pl.String,
        "verified_on": pl.String,
        "permits_use": pl.Boolean,
    }
)
JUDGE = pl.Struct(
    {
        "family": pl.String,
        "runtime": RUNTIME,
        "input_limit": pl.Int64,
        "output_limit": pl.Int64,
        "hosting": pl.String,
        "weight_license": LICENSE,
    }
)
ANSWER = pl.Struct(
    {
        "claim_support": pl.String,
        "theme_fit": pl.String,
        "joint_support_score": pl.Float64,
        "quote_assessments": pl.List(
            pl.Struct({"quote_id": pl.String, "contribution": pl.String})
        ),
        "reason_codes": IDS,
        "summary": pl.String,
    }
)

SCHEMAS = {
    "targets": (
        TargetRecord,
        pl.Schema(
            {
                "schema_version": pl.Int64,
                "target_id": pl.String,
                "target": TARGET,
                "source_run_hash": pl.String,
                "claim_hash": pl.String,
                "input_hash": pl.String,
                "original_quote_ids": IDS,
                "evidence_ids": IDS,
                "theme": THEME,
            }
        ),
    ),
    "evidence": (
        EvidenceReference,
        pl.Schema(
            {
                "schema_version": pl.Int64,
                "target_id": pl.String,
                "quote_id": pl.String,
                "doc_id": pl.String,
                "canonical_hash": pl.String,
                "element_id": pl.String,
                "start": pl.Int64,
                "end": pl.Int64,
                "text_hash": pl.String,
                "validator_version": pl.String,
                "mask_ids": IDS,
            }
        ),
    ),
    "contexts": (
        ContextReference,
        pl.Schema(
            {
                "schema_version": pl.Int64,
                "target_id": pl.String,
                "doc_id": pl.String,
                "canonical_hash": pl.String,
                "element_id": pl.String,
                "start": pl.Int64,
                "end": pl.Int64,
                "text_hash": pl.String,
                "kind": pl.String,
            }
        ),
    ),
    "entailment": (
        EntailmentSignal,
        pl.Schema(
            {
                "schema_version": pl.Int64,
                "signal_id": pl.String,
                "target_id": pl.String,
                "scope": pl.String,
                "quote_id": pl.String,
                "evaluation_id": pl.String,
                "identity": SCORER,
                "input_hash": pl.String,
                "status": pl.String,
                "score": pl.Float64,
                "reason": pl.String,
                "input_tokens": pl.Int64,
                "latency_ms": pl.Int64,
                "cached": pl.Boolean,
            }
        ),
    ),
    "trials": (
        JudgeTrial,
        pl.Schema(
            {
                "schema_version": pl.Int64,
                "trial_id": pl.String,
                "target_id": pl.String,
                "identity": JUDGE,
                "presentation": pl.String,
                "attempt_ids": IDS,
                "status": pl.String,
                "answer": ANSWER,
                "reason": pl.String,
            }
        ),
    ),
    "attempts": (
        JudgeAttempt,
        pl.Schema(
            {
                "schema_version": pl.Int64,
                "attempt_id": pl.String,
                "trial_id": pl.String,
                "attempt": pl.Int64,
                "request_hash": pl.String,
                "prompt_hash": pl.String,
                "schema_hash": pl.String,
                "input_tokens": pl.Int64,
                "reserved_tokens": pl.Int64,
                "actual_prompt_tokens": pl.Int64,
                "actual_completion_tokens": pl.Int64,
                "latency_ms": pl.Int64,
                "cached": pl.Boolean,
                "raw_ref": pl.String,
                "problem": pl.String,
                "answer": ANSWER,
            }
        ),
    ),
    "usage": (
        UsageRecord,
        pl.Schema(
            {
                "schema_version": pl.Int64,
                "target_id": pl.String,
                "doc_id": pl.String,
                "operation_id": pl.String,
                "kind": pl.String,
                "reserved_tokens": pl.Int64,
                "actual_prompt_tokens": pl.Int64,
                "actual_completion_tokens": pl.Int64,
                "unreported": pl.Boolean,
                "cached": pl.Boolean,
                "latency_ms": pl.Int64,
            }
        ),
    ),
    "outcomes": (
        ReviewOutcome,
        pl.Schema(
            {
                "schema_version": pl.Int64,
                "target_id": pl.String,
                "status": pl.String,
                "flags": IDS,
                "missing": IDS,
                "signal_ids": IDS,
                "trial_ids": IDS,
            }
        ),
    ),
}


def _require(condition: bool) -> None:
    if not condition:
        raise SupportError("storage_corrupt")


def _unique(rows: Sequence, key) -> None:
    _require(len({key(r) for r in rows}) == len(rows))


def _raw_name(reference: str) -> bool:
    return (
        type(reference) is str
        and len(reference) == 69
        and reference.endswith(".json")
        and all(c in "0123456789abcdef" for c in reference[:64])
    )


def _assessments(stored: StoredSupportRun) -> tuple[AssessmentResult, ...]:
    outcomes = {o.target_id: o for o in stored.outcomes}
    return tuple(
        AssessmentResult(
            t,
            *(
                tuple(r for r in getattr(stored, kind) if r.target_id == t.target_id)
                for kind in ("evidence", "contexts", "entailment", "trials")
            ),
            tuple(
                a
                for a in stored.attempts
                if a.trial_id
                in {
                    trial.trial_id
                    for trial in stored.trials
                    if trial.target_id == t.target_id
                }
            ),
            tuple(u for u in stored.usage if u.target_id == t.target_id),
            outcomes[t.target_id],
        )
        for t in stored.targets
    )


def _stored(result: SupportRunResult) -> StoredSupportRun:
    return StoredSupportRun(
        result.record,
        tuple(a.target for a in result.assessments),
        *(
            tuple(r for a in result.assessments for r in getattr(a, kind))
            for kind in (
                "evidence",
                "contexts",
                "entailment",
                "trials",
                "attempts",
                "usage",
            )
        ),
        tuple(a.outcome for a in result.assessments),
    )


def _validate(stored: StoredSupportRun, *, published: bool) -> StoredSupportRun:
    """Closed models and complete graph checks; no source exactness claim."""
    try:
        _require(type(stored) is StoredSupportRun)
        record = _validated(stored.record, SupportRunRecord)
        tables = {}
        for kind, (model, _) in SCHEMAS.items():
            _require(type(getattr(stored, kind)) is tuple)
            tables[kind] = tuple(_validated(r, model) for r in getattr(stored, kind))
        stored = StoredSupportRun(record, **tables)
        validate_panel(record.extractor_family, record.judge_identities)
        _require(record.validator_version == VALIDATOR_VERSION)
        _unique(stored.targets, lambda r: r.target_id)
        _unique(stored.targets, lambda r: digest(r.target.model_dump(mode="json")))
        _unique(stored.outcomes, lambda r: r.target_id)
        _unique(stored.evidence, lambda r: (r.target_id, r.quote_id))
        _unique(stored.contexts, lambda r: (r.target_id, r.element_id, r.kind))
        _unique(stored.entailment, lambda r: r.signal_id)
        _unique(stored.trials, lambda r: r.trial_id)
        _unique(stored.attempts, lambda r: r.attempt_id)
        _unique(stored.usage, lambda r: r.operation_id)
        ids = {t.target_id for t in stored.targets}
        _require(
            tuple(o.target_id for o in stored.outcomes)
            == tuple(t.target_id for t in stored.targets)
        )
        for kind in ("evidence", "contexts", "entailment", "trials", "usage"):
            _require(all(r.target_id in ids for r in getattr(stored, kind)))
        _require(
            all(
                a.trial_id in {t.trial_id for t in stored.trials}
                for a in stored.attempts
            )
        )
        raw_refs = {a.raw_ref for a in stored.attempts if a.raw_ref is not None}
        _require(all(_raw_name(ref) for ref in raw_refs))
        artifacts = dict(record.artifact_hashes)
        expected = {f"raw/{ref}" for ref in raw_refs}
        if published:
            expected |= {f"{kind}.parquet" for kind in SCHEMAS}
        _require(set(artifacts) == expected)
        _require(len({a.prompt_hash for a in stored.attempts}) <= 1)
        _require(
            all(
                a.schema_hash == digest(JudgeAnswer.model_json_schema())
                for a in stored.attempts
            )
        )
        documents = dict(record.documents)
        for a in _assessments(stored):
            target, outcome = a.target, a.outcome
            _require(
                target.target.source_run_id == record.source_run_id
                and target.source_run_hash == record.source_run_hash
                and target.target.codebook == record.codebook
            )
            if outcome.status == ReviewStatus.REFUSED:
                _require(
                    not any(
                        (
                            a.evidence,
                            a.contexts,
                            a.entailment,
                            a.trials,
                            a.attempts,
                            a.usage,
                            target.evidence_ids,
                            target.original_quote_ids,
                            outcome.signal_ids,
                            outcome.trial_ids,
                            outcome.flags,
                        )
                    )
                )
                _require(target.theme is None and bool(outcome.missing))
                identity = digest(
                    {
                        "target": target.target.model_dump(mode="json"),
                        "source_run_hash": target.source_run_hash,
                    }
                )
                _require(
                    target.target_id == "support-" + identity
                    and target.input_hash == identity
                    and target.claim_hash == digest(None)
                )
                continue
            _require(target.target.doc_id in documents)
            _require(
                target.theme is not None
                and target.theme.codebook == record.codebook
                and target.theme.theme_id == target.target.theme_id
            )
            _require(
                target.target_id
                == "support-"
                + digest(
                    {
                        "target": target.target.model_dump(mode="json"),
                        "input_hash": target.input_hash,
                    }
                )
            )
            _require(
                bool(target.evidence_ids)
                and target.evidence_ids == tuple(e.quote_id for e in a.evidence)
                and set(target.evidence_ids) == set(target.original_quote_ids)
            )
            for ref in (*a.evidence, *a.contexts):
                _require(
                    ref.doc_id == target.target.doc_id
                    and ref.canonical_hash == documents[ref.doc_id]
                )
            _require(
                all(e.validator_version == record.validator_version for e in a.evidence)
            )
            _require(
                tuple((e.start, e.end, e.quote_id) for e in a.evidence)
                == tuple(sorted((e.start, e.end, e.quote_id) for e in a.evidence))
            )
            _require(all(s.identity == record.scorer_identity for s in a.entailment))
            for signal in a.entailment:
                evaluation = digest(
                    {
                        "target": target.target_id,
                        "identity": signal.identity.model_dump(mode="json"),
                        "input": signal.input_hash,
                        "quote": signal.quote_id,
                        "scope": signal.scope,
                    }
                )
                # A single quote's joint slot aliases the one raw evaluation.
                if signal.scope == "joint" and len(target.evidence_ids) == 1:
                    quote_signal = next(s for s in a.entailment if s.scope == "quote")
                    evaluation = quote_signal.evaluation_id
                    _require(
                        signal
                        == quote_signal.model_copy(
                            update={
                                "scope": "joint",
                                "quote_id": None,
                                "signal_id": signal.signal_id,
                            }
                        )
                    )
                _require(
                    signal.evaluation_id == evaluation
                    and signal.signal_id
                    == digest(
                        {
                            "evaluation": evaluation,
                            "scope": signal.scope,
                            "quote": signal.quote_id,
                        }
                    )
                )
            _require(
                len(a.trials) == 4
                and {(t.identity.family, t.presentation.value) for t in a.trials}
                == {
                    (j.family, p)
                    for j in record.judge_identities
                    for p in ("evidence_first", "claim_theme_first")
                }
            )
            for trial in a.trials:
                _require(trial.identity in record.judge_identities)
                _require(
                    trial.trial_id
                    == digest(
                        {
                            "target": target.target_id,
                            "identity": trial.identity.model_dump(mode="json"),
                            "presentation": trial.presentation,
                        }
                    )
                )
                attempts = tuple(v for v in a.attempts if v.trial_id == trial.trial_id)
                _require(
                    1 <= len(attempts) <= 2
                    and trial.attempt_ids == tuple(v.attempt_id for v in attempts)
                )
                _require(
                    tuple(v.attempt for v in attempts)
                    == tuple(range(1, len(attempts) + 1))
                )
                for attempt in attempts:
                    _require(
                        attempt.attempt_id
                        == digest(
                            {
                                "trial": trial.trial_id,
                                "attempt": attempt.attempt,
                                "request": attempt.request_hash,
                            }
                        )
                    )
                    _require(attempt.cached is False or attempt.reserved_tokens == 0)
                    _require(not attempt.cached or attempt.raw_ref is not None)
                    if attempt.answer is not None:
                        _require(attempt.raw_ref is not None)
                        _require(
                            attempt.problem is None
                            and {q.quote_id for q in attempt.answer.quote_assessments}
                            == set(target.evidence_ids)
                        )
                _require(
                    trial.answer == attempts[-1].answer
                    and trial.reason == attempts[-1].problem
                )
                if len(attempts) == 2:
                    _require(
                        attempts[0].answer is None
                        and attempts[0].problem
                        in {
                            "malformed_reply",
                            "invalid_references",
                            "tool_call_refused",
                            "model_mismatch",
                            "transport_error",
                        }
                    )
            _require(
                outcome
                == derive_outcome(
                    target.target_id, a.entailment, a.trials, target.evidence_ids
                )
            )
            _require(
                all(
                    u.doc_id == target.target.doc_id
                    and (not u.cached or u.reserved_tokens == 0)
                    and u.unreported
                    == (
                        u.actual_prompt_tokens is None
                        or u.actual_completion_tokens is None
                    )
                    for u in a.usage
                )
            )
            _check_usage(a)
        totals = accounting(_assessments(stored), stored.usage)
        _require(all(getattr(record, key) == value for key, value in totals.items()))
        _check_ceilings(stored)
        return stored
    except (
        SupportError,
        ValueError,
        TypeError,
        AttributeError,
        KeyError,
        StopIteration,
        OverflowError,
    ):
        raise SupportError("storage_corrupt") from None


def _check_usage(a: AssessmentResult) -> None:
    """Each actual dispatch/cache access has exactly one accounting record."""
    scorer = [u for u in a.usage if u.kind == "scorer"]
    unique = {
        s.evaluation_id: s
        for s in a.entailment
        if s.scope == "quote" or len(a.evidence) > 1
    }
    executed = [
        s
        for s in unique.values()
        if s.cached
        or s.status == "available"
        or s.reason in {"scorer_failed", "malformed_reply", "transport_error"}
    ]
    # Failed cache validation and failed scorer execution can share fixed reasons;
    # reported dispatch rows remain authoritative, bounded by the required slots.
    _require(
        len(scorer) <= len(unique)
        and len(scorer) >= sum(s.cached or s.status == "available" for s in executed)
    )
    judges = [u for u in a.usage if u.kind == "judge"]
    dispatched = [v for v in a.attempts if v.cached or v.reserved_tokens > 0]
    _require(len(judges) == len(dispatched))
    for usage, attempt in zip(judges, dispatched, strict=True):
        _require(
            usage.cached == attempt.cached
            and usage.reserved_tokens == attempt.reserved_tokens
            and usage.actual_prompt_tokens == attempt.actual_prompt_tokens
            and usage.actual_completion_tokens == attempt.actual_completion_tokens
            and usage.latency_ms == attempt.latency_ms
        )


def _check_ceilings(stored: StoredSupportRun) -> None:
    fresh = [u for u in stored.usage if not u.cached]
    ceiling = stored.record.ceilings
    for ordinal, row in enumerate(fresh):
        _require(
            row.operation_id
            == digest(
                {
                    "ordinal": ordinal,
                    "kind": row.kind,
                    "target": row.target_id,
                    "document": row.doc_id,
                }
            )
        )
    for kind in ("scorer", "judge"):
        rows = [u for u in fresh if u.kind == kind]
        _require(len(rows) <= getattr(ceiling, f"{kind}_per_run"))
        for field, scope in (("target_id", "target"), ("doc_id", "document")):
            for value in {getattr(u, field) for u in rows}:
                _require(
                    sum(getattr(u, field) == value for u in rows)
                    <= getattr(ceiling, f"{kind}_per_{scope}")
                )
    # Reservations are checked before dispatch. A reply may report overspend;
    # retain it truthfully and disallow subsequent reservations that exceed limits.
    charged_run = 0
    charged_documents = {}
    for row in fresh:
        if row.kind != "judge":
            continue
        charged_document = charged_documents.get(row.doc_id, 0)
        _require(charged_run + row.reserved_tokens <= ceiling.tokens_per_run)
        _require(charged_document + row.reserved_tokens <= ceiling.tokens_per_document)
        charge = (
            row.reserved_tokens
            if row.unreported
            else (row.actual_prompt_tokens or 0) + (row.actual_completion_tokens or 0)
        )
        charged_run += charge
        charged_documents[row.doc_id] = charged_document + charge


def reverify_support_run(
    stored: StoredSupportRun, sources: SupportSources
) -> tuple[ReviewOutcome, ...]:
    """Re-resolve current evidence/theme/context; return processing outcomes only."""
    stored = _validate(
        stored,
        published=any(
            name.endswith(".parquet") for name, _ in stored.record.artifact_hashes
        ),
    )
    try:
        _require(type(sources) is SupportSources)
        _require(
            stored.record.source_run_hash
            == _source_hash(sources.stored_run, sources.provenance_hash)
        )
        _require(
            stored.record.documents
            == tuple(sorted(sources.stored_run.record.documents.items()))
        )
        for assessment in _assessments(stored):
            if assessment.outcome.status == ReviewStatus.REFUSED:
                continue
            resolved = resolve_target(
                sources.stored_run,
                sources.bundles,
                sources.codebook,
                assessment.target.target,
                provenance_hash=sources.provenance_hash,
            )
            if isinstance(resolved, RefusedTarget):
                raise SupportError("input_changed")
            if (
                resolved.record != assessment.target
                or resolved.evidence != assessment.evidence
                or resolved.contexts != assessment.contexts
            ):
                raise SupportError("input_changed")
            hashes = {
                quote: request.input_hash for quote, request in score_requests(resolved)
            }
            for signal in assessment.entailment:
                expected = (
                    hashes[signal.quote_id]
                    if signal.quote_id is not None or len(resolved.evidence) > 1
                    else hashes[resolved.evidence[0].quote_id]
                )
                _require(signal.input_hash == expected)
        return stored.outcomes
    except SupportError:
        raise
    except Exception:  # noqa: BLE001 - suppress arbitrary source-bearing diagnostics
        raise SupportError("input_changed") from None


def write_support_run(
    directory: Path, result: SupportRunResult, sources: SupportSources
) -> Path:
    """Gate before I/O, then publish a complete new sibling atomically."""
    try:
        _require(
            type(result) is SupportRunResult
            and type(result.assessments) is tuple
            and all(type(a) is AssessmentResult for a in result.assessments)
        )
        stored = _validate(_stored(result), published=False)
    except (AttributeError, TypeError, ValueError):
        raise SupportError("storage_corrupt") from None
    reverify_support_run(stored, sources)
    if directory.exists():
        raise FileExistsError("support_destination_exists")
    partial = None
    try:
        directory.parent.mkdir(parents=True, exist_ok=True)
        partial = Path(
            tempfile.mkdtemp(dir=directory.parent, prefix=f".{directory.name}-")
        )
        hashes = dict(stored.record.artifact_hashes)
        for kind, (_, schema) in SCHEMAS.items():
            rows = [r.model_dump(mode="json") for r in getattr(stored, kind)]
            path = partial / f"{kind}.parquet"
            pl.DataFrame(rows, schema=schema, orient="row").write_parquet(path)
            hashes[path.name] = sha256_hex(path.read_bytes())
        record = _validated(
            stored.record.model_copy(
                update={"artifact_hashes": tuple(sorted(hashes.items()))}
            ),
            SupportRunRecord,
        )
        (partial / "run.json").write_bytes(record_json(record))
        if directory.exists():
            raise FileExistsError("support_destination_exists")
        os.rename(partial, directory)
    except Exception:  # noqa: BLE001 - suppress arbitrary source-bearing diagnostics
        if partial is not None:
            shutil.rmtree(partial, ignore_errors=True)
        raise SupportError("storage_corrupt") from None
    except BaseException:
        if partial is not None:
            shutil.rmtree(partial, ignore_errors=True)
        raise
    return directory


def read_support_run(directory: Path) -> StoredSupportRun:
    """Check bytes, declared schemas, closed records, bindings and accounting."""
    try:
        record = parse_support(
            json.loads((directory / "run.json").read_bytes()), SupportRunRecord
        )
        hashes = dict(record.artifact_hashes)
        tables = {}
        for kind, (model, schema) in SCHEMAS.items():
            path = directory / f"{kind}.parquet"
            _require(
                not path.is_symlink()
                and hashes.get(path.name) == sha256_hex(path.read_bytes())
            )
            frame = pl.read_parquet(path)
            _require(frame.schema == schema)
            tables[kind] = tuple(
                parse_support(row, model) for row in frame.iter_rows(named=True)
            )
        return _validate(StoredSupportRun(record, **tables), published=True)
    except Exception:  # noqa: BLE001 - suppress arbitrary source-bearing diagnostics
        raise SupportError("storage_corrupt") from None
