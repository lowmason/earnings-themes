"""Per-event counts and their figures, with hand-computed known answers (the Stage
11 spec, §Metrics; R12.5, R12.8, R13.1)."""

import pytest
from earnings_themes.annotation import Reading
from earnings_themes.evaluation.align import unit_index
from earnings_themes.evaluation.cells import event_cells
from earnings_themes.evaluation.scores import (
    EvidenceTally,
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
    """g1 resolves to the predicted pricing. Cells: capacity {P0}, g1 {P1, P2}.
    Units: accepted capacity {P0, P3} (1 hit) and pricing {P1} (1 hit): 2 of 3;
    gold P0 and P1 covered, P2 not: 2 of 3. P = R = F1 = 2/3, as the old
    Tally(2, 1, 1) gave. Characters: accepted capacity [0, 20) and [57, 73) (36,
    5 within [0, 5)) and pricing [21, 37) (16, 7 within [30, 45)): 12 of 52; gold
    [0, 5) and [30, 45), 20, of which 12 covered. Union 52 + 20 - 12 = 60: shared
    over union (12, 60), as before."""
    source, gold = example()
    p0, p1, _, p3 = unit_ids(source)
    cells = event_cells(gold, unit_index(source), {"pricing", "capacity"})
    accepted_units = {"pricing": frozenset({p1}), "capacity": frozenset({p0, p3})}
    counts = unit_tally(cells, accepted_units)
    assert counts == EvidenceTally(accepted_hits=2, accepted=3, gold_hits=2, gold=3)
    assert counts.f1() == pytest.approx(2 / 3)
    spans = {"pricing": ((21, 37),), "capacity": ((0, 20), (57, 73))}
    chars = char_counts(cells, spans)
    assert chars == EvidenceTally(accepted_hits=12, accepted=52, gold_hits=12, gold=20)
    assert (chars.accepted_hits, chars.union()) == (12, 60)


def untied_reading() -> Reading:
    """Capacity by c1 (q1 = [0, 5) in P0), labor by c2 (q2 = P1), hiring only
    uncertain for c2, and debt decided against for c3 (q3 = P3): no tie group."""
    p0, p1, _, p3 = unit_ids(bundle())
    return reading(
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


def test_a_reading_without_tie_groups_scores_as_before() -> None:
    """No tie group: each present theme is its own evidence cell. Gold: capacity by
    c1 (q1 = [0, 5) in P0), labor by c2 (q2 = P1), hiring only uncertain for c2, debt
    decided against for c3. The run accepts capacity over P0 and P3, hiring over P1
    and debt over P3. Units: capacity tp 1 (P0) and fp 1 (P3); labor fn 1 (P1);
    hiring is uncertain only, so unscored; debt fp 1 (P3): the old Tally(1, 2, 1),
    precision 1/3, recall 1/2, F1 2 / (2 + 2 + 1) = 2/5. In the new counts: accepted
    capacity {P0, P3} and debt {P3}, 1 hit of 3; gold capacity {P0} and labor {P1},
    1 covered of 2; F1 = 2 * 1 * 1 / (1 * 2 + 1 * 3) = 2/5.
    Characters: capacity shares 5 of a 5 + 15 + 16 = 36 union; labor's 16 are
    missed; debt's 16 are extra: (5, 36 + 16 + 16) = (5, 68). In the new counts:
    accepted 36 + 16 = 52 with 5 hits; gold 5 + 16 = 21 with 5 covered; union 52 +
    21 - 5 = 68."""
    source = bundle()
    p0, p1, _, p3 = unit_ids(source)
    gold = untied_reading()
    units = {
        "capacity": frozenset({p0, p3}),
        "hiring": frozenset({p1}),
        "debt": frozenset({p3}),
    }
    cells = event_cells(gold, unit_index(source), units)
    counts = unit_tally(cells, units)
    assert counts == EvidenceTally(accepted_hits=1, accepted=3, gold_hits=1, gold=2)
    old = Tally(tp=1, fp=2, fn=1)
    assert counts.precision() == precision(old) == pytest.approx(1 / 3)
    assert counts.recall() == recall(old) == 1 / 2
    assert counts.f1() == f1(old) == pytest.approx(2 / 5)
    spans = {
        "capacity": ((0, 20), (57, 73)),
        "hiring": ((21, 37),),
        "debt": ((57, 73),),
    }
    chars = char_counts(cells, spans)
    assert chars == EvidenceTally(accepted_hits=5, accepted=52, gold_hits=5, gold=21)
    assert (chars.accepted_hits, chars.union()) == (5, 68)
    assert chars.jaccard() == 5 / 68


def test_evidence_under_the_wrong_theme_is_no_hit() -> None:
    """Scoring stays theme-specific. ``untied_reading``, and a run accepting only
    debt, over [0, 5) in P0: capacity's gold characters, under another theme. Cells:
    capacity's {P0} ([0, 5)) and labor's {P1} ([21, 37)); debt, decided against and
    not present, is scored and belongs to no cell. Units: debt's P0 is accepted, no
    hit (1, 0); neither cell's theme accepts anything: gold 2, covered 0. (0, 1, 0,
    2), F1 0; union 1 + 2 - 0 = 3, as the old Tally(fp=1, fn=2) totals 3, P0 counted
    once as debt's and once as capacity's gold item. Characters: debt's 5 accepted, none a
    hit; gold 5 + 16 = 21, none covered: (0, 5, 0, 21), union 5 + 21 - 0 = 26,
    Jaccard 0 / 26 = 0, as the old (shared 0, union 5 + 5 + 16 = 26)."""
    source = bundle()
    p0 = unit_ids(source)[0]
    units = {"debt": frozenset({p0})}
    cells = event_cells(untied_reading(), unit_index(source), units)
    assert cells.present == {"capacity", "labor"} and cells.scored("debt")
    counts = unit_tally(cells, units)
    assert counts == EvidenceTally(accepted_hits=0, accepted=1, gold_hits=0, gold=2)
    assert (counts.f1(), counts.union()) == (0.0, 3)
    chars = char_counts(cells, {"debt": ((0, 5),)})
    assert chars == EvidenceTally(accepted_hits=0, accepted=5, gold_hits=0, gold=21)
    assert (chars.accepted_hits, chars.union(), chars.jaccard()) == (0, 26, 0.0)


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


def plus_claim(gold: Reading, claim_id: str, quote_id: str) -> Reading:
    """``gold`` with one more claim, ``claim_id``, quoting ``quote_id``."""
    return gold.model_copy(update={"claims": (*gold.claims, claim(claim_id, quote_id))})


def test_a_tie_groups_evidence_is_covered_by_any_predicted_member() -> None:
    """Gold: capacity is supported untied by c0 (P0), and tie group g1 over capacity
    and pricing by c1 (P1). The run accepts capacity over P0 and pricing over P1.
    D19-6 resolves g1 to capacity, the lower predicted member, and excuses pricing:
    the theme cells are capacity, a hit, and nothing else (theme F1 1, as before).

    Evidence cells: capacity's own {P0}, and g1's {P1}, which capacity or pricing
    covers. Gold side: capacity covers P0 and pricing covers P1, 2 of 2. Accepted
    side: capacity, scored, accepts P0, in its own cell: 1 accepted, 1 hit. Pricing
    is excused: its P1 lies in g1, a cell it belongs to, so it counts as 1 accepted
    and 1 hit, never a false positive. 2 of 2: precision 1, recall 1, unit F1 1.
    Characters: capacity's 20 of P0 and pricing's 16 of P1 accepted, all hits; gold
    20 + 16, all covered: union 36 + 36 - 36 = 36, Jaccard 36 / 36 = 1. (Round 2
    left the excused pricing out of the accepted side, (1, 1, 2, 2) and (20, 20, 36,
    36): the figures agree, but the counts now hold the group's evidence that the
    run did accept. Before the tie cells: capacity's gold {P0, P1} against {P0}: tp
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
    counts = unit_tally(cells, units)
    assert counts == EvidenceTally(accepted_hits=2, accepted=2, gold_hits=2, gold=2)
    assert (counts.precision(), counts.recall(), counts.f1()) == (1.0, 1.0, 1.0)
    spans = {"capacity": ((0, 20),), "pricing": ((21, 37),)}
    chars = char_counts(cells, spans)
    assert chars == EvidenceTally(accepted_hits=36, accepted=36, gold_hits=36, gold=36)
    assert (chars.union(), chars.jaccard()) == (36, 1.0)


def test_an_excused_members_evidence_outside_its_group_is_ignored() -> None:
    """The scenario above, with pricing also accepting P3, which no gold cell holds.
    Pricing is excused, so only its evidence inside g1's units counts: P1, 1
    accepted and 1 hit; its P3 is neither accepted nor a false positive. Units: (2,
    2, 2, 2), F1 1, as above. Characters: pricing's [57, 73) lies outside g1's
    [21, 37), so it adds nothing: (36, 36, 36, 36), union 36, Jaccard 1."""
    source = bundle()
    p0, p1, _, p3 = unit_ids(source)
    gold = tie_reading(
        row("c0", "capacity"),
        row("c1", "capacity", tie_group="g1"),
        row("c1", "pricing", tie_group="g1"),
    )
    units = {"capacity": frozenset({p0}), "pricing": frozenset({p1, p3})}
    cells = event_cells(gold, unit_index(source), units)
    assert cells.excused == {"pricing"}
    counts = unit_tally(cells, units)
    assert counts == EvidenceTally(accepted_hits=2, accepted=2, gold_hits=2, gold=2)
    assert counts.f1() == 1.0
    spans = {"capacity": ((0, 20),), "pricing": ((21, 37), (57, 73))}
    chars = char_counts(cells, spans)
    assert chars == EvidenceTally(accepted_hits=36, accepted=36, gold_hits=36, gold=36)
    assert (chars.union(), chars.jaccard()) == (36, 1.0)


def test_the_unchosen_member_carrying_the_groups_evidence_is_a_hit() -> None:
    """Gold: tie group g1 over capacity and pricing, by c1 (P1). The run accepts
    capacity over P3 and pricing over P1. D19-6 resolves g1 to capacity, the lower
    predicted member, so pricing, which carries g1's evidence, is excused. Gold
    side: g1's cell {P1} is covered by pricing, 1 of 1: recall 1. Accepted side:
    capacity, scored, accepts P3, in no cell it belongs to: 1 accepted, no hit. The
    excused pricing's P1 lies in g1, its group's cell: 1 accepted, 1 hit. Precision
    1 / 2, F1 = 2 * 1 * 1 / (1 * 1 + 1 * 2) = 2/3, as 7cde927's single tally gave
    (tp 1, fp 1). Characters: capacity's 16 of P3, no hit, and pricing's 16 of P1,
    all hits: accepted 32, 16 hits; gold 16, covered: union 32 + 16 - 16 = 32, the
    accepted (capacity, P3) and (pricing, P1) and no missed gold item; Jaccard
    16 / 32 = 1/2."""
    source = bundle()
    _, p1, _, p3 = unit_ids(source)
    gold = tie_reading(
        row("c1", "capacity", tie_group="g1"), row("c1", "pricing", tie_group="g1")
    )
    units = {"capacity": frozenset({p3}), "pricing": frozenset({p1})}
    cells = event_cells(gold, unit_index(source), units)
    assert cells.present == {"capacity"} and cells.excused == {"pricing"}
    counts = unit_tally(cells, units)
    assert counts == EvidenceTally(accepted_hits=1, accepted=2, gold_hits=1, gold=1)
    assert (counts.precision(), counts.recall()) == (1 / 2, 1.0)
    assert counts.f1() == pytest.approx(2 / 3)
    spans = {"capacity": ((57, 73),), "pricing": ((21, 37),)}
    chars = char_counts(cells, spans)
    assert chars == EvidenceTally(accepted_hits=16, accepted=32, gold_hits=16, gold=16)
    assert (chars.union(), chars.jaccard()) == (32, 1 / 2)


def test_redundant_correct_alternatives_each_count_as_hits() -> None:
    """The rule's known effect: an accepted (theme, item) pair lying in a cell its
    theme belongs to is a hit however many other themes of the cell accept the item,
    so a run that also asserts a correct alternative scores higher. A maximum
    matching of accepted pairs to gold items is the stricter alternative, recorded
    as a handoff for plan B.

    An excused alternative. Gold: tie group g1 over capacity and pricing, by c1
    (P1). Capacity alone over P1 and P3: g1 resolves to capacity, scored: 2
    accepted, 1 hit (P1); g1's {P1} covered, 1 of 1. (1, 2, 1, 1): F1 = 2 * 1 * 1 /
    (1 * 1 + 1 * 2) = 2/3. Characters, [21, 37) and [57, 73): (16, 32, 16, 16),
    union 32 + 16 - 16 = 32, Jaccard 1/2. Adding pricing over P1: g1 still resolves
    to capacity, the lower predicted member, and the excused pricing's P1 lies in
    g1: 1 accepted, 1 hit. (2, 3, 1, 1): precision 2/3, F1 = 2 * 2 * 1 / (2 * 1 +
    1 * 3) = 4/5. Characters: (32, 48, 16, 16), union 48, Jaccard 2/3.

    A scored alternative. Gold: g1 as above, and pricing untied by c0 (P0), so
    pricing is present, scored, and g1 still resolves to capacity. Cells: pricing's
    {P0} and g1's {P1}. Capacity over P1 and P3 (2 accepted, 1 hit) and pricing over
    P0 (1, 1); gold P0 and P1 covered, 2 of 2: (2, 3, 2, 2), F1 = 2 * 2 * 2 / (2 * 2
    + 2 * 3) = 4/5. Characters: capacity's 32, 16 hits; pricing's [0, 20), 20 hits;
    gold 20 + 16, covered: (36, 52, 36, 36). Pricing over P0 and P1: its P1 lies in
    g1, a cell it belongs to: (2, 2). (3, 4, 2, 2), F1 = 2 * 3 * 2 / (3 * 2 + 2 * 4)
    = 6/7. Characters: pricing's [0, 20) and [21, 37), 36, all hits: (52, 68, 36,
    36)."""
    source = bundle()
    p0, p1, _, p3 = unit_ids(source)
    index = unit_index(source)
    capacity = {"capacity": frozenset({p1, p3})}
    capacity_spans = {"capacity": ((21, 37), (57, 73))}
    tie = (row("c1", "capacity", tie_group="g1"), row("c1", "pricing", tie_group="g1"))

    def tallies(gold, units, spans):
        cells = event_cells(gold, index, units)
        return unit_tally(cells, units), char_counts(cells, spans)

    excused = tie_reading(*tie)
    assert event_cells(excused, index, {"capacity", "pricing"}).excused == {"pricing"}
    alone, alone_chars = tallies(excused, capacity, capacity_spans)
    assert (alone, alone_chars) == (
        EvidenceTally(1, 2, 1, 1),
        EvidenceTally(16, 32, 16, 16),
    )
    assert alone.f1() == pytest.approx(2 / 3) and alone_chars.jaccard() == 1 / 2
    both, both_chars = tallies(
        excused,
        {**capacity, "pricing": frozenset({p1})},
        {**capacity_spans, "pricing": ((21, 37),)},
    )
    assert (both, both_chars) == (
        EvidenceTally(2, 3, 1, 1),
        EvidenceTally(32, 48, 16, 16),
    )
    assert both.f1() == pytest.approx(4 / 5) and both_chars.jaccard() == pytest.approx(
        2 / 3
    )
    scored = tie_reading(row("c0", "pricing"), *tie)
    cells = event_cells(scored, index, {"capacity", "pricing"})
    assert cells.present == {"capacity", "pricing"} and not cells.excused
    one, one_chars = tallies(
        scored,
        {**capacity, "pricing": frozenset({p0})},
        {**capacity_spans, "pricing": ((0, 20),)},
    )
    assert (one, one_chars) == (
        EvidenceTally(2, 3, 2, 2),
        EvidenceTally(36, 52, 36, 36),
    )
    assert one.f1() == pytest.approx(4 / 5)
    two, two_chars = tallies(
        scored,
        {**capacity, "pricing": frozenset({p0, p1})},
        {**capacity_spans, "pricing": ((0, 20), (21, 37))},
    )
    assert (two, two_chars) == (
        EvidenceTally(3, 4, 2, 2),
        EvidenceTally(52, 68, 36, 36),
    )
    assert two.f1() == pytest.approx(6 / 7)


def test_adding_a_correct_item_never_lowers_a_figure() -> None:
    """Monotone. Gold: tie group g1 over capacity and demand by c1, and g2 over
    capacity and pricing by c4, which quotes q1 too: both groups' evidence is P1.
    Run 1 accepts capacity over P3, and demand and pricing over P1: g1 and g2
    resolve to capacity, the lowest predicted member, which is scored; demand and
    pricing are excused. Gold: g1's {P1}, covered by demand, and g2's {P1}, covered
    by pricing: 2 of 2. Accepted: capacity's P3, in no cell of capacity's (1
    accepted, 0 hits); demand's P1, in g1, and pricing's P1, in g2 (1, 1 each). (2,
    3, 2, 2): precision 2/3, recall 1, F1 = 2 * 2 * 2 / (2 * 2 + 2 * 3) = 8/10.
    Characters: 16 + 16 + 16 accepted, 32 hits; gold 16 + 16, all covered: (32, 48,
    32, 32), union 48 + 32 - 32 = 48, Jaccard 2/3.

    Run 2 adds P1 to capacity, which lies in both its cells: capacity 2 accepted, 1
    hit, the others as before. (3, 4, 2, 2): precision 3/4, recall 1, F1 = 2 * 3 *
    2 / (3 * 2 + 2 * 4) = 6/7. Characters: capacity's [21, 37) and [57, 73), 32
    accepted, 16 hits: (48, 64, 32, 32), union 64, Jaccard 3/4. Every figure is at
    least run 1's. (041bb39's one-credit rule gave run 2 (1, 2, 2, 2), F1 2/3,
    lower than run 1's 8/10.)"""
    source = bundle()
    _, p1, _, p3 = unit_ids(source)
    gold = plus_claim(
        tie_reading(
            row("c1", "capacity", tie_group="g1"),
            row("c1", "demand", tie_group="g1"),
            row("c4", "capacity", tie_group="g2"),
            row("c4", "pricing", tie_group="g2"),
        ),
        "c4",
        "q1",
    )
    first = {
        "capacity": frozenset({p3}),
        "demand": frozenset({p1}),
        "pricing": frozenset({p1}),
    }
    second = {**first, "capacity": frozenset({p1, p3})}
    first_spans = {
        "capacity": ((57, 73),),
        "demand": ((21, 37),),
        "pricing": ((21, 37),),
    }
    second_spans = {**first_spans, "capacity": ((21, 37), (57, 73))}
    cells = event_cells(gold, unit_index(source), first)
    assert cells.present == {"capacity"} and cells.excused == {"demand", "pricing"}
    before, after = unit_tally(cells, first), unit_tally(cells, second)
    assert before == EvidenceTally(accepted_hits=2, accepted=3, gold_hits=2, gold=2)
    assert after == EvidenceTally(accepted_hits=3, accepted=4, gold_hits=2, gold=2)
    assert (before.f1(), after.f1()) == (pytest.approx(8 / 10), pytest.approx(6 / 7))
    for figure in (EvidenceTally.precision, EvidenceTally.recall, EvidenceTally.f1):
        assert figure(after) >= figure(before)
    chars_before = char_counts(cells, first_spans)
    chars_after = char_counts(cells, second_spans)
    assert chars_before == EvidenceTally(32, 48, 32, 32)
    assert chars_after == EvidenceTally(48, 64, 32, 32)
    assert (chars_before.union(), chars_after.union()) == (48, 64)
    assert chars_before.jaccard() == pytest.approx(2 / 3)
    assert chars_after.jaccard() == 3 / 4 >= chars_before.jaccard()


def test_the_tally_does_not_depend_on_theme_ids() -> None:
    """Gold: tie group g1 over capacity, demand and pricing by c1, and g3 over
    capacity and pricing by c4, which quotes q1 too: both groups' evidence is P1.
    The run accepts capacity over P3, and demand and pricing over P1. g1 and g3
    resolve to capacity, the lowest predicted member, which is scored; demand and
    pricing are excused. Gold: g1's {P1}, covered by demand or pricing, and g3's
    {P1}, covered by pricing: 2 of 2. Accepted: capacity's P3, no hit (1, 0);
    demand's P1, in g1 (1, 1); pricing's P1, in g1 and g3, once (1, 1). (2, 3, 2,
    2), F1 = 2 * 2 * 2 / (2 * 2 + 2 * 3) = 8/10. Characters: 16 + 16 + 16 accepted,
    32 hits; gold 16 + 16, all covered: (32, 48, 32, 32), union 48, Jaccard 2/3.

    Swapping the names demand and pricing (g1 the same set; g3 over capacity and
    demand) changes no count: demand's P1 now lies in g1 and g3, once, and
    pricing's in g1. (041bb39's one-credit rule gave the swapped reading (1, 2, 2,
    2), since the lower ID, demand, took g1's credit.)"""
    source = bundle()
    _, p1, _, p3 = unit_ids(source)
    index = unit_index(source)
    units = {
        "capacity": frozenset({p3}),
        "demand": frozenset({p1}),
        "pricing": frozenset({p1}),
    }
    spans = {
        "capacity": ((57, 73),),
        "demand": ((21, 37),),
        "pricing": ((21, 37),),
    }

    def tallies(in_g3: str) -> tuple[EvidenceTally, EvidenceTally]:
        gold = plus_claim(
            tie_reading(
                row("c1", "capacity", tie_group="g1"),
                row("c1", "demand", tie_group="g1"),
                row("c1", "pricing", tie_group="g1"),
                row("c4", "capacity", tie_group="g3"),
                row("c4", in_g3, tie_group="g3"),
            ),
            "c4",
            "q1",
        )
        cells = event_cells(gold, index, units)
        assert cells.present == {"capacity"}
        assert cells.excused == {"demand", "pricing"}
        return unit_tally(cells, units), char_counts(cells, spans)

    counts, chars = tallies("pricing")
    assert counts == EvidenceTally(accepted_hits=2, accepted=3, gold_hits=2, gold=2)
    assert counts.f1() == pytest.approx(8 / 10)
    assert chars == EvidenceTally(accepted_hits=32, accepted=48, gold_hits=32, gold=32)
    assert (chars.union(), chars.jaccard()) == (48, pytest.approx(2 / 3))
    assert tallies("demand") == (counts, chars)


def test_an_excused_members_item_in_two_of_its_cells_counts_once() -> None:
    """Gold: tie group g1 over capacity and pricing by c1, and g2 over demand and
    pricing by c4, which quotes q1 too: both groups' evidence is P1. The run accepts
    capacity and demand over P3, and pricing over P1. g1 resolves to capacity and g2
    to demand, the lower predicted members, so pricing is excused from both. Gold:
    g1's {P1} and g2's {P1}, each covered by pricing: 2 of 2. Accepted: capacity's
    and demand's P3, no hits (2 accepted, 0 hits); pricing's P1 lies in g1 and in
    g2, counted once (1, 1). (1, 3, 2, 2): precision 1/3, recall 1, F1 = 2 * 1 * 2 /
    (1 * 2 + 2 * 3) = 1/2. Characters: 16 + 16 accepted, no hits, and pricing's
    [21, 37), 16 hits, once; gold 16 + 16, all covered: (16, 48, 32, 32), union 48 +
    32 - 32 = 48, Jaccard 1/3."""
    source = bundle()
    _, p1, _, p3 = unit_ids(source)
    gold = plus_claim(
        tie_reading(
            row("c1", "capacity", tie_group="g1"),
            row("c1", "pricing", tie_group="g1"),
            row("c4", "demand", tie_group="g2"),
            row("c4", "pricing", tie_group="g2"),
        ),
        "c4",
        "q1",
    )
    units = {
        "capacity": frozenset({p3}),
        "demand": frozenset({p3}),
        "pricing": frozenset({p1}),
    }
    cells = event_cells(gold, unit_index(source), units)
    assert cells.present == {"capacity", "demand"} and cells.excused == {"pricing"}
    counts = unit_tally(cells, units)
    assert counts == EvidenceTally(accepted_hits=1, accepted=3, gold_hits=2, gold=2)
    assert counts.f1() == 1 / 2
    spans = {
        "capacity": ((57, 73),),
        "demand": ((57, 73),),
        "pricing": ((21, 37),),
    }
    chars = char_counts(cells, spans)
    assert chars == EvidenceTally(accepted_hits=16, accepted=48, gold_hits=32, gold=32)
    assert (chars.union(), chars.jaccard()) == (48, 1 / 3)


def test_a_member_with_the_wrong_evidence_is_still_a_miss() -> None:
    """Gold: tie group g1 over capacity and pricing, by c1 (P1). A run accepting
    only pricing, over P3: D19-6 resolves g1 to pricing. g1's cell {P1} is not
    covered (0 of 1); pricing's P3 lies outside it (0 of 1): F1 0, as before. A run
    accepting capacity over P1 and pricing over P3: g1 resolves to capacity, which
    covers its cell (1 of 1) with its one accepted unit (1 of 1); pricing is excused
    and its P3 lies outside g1's units, so it is not scored, as before: F1 1.
    Characters: capacity's 16 accepted, all hits, and g1's 16, covered: union 16."""
    source = bundle()
    _, p1, _, p3 = unit_ids(source)
    gold = tie_reading(
        row("c1", "capacity", tie_group="g1"), row("c1", "pricing", tie_group="g1")
    )
    index = unit_index(source)
    wrong = {"pricing": frozenset({p3})}
    counts = unit_tally(event_cells(gold, index, wrong), wrong)
    assert counts == EvidenceTally(accepted_hits=0, accepted=1, gold_hits=0, gold=1)
    assert counts.f1() == 0.0
    both = {"capacity": frozenset({p1}), "pricing": frozenset({p3})}
    cells = event_cells(gold, index, both)
    assert cells.excused == {"pricing"}
    counts = unit_tally(cells, both)
    assert counts == EvidenceTally(accepted_hits=1, accepted=1, gold_hits=1, gold=1)
    assert counts.f1() == 1.0
    chars = char_counts(cells, {"capacity": ((21, 37),), "pricing": ((57, 73),)})
    assert chars == EvidenceTally(accepted_hits=16, accepted=16, gold_hits=16, gold=16)
    assert chars.union() == 16


def test_overlapping_tie_groups_sharing_a_quote_are_each_covered() -> None:
    """Gold: tie group g1 over capacity and demand by c0, and g2 over demand and
    pricing by c4, which quotes q0 too: both groups' evidence is P0.

    A run accepting demand over P0: D19-6 resolves both groups to demand. Each group
    is one evidence cell over {P0}, and demand covers both: recall 2/2. Its one
    accepted unit lies in its cells: precision 1/1. F1 1. Characters: 20 accepted,
    all hits; 20 + 20 gold, all covered: union 20 + 40 - 40 = 20, Jaccard 1.

    A run accepting pricing over P0: g1 resolves to capacity (nothing predicted, no
    member present untied, lowest ID) and g2 to pricing. g1's cell is not covered,
    since neither capacity nor demand predicts it, and g2's is covered by pricing:
    recall 1/2. Pricing's P0 lies in g2: precision 1/1. F1 = 2 * 1 * 1 / (1 * 2 +
    1 * 1) = 2/3; the theme cells are capacity a miss and pricing a hit, as
    before."""
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
    counts = unit_tally(cells, demand)
    assert counts == EvidenceTally(accepted_hits=1, accepted=1, gold_hits=2, gold=2)
    assert (counts.precision(), counts.recall(), counts.f1()) == (1.0, 1.0, 1.0)
    chars = char_counts(cells, {"demand": ((0, 20),)})
    assert chars == EvidenceTally(accepted_hits=20, accepted=20, gold_hits=40, gold=40)
    assert chars.jaccard() == 1.0
    pricing = {"pricing": frozenset({p0})}
    cells = event_cells(gold, index, pricing)
    assert theme_tallies(cells, pricing) == {
        "capacity": Tally(fn=1),
        "pricing": Tally(tp=1),
    }
    counts = unit_tally(cells, pricing)
    assert counts == EvidenceTally(accepted_hits=1, accepted=1, gold_hits=1, gold=2)
    assert (counts.precision(), counts.recall()) == (1.0, 1 / 2)
    assert counts.f1() == pytest.approx(2 / 3)


def test_an_accepted_unit_is_one_hit_however_many_cells_hold_it() -> None:
    """N1. Gold: capacity untied by c0, quoting [0, 5) in P0, and tie group g1 over
    capacity and pricing by c1, quoting [10, 15) in P0 too. The run accepts capacity
    over P0 and P3; g1 resolves to capacity. Gold cells: capacity's {P0} and g1's
    {P0}, both covered by capacity's P0: recall 2/2 = 1. Accepted (theme, unit)
    pairs: (capacity, P0), in capacity's cells, and (capacity, P3), in none:
    precision 1/2. F1 = 2 * 1/2 * 1 / (1/2 + 1) = 2/3."""
    source = bundle()
    p0, _, _, p3 = unit_ids(source)
    gold = reading(
        quotes=(quote("q0", 0, 5, p0), quote("q1", 10, 15, p0)),
        claims=(claim("c0", "q0"), claim("c1", "q1")),
        assignments=(
            row("c0", "capacity"),
            row("c1", "capacity", tie_group="g1"),
            row("c1", "pricing", tie_group="g1"),
        ),
    )
    units = {"capacity": frozenset({p0, p3})}
    counts = unit_tally(event_cells(gold, unit_index(source), units), units)
    assert counts == EvidenceTally(accepted_hits=1, accepted=2, gold_hits=2, gold=2)
    assert counts.precision() == 1 / 2
    assert counts.recall() == 1.0
    assert counts.f1() == pytest.approx(2 / 3)


def test_an_accepted_character_is_one_hit_however_many_cells_hold_it() -> None:
    """N1, characters. Gold: capacity untied by c0 and tie group g1 over capacity
    and pricing by c1, both quoting q0 = [0, 20). The run accepts capacity over
    [0, 20) and [57, 73). Accepted characters: 36, of which 20 lie in capacity's
    cells (hits). Gold characters: 20 in each cell, all covered (40 of 40). Jaccard
    = hits / (accepted + gold missed) = 20 / (36 + 0) = 5/9, as the pre-tie-cell
    model gave (capacity's 20 gold characters against its 36 accepted)."""
    source = bundle()
    p0 = unit_ids(source)[0]
    gold = reading(
        quotes=(quote("q0", 0, 20, p0),),
        claims=(claim("c0", "q0"), claim("c1", "q0")),
        assignments=(
            row("c0", "capacity"),
            row("c1", "capacity", tie_group="g1"),
            row("c1", "pricing", tie_group="g1"),
        ),
    )
    cells = event_cells(gold, unit_index(source), {"capacity"})
    chars = char_counts(cells, {"capacity": ((0, 20), (57, 73))})
    assert chars == EvidenceTally(accepted_hits=20, accepted=36, gold_hits=40, gold=40)
    assert (chars.accepted_hits, chars.union()) == (20, 36)
    assert chars.jaccard() == pytest.approx(5 / 9)


def test_uncertain_only_predictions_add_no_extra_units() -> None:
    """``labor`` is uncertain only, so unscored; the unpredicted tie resolves to
    demand. Gold capacity {P0} and g1 {P1, P2}: 0 of 3 covered, nothing accepted:
    F1 0, as the old Tally(fn=3) gave."""
    source, gold = example()
    p3 = unit_ids(source)[3]
    cells = event_cells(gold, unit_index(source), {"labor"})
    counts = unit_tally(cells, {"labor": frozenset({p3})})
    assert counts == EvidenceTally(gold=3)
    assert counts.f1() == f1(Tally(fn=3)) == 0.0
    assert EvidenceTally().f1() is None


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
