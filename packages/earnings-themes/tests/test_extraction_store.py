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
    with pytest.raises(ValueError, match="^storage_corrupt$"):
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
    with pytest.raises(ValueError, match="^storage_corrupt$"):
        read_run(target)


def test_a_refused_row_has_a_fixed_error_without_source_fields(
    synthetic, template, tmp_path: Path
) -> None:
    """GS13: storage refusals never include a field, value, or exception chain."""
    run = stored([synthetic.bundle], synthetic_reply, template)
    target = write_run(tmp_path / "run-1", run, [synthetic.bundle])
    claims = target / "claims.parquet"
    frame = pl.read_parquet(claims)
    frame.with_columns(
        pl.lit(SENTINEL).alias("claim"),
        pl.lit([], dtype=pl.List(pl.String)).alias("quote_ids"),
    ).write_parquet(claims)
    with pytest.raises(ValueError, match="^storage_corrupt$") as refused:
        read_run(target)
    assert refused.value.__suppress_context__
    assert SENTINEL not in str(refused.value)

    # A model's own check can name a value too: a quote's ID, and a reason's key.
    named = write_run(tmp_path / "run-2", run, [synthetic.bundle])
    quotes = named / "quotes.parquet"
    frame = pl.read_parquet(quotes)
    frame.with_columns(pl.lit(SENTINEL).alias("quote_id")).write_parquet(quotes)
    with pytest.raises(ValueError, match="^storage_corrupt$") as refused_id:
        read_run(named)
    id_message = str(refused_id.value)
    assert refused_id.value.__suppress_context__
    assert SENTINEL not in id_message

    keyed = write_run(tmp_path / "run-3", run, [synthetic.bundle])
    record = json.loads((keyed / RUN_FILE).read_text(encoding="utf-8"))
    record["rejections_by_reason"][SENTINEL] = 1
    (keyed / RUN_FILE).write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="^storage_corrupt$") as refused_key:
        read_run(keyed)
    key_message = str(refused_key.value)
    assert refused_key.value.__suppress_context__
    assert SENTINEL not in key_message


def test_the_run_file_is_the_run_record(synthetic, template, tmp_path: Path) -> None:
    run = stored([synthetic.bundle], synthetic_reply, template)
    target = write_run(tmp_path / "run-1", run, [synthetic.bundle])
    record = RunRecord.model_validate_json((target / RUN_FILE).read_bytes())
    assert record == run.record


def validate(run):
    from earnings_themes.extraction import validate_stored_run

    return validate_stored_run(run)


def test_valid_gate_reconstructs_nested_models(case):
    _, _, run = case
    checked = validate(run)
    assert checked is not run
    assert checked.record is not run.record
    assert checked.record.run_id == run.record.run_id
    assert checked.record.configuration_hash == run.record.configuration_hash
    assert checked.record.documents == run.record.documents
    for kind in SCHEMAS:
        original_rows = getattr(run, kind)
        checked_rows = getattr(checked, kind)
        assert len(checked_rows) == len(original_rows)
        assert all(
            left is not right
            for left, right in zip(checked_rows, original_rows, strict=True)
        )
    assert tuple(
        (
            quote.span.doc_id,
            quote.quote_id,
            quote.span.canonical_hash,
            quote.span.start,
            quote.span.end,
        )
        for quote in checked.quotes
    ) == tuple(
        (
            quote.span.doc_id,
            quote.quote_id,
            quote.span.canonical_hash,
            quote.span.start,
            quote.span.end,
        )
        for quote in run.quotes
    )


@pytest.mark.parametrize(
    "defect",
    [
        "document-duplicate",
        "document-map",
        "document-hash",
        "document-count",
        "window-duplicate",
        "window-document",
        "visit-duplicate",
        "visit-order",
        "visit-outcome",
        "quote-duplicate",
        "quote-document",
        "quote-hash",
        "claim-duplicate",
        "claim-window",
        "claim-attempt",
        "claim-link",
        "candidate-count",
        "reason-count",
        "usage",
        "configuration-hash",
        "nested-construct",
        "nested-copy",
        "bool-count",
        "empty-links",
    ],
    ids=lambda value: value,
)
def test_gate_refuses_forged_relations(synthetic, template, defect):
    from earnings_themes.extraction.records import Claim, WindowOutcome

    run = stored([synthetic.bundle], synthetic_reply, template)
    document, window, visit, quote, claim = (
        run.documents[0],
        run.windows[0],
        run.visits[0],
        run.quotes[0],
        run.claims[0],
    )
    if defect == "document-duplicate":
        bad = replace(run, documents=run.documents * 2)
    elif defect == "document-map":
        bad = replace(run, record=run.record.model_copy(update={"documents": {}}))
    elif defect == "document-hash":
        bad = replace(
            run, documents=(document.model_copy(update={"canonical_hash": "a" * 64}),)
        )
    elif defect == "document-count":
        bad = replace(
            run, documents=(document.model_copy(update={"windows_failed": 1}),)
        )
    elif defect == "window-duplicate":
        bad = replace(run, windows=run.windows * 2)
    elif defect == "window-document":
        bad = replace(run, windows=(window.model_copy(update={"doc_id": SENTINEL}),))
    elif defect == "visit-duplicate":
        bad = replace(run, visits=run.visits + (visit,))
    elif defect == "visit-order":
        bad = replace(run, visits=tuple(reversed(run.visits)))
    elif defect == "visit-outcome":
        bad = replace(
            run,
            visits=(
                visit.model_copy(
                    update={
                        "outcome": WindowOutcome.FAILED,
                        "reason": ExtractionProblem.REPLAY_MISS,
                    }
                ),
                *run.visits[1:],
            ),
        )
    elif defect == "quote-duplicate":
        bad = replace(run, quotes=run.quotes + (quote,))
    elif defect in {"quote-document", "quote-hash"}:
        key, value = (
            ("doc_id", SENTINEL)
            if defect == "quote-document"
            else ("canonical_hash", "a" * 64)
        )
        bad_quote = quote.model_copy(
            update={"span": quote.span.model_copy(update={key: value})}
        )
        bad = replace(run, quotes=(bad_quote, *run.quotes[1:]))
    elif defect == "claim-duplicate":
        bad = replace(run, claims=run.claims + (claim,))
    elif defect == "claim-window":
        bad = replace(
            run,
            claims=(
                claim.model_copy(
                    update={"window_id": "w-0-1", "claim_id": "c-0-1-1-0"}
                ),
                *run.claims[1:],
            ),
        )
    elif defect == "claim-attempt":
        bad = replace(
            run,
            claims=(
                claim.model_copy(
                    update={
                        "attempt": 2,
                        "claim_id": claim.claim_id.replace("-1-", "-2-"),
                    }
                ),
                *run.claims[1:],
            ),
        )
    elif defect == "claim-link":
        bad = replace(
            run,
            claims=(
                claim.model_copy(update={"quote_ids": ("q-0-1",)}),
                *run.claims[1:],
            ),
        )
    elif defect == "candidate-count":
        bad = replace(
            run,
            documents=(
                document.model_copy(update={"candidates": document.candidates + 1}),
            ),
        )
    elif defect == "reason-count":
        bad = replace(
            run, record=run.record.model_copy(update={"rejections_by_reason": {}})
        )
    elif defect == "usage":
        bad = replace(run, record=run.record.model_copy(update={"prompt_tokens": 1}))
    elif defect == "configuration-hash":
        bad = replace(
            run, record=run.record.model_copy(update={"configuration_hash": "a" * 64})
        )
    elif defect == "nested-construct":
        fields = claim.model_dump()
        fields["attempt"] = True
        bad = replace(run, claims=(Claim.model_construct(**fields), *run.claims[1:]))
    elif defect == "nested-copy":
        bad = replace(
            run,
            quotes=(
                quote.model_copy(
                    update={"span": quote.span.model_copy(update={"start": True})}
                ),
                *run.quotes[1:],
            ),
        )
    elif defect == "bool-count":
        bad = replace(run, documents=(document.model_copy(update={"units": True}),))
    else:
        bad = replace(
            run, claims=(claim.model_copy(update={"quote_ids": ()}), *run.claims[1:])
        )
    with pytest.raises(ValueError, match="^malformed_record$") as raised:
        validate(bad)
    assert SENTINEL not in str(raised.value)
    assert raised.value.__suppress_context__


@pytest.mark.parametrize(
    "defect",
    ["missing", "directory-symlink", "file-symlink", "corrupt", "forged-row"],
    ids=lambda value: value,
)
def test_storage_errors_are_fixed(synthetic, template, tmp_path, defect):
    run = stored([synthetic.bundle], synthetic_reply, template)
    target = write_run(tmp_path / "run-1", run, [synthetic.bundle])
    if defect == "missing":
        (target / "run.json").unlink()
    elif defect == "directory-symlink":
        link = tmp_path / SENTINEL
        link.symlink_to(target, target_is_directory=True)
        target = link
    elif defect == "file-symlink":
        saved = tmp_path / "saved.json"
        (target / "run.json").rename(saved)
        (target / "run.json").symlink_to(saved)
    elif defect == "corrupt":
        (target / "quotes.parquet").write_bytes(SENTINEL.encode())
    else:
        path = target / "windows.parquet"
        pl.read_parquet(path).with_columns(
            pl.lit(SENTINEL).alias("doc_id")
        ).write_parquet(path)
    with pytest.raises(ValueError, match="^storage_corrupt$") as raised:
        read_run(target)
    assert SENTINEL not in str(raised.value)
    assert raised.value.__suppress_context__


def test_writer_calls_structural_gate_before_publication(synthetic, template, tmp_path):
    run = stored([synthetic.bundle], synthetic_reply, template)
    bad = replace(run, windows=run.windows * 2)
    with pytest.raises(ValueError, match="^malformed_record$"):
        write_run(tmp_path / SENTINEL, bad, [synthetic.bundle])
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "field",
    [
        "units",
        "windows",
        "candidates",
        "quotes",
        "claims",
        "requests",
        "cache_hits",
        "prompt_tokens",
        "completion_tokens",
        "unreported",
        "exhausted",
    ],
    ids=lambda value: value,
)
def test_all_run_totals_are_bound(synthetic, template, field):
    run = stored([synthetic.bundle], synthetic_reply, template)
    value = (
        not run.record.exhausted
        if field == "exhausted"
        else getattr(run.record, field) + 1
    )
    bad = replace(run, record=run.record.model_copy(update={field: value}))
    with pytest.raises(ValueError, match="^malformed_record$"):
        validate(bad)


@pytest.mark.parametrize(
    "field",
    [
        "units",
        "windows",
        "windows_failed",
        "candidates",
        "quotes",
        "claims",
        "rejections",
    ],
    ids=lambda value: value,
)
def test_all_document_totals_are_bound(synthetic, template, field):
    run = stored([synthetic.bundle], synthetic_reply, template)
    document = run.documents[0]
    bad = replace(
        run,
        documents=(document.model_copy(update={field: getattr(document, field) + 1}),),
    )
    with pytest.raises(ValueError, match="^malformed_record$"):
        validate(bad)


@pytest.mark.parametrize(
    "defect",
    ["document", "window", "attempt", "candidate-duplicate", "unknown-reason"],
    ids=lambda value: value,
)
def test_rejections_are_bound_to_current_run(synthetic, template, defect):
    run = stored([synthetic.bundle], synthetic_reply, template)
    rejection = run.rejections[0]
    changes = {
        "document": {"doc_id": SENTINEL},
        "window": {"window_id": "w-0-1"},
        "attempt": {"attempt": 2},
        "unknown-reason": {"problem": SENTINEL, "rejection": None},
    }
    rows = (
        run.rejections * 2
        if defect == "candidate-duplicate"
        else (rejection.model_copy(update=changes[defect]), *run.rejections[1:])
    )
    with pytest.raises(ValueError, match="^malformed_record$"):
        validate(replace(run, rejections=rows))


def test_publication_exception_is_guarded(synthetic, template, tmp_path, monkeypatch):
    import earnings_themes.extraction.store as store_module

    run = stored([synthetic.bundle], synthetic_reply, template)

    def refused(*args):
        raise RuntimeError(SENTINEL)

    monkeypatch.setattr(store_module, "refused_quotes", refused)
    with pytest.raises(ValueError, match="^malformed_record$") as raised:
        write_run(tmp_path / "run", run, [synthetic.bundle])
    assert raised.value.__suppress_context__
    assert not list(tmp_path.iterdir())


def test_writer_refuses_symlink_or_parent_traversal(synthetic, template, tmp_path):
    run = stored([synthetic.bundle], synthetic_reply, template)
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / SENTINEL
    link.symlink_to(real, target_is_directory=True)
    for target in (link / "run", real / ".." / "run"):
        with pytest.raises(ValueError, match="^storage_corrupt$"):
            write_run(target, run, [synthetic.bundle])
    assert not list(real.iterdir())


@pytest.mark.parametrize(
    "doc_id",
    [
        "/private/tmp/SENTINEL-TEXT-NEVER-PRINTED",
        "https://invented.example/SENTINEL-TEXT-NEVER-PRINTED",
        "SENTINEL-TEXT-NEVER-PRINTED",
    ],
    ids=["path", "url", "alphanumeric"],
)
def test_consistently_forged_identifiers_never_print(
    synthetic, template, tmp_path, doc_id
):
    run = stored([synthetic.bundle], synthetic_reply, template)
    forged = replace(
        run,
        record=run.record.model_copy(
            update={"documents": {doc_id: run.documents[0].canonical_hash}}
        ),
        documents=tuple(
            row.model_copy(update={"doc_id": doc_id}) for row in run.documents
        ),
        windows=tuple(row.model_copy(update={"doc_id": doc_id}) for row in run.windows),
        visits=tuple(row.model_copy(update={"doc_id": doc_id}) for row in run.visits),
        quotes=tuple(
            row.model_copy(
                update={"span": row.span.model_copy(update={"doc_id": doc_id})}
            )
            for row in run.quotes
        ),
        claims=tuple(row.model_copy(update={"doc_id": doc_id}) for row in run.claims),
        rejections=tuple(
            row.model_copy(update={"doc_id": doc_id}) for row in run.rejections
        ),
    )
    checked = validate(forged)
    assert len(checked.quotes) == len(run.quotes)
    with pytest.raises(StorageRefused) as raised:
        write_run(tmp_path / "run", checked, [synthetic.bundle])
    assert len(raised.value.refused) == len(run.quotes)
    assert SENTINEL not in str(raised.value)
    assert SENTINEL not in repr(raised.value)
    assert "wrong_document" in str(raised.value)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "reason,exhausted",
    [
        (None, False),
        (ExtractionProblem.REPLAY_MISS, False),
        (ExtractionProblem.BUDGET_EXHAUSTED, False),
    ],
    ids=["completed", "replay", "budget-not-exhausted"],
)
def test_stored_run_refuses_impossible_zero_attempt(
    synthetic, template, reason, exhausted
):
    from earnings_themes.extraction.records import DocumentOutcome, WindowOutcome

    run = stored(
        [synthetic.bundle],
        lambda _: ModelReply(text='{"candidates": []}', model="scripted"),
        template,
    )
    outcome = WindowOutcome.COMPLETED if reason is None else WindowOutcome.FAILED
    failed = int(reason is not None)
    forged = replace(
        run,
        record=run.record.model_copy(
            update={"requests": 0, "unreported": 0, "exhausted": exhausted}
        ),
        documents=(
            run.documents[0].model_copy(
                update={
                    "windows_failed": failed,
                    "outcome": DocumentOutcome.FAILED
                    if failed
                    else DocumentOutcome.COMPLETED,
                }
            ),
        ),
        windows=(
            run.windows[0].model_copy(
                update={
                    "attempts": 0,
                    "requests": 0,
                    "unreported": 0,
                    "outcome": outcome,
                    "reason": reason,
                    "exhausted": exhausted,
                }
            ),
        ),
        visits=tuple(
            visit.model_copy(update={"outcome": outcome, "reason": reason})
            for visit in run.visits
        ),
    )
    with pytest.raises(ValueError, match="^malformed_record$"):
        validate(forged)


@pytest.mark.parametrize("mode", ["budget", "replay"], ids=["budget", "replay"])
def test_gate_preserves_actual_budget_stop_and_replay_miss(
    synthetic, template, tmp_path, mode
):
    from earnings_themes.extraction.cache import CachedAdapter, CacheMode
    from earnings_themes.extraction.records import WindowOutcome

    adapter = ScriptedAdapter(
        lambda _: ModelReply(text='{"candidates": []}', model="scripted")
    )
    if mode == "replay":
        adapter = CachedAdapter(
            ScriptedAdapter(lambda _: pytest.fail("replay_dispatch_forbidden")),
            tmp_path / "cache",
            CacheMode.REPLAY,
        )
    result = extract_run(
        [synthetic.bundle],
        adapter,
        ExtractionPolicy(window_budget=40),
        template,
        Ceilings(requests_per_document=1, requests_per_run=1, tokens_per_run=1000),
        run_id="run-compatibility",
        started_at=datetime(2026, 10, 4, 12, tzinfo=UTC),
        software={"earnings-themes": "0.1.0"},
    )
    checked = validate(StoredRun.of(result))
    failed = tuple(
        window for window in checked.windows if window.outcome is WindowOutcome.FAILED
    )
    assert len(failed) > 0
    if mode == "budget":
        assert all(
            window.attempts == 0
            and window.exhausted
            and window.reason is ExtractionProblem.BUDGET_EXHAUSTED
            for window in failed
        )
        assert checked.record.requests == 1
    else:
        assert all(
            window.attempts == 2
            and not window.exhausted
            and window.reason is ExtractionProblem.REPLAY_MISS
            for window in failed
        )
        assert checked.record.requests == 0
    target = write_run(tmp_path / "run", checked, [synthetic.bundle])
    loaded = read_run(target)
    assert loaded.record.configuration_hash == checked.record.configuration_hash
    assert loaded.record.requests == checked.record.requests
    assert tuple(window.attempts for window in loaded.windows) == tuple(
        window.attempts for window in checked.windows
    )


def test_public_refusal_formatter_closes_untrusted_reason():
    refused = StorageRefused((("invented-doc", "q-0-5", SENTINEL),))
    assert SENTINEL not in str(refused)
    assert SENTINEL not in repr(refused)
    assert "malformed_record" in str(refused)
