"""Adapter logic with stand-in objects; the real libraries run only in each script's own env."""

from enum import Enum, auto
from types import SimpleNamespace

import adapter_edgartools
import adapter_secparser
import control
import pytest
from pf_dump import Cell, Element, Row, validate_elements


class NodeType(Enum):
    DOCUMENT = auto()
    HEADING = auto()
    PARAGRAPH = auto()
    TABLE = auto()
    LIST = auto()
    LIST_ITEM = auto()
    TEXT = auto()
    CONTAINER = auto()


class FakeNode:
    def __init__(self, kind, text="", children=(), **attrs):
        self.type = NodeType[kind]
        self._text = text
        self.children = list(children)
        self.__dict__.update(attrs)

    def text(self):
        return self._text


def cell(text, colspan=1):
    return SimpleNamespace(text=lambda: text, colspan=colspan, rowspan=1)


def test_edgartools_flatten_keeps_order_parents_and_types():
    table = FakeNode(
        "TABLE",
        headers=[[cell(""), cell("Three Months Ended", 2)]],
        rows=[
            SimpleNamespace(
                is_header=False, cells=[cell("Net sales"), cell("4,321"), cell("3,210")]
            )
        ],
        footer=[],
        caption=None,
    )
    footnote = FakeNode(
        "PARAGRAPH", "Excludes items", semantic_type=SimpleNamespace(name="FOOTNOTE")
    )
    root = FakeNode(
        "DOCUMENT",
        children=[
            FakeNode("HEADING", "Results", level=1),
            FakeNode(
                "LIST",
                children=[
                    FakeNode("LIST_ITEM", "First"),
                    FakeNode("LIST_ITEM", "Second"),
                ],
            ),
            table,
            footnote,
            FakeNode("TEXT", "loose text"),
        ],
    )
    elements = adapter_edgartools.flatten(root)
    validate_elements(elements)
    assert [(e.type, e.text, e.parent) for e in elements] == [
        ("other", "", None),
        ("heading", "Results", 0),
        ("other", "", 0),
        ("list_item", "First", 2),
        ("list_item", "Second", 2),
        ("table", " Three Months Ended\nNet sales 4,321 3,210", 0),
        ("footnote", "Excludes items", 0),
        ("other", "loose text", 0),
    ]
    assert elements[1].level == 1
    assert elements[5].rows[0] == Row(
        True, (Cell(""), Cell("Three Months Ended", 2, 1))
    )


def test_edgartools_mapping_covers_the_5_58_0_node_types():
    members = {
        "DOCUMENT",
        "SECTION",
        "HEADING",
        "PARAGRAPH",
        "TABLE",
        "LIST",
        "LIST_ITEM",
        "LINK",
        "IMAGE",
        "XBRL_FACT",
        "TEXT",
        "CONTAINER",
    }
    assert members == adapter_edgartools.CONTAINER_NODE_TYPES | set(
        adapter_edgartools.LEAF_NODE_TYPES
    )


def test_secparser_types_follow_the_most_specific_class():
    class AbstractSemanticElement:
        text = "x"

    class TableElement(AbstractSemanticElement):
        pass

    class TableOfContentsElement(TableElement):
        pass

    class TitleElement(AbstractSemanticElement):
        level = 2

    class Mystery:
        text = "y"

    converted = adapter_secparser.convert(
        [TableOfContentsElement(), TitleElement(), AbstractSemanticElement()]
    )
    assert [(e.type, e.level, e.source_type) for e in converted] == [
        ("table", None, "TableOfContentsElement"),
        ("heading", 2, "TitleElement"),
        ("other", None, "AbstractSemanticElement"),
    ]
    with pytest.raises(TypeError):
        adapter_secparser.convert([Mystery()])


def test_control_emits_one_paragraph_per_line():
    html = "<html><head><title>T</title></head><body><p>First line</p><table><tr><td>A</td><td>B</td></tr></table></body></html>"
    assert control.parse(html) == [
        Element("paragraph", "T", None, None, "line"),
        Element("paragraph", "First line", None, None, "line"),
        Element("paragraph", "A", None, None, "line"),
        Element("paragraph", "B", None, None, "line"),
    ]


def fake_table():
    return FakeNode(
        "TABLE",
        "rich-rendered text",
        headers=[[cell(""), cell("2025")]],
        rows=[
            SimpleNamespace(is_header=False, cells=[cell("Net sales"), cell("4,321")])
        ],
        footer=[],
        caption=None,
    )


def item(text, children):
    """A list item whose text() is what ListItemNode.text() flattens its children to."""
    return FakeNode("LIST_ITEM", text, children=children)


def test_edgartools_nested_list_keeps_its_items_in_order():
    inner = FakeNode("LIST", children=[item("Inner", [FakeNode("TEXT", "Inner")])])
    outer = item(
        "Lead  • Inner  Trail words",
        [FakeNode("TEXT", "Lead "), inner, FakeNode("TEXT", " Trail words")],
    )
    last = item("Costs fell", [FakeNode("TEXT", "Costs fell")])
    root = FakeNode("DOCUMENT", children=[FakeNode("LIST", children=[outer, last])])
    elements = adapter_edgartools.flatten(root)
    validate_elements(elements)
    assert [(e.type, e.text, e.parent) for e in elements] == [
        ("other", "", None),
        ("other", "", 0),
        ("list_item", "Lead ", 1),
        ("other", "", 2),
        ("list_item", "Inner", 3),
        ("list_item", " Trail words", 1),
        ("list_item", "Costs fell", 1),
    ]


def test_edgartools_table_inside_a_list_item_keeps_its_grid():
    summary = FakeNode("PARAGRAPH", "Summary", children=[FakeNode("TEXT", "Summary")])
    holder = item(
        "Summary rich", [summary, FakeNode("CONTAINER", children=[fake_table()])]
    )
    root = FakeNode("DOCUMENT", children=[FakeNode("LIST", children=[holder])])
    elements = adapter_edgartools.flatten(root)
    validate_elements(elements)
    assert [(e.type, e.text, e.parent) for e in elements] == [
        ("other", "", None),
        ("other", "", 0),
        ("list_item", "Summary", 1),
        ("other", "", 2),
        ("table", " 2025\nNet sales 4,321", 3),
    ]


def test_edgartools_list_item_holding_only_a_paragraph_stays_one_item():
    para = FakeNode(
        "PARAGRAPH", "Revenue grew", children=[FakeNode("TEXT", "Revenue grew")]
    )
    root = FakeNode(
        "DOCUMENT", children=[FakeNode("LIST", children=[item("Revenue grew", [para])])]
    )
    assert [(e.type, e.text) for e in adapter_edgartools.flatten(root)] == [
        ("other", ""),
        ("other", ""),
        ("list_item", "Revenue grew"),
    ]
