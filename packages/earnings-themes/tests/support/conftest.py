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
