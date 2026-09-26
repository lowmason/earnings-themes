from collections import Counter

import pytest
from layout1_units import (
    CLASSES,
    UNITS,
    derive,
    fixture_units,
    load_units,
    render,
    stylesheets,
)


def test_the_committed_units_are_what_the_script_derives() -> None:
    assert UNITS.read_text(encoding="utf-8") == render(derive()), (
        "regenerate: uv run --locked --all-packages python"
        " expirements/parser-fidelity/layout1_units.py"
    )


def test_the_classes_hold_v2s_counts() -> None:
    units = load_units()
    assert Counter(unit.klass for unit in units) == {CLASSES[0]: 23, CLASSES[1]: 38}
    in_tables = Counter(unit.type for unit in units if unit.klass == CLASSES[1])
    assert in_tables == {"heading": 19, "paragraph": 13, "footnote": 6}
    assert len({(unit.klass, unit.fixture, unit.block) for unit in units}) == 61


@pytest.mark.parametrize(
    ("html", "count"),
    [
        ("<p>plain</p>", 0),
        ("<style>p { display: none }</style><p>x</p>", 1),
        ('<link rel="Stylesheet" href="a.css"><p>x</p>', 1),
        ('<link rel="icon" href="a.ico"><p>x</p>', 0),
    ],
)
def test_stylesheets_are_counted(html: str, count: int) -> None:
    assert stylesheets(html) == count


def test_a_fixture_with_a_stylesheet_stops_the_derivation() -> None:
    raw = b"<html><head><style>.x{}</style></head><body><p>x</p></body></html>"
    with pytest.raises(SystemExit, match="stop and report"):
        fixture_units("synthetic", raw, {"blocks": []})
