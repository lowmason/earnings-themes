"""The local label view (the Stage 11 spec, A4 and §Labels; FP8; GS13).

For each sampled target, in sample order: its claim, each quote in its block with
the nearest heading, and the theme's definition and rules. It holds no score, no
judge answer, no flag or reason code, and no model's identity, so the user labels
unaided (FP8). The view holds release text, so it is written only under
``data/runs/pilot/labels/views/`` and never printed (A8).
"""

from collections.abc import Sequence

from earnings_themes.evaluation.problems import EvaluationError, EvaluationProblem
from earnings_themes.support.context import context_elements
from earnings_themes.support.records import (
    EvidenceReference,
    StoredSupportRun,
    SupportSources,
)

INSTRUCTIONS = (
    "Answer two questions for each target, from this view alone:\n"
    "- claim_support: does the cited evidence support the claim, with its"
    " attribution, time, scope and polarity? supported, unsupported or unsure.\n"
    "- theme_fit: does the claim fit the theme's definition and its rules?"
    " fits, does_not_fit or unsure.\n"
    "Each quote is shown in its block, between ⟦ and ⟧."
)


def _flat(text: str) -> str:
    return " ".join(text.split())


def _quote(
    text: str, sources: SupportSources, evidence: EvidenceReference
) -> list[str]:
    bundle = next(
        (b for b in sources.bundles if b.document.doc_id == evidence.doc_id), None
    )
    if bundle is None:
        raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, "evidence.doc_id")
    context = context_elements(bundle, evidence.element_id)
    block = context[-1].span
    start, end = evidence.start, evidence.end
    lines = []
    if len(context) == 2:
        heading = context[0].span
        lines.append(f"*{_flat(text[heading.start : heading.end])}*")
    before = text[block.start : start] if block.start <= start else ""
    after = text[end : block.end] if end <= block.end else ""
    lines.append(
        f"> {_flat(before)} ⟦{_flat(text[start:end])}⟧ {_flat(after)}".rstrip()
    )
    return lines


def label_views(
    support: StoredSupportRun, sources: SupportSources, sample: Sequence[str]
) -> str:
    """The markdown view of ``sample``'s targets, from a reverified support run."""
    targets = {t.target_id: t for t in support.targets}
    claims = {(c.doc_id, c.claim_id): c.claim for c in sources.stored_run.claims}
    texts = {b.document.doc_id: b.document.canonical_text for b in sources.bundles}
    out = ["# Support labels", "", INSTRUCTIONS]
    for number, target_id in enumerate(sample, 1):
        record = targets.get(target_id)
        if record is None:
            raise EvaluationError(EvaluationProblem.UNKNOWN_TARGET, target_id)
        target, theme = record.target, record.theme
        claim = claims.get((target.doc_id, target.claim_id))
        if theme is None or claim is None or target.doc_id not in texts:
            raise EvaluationError(EvaluationProblem.MALFORMED_RECORD, target_id)
        out += ["", f"## {number}. {target_id}", "", f"**Claim:** {_flat(claim)}", ""]
        for evidence in support.evidence:
            if evidence.target_id == target_id:
                out += [*_quote(texts[target.doc_id], sources, evidence), ""]
        out += [f"**Theme:** {_flat(theme.label)}", "", _flat(theme.definition), ""]
        out += ["Include when:", *(f"- {_flat(r)}" for r in theme.inclusion_rules)]
        out += ["Exclude when:", *(f"- {_flat(r)}" for r in theme.exclusion_rules)]
    return "\n".join(out) + "\n"
