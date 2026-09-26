"""C1-C5: each rule's positive and negative cases (Stage 3 spec: Verification, item 9)."""

import pytest
from earnings_ingestion.canonical.blocks import Block, GridCell
from earnings_ingestion.canonical.compensate import RULES, compensate, is_pre_table


def paragraph(
    text: str, *, source_type: str = "p", pre_lines: tuple[str, ...] | None = None
) -> Block:
    return Block(
        type="paragraph", text=text, source_type=source_type, pre_lines=pre_lines
    )


def types_after(blocks: list[Block]) -> list[str]:
    return [block.type for block in compensate(blocks)[0]]


@pytest.mark.parametrize(
    "lines",
    [
        ("Net sales", "  ----------  ------"),
        ("Net sales", "=== ==="),
        ("Net sales", "___"),
        ("Net sales ............ 1", "Cost"),
        ("Net sales        1,234   ",),
        ("Net loss      $(56.7)",),
        ("Margin    12.5%",),
        ("Change     -3",),
    ],
    ids=[
        "dash-rule",
        "equals-rule",
        "underscore-rule",
        "dot-leader",
        "numeric-field",
        "parenthesized-dollars",
        "percent",
        "dash-sign",
    ],
)
def test_c1_finds_a_table_line(lines: tuple[str, ...]) -> None:
    assert is_pre_table(lines)


@pytest.mark.parametrize(
    "lines",
    [
        ("Revenue grew in every region.", "Margins widened."),
        ("A two-dash aside -- like this.",),
        ("--",),
        ("Three dots... then more text.",),
        ("Figures were 1,234 for the year.",),
        ("1,234",),
        ("Fiscal    2024 results",),
        ("Net sales  1,234 units",),
    ],
    ids=[
        "prose",
        "inner-dashes",
        "short-rule",
        "ellipsis",
        "single-spaced-figure",
        "figure-alone-on-its-line",
        "field-not-at-line-end",
        "figure-then-word",
    ],
)
def test_c1_leaves_prose_lines_alone(lines: tuple[str, ...]) -> None:
    assert not is_pre_table(lines)


def test_c1_retypes_a_pre_piece_to_a_table_and_keeps_its_text() -> None:
    block = paragraph(
        "Net sales 1,234", source_type="pre", pre_lines=("Net sales    1,234",)
    )
    [retyped], retypes = compensate([block])
    assert (retyped.type, retyped.text, retyped.retyped_by) == (
        "table",
        "Net sales 1,234",
        "C1",
    )
    assert retypes == {"C1": 1, "C2": 0, "C3": 0, "C4": 0, "C5": 0}


def test_c1_reads_only_pre_pieces() -> None:
    assert types_after([paragraph("Net sales    1,234")]) == ["paragraph"]


def test_c2_retypes_the_edgar_header_line_when_it_comes_first() -> None:
    header = "EX-99.1 2 exhibit991.htm EXHIBIT 99.1"
    container = Block(type="other", text="", source_type="ul", container=True)
    assert types_after([container, paragraph(header), paragraph("Body.")]) == [
        "other",
        "page_artifact",
        "paragraph",
    ]
    assert types_after([paragraph(header.lower())]) == ["page_artifact"]


@pytest.mark.parametrize(
    "blocks",
    [
        [paragraph("Title"), paragraph("EX-99.1 2 exhibit991.htm EXHIBIT 99.1")],
        [paragraph("EX-99.1 exhibit991.htm")],
        [paragraph("EX-99.1 2 exhibit991.pdf")],
    ],
    ids=["not-first", "no-sequence-number", "not-a-web-file"],
)
def test_c2_leaves_other_blocks_alone(blocks: list[Block]) -> None:
    assert "page_artifact" not in types_after(blocks)


def test_c3_retypes_bare_page_numbers_and_keeps_years() -> None:
    page = Block(type="other", text="- 12 -", source_type="p")
    year = Block(type="other", text="2009", source_type="td")
    assert types_after([paragraph("Body."), page, year]) == [
        "paragraph",
        "page_artifact",
        "other",
    ]


def test_a_year_c3_keeps_is_not_retyped_by_a_later_rule() -> None:
    years = [Block(type="other", text="2009", source_type="p") for _ in range(3)]
    assert types_after([paragraph("Body."), *years]) == ["paragraph"] + ["other"] * 3


def test_c3_never_touches_a_list_container() -> None:
    container = Block(type="other", text="", source_type="ul", container=True)
    assert types_after([paragraph("Body."), container]) == ["paragraph", "other"]


@pytest.mark.parametrize("text", ["Page 3 of 12", "page 3 of 12", "3 of 12"])
def test_c4_retypes_page_n_of_m(text: str) -> None:
    assert types_after([paragraph("Body."), paragraph(text)])[1] == "page_artifact"


@pytest.mark.parametrize(
    "text", ["Page 3 of 12 follows", "3 of our 12 plants", "Page 12345 of 2"]
)
def test_c4_needs_the_whole_text(text: str) -> None:
    assert types_after([paragraph("Body."), paragraph(text)])[1] == "paragraph"


def test_c5_retypes_short_blocks_that_repeat_three_times() -> None:
    running = [paragraph("Acme Corp.") for _ in range(3)]
    blocks, retypes = compensate([paragraph("Body."), *running])
    assert [block.type for block in blocks] == ["paragraph"] + ["page_artifact"] * 3
    assert retypes["C5"] == 3


def test_c5_needs_three_occurrences() -> None:
    assert types_after([paragraph("Acme Corp."), paragraph("Acme Corp.")]) == [
        "paragraph",
        "paragraph",
    ]


def test_c5_needs_twelve_words_or_fewer() -> None:
    long = " ".join(["word"] * 13)
    assert types_after([paragraph(long) for _ in range(3)]) == ["paragraph"] * 3


def test_c5_never_retypes_a_heading() -> None:
    html = Block(type="heading", text="Acme Corp.", source_type="h3", level=3)
    styled = Block(type="heading", text="Acme Corp.", source_type="p")
    blocks, retypes = compensate(
        [paragraph("Body."), html, styled, paragraph("Acme Corp.")]
    )
    assert [(block.type, block.level) for block in blocks[1:]] == [
        ("heading", 3),
        ("heading", None),
        ("page_artifact", None),
    ]
    assert retypes["C5"] == 1


def test_a_retype_drops_a_headings_level() -> None:
    heading = Block(type="heading", text="Page 1 of 2", source_type="h3", level=3)
    blocks, _ = compensate([paragraph("Body."), heading])
    assert (blocks[1].type, blocks[1].level, blocks[1].retyped_by) == (
        "page_artifact",
        None,
        "C4",
    )


def test_a_retyped_list_item_keeps_its_container() -> None:
    container = Block(type="other", text="", source_type="ul", container=True)
    items = [
        Block(type="list_item", text="Repeat", source_type="li", parent=0, level=1)
        for _ in range(3)
    ]
    blocks, _ = compensate([container, *items])
    assert [(block.type, block.parent, block.level) for block in blocks[1:]] == [
        ("page_artifact", 0, None)
    ] * 3


def test_grid_tables_are_never_retyped() -> None:
    cell = GridCell("Acme", 0, 0, 1, 1, False)
    table = Block(type="table", text="Acme", source_type="table", cells=(cell,))
    assert types_after([table, table, table]) == ["table"] * 3


def test_an_earlier_rule_wins() -> None:
    pre = paragraph(
        "Page 1 of 2", source_type="pre", pre_lines=("Page 1 of 2", "-----")
    )
    blocks, retypes = compensate([paragraph("Body."), pre])
    assert blocks[1].retyped_by == "C1"
    assert retypes == {"C1": 1, "C2": 0, "C3": 0, "C4": 0, "C5": 0}


def test_rules_can_be_narrowed() -> None:
    blocks = [
        paragraph("Body."),
        paragraph("x", source_type="pre", pre_lines=("-----",)),
        paragraph("Page 1 of 2"),
    ]
    narrowed, retypes = compensate(blocks, rules=("C1",))
    assert [block.type for block in narrowed] == ["paragraph", "table", "paragraph"]
    assert retypes == {"C1": 1, "C2": 0, "C3": 0, "C4": 0, "C5": 0}
    assert RULES == ("C1", "C2", "C3", "C4", "C5")
