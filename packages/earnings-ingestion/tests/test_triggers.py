"""The fallback's two triggers, read from walker-1's output."""

import pytest
from earnings_ingestion.canonical import Canonicalized, canonicalize
from earnings_ingestion.canonical.triggers import NO_HEADING, PROSE_ROW, fired

HEADING = "<h1>Acme Reports Results</h1>"
PARAGRAPH = "<p>Revenue rose.</p>"
TABLE = (
    "<table><tr><td></td><td>2026</td></tr><tr><td>Revenue</td><td>9.8</td></tr>{row}"
    "</table>"
)
LONG = '<tr><td colspan="2">' + " ".join(["word"] * 13) + "</td></tr>"
SHORT = '<tr><td colspan="2">' + " ".join(["word"] * 12) + "</td></tr>"


def triggers(body: str) -> tuple[str, ...]:
    html = f"<html><body>{body}</body></html>".encode()
    result = canonicalize(html, source_document_id="release", media_type="text/html")
    assert isinstance(result, Canonicalized)
    return fired(result.document, result.elements)


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        (HEADING + PARAGRAPH, ()),
        (PARAGRAPH, (NO_HEADING,)),
        (HEADING + TABLE.format(row=LONG), (PROSE_ROW,)),
        (HEADING + TABLE.format(row=SHORT), ()),
        (PARAGRAPH + TABLE.format(row=LONG), (NO_HEADING, PROSE_ROW)),
    ],
)
def test_each_trigger_fires_exactly_when_its_condition_holds(
    body: str, expected: tuple[str, ...]
) -> None:
    assert triggers(body) == expected
