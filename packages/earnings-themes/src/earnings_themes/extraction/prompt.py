"""The prompt and the reply contract (the Stage 7 spec, §The prompt and the reply;
ES16, ES17, ES19).

- **The template.** The repository's ``prompts/extraction/pointer-1.md``, which the
  caller reads and passes in as text: the package reads no repository path (ES17).
  It has three sections, each opened by its heading line: ``# System``; ``# User``,
  which holds ``{units}`` once; and ``# Schema``, which holds ``{schema}`` once and
  joins the system message only without structured mode. ``sha256`` covers the
  template's UTF-8 bytes.
- **The units.** One line per unit, its label in brackets and its text with every
  run of whitespace made one space, grouped by block with a blank line between
  blocks. A context heading comes first, unlabeled and marked as not quotable.
  Labels come only from this rendering: a unit's own text cannot add one (R14.7).
- **The reply.** ``{"candidates": [{"quote_labels": [...], "claim": "..."}]}``, with
  no other key at any level. ``REPLY_SCHEMA`` comes from ``Reply``.
- **Feedback.** A reply that is not JSON or breaks the schema is answered with each
  problem by its field path, never by a value. A refused candidate is named by its
  index, labels, and reason. A label that is not ``U<n>`` may copy text, so it is
  shown as ``<not a label>`` (ES16).
"""

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated

from earnings_core import sha256_hex
from pydantic import Field, ValidationError

from earnings_themes.anchoring import Bundle
from earnings_themes.extraction.records import ExtractionProblem
from earnings_themes.extraction.windows import Window
from earnings_themes.records import Part, describe

SECTIONS = ("# System", "# User", "# Schema")
UNITS = "{units}"
SCHEMA = "{schema}"
CONTEXT = "[context, not quotable]"
LABEL = re.compile(r"U[1-9][0-9]*")
NOT_A_LABEL = "<not a label>"


@dataclass(frozen=True)
class PromptTemplate:
    """A parsed template, and the SHA-256 of its UTF-8 bytes (R14.6)."""

    system: str
    user: str
    schema: str
    sha256: str


def parse_template(text: str) -> PromptTemplate:
    """``text`` as a template; raises ``ValueError`` when a section or placeholder is
    missing, repeated, or out of order."""
    lines = text.splitlines()
    marks = [n for n, line in enumerate(lines) if line in SECTIONS]
    if [lines[n] for n in marks] != list(SECTIONS) or marks[0] != 0:
        raise ValueError("a template is # System, # User, and # Schema, in order")
    ends = [*marks[1:], len(lines)]
    system, user, schema = (
        "\n".join(lines[start + 1 : end]).strip() for start, end in zip(marks, ends)
    )
    if text.count(UNITS) != 1 or UNITS not in user:
        raise ValueError(
            f"the # User section holds {UNITS} once, and nothing else does"
        )
    if text.count(SCHEMA) != 1 or SCHEMA not in schema:
        raise ValueError(
            f"the # Schema section holds {SCHEMA} once, and nothing else does"
        )
    return PromptTemplate(system, user, schema, sha256_hex(text.encode("utf-8")))


class CandidateReply(Part):
    quote_labels: Annotated[tuple[str, ...], Field(min_length=1)]
    claim: str


class Reply(Part):
    candidates: tuple[CandidateReply, ...]


REPLY_SCHEMA = Reply.model_json_schema()


def _one_line(text: str) -> str:
    return " ".join(text.split())


def render_units(bundle: Bundle, window: Window) -> str:
    """The window's units as the model sees them."""
    text = bundle.document.canonical_text
    by_id = {element.element_id: element for element in bundle.elements}

    def words(element_id: str) -> str:
        return _one_line(by_id[element_id].span.slice_of(text))

    lines = []
    if window.context_id is not None:
        lines += [f"{CONTEXT} {words(window.context_id)}", ""]
    labels = iter(window.labels)
    for n, block in enumerate(window.blocks):
        if n:
            lines.append("")
        lines += [f"[{next(labels)}] {words(unit_id)}" for unit_id in block]
    return "\n".join(lines)


def render_messages(
    template: PromptTemplate, bundle: Bundle, window: Window, *, structured: bool
) -> tuple[str, str]:
    """The system and user messages for one window. Without structured mode, the
    system message also carries the reply's schema (ES19)."""
    system = template.system
    if not structured:
        schema = json.dumps(REPLY_SCHEMA, sort_keys=True)
        system = f"{system}\n\n{template.schema.replace(SCHEMA, schema)}"
    return system, template.user.replace(UNITS, render_units(bundle, window))


def parse_reply(text: str) -> Reply | tuple[str, ...]:
    """The reply, or each problem by its field path, never its value."""
    try:
        return Reply.model_validate_json(text)
    except ValidationError as error:
        return describe(error)


def unusable_feedback(problems: Sequence[str]) -> str:
    """Feedback on a reply that is not JSON or breaks the schema."""
    return "\n".join(
        [
            "Your reply could not be used:",
            *(f"- {problem}" for problem in problems),
            "Reply again with the JSON object only.",
        ]
    )


def shown(label: str) -> str:
    """A label as feedback shows it: ``U<n>`` as given, anything else as
    ``NOT_A_LABEL``, since it may copy text (ES16)."""
    return label if LABEL.fullmatch(label) else NOT_A_LABEL


def refused_feedback(
    refused: Sequence[tuple[int, tuple[str, ...], ExtractionProblem]],
    *,
    units: int,
    claim_limit: int,
) -> str:
    """Feedback on refused candidates, each by its index, labels, and reason."""
    rules = (
        f"Each label is one of U1 to U{units}, at most once per candidate, and each"
        f" claim is non-blank and at most {claim_limit} characters."
    )
    return "\n".join(
        [
            "These candidates were refused:",
            *(
                f"- candidates[{index}], labels"
                f" {json.dumps([shown(label) for label in labels])}: {problem}"
                for index, labels, problem in refused
            ),
            rules,
            "Reply with corrected versions of these candidates only, as a new object.",
        ]
    )
