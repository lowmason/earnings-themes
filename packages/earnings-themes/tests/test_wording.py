"""F20's rule over Stage 6's files (the Stage 6 spec, §Wording guard): 40 characters
copied from a text are caught, 39 are not, dates are facts, and a Markdown phrase
wrapped across lines is still caught."""

import pytest
from earnings_themes.wording import (
    WIDTH,
    labelled_strings,
    markdown_paragraphs,
    masked,
    shared,
)

TEXT = (
    "Net sales for the quarter ended September 30, 2025 grew in every region, "
    "led by strong demand for the company's industrial filtration products."
)


def copied(width: int) -> str:
    start = TEXT.index("led by")
    return f"The user noted [{TEXT[start : start + width]}] in passing."


@pytest.mark.parametrize(("width", "caught"), [(WIDTH, True), (WIDTH - 1, False)])
def test_the_window_is_40_characters(width: int, caught: bool) -> None:
    found = shared([("claim c1", copied(width))], [("doc-1", TEXT)])
    assert found == ({("claim c1", "doc-1")} if caught else set())


def test_a_date_is_a_fact_not_wording() -> None:
    fact = "for the quarter ended September 30, 2025 grew in every region"
    assert len(fact) > WIDTH
    assert shared([("note", fact)], [("doc-1", TEXT)]) == {("note", "doc-1")}
    assert masked("ended Sept. 30, 2025 and") == "ended \0 and"
    short = "the quarter ended September 30, 2025"
    assert len(masked(short)) < WIDTH
    assert shared([("note", short)], [("doc-1", TEXT)]) == set()


def test_only_labels_and_ids_come_back() -> None:
    found = shared([("a", copied(WIDTH)), ("b", "own words")], [("doc-1", TEXT)])
    assert found == {("a", "doc-1")}
    assert all(TEXT not in label and "led by" not in label for label, _ in found)


def test_every_string_leaf_is_labelled_by_its_path() -> None:
    data = {"claims": [{"claim_id": "c1", "claim": "x"}], "no_theme": False, "n": 1}
    assert labelled_strings(data) == [
        ("claims[0].claim_id", "c1"),
        ("claims[0].claim", "x"),
    ]


def test_a_phrase_wrapped_across_markdown_lines_is_caught() -> None:
    start = TEXT.index("led by")
    phrase = TEXT[start : start + WIDTH + 10]
    head, tail = phrase[:20].rstrip(), phrase[20:].lstrip()
    markdown = f"# Brief\n\nSome words, {head}\n{tail}, more.\n\n- another\n"
    paragraphs = markdown_paragraphs(markdown, "brief.md")
    assert [label for label, _ in paragraphs] == [
        "brief.md paragraph 1",
        "brief.md paragraph 2",
        "brief.md paragraph 3",
    ]
    assert shared(paragraphs, [("doc-1", TEXT)]) == {("brief.md paragraph 2", "doc-1")}
