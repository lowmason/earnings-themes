"""Validate hand-marked gold structure (spec: Gold annotation > Validator). Standard library only.

    uv run --locked --all-packages python expirements/parser-fidelity/validate_gold.py tests/fixtures/releases/<id> [...]
    uv run --locked --all-packages python expirements/parser-fidelity/validate_gold.py --init tests/fixtures/releases/<id>

The source text comes from the standard library's ``html.parser`` (pf_text), which is
independent of every candidate. Errors block scoring; warnings do not.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path

import tomllib
from pf_decode import decode_html_bytes
from pf_space import fallback_space, find_all, primary_space
from pf_text import extract_document_text

TEXT_TYPES = frozenset({"heading", "paragraph", "list_item", "footnote"})
BLOCK_TYPES = TEXT_TYPES | {"table", "page_artifact"}
LEVEL_TYPES = frozenset({"heading", "list_item"})
CELL_ROLES = ("corner", "right", "below")
TOP_KEYS = frozenset(
    {
        "schema_version",
        "fixture_id",
        "annotator",
        "marked_from",
        "browser",
        "completed",
        "blocks",
    }
)
TEXT_KEYS = frozenset({"id", "type", "level", "start", "end", "after", "unanchorable"})
TABLE_KEYS = frozenset({"id", "type", "headers", "cells"})
ARTIFACT_KEYS = frozenset({"id", "type", "start"})
CELL_KEYS = frozenset({"role", "text", "row_header", "col_header"})
MIN_ANCHOR_WORDS = 4
MIN_ANCHOR_CHARS = 20
_ID = re.compile(r"^[A-Za-z0-9_-]+$")
_LEADING_MARKER = re.compile(
    r"^\s*(?:[\u2022\u25cf\u25e6\u25aa\u25a0\xb7*\u2020\u2021\xa7]|\(?\d{1,2}\)|\([a-z]\))\s"
)

SKELETON = """schema_version = 1
fixture_id = "{fixture_id}"
annotator = ""
marked_from = "browser rendering"
browser = ""
# completed = YYYY-MM-DD   (add when the file is finished)

# One [[blocks]] entry per rendered block, in rendered reading order. Example:
# [[blocks]]
# id = "b001"
# type = "heading"
# level = 1
# start = "first words of the block"
"""


@dataclass
class Report:
    fixture_id: str
    encoding: str = ""
    encoding_basis: str = ""
    ascii_only: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unanchorable: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors


class SourceText:
    """A fixture's validator text in both matching spaces."""

    def __init__(self, raw: bytes) -> None:
        decoded = decode_html_bytes(raw)
        self.decoded = decoded
        text = extract_document_text(decoded.text)
        self.primary = primary_space(text)
        self.fallback = fallback_space(text)
        self.casefolded = self.primary.casefold()

    def count(self, anchor: str) -> int:
        return len(find_all(self.primary, anchor)) if anchor else 0

    def count_fallback(self, anchor: str) -> int:
        return len(find_all(self.fallback, anchor)) if anchor else 0

    def count_casefold(self, anchor: str) -> int:
        return len(find_all(self.casefolded, anchor.casefold())) if anchor else 0


def load_gold(fixture_dir: Path) -> dict:
    return tomllib.loads((fixture_dir / "gold.toml").read_text(encoding="utf-8"))


def _short(anchor: str) -> bool:
    return len(anchor.split()) < MIN_ANCHOR_WORDS and len(anchor) < MIN_ANCHOR_CHARS


def _nonempty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def check_schema(gold: dict, fixture_id: str) -> list[str]:
    errors = [f"unknown top-level key {key!r}" for key in sorted(set(gold) - TOP_KEYS)]
    errors += [f"missing top-level key {key!r}" for key in sorted(TOP_KEYS - set(gold))]
    if gold.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if gold.get("fixture_id") != fixture_id:
        errors.append(f"fixture_id must be {fixture_id!r}")
    for key in ("annotator", "browser"):
        if key in gold and not _nonempty_str(gold[key]):
            errors.append(f"{key} must be a non-empty string")
    if gold.get("marked_from", "browser rendering") != "browser rendering":
        errors.append('marked_from must be "browser rendering"')
    if "completed" in gold and not isinstance(gold["completed"], dt.date):
        errors.append("completed must be a date such as 2026-10-01")
    blocks = gold.get("blocks", [])
    if not isinstance(blocks, list) or not blocks:
        return errors + ["blocks must be a non-empty array of tables"]
    seen: set[str] = set()
    for position, block in enumerate(blocks, start=1):
        errors += [
            f"block {block.get('id', f'#{position}')}: {e}"
            for e in _check_block(block, seen)
        ]
    return errors


def _check_block(block: dict, seen: set[str]) -> list[str]:
    errors = []
    block_id, kind = block.get("id"), block.get("type")
    if not isinstance(block_id, str) or not _ID.match(block_id):
        errors.append("id must be letters, digits, '-' or '_'")
    elif block_id in seen:
        errors.append("duplicate id")
    else:
        seen.add(block_id)
    if kind not in BLOCK_TYPES:
        return errors + [f"type must be one of {sorted(BLOCK_TYPES)}"]
    allowed = (
        TEXT_KEYS
        if kind in TEXT_TYPES
        else TABLE_KEYS
        if kind == "table"
        else ARTIFACT_KEYS
    )
    errors += [
        f"key {key!r} is not allowed on a {kind}"
        for key in sorted(set(block) - allowed)
    ]
    if "level" in block and (
        kind not in LEVEL_TYPES
        or not isinstance(block["level"], int)
        or block["level"] < 1
    ):
        errors.append(
            "level must be a positive integer, and only on headings and list items"
        )
    if kind == "table":
        return errors + _check_table(block)
    if not _nonempty_str(block.get("start")):
        errors.append("start must be a non-empty string")
    for key in ("end", "after"):
        if key in block and not _nonempty_str(block[key]):
            errors.append(f"{key} must be a non-empty string")
    if "unanchorable" in block and not isinstance(block["unanchorable"], bool):
        errors.append("unanchorable must be true or false")
    if "after" in block and "end" in block:
        errors.append("a block with after omits end")
    if block.get("unanchorable") and "end" in block:
        errors.append("an unanchorable block puts its full text in start and omits end")
    if kind in TEXT_TYPES and not block.get("unanchorable") and not errors:
        if "end" in block and _short(block["start"]):
            errors.append(
                "start is shorter than four words and 20 characters but the block has an end"
            )
        if "end" in block and _short(block["end"]):
            errors.append("end is shorter than four words and 20 characters")
    return errors


def _check_table(block: dict) -> list[str]:
    errors = []
    headers = block.get("headers")
    if not isinstance(headers, list) or not all(_nonempty_str(h) for h in headers):
        errors.append("headers must be an array of non-empty strings")
    cells = block.get("cells")
    if not isinstance(cells, list) or len(cells) != 3:
        return errors + ["cells must hold exactly three cells"]
    roles = []
    for cell in cells:
        if (
            not isinstance(cell, dict)
            or set(cell) != CELL_KEYS
            or not all(_nonempty_str(cell[k]) for k in CELL_KEYS)
        ):
            errors.append(
                "each cell needs non-empty role, text, row_header, and col_header"
            )
            continue
        roles.append(cell["role"])
    if sorted(roles) != sorted(CELL_ROLES) and len(roles) == 3:
        errors.append("cells must have exactly one each of roles corner, right, below")
    return errors


def text_anchors(block: dict) -> list[tuple[str, str]]:
    """(label, raw anchor) pairs a text block is matched by; a block with after matches start+after."""
    if "after" in block:
        return [("start+after", block["start"] + block["after"])]
    anchors = [("start", block["start"])]
    if "end" in block:
        anchors.append(("end", block["end"]))
    return anchors


def check_anchors(gold: dict, source: SourceText) -> tuple[list[str], list[str], int]:
    errors: list[str] = []
    warnings: list[str] = []
    unanchorable = 0
    for block in gold["blocks"]:
        block_id, kind = block["id"], block["type"]
        if kind == "page_artifact":
            continue
        if kind == "table":
            for cell in block["cells"]:
                errors += _unique(
                    source, f"block {block_id}: cell {cell['role']}", cell["text"]
                )
            for header in block["headers"]:
                if source.count(primary_space(header)) == 0:
                    errors.append(
                        f"block {block_id}: header {header!r} not found{_case_hint(source, header)}"
                    )
            continue
        if block.get("unanchorable"):
            unanchorable += 1
            probe = block["start"] + block.get("after", "")
            if source.count(primary_space(probe)) < 2:
                errors.append(
                    f"block {block_id}: unanchorable text must occur at least twice"
                )
            continue
        for label, anchor in text_anchors(block):
            errors += _unique(source, f"block {block_id}: {label}", anchor)
            if source.count_fallback(fallback_space(anchor)) != 1:
                warnings.append(
                    f"block {block_id}: {label} is not unique in the fallback space"
                )
            if _LEADING_MARKER.match(anchor):
                warnings.append(
                    f"block {block_id}: {label} may begin with a bullet or marker"
                )
        if "end" in block:
            start_hits = (
                find_all(source.primary, primary_space(block["start"]))
                if primary_space(block["start"])
                else []
            )
            end_hits = (
                find_all(source.primary, primary_space(block["end"]))
                if primary_space(block["end"])
                else []
            )
            if (
                len(start_hits) == 1
                and len(end_hits) == 1
                and end_hits[0] < start_hits[0]
            ):
                warnings.append(f"block {block_id}: end precedes start")
    return errors, warnings, unanchorable


def _unique(source: SourceText, label: str, anchor: str) -> list[str]:
    form = primary_space(anchor)
    if not form:
        return [f"{label}: anchor has no characters in the matching space"]
    hits = source.count(form)
    if hits == 1:
        return []
    if hits == 0:
        return [f"{label}: not found{_case_hint(source, anchor)}"]
    return [f"{label}: occurs {hits} times; extend it until it is unique"]


def _case_hint(source: SourceText, anchor: str) -> str:
    hits = source.count_casefold(primary_space(anchor))
    return (
        f" (case-insensitive hits: {hits}; CSS text-transform may have changed the case)"
        if hits
        else ""
    )


def validate_fixture(fixture_dir: Path) -> Report:
    report = Report(fixture_id=fixture_dir.name)
    source = SourceText((fixture_dir / "source.html").read_bytes())
    report.encoding = source.decoded.encoding
    report.encoding_basis = source.decoded.basis
    report.ascii_only = source.decoded.ascii_only
    gold_path = fixture_dir / "gold.toml"
    if not gold_path.exists():
        report.errors.append("gold.toml is missing")
        return report
    try:
        gold = load_gold(fixture_dir)
    except tomllib.TOMLDecodeError as exc:
        report.errors.append(f"gold.toml is not valid TOML: {exc}")
        return report
    report.errors += check_schema(gold, fixture_dir.name)
    if report.errors:
        return report
    errors, warnings, unanchorable = check_anchors(gold, source)
    report.errors += errors
    report.warnings += warnings
    report.unanchorable = unanchorable
    return report


def init_skeleton(fixture_dir: Path) -> Path:
    path = fixture_dir / "gold.toml"
    if path.exists():
        raise FileExistsError(f"{path} exists; refusing to overwrite")
    path.write_text(SKELETON.format(fixture_id=fixture_dir.name), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("fixture_dirs", nargs="+", type=Path)
    parser.add_argument(
        "--init",
        action="store_true",
        help="write a gold.toml skeleton (header fields only)",
    )
    args = parser.parse_args(argv)
    if args.init:
        for fixture_dir in args.fixture_dirs:
            print(f"wrote {init_skeleton(fixture_dir)}")
        return 0
    status = 0
    for fixture_dir in args.fixture_dirs:
        report = validate_fixture(fixture_dir)
        ascii_note = (
            "; every byte is ASCII, so any browser encoding agrees"
            if report.ascii_only
            else ""
        )
        print(
            f"{report.fixture_id}: decoded as {report.encoding} (basis: {report.encoding_basis}{ascii_note})"
        )
        for error in report.errors:
            print(f"  ERROR   {error}")
        for warning in report.warnings:
            print(f"  warning {warning}")
        print(
            f"  {len(report.errors)} errors, {len(report.warnings)} warnings, {report.unanchorable} unanchorable"
        )
        status |= 0 if report.ok else 1
    return status


if __name__ == "__main__":
    raise SystemExit(main())
