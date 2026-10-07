"""Publication tests read only explicitly created temporary invented bytes."""

import importlib
import importlib.util
import json
from dataclasses import replace

import pytest
from earnings_core import canonical_json, sha256_hex
from earnings_themes.analysis import AnalysisError, build_analysis


def store():
    assert importlib.util.find_spec("earnings_themes.analysis.store") is not None
    return importlib.import_module("earnings_themes.analysis.store")


def publish(tmp_path, inputs, families):
    result = build_analysis(inputs, inputs.analysis_policy, families)
    path = tmp_path / "analysis"
    store().write_analysis_run(
        path, result, inputs, inputs.analysis_policy, families, evidence=()
    )
    return path, result


def test_roundtrip_all_tables_and_empty_schemas(analysis_inputs, family_map, tmp_path):
    path, original = publish(tmp_path, analysis_inputs, family_map)
    saved = store().read_analysis_run(path)
    assert len(saved.tables.frames) == 14
    assert any(f.is_empty() for f in saved.tables.frames.values())
    for name, frame in original.tables.frames.items():
        assert saved.tables.frames[name].equals(frame)
        assert saved.tables.frames[name].schema == frame.schema
    assert saved.manifest_hash == sha256_hex((path / "run.json").read_bytes())
    store().reverify_analysis_run(
        saved, analysis_inputs, analysis_inputs.analysis_policy, family_map
    )


def test_changed_policy_refuses_before_any_publication(
    analysis_inputs, family_map, tmp_path
):
    result = build_analysis(
        analysis_inputs, analysis_inputs.analysis_policy, family_map
    )
    with pytest.raises(AnalysisError, match="^input_changed$"):
        store().write_analysis_run(
            tmp_path / "analysis",
            result,
            replace(analysis_inputs, assignment_policy=None),
            analysis_inputs.analysis_policy,
            family_map,
            evidence=(),
        )
    assert not (tmp_path / "analysis").exists()


@pytest.mark.parametrize(
    "change",
    ["policy", "family", "completion", "copy", "table"],
    ids=["policy", "family", "completion", "copy", "table"],
)
def test_stale_result_refuses(analysis_inputs, family_map, tmp_path, change):
    result = build_analysis(
        analysis_inputs, analysis_inputs.analysis_policy, family_map
    )
    if change == "table":
        frames = dict(result.tables.frames)
        frames["quotes"] = frames["quotes"].reverse()
        result = replace(result, tables=replace(result.tables, frames=frames))
    else:
        changes = {
            "policy": {"binding_hash": "0" * 64},
            "family": {"family_map": None},
            "completion": {"completion_hashes": ()},
            "copy": {"copy_hashes": ()},
        }[change]
        result = replace(result, record=result.record.model_copy(update=changes))
    with pytest.raises(AnalysisError):
        store().write_analysis_run(
            tmp_path / "analysis",
            result,
            analysis_inputs,
            analysis_inputs.analysis_policy,
            family_map,
            evidence=(),
        )
    assert not (tmp_path / "analysis").exists()


@pytest.mark.parametrize(
    "change",
    ["bytes", "filename", "symlink", "counts", "validator", "policy"],
    ids=["bytes", "filename", "symlink", "counts", "validator", "policy"],
)
def test_reader_refuses_corruption(analysis_inputs, family_map, tmp_path, change):
    path, _ = publish(tmp_path, analysis_inputs, family_map)
    manifest = path / "run.json"
    data = json.loads(manifest.read_bytes())
    if change == "bytes":
        with (path / "quotes.parquet").open("ab") as stream:
            stream.write(b"invented tamper")
    elif change == "symlink":
        target = path / "quotes.parquet"
        target.rename(tmp_path / "outside.parquet")
        target.symlink_to(tmp_path / "outside.parquet")
    else:
        if change == "filename":
            data["table_hashes"][0][0] = "../outside.parquet"
        elif change == "validator":
            data["validator_version"] = "invented-stale-validator"
        elif change == "policy":
            data["assignment_policy"] = None
        else:
            data["counts_by_state"] = [["completed", 999]]
        manifest.write_bytes(canonical_json(data))
    with pytest.raises(AnalysisError, match="^storage_corrupt$"):
        store().read_analysis_run(path)


@pytest.mark.parametrize(
    "failure", [OSError, FileExistsError], ids=["io-error", "foreign-file-exists"]
)
def test_existing_destination_and_own_cleanup(
    analysis_inputs, family_map, tmp_path, monkeypatch, failure
):
    path, result = publish(tmp_path, analysis_inputs, family_map)
    before = (path / "run.json").read_bytes()
    with pytest.raises(FileExistsError):
        store().write_analysis_run(
            path,
            result,
            analysis_inputs,
            analysis_inputs.analysis_policy,
            family_map,
            evidence=(),
        )
    assert (path / "run.json").read_bytes() == before
    import polars as pl

    def fail(*args, **kwargs):
        raise failure("invented private detail")

    monkeypatch.setattr(pl.DataFrame, "write_parquet", fail)
    with pytest.raises(AnalysisError, match="^storage_corrupt$"):
        store().write_analysis_run(
            tmp_path / "failed",
            result,
            analysis_inputs,
            analysis_inputs.analysis_policy,
            family_map,
            evidence=(),
        )
    assert not (tmp_path / "failed").exists()
    assert not list(tmp_path.glob(".failed-*"))


def test_evidence_reference_is_current_but_external_html_not_claimed(
    analysis_inputs, family_map, tmp_path
):
    from earnings_pipeline.evidence_views import make_evidence_view
    from earnings_themes.analysis import reverify_analysis_inputs

    bound = reverify_analysis_inputs(analysis_inputs)
    q = analysis_inputs.sources.stored_run.quotes[0]
    view = make_evidence_view(
        bound,
        q.span.doc_id,
        q.quote_id,
        audience="local",
        raw_snapshot=analysis_inputs.raw_snapshots[0],
    )
    result = build_analysis(
        analysis_inputs, analysis_inputs.analysis_policy, family_map
    )
    path = tmp_path / "evidence-analysis"
    store().write_analysis_run(
        path,
        result,
        analysis_inputs,
        analysis_inputs.analysis_policy,
        family_map,
        evidence=(view.reference,),
    )
    saved = store().read_analysis_run(path)
    assert saved.tables.frames["evidence"].height == 1
    assert len(saved.record.evidence_hashes) == 1
    assert not (path / "views").exists()
    store().reverify_analysis_run(
        saved, analysis_inputs, analysis_inputs.analysis_policy, family_map
    )
    altered = view.reference.model_copy(update={"quote_text_hash": "0" * 64})
    with pytest.raises(AnalysisError, match="^input_changed$"):
        store().write_analysis_run(
            tmp_path / "stale-evidence",
            result,
            analysis_inputs,
            analysis_inputs.analysis_policy,
            family_map,
            evidence=(altered,),
        )
    assert not (tmp_path / "stale-evidence").exists()


@pytest.mark.parametrize(
    "change",
    ["canonical", "raw", "metadata", "book", "source"],
    ids=["canonical", "raw", "metadata", "book", "source"],
)
def test_changed_current_material_refuses(
    analysis_inputs, family_map, tmp_path, change
):
    result = build_analysis(
        analysis_inputs, analysis_inputs.analysis_policy, family_map
    )
    if change == "canonical":
        changed = replace(
            analysis_inputs,
            canonical_snapshots=(
                replace(analysis_inputs.canonical_snapshots[0], data=b"invented stale"),
            ),
        )
    elif change == "raw":
        changed = replace(
            analysis_inputs,
            raw_snapshots=(
                replace(analysis_inputs.raw_snapshots[0], data=b"invented stale"),
            ),
        )
    elif change == "metadata":
        changed = replace(
            analysis_inputs,
            metadata=(
                analysis_inputs.metadata[0].model_copy(
                    update={"mask_manifest_hash": "0" * 64}
                ),
            ),
        )
    elif change == "book":
        sources = replace(
            analysis_inputs.sources,
            codebook=analysis_inputs.sources.codebook.model_copy(
                update={"content_hash": "0" * 64}
            ),
        )
        changed = replace(analysis_inputs, sources=sources)
    else:
        sources = replace(analysis_inputs.sources, provenance_hash="0" * 64)
        changed = replace(analysis_inputs, sources=sources, provenance_hash="0" * 64)
    with pytest.raises(AnalysisError):
        store().write_analysis_run(
            tmp_path / "changed",
            result,
            changed,
            analysis_inputs.analysis_policy,
            family_map,
            evidence=(),
        )
    assert not (tmp_path / "changed").exists()


def test_forged_source_fragment_reference_refuses(
    analysis_inputs, family_map, tmp_path
):
    from earnings_pipeline.evidence_views import make_evidence_view
    from earnings_themes.analysis import reverify_analysis_inputs

    q = analysis_inputs.sources.stored_run.quotes[0]
    view = make_evidence_view(
        reverify_analysis_inputs(analysis_inputs),
        q.span.doc_id,
        q.quote_id,
        audience="local",
        raw_snapshot=analysis_inputs.raw_snapshots[0],
    )
    ref = view.reference.model_copy(
        update={"source_fragment_url": "https://example.invalid/forged#:~:text=private"}
    )
    result = build_analysis(
        analysis_inputs, analysis_inputs.analysis_policy, family_map
    )
    with pytest.raises(AnalysisError, match="^input_changed$"):
        store().write_analysis_run(
            tmp_path / "forged",
            result,
            analysis_inputs,
            analysis_inputs.analysis_policy,
            family_map,
            evidence=(ref,),
        )
    assert not (tmp_path / "forged").exists()


@pytest.mark.parametrize("stage", ["classifier", "judge"], ids=["classifier", "judge"])
def test_changed_external_cache_refuses_before_writes(
    analysis_input_factory, tmp_path, stage
):
    inputs, root = analysis_input_factory(caches=True)
    result = build_analysis(inputs, inputs.analysis_policy, None)
    ref = (
        inputs.coding.attempts[0].raw_ref
        if stage == "classifier"
        else inputs.support.attempts[0].raw_ref
    )
    path = (
        root / ("classifier-cache" if stage == "classifier" else "support-cache") / ref
    )
    path.write_bytes(b'{"invented":"cache tamper"}')
    with pytest.raises(AnalysisError, match="^storage_corrupt$"):
        store().write_analysis_run(
            tmp_path / "changed-cache",
            result,
            inputs,
            inputs.analysis_policy,
            None,
            evidence=(),
        )
    assert not (tmp_path / "changed-cache").exists()


def test_policy_callback_mutation_refuses_before_writes(
    analysis_inputs, family_map, tmp_path
):
    result = build_analysis(
        analysis_inputs, analysis_inputs.analysis_policy, family_map
    )
    actual = analysis_inputs.assignment_policy

    class MutatingPolicy:
        reference = actual.reference

        def evaluate(self, value):
            object.__setattr__(
                analysis_inputs.metadata[0], "publisher", "Invented changed publisher"
            )
            return actual.evaluate(value)

    changed = replace(analysis_inputs, assignment_policy=MutatingPolicy())
    with pytest.raises(AnalysisError):
        store().write_analysis_run(
            tmp_path / "callback",
            result,
            changed,
            analysis_inputs.analysis_policy,
            family_map,
            evidence=(),
        )
    assert not (tmp_path / "callback").exists()


def test_claimless_run_roundtrip_keeps_unconfirmed_absence(
    analysis_input_factory, tmp_path
):
    inputs, _ = analysis_input_factory(claims=())
    path, result = publish(tmp_path, inputs, None)
    saved = store().read_analysis_run(path)
    assert saved.tables.frames["quotes"].is_empty()
    assert saved.tables.frames["claims"].is_empty()
    assert saved.tables.frames["observations"].is_empty()
    assert saved.record.counts_by_state == result.record.counts_by_state
    assert saved.tables.frames["coverage"]["observable"].sum() == 0
    store().reverify_analysis_run(saved, inputs, inputs.analysis_policy, None)
