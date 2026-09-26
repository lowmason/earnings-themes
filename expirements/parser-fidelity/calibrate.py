"""Rendered-text calibration: the capture's innerText against the user's copies.

    uv run --locked --all-packages python expirements/parser-fidelity/calibrate.py

(Stage 3 spec, Checks; the browser spec, Rendered-text calibration.) For one release
of each named category, compares the committed capture's text
(``document.body.innerText``) with the user's copy, made in Chrome by Select All and
Copy (data/runs/parser-fidelity/gold-drafts/<fixture>.rendered.txt, local and never
committed), and writes docs/verification/browser-calibration.md. The copies are
calibration observations, not gold, and no gold changes.

Both texts are split into tokens, the maximal runs of non-whitespace, and aligned by
difflib with its junk heuristic off. Each difference is classed into one of the
browser spec's eight kinds by the first rule that fits (plan 5, PB-15):

- a separator between two aligned tokens that differs, or differing leading or
  trailing whitespace, is ``table-cell separation`` when either side holds a tab, and
  ``whitespace`` otherwise;
- a hunk present on one side only whose tokens appear, in order, as a one-sided hunk
  on the other side is ``reading order``, and so is its partner;
- a hunk of bullet glyphs only is ``bullets``;
- a hunk whose tokens differ only in case is ``CSS text transformation``;
- a one-sided hunk that is one of the source's image alternative texts is ``image
  alternative text``;
- a one-sided hunk inside the source's hidden text is ``hidden content``: text under
  ``display: none``, ``visibility: hidden``, or the ``hidden`` attribute, read by
  ``html.parser``;
- anything else is ``visible characters``.
"""

from __future__ import annotations

import difflib
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from html.parser import HTMLParser

from earnings_ingestion.browser.serialize import from_capture_json
from earnings_ingestion.canonical.walker import BULLETS
from pf_decode import decode_html_bytes
from pf_paths import FIXTURES, REPO_ROOT, RUNS

REPORT = REPO_ROOT / "docs" / "verification" / "browser-calibration.md"
CAPTURES = REPO_ROOT / "tests" / "fixtures" / "browser"
COPIES = RUNS / "gold-drafts"
CALIBRATED = (
    ("narrative-only", "0000706863-16-000110_ex-99-1"),
    ("table-bearing", "0000877860-13-000100_ex-99-1"),
    ("malformed layout", "0000009389-10-000004_ex-99-1"),
)
"""The browser spec's three categories: Union Bankshares, National Health Investors,
and Ball."""
KINDS = (
    "visible characters",
    "whitespace",
    "bullets",
    "CSS text transformation",
    "hidden content",
    "image alternative text",
    "table-cell separation",
    "reading order",
)
EXAMPLES = 5
"""Hunks shown per kind and fixture; every hunk is counted."""
_TOKEN = re.compile(r"\S+")
_HIDDEN_STYLE = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden")
_VOID = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
     "param", "source", "track", "wbr"}
)  # fmt: skip


@dataclass(frozen=True)
class Difference:
    kind: str
    captured: str
    copied: str


class _Source(HTMLParser):
    """Alternative texts and hidden text, from ``html.parser`` alone."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.alternatives: list[str] = []
        self.hidden: list[str] = []
        self._stack: list[bool] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        values = {name: value or "" for name, value in attrs}
        if tag == "img" and values.get("alt", "").strip():
            self.alternatives.append(" ".join(values["alt"].split()))
        if tag in _VOID:
            return
        hidden = "hidden" in values or bool(
            _HIDDEN_STYLE.search(values.get("style", "").lower())
        )
        self._stack.append(hidden or (bool(self._stack) and self._stack[-1]))

    def handle_endtag(self, tag: str) -> None:
        if tag not in _VOID and self._stack:
            self._stack.pop()

    def handle_data(self, data: str) -> None:
        if self._stack and self._stack[-1]:
            self.hidden.append(data)


@dataclass(frozen=True)
class SourceFacts:
    alternatives: frozenset[str]
    hidden: str
    """The hidden text, whitespace runs collapsed."""


def source_facts(html: str) -> SourceFacts:
    reader = _Source()
    reader.feed(html)
    reader.close()
    return SourceFacts(
        frozenset(reader.alternatives), " ".join(" ".join(reader.hidden).split())
    )


@dataclass
class _Side:
    tokens: list[str]
    separators: list[str]
    """Whitespace before each token, then after the last: one more than tokens."""


def _split(text: str) -> _Side:
    tokens, separators, cursor = [], [], 0
    for match in _TOKEN.finditer(text):
        separators.append(text[cursor : match.start()])
        tokens.append(match.group())
        cursor = match.end()
    separators.append(text[cursor:])
    return _Side(tokens, separators)


def differences(captured: str, copied: str, facts: SourceFacts) -> list[Difference]:
    """Every difference between the two texts, classed into the eight kinds."""
    left, right = _split(captured), _split(copied)
    matcher = difflib.SequenceMatcher(None, left.tokens, right.tokens, autojunk=False)
    found: list[Difference] = []
    hunks: list[tuple[list[str], list[str]]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            hunks.append((left.tokens[i1:i2], right.tokens[j1:j2]))
            continue
        for offset in range(i2 - i1 + 1):
            a, b = left.separators[i1 + offset], right.separators[j1 + offset]
            inner = 0 < offset < i2 - i1
            edge = (i1 + offset in (0, len(left.tokens))) and (
                j1 + offset in (0, len(right.tokens))
            )
            if (inner or edge) and a != b:
                kind = "table-cell separation" if "\t" in a + b else "whitespace"
                found.append(Difference(kind, repr(a), repr(b)))
    moved = _moved(hunks)
    for index, (a, b) in enumerate(hunks):
        found.append(
            Difference(
                "reading order" if index in moved else _kind(a, b, facts),
                " ".join(a),
                " ".join(b),
            )
        )
    return found


def _moved(hunks: Sequence[tuple[list[str], list[str]]]) -> set[int]:
    """One-sided hunks whose tokens appear as a one-sided hunk on the other side."""
    only_left = {i: tuple(a) for i, (a, b) in enumerate(hunks) if a and not b}
    only_right = {i: tuple(b) for i, (a, b) in enumerate(hunks) if b and not a}
    moved: set[int] = set()
    for i, tokens in only_left.items():
        partner = next(
            (
                j
                for j, other in only_right.items()
                if other == tokens and j not in moved
            ),
            None,
        )
        if partner is not None:
            moved.update((i, partner))
    return moved


def _kind(left: list[str], right: list[str], facts: SourceFacts) -> str:
    if all(set(token) <= set(BULLETS) for token in left + right):
        return "bullets"
    if (
        len(left) == len(right)
        and left != right
        and all(a.casefold() == b.casefold() for a, b in zip(left, right, strict=True))
    ):
        return "CSS text transformation"
    extra = " ".join(left or right)
    if not (left and right):
        if extra in facts.alternatives:
            return "image alternative text"
        if f" {extra} " in f" {facts.hidden} ":
            return "hidden content"
    return "visible characters"


@dataclass
class Calibrated:
    category: str
    fixture: str
    differences: list[Difference] = field(default_factory=list)


def missing_inputs() -> list[str]:
    """The captures and local copies the report needs that are not present."""
    wanted = [CAPTURES / f"{fixture}.capture.json" for _, fixture in CALIBRATED]
    wanted += [COPIES / f"{fixture}.rendered.txt" for _, fixture in CALIBRATED]
    return [str(path.relative_to(REPO_ROOT)) for path in wanted if not path.is_file()]


def calibrate() -> list[Calibrated]:
    out = []
    for category, fixture in CALIBRATED:
        capture = from_capture_json(
            (CAPTURES / f"{fixture}.capture.json").read_text(encoding="utf-8")
        )
        copied = (COPIES / f"{fixture}.rendered.txt").read_text(encoding="utf-8")
        raw = (FIXTURES / fixture / "source.html").read_bytes()
        facts = source_facts(decode_html_bytes(raw).text)
        out.append(
            Calibrated(
                category, fixture, differences(capture.rendered_text, copied, facts)
            )
        )
    return out


def render(results: Sequence[Calibrated]) -> str:
    lines = [
        "# Rendered-text calibration: innerText against the user's copies",
        "",
        "Generated by `expirements/parser-fidelity/calibrate.py`; do not edit. It needs",
        "the user's local copies in `data/runs/parser-fidelity/gold-drafts/`, which are",
        "never committed. The copies are calibration observations, not gold, and no",
        "gold changed (Stage 3 spec, Checks).",
        "",
        "Each capture's `document.body.innerText`, under capture policy `isolated/1`,",
        "is compared with the user's copy of the same release, made in Chrome by",
        "Select All and Copy. Tokens are aligned by difflib; every difference is",
        "counted in one of the browser spec's eight kinds, by the rules in",
        "`calibrate.py`'s docstring.",
        "",
        "| Kind | " + " | ".join(r.fixture for r in results) + " |",
        "| --- |" + " --- |" * len(results),
    ]
    counts = [Counter(d.kind for d in r.differences) for r in results]
    for kind in KINDS:
        lines.append(f"| {kind} | " + " | ".join(str(c[kind]) for c in counts) + " |")
    for result, count in zip(results, counts, strict=True):
        lines += [
            "",
            f"## `{result.fixture}` ({result.category})",
            "",
            f"Differences: {sum(count.values())}.",
        ]
        for kind in KINDS:
            shown = [d for d in result.differences if d.kind == kind][:EXAMPLES]
            if not shown:
                continue
            lines += [
                "",
                f"### {kind}: {count[kind]}",
                "",
                "| innerText | Copy |",
                "| --- | --- |",
            ]
            lines += [f"| {_cell(d.captured)} | {_cell(d.copied)} |" for d in shown]
    return "\n".join(lines) + "\n"


def _cell(text: str) -> str:
    text = text.replace("|", "\\|")
    return (text[:77] + "...") if len(text) > 80 else (text or "(nothing)")


def main() -> int:
    missing = missing_inputs()
    if missing:
        print("missing: " + ", ".join(missing))
        return 1
    REPORT.write_text(render(calibrate()), encoding="utf-8", newline="\n")
    print(f"wrote {REPORT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
