"""Prepare escaped canonical evidence bytes; publication owns durable writes."""

import html
from typing import Literal
from urllib.parse import quote, urlsplit, urlunsplit

from earnings_core import (
    ArtifactRef,
    Rejection,
    RightsStatus,
    TextSpan,
    digest,
    make_locator,
    reverify_span,
    sha256_hex,
)
from earnings_themes.analysis import (
    AnalysisError,
    BoundAnalysis,
    EvidenceView,
    EvidenceViewReference,
    RawSnapshot,
    reverify_analysis_inputs,
)

TEMPLATE_VERSION = "canonical-evidence-html/1"


def marked_text(text: str, start: int, end: int, anchor: str) -> str:
    """Escape three exact slices; never locate a span through rendered HTML."""
    if (
        type(start) is not int
        or type(end) is not int
        or not 0 <= start < end <= len(text)
    ):
        raise AnalysisError("input_changed")
    return (
        html.escape(text[:start])
        + '<mark id="'
        + html.escape(anchor, quote=True)
        + '">'
        + html.escape(text[start:end])
        + "</mark>"
        + html.escape(text[end:])
    )


def directive_term(text: str) -> str:
    return quote(text, safe="").replace("-", "%2D")


def text_directive(locator) -> str:
    parts = []
    if locator.prefix:
        parts.append(directive_term(locator.prefix) + "-,")
    parts.append(directive_term(locator.exact))
    if locator.suffix:
        parts.append(",-" + directive_term(locator.suffix))
    return "#:~:text=" + "".join(parts)


def source_url(value: str) -> str:
    """Validate HTTP(S), preserving query and replacing any old fragment."""
    try:
        if type(value) is not str or any(ord(c) <= 32 or ord(c) == 127 for c in value):
            raise ValueError
        parsed = urlsplit(value)
        if (
            parsed.scheme not in ("http", "https")
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ValueError
        _ = parsed.port
        return urlunsplit(parsed._replace(fragment=""))
    except Exception:  # noqa: BLE001 - refused source values never enter diagnostics
        raise AnalysisError("input_changed") from None


def _artifact(data: bytes, media_type: str, directory: str, suffix: str, metadata):
    return ArtifactRef.for_bytes(
        data,
        media_type=media_type,
        storage_ref=directory + "/" + sha256_hex(data) + suffix,
        rights_status=metadata.rights_status,
        rights_basis=metadata.rights_basis,
    )


def _html(document, span, anchor, metadata, fragment_url, scope):
    heading = html.escape(metadata.publisher)
    details = html.escape(
        f"{document.doc_id} | {document.canonical_hash} | [{span.start},{span.end}) | "
        f"validator {span.validator_version} | {scope} | {TEMPLATE_VERSION}"
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Canonical evidence</title><style>"
        "body{font-family:system-ui;margin:2rem;overflow-wrap:anywhere}"
        ".canonical{white-space:pre-wrap}mark{background:#ffe066;color:#111;"
        "outline:2px solid #735600}a{color:#174f9b}</style></head><body>"
        "<h1>" + heading + "</h1><p>" + details + "</p>"
        '<p><a href="'
        + html.escape(fragment_url, quote=True)
        + '">Source passage</a></p>'
        '<div class="canonical">'
        + marked_text(document.canonical_text, span.start, span.end, anchor)
        + "</div></body></html>"
    ).encode("utf-8")


def make_evidence_view(
    bound: BoundAnalysis,
    doc_id: str,
    quote_id: str,
    *,
    audience: Literal["local", "export"],
    raw_snapshot: RawSnapshot | None,
) -> EvidenceView:
    """Rebind current inputs and prepare one immutable, rights-filtered view."""
    try:
        if type(bound) is not BoundAnalysis or audience not in ("local", "export"):
            raise AnalysisError("input_changed")
        current = reverify_analysis_inputs(bound.inputs)
        if current.binding_hash != bound.binding_hash:
            raise AnalysisError("input_changed")
        inputs = current.inputs
        bundle = next(b for b in inputs.sources.bundles if b.document.doc_id == doc_id)
        metadata = next(m for m in current.metadata if m.doc_id == doc_id)
        selected = next(
            q
            for q in inputs.sources.stored_run.quotes
            if (q.span.doc_id, q.quote_id) == (doc_id, quote_id)
        )
        expected_raw = next(
            (s for s in inputs.raw_snapshots if s.doc_id == doc_id), None
        )
        if (
            raw_snapshot is not None and type(raw_snapshot) is not RawSnapshot
        ) or raw_snapshot != expected_raw:
            raise AnalysisError("input_changed")
        span = reverify_span(bundle.document, bundle.elements, selected.span)
        if isinstance(span, Rejection):
            raise AnalysisError("input_changed")
        locator = make_locator(
            bundle.document, TextSpan(start=span.start, end=span.end)
        )
        identity = digest(
            (
                doc_id,
                quote_id,
                span.canonical_hash,
                span.start,
                span.end,
                span.validator_version,
            )
        )
        anchor = "p-" + identity
        plain_url = source_url(metadata.source_url)
        allowed_text = (
            metadata.retain_text
            and metadata.access_status == "available"
            and (
                audience == "local"
                or metadata.export_text
                and metadata.rights_status == RightsStatus.REDISTRIBUTABLE
            )
        )
        common = {
            "evidence_id": "evidence-" + identity,
            "doc_id": doc_id,
            "quote_id": quote_id,
            "canonical_hash": span.canonical_hash,
            "start": span.start,
            "end": span.end,
            "validator_version": span.validator_version,
            "element_id": span.element_id,
            "mask_ids": selected.mask_ids,
            "locator_hash": digest(locator),
            "quote_text_hash": sha256_hex(
                bundle.document.canonical_text[span.start : span.end].encode("utf-8")
            ),
            "source_url": plain_url,
            "anchor_id": anchor,
            "audience": audience,
            "rights_status": metadata.rights_status,
            "rights_basis": metadata.rights_basis,
        }
        if not allowed_text:
            return EvidenceView(
                EvidenceViewReference(
                    **common,
                    source_fragment_url=None,
                    raw_artifact=None,
                    canonical_artifact=None,
                    view_artifact=None,
                    status="withheld",
                    reason="rights_restricted",
                ),
                None,
                None,
                None,
                False,
            )
        canonical_bytes = next(
            s.data for s in inputs.canonical_snapshots if s.doc_id == doc_id
        )
        fragment_url = plain_url + text_directive(locator)
        page = _html(
            bundle.document,
            span,
            anchor,
            metadata,
            fragment_url,
            inputs.analysis_policy.scope,
        )
        allowed_raw = metadata.retain_raw and (
            audience == "local" or metadata.export_raw
        )
        raw_bytes = (
            raw_snapshot.data if raw_snapshot is not None and allowed_raw else None
        )
        reference = EvidenceViewReference(
            **common,
            source_fragment_url=fragment_url,
            raw_artifact=raw_snapshot.artifact if raw_bytes is not None else None,
            canonical_artifact=_artifact(
                canonical_bytes, "application/json", "canonical", ".json", metadata
            ),
            view_artifact=_artifact(
                page, "text/html; charset=utf-8", "views", ".html", metadata
            ),
            status="available",
            reason="raw_snapshot_missing"
            if metadata.retain_raw and raw_snapshot is None
            else None,
        )
        return EvidenceView(
            reference, page, canonical_bytes, raw_bytes, metadata.retain_capture
        )
    except AnalysisError as error:
        raise AnalysisError(error.reason) from None
    except Exception:  # noqa: BLE001 - foreign contracts/source fields are opaque
        raise AnalysisError("input_changed") from None
