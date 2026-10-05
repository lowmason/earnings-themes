"""The run store (the Stage 7 spec, §Storage; R6.1, R6.2; ES6): every quote verified
again before anything is written, one Parquet file per record kind under an explicit
schema, and a run read back record for record. Runs are written to temporary
directories only."""

import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import polars as pl
import pytest
from earnings_core import CanonicalDocument, OverlayMask, Rejection, VerifiedSpan
from earnings_themes.extraction.adapters import ModelReply, ScriptedAdapter
from earnings_themes.extraction.records import (
    Ceilings,
    ExtractionPolicy,
    ExtractionProblem,
    RunRecord,
)
from earnings_themes.extraction.run import extract_run
from earnings_themes.extraction.store import (
    REJECTION,
    RUN_FILE,
    SCHEMAS,
    VERIFIED_SPAN,
    StorageRefused,
    StoredRun,
    read_run,
    write_run,
)
from earnings_themes.records import RecordError

POLICY = ExtractionPolicy()
WIDE = Ceilings(
    requests_per_document=1_000, requests_per_run=10_000, tokens_per_run=10**9
)
SENTINEL = "SENTINEL-TEXT-NEVER-PRINTED"


def stored(bundles, script, template) -> StoredRun:
    result = extract_run(
        list(bundles),
        ScriptedAdapter(script),
        POLICY,
        template,
        WIDE,
        run_id="run-1",
        started_at=datetime(2026, 10, 4, 12, tzinfo=UTC),
        software={"earnings-themes": "0.1.0"},
    )
    return StoredRun.of(result)


def synthetic_reply(_) -> ModelReply:
    """U2 with U5, which verification refuses as OCR text; U6, under a mask; and
    U4, whose text repeats, so its quote carries context."""
    candidates = [
        {"quote_labels": ["U2", "U5"], "claim": "Two units."},
        {"quote_labels": ["U6"], "claim": "Boilerplate."},
        {"quote_labels": ["U4"], "claim": "A repeat."},
    ]
    return ModelReply(text=json.dumps({"candidates": candidates}), model="scripted")


def refused_bundle(synthetic):
    """The synthetic bundle with its mask moved to another document, which
    ``bundle_problems`` refuses (T6-M4)."""
    other = CanonicalDocument.create(
        source_document_id="0009990002-25-000001_ex991.htm",
        canonicalization_version="walker-1",
        canonical_text="Invented text.\n",
    )
    (mask,) = synthetic.bundle.masks
    fields = {name: getattr(mask, name) for name in OverlayMask.model_fields}
    fields |= {"doc_id": other.doc_id, "canonical_hash": other.canonical_hash}
    return replace(synthetic.bundle, masks=(OverlayMask(**fields),))


@pytest.fixture(params=["fixtures", "synthetic", "refused"])
def case(request, fixtures, synthetic, template, mixed):
    """Three runs: the mixed run over the fixtures, with problems of every kind; the
    synthetic document's, with a verification rejection, a masked quote, and a quote
    with context; and a refused document's, whose other files are empty."""
    if request.param == "fixtures":
        bundles = list(fixtures.values())
        script = mixed(bundles, POLICY.window_budget)
    else:
        refused = request.param == "refused"
        bundles = [refused_bundle(synthetic) if refused else synthetic.bundle]
        script = synthetic_reply
    return request.param, bundles, stored(bundles, script, template)


def test_a_run_reads_back_record_for_record(case, tmp_path: Path) -> None:
    _, bundles, run = case
    written = write_run(tmp_path / "run-1", run, bundles)
    assert sorted(p.name for p in written.iterdir()) == sorted(
        [RUN_FILE, *(f"{kind}.parquet" for kind in SCHEMAS)]
    )
    same = read_run(written) == run
    assert same


def test_each_case_holds_what_its_round_trip_covers(case) -> None:
    name, _, run = case
    cores = [r.rejection.reason.value for r in run.rejections if r.rejection]
    if name == "fixtures":
        assert {r.problem for r in run.rejections} == {
            ExtractionProblem.BLANK_CLAIM,
            ExtractionProblem.MALFORMED_REPLY,
            ExtractionProblem.TOOL_CALL_REFUSED,
            ExtractionProblem.TRANSPORT_ERROR,
            ExtractionProblem.UNKNOWN_LABEL,
        }
        assert any(w.context_id for w in run.windows)
        assert any(v.reason for v in run.visits)
    elif name == "synthetic":
        assert cores == ["ocr_derived_text"]
        assert any(q.mask_ids for q in run.quotes)
        assert any(q.span.prefix or q.span.suffix for q in run.quotes)
    else:
        assert cores == ["wrong_document"]
        assert (run.windows, run.quotes, run.claims, run.visits) == ((), (), (), ())


def tampered(run: StoredRun) -> StoredRun:
    """``run`` with its first quote's text changed beneath its offsets."""
    first, *rest = run.quotes
    span = first.span.model_copy(update={"quote_text": SENTINEL})
    return replace(run, quotes=(first.model_copy(update={"span": span}), *rest))


def test_a_quote_that_fails_again_stops_the_write(
    synthetic, template, tmp_path: Path
) -> None:
    """R6.1 before storage: nothing is written, and the refusal names the quote by
    its IDs and reason, never its text (GS13)."""
    run = stored([synthetic.bundle], synthetic_reply, template)
    target = tmp_path / "run-1"
    with pytest.raises(StorageRefused) as refused:
        write_run(target, tampered(run), [synthetic.bundle])
    first = run.quotes[0]
    assert refused.value.refused == (
        (first.span.doc_id, first.quote_id, "quote_text_mismatch"),
    )
    assert SENTINEL not in str(refused.value)
    assert list(tmp_path.iterdir()) == []


def test_a_quote_of_a_document_with_no_bundle_is_refused(
    synthetic, template, tmp_path: Path
) -> None:
    run = stored([synthetic.bundle], synthetic_reply, template)
    with pytest.raises(StorageRefused) as refused:
        write_run(tmp_path / "run-1", run, [])
    assert {reason for _, _, reason in refused.value.refused} == {"wrong_document"}
    assert list(tmp_path.iterdir()) == []


def test_a_run_is_never_overwritten(synthetic, template, tmp_path: Path) -> None:
    run = stored([synthetic.bundle], synthetic_reply, template)
    target = write_run(tmp_path / "run-1", run, [synthetic.bundle])
    before = {p.name: p.read_bytes() for p in target.iterdir()}
    with pytest.raises(FileExistsError):
        write_run(target, run, [synthetic.bundle])
    assert {p.name: p.read_bytes() for p in target.iterdir()} == before
    assert [p.name for p in tmp_path.iterdir()] == ["run-1"]


def test_a_write_that_fails_midway_leaves_nothing(
    synthetic, template, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = stored([synthetic.bundle], synthetic_reply, template)

    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("the disk is full")

    monkeypatch.setattr(pl.DataFrame, "write_parquet", fail)
    with pytest.raises(OSError, match="the disk is full"):
        write_run(tmp_path / "run-1", run, [synthetic.bundle])
    assert list(tmp_path.iterdir()) == []


def test_each_schema_names_its_models_fields_in_order() -> None:
    """A field a model gains, and its schema lacks, would be dropped on write."""
    for model, schema in SCHEMAS.values():
        assert list(schema.names()) == list(model.model_fields)
    assert [f.name for f in VERIFIED_SPAN.fields] == list(VerifiedSpan.model_fields)
    assert [f.name for f in REJECTION.fields] == list(Rejection.model_fields)


def test_a_file_of_another_schema_is_refused(
    synthetic, template, tmp_path: Path
) -> None:
    run = stored([synthetic.bundle], synthetic_reply, template)
    target = write_run(tmp_path / "run-1", run, [synthetic.bundle])
    visits = target / "visits.parquet"
    pl.read_parquet(visits).drop("reason").write_parquet(visits)
    with pytest.raises(ValueError, match="visits.parquet does not have the visits"):
        read_run(target)


def test_a_refused_row_is_named_by_file_row_and_field(
    synthetic, template, tmp_path: Path
) -> None:
    """GS13: a stored record may quote a document, so a refusal names its file, row,
    and field, never a value: not a claim's words, a quote's ID, or a reason's key."""
    run = stored([synthetic.bundle], synthetic_reply, template)
    target = write_run(tmp_path / "run-1", run, [synthetic.bundle])
    claims = target / "claims.parquet"
    frame = pl.read_parquet(claims)
    frame.with_columns(
        pl.lit(SENTINEL).alias("claim"),
        pl.lit([], dtype=pl.List(pl.String)).alias("quote_ids"),
    ).write_parquet(claims)
    with pytest.raises(RecordError) as refused:
        read_run(target)
    assert refused.value.name == "claims.parquet row 0"
    assert [p.partition(":")[0] for p in refused.value.problems] == ["quote_ids"]
    assert SENTINEL not in str(refused.value)

    # A model's own check can name a value too: a quote's ID, and a reason's key.
    named = write_run(tmp_path / "run-2", run, [synthetic.bundle])
    quotes = named / "quotes.parquet"
    frame = pl.read_parquet(quotes)
    frame.with_columns(pl.lit(SENTINEL).alias("quote_id")).write_parquet(quotes)
    with pytest.raises(RecordError) as refused_id:
        read_run(named)
    id_message = str(refused_id.value)
    assert refused_id.value.name == "quotes.parquet row 0"
    assert SENTINEL not in id_message

    keyed = write_run(tmp_path / "run-3", run, [synthetic.bundle])
    record = json.loads((keyed / RUN_FILE).read_text(encoding="utf-8"))
    record["rejections_by_reason"][SENTINEL] = 1
    (keyed / RUN_FILE).write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(RecordError) as refused_key:
        read_run(keyed)
    key_message = str(refused_key.value)
    assert refused_key.value.name == RUN_FILE
    assert SENTINEL not in key_message


def test_the_run_file_is_the_run_record(synthetic, template, tmp_path: Path) -> None:
    run = stored([synthetic.bundle], synthetic_reply, template)
    target = write_run(tmp_path / "run-1", run, [synthetic.bundle])
    record = RunRecord.model_validate_json((target / RUN_FILE).read_bytes())
    assert record == run.record
