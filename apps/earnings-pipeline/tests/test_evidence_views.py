"""Invented static evidence; no protected source, browser, model or network reader."""

import html
import importlib
import importlib.util
from dataclasses import replace
from urllib.parse import urlsplit

import pytest
from earnings_core import RightsStatus, digest, make_locator, sha256_hex
from earnings_themes.analysis import AnalysisError, reverify_analysis_inputs

cases = importlib.import_module("packages.earnings-themes.tests.analysis.cases")
themes_fixtures = importlib.import_module("packages.earnings-themes.tests.conftest")


def view_module():
    assert importlib.util.find_spec("earnings_pipeline.evidence_views") is not None
    return importlib.import_module("earnings_pipeline.evidence_views")


def make_case(tmp_path, monkeypatch, *, metadata_changes=None, **options):
    original = cases.metadata
    if metadata_changes:

        def metadata(bundle, expected):
            row, raw = original(bundle, expected)
            changes = dict(metadata_changes)
            rights = changes.get("rights_status", row.rights_status)
            artifact = raw.artifact.model_copy(update={"rights_status": rights})
            row = row.model_copy(update={**changes, "raw_artifact": artifact})
            raw = replace(raw, artifact=artifact)
            if not row.retain_raw:
                row = row.model_copy(update={"raw_artifact": None})
            return row, raw

        monkeypatch.setattr(cases, "metadata", metadata)
    inputs = cases.make_inputs(
        themes_fixtures.codebook.__wrapped__(),
        themes_fixtures.template.__wrapped__(),
        tmp_path / "invented-run",
        **options,
    )
    if metadata_changes and not inputs.metadata[0].retain_raw:
        inputs = replace(inputs, raw_snapshots=())
    return reverify_analysis_inputs(inputs)


def prepare(bound, *, audience="local", quote_index=-1, raw=True):
    quote = bound.inputs.sources.stored_run.quotes[quote_index]
    snapshot = next(
        (s for s in bound.inputs.raw_snapshots if s.doc_id == quote.span.doc_id), None
    )
    return view_module().make_evidence_view(
        bound,
        quote.span.doc_id,
        quote.quote_id,
        audience=audience,
        raw_snapshot=snapshot if raw else None,
    )


def test_mark_exact_occurrence_and_escaped():
    text = "😀 first <script> then second <script>"
    start = text.rindex("<script>")
    rendered = view_module().marked_text(
        text, start, start + len("<script>"), "p-invented"
    )
    assert '<mark id="p-invented">&lt;script&gt;</mark>' in rendered
    assert rendered.index("<mark") > rendered.index("&lt;script&gt;")
    assert "<script>" not in rendered
    assert len(text[:start].encode("utf-16-le")) // 2 == start + 1


@pytest.mark.parametrize(
    "text",
    [
        "<script> \"x\" & 'y' dash-comma, e\u0301 😀",
        '😀 prefix\nnext line <img src="https://example.invalid/x">',
        "Invented " + "x" * 20000,
    ],
    ids=["escape", "newline", "long"],
)
def test_static_view_keeps_exact_canonical_text(tmp_path, monkeypatch, text):
    bound = make_case(tmp_path, monkeypatch, first_text=text, quote_labels=("U1",))
    view = prepare(bound, quote_index=0)
    ref = view.reference
    canonical = bound.inputs.sources.bundles[0].document.canonical_text
    page = view.html.decode()
    assert html.escape(canonical[: ref.start]) in page
    assert (
        '<mark id="'
        + ref.anchor_id
        + '">'
        + html.escape(canonical[ref.start : ref.end])
        + "</mark>"
        in page
    )
    assert ref.view_artifact.matches(view.html)
    assert ref.canonical_artifact.matches(view.canonical_bytes)
    assert ref.raw_artifact.matches(view.raw_bytes)
    assert ref.canonical_hash == sha256_hex(canonical.encode())
    assert "white-space:pre-wrap" in page
    assert all(
        value not in page for value in ("<script", "<img", "<link", "@import", "url(")
    )
    path = tmp_path / (ref.view_artifact.content_sha256 + ".html")
    path.write_bytes(view.html)
    assert sha256_hex(path.read_bytes()) == ref.view_artifact.content_sha256


def test_second_repeated_sentence_has_its_own_mark_locator_and_id(
    tmp_path, monkeypatch
):
    bound = make_case(tmp_path, monkeypatch)
    first, second = prepare(bound, quote_index=0), prepare(bound)
    doc = bound.inputs.sources.bundles[0].document
    assert second.reference.start > first.reference.end
    assert first.reference.anchor_id != second.reference.anchor_id
    assert second.html.decode().index("<mark") > second.html.decode().index(
        html.escape("Invented 🛠 press expanded.")
    )
    quote = bound.inputs.sources.stored_run.quotes[-1]
    locator = make_locator(doc, quote.span.span)
    assert second.reference.locator_hash == digest(locator)
    assert second.reference.evidence_id == "evidence-" + digest(
        (
            doc.doc_id,
            quote.quote_id,
            doc.canonical_hash,
            quote.span.start,
            quote.span.end,
            quote.span.validator_version,
        )
    )


def test_overlapping_marks_are_separate_views():
    module = view_module()
    assert '<mark id="p-a">aaa</mark>a' == module.marked_text("aaaa", 0, 3, "p-a")
    assert 'a<mark id="p-b">aaa</mark>' == module.marked_text("aaaa", 1, 4, "p-b")


def test_source_link_preserves_query_replaces_fragment_and_encodes_delimiters(
    tmp_path, monkeypatch
):
    bound = make_case(
        tmp_path,
        monkeypatch,
        first_text='😀 dash-comma, "quoted" & e\u0301',
        metadata_changes={"source_url": "https://example.invalid/release?a=1&b=2#old"},
    )
    view = prepare(bound, quote_index=0)
    url = view.reference.source_fragment_url
    assert urlsplit(url).query == "a=1&b=2"
    assert "%2D" in url and "%2C" in url and "%22" in url and "%26" in url
    assert "#old" not in url
    assert view.reference.source_url == "https://example.invalid/release?a=1&b=2"
    assert "&amp;b=2" in view.html.decode()


@pytest.mark.parametrize(
    "url",
    [
        "javascript:evil",
        "https://@example.invalid/a",
        "https://example.invalid/a\x00",
        "https://example.invalid/a\n",
    ],
    ids=["scheme", "userinfo", "control", "newline"],
)
def test_unsafe_source_link_refuses_without_values(url):
    with pytest.raises(AnalysisError, match="^input_changed$") as error:
        view_module().source_url(url)
    assert url not in str(error.value)


def test_explicit_snapshot_must_match_bound_inventory(tmp_path, monkeypatch):
    bound = make_case(tmp_path, monkeypatch)
    with pytest.raises(AnalysisError, match="^input_changed$"):
        prepare(bound, raw=False)
    q = bound.inputs.sources.stored_run.quotes[0]
    snapshot = replace(bound.inputs.raw_snapshots[0], data=b"invented changed")
    with pytest.raises(AnalysisError, match="^input_changed$"):
        view_module().make_evidence_view(
            bound, q.span.doc_id, q.quote_id, audience="local", raw_snapshot=snapshot
        )


def test_missing_raw_keeps_marked_canonical_fallback(tmp_path, monkeypatch):
    bound = make_case(tmp_path, monkeypatch)
    bound = reverify_analysis_inputs(replace(bound.inputs, raw_snapshots=()))
    view = prepare(bound, raw=False)
    assert view.reference.status == "available"
    assert view.reference.reason == "raw_snapshot_missing"
    assert (
        view.raw_bytes is None
        and view.html is not None
        and view.canonical_bytes is not None
    )


@pytest.mark.parametrize(
    "change",
    ["text", "hash", "offset", "masks", "policy"],
    ids=["text", "hash", "offset", "masks", "policy"],
)
def test_current_binding_changes_refuse_before_html(tmp_path, monkeypatch, change):
    bound = make_case(tmp_path, monkeypatch)
    bundle = bound.inputs.sources.bundles[0]
    if change in ("text", "hash"):
        object.__setattr__(
            bundle.document,
            "canonical_text" if change == "text" else "canonical_hash",
            "invented changed" if change == "text" else "0" * 64,
        )
    elif change == "offset":
        object.__setattr__(
            bound.inputs.sources.stored_run.quotes[0].span, "start", True
        )
    elif change == "masks":
        object.__setattr__(bundle, "masks", (object(),))
    else:
        object.__setattr__(bound.inputs.analysis_policy, "mask_policy_version", "2")
    with pytest.raises(AnalysisError):
        prepare(bound)


def test_local_only_export_withholds_all_private_artifacts(tmp_path, monkeypatch):
    bound = make_case(
        tmp_path,
        monkeypatch,
        metadata_changes={
            "rights_status": RightsStatus.LOCAL_ONLY,
            "export_text": False,
            "export_raw": False,
        },
    )
    local = prepare(bound)
    exported = prepare(bound, audience="export")
    assert local.html is not None and local.raw_bytes is not None
    assert (
        exported.reference.status == "withheld"
        and exported.reference.reason == "rights_restricted"
    )
    assert exported.html is exported.raw_bytes is exported.canonical_bytes is None
    assert exported.reference.source_fragment_url is None
    assert exported.reference.source_url is not None
    assert exported.reference.evidence_id == local.reference.evidence_id
    assert exported.retain_capture is False


def test_no_text_retention_withholds_even_redistributable(tmp_path, monkeypatch):
    bound = make_case(tmp_path, monkeypatch, retain_text=False)
    view = prepare(bound)
    assert view.html is view.canonical_bytes is view.raw_bytes is None
    assert view.reference.reason == "rights_restricted" and not view.retain_capture


def test_masked_quote_retained_for_audit(tmp_path, monkeypatch):
    view = prepare(make_case(tmp_path, monkeypatch, masked=True), quote_index=0)
    assert len(view.reference.mask_ids) == 1


def test_restricted_no_retention_withholds_canonical_and_raw(tmp_path, monkeypatch):
    bound = make_case(
        tmp_path,
        monkeypatch,
        metadata_changes={
            "rights_status": RightsStatus.RESTRICTED,
            "access_status": "restricted",
            "retain_text": False,
            "export_text": False,
            "retain_raw": False,
            "export_raw": False,
            "retain_capture": False,
        },
    )
    view = prepare(bound, raw=False)
    assert view.reference.status == "withheld"
    assert view.html is view.canonical_bytes is view.raw_bytes is None
    assert view.reference.reason == "rights_restricted"


def test_default_view_import_needs_no_concrete_browser():
    import json
    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json,sys,earnings_pipeline.evidence_views; print(json.dumps(sorted(sys.modules)))",
        ],
        capture_output=True,
        check=True,
        text=True,
    )
    modules = set(json.loads(result.stdout))
    assert "selenium" not in modules
    assert "earnings_ingestion.browser.selenium_capture" not in modules
    assert not any(m.startswith("earnings_ingestion.browser") for m in modules)


def test_snapshot_duck_type_cannot_replace_explicit_raw_contract(tmp_path, monkeypatch):
    bound = make_case(tmp_path, monkeypatch)
    original = bound.inputs.raw_snapshots[0]

    class PretendingSnapshot:
        doc_id, artifact, data = original.doc_id, original.artifact, original.data

        def __eq__(self, other):
            return True

    quote = bound.inputs.sources.stored_run.quotes[0]
    with pytest.raises(AnalysisError, match="^input_changed$"):
        view_module().make_evidence_view(
            bound,
            quote.span.doc_id,
            quote.quote_id,
            audience="local",
            raw_snapshot=PretendingSnapshot(),
        )


def test_redistributable_export_carries_verified_bytes(tmp_path, monkeypatch):
    exported = prepare(make_case(tmp_path, monkeypatch), audience="export")
    assert (
        exported.reference.status == "available" and exported.reference.reason is None
    )
    assert exported.reference.view_artifact.matches(exported.html)
    assert exported.reference.canonical_artifact.matches(exported.canonical_bytes)
    assert exported.reference.raw_artifact.matches(exported.raw_bytes)
    assert exported.reference.source_fragment_url is not None


def test_publisher_metadata_and_anchor_attributes_are_escaped(tmp_path, monkeypatch):
    publisher = '<script>"Invented" & publisher</script>'
    view = prepare(
        make_case(tmp_path, monkeypatch, metadata_changes={"publisher": publisher})
    )
    assert html.escape(publisher) in view.html.decode()
    assert "<script>" not in view.html.decode()
    assert 'id="&quot; onmouseover=&quot;invented"' in view_module().marked_text(
        "abc", 0, 1, '" onmouseover="invented'
    )
