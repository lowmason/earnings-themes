"""LayoutExtractor end to end: walker-1's text, a synthetic capture, layout-1's stream."""

from collections.abc import Callable

import pytest
from earnings_core import ElementType, RejectionReason, validate_elements
from earnings_ingestion.browser.metadata import parse_metadata
from earnings_ingestion.browser.records import (
    CaptureReason,
    CaptureStatus,
    RenderedCapture,
)
from earnings_ingestion.browser.renderer import EMPTY_LAYOUT
from earnings_ingestion.canonical import Canonicalized, canonicalize
from earnings_ingestion.layout.extract import LayoutExtractor

Make = Callable[..., RenderedCapture]

SOURCE = b"""<html><head><style>.gone { display: none }</style></head><body>
<p><b>Acme Reports Results</b></p>
<p>Revenue rose 5% to $2.1 billion in the third quarter of the year.</p>
<p class="gone">Hidden by the stylesheet</p>
<table>
<tr><td></td><td>2026</td><td>2025</td></tr>
<tr><td>Revenue</td><td>$9.8</td><td>$9.1</td></tr>
<tr><td colspan="3">Amounts in millions, except where noted otherwise below.</td></tr>
</table>
<p>Page 2</p>
</body></html>"""


def walker1() -> Canonicalized:
    result = canonicalize(SOURCE, source_document_id="release", media_type="text/html")
    assert isinstance(result, Canonicalized)
    return result


def rendered(parts, extra: list[dict] = ()) -> dict:
    """What the browser shows: everything but the stylesheet-hidden paragraph."""
    rows = [
        ["", "2026", "2025"],
        ["Revenue", "$9.8", "$9.1"],
        ["Amounts in millions, except where noted otherwise below."],
    ]
    return {
        "blocks": [
            parts.block(parts.run("Acme Reports Results", bold=True)),
            parts.block(
                parts.run(
                    "Revenue rose 5% to $2.1 billion in the third quarter of the year."
                )
            ),
            *parts.cells(rows),
            parts.block(parts.run("Page 2")),
            *extra,
        ],
        "tables": [parts.table([1, 1, 1], [1, 1, 1], [3])],
    }


def extract(make_capture: Make, payload: dict):
    result = walker1()
    capture = make_capture(layout=parse_metadata(payload))
    return result, LayoutExtractor().map_onto(capture, result.document)


def test_layout1_types_the_rendering_over_walker1s_text(
    make_capture: Make, parts
) -> None:
    result, extraction = extract(make_capture, rendered(parts))
    text = result.document.canonical_text
    blocks = [
        (e.type.value, e.span.slice_of(text))
        for e in extraction.elements
        if e.type is not ElementType.TABLE_CELL
    ]
    assert blocks == [
        ("heading", "Acme Reports Results"),
        (
            "paragraph",
            "Revenue rose 5% to $2.1 billion in the third quarter of the year.",
        ),
        ("other", "Hidden by the stylesheet"),
        ("table", "2026\t2025\nRevenue\t$9.8\t$9.1"),
        ("paragraph", "Amounts in millions, except where noted otherwise below."),
        ("page_artifact", "Page 2"),
    ]
    assert extraction.failures == ()
    assert extraction.retypes["C3"] == 1
    assert validate_elements(result.document, extraction.elements) == ()


def test_cells_carry_their_grid_and_header_references(
    make_capture: Make, parts
) -> None:
    result, extraction = extract(make_capture, rendered(parts))
    text = result.document.canonical_text
    cells_found = [e for e in extraction.elements if e.type is ElementType.TABLE_CELL]
    headers = {
        e.element_id: e.span.slice_of(text)
        for e in cells_found
        if e.table_cell.is_header
    }
    assert sorted(headers.values()) == ["2025", "2026"]
    nine_eight = next(e for e in cells_found if e.span.slice_of(text) == "$9.8")
    assert (nine_eight.table_cell.row, nine_eight.table_cell.column) == (1, 1)
    assert [headers[h] for h in nine_eight.table_cell.header_cell_ids] == ["2026"]


def test_every_element_is_layout1s_own(make_capture: Make, parts) -> None:
    _, extraction = extract(make_capture, rendered(parts))
    assert {e.source_type.partition(":")[0] for e in extraction.elements} == {"layout"}
    assert extraction.layout_version == "layout-1"
    assert extraction.mapping_policy == "anchored-1"


def test_text_the_canonical_document_lacks_is_a_recorded_failure(
    make_capture: Make, parts
) -> None:
    extra = [parts.block(parts.run("Shown only because scripts are off"))]
    result, extraction = extract(make_capture, rendered(parts, extra))
    assert [(f.reason, f.text) for f in extraction.failures] == [
        (RejectionReason.LOCATOR_NOT_FOUND, "Shown only because scripts are off")
    ]
    assert extraction.units == 10
    assert validate_elements(result.document, extraction.elements) == ()


@pytest.mark.parametrize("status", [CaptureStatus.FAILED, CaptureStatus.UNAVAILABLE])
def test_a_capture_without_a_rendering_cannot_be_extracted(
    make_capture: Make, status: CaptureStatus
) -> None:
    capture = make_capture(
        status=status,
        reason=CaptureReason.CAPTURE_FAILURE,
        rendered_text="",
        layout=EMPTY_LAYOUT,
    )
    with pytest.raises(ValueError, match=status.value):
        LayoutExtractor().extract(capture)
