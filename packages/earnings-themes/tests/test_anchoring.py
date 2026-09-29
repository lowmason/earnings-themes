"""The anchor and the pointer check (the Stage 6 spec, §Anchoring and validation):
a quote occurs once, sits in narrative, passes Stage 2's checks, and is committed as
offsets and hashes that the local document reproduces."""

import pytest
from earnings_core import RejectionReason, TextSpan, make_locator
from earnings_themes.anchoring import (
    SpanPointer,
    anchor,
    bundle_problems,
    check_pointer,
    context_hash,
    mask_id,
    quote_hash,
)
from earnings_themes.problems import Problem


def test_a_unique_sentence_is_anchored_to_its_sentence(synthetic) -> None:
    pointer = anchor(synthetic.bundle, "Margins held steady.")
    assert isinstance(pointer, SpanPointer)
    span = synthetic.spans["sentence 2"]
    assert (pointer.start, pointer.end) == (span.start, span.end)
    assert pointer.element_id == f"sentence-{span.start}-{span.end}"
    assert pointer.quote_sha256 == quote_hash("Margins held steady.")
    assert pointer.context_sha256 is None
    assert pointer.mask_ids == ()
    assert check_pointer(synthetic.bundle, pointer) == []


def test_repeated_text_needs_context_and_records_its_hash(synthetic) -> None:
    repeated = synthetic.text("repeat")
    assert anchor(synthetic.bundle, repeated) == "ambiguous_occurrence"
    pointer = anchor(synthetic.bundle, repeated, prefix="steady.\n")
    assert isinstance(pointer, SpanPointer)
    assert pointer.start == synthetic.spans["repeat"].start
    locator = make_locator(
        synthetic.bundle.document, TextSpan(start=pointer.start, end=pointer.end)
    )
    assert locator.prefix or locator.suffix
    assert pointer.context_sha256 == context_hash(locator.prefix, locator.suffix)
    assert check_pointer(synthetic.bundle, pointer) == []


def test_text_that_is_not_there_is_not_found(synthetic) -> None:
    assert anchor(synthetic.bundle, "Revenue fell.") == "locator_not_found"
    assert anchor(synthetic.bundle, "") == "malformed"


@pytest.mark.parametrize(
    ("name", "reason"),
    [
        ("cell 1", Problem.NOT_NARRATIVE),
        ("table", Problem.NOT_NARRATIVE),
        ("artifact", Problem.NOT_NARRATIVE),
        ("scanned", RejectionReason.OCR_DERIVED_TEXT),
    ],
)
def test_a_quote_outside_native_narrative_is_refused(synthetic, name, reason) -> None:
    assert anchor(synthetic.bundle, synthetic.text(name)) == reason.value


def test_a_quote_across_two_elements_is_outside_every_element(synthetic) -> None:
    across = synthetic.bundle.document.canonical_text[
        synthetic.spans["heading"].start : synthetic.spans["sentence 1"].end
    ]
    assert anchor(synthetic.bundle, across) == "outside_element"


def test_a_masked_quote_is_allowed_and_its_masks_are_recorded(synthetic) -> None:
    pointer = anchor(synthetic.bundle, synthetic.text("harbor"))
    assert isinstance(pointer, SpanPointer)
    (mask,) = synthetic.bundle.masks
    assert pointer.mask_ids == (mask_id(mask),)
    assert mask_id(mask) == f"safe_harbor-{mask.span.start}-{mask.span.end}"


@pytest.mark.parametrize(
    ("change", "reasons"),
    [
        ({"start": 1}, ["quote_hash_mismatch", "outside_element"]),
        ({"quote_sha256": "0" * 64}, ["quote_hash_mismatch"]),
        ({"context_sha256": "0" * 64}, ["context_hash_mismatch"]),
        ({"mask_ids": ("safe_harbor-0-1",)}, ["masks_mismatch"]),
        ({"element_id": "paragraph-0-1"}, ["unknown_element"]),
        ({"end": 10_000}, ["span_out_of_bounds"]),
    ],
)
def test_a_tampered_pointer_is_refused(synthetic, change, reasons) -> None:
    pointer = anchor(synthetic.bundle, "Margins held steady.")
    assert isinstance(pointer, SpanPointer)
    tampered = SpanPointer(**{**pointer.model_dump(), **change})
    assert check_pointer(synthetic.bundle, tampered) == reasons


def test_a_pointer_into_a_table_cell_is_not_narrative(synthetic) -> None:
    span = synthetic.spans["cell 1"]
    pointer = SpanPointer(
        start=span.start,
        end=span.end,
        element_id=f"table_cell-{span.start}-{span.end}",
        quote_sha256=quote_hash(synthetic.text("cell 1")),
    )
    assert check_pointer(synthetic.bundle, pointer) == ["not_narrative"]

    exact = anchor(synthetic.bundle, "Margins held steady.")
    assert isinstance(exact, SpanPointer)
    exact_span = TextSpan(start=exact.start, end=exact.end)
    paragraph = next(
        e
        for e in synthetic.bundle.elements
        if e.type.value == "paragraph" and e.span.contains(exact_span)
    )
    mismatched = SpanPointer(
        **{**exact.model_dump(), "element_id": paragraph.element_id}
    )
    assert check_pointer(synthetic.bundle, mismatched) == ["element_mismatch"]
    assert check_pointer(synthetic.bundle, exact) == []


def test_the_synthetic_bundle_is_sound(synthetic) -> None:
    assert bundle_problems(synthetic.bundle) == []


def test_every_unique_narrative_sentence_of_the_stage_1_fixtures_anchors(
    fixtures,
) -> None:
    anchored = 0
    for bundle in fixtures.values():
        assert bundle_problems(bundle) == []
        text = bundle.document.canonical_text
        for element in bundle.elements:
            if element.type.value != "sentence":
                continue
            exact = text[element.span.start : element.span.end]
            pointer = anchor(bundle, exact)
            if isinstance(pointer, str):
                assert pointer in {"ambiguous_occurrence", "not_narrative"}
                continue
            assert pointer.element_id == element.element_id
            assert check_pointer(bundle, pointer) == []
            anchored += 1
    assert anchored > 500
