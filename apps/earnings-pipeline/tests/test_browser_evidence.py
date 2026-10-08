"""Invented public renderer outcomes only; no concrete browser or source readers."""

import importlib
import importlib.util
from dataclasses import replace
from pathlib import Path

import pytest
from earnings_core import ArtifactRef, RightsStatus, sha256_hex
from earnings_ingestion.browser import ISOLATED_1, CaptureEnvironment, CaptureStatus
from earnings_ingestion.browser.records import CaptureReason
from earnings_ingestion.browser.renderer import unrendered
from earnings_themes.analysis import AnalysisError

helpers = importlib.import_module("apps.earnings-pipeline.tests.test_evidence_views")
ENV = CaptureEnvironment("invented", "1", "1", "1", "invented", "1", "invented")


def capture_module():
    assert importlib.util.find_spec("earnings_pipeline.browser_evidence") is not None
    return importlib.import_module("earnings_pipeline.browser_evidence")


class Renderer:
    environment = ENV

    def __init__(
        self,
        status=CaptureStatus.COMPLETED,
        reason=None,
        *,
        tamper=False,
        explode=False,
    ):
        self.status, self.reason = status, reason
        self.calls = []
        self.tamper, self.explode = tamper, explode

    def capture(self, saved_html, policy, *, source_document_id):
        self.calls.append((sha256_hex(saved_html), source_document_id))
        if self.explode:
            raise RuntimeError("Invented SENTINEL arbitrary adapter detail")
        result = unrendered(
            saved_html,
            policy,
            ENV,
            source_document_id=source_document_id,
            status=CaptureStatus.FAILED,
            reason=CaptureReason.CAPTURE_FAILURE,
            detail="Invented SENTINEL private",
        )
        result = result.model_copy(
            update={"status": self.status, "reason": self.reason}
        )
        if self.tamper:
            result = result.model_copy(update={"raw_sha256": "0" * 64})
        return result


def capture_view(tmp_path, monkeypatch, allowed=True):
    return helpers.prepare(
        helpers.make_case(
            tmp_path, monkeypatch, metadata_changes={"retain_capture": allowed}
        )
    )


def test_capture_exact_html_source_id_and_utf16_boundary(tmp_path, monkeypatch):
    view = capture_view(tmp_path, monkeypatch)
    renderer = Renderer()
    result = capture_module().capture_evidence_view(view, renderer, ISOLATED_1)
    assert renderer.calls == [(sha256_hex(view.html), "stage10-invented-A-Q1")]
    assert result.status == "completed" and result.reason is None
    assert result.start == view.reference.start and result.end == view.reference.end
    assert result.utf16_start == result.start + 1
    assert result.utf16_end == result.end + 2
    assert result.capture_artifact.rights_status == RightsStatus.LOCAL_ONLY
    assert result.screenshots_rights == "local_only"


@pytest.mark.parametrize(
    ("status", "reason"),
    [
        (CaptureStatus.PARTIAL, CaptureReason.BLOCKED_REQUIRED_RESOURCE),
        (CaptureStatus.FAILED, CaptureReason.STARTUP_FAILURE),
        (CaptureStatus.FAILED, CaptureReason.TIMEOUT),
        (CaptureStatus.FAILED, CaptureReason.DOCUMENT_LOAD_FAILURE),
        (CaptureStatus.FAILED, CaptureReason.CAPTURE_FAILURE),
        (CaptureStatus.UNAVAILABLE, CaptureReason.BROWSER_UNAVAILABLE),
    ],
    ids=["partial", "startup", "timeout", "load", "failed", "unavailable"],
)
def test_public_renderer_outcomes_remain_truthful(
    tmp_path, monkeypatch, status, reason
):
    result = capture_module().capture_evidence_view(
        capture_view(tmp_path, monkeypatch), Renderer(status, reason), ISOLATED_1
    )
    assert result.status == status.value and result.reason == reason.value
    assert "SENTINEL" not in repr(result)


@pytest.mark.parametrize("mode", ["tamper", "explode"], ids=["hash", "exception"])
def test_adapter_failures_are_closed(tmp_path, monkeypatch, mode):
    result = capture_module().capture_evidence_view(
        capture_view(tmp_path, monkeypatch), Renderer(**{mode: True}), ISOLATED_1
    )
    assert result.status == "failed" and result.reason == "capture_failure"
    assert result.capture_artifact is None


def test_denied_capture_never_accesses_renderer(tmp_path, monkeypatch):
    class Forbidden:
        @property
        def environment(self):
            raise AssertionError("invented environment forbidden")

        def capture(self, *args, **kwargs):
            raise AssertionError("invented capture forbidden")

    result = capture_module().capture_evidence_view(
        capture_view(tmp_path, monkeypatch, False), Forbidden(), ISOLATED_1
    )
    assert result.status == "not_requested" and result.reason == "rights_restricted"
    assert result.utf16_start > result.start


def test_withheld_view_refuses_without_fabricating_browser_coordinates(
    tmp_path, monkeypatch
):
    bound = helpers.make_case(tmp_path, monkeypatch, retain_text=False)
    with pytest.raises(AnalysisError, match="^rights_restricted$"):
        capture_module().capture_evidence_view(
            helpers.prepare(bound), Renderer(), ISOLATED_1
        )


def test_changed_prepared_bytes_refuse_before_adapter(tmp_path, monkeypatch):
    view = capture_view(tmp_path, monkeypatch)
    object.__setattr__(view, "html", b"invented tamper")
    renderer = Renderer()
    with pytest.raises(AnalysisError):
        capture_module().capture_evidence_view(view, renderer, ISOLATED_1)
    assert renderer.calls == []


def test_nonisolated_capture_policy_refuses_before_renderer(tmp_path, monkeypatch):
    renderer = Renderer()
    policy = replace(ISOLATED_1, arguments=())
    result = capture_module().capture_evidence_view(
        capture_view(tmp_path, monkeypatch), renderer, policy
    )
    assert result.status == "failed" and result.reason == "capture_failure"
    assert renderer.calls == []


@pytest.mark.parametrize(
    "rights",
    [RightsStatus.LOCAL_ONLY, RightsStatus.REDISTRIBUTABLE],
    ids=["local-screenshot", "exportable-screenshot-refused"],
)
def test_screenshot_artifact_rights_are_always_local(tmp_path, monkeypatch, rights):
    class ScreenshotRenderer(Renderer):
        def capture(self, *args, **kwargs):
            result = super().capture(*args, **kwargs)
            artifact = ArtifactRef.for_bytes(
                b"invented screenshot",
                media_type="image/png",
                storage_ref="invented/screenshot.png",
                rights_status=rights,
                rights_basis="Invented capture fixture",
            )
            return result.model_copy(update={"screenshots": (artifact,)})

    observation = capture_module().capture_evidence_view(
        capture_view(tmp_path, monkeypatch), ScreenshotRenderer(), ISOLATED_1
    )
    assert observation.status == (
        "completed" if rights == RightsStatus.LOCAL_ONLY else "failed"
    )
    assert observation.screenshots_rights == "local_only"


@pytest.mark.parametrize(
    "case_id",
    ["unique", "repeated", "astral", "long-page", "drift", "no-text-fragment"],
    ids=["unique", "repeated", "astral", "long-page", "drift", "no-text-fragment"],
)
def test_v5_static_index_is_durable_exact_and_pending(tmp_path, monkeypatch, case_id):
    path = (
        Path(__file__).resolve().parents[3]
        / "tests/integration/test_stage10_browser.py"
    )
    spec = importlib.util.spec_from_file_location("stage10_invented_v5", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(
        module, "CASES", tuple(c for c in module.CASES if c[0] == case_id)
    )
    directory, rows, views = module.build_artifacts(
        tmp_path / "published", tmp_path / "work", monkeypatch
    )
    assert (directory / "index.html").is_file()
    assert [r["case_id"] for r in rows] == [case_id]
    for row, view in zip(rows, views):
        assert row["native"] == row["fallback"] == row["capture"] == "pending"
        assert row["tested_transport"] == "local_file"
        assert row["https_behavior"] == "unverified"
        assert (
            sha256_hex((directory / row["source_file"]).read_bytes())
            == row["source_artifact_hash"]
        )
        assert row["saved_source_link"].startswith(row["source_file"] + "#:~:text=")
        assert row["fallback_link"].endswith("#" + view.reference.anchor_id)
        page = (directory / row["fallback_file"]).read_bytes()
        assert page == view.html
        assert row["canonical_hash"] == view.reference.canonical_hash
        assert (row["start"], row["end"]) == (view.reference.start, view.reference.end)
        assert page.count(b"<mark ") == 1
    if case_id == "long-page":
        payload = __import__("json").loads(views[0].canonical_bytes)
        text = payload["document"]["canonical_text"]
        assert text[: rows[0]["start"]].count("\r") == 100
        assert not text[rows[0]["start"] : rows[0]["end"]].startswith(("\n", "\r"))
    if case_id == "astral":
        assert rows[0]["utf16_start"] > rows[0]["start"]
    if case_id == "no-text-fragment":
        assert rows[0]["control_link"] == rows[0]["source_file"]


def test_v5_full_invented_bundle_remains_available_after_fixture_cleanup(
    tmp_path, monkeypatch
):
    path = (
        Path(__file__).resolve().parents[3]
        / "tests/integration/test_stage10_browser.py"
    )
    spec = importlib.util.spec_from_file_location("stage10_invented_bundle", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    directory, rows, views = module.build_artifacts(
        module.ROOT, tmp_path / "work", monkeypatch
    )
    assert (module.ROOT / "index.html").is_file()
    assert len(rows) == len(views) == 6
    for row, view in zip(rows, views):
        assert row["native"] == row["fallback"] == "pending"
        renderer = Renderer()
        capture = capture_module().capture_evidence_view(view, renderer, ISOLATED_1)
        assert capture.status == "completed"
        assert row["native"] == row["fallback"] == "pending"
        assert (directory / row["fallback_file"]).read_bytes() == view.html


@pytest.mark.parametrize(
    "native,fallback",
    [
        ("highlighted", "span_visible"),
        ("page_top", "span_visible"),
        ("not_highlighted", "span_visible"),
        ("wrong_occurrence", "span_visible"),
        ("failed", "failed"),
        ("unavailable", "withheld"),
    ],
    ids=["highlighted", "top", "not-highlighted", "wrong", "failed", "unavailable"],
)
def test_fake_manual_statuses_stay_separate_from_capture(
    tmp_path, monkeypatch, native, fallback
):
    path = (
        Path(__file__).resolve().parents[3]
        / "tests/integration/test_stage10_browser.py"
    )
    spec = importlib.util.spec_from_file_location("stage10_fake_statuses", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    view = capture_view(tmp_path, monkeypatch)
    capture = capture_module().capture_evidence_view(view, Renderer(), ISOLATED_1)
    row = {"case_id": "unique", "native": "pending", "fallback": "pending"}
    result = module.observed_row(
        row,
        capture,
        native=native,
        fallback=fallback,
        observer="invented-observer",
        observed_at="2026-10-07T12:00:00Z",
    )
    assert (result["native"], result["fallback"], result["capture"]) == (
        native,
        fallback,
        "completed",
    )
    assert row["native"] == row["fallback"] == "pending"
    assert result["screenshots_rights"] == "local_only"


def test_next_failed_capture_does_not_inherit_previous_screenshot_ids(
    tmp_path, monkeypatch
):
    path = (
        Path(__file__).resolve().parents[3]
        / "tests/integration/test_stage10_browser.py"
    )
    spec = importlib.util.spec_from_file_location("stage10_fake_capture_sequence", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    view = capture_view(tmp_path, monkeypatch)
    ref = view.reference
    payload = __import__("json").loads(view.canonical_bytes)
    text = payload["document"]["canonical_text"]
    row = {
        "canonical_hash": ref.canonical_hash,
        "start": ref.start,
        "end": ref.end,
        "utf16_start": len(text[: ref.start].encode("utf-16-le")) // 2,
        "utf16_end": len(text[: ref.end].encode("utf-16-le")) // 2,
    }
    session = tmp_path / "capture-session"
    session.mkdir()
    store = importlib.import_module("earnings_ingestion.browser.store").CaptureStore(
        session / "captures", session
    )
    shot = store.screenshot(b"invented screenshot bytes")

    class SequenceRenderer(Renderer):
        def capture(self, *args, **kwargs):
            if self.calls:
                raise RuntimeError("Invented SENTINEL sequence failure")
            capture = super().capture(*args, **kwargs)
            return capture.model_copy(update={"screenshots": (shot,)})

    rows = module.capture_observations(
        [row, row], [view, view], SequenceRenderer(), session, store
    )
    assert rows[0]["capture"] == "completed"
    assert rows[0]["screenshot_artifact_ids"] == [shot.content_sha256]
    assert rows[1]["capture"] == "failed"
    assert rows[1]["screenshot_artifact_ids"] == []
    assert rows[1]["capture_observation"]["capture_artifact"] is None


@pytest.mark.parametrize("kind", ["pointer", "prepared", "observations"])
@pytest.mark.parametrize("failure", ["interrupted", "existing"])
def test_v5_publication_is_atomic_and_preserves_existing(
    tmp_path, monkeypatch, kind, failure
):
    path = (
        Path(__file__).resolve().parents[3]
        / "tests/integration/test_stage10_browser.py"
    )
    spec = importlib.util.spec_from_file_location("stage10_atomic_v5", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "CASES", (module.CASES[0],))
    root = tmp_path / "published"
    _, rows, views = module.build_artifacts(root, tmp_path / "work", monkeypatch)
    session = tmp_path / "session"
    session.mkdir()
    store = importlib.import_module("earnings_ingestion.browser.store").CaptureStore(
        session / "captures", session
    )
    capture = Renderer().capture(
        views[0].html,
        ISOLATED_1,
        source_document_id=__import__("json").loads(views[0].canonical_bytes)[
            "document"
        ]["source_document_id"],
    )

    class StaticRenderer:
        environment = ENV

        def capture(self, *args, **kwargs):
            return capture

    if kind == "pointer":
        target = root / "index.html"
        expected = target.read_bytes()
        target.unlink()

        attempts = []

        def publish():
            attempts.append(True)
            return module.build_artifacts(
                root, tmp_path / ("retry-work-" + str(len(attempts))), monkeypatch
            )

    elif kind == "prepared":
        expected = importlib.import_module("earnings_core").canonical_json(capture)
        target = session / "prepared-captures" / (sha256_hex(expected) + ".json")

        def publish():
            return module.capture_observations(
                rows, views, StaticRenderer(), session, store
            )

    else:
        observation = [
            {"case_id": "unique", "native": "pending", "fallback": "pending"}
        ]
        expected = (
            __import__("json").dumps(observation, sort_keys=True, indent=2).encode()
        )
        target = session / "observations.json"

        def publish():
            return module.publish_observations(session, observation)

    target.parent.mkdir(parents=True, exist_ok=True)
    if failure == "existing":
        target.write_bytes(b"Invented existing immutable record")
        try:
            publish()
        except (FileExistsError, AssertionError):
            pass
        assert target.read_bytes() == b"Invented existing immutable record"
    else:
        original_open = Path.open

        class InterruptedWriter:
            def __init__(self, file):
                self.file = file

            def __enter__(self):
                self.file.__enter__()
                return self

            def __exit__(self, *args):
                return self.file.__exit__(*args)

            def write(self, data):
                self.file.write(data[:7])
                self.file.flush()
                raise OSError("Invented interrupted write")

        def interrupted_open(path, mode="r", *args, **kwargs):
            file = original_open(path, mode, *args, **kwargs)
            if ("w" in mode or "x" in mode) and (
                path == target
                or (path.name == "data" and path.parent.parent == target.parent)
            ):
                return InterruptedWriter(file)
            return file

        with monkeypatch.context() as patch:
            patch.setattr(Path, "open", interrupted_open)
            try:
                publish()
            except OSError:
                pass
        assert not target.exists()
        assert not list(target.parent.glob(".v5-write-*"))
        publish()
        assert target.read_bytes() == expected
        assert sha256_hex(target.read_bytes()) == sha256_hex(expected)
    assert not list(target.parent.glob(".v5-write-*"))
