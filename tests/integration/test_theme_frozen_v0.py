"""Frozen v0 metadata/rules with invented evidence and a refusing example resolver."""

import polars as pl
from earnings_themes import analysis
from earnings_themes import codebook as module
from earnings_themes.codebook import load_codebook

from tests.integration import stage10_cases
from tests.integration.stage10_cases import (
    REPO,
    analysis_cases,
    theme_fixtures,
)

no_network = stage10_cases.no_network
PINNED = "635975d1ec952cf5719ea3b473870f96e7e3a52bc3015cc1ac5725aa80ec1e79"


def test_frozen_child_direct_assignment_parent_rollup(
    tmp_path, monkeypatch, no_network
):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(1)
        raise AssertionError("example_resolution_forbidden")

    monkeypatch.setattr(module, "_example", forbidden)
    monkeypatch.setattr(module, "validate_codebook", forbidden)
    book = load_codebook(REPO / "codebooks/djia-pilot/codebook-v0.toml")
    assert book.content_hash == PINNED
    child = next(t for t in book.themes if t.parent_id is not None)
    monkeypatch.setattr(analysis_cases, "make_book", lambda base: book)
    inputs = analysis_cases.make_inputs(
        book,
        theme_fixtures.template.__wrapped__(),
        tmp_path,
        themes=(child.theme_id,),
        quote_labels=("U1",),
    )
    before = inputs.coding.assignments
    result = analysis.build_analysis(inputs, inputs.analysis_policy, None)
    direct = result.tables.frames["observations"]
    assert set(direct["theme_id"]) == {child.theme_id}
    parent = result.tables.frames["prevalence"].filter(
        (pl.col("view_kind") == "parent")
        & (pl.col("view_id") == child.parent_id)
        & (pl.col("unit") == "issuer_period")
        & (pl.col("doc_type") == "release")
    )
    assert parent.select("numerator", "denominator", "rate").rows() == [(1.0, 1, 1.0)]
    originals_unchanged = inputs.coding.assignments == before
    assert originals_unchanged and inputs.sources.codebook.content_hash == PINNED
    assert calls == [] and no_network == []
