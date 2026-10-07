"""V10 counts are hand-computed over invented typed analytical rows."""

import polars as pl
from earnings_themes import analysis


def counted(case):
    assert callable(getattr(analysis, "prevalence", None)), "prevalence_missing"
    return analysis.prevalence(
        case.tables,
        case.tables.frames["coverage"],
        case.book,
        case.policy,
        case.families,
    )


def test_v10_parent_period_counts(counting_case):
    frame = (
        counted(counting_case)
        .filter(
            (pl.col("view_kind") == "parent")
            & (pl.col("view_id") == "capacity")
            & (pl.col("unit") == "issuer_period")
            & (pl.col("doc_type") == "release")
        )
        .sort("period_end")
    )
    assert frame.select("numerator", "denominator").rows() == [(1, 2), (0, 1)]
    assert frame["rate"].to_list() == [0.5, 0.0]


def test_v10_window_units_have_distinct_meanings(counting_case):
    frame = counted(counting_case).filter(
        (pl.col("view_kind") == "parent")
        & (pl.col("view_id") == "capacity")
        & (pl.col("doc_type") == "release")
        & (pl.col("unit") != "issuer_period")
    )
    actual = {
        row["unit"]: (row["numerator"], row["denominator"], row["rate"])
        for row in frame.iter_rows(named=True)
    }
    assert actual == {
        "issuer_window": (1.0, 2, 0.5),
        "firm_quarter": (1.0, 3, 1 / 3),
        "equal_issuer_mean": (0.5, 2, 0.25),
    }


def test_v10_overlapping_families_and_missing_transcripts(counting_case):
    frame = counted(counting_case)
    families = frame.filter(
        (pl.col("view_kind") == "family")
        & (pl.col("unit") == "issuer_period")
        & (pl.col("doc_type") == "release")
        & (pl.col("period_end") == counting_case.expected[0].period_end)
    )
    assert families.select("numerator", "denominator").rows() == [(1.0, 2), (1.0, 2)]
    transcripts = frame.filter(pl.col("doc_type") == "transcript")
    assert set(transcripts["denominator"]) == {0}
    assert set(transcripts["rate"]) == {None}
    assert set(transcripts["reason"]) == {"empty_denominator"}


def test_hand_matrix_full_fk_gate(counting_case):
    analysis.validate_analysis_tables(counting_case.tables)


def test_hand_matrix_view_gate(counting_case):
    from earnings_themes.analysis.prevalence import _views

    assert len(_views(counting_case.book, counting_case.families)) == 6


def test_hand_matrix_policy_binding(counting_case):
    from .cases import reference

    assert all(
        r["analysis_policy_hash"] == counting_case.policy.content_hash
        and r["codebook"] == reference(counting_case.book).model_dump()
        for r in counting_case.tables.frames["completions"].iter_rows(named=True)
    )


def test_duplicate_evidence_and_direct_parent_do_not_multiply_votes(counting_case):
    from types import SimpleNamespace

    frames = dict(counting_case.tables.frames)
    original = next(r for r in counting_case.observations if r.event_id == "A-Q1")
    quotes = list(counting_case.rows["quotes"])
    observations = list(counting_case.observations)
    for index in range(20):
        quote_id = "invented-duplicate-" + str(index)
        quote = next(q for q in quotes if q.doc_id == original.doc_id)
        quotes.append(quote.model_copy(update={"quote_id": quote_id}))
        observations.append(
            original.model_copy(
                update={
                    "quote_id": quote_id,
                    "assignment_id": "invented-duplicate-assignment-" + str(index),
                }
            )
        )
    observations.append(
        original.model_copy(
            update={"theme_id": "capacity", "assignment_id": "invented-direct-parent"}
        )
    )
    for name, rows in (("quotes", quotes), ("observations", observations)):
        frames[name] = pl.DataFrame(
            [r.model_dump() for r in rows], schema=analysis.TABLE_SCHEMAS[name]
        )
    case = SimpleNamespace(**vars(counting_case))
    case.tables = analysis.AnalysisTables(frames)
    result = counted(case).filter(
        (pl.col("view_id") == "capacity")
        & (pl.col("view_kind") == "parent")
        & (pl.col("unit") == "issuer_window")
        & (pl.col("doc_type") == "release")
    )
    assert result.select("numerator", "denominator").rows() == [(1.0, 2)]
    assert counted(case).filter(
        (pl.col("view_kind") == "family")
        & (pl.col("unit") == "issuer_window")
        & (pl.col("doc_type") == "release")
    )["numerator"].to_list() == [1.0, 1.0]


def test_unknown_fiscal_labels_group_by_supported_period_end(counting_case):
    frames = dict(counting_case.tables.frames)
    for name in ("coverage", "observations"):
        frames[name] = frames[name].with_columns(
            pl.lit(None, dtype=pl.Int64).alias("fiscal_year"),
            pl.lit(None, dtype=pl.Int64).alias("fiscal_quarter"),
        )
    result = analysis.prevalence(
        analysis.AnalysisTables(frames),
        frames["coverage"],
        counting_case.book,
        counting_case.policy,
        counting_case.families,
    )
    periods = result.filter(
        (pl.col("unit") == "issuer_period")
        & (pl.col("view_kind") == "parent")
        & (pl.col("doc_type") == "release")
    ).sort("period_end")
    assert periods["period_end"].to_list() == sorted(
        {e.period_end for e in counting_case.expected}
    )
    assert periods["denominator"].to_list() == [2, 1]


import pytest


@pytest.mark.parametrize(
    "kind",
    [
        "orphan",
        "cycle",
        "family_theme",
        "family_version",
        "null_available",
        "book_hash",
    ],
    ids=["orphan", "cycle", "family_theme", "family_version", "nullable", "hash"],
)
def test_incompatible_analysis_inputs_refuse(counting_case, kind):
    from earnings_core import digest
    from earnings_themes.codebook import codebook_hash

    book, families, coverage = (
        counting_case.book,
        counting_case.families,
        counting_case.tables.frames["coverage"],
    )
    if kind in ("orphan", "cycle"):
        theme = book.themes[0].model_copy(
            update={
                "parent_id": "unknown" if kind == "orphan" else "capacity_expansion"
            }
        )
        book = book.model_copy(update={"themes": (theme, *book.themes[1:])})
        book = book.model_copy(update={"content_hash": codebook_hash(book)})
    elif kind.startswith("family"):
        fields = families.model_dump()
        if kind == "family_theme":
            fields["memberships"] = (("unknown", "operations"),)
        else:
            fields["codebook"] = fields["codebook"] | {
                "codebook_version": book.codebook_version + 1
            }
        fields["content_hash"] = analysis.family_map_hash(fields)
        families = analysis.ThemeFamilyMap.model_validate(fields)
    elif kind == "null_available":
        coverage = coverage.with_columns(
            pl.lit(None, dtype=pl.Boolean).alias("available")
        )
    else:
        book = book.model_copy(update={"content_hash": digest("invented-stale-book")})
    with pytest.raises(analysis.AnalysisError):
        analysis.prevalence(
            counting_case.tables, coverage, book, counting_case.policy, families
        )


def test_no_mapping_means_no_invented_family_view(counting_case):
    frame = analysis.prevalence(
        counting_case.tables,
        counting_case.tables.frames["coverage"],
        counting_case.book,
        counting_case.policy,
        None,
    )
    assert "family" not in set(frame["view_kind"])


def test_observed_assignment_policies_cannot_mix(counting_case):
    frames = dict(counting_case.tables.frames)
    rows = frames["completions"].to_dicts()
    row = next(r for r in rows if r["doc_id"] == "invented-doc-B-Q1")
    row["assignment_policy"]["policy_hash"] = "f" * 64
    frames["completions"] = pl.DataFrame(
        rows, schema=analysis.TABLE_SCHEMAS["completions"]
    )
    with pytest.raises(analysis.AnalysisError):
        analysis.prevalence(
            analysis.AnalysisTables(frames),
            counting_case.coverage,
            counting_case.book,
            counting_case.policy,
            counting_case.families,
        )
