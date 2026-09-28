"""The processing-state table (the Stage 5 spec, §Processing states, Storage; plan 8,
P8-7).

- **The frame.** ``state_frame`` holds ``StateTransition`` rows as a Polars frame of
  the fixed ``SCHEMA``, so a column that is null in every row keeps its type, and an
  exhibit's attempts are a list of structs.
- **One file per run.** ``write_run`` writes one run's transitions as Parquet to
  ``<run_id>.parquet``, atomically, and never replaces a file that holds other bytes.
  The runs live under the gitignored ``data/runs/events/states/``.
- **Reading.** ``read_runs`` reads every run in a directory, refuses a file of another
  schema, and checks that each document's transitions chain under each pilot.
"""

import io
from collections.abc import Sequence
from pathlib import Path

import polars as pl

from earnings_ingestion.events.states import StateTransition, check_histories
from earnings_ingestion.fetch.store import write_new

STATES_DIR = Path("data") / "runs" / "events" / "states"

ATTEMPT = pl.Struct(
    {
        "accession": pl.String,
        "filename": pl.String,
        "exhibit_type": pl.String,
        "choice": pl.String,
        "outcome": pl.String,
        "artifact_sha256": pl.String,
        "failure_reason": pl.String,
        "detail": pl.String,
    }
)
SCHEMA = pl.Schema(
    {
        "schema_version": pl.Int64,
        "document_id": pl.String,
        "event_id": pl.String,
        "run_id": pl.String,
        "sequence": pl.Int64,
        "recorded_at": pl.Datetime("us", "UTC"),
        "from_state": pl.String,
        "to_state": pl.String,
        "missing_reason": pl.String,
        "failure_reason": pl.String,
        "pilot_id": pl.String,
        "pilot_version": pl.Int64,
        "pilot_hash": pl.String,
        "frozen_accession": pl.String,
        "accession": pl.String,
        "exhibit": pl.String,
        "artifact_sha256": pl.String,
        "retrieved_at": pl.Datetime("us", "UTC"),
        "doc_id": pl.String,
        "override_id": pl.String,
        "corpus_error": pl.String,
        "attempts": pl.List(ATTEMPT),
    }
)


def state_frame(transitions: Sequence[StateTransition]) -> pl.DataFrame:
    """``transitions`` as a frame of ``SCHEMA``."""
    rows = [transition.model_dump(mode="python") for transition in transitions]
    return pl.DataFrame(rows, schema=SCHEMA, orient="row")


def write_run(directory: Path, transitions: Sequence[StateTransition]) -> Path:
    """Write one run's transitions to ``<run_id>.parquet`` in ``directory``."""
    runs = {transition.run_id for transition in transitions}
    if not runs:
        raise ValueError("no transition to write")
    if len(runs) > 1:
        raise ValueError(f"a run file holds one run's transitions, not {sorted(runs)}")
    buffer = io.BytesIO()
    state_frame(transitions).write_parquet(buffer)
    path = directory / f"{runs.pop()}.parquet"
    write_new(path, buffer.getvalue())
    return path


def read_runs(directory: Path) -> list[StateTransition]:
    """Every transition of every run in ``directory``; raises ``ValueError`` unless
    each file reads, has ``SCHEMA``, and each document's transitions chain."""
    transitions = []
    for path in sorted(directory.glob("*.parquet")):
        try:
            frame = pl.read_parquet(path)
        except pl.exceptions.PolarsError as exc:
            raise ValueError(f"{path.name} cannot be read: {exc}") from exc
        if frame.schema != SCHEMA:
            raise ValueError(f"{path.name} does not have the state table's schema")
        transitions += [
            StateTransition.model_validate(row, strict=False)
            for row in frame.iter_rows(named=True)
        ]
    check_histories(transitions)
    return transitions
