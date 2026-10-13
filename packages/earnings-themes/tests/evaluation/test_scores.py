"""Per-event counts and their figures, with hand-computed known answers (the Stage
11 spec, §Metrics; R12.5, R12.8, R13.1)."""

import pytest
from earnings_themes.annotation import Reading
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
from earnings_themes.gold import DraftCounts, NegativeKind, ReleaseLabel, Support

from .cases import bundle, claim, example, quote, reading, row, unit_ids


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


def test_a_reading_without_tie_groups_scores_as_before() -> None:
    """No tie group: each present theme is its own evidence cell. Gold: capacity by
    c1 (q1 = [0, 5) in P0), labor by c2 (q2 = P1), hiring only uncertain for c2, debt
    decided against for c3. The run accepts capacity over P0 and P3, hiring over P1
    and debt over P3. Units: capacity tp 1 (P0) and fp 1 (P3); labor fn 1 (P1);
    hiring is uncertain only, so unscored; debt fp 1 (P3): Tally(1, 2, 1).
    Characters: capacity shares 5 of a 5 + 15 + 16 = 36 union; labor's 16 are
    missed; debt's 16 are extra: (5, 36 + 16 + 16) = (5, 68)."""
    source = bundle()
    p0, p1, _, p3 = unit_ids(source)
    gold = reading(
        quotes=(
            quote("q1", 0, 5, p0),
            quote("q2", 21, 37, p1),
            quote("q3", 57, 73, p3),
        ),
        claims=(claim("c1", "q1"), claim("c2", "q2"), claim("c3", "q3")),
        assignments=(
            row("c1", "capacity"),
            row("c2", "labor"),
            row("c2", "hiring", Support.UNCERTAIN),
            row("c3", "debt", Support.DOES_NOT_SUPPORT),
        ),
    )
    units = {
        "capacity": frozenset({p0, p3}),
        "hiring": frozenset({p1}),
        "debt": frozenset({p3}),
    }
    cells = event_cells(gold, unit_index(source), units)
    assert unit_tally(cells, units) == Tally(tp=1, fp=2, fn=1)
    spans = {
        "capacity": ((0, 20), (57, 73)),
        "hiring": ((21, 37),),
        "debt": ((57, 73),),
    }
    assert char_counts(cells, spans) == (5, 68)


def tie_reading(*assignments) -> Reading:
    """Quotes q0..q3 over P0..P3, whole, and claims c0..c3, ``cN`` quoting ``qN``."""
    source = bundle()
    return reading(
        quotes=tuple(
            quote(f"q{n}", start, end, unit)
            for n, (start, end, unit) in enumerate(
                zip((0, 21, 38, 57), (20, 37, 56, 73), unit_ids(source), strict=True)
            )
        ),
        claims=tuple(claim(f"c{n}", f"q{n}") for n in range(4)),
        assignments=assignments,
    )


def test_a_tie_groups_evidence_is_covered_by_any_predicted_member() -> None:
    """Gold: capacity is supported untied by c0 (P0), and tie group g1 over capacity
    and pricing by c1 (P1). The run accepts capacity over P0 and pricing over P1.
    D19-6 resolves g1 to capacity, the lower predicted member, and excuses pricing:
    the theme cells are capacity, a hit, and nothing else (theme F1 1, as before).

    Evidence cells: capacity's own {P0}, and g1's {P1}, which capacity or pricing
    covers. Capacity covers P0 and pricing covers P1: tp 2, fn 0. Capacity's P0 lies
    in its own cell, and pricing's P1 in g1's, so neither is a false positive. Unit
    F1 = 4 / 4 = 1. Characters: 20 of P0 and 16 of P1 shared, none missed or extra:
    (36, 36). (Before: capacity's gold {P0, P1} against {P0}, pricing unscored: tp
    1, fn 1, unit F1 2/3; characters (20, 36).)"""
    source = bundle()
    p0, p1, _, _ = unit_ids(source)
    gold = tie_reading(
        row("c0", "capacity"),
        row("c1", "capacity", tie_group="g1"),
        row("c1", "pricing", tie_group="g1"),
    )
    units = {"capacity": frozenset({p0}), "pricing": frozenset({p1})}
    cells = event_cells(gold, unit_index(source), units)
    assert theme_tallies(cells, units) == {"capacity": Tally(tp=1)}
    assert unit_tally(cells, units) == Tally(tp=2)
    assert f1(unit_tally(cells, units)) == 1.0
    spans = {"capacity": ((0, 20),), "pricing": ((21, 37),)}
    assert char_counts(cells, spans) == (36, 36)


def test_the_unchosen_member_carrying_the_groups_evidence_is_a_hit() -> None:
    """Gold: tie group g1 over capacity and pricing, by c1 (P1). The run accepts
    capacity over P3 and pricing over P1. D19-6 resolves g1 to capacity, the lower
    predicted member, so pricing, which carries g1's evidence, is excused. g1's cell
    {P1} is covered by pricing: tp 1, fn 0. Capacity's P3 lies in no cell capacity
    belongs to: fp 1; pricing's P1 is a hit. Unit F1 = 2 / (2 + 1) = 2/3. Characters:
    P1's 16 shared, capacity's 16 of P3 extra: (16, 32). (Before: capacity's gold
    {P1} against {P3}: tp 0, fp 1, fn 1, F1 0.)"""
    source = bundle()
    _, p1, _, p3 = unit_ids(source)
    gold = tie_reading(
        row("c1", "capacity", tie_group="g1"), row("c1", "pricing", tie_group="g1")
    )
    units = {"capacity": frozenset({p3}), "pricing": frozenset({p1})}
    cells = event_cells(gold, unit_index(source), units)
    assert cells.present == {"capacity"} and cells.excused == {"pricing"}
    assert unit_tally(cells, units) == Tally(tp=1, fp=1)
    assert f1(unit_tally(cells, units)) == pytest.approx(2 / 3)
    spans = {"capacity": ((57, 73),), "pricing": ((21, 37),)}
    assert char_counts(cells, spans) == (16, 32)


def test_a_member_with_the_wrong_evidence_is_still_a_miss() -> None:
    """Gold: tie group g1 over capacity and pricing, by c1 (P1). A run accepting
    only pricing, over P3: D19-6 resolves g1 to pricing. g1's cell {P1} is not
    covered: fn 1; pricing's P3 lies outside it: fp 1. Unit F1 = 0 / 2 = 0, as
    before. A run accepting capacity over P1 and pricing over P3: g1 resolves to
    capacity and covers its cell, tp 1; pricing is excused and its P3 lies outside
    g1's units, so it is not scored, as before: Tally(tp=1)."""
    source = bundle()
    _, p1, _, p3 = unit_ids(source)
    gold = tie_reading(
        row("c1", "capacity", tie_group="g1"), row("c1", "pricing", tie_group="g1")
    )
    index = unit_index(source)
    wrong = {"pricing": frozenset({p3})}
    assert unit_tally(event_cells(gold, index, wrong), wrong) == Tally(fp=1, fn=1)
    both = {"capacity": frozenset({p1}), "pricing": frozenset({p3})}
    cells = event_cells(gold, index, both)
    assert cells.excused == {"pricing"}
    assert unit_tally(cells, both) == Tally(tp=1)
    assert char_counts(cells, {"capacity": ((21, 37),), "pricing": ((57, 73),)}) == (
        16,
        16,
    )


def test_overlapping_tie_groups_sharing_a_quote_are_each_covered() -> None:
    """Gold: tie group g1 over capacity and demand by c0, and g2 over demand and
    pricing by c4, which quotes q0 too: both groups' evidence is P0.

    A run accepting demand over P0: D19-6 resolves both groups to demand. Each group
    is one evidence cell over {P0}, and demand covers both: tp 2, unit F1 1;
    characters 20 shared in each: (40, 40).

    A run accepting pricing over P0: g1 resolves to capacity (nothing predicted, no
    member present untied, lowest ID) and g2 to pricing. g1's cell is not covered,
    since neither capacity nor demand predicts it: fn 1; g2's is covered by
    pricing: tp 1. Unit F1 = 2 / (2 + 1) = 2/3; the theme cells are capacity a miss
    and pricing a hit, as before."""
    source = bundle()
    p0 = unit_ids(source)[0]
    base = tie_reading(
        row("c0", "capacity", tie_group="g1"),
        row("c0", "demand", tie_group="g1"),
        row("c4", "demand", tie_group="g2"),
        row("c4", "pricing", tie_group="g2"),
    )
    gold = base.model_copy(update={"claims": (*base.claims, claim("c4", "q0"))})
    index = unit_index(source)
    demand = {"demand": frozenset({p0})}
    cells = event_cells(gold, index, demand)
    assert cells.present == {"demand"}
    assert unit_tally(cells, demand) == Tally(tp=2)
    assert char_counts(cells, {"demand": ((0, 20),)}) == (40, 40)
    pricing = {"pricing": frozenset({p0})}
    cells = event_cells(gold, index, pricing)
    assert theme_tallies(cells, pricing) == {
        "capacity": Tally(fn=1),
        "pricing": Tally(tp=1),
    }
    assert unit_tally(cells, pricing) == Tally(tp=1, fn=1)


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
