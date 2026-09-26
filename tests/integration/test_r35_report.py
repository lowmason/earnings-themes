"""R3.5's committed report covers all six categories (Stage 3 spec: Verification
(plan A), item 10), and both legs, which makes it final (plan B)."""

import re
from pathlib import Path

import pytest

REPORT = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "verification"
    / "R3.5-text-fidelity.md"
)
CATEGORIES = (
    "Unicode",
    "Numeric signs",
    "Scale",
    "Superscripts",
    "Footnotes",
    "Table headings",
)
INSTANCES = re.compile(
    r"^\*\*Instances:\*\* (?:[1-9][0-9]*|no instances in sample)$", re.MULTILINE
)


def sections() -> dict[str, str]:
    parts = re.split(r"^## ", REPORT.read_text(encoding="utf-8"), flags=re.MULTILINE)
    return {part.split("\n", 1)[0]: part for part in parts[1:]}


@pytest.mark.parametrize("category", CATEGORIES)
def test_every_category_reports_its_instances(category: str) -> None:
    section = sections().get(category)
    assert section is not None, f"the R3.5 report has no {category} section"
    assert INSTANCES.search(section), f"{category} reports no instance count"


def test_the_report_is_final_with_both_legs() -> None:
    leg2 = sections().get("Leg 2: canonical text against the browser's text")
    assert leg2 is not None, "the R3.5 report has no second leg"
    assert "### Against innerText" in leg2
    assert "### Against the user's rendered copies" in leg2
