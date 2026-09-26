"""walker-1's port equals the frozen walker (Stage 3 spec: Verification (plan A), item 1).

The committed modules must be exactly port_walker.py's output, and on every input here
the port must decode and walk as the frozen code does, element for element.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import astuple

import pytest
import walker as frozen
from earnings_ingestion.canonical import decode as ported_decode
from earnings_ingestion.canonical import walker as ported
from pf_decode import decode_html_bytes
from pf_paths import DEVSET, FIXTURES, HARNESS
from port_walker import TARGET, build_modules
from round2_fixtures import DEVSET as DEVSET_RELEASES

FIXTURE_IDS = sorted(path.parent.name for path in FIXTURES.glob("*/source.html"))

SYNTHETIC = {
    # construct: (body HTML, a type the frozen walker must emit for it)
    "pre": (
        "<pre>Net sales    1,234\n-----------\n\nA second piece of prose.</pre>",
        "paragraph",
    ),
    "li": ("<ul><li>One<ol><li>Nested</li></ol></li><li>Two</li></ul>", "list_item"),
    "h1-h6": (
        "".join(f"<h{n}>Level {n} heading</h{n}>" for n in range(1, 7)),
        "heading",
    ),
    "th": (
        (
            "<table><tr><th>Item</th><th>Amount</th></tr>"
            "<tr><td>Net sales</td><td>1,234</td></tr></table>"
        ),
        "table",
    ),
    "thead": (
        (
            "<table><thead><tr><td>Item</td><td>Amount</td></tr></thead>"
            "<tbody><tr><td>Net sales</td><td>1,234</td></tr></tbody></table>"
        ),
        "table",
    ),
    "caption": (
        (
            "<table><caption>Table 1: Results</caption>"
            "<tr><td>Item</td><td>Amount</td></tr>"
            "<tr><td>Net sales</td><td>1,234</td></tr></table>"
        ),
        "paragraph",
    ),
    "display-none": (
        '<p>Shown <span style="display:none">secret</span>tail</p>',
        "paragraph",
    ),
    "symbol-font": (
        '<p><font face="Wingdings">&#167;</font> Symbol-font bullet item</p>',
        "list_item",
    ),
    "double-br": ("<p>Line one<br>line two<br><br>Next block</p>", "paragraph"),
    "marker-table-footnote": (
        "<table><tr><td>(1)</td><td>Excludes a one-time charge.</td></tr></table>",
        "footnote",
    ),
    "marker-table-bullet": (
        "<table><tr><td>&#8226;</td><td>Revenue grew in every region.</td></tr></table>",
        "list_item",
    ),
}

DEEP_TEXT = "Deep text."
DEEP_HTML = (
    "<html><body>" + "<div>" * 254 + DEEP_TEXT + "</div>" * 254 + "</body></html>"
)
"""254 nested divs: libxml2 keeps content to that depth, and the frozen walker needs
more stack than the default recursion limit allows to reach it."""


def shape(elements: list) -> list[tuple]:
    """Each element as plain tuples, so the frozen and ported classes compare."""
    return [astuple(element) for element in elements]


def assert_equal_walks(text: str) -> None:
    elements, pre_lines = ported.walk(text)
    assert shape(elements) == shape(frozen.parse(text))
    pre = {i for i, element in enumerate(elements) if element.source_type == "pre"}
    assert set(pre_lines) == pre
    for index, lines in pre_lines.items():
        assert frozen.collapse("\n".join(lines)) == elements[index].text


def test_the_committed_modules_are_the_port_scripts_output() -> None:
    for name, text in build_modules().items():
        assert (TARGET / name).read_text(encoding="utf-8") == text, name


@pytest.mark.parametrize("construct", sorted(SYNTHETIC))
def test_synthetic_constructs_walk_equally(construct: str) -> None:
    body, expected_type = SYNTHETIC[construct]
    text = f"<html><body>{body}</body></html>"
    assert expected_type in {element.type for element in frozen.parse(text)}
    assert_equal_walks(text)


def test_pre_pieces_keep_their_original_lines() -> None:
    body, _ = SYNTHETIC["pre"]
    elements, pre_lines = ported.walk(f"<html><body>{body}</body></html>")
    assert [elements[i].text for i in sorted(pre_lines)] == [
        "Net sales 1,234 -----------",
        "A second piece of prose.",
    ]
    assert list(pre_lines.values()) == [
        ("Net sales    1,234", "-----------"),
        ("A second piece of prose.",),
    ]


@pytest.mark.parametrize("fixture", FIXTURE_IDS)
def test_fixtures_walk_equally(fixture: str) -> None:
    raw = (FIXTURES / fixture / "source.html").read_bytes()
    assert_equal_walks(decode_html_bytes(raw).text)


@pytest.mark.parametrize("release", DEVSET_RELEASES)
def test_development_releases_walk_equally(release: str) -> None:
    path = DEVSET / release / "source.html"
    if not path.exists():
        pytest.skip(f"development release {release} is not saved locally")
    assert_equal_walks(decode_html_bytes(path.read_bytes()).text)


def run_python(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=HARNESS,
        capture_output=True,
        text=True,
        check=False,
    )


def test_deep_nesting_overflows_the_frozen_walker_at_the_default_limit() -> None:
    """The control: without its raised limit, the frozen walker cannot reach the text."""
    result = run_python(
        "import sys\n"
        "sys.setrecursionlimit = lambda limit: None\n"
        "import walker\n"
        f"walker.parse({DEEP_HTML!r})\n"
    )
    assert result.returncode != 0
    assert "RecursionError" in result.stderr


def test_the_port_walks_deep_nesting_at_the_default_limit() -> None:
    result = run_python(
        "import sys\n"
        "from earnings_ingestion.canonical.walker import walk\n"
        "limit = sys.getrecursionlimit()\n"
        f"elements, _ = walk({DEEP_HTML!r})\n"
        "assert sys.getrecursionlimit() == limit, 'the recursion limit changed'\n"
        "print([element.text for element in elements])\n"
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == repr([DEEP_TEXT])


def test_deep_nesting_walks_equally() -> None:
    assert_equal_walks(DEEP_HTML)


DECODE_CASES = {
    "utf-8-bom": b"\xef\xbb\xbf<p>caf\xc3\xa9</p>",
    "utf-16le-bom": "\N{ZERO WIDTH NO-BREAK SPACE}<p>caf\xe9</p>".encode("utf-16-le"),
    "meta-latin-1": b'<meta charset="iso-8859-1"><p>\x93quoted\x94</p>',
    "meta-http-equiv": b'<meta http-equiv="Content-Type" content="text/html; charset=utf-8"><p>\xe2\x80\x94</p>',
    "valid-utf-8": b"<p>\xe2\x80\x9cquoted\xe2\x80\x9d</p>",
    "invalid-utf-8": b"<p>\x93Hi\x94 \x81</p>",
    "unknown-label": b'<meta charset="no-such-charset"><p>plain</p>',
    "label-outside-the-short-list": b'<meta charset="iso-8859-9"><p>\x80</p>',
    "empty": b"",
}


@pytest.mark.parametrize("case", sorted(DECODE_CASES))
def test_decoding_is_equal(case: str) -> None:
    raw = DECODE_CASES[case]
    assert astuple(ported_decode.decode_html_bytes(raw)) == astuple(
        decode_html_bytes(raw)
    )


def test_a_label_outside_the_short_list_decodes_by_codecs_not_whatwg() -> None:
    """A walker-1 limitation (V2 disposition): WHATWG reads 0x80 here as the euro sign."""
    decoded = ported_decode.decode_html_bytes(
        DECODE_CASES["label-outside-the-short-list"]
    )
    assert (decoded.encoding, decoded.basis) == ("iso8859-9", "meta")
    assert "<p>\x80</p>" in decoded.text
    assert "\N{EURO SIGN}" not in decoded.text
