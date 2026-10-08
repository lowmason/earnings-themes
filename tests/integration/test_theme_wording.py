"""Task 11 wording check uses only explicitly permitted Stage 1 canonical fixtures."""

import ast
import json

from earnings_themes.wording import markdown_paragraphs, shared

from tests.integration import stage10_cases
from tests.integration.stage10_cases import REPO

no_network = stage10_cases.no_network


def test_stage10_prompts_templates_and_verification_quote_no_stage1(no_network):
    strings = []
    for relative in (
        "prompts/extraction/pointer-1.md",
        "prompts/coding/deductive-1.md",
        "prompts/support/judge-1.md",
        "docs/verification/theme-vertical-slice.md",
    ):
        strings.extend(
            markdown_paragraphs((REPO / relative).read_text(), "stage10-wording")
        )
    for relative in (
        "apps/earnings-pipeline/src/earnings_pipeline/theme_report.py",
        "apps/earnings-pipeline/src/earnings_pipeline/evidence_views.py",
    ):
        tree = ast.parse((REPO / relative).read_text())
        strings.extend(
            ("stage10-template", node.value)
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        )
    texts = []
    for path in sorted((REPO / "tests/fixtures/canonical").glob("*.json")):
        texts.append(
            (
                "stage1-fixture",
                json.loads(path.read_bytes())["document"]["canonical_text"],
            )
        )
    assert len(texts) > 0
    assert len(shared(strings, texts)) == 0, "stage10_wording_overlap"

    assert no_network == []
