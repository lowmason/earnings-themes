"""M1-M5: each rule's positive and negative cases (Stage 3 spec: Verification, item 9)."""

import pytest
from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    MaskCategory,
    TextSpan,
)
from earnings_ingestion.canonical.boilerplate import (
    POLICY_ID,
    POLICY_VERSION,
    boilerplate_masks,
)

SAFE = MaskCategory.SAFE_HARBOR
NON_GAAP = MaskCategory.NON_GAAP_DISCLAIMER
LEGAL = MaskCategory.REPEATED_LEGAL


def document_of(
    units: list[tuple[ElementType, str]],
) -> tuple[CanonicalDocument, list[DocumentElement]]:
    """One element per unit, one unit per line."""
    text = "\n".join(unit for _, unit in units)
    document = CanonicalDocument.create(
        source_document_id="doc-1",
        canonicalization_version="test-1",
        canonical_text=text,
    )
    elements, start = [], 0
    for element_type, unit in units:
        span = TextSpan(start=start, end=start + len(unit))
        elements.append(DocumentElement.create(document, element_type, span))
        start = span.end + 1
    return document, elements


def masked(units: list[tuple[ElementType, str]]) -> list[MaskCategory | None]:
    """Each unit's mask category, or None when it is not masked."""
    document, elements = document_of(units)
    result = boilerplate_masks(document, elements)
    assert (result.policy_id, result.policy_version) == (POLICY_ID, POLICY_VERSION)
    by_span = {mask.span: mask.category for mask in result.masks}
    return [by_span.get(element.span) for element in elements]


H, P, L, F = (
    ElementType.HEADING,
    ElementType.PARAGRAPH,
    ElementType.LIST_ITEM,
    ElementType.FOOTNOTE,
)
T, A, O = ElementType.TABLE, ElementType.PAGE_ARTIFACT, ElementType.OTHER


@pytest.mark.parametrize(
    "heading",
    [
        "Forward-Looking Statements",
        "Forward-looking information",
        "SAFE HARBOR",
        "Cautionary Statement Regarding Forward-Looking Information",
        "Cautionary note",
    ],
)
def test_m1_masks_a_safe_harbor_heading_and_the_blocks_after_it(heading: str) -> None:
    assert masked(
        [(P, "Revenue rose."), (H, heading), (P, "We may be wrong."), (L, "Risk one.")]
    ) == [None, SAFE, SAFE, SAFE]


def test_m1_stops_at_the_next_heading_or_table() -> None:
    assert masked(
        [
            (H, "Forward-Looking Statements"),
            (P, "We may be wrong."),
            (H, "About Acme"),
            (P, "Acme makes widgets."),
            (H, "Safe Harbor"),
            (T, "Item\t2024"),
            (P, "After the table."),
        ]
    ) == [SAFE, SAFE, None, None, SAFE, None, None]


def test_m1_skips_page_artifacts_and_other_elements() -> None:
    assert masked(
        [
            (H, "Forward-Looking Statements"),
            (A, "Page 3 of 9"),
            (O, "2024"),
            (F, "(1) As restated."),
        ]
    ) == [SAFE, None, None, SAFE]


def test_m1_needs_a_heading() -> None:
    assert masked([(P, "Forward-Looking Statements"), (P, "We may be wrong.")]) == [
        None,
        None,
    ]


def test_m2_masks_a_non_gaap_heading_and_its_extent() -> None:
    assert masked(
        [(H, "Use of Non-GAAP Financial Measures"), (P, "We use adjusted EBITDA.")]
    ) == [NON_GAAP, NON_GAAP]


def test_m1_wins_over_m2_on_one_heading() -> None:
    assert masked(
        [(H, "Forward-Looking Statements and Non-GAAP Measures"), (P, "Text.")]
    ) == [SAFE, SAFE]


def test_an_extent_rule_wins_over_a_block_rule() -> None:
    assert masked(
        [
            (H, "Non-GAAP Measures"),
            (P, "This release contains forward-looking statements with risks."),
        ]
    ) == [NON_GAAP, NON_GAAP]


@pytest.mark.parametrize(
    "block",
    [
        "Statements are made under the Private Securities Litigation Reform Act of 1995.",
        "These forward-looking statements involve risks.",
        "Forward-looking statements carry uncertainties.",
        "Do not place undue reliance on forward-looking statements.",
        "Actual results may differ from forward-looking statements.",
    ],
)
def test_m3_masks_safe_harbor_blocks(block: str) -> None:
    assert masked([(P, block)]) == [SAFE]


@pytest.mark.parametrize(
    "block",
    [
        "Forward-looking statements are discussed below.",
        "We face risks and uncertainties.",
    ],
)
def test_m3_needs_both_parts(block: str) -> None:
    assert masked([(P, block)]) == [None]


@pytest.mark.parametrize(
    "tail",
    [
        "are not prepared in accordance with GAAP.",
        "are not a substitute for GAAP results.",
        "should not be viewed in isolation.",
        "should not be considered alone.",
    ],
)
def test_m4_masks_non_gaap_disclaimers(tail: str) -> None:
    assert masked([(F, f"Non-GAAP measures {tail}")]) == [NON_GAAP]


def test_m4_needs_both_parts() -> None:
    assert masked([(P, "Non-GAAP earnings rose 5%.")]) == [None]


@pytest.mark.parametrize(
    "block",
    [
        "Acme is a registered trademark of Acme Corp.",
        "Widget and Gadget are trademarks of Acme Corp.",
        "This information shall not be deemed filed for any purpose.",
        "This release does not constitute an offer to sell securities.",
        "Where to Find It: the proxy statement is available online.",
        "Directors are participants in the solicitation of proxies.",
    ],
)
def test_m5_masks_repeated_legal_blocks(block: str) -> None:
    assert masked([(P, block)]) == [LEGAL]


def test_m5_needs_both_parts_of_the_deemed_filed_rule() -> None:
    assert masked([(P, "This shall not be deemed an admission.")]) == [None]


def test_masks_never_cover_tables_cells_artifacts_or_other() -> None:
    legal = "Acme is a registered trademark of Acme Corp."
    assert masked([(T, legal), (A, legal), (O, legal)]) == [None, None, None]


def test_masks_leave_the_document_untouched() -> None:
    document, elements = document_of([(P, "Acme is a registered trademark.")])
    result = boilerplate_masks(document, elements)
    assert result.document == document
    assert [mask.span for mask in result.masks] == [elements[0].span]
