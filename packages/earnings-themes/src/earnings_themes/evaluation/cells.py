"""Gold presence and evidence per event and theme, under Stage 11's conventions
(the Stage 11 spec, §Metrics and FP20; P9-4; R12.6).

- **Present.** A theme is present in an event when an assignment pairs it with a
  claim under ``supports``. ``unmatched`` is never a theme (P9-4).
- **Tie groups.** Rows sharing a ``tie_group`` are alternatives for one claim
  (R12.6), one either-of cell. The group resolves to a supporting member the run
  predicted, else to one already present, else to its lowest theme ID. Its other
  members are excused, so predicting one is not a false positive (D19-6).
- **Evidence cells.** Unit and character scoring keep each tie group whole: its
  evidence is one cell that any member's predicted evidence may cover, beside each
  present theme's own untied evidence (FP20). The resolution above decides only the
  theme cells.
- **Uncertain only.** A theme whose every gold row is ``uncertain`` is left out of
  scoring and counted (FP20).
- **Evidence.** A present theme's gold spans are the quotes of the claims that
  support it, after the tie groups resolve. A claim's reference to a quote, or any
  assignment's reference to a claim, that the reading does not hold is counted as
  ``dangling``, one per reference, and adds nothing, so a kept draft is compared as
  drafted (P17-5(2), D19-7).
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
class EvidenceCell:
    """One cell of gold evidence, as unit and character scoring read it: a present
    theme's own (untied) supporting evidence, or one tie group's, with the themes
    whose predicted evidence may cover it."""

    themes: frozenset[str]
    units: frozenset[str]
    spans: tuple[Span, ...]


@dataclass(frozen=True)
class EventCells:
    """One event's gold cells: the present themes, each with its gold units and
    spans; the excused and uncertain-only themes; the evidence cells; and the
    dangling references."""

    present: frozenset[str]
    excused: frozenset[str]
    uncertain: frozenset[str]
    units: Mapping[str, frozenset[str]]
    spans: Mapping[str, tuple[Span, ...]]
    evidence: tuple[EvidenceCell, ...]
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
    dangling = sum(q not in quotes for ids in claims.values() for q in ids) + sum(
        a.claim_id not in claims for a in reading.assignments
    )
    rows = [
        (a.claim_id, mapped(a.theme_id), a.support, a.tie_group)
        for a in reading.assignments
        if a.theme_id != UNMATCHED
    ]
    untied: dict[str, set[str]] = {}
    groups: dict[str, tuple[str, set[str]]] = {}
    for claim_id, theme_id, support, group in rows:
        if support is not Support.SUPPORTS:
            continue
        if group is None:
            untied.setdefault(theme_id, set()).add(claim_id)
        else:
            groups.setdefault(group, (claim_id, set()))[1].add(theme_id)
    supporting = {theme_id: set(claim_ids) for theme_id, claim_ids in untied.items()}
    excused: set[str] = set()
    for group in sorted(groups):
        claim_id, members = groups[group]
        candidates = (members & predicted) or (members & set(untied)) or members
        chosen = min(candidates)
        supporting.setdefault(chosen, set()).add(claim_id)
        excused |= members - {chosen}
    present = frozenset(supporting)
    decided = {
        theme for _, theme, support, _ in rows if support is not Support.UNCERTAIN
    }
    uncertain = {theme for _, theme, _, _ in rows} - decided - present - excused

    def found(claim_ids: Iterable[str]) -> tuple[Span, ...]:
        return tuple(
            sorted(
                {quotes[q] for c in claim_ids for q in claims.get(c, ()) if q in quotes}
            )
        )

    spans = {theme_id: found(claim_ids) for theme_id, claim_ids in supporting.items()}
    cells = [(frozenset({t}), found(c)) for t, c in sorted(untied.items())]
    cells += [(frozenset(m), found((c,))) for _, (c, m) in sorted(groups.items())]
    return EventCells(
        present=present,
        excused=frozenset(excused - present),
        uncertain=frozenset(uncertain),
        units={t: units_over(index, s) for t, s in spans.items()},
        spans=spans,
        evidence=tuple(
            EvidenceCell(themes, units_over(index, s), s) for themes, s in cells
        ),
        dangling=dangling,
    )
