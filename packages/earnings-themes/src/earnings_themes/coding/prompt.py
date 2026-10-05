"""Render exact bounded data and resolve closed replies against frozen targets."""

import json

from earnings_core import VALIDATOR_VERSION, digest, sha256_hex

from earnings_themes.coding.input import CodingInput, reverify_coding_input
from earnings_themes.coding.records import (
    CodingError,
    CodingPolicy,
    CodingReply,
    CodingRequest,
    CodingSubject,
    NoveltyItem,
    checked,
)
from earnings_themes.extraction.adapters import Message, ModelReply
from earnings_themes.support.records import ContextReference, EvidenceReference, Target


def render_coding(input: CodingInput, policy: CodingPolicy) -> CodingRequest:
    """Reverify every original link and preserve complete definitions as JSON data."""
    input = reverify_coding_input(input)
    policy = checked(policy, CodingPolicy)
    if sha256_hex(policy.prompt_text.encode("utf-8")) != policy.prompt_hash:
        raise CodingError("input_changed")
    first = input.probes[0]
    by_doc = {bundle.document.doc_id: bundle for bundle in input.sources.bundles}

    def passage(reference: EvidenceReference | ContextReference) -> dict[str, object]:
        text = by_doc[reference.doc_id].document.canonical_text
        return {
            **reference.model_dump(mode="json"),
            "text": text[reference.start : reference.end],
        }

    data = {
        "claim": first.claim,
        "quoted_evidence": [passage(reference) for reference in first.evidence],
        "attribution_context": [passage(reference) for reference in first.contexts],
        "frozen_themes": [
            probe.record.theme.model_dump(mode="json") for probe in input.probes
        ],
        "codebook_rules": input.sources.codebook.rules.model_dump(mode="json"),
    }
    schema = CodingReply.model_json_schema()
    system = policy.prompt_text
    if not policy.parameters.structured:
        system += "\nClosed reply schema: " + json.dumps(schema, sort_keys=True)
    return CodingRequest(
        messages=(
            Message(role="system", content=system),
            Message(
                role="user",
                content=json.dumps(data, sort_keys=True, ensure_ascii=False),
            ),
        ),
        reply_schema=schema,
        parameters=policy.parameters,
        subject=CodingSubject(
            doc_id=input.doc_id,
            claim_id=input.claim_id,
            input_hash=input.input_hash,
            codebook=first.record.target.codebook,
            prompt_hash=policy.prompt_hash,
            schema_hash=digest(schema),
            validator_version=VALIDATOR_VERSION,
        ),
    )


def parse_coding_reply(
    reply: ModelReply, input: CodingInput, model_id: str
) -> CodingReply:
    """Reverify input before accepting a tool-free closed frozen-ID proposal."""
    input = reverify_coding_input(input)
    reply = checked(reply, ModelReply)
    if reply.tool_calls:
        raise CodingError("tool_call_refused")
    if reply.model != model_id:
        raise CodingError("model_mismatch")
    try:
        answer = checked(json.loads(reply.text), CodingReply)
    except (ValueError, CodingError):
        raise CodingError("malformed_reply") from None
    allowed = {probe.record.target.theme_id for probe in input.probes}
    if not set(answer.theme_ids) <= allowed:
        raise CodingError("invalid_references")
    check_hierarchy(input, answer.theme_ids)
    return answer


def check_hierarchy(input: CodingInput, theme_ids: tuple[str, ...]) -> None:
    """Refuse ancestor-plus-descendant selections without choosing for the model."""
    parents = {
        probe.record.theme.theme_id: probe.record.theme.parent_id
        for probe in input.probes
    }
    chosen = set(theme_ids)
    for theme_id in chosen:
        parent = parents[theme_id]
        while parent is not None:
            if parent in chosen:
                raise CodingError("hierarchy_conflict")
            parent = parents[parent]


def targets_for(input: CodingInput, reply: CodingReply) -> tuple[Target, ...]:
    """Return only explicit selected targets, preserving their original identity."""
    input = reverify_coding_input(input)
    reply = checked(reply, CodingReply)
    targets = {
        probe.record.target.theme_id: probe.record.target for probe in input.probes
    }
    if not set(reply.theme_ids) <= targets.keys():
        raise CodingError("invalid_references")
    check_hierarchy(input, reply.theme_ids)
    return tuple(targets[theme_id] for theme_id in sorted(reply.theme_ids))


def novelty_for(
    input: CodingInput,
    reply: CodingReply,
    *,
    coding_run_id: str,
    classification_id: str,
) -> NoveltyItem | None:
    """Keep valid unmatched claims as original evidence pointers for human review."""
    input = reverify_coding_input(input)
    reply = checked(reply, CodingReply)
    if reply.theme_ids:
        return None
    first = input.probes[0].record
    identity = {
        "coding_run_id": coding_run_id,
        "classification_id": classification_id,
        "input_hash": input.input_hash,
        "reason": "no_theme_fit",
    }
    return NoveltyItem(
        novelty_id="novelty-" + digest(identity),
        coding_run_id=coding_run_id,
        classification_id=classification_id,
        source_run_id=first.target.source_run_id,
        doc_id=input.doc_id,
        claim_id=input.claim_id,
        codebook=first.target.codebook,
        input_hash=input.input_hash,
        original_quote_ids=first.original_quote_ids,
    )


def unusable_feedback(reason: str) -> str:
    """Retry feedback contains a fixed reason, never model or document wording."""
    return (
        f"Unusable reply: {CodingError(reason)}. Return the closed JSON response only."
    )
