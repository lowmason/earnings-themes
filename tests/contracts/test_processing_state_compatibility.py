"""Invented processing runs alongside the unchanged synthetic acquisition history."""

import io
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import polars as pl
import pytest
from earnings_core import sha256_hex
from earnings_ingestion.canonical.records import FailureReason
from earnings_ingestion.events import state_table, states
from earnings_ingestion.events.fixture import ACQUISITION, FIXTURE_DIR, load_transitions
from pydantic import ValidationError

REPO = Path(__file__).resolve().parents[2]
AT = datetime(2026, 10, 6, tzinfo=UTC)
HASH = "d" * 64


def acquisition():
    return load_transitions(REPO / FIXTURE_DIR / ACQUISITION)


def parsed():
    return next(t for t in acquisition() if t.to_state is states.DocumentState.PARSED)


def processing(**updates):
    model = getattr(states, "ProcessingTransition", None)
    assert model is not None
    predecessor = parsed()
    values = (
        predecessor.model_dump(mode="json")
        | {
            "schema_version": 2,
            "run_id": "processing-1",
            "sequence": 0,
            "recorded_at": AT.isoformat(),
            "from_state": "parsed",
            "to_state": "failed",
            "attempts": [],
            "failure_reason": None,
            "processing_run_id": "workflow-1",
            "processing_run_hash": HASH,
            "completion_hash": "e" * 64,
            "processing_reason": "unexpected_error",
            "missing_reason": "processing_failed",
        }
        | updates
    )
    return model.model_validate_json(json.dumps(values))


def test_schema_two_processing_failure_and_legacy_failure_stay_distinct():
    row = processing()
    assert row.schema_version == 2
    assert row.to_state is states.DocumentState.FAILED
    assert row.failure_reason is None
    assert row.missing_reason.value == "processing_failed"
    legacy = parsed().model_dump(mode="json") | {
        "from_state": "parsed",
        "to_state": "failed",
        "missing_reason": "parse_failed",
        "failure_reason": "parse_failed",
    }
    with pytest.raises(ValidationError):
        states.StateTransition.model_validate_json(json.dumps(legacy))


@pytest.mark.parametrize(
    "updates",
    [
        {"to_state": "completed", "missing_reason": None, "processing_reason": None},
        {
            "to_state": "completed-no-theme",
            "missing_reason": None,
            "processing_reason": "explicit_no_theme",
        },
        {
            "to_state": "partial",
            "missing_reason": "valid_unmatched",
            "processing_reason": "valid_unmatched",
        },
    ],
    ids=["completed", "no_theme", "partial"],
)
def test_processing_outcome_round_trips_with_closed_metadata(tmp_path, updates):
    history = acquisition()
    legacy_path = state_table.write_run(tmp_path, history)
    original = sha256_hex(legacy_path.read_bytes())
    row = processing(**updates)
    path = state_table.write_processing_run(tmp_path, [row])
    frame = pl.read_parquet(path)
    assert frame.schema == state_table.PROCESSING_SCHEMA
    assert frame.height == 1
    rows = state_table.read_runs(tmp_path)
    assert len(rows) == len(history) + 1
    latest = states.current_states(rows, row.pilot_hash)[row.document_id]
    assert latest == row
    assert sha256_hex(legacy_path.read_bytes()) == original


@pytest.mark.parametrize(
    "updates",
    [
        {"from_state": "acquired"},
        {"to_state": "acquired"},
        {"document_id": "invented:transcript"},
        {"accession": None},
        {"exhibit": None},
        {"artifact_sha256": None},
        {"retrieved_at": None},
        {"doc_id": None},
        {"recorded_at": "2026-10-06T00:00:00+01:00"},
        {"recorded_at": "2026-10-06T00:00:00"},
        {"retrieved_at": "2026-10-06T00:00:00+01:00"},
        {"failure_reason": FailureReason.PARSE_FAILED.value},
        {"missing_reason": "parse_failed"},
        {"missing_reason": None},
        {"processing_reason": None},
        {"processing_reason": "arbitrary source wording"},
        {"processing_reason": FailureReason.NO_NATIVE_TEXT.value},
        {"schema_version": 1},
        {"schema_version": True},
        {"schema_version": 2.0},
        {"sequence": True},
        {"sequence": 1.0},
        {"processing_run_hash": "invalid"},
        {"completion_hash": None},
        {"to_state": "completed", "missing_reason": "policy_review"},
        {
            "to_state": "completed",
            "missing_reason": None,
            "processing_reason": "unexpected_error",
        },
        {
            "to_state": "completed-no-theme",
            "missing_reason": None,
            "processing_reason": None,
        },
        {"to_state": "partial", "missing_reason": None},
        {"to_state": "partial", "missing_reason": "processing_failed"},
        {
            "to_state": "partial",
            "missing_reason": "policy_review",
            "processing_reason": "explicit_no_theme",
        },
    ],
    ids=[f"invalid_{n}" for n in range(30)],
)
def test_invalid_processing_metadata_refuses(updates):
    with pytest.raises(ValidationError):
        processing(**updates)


@pytest.mark.parametrize(
    "field,value",
    [
        ("pilot_hash", "f" * 64),
        ("pilot_id", "other-pilot"),
        ("pilot_version", 2),
        ("doc_id", "other-doc"),
        ("frozen_accession", "0009990001-25-000001"),
        ("accession", "0009990001-25-000001"),
        ("exhibit", "other.htm"),
        ("artifact_sha256", "f" * 64),
        ("retrieved_at", AT.isoformat()),
        ("override_id", "new-override"),
        ("corpus_error", "new error"),
        ("event_id", "other-event"),
    ],
    ids=[
        "pilot_hash",
        "pilot_id",
        "pilot_version",
        "doc_id",
        "frozen_accession",
        "accession",
        "exhibit",
        "raw_hash",
        "retrieval",
        "override",
        "corpus",
        "event",
    ],
)
def test_processing_copies_exact_current_predecessor(tmp_path, field, value):
    state_table.write_run(tmp_path, acquisition())
    updates = {field: value}
    if field == "event_id":
        updates["document_id"] = "other-event:release"
    row = processing(**updates)
    with pytest.raises(ValueError):
        state_table.write_processing_run(tmp_path, [row])
    assert len(list(tmp_path.glob("*.parquet"))) == 1


def test_processing_preserves_retained_override_history(tmp_path):
    history = acquisition()
    before = parsed()
    changed = [
        t.model_copy(
            update={
                "override_id": "retained-override",
                "corpus_error": "retained-error",
            }
        )
        if t.document_id == before.document_id
        else t
        for t in history
    ]
    state_table.write_run(tmp_path, changed)
    row = processing(override_id="retained-override", corpus_error="retained-error")
    state_table.write_processing_run(tmp_path, [row])
    rows = state_table.read_runs(tmp_path)
    assert len(rows) == len(changed) + 1
    assert rows[-1].attempts == ()
    assert sum(len(t.attempts) for t in rows) == sum(len(t.attempts) for t in changed)
    assert rows[-1].override_id == "retained-override"


def test_processing_refuses_new_attempts():
    with pytest.raises(ValidationError):
        processing(attempts=[parsed().attempts[0].model_dump(mode="json")])


def test_duplicate_positions_and_forged_models_refuse_before_write(tmp_path):
    state_table.write_run(tmp_path, acquisition())
    row = processing()
    with pytest.raises(ValueError):
        state_table.write_processing_run(tmp_path, [row, row])
    forged = row.model_copy(update={"from_state": states.DocumentState.EXPECTED})
    with pytest.raises(ValueError):
        state_table.write_processing_run(tmp_path, [forged])
    assert len(list(tmp_path.glob("*.parquet"))) == 1


def test_identical_processing_retry_is_idempotent_other_bytes_refuse(tmp_path):
    state_table.write_run(tmp_path, acquisition())
    row = processing()
    path = state_table.write_processing_run(tmp_path, [row])
    before = sha256_hex(path.read_bytes())
    assert state_table.write_processing_run(tmp_path, [row]) == path
    assert sha256_hex(path.read_bytes()) == before
    with pytest.raises(FileExistsError, match="state_run_conflict"):
        state_table.write_processing_run(
            tmp_path, [processing(completion_hash="f" * 64)]
        )


@pytest.mark.parametrize(
    "outcome",
    ["failed", "partial", "completed", "completed-no-theme"],
    ids=["failed", "partial", "completed", "no_theme"],
)
def test_other_processing_run_cannot_reopen_final_outcome(tmp_path, outcome):
    state_table.write_run(tmp_path, acquisition())
    metadata = {
        "failed": {},
        "partial": {
            "missing_reason": "policy_review",
            "processing_reason": "policy_review",
        },
        "completed": {"missing_reason": None, "processing_reason": None},
        "completed-no-theme": {
            "missing_reason": None,
            "processing_reason": "explicit_no_theme",
        },
    }
    first = processing(to_state=outcome, **metadata[outcome])
    state_table.write_processing_run(tmp_path, [first])
    retry = processing(
        run_id="processing-2",
        processing_run_id="workflow-2",
        recorded_at=(AT + timedelta(hours=1)).isoformat(),
    )
    with pytest.raises(ValueError, match="state_not_processable"):
        state_table.write_processing_run(tmp_path, [retry])
    assert len(list(tmp_path.glob("*.parquet"))) == 2


def test_processing_failure_cannot_reopen_with_legacy_acquisition_override(tmp_path):
    history = acquisition()
    row = processing()
    acquired = next(
        t
        for t in history
        if t.document_id == row.document_id
        and t.to_state is states.DocumentState.ACQUIRED
    )
    reopened = acquired.model_copy(
        update={
            "run_id": "later-acquisition",
            "sequence": 0,
            "recorded_at": AT + timedelta(hours=1),
            "from_state": states.DocumentState.FAILED,
            "override_id": "new-override",
        }
    )
    with pytest.raises(ValueError, match="state_not_processable"):
        states.check_histories([*history, row, reopened])


def test_schema_one_writer_bytes_and_fixture_are_preserved(tmp_path):
    permitted = tuple(
        REPO / FIXTURE_DIR / name
        for name in (
            ACQUISITION,
            "events-v1.json",
            "events-v1.evidence.json",
            "pilot-v1.json",
        )
    )
    before = tuple(sha256_hex(path.read_bytes()) for path in permitted)
    history = acquisition()
    buffer = io.BytesIO()
    pl.DataFrame(
        [t.model_dump(mode="python") for t in history],
        schema=state_table.SCHEMA,
        orient="row",
    ).write_parquet(buffer)
    path = state_table.write_run(tmp_path, history)
    assert sha256_hex(path.read_bytes()) == sha256_hex(buffer.getvalue())
    assert all(
        type(t) is states.StateTransition for t in state_table.read_runs(tmp_path)
    )
    assert tuple(sha256_hex(path.read_bytes()) for path in permitted) == before


def test_processing_table_retains_all_null_column_types(tmp_path):
    state_table.write_run(tmp_path, acquisition())
    row = processing(to_state="completed", missing_reason=None, processing_reason=None)
    path = state_table.write_processing_run(tmp_path, [row])
    frame = pl.read_parquet(path)
    assert frame.schema == state_table.PROCESSING_SCHEMA
    for name in (
        "missing_reason",
        "failure_reason",
        "processing_reason",
        "override_id",
        "corpus_error",
    ):
        assert frame.schema[name] == pl.String
        assert frame[name].null_count() == 1


@pytest.mark.parametrize(
    "alteration",
    [
        "version",
        "mixed_version",
        "extra_column",
        "wrong_dtype",
        "forged",
        "wrong_filename",
    ],
    ids=[
        "version",
        "mixed_version",
        "extra_column",
        "wrong_dtype",
        "forged",
        "wrong_filename",
    ],
)
def test_reader_refuses_schema_version_and_state_data_forgery(tmp_path, alteration):
    state_table.write_run(tmp_path, acquisition())
    path = state_table.write_processing_run(tmp_path, [processing()])
    frame = pl.read_parquet(path)
    if alteration == "version":
        frame = frame.with_columns(pl.lit(3, dtype=pl.Int64).alias("schema_version"))
    elif alteration == "mixed_version":
        frame = pl.concat(
            [
                frame,
                frame.with_columns(pl.lit(1).cast(pl.Int64).alias("schema_version")),
            ]
        )
    elif alteration == "extra_column":
        frame = frame.with_columns(pl.lit(None, dtype=pl.String).alias("extra"))
    elif alteration == "wrong_dtype":
        frame = frame.with_columns(pl.col("completion_hash").cast(pl.Categorical))
    elif alteration == "forged":
        frame = frame.with_columns(pl.lit("untrusted source text").alias("doc_id"))
    else:
        path.rename(tmp_path / "untrusted source wording.parquet")
    if alteration != "wrong_filename":
        frame.write_parquet(path)
    with pytest.raises(ValueError) as caught:
        state_table.read_runs(tmp_path)
    assert str(caught.value) in {
        "state_storage_corrupt",
        "state_schema_invalid",
        "state_record_invalid",
        "state_history_invalid",
    }
    assert caught.value.__cause__ is None


def test_schema_two_cannot_write_acquisition_or_empty_run(tmp_path):
    assert getattr(state_table, "write_processing_run", None) is not None
    with pytest.raises(ValueError):
        state_table.write_processing_run(tmp_path, acquisition())
    with pytest.raises(ValueError):
        state_table.write_processing_run(tmp_path, [])


@pytest.mark.parametrize(
    "hash_value", [HASH, "f" * 64], ids=["same_hash", "other_hash"]
)
def test_processing_run_binding_cannot_alias_another_state_file(tmp_path, hash_value):
    state_table.write_run(tmp_path, acquisition())
    state_table.write_processing_run(tmp_path, [processing()])
    alias = processing(
        run_id="alias-run",
        processing_run_hash=hash_value,
        recorded_at=(AT + timedelta(hours=1)).isoformat(),
    )
    with pytest.raises(FileExistsError, match="state_run_conflict"):
        state_table.write_processing_run(tmp_path, [alias])
    assert len(list(tmp_path.glob("*.parquet"))) == 2


def test_pinned_processing_vocabulary_covers_upstream_failures_without_runtime_import():
    from earnings_core import RejectionReason
    from earnings_themes.coding.records import CodingProblem
    from earnings_themes.extraction.records import ExtractionProblem
    from earnings_themes.support.problems import SupportProblem

    reasons = {r.value for r in states.ProcessingReason}
    expected = (
        {r.value for r in states.ProcessingMissingReason}
        | {"explicit_no_theme", "unexpected_error", "storage_corrupt", "input_changed"}
        | {
            r.value
            for enum in (
                RejectionReason,
                CodingProblem,
                ExtractionProblem,
                SupportProblem,
            )
            for r in enum
        }
    )
    assert reasons == expected
    assert not reasons & {r.value for r in FailureReason}
