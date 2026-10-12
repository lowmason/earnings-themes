"""Per-event counts and their figures, with hand-computed known answers (the Stage
11 spec, §Metrics; R12.5, R12.8, R13.1)."""

import pytest
from earnings_themes.evaluation.align import unit_index
from earnings_themes.evaluation.cells import event_cells
from earnings_themes.evaluation.scores import (
    Tally,
    char_counts,
    evidence_recall_counts,
    f1,
    gs5_shares,
    hard_negative_counts,
    macro_f1,
    per_theme,
    precision,
    rare_themes,
    recall,
    release_tally,
    theme_tallies,
    total,
    unit_tally,
)
from earnings_themes.gold import DraftCounts, NegativeKind, ReleaseLabel

from .cases import claim, example, quote, reading, row, unit_ids


def test_exact_cells_skip_excused_and_uncertain_predictions() -> None:
    """Both tie members predicted: the lower resolves the group, and the other is
    excused, not a false positive."""
    source, gold = example()
    predicted = {"pricing", "labor", "debt", "demand"}
    cells = event_cells(gold, unit_index(source), predicted)
    assert theme_tallies(cells, predicted) == {
        "capacity": Tally(fn=1),
        "debt": Tally(fp=1),
        "demand": Tally(tp=1),
    }


def test_micro_and_macro_f1_over_two_events() -> None:
    first = {"capacity": Tally(fn=1), "debt": Tally(fp=1), "pricing": Tally(tp=1)}
    second = {"capacity": Tally(tp=1), "demand": Tally(fp=1)}
    micro = total(t for event in (first, second) for t in event.values())
    assert micro == Tally(tp=2, fp=2, fn=1)
    assert precision(micro) == 0.5
    assert recall(micro) == pytest.approx(2 / 3)
    assert f1(micro) == pytest.approx(4 / 7)
    themes = per_theme((first, second))
    assert themes["capacity"] == Tally(tp=1, fn=1)
    assert macro_f1(themes) == pytest.approx((2 / 3 + 0 + 1 + 0) / 4)


def test_empty_denominators_are_none_never_zero() -> None:
    assert precision(Tally(fn=3)) is None
    assert recall(Tally(fp=3)) is None
    assert f1(Tally()) is None
    assert macro_f1({}) is None


def test_the_roll_up_maps_both_sides_to_level_one_so_siblings_meet() -> None:
    source, _ = example()
    p0 = unit_ids(source)[0]
    gold = reading(
        quotes=(quote("q1", 0, 5, p0),),
        claims=(claim("c1", "q1"),),
        assignments=(row("c1", "capex"),),
    )
    roots = {"capital": "capital", "capex": "capital", "buybacks": "capital"}
    exact = event_cells(gold, unit_index(source), {"buybacks"})
    assert theme_tallies(exact, {"buybacks"}) == {
        "buybacks": Tally(fp=1),
        "capex": Tally(fn=1),
    }
    rolled = {roots["buybacks"]}
    up = event_cells(gold, unit_index(source), rolled, theme_map=roots)
    assert theme_tallies(up, rolled) == {"capital": Tally(tp=1)}


def test_unit_and_character_overlap_over_present_and_predicted_cells() -> None:
    source, gold = example()
    p0, p1, _, p3 = unit_ids(source)
    cells = event_cells(gold, unit_index(source), {"pricing", "capacity"})
    accepted_units = {"pricing": frozenset({p1}), "capacity": frozenset({p0, p3})}
    assert unit_tally(cells, accepted_units) == Tally(tp=2, fp=1, fn=1)
    assert f1(unit_tally(cells, accepted_units)) == pytest.approx(2 / 3)
    spans = {"pricing": ((21, 37),), "capacity": ((0, 20), (57, 73))}
    assert char_counts(cells, spans) == (12, 60)


def test_uncertain_only_predictions_add_no_extra_units() -> None:
    """``labor`` is uncertain only; the unpredicted tie resolves to demand."""
    source, gold = example()
    p3 = unit_ids(source)[3]
    cells = event_cells(gold, unit_index(source), {"labor"})
    assert unit_tally(cells, {"labor": frozenset({p3})}) == Tally(fn=3)


def test_gold_evidence_recall_counts_units_whatever_their_theme() -> None:
    source, gold = example()
    p0, p1, _, p3 = unit_ids(source)
    cells = event_cells(gold, unit_index(source), {"pricing"})
    accepted = {"debt": frozenset({p0, p3}), "pricing": frozenset({p1})}
    assert evidence_recall_counts(cells, accepted) == (2, 3)
    assert evidence_recall_counts(cells, {}) == (0, 3)


def test_hard_negatives_by_kind() -> None:
    source, gold = example()
    p0, _, _, p3 = unit_ids(source)
    accepted = {"capacity": frozenset({p0, p3})}
    assert hard_negative_counts(gold, unit_index(source), accepted) == {
        NegativeKind.PERIOD: (1, 1),
        NegativeKind.ISSUER: (1, 0),
    }


def test_release_identification_leaves_ambiguous_out() -> None:
    assert release_tally(True, ReleaseLabel.RELEASE) == Tally(tp=1)
    assert release_tally(True, ReleaseLabel.NOT_RELEASE) == Tally(fp=1)
    assert release_tally(False, ReleaseLabel.RELEASE) == Tally(fn=1)
    assert release_tally(False, ReleaseLabel.NOT_RELEASE) == Tally()
    assert release_tally(True, ReleaseLabel.AMBIGUOUS) is None


def test_gs5_shares_over_summed_counts() -> None:
    counts = (
        DraftCounts(accepted=6, edited=2, rejected=2, added=1),
        DraftCounts(accepted=4, edited=1, rejected=0, added=3),
    )
    shares = gs5_shares(counts)
    assert shares["edited"] == pytest.approx(3 / 15)
    assert shares["rejected"] == pytest.approx(2 / 15)
    assert shares["added"] == pytest.approx(4 / 17)
    assert gs5_shares(()) == {"edited": None, "rejected": None, "added": None}


def test_rare_themes_are_present_in_at_most_two_events() -> None:
    source, _ = example()
    p0 = unit_ids(source)[0]
    index = unit_index(source)

    def present(*themes: str):
        gold = reading(
            quotes=(quote("q1", 0, 5, p0),),
            claims=(claim("c1", "q1"),),
            assignments=tuple(row("c1", t) for t in themes),
        )
        return event_cells(gold, index)

    events = (present("a", "b"), present("a"), present("a", "c"))
    assert rare_themes(events) == {"b", "c"}
