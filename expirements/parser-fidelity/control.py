# /// script
# requires-python = ">=3.14"
# dependencies = ["beautifulsoup4==4.15.0", "lxml==6.1.3"]
# ///
"""Negative control: naive text extraction, scored like a candidate but never selectable.

``BeautifulSoup(html, "lxml").get_text("\\n", strip=True)``, with each non-empty line
as a paragraph.

    uv run --locked --script expirements/parser-fidelity/control.py --input S --output D --sidecar C
"""

from __future__ import annotations

from pf_dump import Element, run_adapter


def parse(html: str) -> list[Element]:
    from bs4 import BeautifulSoup

    text = BeautifulSoup(html, "lxml").get_text("\n", strip=True)
    return [
        Element("paragraph", line, None, None, "line")
        for line in text.split("\n")
        if line.strip()
    ]


if __name__ == "__main__":
    raise SystemExit(run_adapter(parse, library="beautifulsoup4"))
