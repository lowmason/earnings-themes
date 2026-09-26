"""The R3.5 generator's references and header placement, on synthetic input."""

from __future__ import annotations

from earnings_core import ElementType
from earnings_ingestion.canonical import Canonicalized, canonicalize
from r35_report import NO_INSTANCES, header_placement, instances, references


def test_references_are_anchors_and_header_texts_of_anchorable_blocks() -> None:
    gold = {
        "blocks": [
            {"type": "paragraph", "start": "Revenue rose", "end": "in May."},
            {"type": "heading", "start": "Segment Results", "after": "The BD"},
            {
                "type": "table",
                "headers": ["2024", "2023"],
                "cells": [
                    {"role": "corner", "text": "1,234"},
                    {"role": "right", "text": "1,100"},
                ],
            },
            {"type": "paragraph", "start": "Hidden", "unanchorable": True},
        ]
    }
    anchors, headers = references(gold)
    assert anchors == [
        "Revenue rose",
        "in May.",
        "Segment Results",
        "The BD",
        "1,234",
        "1,100",
    ]
    assert headers == ["2024", "2023"]


def canonical(html: str) -> Canonicalized:
    result = canonicalize(html.encode(), source_document_id="t", media_type="text/html")
    assert isinstance(result, Canonicalized), result
    return result


def test_header_texts_are_placed_in_header_cells_other_cells_or_none() -> None:
    result = canonical(
        "<table><tr><th>Item</th><th>2024</th></tr>"
        "<tr><td>Net sales (in millions)</td><td>1,234</td></tr></table>"
    )
    tables = [e for e in result.elements if e.type is ElementType.TABLE]
    assert header_placement("2024", tables, result) == "header cell"
    assert header_placement("in millions", tables, result) == "other cell"
    assert header_placement("Three Months Ended", tables, result) == "no cell"


def test_a_c1_table_has_no_cells_to_place_headers_in() -> None:
    result = canonical(
        "<pre>Item          2024\n----------------\nSales    1,234</pre>"
    )
    tables = [e for e in result.elements if e.type is ElementType.TABLE]
    assert len(tables) == 1
    assert header_placement("2024", tables, result) == "no cell"


def test_zero_instances_reads_as_no_instances_in_sample() -> None:
    assert instances(0) == f"**Instances:** {NO_INSTANCES}"
    assert instances(3) == "**Instances:** 3"
