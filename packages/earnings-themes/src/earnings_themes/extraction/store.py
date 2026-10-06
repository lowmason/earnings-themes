"""Writing and reading an extraction run (the Stage 7 spec, §Storage; R6.1, R6.2;
ES6).

- **Before storage.** ``write_run`` verifies every quote again with
  ``reverify_span``, against the bundle of its document, and writes nothing if any
  fails (R6.1). Its refusal names each quote by its IDs and reason, never by its
  text (GS13).
- **The layout.** A new directory holds ``run.json`` and one Parquet file per record
  kind, each written through Polars under an explicit schema: documents, windows,
  visits, quotes, claims, and rejections. The files are written into a hidden
  sibling, which is then renamed, so a run directory is whole or absent, and an
  existing one is never overwritten.
- **Reading.** ``read_run`` refuses a file of another schema, revalidates nested
  models, and enforces the shared relational gate. Refusals carry fixed reasons,
  with no row values, paths or exception chain (GS13). Each consumer verifies
  quotes again at its own gate.
- **Where.** The caller supplies the directory. Stage 7 writes only to test temporary
  directories: never to ``data/``, and never a committed file.
"""

import hashlib
import itertools
import os
import re
import shutil
import tempfile
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import polars as pl
from earnings_core import Rejection, canonical_json, digest, reverify_span
from pydantic import BaseModel

from earnings_themes.anchoring import Bundle
from earnings_themes.extraction.records import (
    Claim,
    DocumentOutcome,
    DocumentRecord,
    ExtractionProblem,
    ExtractionRecord,
    ExtractionRejection,
    Quote,
    RunRecord,
    Visit,
    WindowOutcome,
    WindowRecord,
)
from earnings_themes.extraction.run import RunResult
from earnings_themes.records import parse, read_json, record_json

RUN_FILE = "run.json"
IDS = pl.List(pl.String)
VERIFIED_SPAN = pl.Struct(
    {
        "schema_version": pl.Int64,
        "doc_id": pl.String,
        "canonical_hash": pl.String,
        "start": pl.Int64,
        "end": pl.Int64,
        "quote_text": pl.String,
        "element_id": pl.String,
        "prefix": pl.String,
        "suffix": pl.String,
        "validator_version": pl.String,
    }
)
REJECTION = pl.Struct(
    {
        "schema_version": pl.Int64,
        "reason": pl.String,
        "detail": pl.String,
        "validator_version": pl.String,
    }
)
SCHEMAS: dict[str, tuple[type[ExtractionRecord], pl.Schema]] = {
    "documents": (
        DocumentRecord,
        pl.Schema(
            {
                "schema_version": pl.Int64,
                "doc_id": pl.String,
                "canonical_hash": pl.String,
                "outcome": pl.String,
                "units": pl.Int64,
                "windows": pl.Int64,
                "windows_failed": pl.Int64,
                "candidates": pl.Int64,
                "quotes": pl.Int64,
                "claims": pl.Int64,
                "rejections": pl.Int64,
            }
        ),
    ),
    "windows": (
        WindowRecord,
        pl.Schema(
            {
                "schema_version": pl.Int64,
                "doc_id": pl.String,
                "window_id": pl.String,
                "start": pl.Int64,
                "end": pl.Int64,
                "unit_ids": IDS,
                "context_id": pl.String,
                "attempts": pl.Int64,
                "outcome": pl.String,
                "reason": pl.String,
                "requests": pl.Int64,
                "cache_hits": pl.Int64,
                "prompt_tokens": pl.Int64,
                "completion_tokens": pl.Int64,
                "unreported": pl.Int64,
                "latency_ms": pl.Int64,
                "exhausted": pl.Boolean,
            }
        ),
    ),
    "visits": (
        Visit,
        pl.Schema(
            {
                "schema_version": pl.Int64,
                "doc_id": pl.String,
                "element_id": pl.String,
                "window_id": pl.String,
                "outcome": pl.String,
                "reason": pl.String,
            }
        ),
    ),
    "quotes": (
        Quote,
        pl.Schema(
            {
                "schema_version": pl.Int64,
                "quote_id": pl.String,
                "span": VERIFIED_SPAN,
                "mask_ids": IDS,
            }
        ),
    ),
    "claims": (
        Claim,
        pl.Schema(
            {
                "schema_version": pl.Int64,
                "claim_id": pl.String,
                "doc_id": pl.String,
                "window_id": pl.String,
                "attempt": pl.Int64,
                "claim": pl.String,
                "quote_ids": IDS,
            }
        ),
    ),
    "rejections": (
        ExtractionRejection,
        pl.Schema(
            {
                "schema_version": pl.Int64,
                "doc_id": pl.String,
                "window_id": pl.String,
                "attempt": pl.Int64,
                "candidate_index": pl.Int64,
                "labels": IDS,
                "element_ids": IDS,
                "rejection": REJECTION,
                "problem": pl.String,
                "detail": pl.String,
            }
        ),
    ),
}
"""Each record kind's file stem, model, and schema."""


@dataclass(frozen=True)
class StoredRun:
    """A run as it is stored: its record, and each kind of record, in order."""

    record: RunRecord
    documents: tuple[DocumentRecord, ...]
    windows: tuple[WindowRecord, ...]
    visits: tuple[Visit, ...]
    quotes: tuple[Quote, ...]
    claims: tuple[Claim, ...]
    rejections: tuple[ExtractionRejection, ...]

    @classmethod
    def of(cls, result: RunResult) -> "StoredRun":
        return cls(
            record=result.record,
            documents=result.document_records,
            windows=result.windows,
            visits=result.visits,
            quotes=result.quotes,
            claims=result.claims,
            rejections=result.rejections,
        )


class StorageRefused(ValueError):
    """Quotes that failed verification again, by IDs and reason only (GS13)."""

    def __init__(self, refused: Sequence[tuple[str, str, str]]) -> None:
        self.refused = tuple(refused)
        listed = "; ".join(
            f"{_safe_id(d)} {_safe_id(q)}: {reason}" for d, q, reason in self.refused
        )
        super().__init__(f"{len(self.refused)} quotes failed verification: {listed}")


def refused_quotes(
    run: StoredRun, bundles: Sequence[Bundle]
) -> list[tuple[str, str, str]]:
    """Each quote that fails ``reverify_span``: its ``doc_id``, ID, and reason. A
    quote of a document with no bundle here is ``wrong_document``."""
    by_doc = {bundle.document.doc_id: bundle for bundle in bundles}
    refused = []
    for quote in run.quotes:
        doc_id = quote.span.doc_id
        bundle = by_doc.get(doc_id)
        if bundle is None:
            refused.append((doc_id, quote.quote_id, "wrong_document"))
            continue
        again = reverify_span(bundle.document, bundle.elements, quote.span)
        if isinstance(again, Rejection):
            refused.append((doc_id, quote.quote_id, again.reason.value))
    return refused


def _safe_id(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_.@#:/-]+", value):
        return value
    return "id-" + hashlib.sha256(value.encode()).hexdigest()[:12]


def _require(condition: bool) -> None:
    if not condition:
        raise ValueError("malformed_record")


def _fresh_record[M: BaseModel](record: M, model: type[M]) -> M:
    _require(type(record) is model)
    return model.model_validate_json(
        canonical_json(record.model_dump(mode="python", warnings=False))
    )


def validate_stored_run(run: StoredRun) -> StoredRun:
    """Return strictly reconstructed, relationally checked schema-1 records.

    This gate performs no I/O or evidence-text verification. Consumers still
    reverify spans against their current immutable bundles and masks.
    """
    try:
        _require(type(run) is StoredRun)
        rows = {}
        for kind, (model, _) in SCHEMAS.items():
            given = getattr(run, kind)
            _require(type(given) is tuple)
            rows[kind] = tuple(_fresh_record(row, model) for row in given)
        checked = StoredRun(record=_fresh_record(run.record, RunRecord), **rows)
        _validate_relations(checked)
        return checked
    except Exception:  # noqa: BLE001 - storage boundaries suppress untrusted diagnostics
        raise ValueError("malformed_record") from None


def _unique[R, K](rows: Sequence[R], key: Callable[[R], K]) -> dict[K, R]:
    indexed = {key(row): row for row in rows}
    _require(len(indexed) == len(rows))
    return indexed


def _validate_relations(run: StoredRun) -> None:
    documents = _unique(run.documents, lambda d: d.doc_id)
    windows = _unique(run.windows, lambda w: (w.doc_id, w.window_id))
    quotes = _unique(run.quotes, lambda q: (q.span.doc_id, q.quote_id))
    _unique(run.claims, lambda c: (c.doc_id, c.claim_id))
    _unique(run.visits, lambda v: (v.doc_id, v.element_id))
    _require(
        run.record.documents == {d.doc_id: d.canonical_hash for d in run.documents}
    )
    _require(run.record.configuration_hash == digest(run.record.configuration))
    for window in run.windows:
        _require(window.doc_id in documents)
    expected_visits = tuple(
        (w.doc_id, unit, w.window_id, w.outcome, w.reason)
        for w in run.windows
        for unit in w.unit_ids
    )
    actual_visits = tuple(
        (v.doc_id, v.element_id, v.window_id, v.outcome, v.reason) for v in run.visits
    )
    _require(actual_visits == expected_visits)
    linked = set()
    candidate_keys = set()
    for claim in run.claims:
        window = windows.get((claim.doc_id, claim.window_id))
        _require(window is not None)
        _require(
            window.outcome is WindowOutcome.COMPLETED
            and claim.attempt <= window.attempts
        )
        index = int(claim.claim_id.rsplit("-", 1)[1])
        key = (claim.doc_id, claim.window_id, claim.attempt, index)
        _require(key not in candidate_keys)
        candidate_keys.add(key)
        for quote_id in claim.quote_ids:
            quote = quotes.get((claim.doc_id, quote_id))
            _require(quote is not None)
            _require(quote.span.element_id in window.unit_ids)
            _require(window.start <= quote.span.start < quote.span.end <= window.end)
            linked.add((claim.doc_id, quote_id))
    _require(linked == set(quotes))
    for quote in run.quotes:
        document = documents.get(quote.span.doc_id)
        _require(
            document is not None
            and quote.span.canonical_hash == document.canonical_hash
        )
    for rejection in run.rejections:
        _require(rejection.doc_id in documents)
        if rejection.window_id is None:
            _require(rejection.attempt is None and rejection.candidate_index is None)
            _require(rejection.rejection is not None)
            continue
        window = windows.get((rejection.doc_id, rejection.window_id))
        _require(window is not None and rejection.attempt is not None)
        blocked = rejection.problem is ExtractionProblem.BUDGET_EXHAUSTED
        maximum = window.attempts + (1 if blocked and window.exhausted else 0)
        _require(rejection.attempt <= min(2, maximum))
        _require(all(unit in window.unit_ids for unit in rejection.element_ids))
        if rejection.candidate_index is not None:
            _require(not blocked)
            key = (
                rejection.doc_id,
                rejection.window_id,
                rejection.attempt,
                rejection.candidate_index,
            )
            _require(key not in candidate_keys)
            candidate_keys.add(key)
    for document in run.documents:
        _validate_document(document, run)
    record = run.record
    for field in ("units", "windows", "candidates", "quotes", "claims"):
        _require(
            getattr(record, field) == sum(getattr(d, field) for d in run.documents)
        )
    _require(
        record.rejections_by_reason == dict(Counter(r.reason for r in run.rejections))
    )
    for field in (
        "requests",
        "cache_hits",
        "prompt_tokens",
        "completion_tokens",
        "unreported",
    ):
        _require(getattr(record, field) == sum(getattr(w, field) for w in run.windows))
    _require(record.exhausted == any(w.exhausted for w in run.windows))


def _validate_document(document: DocumentRecord, run: StoredRun) -> None:
    doc_id = document.doc_id
    windows = tuple(w for w in run.windows if w.doc_id == doc_id)
    claims = tuple(c for c in run.claims if c.doc_id == doc_id)
    quotes = tuple(q for q in run.quotes if q.span.doc_id == doc_id)
    rejections = tuple(r for r in run.rejections if r.doc_id == doc_id)
    units = tuple(unit for w in windows for unit in w.unit_ids)
    _require(len(units) == len(set(units)))
    _require(
        all(left.end <= right.start for left, right in itertools.pairwise(windows))
    )
    failed = sum(w.outcome is WindowOutcome.FAILED for w in windows)
    expected = {
        "units": len(units),
        "windows": len(windows),
        "windows_failed": failed,
        "candidates": len(claims)
        + sum(r.candidate_index is not None for r in rejections),
        "quotes": len(quotes),
        "claims": len(claims),
        "rejections": len(rejections),
    }
    _require(all(getattr(document, key) == value for key, value in expected.items()))
    refused_document = any(r.window_id is None for r in rejections)
    if refused_document:
        _require(not windows and not claims and not quotes)
        outcome = DocumentOutcome.FAILED
    elif not failed:
        outcome = DocumentOutcome.COMPLETED
    elif failed == len(windows):
        outcome = DocumentOutcome.FAILED
    else:
        outcome = DocumentOutcome.PARTIAL
    _require(document.outcome is outcome)


def _safe_path(path: Path) -> None:
    # Check before resolving or reading; a symlink must not expose other inputs.
    if ".." in path.parts or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("storage_corrupt")


def write_run(directory: Path, run: StoredRun, bundles: Sequence[Bundle]) -> Path:
    """Publish a new structurally valid run after current quote reverification.

    Structural refusals are ``malformed_record``; storage failures are
    ``storage_corrupt``. Existing directories raise a fixed ``FileExistsError``.
    """
    run = validate_stored_run(run)
    try:
        refused = refused_quotes(run, bundles)
    except Exception:  # noqa: BLE001 - storage boundaries suppress untrusted diagnostics
        raise ValueError("malformed_record") from None
    if refused:
        raise StorageRefused(refused)
    partial = None
    try:
        _safe_path(directory)
        if directory.exists():
            raise FileExistsError("run_exists")
        directory.parent.mkdir(parents=True, exist_ok=True)
        partial = Path(tempfile.mkdtemp(dir=directory.parent, prefix=".extraction-"))
        for kind, (_, schema) in SCHEMAS.items():
            rows = [record.model_dump(mode="json") for record in getattr(run, kind)]
            frame = pl.DataFrame(rows, schema=schema, orient="row")
            frame.write_parquet(partial / f"{kind}.parquet")
        (partial / RUN_FILE).write_bytes(record_json(run.record))
        os.rename(partial, directory)
    except FileExistsError:
        raise FileExistsError("run_exists") from None
    except Exception:  # noqa: BLE001 - storage boundaries suppress untrusted diagnostics
        raise ValueError("storage_corrupt") from None
    finally:
        if partial is not None:
            shutil.rmtree(partial, ignore_errors=True)
    return directory


def read_run(directory: Path) -> StoredRun:
    """Load only exact schemas, then enforce the public structural gate.

    Files, schemas, rows, and relationships fail as ``storage_corrupt`` without
    their values, paths, details, or exception chains.
    """
    try:
        _safe_path(directory)
        record_path = directory / RUN_FILE
        _safe_path(record_path)
        record = parse(read_json(record_path), RunRecord, RUN_FILE)
        kinds = {}
        for kind, (model, schema) in SCHEMAS.items():
            path = directory / f"{kind}.parquet"
            _safe_path(path)
            frame = pl.read_parquet(path)
            _require(frame.schema == schema)
            kinds[kind] = tuple(
                parse(row, model, kind) for row in frame.iter_rows(named=True)
            )
        return validate_stored_run(StoredRun(record=record, **kinds))
    except Exception:  # noqa: BLE001 - storage boundaries suppress untrusted diagnostics
        raise ValueError("storage_corrupt") from None
