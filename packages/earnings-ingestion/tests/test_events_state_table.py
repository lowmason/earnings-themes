"""The processing-state table (the Stage 5 spec, §Processing states, Storage): a
Polars frame, written as Parquet, one file per run, atomically, never replacing one."""

from datetime import UTC, datetime

import polars as pl
import pytest
from earnings_ingestion.events.state_table import (
    SCHEMA,
    read_runs,
    state_frame,
    write_run,
)
from earnings_ingestion.events.states import (
    AttemptOutcome,
    DocumentState,
    ExhibitAttempt,
    ExhibitChoice,
    MissingReason,
    StateTransition,
)

AT = datetime(2026, 9, 29, 14, 0, tzinfo=UTC)
FROZEN = "0009990003-25-000005"
PILOT = "a" * 64


def transition(sequence: int, before, after, **fields) -> StateTransition:
    return StateTransition(
        document_id="cik-0009990003:2025-06-30:release",
        event_id="cik-0009990003:2025-06-30",
        run_id="acquire-20260929T140000Z",
        sequence=sequence,
        recorded_at=AT,
        from_state=before,
        to_state=after,
        pilot_id="djia-synthetic-pilot",
        pilot_version=1,
        pilot_hash=PILOT,
        frozen_accession=FROZEN,
        **fields,
    )


RUN = [
    transition(
        0,
        None,
        DocumentState.EXPECTED,
        missing_reason=MissingReason.NOT_YET_CHECKED,
    ),
    transition(
        1,
        DocumentState.EXPECTED,
        DocumentState.ACQUIRED,
        accession=FROZEN,
        exhibit="crvd-20250730-ex9901.htm",
        artifact_sha256="b" * 64,
        retrieved_at=AT,
    ),
    transition(
        2,
        DocumentState.ACQUIRED,
        DocumentState.UNAVAILABLE,
        missing_reason=MissingReason.NO_CONFIRMED_RELEASE,
        attempts=(
            ExhibitAttempt(
                accession=FROZEN,
                filename="crvd-20250730-ex9901.htm",
                exhibit_type="EX-99.01",
                choice=ExhibitChoice.NAMED,
                outcome=AttemptOutcome.NOT_CONFIRMED,
                artifact_sha256="b" * 64,
                detail="its opening announces no results",
            ),
            ExhibitAttempt(
                accession=FROZEN,
                filename="crvd-20250730-ex9902.htm",
                exhibit_type="EX-99.02",
                choice=ExhibitChoice.LOWEST_SEQUENCE,
                outcome=AttemptOutcome.NOT_FETCHED,
                detail="HTTP 404",
            ),
        ),
    ),
]


def test_a_run_round_trips_through_parquet(tmp_path) -> None:
    path = write_run(tmp_path / "states", RUN)
    assert path.name == "acquire-20260929T140000Z.parquet"
    frame = pl.read_parquet(path)
    assert frame.schema == SCHEMA
    assert frame.height == 3
    assert read_runs(tmp_path / "states") == RUN


def test_the_frame_keeps_its_schema_when_a_column_is_all_null() -> None:
    frame = state_frame(RUN[:1])
    assert frame.schema == SCHEMA
    assert frame["attempts"].to_list() == [[]]


def test_a_run_is_never_replaced(tmp_path) -> None:
    write_run(tmp_path, RUN)
    write_run(tmp_path, RUN)
    changed = [
        RUN[0].model_copy(update={"recorded_at": datetime(2026, 9, 30, tzinfo=UTC)})
    ]
    with pytest.raises(FileExistsError, match="holds other bytes"):
        write_run(tmp_path, changed)


def test_a_run_file_holds_one_run(tmp_path) -> None:
    other = RUN[0].model_copy(update={"run_id": "acquire-other"})
    with pytest.raises(ValueError, match="one run's transitions"):
        write_run(tmp_path, [RUN[1], other])
    with pytest.raises(ValueError, match="no transition"):
        write_run(tmp_path, [])


def test_reading_refuses_another_schema_or_a_broken_history(tmp_path) -> None:
    state_frame(RUN).drop("corpus_error").write_parquet(tmp_path / "odd.parquet")
    with pytest.raises(ValueError, match="odd.parquet does not have the state table"):
        read_runs(tmp_path)
    (tmp_path / "odd.parquet").unlink()
    write_run(tmp_path, RUN[1:])
    with pytest.raises(ValueError, match="starts at expected"):
        read_runs(tmp_path)


def test_no_directory_is_no_run(tmp_path) -> None:
    assert read_runs(tmp_path / "absent") == []


def test_a_run_file_that_cannot_be_read_is_refused_by_name(tmp_path) -> None:
    (tmp_path / "acquire-x.parquet").write_bytes(b"not parquet")
    with pytest.raises(ValueError, match="acquire-x.parquet cannot be read"):
        read_runs(tmp_path)
