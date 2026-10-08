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

from earnings_ingestion.events.states import (
    ProcessingTransition,
    StateRecord,
    StateTransition,
    check_histories,
)
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


PROCESSING_SCHEMA = pl.Schema(
    dict(SCHEMA)
    | {
        "processing_run_id": pl.String,
        "processing_run_hash": pl.String,
        "completion_hash": pl.String,
        "processing_reason": pl.String,
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


def write_processing_run(
    directory: Path, transitions: Sequence[ProcessingTransition]
) -> Path:
    """Preflight mixed history and write immutable schema-2 processing bytes.

    Exact retries compare bytes before chaining, since the document is terminal
    after the first write. Different bytes under the same state run refuse.
    """
    try:
        if not transitions or any(
            type(t) is not ProcessingTransition for t in transitions
        ):
            raise ValueError("state_record_invalid")
        checked = [
            ProcessingTransition.model_validate_json(t.model_dump_json())
            for t in transitions
        ]
        runs = {t.run_id for t in checked}
        processing_runs = {
            (t.processing_run_id, t.processing_run_hash) for t in checked
        }
        if len(runs) != 1 or len(processing_runs) != 1:
            raise ValueError("state_record_invalid")
        frame = pl.DataFrame(
            [t.model_dump(mode="python") for t in checked],
            schema=PROCESSING_SCHEMA,
            orient="row",
        )
        buffer = io.BytesIO()
        frame.write_parquet(buffer)
        data = buffer.getvalue()
        path = directory / f"{runs.pop()}.parquet"
        if path.exists():
            if path.read_bytes() != data:
                raise FileExistsError("state_run_conflict")
            read_runs(directory)
            return path
        previous = read_runs(directory)
        processing_id = checked[0].processing_run_id
        if any(
            isinstance(t, ProcessingTransition) and t.processing_run_id == processing_id
            for t in previous
        ):
            raise FileExistsError("state_run_conflict")
        check_histories([*previous, *checked])
        write_new(path, data)
        return path
    except FileExistsError:
        raise FileExistsError("state_run_conflict") from None
    except ValueError as error:
        reasons = {
            "state_record_invalid",
            "state_not_processable",
            "state_predecessor_mismatch",
            "state_storage_corrupt",
            "state_schema_invalid",
            "state_history_invalid",
        }
        reason = (
            str(error)
            if type(error) is ValueError and str(error) in reasons
            else "state_record_invalid"
        )
        raise ValueError(reason) from None
    except Exception:  # noqa: BLE001 - diagnostic boundary suppresses source text
        raise ValueError("state_storage_corrupt") from None


def read_runs(directory: Path) -> list[StateRecord]:
    """Read exact schema-1/schema-2 files and validate their combined histories.

    Version dispatch never coerces an unknown/mixed schema. Diagnostics contain
    closed reasons only, including for malformed acquisition files.
    """
    transitions: list[StateRecord] = []
    try:
        for path in sorted(directory.glob("*.parquet")):
            try:
                frame = pl.read_parquet(path)
            except (pl.exceptions.PolarsError, OSError):
                raise ValueError("state_storage_corrupt") from None
            if frame.schema == SCHEMA:
                model, version = StateTransition, 1
            elif frame.schema == PROCESSING_SCHEMA:
                model, version = ProcessingTransition, 2
            else:
                raise ValueError("state_schema_invalid")
            if (
                not frame.height
                or frame["schema_version"].to_list() != [version] * frame.height
            ):
                raise ValueError("state_schema_invalid")
            try:
                rows = [
                    model.model_validate(row, strict=False)
                    for row in frame.iter_rows(named=True)
                ]
            except (ValueError, TypeError):
                raise ValueError("state_record_invalid") from None
            if model is ProcessingTransition and {row.run_id for row in rows} != {
                path.stem
            }:
                raise ValueError("state_record_invalid")
            if (
                model is ProcessingTransition
                and len(
                    {(row.processing_run_id, row.processing_run_hash) for row in rows}
                )
                != 1
            ):
                raise ValueError("state_record_invalid")
            transitions.extend(rows)
        bindings: dict[str, tuple[str, str]] = {}
        for transition in transitions:
            if isinstance(transition, ProcessingTransition):
                binding = (transition.run_id, transition.processing_run_hash)
                previous_binding = bindings.setdefault(
                    transition.processing_run_id, binding
                )
                if previous_binding != binding:
                    raise ValueError("state_record_invalid")
        try:
            check_histories(transitions)
        except (ValueError, TypeError):
            raise ValueError("state_history_invalid") from None
    except ValueError as error:
        reason = str(error)
        if reason not in {
            "state_storage_corrupt",
            "state_schema_invalid",
            "state_record_invalid",
            "state_history_invalid",
        }:
            reason = "state_storage_corrupt"
        raise ValueError(reason) from None
    except Exception:  # noqa: BLE001 - diagnostic boundary suppresses source text
        raise ValueError("state_storage_corrupt") from None
    return transitions
