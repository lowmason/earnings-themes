"""Gold and run quotes in pointer units, and their characters (the Stage 11 spec,
A3's alignment and FP13; ES12).

- **Units.** A span maps to every unit whose span shares at least one character
  with it. A run quote is a whole unit (ES12), so it maps to that unit; a gold quote
  may be part of a unit, or cross several.
- **Characters.** Spans are half-open ``[start, end)`` offsets into one document's
  canonical text. Character Jaccard is the characters two span sets share over the
  characters either covers.

Nothing here reads text, so nothing here can print it (GS13).
"""

from collections.abc import Iterable
from dataclasses import dataclass

from earnings_themes.anchoring import Bundle
from earnings_themes.extraction.units import units

type Span = tuple[int, int]


@dataclass(frozen=True)
class UnitIndex:
    """One document's units: each one's element ID, start and end, in document
    order."""

    doc_id: str
    spans: tuple[tuple[str, int, int], ...]


def unit_index(bundle: Bundle) -> UnitIndex:
    """The bundle's pointer units (ES12), by span."""
    return UnitIndex(
        bundle.document.doc_id,
        tuple((u.element_id, u.span.start, u.span.end) for u in units(bundle)),
    )


def units_over(index: UnitIndex, spans: Iterable[Span]) -> frozenset[str]:
    """The units sharing at least one character with any of ``spans``."""
    found: set[str] = set()
    for start, end in spans:
        found.update(e for e, s, t in index.spans if s < end and start < t)
    return frozenset(found)


def merged(spans: Iterable[Span]) -> tuple[Span, ...]:
    """The union of ``spans``, as sorted, disjoint spans."""
    out: list[list[int]] = []
    for start, end in sorted(spans):
        if out and start <= out[-1][1]:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return tuple((start, end) for start, end in out)


def covered(spans: Iterable[Span]) -> int:
    """How many characters ``spans`` cover, each counted once."""
    return sum(end - start for start, end in merged(spans))


def intersection(a: Iterable[Span], b: Iterable[Span]) -> tuple[Span, ...]:
    """The characters both ``a`` and ``b`` cover, as sorted, disjoint spans."""
    a, b = merged(a), merged(b)
    out: list[Span] = []
    i = j = 0
    while i < len(a) and j < len(b):
        start, end = max(a[i][0], b[j][0]), min(a[i][1], b[j][1])
        if start < end:
            out.append((start, end))
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return tuple(out)


def difference(a: Iterable[Span], b: Iterable[Span]) -> tuple[Span, ...]:
    """The characters ``a`` covers and ``b`` does not, as sorted, disjoint spans."""
    holes = merged(b)
    out: list[Span] = []
    for start, end in merged(a):
        for hole_start, hole_end in holes:
            if hole_end <= start or hole_start >= end:
                continue
            if start < hole_start:
                out.append((start, hole_start))
            start = hole_end
        if start < end:
            out.append((start, end))
    return tuple(out)


def char_overlap(a: Iterable[Span], b: Iterable[Span]) -> tuple[int, int]:
    """The characters ``a`` and ``b`` share, and the characters either covers."""
    a, b = tuple(a), tuple(b)
    union = covered((*a, *b))
    return covered(a) + covered(b) - union, union
