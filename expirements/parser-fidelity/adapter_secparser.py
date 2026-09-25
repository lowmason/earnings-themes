# /// script
# requires-python = ">=3.13,<3.14"
# dependencies = ["sec-parser==0.58.1"]
# ///
"""Candidate adapter: sec-parser 0.58.1, run in isolation.

Python 3.13, because sec-parser 0.58.1 requires lxml<6, which publishes no CPython
3.14 wheel (checked 2026-09-22 with ``uv pip compile --python-version 3.14
--only-binary lxml``). The parse path is the library's documented default:
``Edgar10QParser().parse(html)``, which returns a flat list (no nesting) and drops
IrrelevantElement subclasses. A table's text is exactly what the element emits; the
library exposes no cell grid.

    uv run --locked --script expirements/parser-fidelity/adapter_secparser.py --input S --output D --sidecar C
    uv run --locked --script expirements/parser-fidelity/adapter_secparser.py --self-check

Type mapping (class name, most specific first in the element's MRO -> common type).
"""

from __future__ import annotations

import sys

from pf_dump import Element, run_adapter

TYPE_BY_CLASS = {
    "TopSectionTitle": "heading",
    "TitleElement": "heading",
    "TableOfContentsElement": "table",
    "TableElement": "table",
    "TextElement": "paragraph",
    "SupplementaryText": "paragraph",
    "HighlightedTextElement": "other",
    "ImageElement": "other",
    "PageHeaderElement": "other",
    "PageNumberElement": "other",
    "EmptyElement": "other",
    "IntroductorySectionElement": "other",
    "IrrelevantElement": "other",
    "NotYetClassifiedElement": "other",
    "ErrorWhileProcessingElement": "other",
    "CompositeSemanticElement": "other",
    "AbstractSemanticElement": "other",
}


def common_type(element: object) -> str:
    for cls in type(element).__mro__:
        if cls.__name__ in TYPE_BY_CLASS:
            return TYPE_BY_CLASS[cls.__name__]
    raise TypeError(f"unmapped sec-parser element type {type(element).__name__}")


def convert(elements: list[object]) -> list[Element]:
    out = []
    for element in elements:
        kind = common_type(element)
        level = getattr(element, "level", None) if kind == "heading" else None
        out.append(
            Element(kind, element.text or "", None, level, type(element).__name__)
        )
    return out


def parse(html: str) -> list[Element]:
    import sec_parser  # imported after the network guard is installed

    return convert(sec_parser.Edgar10QParser().parse(html))


def self_check() -> int:
    """Every exported semantic element class must be mapped; run before the freeze."""
    import inspect

    import sec_parser
    from sec_parser.semantic_elements.abstract_semantic_element import (
        AbstractSemanticElement,
    )

    exported = {
        name
        for name, obj in inspect.getmembers(sec_parser, inspect.isclass)
        if issubclass(obj, AbstractSemanticElement)
    }
    unmapped = sorted(exported - set(TYPE_BY_CLASS))
    print(f"exported element classes: {sorted(exported)}")
    print(f"unmapped: {unmapped}")
    return 1 if unmapped else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-check"]:
        raise SystemExit(self_check())
    raise SystemExit(run_adapter(parse, library="sec-parser"))
