"""Blind-safe subset: support prompts against committed canonical Stage 1 fixtures."""

import json
from pathlib import Path

from earnings_core import CanonicalDocument, canonical_json
from earnings_themes.wording import markdown_paragraphs, shared

REPO = Path(__file__).resolve().parents[2]


def test_support_prompts_do_not_quote_stage1():
    paths = sorted((REPO / "prompts" / "support").glob("*.md"))
    assert [p.name for p in paths] == ["judge-1.md"]
    strings = [
        item
        for p in paths
        for item in markdown_paragraphs(p.read_text(encoding="utf-8"), p.name)
    ]
    texts = []
    for path in sorted((REPO / "tests" / "fixtures" / "canonical").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        document = CanonicalDocument.model_validate_json(
            canonical_json(data["document"])
        )
        texts.append((path.stem, document.canonical_text))
    found = shared(strings, texts)
    assert found == set()
