"""Gold cells under FP20's conventions, with known answers (the Stage 11 spec,
§Metrics; R12.6)."""

from types import SimpleNamespace
from typing import get_protocol_members

import pytest
from earnings_themes import evaluation
from earnings_themes.evaluation.align import unit_index
from earnings_themes.evaluation.cells import (
    EvidenceCell,
    GoldReading,
    event_cells,
    level_one,
)
from earnings_themes.evaluation.problems import EvaluationError
from earnings_themes.gold import ReleaseLabel, Support

from .cases import claim, example, gold, quote, reading, row, unit_ids


def test_present_excused_uncertain_and_evidence_with_the_tie_predicted() -> None:
    source, gold = example()
    p0, p1, p2, _ = unit_ids(source)
    cells = event_cells(gold, unit_index(source), predicted={"pricing", "labor"})
    assert cells.present == {"capacity", "pricing"}
    assert cells.excused == {"demand"}
    assert cells.uncertain == {"labor"}
    assert cells.units == {"capacity": {p0}, "pricing": {p1, p2}}
    assert cells.spans == {"capacity": ((0, 5),), "pricing": ((30, 45),)}
    assert cells.dangling == 0


def test_an_unpredicted_tie_group_resolves_to_its_lowest_member() -> None:
    source, gold = example()
    cells = event_cells(gold, unit_index(source))
    assert cells.present == {"capacity", "demand"}
    assert cells.excused == {"pricing"}


def test_a_tie_group_resolves_to_a_member_already_present() -> None:
    source, base = example()
    gold = base.model_copy(
        update={
            "claims": (*base.claims, claim("c5", "q3")),
            "assignments": (
                *base.assignments,
                row("c5", "capacity", tie_group="g2"),
                row("c5", "labor", tie_group="g2"),
            ),
        }
    )
    p0, _, _, p3 = unit_ids(source)
    cells = event_cells(gold, unit_index(source))
    assert "labor" in cells.excused and "labor" not in cells.uncertain
    assert cells.units["capacity"] == {p0, p3}


def test_dangling_references_are_counted_and_add_nothing() -> None:
    source, _ = example()
    p0 = unit_ids(source)[0]
    gold = reading(
        quotes=(quote("q1", 0, 5, p0),),
        claims=(claim("c1", "q1", "q9"),),
        assignments=(row("c1", "capacity"), row("c8", "capacity")),
    )
    cells = event_cells(gold, unit_index(source))
    assert cells.units == {"capacity": {p0}}
    assert cells.dangling == 2


def test_every_assignment_citing_a_missing_claim_is_dangling() -> None:
    """D19-7: one dangling reference per assignment whose claim the reading lacks,
    whatever its support, theme or tie. The reading holds c1 only. Rows citing a
    missing claim: c7 ``uncertain`` for labor (1), c8 ``does_not_support`` for debt
    (1), c9 ``unmatched`` (1), and c6's tie group g1 over demand and pricing (2,
    one per row, the excused pricing row included): 5, and no claim cites a missing
    quote.

    Scoring is as before: g1 resolves to demand (nothing predicted, no member
    present untied, lowest ID), pricing is excused, labor is uncertain only, debt is
    decided against, and demand's missing claim adds no evidence."""
    source, _ = example()
    p0 = unit_ids(source)[0]
    gold = reading(
        quotes=(quote("q1", 0, 5, p0),),
        claims=(claim("c1", "q1"),),
        assignments=(
            row("c1", "capacity"),
            row("c7", "labor", Support.UNCERTAIN),
            row("c8", "debt", Support.DOES_NOT_SUPPORT),
            row("c9", "unmatched"),
            row("c6", "demand", tie_group="g1"),
            row("c6", "pricing", tie_group="g1"),
        ),
    )
    cells = event_cells(gold, unit_index(source))
    assert cells.dangling == 5
    assert cells.present == {"capacity", "demand"}
    assert cells.excused == {"pricing"}
    assert cells.uncertain == {"labor"}
    assert cells.units == {"capacity": {p0}, "demand": frozenset()}
    assert cells.spans == {"capacity": ((0, 5),), "demand": ()}


def test_a_gold_reading_offers_what_compare_readings_reads() -> None:
    """``compare_readings`` reads each reading's release identification, so the
    protocol names it, and signed gold and an anchored reading both hold one."""
    assert get_protocol_members(GoldReading) == {
        "quotes",
        "claims",
        "assignments",
        "hard_negatives",
        "release_identification",
    }
    _, base = example()
    for value in (base, gold("e1", base)):
        assert value.release_identification.label is ReleaseLabel.RELEASE


def test_the_package_exports_both_cell_records() -> None:
    """``EventCells.evidence`` holds ``EvidenceCell``s, so both are public."""
    assert {"EventCells", "EvidenceCell"} <= set(evaluation.__all__)
    assert evaluation.EvidenceCell is EvidenceCell
    assert len(evaluation.__all__) == len(set(evaluation.__all__)) == 46


def test_level_one_maps_each_theme_to_its_root() -> None:
    book = SimpleNamespace(
        themes=(
            SimpleNamespace(theme_id="capital", parent_id=None),
            SimpleNamespace(theme_id="capex", parent_id="capital"),
            SimpleNamespace(theme_id="buybacks", parent_id="capital"),
            SimpleNamespace(theme_id="pricing", parent_id=None),
        )
    )
    assert level_one(book) == {
        "capital": "capital",
        "capex": "capital",
        "buybacks": "capital",
        "pricing": "pricing",
    }
    loop = SimpleNamespace(
        themes=(
            SimpleNamespace(theme_id="a", parent_id="b"),
            SimpleNamespace(theme_id="b", parent_id="a"),
        )
    )
    with pytest.raises(EvaluationError, match="parent_cycle"):
        level_one(loop)
