import pytest
from earnings_core.documents import CanonicalDocument
from earnings_core.evidence import VerifiedSpan, validate_span
from earnings_core.hashing import hash_canonical_text
from earnings_core.masks import MaskCategory, MaskedDocument, OverlayMask, apply_masks
from earnings_core.spans import TextSpan
from pydantic import ValidationError

POLICY = {"policy_id": "boilerplate", "policy_version": "1"}


def mask_over(document: CanonicalDocument, span: TextSpan, **changes) -> OverlayMask:
    fields: dict[str, object] = {
        "doc_id": document.doc_id,
        "canonical_hash": document.canonical_hash,
        "span": span,
        "category": MaskCategory.SAFE_HARBOR,
        **POLICY,
    }
    fields.update(changes)
    return OverlayMask(**fields)


def test_applying_a_mask_leaves_the_text_and_hash_unchanged(sample) -> None:
    before_text = sample.document.canonical_text
    before_hash = sample.document.canonical_hash
    mask = mask_over(sample.document, sample.span_of("Results are preliminary."))
    masked = apply_masks(sample.document, [mask], **POLICY)
    assert masked.document.canonical_text == before_text
    assert masked.document.canonical_hash == before_hash
    assert hash_canonical_text(masked.document.canonical_text) == before_hash
    assert masked.document.doc_id == sample.document.doc_id


def test_a_masked_span_still_verifies_and_is_reported_for_audit(sample) -> None:
    span = sample.span_of("Results are preliminary.")
    mask = mask_over(sample.document, span)
    masked = apply_masks(sample.document, [mask], **POLICY)
    verified = validate_span(
        masked.document, sample.elements, sample.candidate("Results are preliminary.")
    )
    assert isinstance(verified, VerifiedSpan)
    assert masked.masks_overlapping(verified.span) == (mask,)
    assert masked.masks_overlapping(sample.span_of("Margins held")) == ()


def test_a_policy_that_found_nothing_is_still_recorded(sample) -> None:
    masked = apply_masks(sample.document, [], **POLICY)
    assert (masked.policy_id, masked.policy_version, masked.masks) == (
        "boilerplate",
        "1",
        (),
    )


def test_a_mask_of_another_version_is_refused(sample) -> None:
    newer = CanonicalDocument.create(
        source_document_id="sample-call",
        canonicalization_version="test-1",
        canonical_text=sample.text.replace("5%", "6%"),
    )
    stale = mask_over(sample.document, sample.span_of("Margins held"))
    with pytest.raises(ValueError, match="belongs to"):
        apply_masks(newer, [stale], **POLICY)


def test_a_mask_past_the_text_is_refused(sample) -> None:
    beyond = mask_over(sample.document, TextSpan(start=0, end=len(sample.text) + 1))
    with pytest.raises(ValueError, match="runs past"):
        apply_masks(sample.document, [beyond], **POLICY)


def test_masks_from_two_policy_versions_are_refused(sample) -> None:
    older = mask_over(
        sample.document, sample.span_of("Margins held"), policy_version="0"
    )
    with pytest.raises(ValueError, match="under policy"):
        apply_masks(sample.document, [older], **POLICY)


def test_a_mask_round_trips_through_json(sample) -> None:
    mask = mask_over(
        sample.document,
        sample.span_of("Margins held"),
        category=MaskCategory.NON_GAAP_DISCLAIMER,
    )
    assert OverlayMask.model_validate_json(mask.model_dump_json()) == mask


def test_a_directly_built_masked_document_is_checked_too(sample) -> None:
    newer = CanonicalDocument.create(
        source_document_id="sample-call",
        canonicalization_version="test-1",
        canonical_text=sample.text.replace("5%", "6%"),
    )
    stale = mask_over(sample.document, sample.span_of("Margins held"))
    with pytest.raises(ValidationError, match="belongs to"):
        MaskedDocument(document=newer, masks=(stale,), **POLICY)
    beyond = mask_over(sample.document, TextSpan(start=0, end=len(sample.text) + 1))
    with pytest.raises(ValidationError, match="runs past"):
        MaskedDocument(document=sample.document, masks=(beyond,), **POLICY)
    older = mask_over(
        sample.document, sample.span_of("Margins held"), policy_version="0"
    )
    with pytest.raises(ValidationError, match="under policy"):
        MaskedDocument(document=sample.document, masks=(older,), **POLICY)


def test_a_tampered_document_cannot_carry_masks(sample) -> None:
    tampered = sample.document.model_copy(update={"canonical_text": "changed"})
    with pytest.raises(ValidationError, match="canonical_hash"):
        MaskedDocument(document=tampered, masks=(), **POLICY)
    with pytest.raises(ValueError, match="canonical_hash"):
        apply_masks(tampered, [], **POLICY)
