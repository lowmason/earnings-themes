from pf_classes import is_data_table, parse_document, run_class_tests

DATA_TABLE = (
    "<table><tr><td></td><td>2025</td><td>2024</td></tr>"
    "<tr><td>Net sales</td><td>4,321</td><td>3,210</td></tr></table>"
)
PROSE = "<p>" + " ".join(["word"] * 30) + "</p>"


def page(body: str, head: str = "") -> bytes:
    return f"<html><head>{head}</head><body>{body}</body></html>".encode()


def first_table(html: str):
    return parse_document(html).find(".//table")


def test_data_table_needs_two_rows_with_text_and_a_multi_cell_row():
    assert is_data_table(first_table(DATA_TABLE))
    assert not is_data_table(
        first_table("<table><tr><td>Only</td><td>row</td></tr></table>")
    )
    assert not is_data_table(
        first_table("<table><tr><td>a</td></tr><tr><td>b</td></tr></table>")
    )


def test_nested_table_rows_do_not_count_for_the_outer_table():
    wrapper = f"<table><tr><td>{DATA_TABLE}</td></tr></table>"
    root = parse_document(wrapper)
    outer, inner = root.findall(".//table")
    assert not is_data_table(outer)
    assert is_data_table(inner)


def test_narrative_only_release_is_clean():
    tests = run_class_tests(page(PROSE))
    assert tests.narrative_only and tests.clean_html and not tests.table_heavy
    assert tests.visible_chars == len("word") * 30


def test_table_heavy_counts_characters_inside_data_tables():
    tests = run_class_tests(page("<p>Intro</p>" + DATA_TABLE))
    assert tests.data_tables == 1
    assert tests.table_heavy
    assert tests.data_table_chars == len("20252024Netsales4,3213,210")


def test_hidden_text_is_not_visible():
    tests = run_class_tests(
        page('<div style="display: none">hidden words</div><p>shown</p>')
    )
    assert tests.visible_chars == len("shown")


def test_positioned_text_fires_from_inline_style_or_style_block():
    assert run_class_tests(
        page('<p style="position:absolute;top:5px">x</p>')
    ).positioned_text
    assert run_class_tests(
        page("<p>x</p>", head="<style>.a{position: fixed}</style>")
    ).positioned_text


def test_layout_table_prose_fires_on_a_40_word_cell_in_a_non_data_table():
    long_cell = "<table><tr><td>" + " ".join(["w"] * 40) + "</td></tr></table>"
    tests = run_class_tests(page(long_cell))
    assert tests.layout_table_prose and tests.malformed_layout
    assert tests.max_layout_cell_words == 40


def test_page_break_debris_needs_page_break_styling_and_a_bare_page_number():
    debris = '<p>Text</p><p style="text-align:center">- 2 -</p><hr style="page-break-after: always">'
    assert run_class_tests(page(debris)).page_break_debris
    assert not run_class_tests(
        page('<p>Text</p><p style="text-align:center">- 2 -</p>')
    ).page_break_debris
    assert run_class_tests(
        page('<p>Text</p><p>Page 3</p><div style="break-before: page"></div>')
    ).page_break_debris


def test_preformatted_text_fires_when_pre_holds_half_the_characters():
    tests = run_class_tests(
        page("<pre>Revenue rose five percent in the quarter.</pre><p>x</p>")
    )
    assert tests.preformatted_text and tests.malformed_layout
