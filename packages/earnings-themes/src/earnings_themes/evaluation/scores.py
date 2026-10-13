"""Stage 11's per-event counts, and the figures they combine into (the Stage 11
spec, §Metrics; R12.8, R13.1).

Each function scores one event. A partition's figure sums its events' counts, so the
event-clustered bootstrap (``bootstrap.py``) resamples whole events. A figure with an
empty denominator is ``None``, never zero (A §Non-negotiables: never coerce null).
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from earnings_themes.evaluation.align import (
    Span,
    UnitIndex,
    char_overlap,
    covered,
    difference,
    intersection,
    units_over,
)
from earnings_themes.evaluation.cells import EventCells, EvidenceCell, GoldReading
from earnings_themes.gold import DraftCounts, NegativeKind, ReleaseLabel


@dataclass(frozen=True)
class Tally:
    """Hits, false positives, and misses."""

    tp: int = 0
    fp: int = 0
    fn: int = 0

    def __add__(self, other: "Tally") -> "Tally":
        return Tally(self.tp + other.tp, self.fp + other.fp, self.fn + other.fn)


def ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def precision(tally: Tally) -> float | None:
    return ratio(tally.tp, tally.tp + tally.fp)


def recall(tally: Tally) -> float | None:
    return ratio(tally.tp, tally.tp + tally.fn)


def f1(tally: Tally) -> float | None:
    return ratio(2 * tally.tp, 2 * tally.tp + tally.fp + tally.fn)


@dataclass(frozen=True)
class EvidenceTally:
    """One event's evidence, in units or characters (FP13, FP20), counted from each
    side, so that one accepted item covering two gold cells is one hit: a scored
    theme's accepted items, and those lying in a cell it belongs to as hits; an
    excused member's accepted items that fill a gold slot of one of its cells that
    no scored theme, nor a member with a lower ID, of that cell also accepts (one
    credit per slot), each both accepted and a hit, its others not scored; the gold
    cells' items, and those some theme of their cell accepts."""

    accepted_hits: int = 0
    accepted: int = 0
    gold_hits: int = 0
    gold: int = 0

    def __add__(self, other: "EvidenceTally") -> "EvidenceTally":
        return EvidenceTally(
            self.accepted_hits + other.accepted_hits,
            self.accepted + other.accepted,
            self.gold_hits + other.gold_hits,
            self.gold + other.gold,
        )

    def precision(self) -> float | None:
        return ratio(self.accepted_hits, self.accepted)

    def recall(self) -> float | None:
        return ratio(self.gold_hits, self.gold)

    def f1(self) -> float | None:
        """The harmonic mean of precision and recall, 2PR / (P + R), in integers;
        0 when either side holds items but nothing hits, and ``None`` when neither
        side holds any. Without tie groups both hit counts are ``Tally``'s ``tp``,
        and this is its F1."""
        if not self.accepted and not self.gold:
            return None
        both = 2 * self.accepted_hits * self.gold_hits
        either = self.accepted_hits * self.gold + self.gold_hits * self.accepted
        return ratio(both, either) or 0.0

    def union(self) -> int:
        """The union over (theme or cell, item) pairs: the accepted (theme, item)
        pairs, and the gold (cell, item) slots that no theme of their cell accepts.
        A gold item can also be another theme's accepted item, and is then counted
        on both sides, as the single tally's ``tp + fp + fn`` counts it."""
        return self.accepted + self.gold - self.gold_hits

    def jaccard(self) -> float | None:
        """Accepted hits over ``union``. Without tie groups, shared over union."""
        return ratio(self.accepted_hits, self.union())


def total(tallies: Iterable[Tally]) -> Tally:
    return sum(tallies, Tally())


def theme_tallies(cells: EventCells, predicted: Iterable[str]) -> dict[str, Tally]:
    """One event's theme cells: each present theme a hit or a miss, each other
    scored prediction a false positive. Excused and uncertain-only cells score
    nothing (FP20)."""
    predicted = frozenset(predicted)
    return {
        theme: Tally(tp=1)
        if theme in cells.present and theme in predicted
        else Tally(fn=1)
        if theme in cells.present
        else Tally(fp=1)
        for theme in sorted(cells.present | predicted)
        if cells.scored(theme)
    }


def per_theme(events: Iterable[Mapping[str, Tally]]) -> dict[str, Tally]:
    """Each theme's counts, summed over events."""
    out: dict[str, Tally] = {}
    for tallies in events:
        for theme, tally in tallies.items():
            out[theme] = out.get(theme, Tally()) + tally
    return out


def macro_f1(themes: Mapping[str, Tally]) -> float | None:
    """The mean F1 over themes with gold or a prediction; ``themes`` holds only
    those, so each one's F1 is defined."""
    values = [value for value in map(f1, themes.values()) if value is not None]
    return sum(values) / len(values) if values else None


def rare_themes(events: Iterable[EventCells], most: int = 2) -> frozenset[str]:
    """The themes present in at most ``most`` of a partition's events (D1)."""
    seen: dict[str, int] = {}
    for cells in events:
        for theme in cells.present:
            seen[theme] = seen.get(theme, 0) + 1
    return frozenset(theme for theme, n in seen.items() if n <= most)


def _ahead(cells: EventCells, cell: EvidenceCell, theme_id: str) -> list[str]:
    """The themes of ``cell`` that take ``theme_id``'s credit for an item of the
    cell's gold that they also accept, so each gold slot is credited once: none, for
    a scored theme; for an excused member, the cell's scored themes, and its other
    members with a lower ID, so that when only excused members accept an item, the
    lowest ID among them takes its credit."""
    if cells.scored(theme_id):
        return []
    return [
        other
        for other in sorted(cell.themes)
        if other != theme_id and (cells.scored(other) or other < theme_id)
    ]


def unit_tally(
    cells: EventCells, accepted_units: Mapping[str, frozenset[str]]
) -> EvidenceTally:
    """One event's evidence units (FP13, FP20). Gold side: each evidence cell's
    units, and those any of its themes' accepted evidence covers, so a tie group's
    evidence is covered whichever member carries it. Accepted side, one credit per
    gold slot: a scored theme's accepted units are all accepted, and those lying in
    some cell it belongs to are hits. An excused member's accepted unit counts, as
    accepted and a hit, only where it fills a slot of one of its cells that no
    theme ahead of it (``_ahead``) also accepts; its other units are not scored. A
    unit counts once per theme however many cells hold it. An uncertain-only theme
    belongs to no cell, so adds nothing."""
    gold_hits = gold = accepted_hits = accepted = 0
    for cell in cells.evidence:
        got = frozenset().union(*(accepted_units.get(t, ()) for t in cell.themes))
        gold_hits, gold = gold_hits + len(cell.units & got), gold + len(cell.units)
    for theme, got in sorted(accepted_units.items()):
        hits: set[str] = set()
        for cell in cells.evidence:
            if theme in cell.themes:
                ahead = (accepted_units.get(t, ()) for t in _ahead(cells, cell, theme))
                hits |= (got & cell.units).difference(*ahead)
        accepted_hits += len(hits)
        accepted += len(got) if cells.scored(theme) else len(hits)
    return EvidenceTally(accepted_hits, accepted, gold_hits, gold)


def char_counts(
    cells: EventCells, accepted_spans: Mapping[str, tuple[Span, ...]]
) -> EvidenceTally:
    """One event's evidence characters, counted as ``unit_tally`` counts units: each
    cell's gold characters and those its themes' accepted spans cover; a scored
    theme's accepted characters, and those within its cells as hits; an excused
    member's accepted characters within a cell's gold spans that no theme ahead of
    it (``_ahead``) also covers, as accepted and hits, each counted once. Character
    Jaccard is its ``jaccard``."""
    gold_hits = gold = accepted_hits = accepted = 0
    for cell in cells.evidence:
        got = [s for t in sorted(cell.themes) for s in accepted_spans.get(t, ())]
        both, _ = char_overlap(cell.spans, got)
        gold_hits, gold = gold_hits + both, gold + covered(cell.spans)
    for theme, got in sorted(accepted_spans.items()):
        hits: list[Span] = []
        for cell in cells.evidence:
            if theme in cell.themes:
                ahead = [
                    s
                    for t in _ahead(cells, cell, theme)
                    for s in accepted_spans.get(t, ())
                ]
                hits += difference(intersection(got, cell.spans), ahead)
        accepted_hits += covered(hits)
        accepted += covered(got) if cells.scored(theme) else covered(hits)
    return EvidenceTally(accepted_hits, accepted, gold_hits, gold)


def evidence_recall_counts(
    cells: EventCells, accepted_units: Mapping[str, frozenset[str]]
) -> tuple[int, int]:
    """Gold-evidence recall's counts (R12.8 (iii)): the gold-supporting units that
    any accepted assignment holds, and all gold-supporting units (D19-8)."""
    gold = frozenset().union(*cells.units.values())
    got = frozenset().union(*accepted_units.values())
    return len(gold & got), len(gold)


def hard_negative_counts(
    reading: GoldReading,
    index: UnitIndex,
    accepted_units: Mapping[str, frozenset[str]],
) -> dict[NegativeKind, tuple[int, int]]:
    """Per negative kind (R12.5): the hard negatives that name a theme, and those
    falsely accepted, by an accepted assignment to that theme whose evidence units
    overlap the negative's."""
    quotes = {q.quote_id: (q.start, q.end) for q in reading.quotes}
    out: dict[NegativeKind, tuple[int, int]] = {}
    for negative in reading.hard_negatives:
        if negative.theme_id is None:
            continue
        own = units_over(index, (quotes[q] for q in negative.quote_ids if q in quotes))
        hit = bool(own & accepted_units.get(negative.theme_id, frozenset()))
        named, accepted = out.get(negative.negative_kind, (0, 0))
        out[negative.negative_kind] = (named + 1, accepted + hit)
    return out


def release_tally(confirmed: bool, label: ReleaseLabel) -> Tally | None:
    """Release identification's cell: the system's confirmed release against the
    gold label; ``ambiguous`` is left out and counted (R13.1)."""
    if label is ReleaseLabel.AMBIGUOUS:
        return None
    gold = label is ReleaseLabel.RELEASE
    return Tally(
        tp=int(confirmed and gold),
        fp=int(confirmed and not gold),
        fn=int(gold and not confirmed),
    )


def gs5_shares(counts: Iterable[DraftCounts]) -> dict[str, float | None]:
    """GS5's shares over summed counts: edited and rejected over drafted items,
    added over signed items (D19-9)."""
    rows = list(counts)
    accepted = sum(c.accepted for c in rows)
    edited = sum(c.edited for c in rows)
    rejected = sum(c.rejected for c in rows)
    added = sum(c.added for c in rows)
    drafted = accepted + edited + rejected
    return {
        "edited": ratio(edited, drafted),
        "rejected": ratio(rejected, drafted),
        "added": ratio(added, accepted + edited + added),
    }
