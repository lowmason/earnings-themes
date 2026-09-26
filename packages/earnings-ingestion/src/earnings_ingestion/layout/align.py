"""Mapping policy ``anchored-1``: layout-1's units onto walker-1's canonical text (SC13).

- **Space.** The canonical text with every whitespace run collapsed to one space. Each
  collapsed character keeps the canonical offset it came from, so a match maps back
  to exactly one canonical span: the map is deterministic and reversible.
- **Occurrences.** A unit's N1 text occurs where it matches exactly, starting and
  ending at a token boundary: the text's edge or a space. Overlapping occurrences
  count.
- **Anchors.** A unit with exactly one occurrence maps there.
- **Order.** Mapped units are kept only when they are consistent: a unit whose span
  overlaps another mapped unit's is dropped with it, and a unit is kept only when it
  belongs to every longest sequence of mapped units whose spans follow document order.
  One unit far out of place therefore costs only itself, and neither unit of a
  swapped pair is kept.
- **Neighbours.** Between two kept units, a text whose units there number exactly as
  many as its occurrences there maps in order: the first such unit to the first
  occurrence, and so on. With one unit and one occurrence, that is the neighbours
  deciding. Each round's new units pass the order check with the kept ones, and
  rounds repeat until none maps.
- **Failures.** No occurrence is ``locator_not_found``. Several occurrences that the
  neighbours never settle, or a place the order check refuses, is
  ``ambiguous_occurrence``. Nothing is placed at a first match or by a score.
"""

import bisect
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from earnings_core import RejectionReason, TextSpan

MAPPING_POLICY = "anchored-1"


@dataclass(frozen=True)
class CollapsedText:
    """The canonical text with whitespace runs collapsed, and each character's origin."""

    text: str
    origins: tuple[int, ...]

    @classmethod
    def of(cls, canonical_text: str) -> "CollapsedText":
        chars: list[str] = []
        origins: list[int] = []
        previous_space = True
        for offset, char in enumerate(canonical_text):
            if char.isspace():
                if not previous_space:
                    chars.append(" ")
                    origins.append(offset)
                previous_space = True
                continue
            chars.append(char)
            origins.append(offset)
            previous_space = False
        if chars and chars[-1] == " ":
            chars.pop()
            origins.pop()
        return cls("".join(chars), tuple(origins))

    def span(self, start: int, end: int) -> TextSpan:
        """The canonical span of collapsed characters ``[start, end)``."""
        return TextSpan(start=self.origins[start], end=self.origins[end - 1] + 1)

    def occurrences(self, unit: str) -> list[int]:
        """Every token-bounded start of ``unit``, overlapping ones included."""
        found: list[int] = []
        if not unit:
            return found
        width = len(unit)
        position = self.text.find(unit)
        while position != -1:
            before = position == 0 or self.text[position - 1] == " "
            end = position + width
            after = end == len(self.text) or self.text[end] == " "
            if before and after:
                found.append(position)
            position = self.text.find(unit, position + 1)
        return found


@dataclass(frozen=True)
class Placed:
    """Where one unit maps: a collapsed start, or the reason it maps nowhere."""

    start: int | None
    reason: RejectionReason | None
    detail: str


def align(collapsed: CollapsedText, units: Sequence[str]) -> list[Placed]:
    """Each unit's placement under ``anchored-1``, in the units' order."""
    found = [collapsed.occurrences(unit) for unit in units]
    widths = [len(unit) for unit in units]
    kept: dict[int, int] = {}
    refused: set[int] = set()
    proposed = {index: hits[0] for index, hits in enumerate(found) if len(hits) == 1}
    while proposed:
        merged = {**kept, **proposed}
        consistent = _consistent(merged, widths)
        refused |= set(proposed) - consistent
        kept = {index: merged[index] for index in consistent}
        proposed = _by_neighbours(units, found, kept, refused, len(collapsed.text))
    out: list[Placed] = []
    for index, hits in enumerate(found):
        if index in kept:
            out.append(Placed(kept[index], None, ""))
        elif not hits:
            out.append(Placed(None, RejectionReason.LOCATOR_NOT_FOUND, "no occurrence"))
        elif index in refused:
            out.append(
                Placed(
                    None,
                    RejectionReason.AMBIGUOUS_OCCURRENCE,
                    "its place is out of order with, or overlaps, other mapped units",
                )
            )
        else:
            out.append(
                Placed(
                    None,
                    RejectionReason.AMBIGUOUS_OCCURRENCE,
                    f"{len(hits)} occurrences, and its neighbours do not settle which",
                )
            )
    return out


def _by_neighbours(
    units: Sequence[str],
    found: Sequence[list[int]],
    kept: dict[int, int],
    refused: set[int],
    length: int,
) -> dict[int, int]:
    """New places from the windows between kept units: equal counts map in order."""
    proposed: dict[int, int] = {}
    index = 0
    while index < len(units):
        if index in kept:
            index += 1
            continue
        first = index
        while index < len(units) and index not in kept:
            index += 1
        low = next(
            (kept[i] + len(units[i]) for i in range(first - 1, -1, -1) if i in kept), 0
        )
        high = kept[index] if index < len(units) else length
        members: dict[str, list[int]] = defaultdict(list)
        for unit in range(first, index):
            if unit not in refused and found[unit]:
                members[units[unit]].append(unit)
        for text, group in members.items():
            inside = [
                start
                for start in found[group[0]]
                if low <= start and start + len(text) <= high
            ]
            if inside and len(inside) == len(group):
                proposed.update(zip(group, inside, strict=True))
    return proposed


def _consistent(places: dict[int, int], widths: Sequence[int]) -> set[int]:
    """The units that overlap no other and lie on every longest in-order sequence."""
    overlapping: set[int] = set()
    reach, holder = 0, -1
    for unit in sorted(places, key=lambda unit: places[unit]):
        if places[unit] < reach:
            overlapping.update((unit, holder))
        if places[unit] + widths[unit] > reach:
            reach, holder = places[unit] + widths[unit], unit
    units = sorted(unit for unit in places if unit not in overlapping)
    starts = [places[unit] for unit in units]
    ending = _longest_ending(starts)
    starting = _longest_ending([-start for start in reversed(starts)])[::-1]
    longest = max(ending, default=0)
    on_some = [
        position
        for position in range(len(units))
        if ending[position] + starting[position] - 1 == longest
    ]
    per_level: dict[int, list[int]] = defaultdict(list)
    for position in on_some:
        per_level[ending[position]].append(position)
    return {units[members[0]] for members in per_level.values() if len(members) == 1}


def _longest_ending(values: Sequence[int]) -> list[int]:
    """For each position, the length of the longest strictly increasing run of values
    that ends there, taken in order (patience sorting)."""
    tails: list[int] = []
    lengths: list[int] = []
    for value in values:
        position = bisect.bisect_left(tails, value)
        if position == len(tails):
            tails.append(value)
        else:
            tails[position] = value
        lengths.append(position + 1)
    return lengths
