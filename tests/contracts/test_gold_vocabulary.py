"""The element contract expresses every type and level in the Stage 1 gold.

Roadmap Stage 2 consumes V2's "Element types and nesting observed in the gold"
(docs/verification/V2-parser-fidelity.md); this reads the eight committed gold files.
"""

from pathlib import Path

import tomllib
from earnings_core import (
    LEVELED_TYPES,
    CanonicalDocument,
    DocumentElement,
    ElementType,
    TextSpan,
)

RELEASES = Path(__file__).resolve().parents[1] / "fixtures" / "releases"


def gold_blocks() -> list[tuple[str, dict]]:
    blocks: list[tuple[str, dict]] = []
    for path in sorted(RELEASES.glob("*/gold.toml")):
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        blocks.extend((path.parent.name, block) for block in data["blocks"])
    return blocks


def test_all_eight_gold_files_are_read() -> None:
    blocks = gold_blocks()
    assert len({fixture for fixture, _ in blocks}) == 8
    assert len(blocks) == 574


def test_every_gold_block_type_is_an_element_type() -> None:
    gold_types = {block["type"] for _, block in gold_blocks()}
    assert gold_types == {
        "footnote",
        "heading",
        "list_item",
        "page_artifact",
        "paragraph",
        "table",
    }
    assert gold_types <= {element_type.value for element_type in ElementType}


def test_every_gold_type_and_level_is_a_valid_element() -> None:
    document = CanonicalDocument.create(
        source_document_id="gold-vocabulary",
        canonicalization_version="test-1",
        canonical_text="x",
    )
    seen = {
        (ElementType(block["type"]), block.get("level")) for _, block in gold_blocks()
    }
    for element_type, level in seen:
        DocumentElement.create(
            document, element_type, TextSpan(start=0, end=1), level=level
        )
    assert seen == {
        (ElementType.HEADING, 1),
        (ElementType.HEADING, 2),
        (ElementType.HEADING, 3),
        (ElementType.HEADING, None),
        (ElementType.LIST_ITEM, 1),
        (ElementType.PARAGRAPH, None),
        (ElementType.FOOTNOTE, None),
        (ElementType.PAGE_ARTIFACT, None),
        (ElementType.TABLE, None),
    }


def test_gold_levels_sit_only_on_leveled_types() -> None:
    for fixture, block in gold_blocks():
        if "level" in block:
            assert ElementType(block["type"]) in LEVELED_TYPES, fixture
