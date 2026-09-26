"""Name coverage: every significant cited token appears; nothing fuzzy."""

import pytest
from earnings_ingestion.cohort.names import covered, tokens


def test_tokens_fold_case_accents_apostrophes_and_parentheticals() -> None:
    assert tokens("Caf" + chr(0xE9) + " Holdings (Class A) Inc.") == {
        "cafe",
        "holdings",
        "inc",
    }
    assert tokens("O'Brien & Sons/The") == {"obrien", "and", "sons", "the"}
    assert tokens("Acme-Widget Co") == {"acme", "widget", "co"}


@pytest.mark.parametrize(
    ("cited", "other"),
    [
        ("Acme Industrial", "ACME INDUSTRIAL CORP"),
        ("The Acme Companies, Inc.", "Acme Cos Inc/The"),
        ("Acme-Widget", "ACME WIDGET CO"),
        ("Borealis Air (Class A)", "Borealis Air Inc"),
        ("Crane & Sons", "CRANE AND SONS LTD"),
    ],
)
def test_a_cited_name_is_covered_by_a_longer_legal_name(cited, other) -> None:
    assert covered(cited, other)


@pytest.mark.parametrize(
    ("cited", "other"),
    [
        ("ACI", "Acme Commercial Industries"),
        ("Acme Industrial", "Acme Corp"),
        ("Inc.", "Acme Inc"),
        ("Acme Air", "Acme Airlines Corp"),
    ],
    ids=["initials", "missing-word", "only-legal-form", "prefix-is-not-a-token"],
)
def test_anything_less_is_not_covered(cited, other) -> None:
    assert not covered(cited, other)
