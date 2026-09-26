"""R3.5's comparators, with the synthetic cases the fixtures cannot supply.

Non-ASCII inputs are built from code points, so no tool can normalize them.
"""

import pytest
from earnings_ingestion.canonical import Canonicalized, canonicalize
from earnings_ingestion.canonical.fidelity import (
    SCALE_PHRASES,
    classify_run,
    comparison_space,
    joined_to_text,
    locate_run,
    non_ascii,
    read_source,
    scale_counts,
    signed_figures,
)

EN_DASH, MINUS, NBSP = chr(0x2013), chr(0x2212), chr(0x00A0)
REGISTERED, E_ACUTE = chr(0x00AE), chr(0x00E9)


def test_the_comparison_space_is_nfc_with_collapsed_whitespace() -> None:
    assert comparison_space(f" caf{'e' + chr(0x0301)}\n\t{NBSP}bar ") == (
        f"caf{E_ACUTE} bar"
    )


def test_the_comparison_space_keeps_compatibility_forms() -> None:
    superscript_one, one_half = chr(0x00B9), chr(0x00BD)
    assert comparison_space(f"x{superscript_one} {one_half}") == (
        f"x{superscript_one} {one_half}"
    )


def test_non_ascii_lists_every_non_ascii_character() -> None:
    assert non_ascii(f"Acme{REGISTERED} {EN_DASH} caf{E_ACUTE}{REGISTERED}") == [
        REGISTERED,
        EN_DASH,
        E_ACUTE,
        REGISTERED,
    ]


def test_signed_figures_cover_parentheses_and_leading_signs() -> None:
    text = (
        f"Loss of (1,234) and ($5.2) and (3.1%); -4% and {EN_DASH}7 and {MINUS}0.5"
        " and +12%"
    )
    assert signed_figures(text) == [
        "(1,234)",
        "($5.2)",
        "(3.1%)",
        "-4%",
        f"{EN_DASH}7",
        f"{MINUS}0.5",
        "+12%",
    ]


def test_footnote_markers_and_ranges_are_not_signed_figures() -> None:
    assert signed_figures("See note (1) for 2020-2021 and pages 3-4.") == []


def test_scale_phrases_are_counted_case_insensitively() -> None:
    counts = scale_counts("(In millions, except per share data) in MILLIONS")
    assert counts == {
        "in millions": 2,
        "in thousands": 0,
        "in billions": 0,
        "except per share": 1,
    }
    assert tuple(counts) == SCALE_PHRASES


def test_read_source_skips_hidden_tags_and_spaces_block_boundaries() -> None:
    source = read_source(
        "<html><head><title>T</title><style>p {}</style></head><body>"
        "<p>Revenue</p><p>rose<br>sharply</p><script>x()</script></body></html>"
    )
    assert source.text == "Revenue rose sharply"


def test_read_source_marks_outermost_sup_runs() -> None:
    source = read_source(
        "<p>1<sup>st</sup> quarter, net income<sup> (a)</sup>"
        f" and Acme<sup><sup>{REGISTERED}</sup></sup></p>"
    )
    assert [source.text[start:end] for start, end in source.sup_runs] == [
        "st",
        "(a)",
        REGISTERED,
    ]


@pytest.mark.parametrize(
    ("run", "expected"),
    [
        ("st", "ordinal_suffix"),
        ("TH", "ordinal_suffix"),
        ("(1)", "parenthesized_marker"),
        ("( a )", "parenthesized_marker"),
        ("(1)(2)", "parenthesized_marker"),
        (REGISTERED, "symbol"),
        ("*", "symbol"),
        ("  ", "empty"),
        ("12", "bare_digits"),
        ("TM", "other"),
        (chr(0x00B2), "other"),
    ],
)
def test_runs_are_classed(run: str, expected: str) -> None:
    assert classify_run(run) == expected


def canonical_text(html: str) -> str:
    result = canonicalize(
        html.encode(), source_document_id="sup", media_type="text/html"
    )
    assert isinstance(result, Canonicalized)
    return comparison_space(result.document.canonical_text)


def test_a_run_is_located_by_the_fewest_words_that_make_it_unique() -> None:
    html = "<p>Revenue rose in the first half and the 1<sup>st</sup> quarter.</p>"
    source = read_source(html)
    canonical = canonical_text(html)
    [(start, end)] = source.sup_runs
    position = locate_run(canonical, source, start, end)
    assert position == canonical.index("1st") + 1


def test_a_run_no_context_singles_out_is_unlocatable() -> None:
    source = read_source("<p>A 1<sup>st</sup> B</p>")
    [(start, end)] = source.sup_runs
    assert source.text == "A 1st B"
    assert locate_run("A 1st B A 1st B", source, start, end) is None


def test_a_run_whose_context_does_not_match_is_unlocatable() -> None:
    source = read_source("<p>Net income<sup>(1)</sup> rose.</p>")
    [(start, end)] = source.sup_runs
    canonical = "Net earnings (1) and costs (1) rose."
    assert locate_run(canonical, source, start, end) is None


def test_a_run_missing_from_the_canonical_text_is_unlocatable() -> None:
    source = read_source("<p>Net income<sup>(1)</sup> rose.</p>")
    [(start, end)] = source.sup_runs
    assert locate_run("Net income rose.", source, start, end) is None


def test_an_empty_run_has_nothing_to_locate() -> None:
    source = read_source("<p>Net income<sup> </sup> rose.</p>")
    [(start, end)] = source.sup_runs
    assert start == end
    assert locate_run("Net income rose.", source, start, end) is None


def test_a_bare_digit_run_joined_to_a_number_is_a_hazard() -> None:
    html = "<p>Revenue was $4.5 million<sup>1</sup> in 2024.</p>"
    source = read_source(html)
    canonical = canonical_text(html)
    [(start, end)] = source.sup_runs
    run = source.text[start:end]
    position = locate_run(canonical, source, start, end)
    assert (classify_run(run), canonical) == (
        "bare_digits",
        "Revenue was $4.5 million1 in 2024.",
    )
    assert position is not None and joined_to_text(canonical, position)


def test_a_marker_after_a_space_is_not_joined() -> None:
    canonical = "Net income (1) rose."
    assert not joined_to_text(canonical, canonical.index("(1)"))
