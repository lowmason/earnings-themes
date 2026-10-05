"""Windows: whole blocks packed in document order (the Stage 7 spec, §Windows; ES13,
ES14).

- **Packing.** Blocks are packed greedily in document order while the window's unit
  text stays within the budget. A block is never split, and one longer than the
  budget gets a window of its own. A budget of ``None`` packs the whole document
  into one window, which is Stage 14's whole-document arm.
- **Identity and context.** A window's ID is ``w-<start>-<end>``, from its first
  unit's start and its last unit's end. It carries the nearest heading unit before
  its first block, unlabeled and not quotable, unless its first unit is a heading.
- **Labels.** ``U1`` to ``Un`` in document order within the window. The model sees
  only labels, and code maps each to its element ID (ES14).
- **The guarantee.** Every unit lies in exactly one window. The plan reads element
  types, spans, and parents, never a unit's text or a score, so no top-k path exists
  (R10.2). The only text read is ``narrative_home``'s whitespace test of a container
  (ES9).
"""

from typing import Annotated, Self

from earnings_core import DocumentElement, ElementType
from pydantic import Field, NonNegativeInt, model_validator

from earnings_themes.anchoring import Bundle
from earnings_themes.extraction.units import block_of, units
from earnings_themes.records import NonBlank, Part

Block = Annotated[tuple[NonBlank, ...], Field(min_length=1)]


class Window(Part):
    """One window's plan: its units, grouped by block, and its context heading."""

    doc_id: NonBlank
    start: NonNegativeInt
    end: NonNegativeInt
    blocks: Annotated[tuple[Block, ...], Field(min_length=1)]
    context_id: NonBlank | None = None

    @model_validator(mode="after")
    def _start_before_end(self) -> Self:
        if self.start >= self.end:
            raise ValueError(f"window [{self.start}, {self.end}) is empty or reversed")
        return self

    @property
    def window_id(self) -> str:
        return f"w-{self.start}-{self.end}"

    @property
    def unit_ids(self) -> tuple[str, ...]:
        """The window's units in label order: ``U1`` names the first."""
        return tuple(unit_id for block in self.blocks for unit_id in block)

    @property
    def labels(self) -> dict[str, str]:
        """Each label and the element ID it names (ES14)."""
        return {f"U{n}": unit_id for n, unit_id in enumerate(self.unit_ids, start=1)}


def plan_windows(bundle: Bundle, budget: int | None) -> tuple[Window, ...]:
    """The bundle's windows in document order, under ``budget`` characters of unit
    text, or one window when ``budget`` is ``None`` (ES13)."""
    found = units(bundle)
    if not found:
        return ()
    by_id = {element.element_id: element for element in bundle.elements}
    blocks: dict[str, list[DocumentElement]] = {}
    for unit in found:
        blocks.setdefault(block_of(unit, by_id), []).append(unit)
    packed: list[list[list[DocumentElement]]] = []
    size = 0
    for block in blocks.values():
        width = sum(unit.span.length for unit in block)
        if packed and budget is not None and size + width > budget:
            packed.append([])
            size = 0
        if not packed:
            packed.append([])
        packed[-1].append(block)
        size += width
    headings = [unit for unit in found if unit.type is ElementType.HEADING]
    windows = []
    for window_blocks in packed:
        first, last = window_blocks[0][0], window_blocks[-1][-1]
        before = [h for h in headings if h.span.end <= first.span.start]
        context = (
            before[-1].element_id
            if before and first.type is not ElementType.HEADING
            else None
        )
        windows.append(
            Window(
                doc_id=bundle.document.doc_id,
                start=first.span.start,
                end=last.span.end,
                blocks=tuple(
                    tuple(unit.element_id for unit in block) for block in window_blocks
                ),
                context_id=context,
            )
        )
    return tuple(windows)
