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
- **Reading.** ``read_run`` refuses a file of another schema, and reads each row back
  through its model in JSON mode, so strict typing holds. A refused row is named by
  its file, row, and fields, never its text (GS13). Each consumer verifies the quotes
  again at its own gate.
- **Where.** The caller supplies the directory. Stage 7 writes only to test temporary
  directories: never to ``data/``, and never a committed file.
"""

import os
import shutil
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import polars as pl
from earnings_core import Rejection, reverify_span

from earnings_themes.anchoring import Bundle
from earnings_themes.extraction.records import (
    Claim,
    DocumentRecord,
    ExtractionRecord,
    ExtractionRejection,
    Quote,
    RunRecord,
    Visit,
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
        listed = "; ".join(f"{d} {q}: {reason}" for d, q, reason in self.refused)
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


def write_run(directory: Path, run: StoredRun, bundles: Sequence[Bundle]) -> Path:
    """Write ``run`` to the new directory ``directory``, once every quote verifies
    again against ``bundles``; raises ``StorageRefused`` and writes nothing if any
    fails, and ``FileExistsError`` if ``directory`` exists."""
    refused = refused_quotes(run, bundles)
    if refused:
        raise StorageRefused(refused)
    if directory.exists():
        raise FileExistsError(f"{directory} exists; a run is never overwritten")
    directory.parent.mkdir(parents=True, exist_ok=True)
    partial = Path(tempfile.mkdtemp(dir=directory.parent, prefix=f".{directory.name}-"))
    try:
        for kind, (_, schema) in SCHEMAS.items():
            rows = [record.model_dump(mode="json") for record in getattr(run, kind)]
            frame = pl.DataFrame(rows, schema=schema, orient="row")
            frame.write_parquet(partial / f"{kind}.parquet")
        (partial / RUN_FILE).write_bytes(record_json(run.record))
        os.rename(partial, directory)
    except BaseException:
        shutil.rmtree(partial, ignore_errors=True)
        raise
    return directory


def read_run(directory: Path) -> StoredRun:
    """The run stored in ``directory``; raises ``ValueError`` for a file of another
    schema, and ``RecordError`` for a record its model refuses."""
    record = parse(read_json(directory / RUN_FILE), RunRecord, RUN_FILE)
    kinds = {}
    for kind, (model, schema) in SCHEMAS.items():
        path = directory / f"{kind}.parquet"
        frame = pl.read_parquet(path)
        if frame.schema != schema:
            raise ValueError(f"{path.name} does not have the {kind} schema")
        kinds[kind] = tuple(
            parse(row, model, f"{path.name} row {index}")
            for index, row in enumerate(frame.iter_rows(named=True))
        )
    return StoredRun(record=record, **kinds)
