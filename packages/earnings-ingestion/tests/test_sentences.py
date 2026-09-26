"""S1 and V9's sentence-splitting cases (Stage 3 spec: Verification (plan A), item 8).

Curly quotes and markers are built from code points, so no tool can normalize them.
"""

import pytest
from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    TextSpan,
    validate_elements,
)
from earnings_ingestion.canonical.sentences import sentence_spans, with_sentences

LEFT_DOUBLE, RIGHT_DOUBLE = chr(0x201C), chr(0x201D)
RIGHT_SINGLE = chr(0x2019)
BULLET, DAGGER, SUPERSCRIPT_ONE = chr(0x2022), chr(0x2020), chr(0x00B9)


def sentences(text: str) -> list[str]:
    return [text[start:end] for start, end in sentence_spans(text)]


def test_sentences_split_at_terminal_punctuation_before_a_capital() -> None:
    assert sentences("Revenue rose. Margins widened! Why? Demand.") == [
        "Revenue rose.",
        "Margins widened!",
        "Why?",
        "Demand.",
    ]


def test_a_digit_can_start_the_next_sentence() -> None:
    assert sentences("Revenue rose. 2024 was strong.") == [
        "Revenue rose.",
        "2024 was strong.",
    ]


def test_a_lowercase_word_never_starts_a_sentence() -> None:
    assert sentences("Revenue rose, e.g. in Asia. Costs fell.") == [
        "Revenue rose, e.g. in Asia.",
        "Costs fell.",
    ]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Mr. Smith spoke. Ms. Jones replied.",
            ["Mr. Smith spoke.", "Ms. Jones replied."],
        ),
        (
            "Acme Corp. Reported results. Beta Ltd. Did too.",
            ["Acme Corp. Reported results.", "Beta Ltd. Did too."],
        ),
        (
            "Sales in the U.S. Rose sharply. Sales in the U.K. Fell.",
            ["Sales in the U.S. Rose sharply.", "Sales in the U.K. Fell."],
        ),
        (
            "The quarter ended Sept. 30 and Dec. Results follow.",
            ["The quarter ended Sept. 30 and Dec. Results follow."],
        ),
        (
            "See Fig. A for details, approx. Ten units.",
            ["See Fig. A for details, approx. Ten units."],
        ),
    ],
    ids=["titles", "company-forms", "places", "months", "other-abbreviations"],
)
def test_listed_abbreviations_end_no_sentence(text: str, expected: list[str]) -> None:
    assert sentences(text) == expected


def test_an_abbreviation_must_start_a_word() -> None:
    assert sentences("It went best. Then it fell.") == [
        "It went best.",
        "Then it fell.",
    ]


def test_initials_end_no_sentence() -> None:
    assert sentences("J.P. Morgan and John F. Kennedy met. Talks ended.") == [
        "J.P. Morgan and John F. Kennedy met.",
        "Talks ended.",
    ]


def test_decimals_and_currency_end_no_sentence_until_the_final_period() -> None:
    assert sentences("EPS was $0.48. Margin was 6.0%. Sales grew 3.5 times.") == [
        "EPS was $0.48.",
        "Margin was 6.0%.",
        "Sales grew 3.5 times.",
    ]


def test_a_m_and_p_m_end_no_sentence() -> None:
    assert sentences("The call is at 8:30 a.m. Eastern, and 5 p.m. Pacific.") == [
        "The call is at 8:30 a.m. Eastern, and 5 p.m. Pacific."
    ]


def test_closing_quotes_and_brackets_belong_to_the_sentence() -> None:
    text = (
        f'He said "growth." Then {LEFT_DOUBLE}more.{RIGHT_DOUBLE} (See note 2.) '
        f"[Done.] It{RIGHT_SINGLE}s over."
    )
    assert sentences(text) == [
        'He said "growth."',
        f"Then {LEFT_DOUBLE}more.{RIGHT_DOUBLE}",
        "(See note 2.)",
        "[Done.]",
        f"It{RIGHT_SINGLE}s over.",
    ]


def test_an_opening_quote_or_bracket_can_start_the_next_sentence() -> None:
    assert sentences(f"Revenue rose. {LEFT_DOUBLE}Good,{RIGHT_DOUBLE} he said.") == [
        "Revenue rose.",
        f"{LEFT_DOUBLE}Good,{RIGHT_DOUBLE} he said.",
    ]


@pytest.mark.parametrize(
    ("text", "first"),
    [
        (f"{BULLET} Revenue rose. Costs fell.", "Revenue rose."),
        ("(1) Excludes charges. See below.", "Excludes charges."),
        ("(a) Restated.", "Restated."),
        ("** Unaudited.", "Unaudited."),
        (f"{DAGGER} Pro forma.", "Pro forma."),
        (f"{SUPERSCRIPT_ONE} Non-GAAP.", "Non-GAAP."),
    ],
    ids=["bullet", "number", "letter", "asterisks", "dagger", "superscript"],
)
def test_a_leading_marker_stays_outside_the_first_sentence(
    text: str, first: str
) -> None:
    assert sentences(text)[0] == first


def test_a_unit_that_is_only_a_marker_has_no_sentence() -> None:
    assert sentence_spans("(1)") == []
    assert sentence_spans(BULLET) == []


def test_a_dash_bullet_is_not_a_leading_marker() -> None:
    assert sentences("- Revenue rose.") == ["- Revenue rose."]


@pytest.mark.parametrize(
    "text", ["1. Revenue rose.", "a. Revenue rose.", "iv. Revenue rose."]
)
def test_an_enumerator_opening_the_unit_ends_no_sentence(text: str) -> None:
    assert sentences(text) == [text]


def test_an_enumerator_later_in_the_unit_is_an_ordinary_word() -> None:
    assert sentences("Revenue rose. See item 1. Costs fell.") == [
        "Revenue rose.",
        "See item 1.",
        "Costs fell.",
    ]


def test_a_sentence_ending_in_an_abbreviation_is_deliberately_under_split() -> None:
    assert sentences("We acquired Acme Inc. The deal closed in May.") == [
        "We acquired Acme Inc. The deal closed in May."
    ]


def test_a_unit_without_terminal_punctuation_is_one_sentence() -> None:
    assert sentences("Revenue rose in every region") == ["Revenue rose in every region"]


def test_sentences_follow_their_block_and_point_to_it() -> None:
    text = "Results\nRevenue rose. Costs fell.\n(1) Unaudited."
    document = CanonicalDocument.create(
        source_document_id="doc-1",
        canonicalization_version="test-1",
        canonical_text=text,
    )
    body, note = text.index("Revenue"), text.index("(1)")
    heading = DocumentElement.create(
        document, ElementType.HEADING, TextSpan(start=0, end=body - 1)
    )
    paragraph = DocumentElement.create(
        document, ElementType.PARAGRAPH, TextSpan(start=body, end=note - 1)
    )
    footnote = DocumentElement.create(
        document, ElementType.FOOTNOTE, TextSpan(start=note, end=len(text))
    )
    elements = with_sentences(document, [heading, paragraph, footnote])
    assert [
        (element.type.value, element.span.slice_of(text), element.parent_id)
        for element in elements
    ] == [
        ("heading", "Results", None),
        ("paragraph", "Revenue rose. Costs fell.", None),
        ("sentence", "Revenue rose.", paragraph.element_id),
        ("sentence", "Costs fell.", paragraph.element_id),
        ("footnote", "(1) Unaudited.", None),
        ("sentence", "Unaudited.", footnote.element_id),
    ]
    assert {element.source_type for element in elements[2:4]} == {"sentence"}
    assert validate_elements(document, elements) == ()
