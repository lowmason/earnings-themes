"""Gold cells under FP20's conventions, with known answers (the Stage 11 spec,
§Metrics; R12.6)."""

from types import SimpleNamespace

import pytest
from earnings_themes.evaluation.align import unit_index
from earnings_themes.evaluation.cells import event_cells, level_one
from earnings_themes.evaluation.problems import EvaluationError

from .cases import claim, example, quote, reading, row, unit_ids


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
