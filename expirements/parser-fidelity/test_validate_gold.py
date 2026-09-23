import pytest
from validate_gold import init_skeleton, main, validate_fixture

FID = "0001234567-25-000123_ex-99-1"
SOURCE = """<html><head><title>Acme</title></head><body>
<p><b>ACME REPORTS THIRD QUARTER RESULTS</b></p>
<p>Acme Corp. today reported net sales of $4.3 billion for the quarter, up 5 percent.</p>
<p>Outlook</p>
<p style="text-transform: uppercase">guidance is unchanged for the year.</p>
<table>
<tr><td></td><td>Three Months Ended</td><td></td></tr>
<tr><td></td><td>2025</td><td>2024</td></tr>
<tr><td>Net sales</td><td>4,321</td><td>3,210</td></tr>
<tr><td>Cost of sales</td><td>2,109</td><td>1,987</td></tr>
</table>
<p>(1) Excludes the impact of the divestiture completed in the second quarter.</p>
<p>Outlook</p>
</body></html>"""

HEADER = f"""schema_version = 1
fixture_id = "{FID}"
annotator = "Tester"
marked_from = "browser rendering"
browser = "Firefox 140"
completed = 2026-10-01
"""

GOOD_BLOCKS = """
[[blocks]]
id = "b001"
type = "heading"
level = 1
start = "ACME REPORTS THIRD QUARTER RESULTS"

[[blocks]]
id = "b002"
type = "paragraph"
start = "Acme Corp. today reported"
end = "for the quarter, up 5 percent."

[[blocks]]
id = "t001"
type = "table"
headers = ["Three Months Ended", "2025", "2024"]
cells = [
  { role = "corner", text = "4,321", row_header = "Net sales", col_header = "2025" },
  { role = "right", text = "3,210", row_header = "Net sales", col_header = "2024" },
  { role = "below", text = "2,109", row_header = "Cost of sales", col_header = "2025" },
]

[[blocks]]
id = "b003"
type = "footnote"
start = "Excludes the impact of the divestiture"
end = "completed in the second quarter."
"""


# A draft before the annotator signs off (decision F9): header fields blank, no completed.
DRAFT_HEADER = f"""schema_version = 1
fixture_id = "{FID}"
annotator = ""
marked_from = "browser rendering"
browser = ""
"""
HEADER_ERRORS = [
    "missing top-level key 'completed'",
    "annotator must be a non-empty string",
    "browser must be a non-empty string",
]


def fixture(tmp_path, blocks, header=HEADER):
    folder = tmp_path / FID
    folder.mkdir()
    (folder / "source.html").write_text(SOURCE, encoding="utf-8")
    (folder / "gold.toml").write_text(header + blocks, encoding="utf-8")
    return folder


def test_valid_gold_passes(tmp_path):
    report = validate_fixture(fixture(tmp_path, GOOD_BLOCKS))
    assert report.errors == []
    assert report.encoding == "UTF-8" and report.ascii_only


def test_schema_errors_are_reported(tmp_path):
    blocks = """
[[blocks]]
id = "b1"
type = "sidebar"
start = "x"

[[blocks]]
id = "b1"
type = "paragraph"
level = 2
strat = "typo"
"""
    errors = validate_fixture(fixture(tmp_path, blocks)).errors
    assert any("type must be one of" in e for e in errors)
    assert any("duplicate id" in e for e in errors)
    assert any("level must be a positive integer" in e for e in errors)
    assert any("key 'strat' is not allowed" in e for e in errors)


def test_anchors_are_checked_before_the_header_is_filled(tmp_path):
    blocks = GOOD_BLOCKS.replace("today reported", "today announced")
    errors = validate_fixture(fixture(tmp_path, blocks, header=DRAFT_HEADER)).errors
    assert all(e in errors for e in HEADER_ERRORS)
    assert any("b002: start: not found" in e for e in errors)


def test_a_clean_draft_fails_only_on_the_header(tmp_path):
    errors = validate_fixture(
        fixture(tmp_path, GOOD_BLOCKS, header=DRAFT_HEADER)
    ).errors
    assert sorted(errors) == sorted(HEADER_ERRORS)


FLAGGED_TABLE = GOOD_BLOCKS.replace(
    'type = "table"\n', 'type = "table"\nunanchorable = true\n'
)


def test_a_table_whose_values_recur_can_be_marked_unanchorable(tmp_path):
    folder = fixture(tmp_path, GOOD_BLOCKS)
    # A later table repeats the corner value, so no L of unique cells exists.
    (folder / "source.html").write_text(
        SOURCE.replace(
            "</body>", "<table><tr><td>Restated</td><td>4,321</td></tr></table></body>"
        ),
        encoding="utf-8",
    )
    errors = validate_fixture(folder).errors
    assert any("t001: cell corner: occurs 2 times" in e for e in errors)
    (folder / "gold.toml").write_text(HEADER + FLAGGED_TABLE, encoding="utf-8")
    report = validate_fixture(folder)
    assert report.errors == []
    assert report.unanchorable == 1


def test_an_unanchorable_table_must_have_a_repeated_cell(tmp_path):
    errors = validate_fixture(fixture(tmp_path, FLAGGED_TABLE)).errors
    assert errors == [
        "block t001: unanchorable table must have a cell that occurs at least twice"
    ]


def test_unanchorable_on_a_table_must_be_true_or_false(tmp_path):
    blocks = FLAGGED_TABLE.replace("unanchorable = true", 'unanchorable = "yes"')
    errors = validate_fixture(fixture(tmp_path, blocks)).errors
    assert "block t001: unanchorable must be true or false" in errors


def test_table_needs_one_cell_per_role(tmp_path):
    blocks = GOOD_BLOCKS.replace('role = "right"', 'role = "corner"')
    errors = validate_fixture(fixture(tmp_path, blocks)).errors
    assert any("exactly one each of roles" in e for e in errors)


def test_duplicate_and_missing_anchors_are_errors_with_case_hints(tmp_path):
    blocks = """
[[blocks]]
id = "b001"
type = "heading"
start = "Outlook"

[[blocks]]
id = "b002"
type = "paragraph"
start = "GUIDANCE IS UNCHANGED FOR THE YEAR."
"""
    errors = validate_fixture(fixture(tmp_path, blocks)).errors
    assert any("b001: start: occurs 2 times" in e for e in errors)
    assert any("b002: start: not found (case-insensitive hits: 1" in e for e in errors)


def test_after_disambiguates_a_short_repeated_block(tmp_path):
    blocks = """
[[blocks]]
id = "b001"
type = "heading"
start = "Outlook"
after = "guidance is unchanged"
"""
    assert validate_fixture(fixture(tmp_path, blocks)).errors == []


def test_short_anchor_with_an_end_is_an_error(tmp_path):
    blocks = """
[[blocks]]
id = "b001"
type = "paragraph"
start = "Acme Corp."
end = "for the quarter, up 5 percent."
"""
    errors = validate_fixture(fixture(tmp_path, blocks)).errors
    assert any("start is shorter than four words" in e for e in errors)


def test_order_and_marker_warnings(tmp_path):
    blocks = """
[[blocks]]
id = "b001"
type = "paragraph"
start = "for the quarter, up 5 percent."
end = "Acme Corp. today reported net sales"

[[blocks]]
id = "b002"
type = "footnote"
start = "(1) Excludes the impact of"
end = "completed in the second quarter."
"""
    report = validate_fixture(fixture(tmp_path, blocks))
    assert report.errors == []
    assert any("b001: end precedes start" in w for w in report.warnings)
    assert any(
        "b002: start may begin with a bullet or marker" in w for w in report.warnings
    )


def test_unanchorable_block_must_repeat(tmp_path):
    blocks = """
[[blocks]]
id = "b001"
type = "heading"
start = "Outlook"
unanchorable = true

[[blocks]]
id = "b002"
type = "heading"
start = "ACME REPORTS THIRD QUARTER RESULTS"
unanchorable = true
"""
    report = validate_fixture(fixture(tmp_path, blocks))
    assert report.unanchorable == 2
    assert report.errors == ["block b002: unanchorable text must occur at least twice"]


def test_init_writes_a_skeleton_that_fails_until_filled(tmp_path):
    folder = tmp_path / FID
    folder.mkdir()
    (folder / "source.html").write_text(SOURCE, encoding="utf-8")
    init_skeleton(folder)
    with pytest.raises(FileExistsError):
        init_skeleton(folder)
    errors = validate_fixture(folder).errors
    assert "missing top-level key 'blocks'" in errors
    assert main([str(folder)]) == 1
