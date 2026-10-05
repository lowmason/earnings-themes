"""The anchor and the pointer check (the Stage 6 spec, §Anchoring and validation):
a quote occurs once, sits in narrative, passes Stage 2's checks, and is committed as
offsets and hashes that the local document reproduces."""

import json
from collections import Counter
from dataclasses import replace

import pytest
from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    OverlayMask,
    RejectionReason,
    TextSpan,
    make_locator,
    sha256_hex,
)
from earnings_themes.anchoring import (
    Bundle,
    SpanPointer,
    anchor,
    bundle_problems,
    check_pointer,
    context_hash,
    mask_id,
    narrative_home,
    quote_hash,
)
from earnings_themes.annotation import (
    CuratedDraft,
    GoldDraft,
    build_curated,
    build_gold,
    validate_curated,
    validate_gold,
)
from earnings_themes.gold import Gold, GoldQuote, HardNegativeSet
from earnings_themes.problems import Problem, Refusal
from earnings_themes.records import parse
from earnings_themes.synthetic import PIN, curated_draft, gold_draft, synthetic_split

SIGNED = "Lowell Mason (verified a Claude draft)"


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
def test_a_tampered_pointer_is_refused(
    synthetic, codebook, fixtures, change, reasons
) -> None:
    """The check gives each tampered field's reasons, and the validators refuse a
    signed record whose first quote is tampered alike, naming the quote."""
    pointer = anchor(synthetic.bundle, "Margins held steady.")
    assert isinstance(pointer, SpanPointer)
    tampered = SpanPointer(**{**pointer.model_dump(), **change})
    assert check_pointer(synthetic.bundle, tampered) == reasons

    draft = parse(gold_draft(annotator=SIGNED), GoldDraft, "draft")
    split = synthetic_split()
    gold = build_gold(
        draft, draft, bundle=synthetic.bundle, pin=PIN, split=split, codebook=codebook
    )
    assert isinstance(gold, Gold)
    first = gold.quotes[0]
    assert first.quote_id == "q1"
    assert SpanPointer(**first.model_dump(exclude={"quote_id", "origin"})) == pointer
    quote = GoldQuote(**tampered.model_dump(), quote_id="q1", origin=first.origin)
    refusals = validate_gold(
        gold.model_copy(update={"quotes": (quote, *gold.quotes[1:])}),
        bundle=synthetic.bundle,
        pin=PIN,
        split=split,
        codebook=codebook,
    )
    assert refusals == [Refusal("quote q1", reason) for reason in reasons]

    if "quote_sha256" in change:
        curated = parse(curated_draft(fixtures, SIGNED), CuratedDraft, "curated")
        record = build_curated(
            curated, curated, bundles=fixtures, pin=PIN, codebook=codebook
        )
        assert isinstance(record, HardNegativeSet)
        document = record.documents[0]
        assert document.quotes[0].quote_id == "q1"
        quote = GoldQuote(**{**document.quotes[0].model_dump(), **change})
        document = document.model_copy(update={"quotes": (quote, *document.quotes[1:])})
        refusals = validate_curated(
            record.model_copy(update={"documents": (document, *record.documents[1:])}),
            bundles=fixtures,
            pin=PIN,
            codebook=codebook,
        )
        subject = f"{document.fixture_id} quote q1"
        assert refusals == [Refusal(subject, reason) for reason in reasons]


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


def remask(bundle: Bundle, **change: object) -> Bundle:
    """``bundle`` with its one mask changed, and constructed again, so validated."""
    (mask,) = bundle.masks
    fields = {name: getattr(mask, name) for name in OverlayMask.model_fields}
    return replace(bundle, masks=(OverlayMask(**{**fields, **change}),))


def test_a_mask_of_another_document_or_past_the_text_is_wrong_document(
    synthetic,
) -> None:
    """T6-M4: ``bundle_problems``' mask branch. A mask whose ``doc_id`` or hash is
    another document's, or whose span ends past the text, is ``wrong_document``,
    reported once however many masks are."""
    bundle = synthetic.bundle
    other = CanonicalDocument.create(
        source_document_id="0009990002-25-000001_ex991.htm",
        canonicalization_version="walker-1",
        canonical_text="Invented text.\n",
    )
    end = len(bundle.document.canonical_text)
    wrong = [RejectionReason.WRONG_DOCUMENT.value]
    for changed in (
        remask(bundle, doc_id=other.doc_id, canonical_hash=other.canonical_hash),
        remask(bundle, canonical_hash=other.canonical_hash),
        remask(bundle, span=TextSpan(start=end - 1, end=end + 1)),
    ):
        assert bundle_problems(changed) == wrong
        (mask,) = changed.masks
        assert bundle_problems(replace(changed, masks=(mask, mask))) == wrong


def list_bundle(lead: str, between: str = "", tail: str = "") -> Bundle:
    """Invented text: a heading; a list container of type ``other``, as walker-1
    makes one (W7), whose two list items hold one sentence each, with ``lead``,
    ``between``, and ``tail`` as the container's own text before its first item,
    after the newline between its items, and after its last item; and a
    4-character ``other`` div."""
    text = f"Outlook\n{lead}Sales rose.\n{between}Costs fell.{tail}\nNote\n"
    document = CanonicalDocument.create(
        source_document_id="0009990001-25-000002_ex991.htm",
        canonicalization_version="walker-1",
        canonical_text=text,
    )

    def span(needle: str) -> TextSpan:
        start = text.index(needle)
        return TextSpan(start=start, end=start + len(needle))

    first, second = span("Sales rose."), span("Costs fell.")
    container = DocumentElement.create(
        document,
        ElementType.OTHER,
        TextSpan(start=first.start - len(lead), end=second.end + len(tail)),
    )
    elements = [
        DocumentElement.create(document, ElementType.HEADING, span("Outlook"), level=1),
        container,
    ]
    for item_span in (first, second):
        item = DocumentElement.create(
            document, ElementType.LIST_ITEM, item_span, parent_id=container.element_id
        )
        sentence = DocumentElement.create(
            document, ElementType.SENTENCE, item_span, parent_id=item.element_id
        )
        elements += [item, sentence]
    elements.append(DocumentElement.create(document, ElementType.OTHER, span("Note")))
    return Bundle("synthetic-list", document, tuple(elements), ())


def test_only_a_container_whose_children_hold_its_text_is_transparent() -> None:
    """ES9 (T6-M1): an ``other`` element with children and no non-space character
    outside them is a transparent container. It no longer blocks a quote, and it is
    never a quote's home. An ``other`` element with text of its own still blocks,
    and so does a container with text outside its children: before, between, or
    after them."""
    bundle = list_bundle("")
    assert bundle_problems(bundle) == []
    sentence = next(e for e in bundle.elements if e.type is ElementType.SENTENCE)
    pointer = anchor(bundle, "Sales rose.")
    assert isinstance(pointer, SpanPointer)
    assert pointer.element_id == sentence.element_id
    assert narrative_home(bundle, sentence.span) == sentence
    assert check_pointer(bundle, pointer) == []
    container = next(e for e in bundle.elements if e.type is ElementType.OTHER)
    named = SpanPointer(**{**pointer.model_dump(), "element_id": container.element_id})
    assert check_pointer(bundle, named) == ["not_narrative"]
    assert anchor(bundle, "Sales rose.\nCosts fell.") == "outside_element"
    assert anchor(bundle, "Note") == "not_narrative"

    for own in (
        list_bundle("Also: "),
        list_bundle("", between="Then: "),
        list_bundle("", tail=" (est.)"),
    ):
        assert bundle_problems(own) == []
        assert anchor(own, "Sales rose.") == "not_narrative"


def test_every_unique_narrative_sentence_of_the_stage_1_fixtures_anchors(
    fixtures,
) -> None:
    """Each of the 686 sentences of Stage 1's fixtures anchors to itself, or is
    refused because its text repeats: 26 do, so need context. The 10 that sit in a
    list item under an ``other`` element, all in one fixture, anchor, since that
    element is a transparent container (ES9). Plan 10 pinned 650 anchored, 26
    repeated, and those 10 not narrative (T6-M2); plan 11 moves the 10."""
    verdicts: Counter[str] = Counter()
    under_other: Counter[str] = Counter()
    for name, bundle in fixtures.items():
        assert bundle_problems(bundle) == []
        text = bundle.document.canonical_text
        others = [e for e in bundle.elements if e.type.value == "other"]
        items = [
            e
            for e in bundle.elements
            if e.type.value == "list_item"
            and any(other.span.contains(e.span) for other in others)
        ]
        for element in bundle.elements:
            if element.type.value != "sentence":
                continue
            exact = text[element.span.start : element.span.end]
            pointer = anchor(bundle, exact)
            verdict = pointer if isinstance(pointer, str) else "anchored"
            if not isinstance(pointer, str):
                assert pointer.element_id == element.element_id
                assert check_pointer(bundle, pointer) == []
            verdicts[verdict] += 1
            if any(item.span.contains(element.span) for item in items):
                under_other[f"{name}: {verdict}"] += 1
    assert verdicts == {"anchored": 660, "ambiguous_occurrence": 26}
    assert verdicts["not_narrative"] == 0
    assert under_other == {"0000949699-08-000023_ex-99-1: anchored": 10}


def test_context_hash_is_the_sha256_of_a_compact_utf8_json_pair() -> None:
    """T6-M3 (ES8): the byte format the three signed bundles and the curated hard
    negatives store. The pair holds a non-ASCII character, a double quote, and a
    backslash, so ``ensure_ascii=False``, the escaping, and the separators all
    show; an ASCII-only pair could not show the first. Plan 11's Task 6 wrote
    these literals as escape text, from code points."""
    prefix = 'the caf\xe9 line, "net" '
    suffix = " under C:\\notes"
    pair = b'["the caf\xc3\xa9 line, \\"net\\" "," under C:\\\\notes"]'
    expected = "fd4874e7855a8b8d6c9df217cca901d75d1129624089f94a6db6cda22ef52280"
    assert context_hash(prefix, suffix) == expected
    assert sha256_hex(pair) == expected
    escaped = json.dumps([prefix, suffix], separators=(",", ":")).encode("ascii")
    assert escaped != pair
