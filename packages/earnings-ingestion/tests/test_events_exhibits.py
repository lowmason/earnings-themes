"""R1.2's exhibit choice (the Stage 5 spec, §Exhibit choice): the exhibit the Item
2.02 text names, then one whose description names a release, then the lowest
sequence, each group by sequence."""

from datetime import date

import pytest
from earnings_ingestion.events.exhibits import exhibit_order, named_numbers
from earnings_ingestion.events.states import ExhibitChoice
from earnings_ingestion.sec.filing_index import FilingIndex, IndexDocument


def index(*documents: tuple[int, str, str, str]) -> FilingIndex:
    return FilingIndex(
        accession="0009990001-25-000012",
        form="8-K",
        filing_date=date(2025, 9, 25),
        accepted="2025-09-25 16:05:00",
        period_of_report=date(2025, 9, 25),
        items=("2.02", "9.01"),
        documents=(
            IndexDocument(1, "8-K", "acme-8k-20250925.htm", "8-K"),
            *(IndexDocument(*document) for document in documents),
            IndexDocument(None, "Complete submission text file", "x.txt", " "),
        ),
    )


@pytest.mark.parametrize(
    ("text", "numbers"),
    [
        ("furnished as Exhibit 99.1.", {(99, 1)}),
        ("in Exhibit 99 to this report", {(99, None)}),
        ("as Exhibit 99.01 hereto", {(99, 1)}),
        ("as Exhibits 99.1 and 99.2.", {(99, 1), (99, 2)}),
        ("Exhibits 99.1, 99.2, and 99.3", {(99, 1), (99, 2), (99, 3)}),
        ("exhibit no. 99.2 and Exhibit 99.3", {(99, 2), (99, 3)}),
        ("a copy is attached as Exhibit 99.1 & 99.2", {(99, 1), (99, 2)}),
        ("furnished its quarterly earnings release.", set()),
        ("Exhibit 10.1 is the credit agreement", set()),
    ],
)
def test_the_numbers_a_text_names(text: str, numbers: set) -> None:
    assert named_numbers(text) == numbers


def order(filing: FilingIndex, text: str) -> list[tuple[str, ExhibitChoice]]:
    return [(c.document.filename, c.choice) for c in exhibit_order(filing, text)]


def test_named_exhibits_come_first_by_sequence() -> None:
    filing = index(
        (2, "Press release", "ex991.htm", "EX-99.1"),
        (3, "Supplemental information", "ex992.htm", "EX-99.2"),
        (4, "Investor presentation", "ex993.htm", "EX-99.3"),
    )
    assert order(filing, "furnished as Exhibits 99.2 and 99.3") == [
        ("ex992.htm", ExhibitChoice.NAMED),
        ("ex993.htm", ExhibitChoice.NAMED),
        ("ex991.htm", ExhibitChoice.DESCRIBED),
    ]


@pytest.mark.parametrize(
    ("kind", "said"),
    [
        ("EX-99", "Exhibit 99"),
        ("EX-99.1", "Exhibit 99.1"),
        ("EX-99.01", "Exhibit 99.1"),
    ],
)
def test_each_numbering_is_named(kind: str, said: str) -> None:
    filing = index((2, "Financial tables", "ex.htm", kind))
    assert order(filing, f"furnished as {said}.") == [("ex.htm", ExhibitChoice.NAMED)]


def test_a_description_that_names_a_release_comes_next() -> None:
    filing = index(
        (2, "Supplemental schedules", "ex991.htm", "EX-99.1"),
        (3, "PRESS RELEASE DATED OCTOBER 21, 2025", "ex992.htm", "EX-99.2"),
        (4, "Earnings release, financial tables", "ex993.htm", "EX-99.3"),
    )
    assert order(filing, "furnished its release") == [
        ("ex992.htm", ExhibitChoice.DESCRIBED),
        ("ex993.htm", ExhibitChoice.DESCRIBED),
        ("ex991.htm", ExhibitChoice.LOWEST_SEQUENCE),
    ]


def test_otherwise_the_lowest_sequence_first() -> None:
    filing = index(
        (3, "Exhibit", "b.htm", "EX-99.2"),
        (2, "Exhibit", "a.htm", "EX-99.1"),
        (4, "Charter", "c.htm", "EX-3.1"),
    )
    assert order(filing, "") == [
        ("a.htm", ExhibitChoice.LOWEST_SEQUENCE),
        ("b.htm", ExhibitChoice.LOWEST_SEQUENCE),
    ]


def test_released_is_not_a_release() -> None:
    filing = index((2, "Released guidance", "a.htm", "EX-99.1"))
    assert order(filing, "") == [("a.htm", ExhibitChoice.LOWEST_SEQUENCE)]


def test_a_filing_without_ex_99_has_no_candidate() -> None:
    assert exhibit_order(index((2, "Charter", "c.htm", "EX-3.1")), "Exhibit 99.1") == ()
