"""The comparison's pre-registered rules, on synthetic scores: no capture needed."""

import re

import pytest
from earnings_core import RejectionReason
from earnings_ingestion.layout import AlignmentFailure, LayoutExtraction
from layout1_report import (
    PROBES,
    Fixture,
    metric_pairs,
    regression,
    repaired,
    unit_lost,
)
from layout1_units import Unit
from pf_dump import Cell, Element, Row
from score import score_fixture
from validate_gold import SourceText

HEADING = "Quarterly Results Overview"
PROSE = "Revenue rose five percent in the quarter."
RAW = f"<p>{HEADING}</p><p>{PROSE}</p>".encode()
GOLD = {
    "blocks": [
        {"id": "b001", "type": "heading", "level": 1, "start": HEADING},
        {"id": "b002", "type": "paragraph", "start": PROSE},
    ]
}
BLOCKS = {block["id"]: block for block in GOLD["blocks"]}


@pytest.mark.parametrize(
    ("metric", "baseline", "other", "found"),
    [
        ("header_section", (5, 23), (6, 23), None),
        ("header_section", (5, 23), (7, 23), "worse by 2/23, more than 1/23"),
        ("header_section", (5, 23), (0, 23), None),
        ("header_section", (7, 30), (7, 29), None),
        ("coverage", (70, 70), (69, 70), None),
        ("coverage", (70, 70), (68, 70), "worse by 1/35, more than 1/70"),
        ("cell_association", (10, 12), (11, 12), None),
        ("footnote_merging", (0, 0), (0, 0), None),
        ("footnote_merging", (0, 0), (0, 1), "not comparable: one denominator is zero"),
        ("header_section", (3, 30), (0, 0), "not comparable: one denominator is zero"),
        ("alignment", (0, 937), (1, 937), None),
        ("alignment", (0, 937), (2, 937), "worse by 2/937, more than 1/937"),
    ],
)
def test_a_regression_is_worse_by_more_than_one_nth(
    metric: str, baseline: tuple, other: tuple, found: str | None
) -> None:
    assert regression(metric, baseline, other) == found


def test_a_class_is_repaired_by_strictly_fewer_losses() -> None:
    unit = Unit("styled_headings", "f", "b001", "heading")
    losses = {"walker-1": [unit], "layout-1": [], "fallback": [unit]}
    assert repaired(losses, "layout-1")
    assert not repaired(losses, "fallback")
    assert not repaired({"walker-1": [], "layout-1": []}, "layout-1")


def fixture(projections: dict[str, list[Element]], triggers=()) -> Fixture:
    source = SourceText(RAW)
    failure = AlignmentFailure(
        reason=RejectionReason.LOCATOR_NOT_FOUND,
        unit_type="paragraph",
        text="gone",
        detail="no occurrence",
    )
    extraction = LayoutExtraction(
        layout_version="layout-1",
        mapping_policy="anchored-1",
        capture_id="c",
        doc_id="d",
        units=3,
        retypes={},
        elements=(),
        failures=(failure,),
    )
    return Fixture(
        fixture="f",
        klass="clean_html",
        gold=GOLD,
        source=source,
        result=None,
        capture=None,
        extraction=extraction,
        triggers=triggers,
        elements={},
        projections=projections,
        scores={
            name: score_fixture(GOLD, source, projection)
            for name, projection in projections.items()
        },
    )


def paragraph(text: str) -> Element:
    return Element("paragraph", text, source_type="p")


def heading(text: str) -> Element:
    return Element("heading", text, level=1, source_type="h1")


def in_table(text: str) -> Element:
    return Element(
        "table", text, source_type="table", rows=(Row(False, (Cell(text),)),)
    )


def test_a_heading_unit_is_lost_unless_its_home_is_a_heading() -> None:
    unit = Unit("styled_headings", "f", "b001", "heading")
    typed = {
        "walker-1": [paragraph(HEADING), paragraph(PROSE)],
        "layout-1": [heading(HEADING), paragraph(PROSE)],
        "fallback": [paragraph(HEADING), paragraph(PROSE)],
    }
    measured = fixture(typed)
    assert [unit_lost(measured, name, unit, BLOCKS) for name in typed] == [
        True,
        False,
        True,
    ]


def test_a_prose_unit_is_lost_while_any_of_its_elements_is_a_table() -> None:
    unit = Unit("prose_in_tables", "f", "b002", "paragraph")
    typed = {
        "walker-1": [heading(HEADING), in_table(PROSE)],
        "layout-1": [heading(HEADING), paragraph(PROSE)],
        "fallback": [heading(HEADING)],
    }
    measured = fixture(typed)
    assert [unit_lost(measured, name, unit, BLOCKS) for name in typed] == [
        True,
        False,
        True,
    ]


@pytest.mark.parametrize("triggers", [(), ("no_heading",)])
def test_the_fallback_counts_alignment_failures_only_where_it_switches(
    triggers: tuple,
) -> None:
    typed = {
        name: [heading(HEADING), paragraph(PROSE)]
        for name in ("walker-1", "layout-1", "fallback")
    }
    pairs = metric_pairs(fixture(typed, triggers))
    assert pairs["walker-1"]["alignment"] == (0, 3)
    assert pairs["layout-1"]["alignment"] == (1, 3)
    assert pairs["fallback"]["alignment"] == ((1, 3) if triggers else (0, 3))
    assert pairs["walker-1"]["coverage"] == (2, 2)
    assert pairs["walker-1"]["altered"] == (0, 2)


def test_every_metric_is_reported_for_every_configuration() -> None:
    typed = {
        name: [heading(HEADING), paragraph(PROSE)]
        for name in ("walker-1", "layout-1", "fallback")
    }
    pairs = metric_pairs(fixture(typed))
    wanted = {
        "coverage",
        "reading_order",
        "header_section",
        "footnote_merging",
        "header_table",
        "cell_association",
        "altered",
        "alignment",
    }
    assert all(set(by_metric) == wanted for by_metric in pairs.values())


@pytest.mark.parametrize(
    ("finding", "text"),
    [
        (
            "NHI's headline",
            "NHI Reports 17.2% Increase in Third Quarter Normalized FFO",
        ),
        ("Becton Dickinson's statement titles", "BECTON DICKINSON AND COMPANY"),
        ("End marks", "# # #"),
        ("End marks", "***"),
        ("End marks", "###"),
        ("End marks", "***** ***** *****"),
        ("Ball's numbered running heads", "Ball Corp - 4"),
        (
            "FMC's numbered running heads",
            "Page 6/ FMC Corporation Announces Fourth Quarter Results",
        ),
        (
            "Becton Dickinson's non-GAAP footnotes",
            "1Represents a non-GAAP financial measure; refer to reconciliations.",
        ),
        (
            "Southwestern Energy's forward-looking-statements continuation",
            "rates and the ability of the company" + chr(0x2019) + "s lenders to act",
        ),
    ],
)
def test_each_probe_matches_its_findings_text(finding: str, text: str) -> None:
    [probe] = [probe for probe in PROBES if probe.finding == finding]
    assert re.fullmatch(probe.pattern, text, re.DOTALL)


def test_end_marks_never_match_prose() -> None:
    [probe] = [probe for probe in PROBES if probe.finding == "End marks"]
    assert not re.fullmatch(probe.pattern, "# of shares", re.DOTALL)
