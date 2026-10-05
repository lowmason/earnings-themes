"""Only invented text; inherited socket guard protects all resolver tests."""

import pytest
from earnings_core import CanonicalDocument, DocumentElement, ElementType, TextSpan
from earnings_themes.anchoring import Bundle

from .cases import stored_case


@pytest.fixture
def case(codebook, no_network):
    text = "Orion expanded its workshop.\nThe new tooling reduced delays."
    doc = CanonicalDocument.create(
        source_document_id="invented-support",
        canonicalization_version="test-1",
        canonical_text=text,
    )
    ends = (text.index("\n"), len(text))
    spans = ((0, ends[0]), (ends[0] + 1, ends[1]))
    elements = tuple(
        DocumentElement.create(doc, ElementType.PARAGRAPH, TextSpan(start=s, end=e))
        for s, e in spans
    )
    bundle = Bundle("invented", doc, elements, ())
    result = stored_case(
        bundle,
        codebook,
        "Workshop expansion reduced delays.",
        tuple((e.span.start, e.span.end, e.element_id) for e in reversed(elements)),
    )
    yield result
    assert no_network == []


@pytest.fixture
def one_quote(codebook, no_network):
    from .cases import context_bundle, resolved_case

    bundle, sentence = context_bundle()
    yield resolved_case(
        *stored_case(
            bundle,
            codebook,
            "Orion improved output.",
            ((sentence.span.start, sentence.span.end, sentence.element_id),),
        )
    )
    assert no_network == []


@pytest.fixture
def scorer_identity():
    from earnings_themes.support.records import RuntimeIdentity, ScorerIdentity

    return ScorerIdentity(
        kind="scripted",
        input_limit=1000,
        runtime=RuntimeIdentity(
            model_id="invented-scorer",
            revision="test-1",
            files=(),
            runtime="scripted",
            runtime_version="1",
            device="cpu",
            precision="float32",
            encoding_version="test-1",
        ),
    )
