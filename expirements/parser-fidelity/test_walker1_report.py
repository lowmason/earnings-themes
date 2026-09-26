"""The re-score's projection and verdicts, and the review gate's page-artifact and
mask reports, on synthetic input (Stage 3, plan A)."""

from __future__ import annotations

from dataclasses import astuple

import pytest
import walker as frozen
from earnings_ingestion.canonical import Canonicalized, canonicalize
from earnings_ingestion.canonical.blocks import to_blocks
from earnings_ingestion.canonical.compensate import compensate
from earnings_ingestion.canonical.walker import walk
from score import FixtureScore
from walker1_report import (
    Fixture,
    mask_rows,
    page_artifact_rows,
    project,
    verdict,
)

UNRETYPED = (
    "<html><body>"
    "<h2>Results</h2><p>Revenue rose. Costs fell.</p>"
    "<ul><li>One</li><li>Two<ol><li>Nested</li></ol></li></ul>"
    '<table><tr><th rowspan="2">Item</th><th>2024</th><th></th><th>2023</th></tr>'
    "<tr><td>Q1</td><td></td><td>Q1</td></tr>"
    "<tr><td>Sales</td><td>1,234</td><td></td><td>1,100</td></tr></table>"
    "</body></html>"
)


def canonical(html: str) -> Canonicalized:
    result = canonicalize(html.encode(), source_document_id="t", media_type="text/html")
    assert isinstance(result, Canonicalized), result
    return result


def test_a_projection_without_retypes_is_the_frozen_walkers_dump() -> None:
    result = canonical(UNRETYPED)
    assert result.manifest.retypes == dict.fromkeys(("C1", "C2", "C3", "C4", "C5"), 0)
    dump, sources = project(result.document.canonical_text, result.elements)
    assert [astuple(e) for e in dump] == [astuple(e) for e in frozen.parse(UNRETYPED)]
    assert len(sources) == len(dump)


def test_a_projection_folds_page_artifacts_into_other() -> None:
    result = canonical("<p>EX-99.1 2 x.htm EXHIBIT 99.1</p><p>Body.</p>")
    dump, _ = project(result.document.canonical_text, result.elements)
    assert [(e.type, e.text) for e in dump] == [
        ("other", "EX-99.1 2 x.htm EXHIBIT 99.1"),
        ("paragraph", "Body."),
    ]


@pytest.mark.parametrize(
    ("metric", "before", "after", "expected"),
    [
        ("coverage", (90, 100), (91, 100), "better"),
        ("coverage", (90, 100), (89, 100), "worse"),
        ("header_section", (1, 17), (7, 17), "worse"),
        ("header_table", (12, 12), (4, 12), "better"),
        ("reading_order", (3, 50), (3, 50), "same"),
        ("footnote_merging", (1, 10), (1, 11), "denominator"),
    ],
)
def test_verdicts_compare_exact_counts(
    metric: str, before: tuple[int, int], after: tuple[int, int], expected: str
) -> None:
    assert verdict(metric, before, after) == expected


def fixture_of(html: str, gold_blocks: list[dict]) -> Fixture:
    result = canonical(html)
    blocks, _ = compensate(to_blocks(*walk(html)))
    return Fixture(
        fixture="t",
        klass="synthetic",
        gold={"blocks": gold_blocks},
        result=result,
        blocks=blocks,
        frozen=FixtureScore(),
        c1_only=FixtureScore(),
        walker1=FixtureScore(),
    )


def test_page_artifacts_are_counted_per_anchor_and_unmatched_ones_listed() -> None:
    html = (
        "<p>EX-99.1 2 x.htm EXHIBIT 99.1</p><p>Acme Corp.</p><p>Body one.</p>"
        "<p>Acme Corp.</p><p>Body two.</p><p>Acme Corp.</p><p>- 7 -</p>"
    )
    gold = [
        {"id": "b1", "type": "page_artifact", "start": "EX-99.1 2 x.htm"},
        {"id": "b2", "type": "page_artifact", "start": "Acme Corp."},
        {"id": "b3", "type": "page_artifact", "start": "Acme Corp."},
        {"id": "b4", "type": "page_artifact", "start": "Page 9"},
        {"id": "b5", "type": "paragraph", "start": "Body one."},
    ]
    anchors, unmatched = page_artifact_rows(fixture_of(html, gold))
    assert anchors == [
        {"anchor": "Acme Corp.", "gold": 2, "canonical": 3, "page_artifact": 3},
        {"anchor": "EX-99.1 2 x.htm", "gold": 1, "canonical": 1, "page_artifact": 1},
        {"anchor": "Page 9", "gold": 1, "canonical": 0, "page_artifact": 0},
    ]
    assert [(row["text"], row["rules"]) for row in unmatched] == [("- 7 -", "C3")]


def test_masks_are_listed_and_unmasked_mentions_flagged() -> None:
    html = (
        "<h2>Forward-Looking Statements</h2><p>We may be wrong.</p>"
        "<h2>About Acme</h2><p>Our forward looking view is bright.</p>"
        "<p>Non-GAAP earnings rose.</p><p>Plain text.</p>"
    )
    masks, flagged = mask_rows(fixture_of(html, []))
    assert masks == [
        {
            "category": "safe_harbor",
            "type": "heading",
            "text": "Forward-Looking Statements",
        },
        {"category": "safe_harbor", "type": "paragraph", "text": "We may be wrong."},
    ]
    assert flagged == [
        {"type": "paragraph", "text": "Our forward looking view is bright."},
        {"type": "paragraph", "text": "Non-GAAP earnings rose."},
    ]
