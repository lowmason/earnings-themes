"""Two parser implementations emit one browser-neutral element schema.

Stand-ins, not the real pair (browser-rendering spec, Stage 2 verification): a
standard-library ``html.parser`` reader plays the canonicalizing parser, and an lxml
reader plays a second extractor that maps its blocks onto the first reader's
``CanonicalDocument``, the sole coordinate system (B5). Stage 3 reruns this contract
with the ported walker and the DOM/layout extractor in their place.
"""

import json
from dataclasses import dataclass
from html.parser import HTMLParser

import lxml.html
from earnings_core import (
    CanonicalDocument,
    DocumentElement,
    ElementType,
    Rejection,
    RejectionReason,
    SpanLocator,
    TableCellContext,
    TextSpan,
    resolve_locator,
    validate_elements,
)

SOURCE = """<html><body>
<h1>Acme Reports Third Quarter Results</h1>
<p>Revenue rose 5% to $2.1 billion.</p>
<p>Results are preliminary.</p>
<ul><li>Margins expanded.</li><li>Results are preliminary.</li></ul>
<table>
<tr><th>Metric</th><th>Q3 2026</th></tr>
<tr><td>Net sales</td><td>$9.8</td></tr>
</table>
</body></html>"""

TYPES = {
    "h1": (ElementType.HEADING, 1),
    "p": (ElementType.PARAGRAPH, None),
    "li": (ElementType.LIST_ITEM, 1),
}
Row = tuple[tuple[str, bool], ...]


@dataclass(frozen=True)
class Block:
    """What a reader saw: a typed text block, or a table of (text, is_header) cells."""

    type: ElementType
    source_type: str
    text: str = ""
    level: int | None = None
    rows: tuple[Row, ...] = ()


class StdlibReader(HTMLParser):
    """Stand-in for the canonicalizing parser: standard-library parse events."""

    def __init__(self) -> None:
        super().__init__()
        self.blocks: list[Block] = []
        self._parts: list[str] | None = None
        self._rows: list[list[tuple[str, bool]]] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in TYPES or tag in {"th", "td"}:
            self._parts = []
        elif tag == "tr":
            self._rows.append([])

    def handle_data(self, data: str) -> None:
        if self._parts is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "table":
            rows = tuple(tuple(row) for row in self._rows)
            self.blocks.append(Block(ElementType.TABLE, "html.parser:table", rows=rows))
            self._rows = []
        elif self._parts is not None and (tag in TYPES or tag in {"th", "td"}):
            text = " ".join("".join(self._parts).split())
            self._parts = None
            if tag in TYPES:
                element_type, level = TYPES[tag]
                self.blocks.append(
                    Block(element_type, f"html.parser:{tag}", text, level)
                )
            else:
                self._rows[-1].append((text, tag == "th"))


def stdlib_blocks(source: str) -> list[Block]:
    reader = StdlibReader()
    reader.feed(source)
    reader.close()
    return reader.blocks


def lxml_blocks(source: str) -> list[Block]:
    """Stand-in for a second extractor: an lxml tree walked in document order."""
    blocks: list[Block] = []
    for node in lxml.html.fromstring(source).iter("h1", "p", "li", "table"):
        if node.tag == "table":
            rows = tuple(
                tuple(
                    (" ".join(cell.text_content().split()), cell.tag == "th")
                    for cell in row.iter("th", "td")
                )
                for row in node.iter("tr")
            )
            blocks.append(Block(ElementType.TABLE, "lxml:table", rows=rows))
        else:
            element_type, level = TYPES[node.tag]
            text = " ".join(node.text_content().split())
            blocks.append(Block(element_type, f"lxml:{node.tag}", text, level))
    return blocks


def table_elements(
    document: CanonicalDocument, block: Block, spans: list[list[TextSpan]]
) -> list[DocumentElement]:
    """A table element over its cells, then each cell with its column's headers."""
    table = DocumentElement.create(
        document,
        ElementType.TABLE,
        TextSpan(start=spans[0][0].start, end=spans[-1][-1].end),
        source_type=block.source_type,
    )
    cells: list[DocumentElement] = []
    header_ids: dict[int, str] = {}
    for row_index, (row, row_spans) in enumerate(zip(block.rows, spans, strict=True)):
        for column, ((_, is_header), span) in enumerate(
            zip(row, row_spans, strict=True)
        ):
            headers = () if is_header else (header_ids[column],)
            cell = DocumentElement.create(
                document,
                ElementType.TABLE_CELL,
                span,
                parent_id=table.element_id,
                table_cell=TableCellContext(
                    row=row_index,
                    column=column,
                    is_header=is_header,
                    header_cell_ids=headers,
                ),
                source_type=block.source_type.replace(
                    "table", "th" if is_header else "td"
                ),
            )
            if is_header:
                header_ids[column] = cell.element_id
            cells.append(cell)
    return [table, *cells]


def canonicalize(
    blocks: list[Block],
) -> tuple[CanonicalDocument, list[DocumentElement]]:
    """The canonicalizing reader: blocks joined by blank lines, cells by tabs, rows by
    newlines, with every element's span fixed as the text is assembled."""
    pieces: list[str] = []
    starts: list[int] = []
    offset = 0
    for block in blocks:
        text = block.text
        if block.type is ElementType.TABLE:
            text = "\n".join("\t".join(cell for cell, _ in row) for row in block.rows)
        starts.append(offset)
        pieces.append(text)
        offset += len(text) + 2
    document = CanonicalDocument.create(
        source_document_id="contract-release",
        canonicalization_version="stand-in-stdlib-1",
        canonical_text="\n\n".join(pieces),
    )
    elements: list[DocumentElement] = []
    for block, start in zip(blocks, starts, strict=True):
        if block.type is ElementType.TABLE:
            spans: list[list[TextSpan]] = []
            position = start
            for row in block.rows:
                spans.append([])
                for cell, _ in row:
                    spans[-1].append(TextSpan(start=position, end=position + len(cell)))
                    position += len(cell) + 1
            elements.extend(table_elements(document, block, spans))
        else:
            span = TextSpan(start=start, end=start + len(block.text))
            elements.append(
                DocumentElement.create(
                    document,
                    block.type,
                    span,
                    level=block.level,
                    source_type=block.source_type,
                )
            )
    return document, elements


def map_onto(
    document: CanonicalDocument, blocks: list[Block]
) -> tuple[list[DocumentElement], list[Rejection]]:
    """The second reader: each text located exactly in the given document, or refused."""
    elements: list[DocumentElement] = []
    failures: list[Rejection] = []
    for block in blocks:
        texts = [cell for row in block.rows for cell, _ in row] or [block.text]
        located = [resolve_locator(document, SpanLocator(exact=text)) for text in texts]
        refused = [outcome for outcome in located if isinstance(outcome, Rejection)]
        if refused:
            failures.extend(refused)
            continue
        if block.type is ElementType.TABLE:
            cells = iter(located)
            spans = [[next(cells) for _ in row] for row in block.rows]
            elements.extend(table_elements(document, block, spans))
        else:
            elements.append(
                DocumentElement.create(
                    document,
                    block.type,
                    located[0],
                    level=block.level,
                    source_type=block.source_type,
                )
            )
    return elements, failures


def without_provenance(element: DocumentElement) -> dict:
    return element.model_dump(exclude={"source_type"})


def test_the_two_readers_see_the_same_blocks() -> None:
    def shape(blocks: list[Block]) -> list[tuple]:
        return [(b.type, b.text, b.level, b.rows) for b in blocks]

    assert shape(stdlib_blocks(SOURCE)) == shape(lxml_blocks(SOURCE))


def test_the_canonicalizing_reader_emits_a_valid_element_set() -> None:
    document, elements = canonicalize(stdlib_blocks(SOURCE))
    assert validate_elements(document, elements) == ()
    assert {element.source_type.partition(":")[0] for element in elements} == {
        "html.parser"
    }


def test_the_mapping_reader_emits_valid_elements_over_the_same_document() -> None:
    document, _ = canonicalize(stdlib_blocks(SOURCE))
    mapped, _ = map_onto(document, lxml_blocks(SOURCE))
    assert validate_elements(document, mapped) == ()
    assert {element.source_type.partition(":")[0] for element in mapped} == {"lxml"}


def test_elements_both_readers_place_agree_in_everything_but_provenance() -> None:
    document, canonical = canonicalize(stdlib_blocks(SOURCE))
    mapped, _ = map_onto(document, lxml_blocks(SOURCE))
    mapped_ids = {element.element_id for element in mapped}
    assert [without_provenance(e) for e in mapped] == [
        without_provenance(e) for e in canonical if e.element_id in mapped_ids
    ]
    assert len(mapped) == len(canonical) - 2


def test_repeated_text_fails_to_map_explicitly_never_to_the_first_match() -> None:
    document, canonical = canonicalize(stdlib_blocks(SOURCE))
    mapped, failures = map_onto(document, lxml_blocks(SOURCE))
    assert [failure.reason for failure in failures] == [
        RejectionReason.AMBIGUOUS_OCCURRENCE,
        RejectionReason.AMBIGUOUS_OCCURRENCE,
    ]
    mapped_ids = {element.element_id for element in mapped}
    unmapped = [e for e in canonical if e.element_id not in mapped_ids]
    assert [element.type for element in unmapped] == [
        ElementType.PARAGRAPH,
        ElementType.LIST_ITEM,
    ]
    assert {e.span.slice_of(document.canonical_text) for e in unmapped} == {
        "Results are preliminary."
    }


def test_both_readers_emit_records_of_the_one_schema() -> None:
    document, canonical = canonicalize(stdlib_blocks(SOURCE))
    mapped, _ = map_onto(document, lxml_blocks(SOURCE))
    fields = set(DocumentElement.model_fields)
    for element in [*canonical, *mapped]:
        payload = element.model_dump_json()
        assert set(json.loads(payload)) == fields
        assert DocumentElement.model_validate_json(payload) == element
