"""Gold presence and evidence per event and theme, under Stage 11's conventions
(the Stage 11 spec, §Metrics and FP20; P9-4; R12.6).

- **Present.** A theme is present in an event when an assignment pairs it with a
  claim under ``supports``. ``unmatched`` is never a theme (P9-4).
- **Tie groups.** Rows sharing a ``tie_group`` are alternatives for one claim
  (R12.6), one either-of cell. The group resolves to a supporting member the run
  predicted, else to one already present, else to its lowest theme ID. Its other
  members are excused, so predicting one is not a false positive (D19-6).
- **Uncertain only.** A theme whose every gold row is ``uncertain`` is left out of
  scoring and counted (FP20).
- **Evidence.** A present theme's gold spans are the quotes of the claims that
  support it, after the tie groups resolve. A reference to a quote or a claim that
  the reading does not hold is counted as ``dangling`` and adds nothing, so a kept
  draft is compared as drafted (P17-5(2), D19-7).
- **Roll-up.** ``theme_map`` maps every theme before anything else; ``level_one``
  maps each theme to its root, on both sides (D19-3).
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Protocol

from earnings_themes.codebook import UNMATCHED, Codebook
from earnings_themes.evaluation.align import Span, UnitIndex, units_over
from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
from earnings_themes.gold import (
    GoldAssignment,
    GoldClaim,
    GoldQuote,
    HardNegative,
    Support,
)


class GoldReading(Protocol):
    """What scoring reads from signed gold or an anchored reading (A6(3))."""

    @property
    def quotes(self) -> tuple[GoldQuote, ...]: ...

    @property
    def claims(self) -> tuple[GoldClaim, ...]: ...

    @property
    def assignments(self) -> tuple[GoldAssignment, ...]: ...

    @property
    def hard_negatives(self) -> tuple[HardNegative, ...]: ...


@dataclass(frozen=True)
class EventCells:
    """One event's gold cells: the present themes, each with its gold units and
    spans; the excused and uncertain-only themes; and the dangling references."""

    present: frozenset[str]
    excused: frozenset[str]
    uncertain: frozenset[str]
    units: Mapping[str, frozenset[str]]
    spans: Mapping[str, tuple[Span, ...]]
    dangling: int

    def scored(self, theme_id: str) -> bool:
        """Whether a prediction of ``theme_id`` is scored at all."""
        return theme_id in self.present or (
            theme_id not in self.excused and theme_id not in self.uncertain
        )


def level_one(codebook: Codebook) -> dict[str, str]:
    """Each theme's level-one ancestor: its root, or itself (D19-3)."""
    parents = {theme.theme_id: theme.parent_id for theme in codebook.themes}
    roots: dict[str, str] = {}
    for theme_id in parents:
        current, seen = theme_id, {theme_id}
        while (parent := parents.get(current)) is not None:
            if parent in seen:
                raise EvaluationError(EvaluationProblem.PARENT_CYCLE, theme_id)
            current = parent
            seen.add(current)
        roots[theme_id] = current
    return roots


def event_cells(
    reading: GoldReading,
    index: UnitIndex,
    predicted: Iterable[str] = (),
    theme_map: Mapping[str, str] | None = None,
) -> EventCells:
    """``reading``'s cells over ``index``, with its tie groups resolved against
    ``predicted``, whose themes ``theme_map`` has already mapped."""

    def mapped(theme_id: str) -> str:
        return theme_id if theme_map is None else theme_map.get(theme_id, theme_id)

    predicted = frozenset(predicted)
    quotes = {q.quote_id: (q.start, q.end) for q in reading.quotes}
    claims = {c.claim_id: c.quote_ids for c in reading.claims}
    dangling = sum(q not in quotes for ids in claims.values() for q in ids)
    rows = [
        (a.claim_id, mapped(a.theme_id), a.support, a.tie_group)
        for a in reading.assignments
        if a.theme_id != UNMATCHED
    ]
    supporting: dict[str, set[str]] = {}
    groups: dict[str, tuple[str, set[str]]] = {}
    for claim_id, theme_id, support, group in rows:
        if support is not Support.SUPPORTS:
            continue
        if group is None:
            supporting.setdefault(theme_id, set()).add(claim_id)
        else:
            groups.setdefault(group, (claim_id, set()))[1].add(theme_id)
    present_untied = set(supporting)
    excused: set[str] = set()
    for group in sorted(groups):
        claim_id, members = groups[group]
        candidates = (members & predicted) or (members & present_untied) or members
        chosen = min(candidates)
        supporting.setdefault(chosen, set()).add(claim_id)
        excused |= members - {chosen}
    present = frozenset(supporting)
    decided = {
        theme for _, theme, support, _ in rows if support is not Support.UNCERTAIN
    }
    uncertain = {theme for _, theme, _, _ in rows} - decided - present - excused
    spans: dict[str, tuple[Span, ...]] = {}
    for theme_id, claim_ids in supporting.items():
        dangling += sum(c not in claims for c in claim_ids)
        found = {quotes[q] for c in claim_ids for q in claims.get(c, ()) if q in quotes}
        spans[theme_id] = tuple(sorted(found))
    return EventCells(
        present=present,
        excused=frozenset(excused - present),
        uncertain=frozenset(uncertain),
        units={t: units_over(index, s) for t, s in spans.items()},
        spans=spans,
        dangling=dangling,
    )
