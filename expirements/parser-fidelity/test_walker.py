"""One test per walker rule (walker-rules.md)."""

from walker import parse


def kinds(html):
    return [(e.type, e.text) for e in parse(f"<html><body>{html}</body></html>")]


def test_w1_hidden_content_is_skipped_but_following_text_is_kept():
    assert kinds(
        '<p>Shown <span style="display:none">secret</span>tail</p><script>x()</script>'
    ) == [("paragraph", "Shown tail")]


def test_w2_block_tags_split_and_inline_tags_join():
    assert kinds("<div>Intro <b>bold</b> text<p>Inner block</p>after</div>") == [
        ("paragraph", "Intro bold text"),
        ("paragraph", "Inner block"),
        ("paragraph", "after"),
    ]


def test_w3_one_break_joins_two_breaks_split():
    assert kinds("<p>Line one<br>line two<br><br>Next block</p>") == [
        ("paragraph", "Line one line two"),
        ("paragraph", "Next block"),
    ]


def test_w4_whitespace_collapses_and_empty_blocks_drop():
    assert kinds("<p>  Net\n   sales  </p><p> </p><hr>") == [("paragraph", "Net sales")]


def test_w5_pre_splits_at_blank_lines():
    assert kinds("<pre>First paragraph\ncontinues.\n\n  \nSecond paragraph.</pre>") == [
        ("paragraph", "First paragraph continues."),
        ("paragraph", "Second paragraph."),
    ]


def test_w6_html_headings_carry_their_level():
    [heading] = parse("<html><body><h2>Outlook</h2></body></html>")
    assert (heading.type, heading.level) == ("heading", 2)


def test_w7_lists_are_containers_with_levelled_items():
    elements = parse(
        "<html><body><ul><li>One<ol><li>Nested</li></ol></li><li>Two</li></ul></body></html>"
    )
    assert [(e.type, e.text, e.parent, e.level) for e in elements] == [
        ("other", "", None, None),
        ("list_item", "One", 0, 1),
        ("other", "", 0, None),
        ("list_item", "Nested", 2, 2),
        ("list_item", "Two", 0, 1),
    ]


def test_w8_bare_page_numbers_are_other():
    assert kinds("<p>- 12 -</p><p>Page 3</p>") == [
        ("other", "- 12 -"),
        ("other", "Page 3"),
    ]


def test_w9_bullet_glyphs_and_symbol_fonts_make_list_items():
    html = (
        "<p>\u2022 Revenue grew</p><p>- Margin expanded</p>"
        '<p><font face="Wingdings">\xa7</font> Cash rose</p>'
    )
    assert kinds(html) == [
        ("list_item", "\u2022 Revenue grew"),
        ("list_item", "- Margin expanded"),
        ("list_item", "\xa7 Cash rose"),
    ]


def test_w10_footnote_markers():
    assert kinds(
        "<p>(1) Excludes charges.</p><p>* Non-GAAP.</p><p><sup>2</sup> Restated.</p>"
    ) == [
        ("footnote", "(1) Excludes charges."),
        ("footnote", "* Non-GAAP."),
        ("footnote", "2 Restated."),
    ]


def test_w11_short_fully_bold_or_underlined_blocks_are_headings():
    html = (
        "<p><b>Business Highlights</b></p>"
        '<p style="font-weight:700">About Acme Corp.</p>'
        "<p><u>Outlook</u></p>"
        "<p><b>Revenue:</b> rose five percent.</p>"
        '<p style="font-weight:bold"><span style="font-weight:normal">Not bold</span></p>'
    )
    assert kinds(html) == [
        ("heading", "Business Highlights"),
        ("heading", "About Acme Corp."),
        ("heading", "Outlook"),
        ("paragraph", "Revenue: rose five percent."),
        ("paragraph", "Not bold"),
    ]


def test_w11_long_bold_blocks_stay_paragraphs():
    words = " ".join(["word"] * 13)
    assert kinds(f"<p><b>{words}</b></p>") == [("paragraph", words)]


def test_w13_marker_tables_become_list_items_or_footnotes():
    html = (
        "<table><tr><td>\u2022</td><td>Opened three plants</td></tr>"
        "<tr><td>\u2022</td><td>Cut costs</td></tr></table>"
        "<table><tr><td>(1)</td><td>Excludes the divestiture.</td></tr></table>"
    )
    assert kinds(html) == [
        ("list_item", "Opened three plants"),
        ("list_item", "Cut costs"),
        ("footnote", "Excludes the divestiture."),
    ]


def test_w14_w15_data_tables_carry_their_grid_and_header_rows():
    html = (
        "<table><caption>Summary</caption>"
        '<tr><td></td><td colspan="2">Three Months Ended</td></tr>'
        "<tr><td></td><td>2025</td><td>2024</td></tr>"
        "<tr><td></td><td></td><td></td></tr>"
        "<tr><td>Net sales</td><td>$ 4,321</td><td>(3,210)</td></tr></table>"
    )
    elements = parse(f"<html><body>{html}</body></html>")
    assert [(e.type, e.text) for e in elements] == [
        ("paragraph", "Summary"),
        ("table", " Three Months Ended\n 2025 2024\nNet sales $ 4,321 (3,210)"),
    ]
    rows = elements[1].rows
    assert [row.header for row in rows] == [True, True, False]
    assert rows[0].cells[1].colspan == 2


def test_w16_layout_tables_are_walked_cell_by_cell():
    html = "<table><tr><td><p><b>Outlook</b></p><p>We expect growth.</p></td><td>Contact: IR</td></tr></table>"
    assert kinds(html) == [
        ("heading", "Outlook"),
        ("paragraph", "We expect growth."),
        ("paragraph", "Contact: IR"),
    ]


def test_parse_is_deterministic():
    html = "<html><body><h1>T</h1><p>x</p><table><tr><td>a</td><td>1</td></tr><tr><td>b</td><td>2</td></tr></table></body></html>"
    assert parse(html) == parse(html)
