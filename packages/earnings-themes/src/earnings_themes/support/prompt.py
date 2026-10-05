"""Reconstruct separate canonical views; joint scorer input contains evidence only."""

from earnings_core import CanonicalDocument, sha256_hex

from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import (
    ContextReference,
    EvidenceReference,
    ResolvedInput,
)
from earnings_themes.support.resolve import _validated


def _canonical_slice(
    input: ResolvedInput, ref: EvidenceReference | ContextReference
) -> str:
    try:
        if type(ref) is EvidenceReference:
            retained = input.evidence
        elif type(ref) is ContextReference:
            retained = input.contexts
        else:
            raise SupportError("input_changed")
        ref = _validated(ref, type(ref))
        if ref not in retained:
            raise SupportError("input_changed")
        if ref.target_id != input.record.target_id:
            raise SupportError("input_changed")
        bundles = [b for b in input.sources.bundles if b.document.doc_id == ref.doc_id]
        if len(bundles) != 1:
            raise SupportError("input_changed")
        bundle = bundles[0]
        document = _validated(bundle.document, CanonicalDocument)
        elements = [e for e in bundle.elements if e.element_id == ref.element_id]
        if (
            document.canonical_hash != ref.canonical_hash
            or len(elements) != 1
            or not (0 <= ref.start < ref.end <= len(document.canonical_text))
            or elements[0].doc_id != ref.doc_id
            or not (
                elements[0].span.start <= ref.start < ref.end <= elements[0].span.end
            )
        ):
            raise SupportError("input_changed")
        text = document.canonical_text[ref.start : ref.end]
        if sha256_hex(text.encode("utf-8")) != ref.text_hash:
            raise SupportError("input_changed")
        return text
    except (SupportError, AttributeError, TypeError, ValueError, OverflowError):
        raise SupportError("input_changed") from None


def evidence_text(input: ResolvedInput, ref: EvidenceReference) -> str:
    """Materialize the original quote slice, never its containing context."""
    if type(ref) is not EvidenceReference:
        raise SupportError("input_changed")
    return _canonical_slice(input, ref)


def context_text(input: ResolvedInput, ref: ContextReference) -> str:
    """Materialize a separately tagged attribution block or heading."""
    if type(ref) is not ContextReference:
        raise SupportError("input_changed")
    return _canonical_slice(input, ref)


def joint_premise(input: ResolvedInput) -> str:
    """Preserve noncontiguous quotes as individually bounded document-order passages."""
    if len(input.evidence) == 1:
        return evidence_text(input, input.evidence[0])
    return "\n\n".join(
        f"PASSAGE {index} [{ref.quote_id}]\n{evidence_text(input, ref)}\nEND PASSAGE {index}"
        for index, ref in enumerate(input.evidence, 1)
    )
