"""The canonicalizer's records keep their evidence consistent with their reason."""

import pytest
from earnings_core import (
    CanonicalDocument,
    Rejection,
    RejectionReason,
    apply_masks,
    sha256_hex,
)
from earnings_ingestion.canonical import (
    CanonicalizationFailure,
    Canonicalized,
    FailureReason,
    canonicalize,
)
from pydantic import ValidationError

RAW = b"<p>Revenue rose.</p>"
REJECTION = Rejection(reason=RejectionReason.CROSSING_ELEMENTS, detail="planted")


def failure(reason: FailureReason, **evidence: object) -> CanonicalizationFailure:
    return CanonicalizationFailure(
        source_document_id="doc-1",
        raw_sha256=sha256_hex(RAW),
        canonicalization_version="walker-1",
        reason=reason,
        detail="test",
        **evidence,
    )


def test_each_reason_records_its_own_evidence() -> None:
    assert failure(FailureReason.NO_NATIVE_TEXT, image_count=3).image_count == 3
    assert failure(FailureReason.INVALID_ELEMENTS, rejections=(REJECTION,)).rejections
    assert failure(FailureReason.PARSE_FAILED).image_count is None


@pytest.mark.parametrize(
    ("reason", "evidence"),
    [
        (FailureReason.NO_NATIVE_TEXT, {}),
        (FailureReason.PARSE_FAILED, {"image_count": 0}),
        (FailureReason.INVALID_ELEMENTS, {}),
        (FailureReason.UNSUPPORTED_MEDIA_TYPE, {"rejections": (REJECTION,)}),
    ],
    ids=[
        "no-text-without-images",
        "images-on-a-parse-failure",
        "invalid-without-rejections",
        "rejections-on-a-media-type",
    ],
)
def test_evidence_that_does_not_fit_the_reason_is_refused(
    reason: FailureReason, evidence: dict[str, object]
) -> None:
    with pytest.raises(ValidationError):
        failure(reason, **evidence)


def result() -> Canonicalized:
    made = canonicalize(RAW, source_document_id="doc-1", media_type="text/html")
    assert isinstance(made, Canonicalized)
    return made


def test_a_result_whose_parts_disagree_is_refused() -> None:
    made = result()
    other = CanonicalDocument.create(
        source_document_id="doc-2",
        canonicalization_version="walker-1",
        canonical_text="Other.",
    )
    foreign_masks = apply_masks(other, [], policy_id="boilerplate", policy_version="1")
    with pytest.raises(ValidationError, match="masks belong to another document"):
        Canonicalized(
            document=made.document,
            elements=made.elements,
            masked=foreign_masks,
            manifest=made.manifest,
        )
    with pytest.raises(ValidationError, match="manifest describes another document"):
        Canonicalized(
            document=other,
            elements=(),
            masked=foreign_masks,
            manifest=made.manifest,
        )
    with pytest.raises(ValidationError, match="element belongs to another document"):
        Canonicalized(
            document=other,
            elements=made.elements,
            masked=foreign_masks,
            manifest=made.manifest.model_copy(update={"source_document_id": "doc-2"}),
        )


def test_another_schema_version_is_refused() -> None:
    payload = result().manifest.model_dump()
    payload["schema_version"] = 2
    with pytest.raises(ValidationError):
        type(result().manifest).model_validate(payload)
