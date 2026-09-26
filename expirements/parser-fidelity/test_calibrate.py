"""The calibration's eight kinds, on synthetic pairs: no capture or copy needed."""

import pytest
from calibrate import CALIBRATED, KINDS, differences, source_facts

SOURCE = (
    '<p>Visible text.</p><img src="logo.png" alt="Company Logo">'
    '<div style="display: none">Secret note</div>'
    '<p hidden>Old draft</p><span style="Visibility : Hidden">Tucked away</span>'
)
FACTS = source_facts(SOURCE)
BULLET = chr(0x2022)


def kinds(captured: str, copied: str) -> list[str]:
    return [difference.kind for difference in differences(captured, copied, FACTS)]


def test_the_source_facts_come_from_html_parser() -> None:
    assert FACTS.alternatives == {"Company Logo"}
    assert FACTS.hidden == "Secret note Old draft Tucked away"


def test_identical_texts_have_no_differences() -> None:
    assert kinds("Net sales\t$9.8\nTotal", "Net sales\t$9.8\nTotal") == []


@pytest.mark.parametrize(
    ("captured", "copied", "kind"),
    [
        ("Net sales rose", "Net sales fell", "visible characters"),
        ("One.\n\nTwo.", "One.\nTwo.", "whitespace"),
        ("One.", "One.\n", "whitespace"),
        (f"Items {BULLET} Margins", "Items Margins", "bullets"),
        ("FIRST QUARTER results", "First Quarter results", "CSS text transformation"),
        ("Hidden? Secret note here", "Hidden? here", "hidden content"),
        ("Logo: Company Logo here", "Logo: here", "image alternative text"),
        ("Net sales\t$9.8", "Net sales $9.8", "table-cell separation"),
    ],
)
def test_each_kind_is_recognized(captured: str, copied: str, kind: str) -> None:
    assert kinds(captured, copied) == [kind]


def test_a_moved_block_is_reading_order_on_both_sides() -> None:
    captured = "Alpha beta gamma. Delta epsilon zeta. Eta theta iota."
    copied = "Alpha beta gamma. Eta theta iota. Delta epsilon zeta."
    assert set(kinds(captured, copied)) == {"reading order"}
    assert len(kinds(captured, copied)) == 2


def test_hidden_text_counts_only_at_token_boundaries() -> None:
    assert kinds("Secret notes here", "here") == ["visible characters"]


def test_the_three_named_categories_are_calibrated() -> None:
    assert [category for category, _ in CALIBRATED] == [
        "narrative-only",
        "table-bearing",
        "malformed layout",
    ]
    assert len(KINDS) == 8
