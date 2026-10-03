"""Local views, for drafting and for verification (the Stage 6 spec, §Anchoring and
validation; GS11, GS13).

A view holds a release's text, so the application writes it only under
``data/runs/gold/``, which is never committed, and no command prints it.

- ``render_text`` is one bundle's text alone: the only text a drafting session is
  given (GS13).
- ``render_view`` marks each quote in the text as ``[[q1>>`` ... ``<<q1]]`` and
  lists the claims, their themes and support, the hard negatives, and the
  release-identification label: the user verifies, and does the omission pass,
  against it.
"""

import re

from earnings_themes.anchoring import Bundle
from earnings_themes.gold import FixtureNegatives, Gold, GoldQuote, HardNegative

_TICKS = re.compile(r"`+")


def _fenced(text: str) -> list[str]:
    longest = max((len(run) for run in _TICKS.findall(text)), default=0)
    fence = "`" * max(3, longest + 1)
    return [f"{fence}text", text.rstrip("\n"), fence]


def _head(bundle: Bundle) -> list[str]:
    return [
        f"# {bundle.name}",
        "",
        (
            f"`{bundle.document.doc_id}`. A local view of a release's text: never"
            " commit it, and never paste from it into a committed file."
        ),
        "",
    ]


def render_text(bundle: Bundle) -> str:
    """The bundle's canonical text, for a drafting session."""
    return "\n".join([*_head(bundle), *_fenced(bundle.document.canonical_text)]) + "\n"


def marked(text: str, quotes: tuple[GoldQuote, ...]) -> str:
    """``text`` with each quote's start and end marked by its ID."""
    marks = []
    for quote in quotes:
        marks.append((quote.start, 1, -quote.end, f"[[{quote.quote_id}>>"))
        marks.append((quote.end, 0, -quote.start, f"<<{quote.quote_id}]]"))
    pieces, position = [], 0
    for at, _, _, mark in sorted(marks):
        pieces += [text[position:at], mark]
        position = at
    return "".join([*pieces, text[position:]])


def _negatives(negatives: tuple[HardNegative, ...]) -> list[str]:
    lines = ["", "## Hard negatives", ""]
    if not negatives:
        lines.append("(none)")
    for n in negatives:
        wrongly = f"; would wrongly support {n.theme_id}" if n.theme_id else ""
        quotes = ", ".join(n.quote_ids)
        lines.append(
            f"- {n.claim_id} ({n.negative_kind}{wrongly}; {n.origin}), quotes"
            f" {quotes}: {n.claim}"
        )
    return lines


def _quotes(quotes: tuple[GoldQuote, ...]) -> list[str]:
    lines = ["", "## Quotes", ""]
    for q in quotes:
        masks = f"; masks {', '.join(q.mask_ids)}" if q.mask_ids else ""
        lines.append(f"- {q.quote_id} ({q.origin}) in {q.element_id}{masks}")
    return lines


def render_view(bundle: Bundle, gold: Gold) -> str:
    """The bundle's text with its gold marked, for verification."""
    release = gold.release_identification
    lines = [
        *_head(bundle),
        (
            f"Partition {gold.partition}; codebook {gold.codebook.codebook_id}"
            f" v{gold.codebook.codebook_version}; signed: {gold.annotator or '(no)'};"
            f" no_theme: {str(gold.no_theme).lower()}."
        ),
        "",
        f"Release identification: {release.label}. {release.note}",
        "",
        *_fenced(marked(bundle.document.canonical_text, gold.quotes)),
        "",
        "## Claims",
        "",
    ]
    for claim in gold.claims:
        lines.append(
            f"- {claim.claim_id} ({claim.origin}), quotes"
            f" {', '.join(claim.quote_ids)}: {claim.claim}"
        )
        for a in gold.assignments:
            if a.claim_id == claim.claim_id:
                tie = f", tie {a.tie_group}" if a.tie_group else ""
                lines.append(f"  - {a.theme_id}: {a.support}{tie} ({a.origin})")
    lines += _negatives(gold.hard_negatives) + _quotes(gold.quotes)
    return "\n".join(lines) + "\n"


def render_curated_view(bundle: Bundle, document: FixtureNegatives) -> str:
    """One Stage 1 fixture's text with its curated hard negatives marked."""
    lines = [
        *_head(bundle),
        *_fenced(marked(bundle.document.canonical_text, document.quotes)),
        *_negatives(document.hard_negatives),
        *_quotes(document.quotes),
    ]
    return "\n".join(lines) + "\n"
