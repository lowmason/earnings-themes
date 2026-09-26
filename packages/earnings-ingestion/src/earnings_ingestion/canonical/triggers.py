"""The fallback's activation triggers, read from walker-1's recorded output.

The Stage 3 spec's pre-registered comparison names two (§Pre-registered comparison,
"Fallback activation"). A document switches to layout-1's element stream when either
fires:

1. ``no_heading``: walker-1 emitted no ``heading`` element at all;
2. ``prose_row``: a row of a data table whose only non-empty cell holds more than 12
   words (``MAX_HEADING_WORDS``).
"""

from collections import defaultdict
from collections.abc import Sequence

from earnings_core import CanonicalDocument, DocumentElement, ElementType

from earnings_ingestion.canonical.walker import MAX_HEADING_WORDS

NO_HEADING = "no_heading"
PROSE_ROW = "prose_row"


def fired(
    document: CanonicalDocument, elements: Sequence[DocumentElement]
) -> tuple[str, ...]:
    """The triggers walker-1's elements fire, in the spec's order."""
    found: list[str] = []
    if not any(element.type is ElementType.HEADING for element in elements):
        found.append(NO_HEADING)
    rows: dict[tuple[str, int], list[DocumentElement]] = defaultdict(list)
    for element in elements:
        if element.type is ElementType.TABLE_CELL and element.table_cell is not None:
            rows[element.parent_id or "", element.table_cell.row].append(element)
    if any(
        len(cells) == 1
        and len(cells[0].span.slice_of(document.canonical_text).split())
        > MAX_HEADING_WORDS
        for cells in rows.values()
    ):
        found.append(PROSE_ROW)
    return tuple(found)
