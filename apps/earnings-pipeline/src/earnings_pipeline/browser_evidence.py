"""Optional public renderer boundary; capture provenance never verifies evidence."""

from dataclasses import asdict

from earnings_core import (
    ArtifactRef,
    Rejection,
    RightsStatus,
    TextSpan,
    VerifiedSpan,
    canonical_json,
    digest,
    make_locator,
    reverify_span,
    sha256_hex,
)
from earnings_ingestion.browser import (
    ISOLATED_1,
    BrowserRenderer,
    CapturePolicy,
    RenderedCapture,
)
from earnings_ingestion.canonical.serialize import from_fixture_json
from earnings_themes.analysis import (
    AnalysisError,
    CaptureObservation,
    EvidenceView,
    EvidenceViewReference,
)
from earnings_themes.anchoring import mask_id


def _canonical_view(view: EvidenceView):
    """Check supplied byte/identity bindings before any adapter access."""
    try:
        if type(view) is not EvidenceView:
            raise AnalysisError("input_changed")
        reference = EvidenceViewReference.model_validate_json(
            view.reference.model_dump_json()
        )
        view = EvidenceView(
            reference,
            view.html,
            view.canonical_bytes,
            view.raw_bytes,
            view.retain_capture,
        )
        if view.reference.status == "withheld":
            raise AnalysisError("rights_restricted")
        canonical = from_fixture_json(view.canonical_bytes.decode("utf-8"))
        doc, ref = canonical.document, view.reference
        if (doc.doc_id, doc.canonical_hash) != (ref.doc_id, ref.canonical_hash):
            raise AnalysisError("input_changed")
        text_span = TextSpan(start=ref.start, end=ref.end)
        locator = make_locator(doc, text_span)
        if (
            digest(locator) != ref.locator_hash
            or sha256_hex(locator.exact.encode("utf-8")) != ref.quote_text_hash
        ):
            raise AnalysisError("input_changed")
        verified = reverify_span(
            doc,
            canonical.elements,
            VerifiedSpan(
                doc_id=ref.doc_id,
                canonical_hash=ref.canonical_hash,
                start=ref.start,
                end=ref.end,
                quote_text=locator.exact,
                element_id=ref.element_id,
                prefix=locator.prefix,
                suffix=locator.suffix,
                validator_version=ref.validator_version,
            ),
        )
        if (
            isinstance(verified, Rejection)
            or verified.validator_version != ref.validator_version
        ):
            raise AnalysisError("input_changed")
        masks = tuple(
            sorted(
                mask_id(m) for m in canonical.masked.masks if m.span.overlaps(text_span)
            )
        )
        identity = digest(
            (
                ref.doc_id,
                ref.quote_id,
                ref.canonical_hash,
                ref.start,
                ref.end,
                ref.validator_version,
            )
        )
        if (
            masks != ref.mask_ids
            or ref.evidence_id != "evidence-" + identity
            or ref.anchor_id != "p-" + identity
        ):
            raise AnalysisError("input_changed")
        return view, doc
    except AnalysisError as error:
        raise AnalysisError(error.reason) from None
    except Exception:  # noqa: BLE001 - saved source/validation diagnostics are private
        raise AnalysisError("input_changed") from None


def capture_evidence_view(
    view: EvidenceView,
    renderer: BrowserRenderer,
    policy: CapturePolicy,
) -> CaptureObservation:
    """Prepare capture provenance; later publication must supply/store actual bytes."""
    view, document = _canonical_view(view)
    ref = view.reference
    text = document.canonical_text
    common = {
        "evidence_id": ref.evidence_id,
        "doc_id": ref.doc_id,
        "quote_id": ref.quote_id,
        "canonical_hash": ref.canonical_hash,
        "start": ref.start,
        "end": ref.end,
        "utf16_start": len(text[: ref.start].encode("utf-16-le")) // 2,
        "utf16_end": len(text[: ref.end].encode("utf-16-le")) // 2,
    }
    if not view.retain_capture:
        return CaptureObservation(
            **common,
            capture_id=None,
            capture_artifact=None,
            policy_hash=None,
            environment_hash=None,
            status="not_requested",
            reason="rights_restricted",
        )
    policy_hash = environment_hash = None
    try:
        if type(policy) is not CapturePolicy or policy != ISOLATED_1:
            raise ValueError
        policy_fields = asdict(policy)
        policy_fields["required_resource_types"] = sorted(
            policy.required_resource_types
        )
        policy_hash = digest(policy_fields)
        environment_fields = asdict(renderer.environment)
        environment_hash = digest(environment_fields)
        capture = renderer.capture(
            view.html, policy, source_document_id=document.source_document_id
        )
        if type(capture) is not RenderedCapture:
            raise ValueError
        capture = RenderedCapture.model_validate_json(capture.model_dump_json())
        if (
            capture.raw_sha256 != sha256_hex(view.html)
            or capture.source_document_id != document.source_document_id
            or capture.capture_policy != policy.name
            or capture.capture_policy_version != policy.version
            or any(
                a.rights_status != RightsStatus.LOCAL_ONLY for a in capture.screenshots
            )
        ):
            raise ValueError
        capture_environment = {key: getattr(capture, key) for key in environment_fields}
        if digest(capture_environment) != environment_hash:
            raise ValueError
        data = canonical_json(capture)
        artifact = ArtifactRef.for_bytes(
            data,
            media_type="application/json",
            storage_ref="prepared-captures/" + sha256_hex(data) + ".json",
            rights_status=RightsStatus.LOCAL_ONLY,
            rights_basis="Prepared rendering provenance; local retention only",
        )
        return CaptureObservation(
            **common,
            capture_id=capture.capture_id,
            capture_artifact=artifact,
            policy_hash=policy_hash,
            environment_hash=environment_hash,
            status=capture.status.value,
            reason=capture.reason.value if capture.reason else None,
        )
    except Exception:  # noqa: BLE001 - arbitrary adapter errors/details/chains are private
        return CaptureObservation(
            **common,
            capture_id=None,
            capture_artifact=None,
            policy_hash=policy_hash,
            environment_hash=environment_hash,
            status="failed",
            reason="capture_failure",
        )
