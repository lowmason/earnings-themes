"""Blind-safe coding prompts against the permitted canonical Stage 1 fixtures."""

import json
from pathlib import Path

from earnings_core import CanonicalDocument, canonical_json
from earnings_themes.wording import markdown_paragraphs, shared

REPO = Path(__file__).resolve().parents[2]


def test_coding_prompts_do_not_quote_stage1():
    paths = sorted((REPO / "prompts" / "coding").glob("*.md"))
    assert [path.name for path in paths] == ["deductive-1.md"]
    strings = [
        paragraph
        for path in paths
        for paragraph in markdown_paragraphs(
            path.read_text(encoding="utf-8"), path.name
        )
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
