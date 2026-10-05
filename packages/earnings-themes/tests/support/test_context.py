"""Invented structural bounds and canonical evidence rendering only."""

from dataclasses import replace

import pytest
from earnings_core import DocumentElement, ElementType, TextSpan, sha256_hex
from earnings_themes.support.context import context_elements
from earnings_themes.support.problems import SupportError
from earnings_themes.support.prompt import context_text, evidence_text, joint_premise
from earnings_themes.support.records import RefusedTarget, ResolvedInput
from earnings_themes.support.resolve import resolve_target, reverify_input

from .cases import context_bundle, stored_case


def resolve(sources, target):
    return resolve_target(
        sources.stored_run,
        sources.bundles,
        sources.codebook,
        target,
        provenance_hash=sources.provenance_hash,
    )


@pytest.fixture
def resolved(codebook, no_network):
    bundle, sentence = context_bundle()
    text = bundle.document.canonical_text
    spans = tuple(
        (s, s + len("Orion improved"), e.element_id)
        for s, e in [
            (text.index("Orion"), sentence),
            (text.rindex("Orion"), bundle.elements[-1]),
        ]
    )
    result = resolve(*stored_case(bundle, codebook, "Output improved.", spans[::-1]))
    assert isinstance(result, ResolvedInput)
    yield result
    assert no_network == []


def test_partial_evidence_does_not_gain_context_as_premise(resolved):
    premise = joint_premise(resolved)
    assert all(evidence_text(resolved, r) in premise for r in resolved.evidence)
    assert "INVENTED_CONTEXT_ONLY_ASSERTION" not in premise
    assert "PASSAGE 1 [" in premise and "END PASSAGE 2" in premise
    assert [r.kind for r in resolved.contexts] == ["heading", "block"]
    assert "INVENTED_CONTEXT_ONLY_ASSERTION" in context_text(
        resolved, resolved.contexts[1]
    )
    assert all(r.target_id == resolved.record.target_id for r in resolved.contexts)
    assert isinstance(reverify_input(resolved), ResolvedInput)


@pytest.mark.parametrize("kind", ["paragraph", "list_item", "footnote"])
def test_nearest_narrative_ancestor_including_self(kind):
    bundle, sentence = context_bundle()
    block = DocumentElement.create(
        bundle.document,
        ElementType(kind),
        sentence.span,
        parent_id=bundle.elements[4].element_id,
    )
    child = sentence.model_copy(update={"parent_id": block.element_id})
    bundle = replace(bundle, elements=(*bundle.elements[:5], block, child))
    assert context_elements(bundle, child.element_id)[-1] == block
    assert context_elements(bundle, block.element_id)[-1] == block


def test_nearest_section_excludes_outer_heading():
    bundle, sentence = context_bundle()
    assert context_elements(bundle, sentence.element_id) == (
        bundle.elements[3],
        bundle.elements[4],
    )
    without = replace(
        bundle, elements=tuple(e for e in bundle.elements if e != bundle.elements[3])
    )
    assert context_elements(without, sentence.element_id) == (bundle.elements[4],)


def test_speaker_bound_is_independent_of_section():
    bundle, sentence = context_bundle()
    paragraph = bundle.elements[4]
    turn = DocumentElement.create(
        bundle.document,
        ElementType.SPEAKER_TURN,
        paragraph.span,
        parent_id=bundle.elements[2].element_id,
    )
    paragraph = paragraph.model_copy(update={"parent_id": turn.element_id})
    bundle = replace(
        bundle, elements=(*bundle.elements[:4], turn, paragraph, *bundle.elements[5:])
    )
    assert context_elements(bundle, sentence.element_id) == (paragraph,)
    assert context_elements(bundle, turn.element_id) == (turn,)


@pytest.mark.parametrize("kind", [ElementType.SECTION, ElementType.SPEAKER_TURN])
def test_fallback_stays_inside_nearest_boundary(kind):
    bundle, sentence = context_bundle()
    bound = DocumentElement.create(
        bundle.document, kind, sentence.span, parent_id=bundle.elements[4].element_id
    )
    child = sentence.model_copy(update={"parent_id": bound.element_id})
    changed = replace(bundle, elements=(*bundle.elements[:5], bound, child))
    assert context_elements(changed, child.element_id) == (child,)


def test_heading_tie_break_by_end_start_then_id():
    bundle, sentence = context_bundle()
    heading = bundle.elements[3]
    narrower = DocumentElement.create(
        bundle.document,
        ElementType.HEADING,
        TextSpan(start=heading.span.start + 1, end=heading.span.end),
    )
    changed = replace(bundle, elements=(*bundle.elements, narrower))
    assert context_elements(changed, sentence.element_id)[0] == narrower
    # The ID tie-break is tested directly; these forged equal-span IDs never resolve.
    a = narrower.model_copy(update={"element_id": "a"})
    z = narrower.model_copy(update={"element_id": "z"})
    changed = replace(bundle, elements=(*bundle.elements, z, a))
    assert context_elements(changed, sentence.element_id)[0] == a


def test_single_quote_joint_input_is_exact_evidence(codebook):
    bundle, sentence = context_bundle()
    spans = (
        (sentence.span.start, sentence.span.start + len("Orion"), sentence.element_id),
    )
    result = resolve(*stored_case(bundle, codebook, "Output improved.", spans))
    assert joint_premise(result) == "Orion"


@pytest.mark.parametrize(
    "accessor,field,value",
    [
        (evidence_text, "canonical_hash", "0" * 64),
        (evidence_text, "text_hash", "0" * 64),
        (evidence_text, "doc_id", "invented-missing"),
        (evidence_text, "start", True),
        (context_text, "text_hash", "0" * 64),
        (context_text, "end", 99999),
    ],
)
def test_views_reject_changed_references(resolved, accessor, field, value):
    ref = resolved.evidence[0] if accessor is evidence_text else resolved.contexts[0]
    with pytest.raises(SupportError, match="^input_changed$"):
        accessor(resolved, ref.model_copy(update={field: value}))


def test_views_reject_changed_canonical_text(resolved):
    bundle = resolved.sources.bundles[0]
    changed = replace(
        bundle,
        document=bundle.document.model_copy(
            update={
                "canonical_text": bundle.document.canonical_text + "INVENTED_CHANGE"
            }
        ),
    )
    forged = replace(resolved, sources=replace(resolved.sources, bundles=(changed,)))
    with pytest.raises(SupportError, match="^input_changed$"):
        evidence_text(forged, resolved.evidence[0])


def test_contexts_are_hash_bound_and_reverified(resolved):
    for ref in resolved.contexts:
        assert ref.text_hash == sha256_hex(context_text(resolved, ref).encode("utf-8"))
    refused = reverify_input(replace(resolved, contexts=()))
    assert isinstance(refused, RefusedTarget)
    assert refused.outcome.missing == ("input_changed",)


@pytest.mark.parametrize("accessor", [evidence_text, context_text])
def test_arbitrary_canonical_slice_cannot_replace_retained_reference(
    resolved, accessor
):
    ref = resolved.evidence[0] if accessor is evidence_text else resolved.contexts[0]
    doc = resolved.sources.bundles[0].document
    end = ref.end - 1
    forged = ref.model_copy(
        update={
            "end": end,
            "text_hash": sha256_hex(
                doc.canonical_text[ref.start : end].encode("utf-8")
            ),
        }
    )
    with pytest.raises(SupportError, match="^input_changed$"):
        accessor(resolved, forged)


def test_context_document_order_is_independent_of_claim_link_order(case):
    resolved = resolve(*case)
    assert [ref.start for ref in resolved.contexts] == sorted(
        ref.start for ref in resolved.contexts
    )
    assert len(resolved.contexts) == 2
    assert all(ref.kind == "block" for ref in resolved.contexts)


def test_evidence_view_preserves_unicode_and_whitespace(codebook):
    bundle, _sentence = context_bundle()
    text = bundle.document.canonical_text.replace("Orion improved", "Oríon  improved")
    from earnings_core import CanonicalDocument
    from earnings_themes.anchoring import Bundle

    doc = CanonicalDocument.create(
        source_document_id="invented-unicode",
        canonicalization_version="test-1",
        canonical_text=text,
    )
    element = DocumentElement.create(
        doc, ElementType.PARAGRAPH, TextSpan(start=0, end=len(text))
    )
    start = text.index("Oríon")
    result = resolve(
        *stored_case(
            Bundle("invented-unicode", doc, (element,), ()),
            codebook,
            "Output improved.",
            ((start, start + len("Oríon  improved"), element.element_id),),
        )
    )
    assert evidence_text(result, result.evidence[0]) == "Oríon  improved"


def test_context_reference_cannot_be_rendered_as_evidence(resolved):
    with pytest.raises(SupportError, match="^input_changed$"):
        evidence_text(resolved, resolved.contexts[0])
    with pytest.raises(SupportError, match="^input_changed$"):
        context_text(resolved, resolved.evidence[0])
