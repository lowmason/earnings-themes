"""Public analytical identities, schema keys and immutable current-gate contracts."""

import importlib
import inspect

import polars as pl
import pytest
from earnings_themes import analysis

PUBLIC_FUNCTIONS = {
    "reverify_analysis_inputs": "consume",
    "analysis_provenance_hash": "consume",
    "build_observations": "rows",
    "document_completions": "completion",
    "build_coverage": "coverage",
    "prevalence": "prevalence",
    "build_analysis": "prevalence",
    "write_analysis_run": "store",
    "read_analysis_run": "store",
    "reverify_analysis_run": "store",
    "validate_analysis_tables": "records",
}


@pytest.mark.parametrize("name", tuple(PUBLIC_FUNCTIONS), ids=tuple(PUBLIC_FUNCTIONS))
def test_public_exports_are_implemented_objects(name):
    module = importlib.import_module(
        "earnings_themes.analysis." + PUBLIC_FUNCTIONS[name]
    )
    assert getattr(analysis, name) is getattr(module, name)
    assert name in analysis.__all__


@pytest.mark.parametrize(
    "table", tuple(analysis.TABLE_SCHEMAS), ids=tuple(analysis.TABLE_SCHEMAS)
)
def test_typed_empty_tables_retain_all_grain_and_foreign_keys(table):
    schema = analysis.TABLE_SCHEMAS[table]
    frame = pl.DataFrame(schema=schema)
    assert frame.schema == pl.Schema(schema)
    assert set(analysis.TABLE_GRAINS[table]) <= set(schema)
    assert schema["schema_version"] == pl.Int64
    for local, target, remote in analysis.TABLE_FOREIGN_KEYS[table]:
        assert set(local) <= set(schema)
        assert set(remote) <= set(analysis.TABLE_SCHEMAS[target])


def test_published_reader_and_current_gate_are_distinct_contracts():
    assert tuple(inspect.signature(analysis.read_analysis_run).parameters) == (
        "directory",
    )
    assert tuple(inspect.signature(analysis.reverify_analysis_run).parameters) == (
        "stored",
        "inputs",
        "policy",
        "families",
    )
    assert tuple(inspect.signature(analysis.write_analysis_run).parameters) == (
        "directory",
        "result",
        "inputs",
        "policy",
        "families",
        "evidence",
    )
    public = importlib.import_module("earnings_pipeline.evidence_views")
    signature = inspect.signature(public.make_evidence_view)
    assert signature.parameters["raw_snapshot"].kind is inspect.Parameter.KEYWORD_ONLY
    assert signature.parameters["raw_snapshot"].default is inspect.Parameter.empty


def test_public_writer_is_immutable_and_current_gate_refuses_changed_policy(
    tmp_path, monkeypatch
):
    from dataclasses import replace

    from earnings_core import sha256_hex

    from tests.integration.stage10_cases import analysis_cases, theme_fixtures

    trips = theme_fixtures.no_network.__wrapped__(monkeypatch)
    inputs = analysis_cases.make_inputs(
        theme_fixtures.codebook.__wrapped__(),
        theme_fixtures.template.__wrapped__(),
        tmp_path / "inputs",
        quote_labels=("U1",),
    )
    policy = inputs.analysis_policy
    result = analysis.build_analysis(inputs, policy, None)
    destination = tmp_path / "published"
    analysis.write_analysis_run(destination, result, inputs, policy, None, ())
    hashes = {p.name: sha256_hex(p.read_bytes()) for p in destination.iterdir()}
    stored = analysis.read_analysis_run(destination)
    analysis.reverify_analysis_run(stored, inputs, policy, None)
    with pytest.raises(FileExistsError, match="^analysis_destination_exists$"):
        analysis.write_analysis_run(destination, result, inputs, policy, None, ())
    changed = replace(inputs, assignment_policy=None)
    with pytest.raises(analysis.AnalysisError):
        analysis.reverify_analysis_run(stored, changed, policy, None)
    with pytest.raises(analysis.AnalysisError):
        analysis.write_analysis_run(
            tmp_path / "refused", result, changed, policy, None, ()
        )
    assert not (tmp_path / "refused").exists()
    assert hashes == {p.name: sha256_hex(p.read_bytes()) for p in destination.iterdir()}
    assert trips == []


def test_legacy_fixture_producer_preserves_partial_spans_with_current_contracts(
    monkeypatch,
):
    from earnings_core import CanonicalDocument, DocumentElement, ElementType, TextSpan
    from earnings_themes.anchoring import Bundle
    from earnings_themes.extraction import validate_stored_run

    from tests.integration.stage10_cases import theme_fixtures

    cases = importlib.import_module("packages.earnings-themes.tests.support.cases")
    trips = theme_fixtures.no_network.__wrapped__(monkeypatch)
    text = "Invented first passage.\nInvented second passage."
    document = CanonicalDocument.create(
        source_document_id="invented-partial-contract",
        canonicalization_version="test-1",
        canonical_text=text,
    )
    split = text.index("\n")
    elements = tuple(
        DocumentElement.create(
            document, ElementType.PARAGRAPH, TextSpan(start=start, end=end)
        )
        for start, end in ((0, split), (split + 1, len(text)))
    )
    spans = (
        (split + 2, len(text) - 1, elements[1].element_id),
        (1, split - 1, elements[0].element_id),
    )
    sources, target = cases.stored_case(
        Bundle("invented", document, elements, ()),
        theme_fixtures.codebook.__wrapped__(),
        "An invented partial-span interpretation.",
        spans,
    )
    stored = validate_stored_run(sources.stored_run)
    actual = tuple((q.span.start, q.span.end, q.span.element_id) for q in stored.quotes)
    assert actual == spans
    assert stored.claims[0].quote_ids == tuple(q.quote_id for q in stored.quotes)
    interpretation_unchanged = (
        stored.claims[0].claim == "An invented partial-span interpretation."
    )
    assert interpretation_unchanged
    assert target.claim_id == stored.claims[0].claim_id
    assert len(stored.windows) == 1 and len(stored.visits) == 2
    assert trips == []
