"""Explicit invented source factories and temporary report artifacts only."""

import importlib
import importlib.util
from dataclasses import replace

import pytest
from earnings_core import RightsStatus, sha256_hex
from earnings_pipeline.evidence_views import make_evidence_view
from earnings_themes.analysis import (
    AnalysisError,
    build_analysis,
    reverify_analysis_inputs,
)

cases = importlib.import_module("packages.earnings-themes.tests.analysis.cases")
fixtures = importlib.import_module("packages.earnings-themes.tests.conftest")


def report():
    assert importlib.util.find_spec("earnings_pipeline.theme_report") is not None
    return importlib.import_module("earnings_pipeline.theme_report")


def setup_case(tmp_path, *, raw=True, **options):
    inputs = cases.make_inputs(
        fixtures.codebook.__wrapped__(),
        fixtures.template.__wrapped__(),
        tmp_path / "invented",
        **options,
    )
    if not raw:
        inputs = replace(inputs, raw_snapshots=())
    families = cases.make_families(inputs.sources.codebook)
    bound = reverify_analysis_inputs(inputs)
    views = tuple(
        make_evidence_view(
            bound,
            q.span.doc_id,
            q.quote_id,
            audience="export",
            raw_snapshot=next(
                (s for s in inputs.raw_snapshots if s.doc_id == q.span.doc_id), None
            ),
        )
        for q in inputs.sources.stored_run.quotes
    )
    module = importlib.import_module("earnings_themes.analysis.store")
    module.write_analysis_run(
        tmp_path / "analysis",
        build_analysis(inputs, inputs.analysis_policy, families),
        inputs,
        inputs.analysis_policy,
        families,
        evidence=(),
    )
    return inputs, families, views, module.read_analysis_run(tmp_path / "analysis")


def test_separate_immutable_cited_bundle(tmp_path):
    module = report()
    inputs, families, views, stored = setup_case(tmp_path)
    before = (tmp_path / "analysis/run.json").read_bytes()
    directory = tmp_path / "report"
    module.write_theme_report(
        directory,
        stored,
        inputs,
        inputs.analysis_policy,
        families,
        views,
        audience="export",
    )
    manifest = module.ReportManifest.model_validate_json(
        (directory / "report.json").read_bytes()
    )
    assert manifest.analysis_manifest_hash == stored.manifest_hash
    for filename, hash_value in manifest.artifact_hashes:
        assert sha256_hex((directory / filename).read_bytes()) == hash_value
    page = (directory / "report.html").read_text()
    assert all(
        term in page
        for term in (
            "fixture",
            "numerator",
            "denominator",
            "issuer_period",
            "transcript_not_in_scope",
            "Model-derived",
            "not_bound",
            "not_supplied",
        )
    )
    assert all(v.reference.anchor_id in page for v in views)
    assert str(tmp_path) not in page and "<script" not in page
    assert (tmp_path / "analysis/run.json").read_bytes() == before
    with pytest.raises(FileExistsError):
        module.write_theme_report(
            directory,
            stored,
            inputs,
            inputs.analysis_policy,
            families,
            views,
            audience="export",
        )


@pytest.mark.parametrize(
    "change",
    ["missing", "tamper", "audience", "raw"],
    ids=["missing", "tamper", "audience", "raw"],
)
def test_invalid_views_refuse_before_publication(tmp_path, change):
    module = report()
    inputs, families, views, stored = setup_case(tmp_path, raw=change != "raw")
    if change == "missing":
        views = ()
    elif change == "tamper":
        object.__setattr__(views[0], "html", b"invented forbidden sentinel")
    elif change == "audience":
        object.__setattr__(views[0].reference, "audience", "local")
    with pytest.raises(AnalysisError):
        module.write_theme_report(
            tmp_path / "report",
            stored,
            inputs,
            inputs.analysis_policy,
            families,
            views,
            audience="export",
        )
    assert not (tmp_path / "report").exists()


def test_nested_rights_strip_quote_claim_and_private_refs(tmp_path):
    module = report()
    inputs, families, views, stored = setup_case(
        tmp_path,
        text_artifact_rights=RightsStatus.LOCAL_ONLY,
        first_text="Invented forbidden private sentinel",
        claims=("Invented forbidden claim sentinel",),
    )
    directory = tmp_path / "report"
    module.write_theme_report(
        directory,
        stored,
        inputs,
        inputs.analysis_policy,
        families,
        views,
        audience="export",
    )
    for filename in ("report.html", "report.json"):
        assert b"Invented forbidden" not in (directory / filename).read_bytes()
    assert b"rights_restricted" in (directory / "report.html").read_bytes()
    assert (
        len(
            module.ReportManifest.model_validate_json(
                (directory / "report.json").read_bytes()
            ).artifact_hashes
        )
        == 1
    )


def test_local_profile_and_report_parent_symlink_refusal(tmp_path):
    module = report()
    inputs, families, _, stored = setup_case(tmp_path)
    bound = reverify_analysis_inputs(inputs)
    views = tuple(
        make_evidence_view(
            bound,
            q.span.doc_id,
            q.quote_id,
            audience="local",
            raw_snapshot=inputs.raw_snapshots[0],
        )
        for q in inputs.sources.stored_run.quotes
    )
    directory = tmp_path / "local-report"
    module.write_theme_report(
        directory,
        stored,
        inputs,
        inputs.analysis_policy,
        families,
        views,
        audience="local",
    )
    assert (
        module.ReportManifest.model_validate_json(
            (directory / "report.json").read_bytes()
        ).audience
        == "local"
    )
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(AnalysisError):
        module.write_theme_report(
            link / "report",
            stored,
            inputs,
            inputs.analysis_policy,
            families,
            views,
            audience="local",
        )
    assert not (target / "report").exists()
