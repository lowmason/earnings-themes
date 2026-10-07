"""Invented public renderer outcomes only; no concrete browser or source readers."""

import importlib
import importlib.util
from dataclasses import replace

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
