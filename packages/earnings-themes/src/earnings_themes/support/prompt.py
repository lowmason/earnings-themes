"""Reconstruct separate canonical views; joint scorer input contains evidence only."""

from earnings_core import (
    VALIDATOR_VERSION,
    CanonicalDocument,
    canonical_json,
    digest,
    sha256_hex,
)

from earnings_themes.extraction.adapters import Message
from earnings_themes.support.judges import JudgeRequest, JudgeSubject
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import (
    ContextReference,
    EvidenceReference,
    JudgeAnswer,
    Presentation,
    RefusedTarget,
    ResolvedInput,
    SupportPolicy,
)
from earnings_themes.support.resolve import _validated, reverify_input


def _canonical_slice(
    input: ResolvedInput, ref: EvidenceReference | ContextReference
) -> str:
    try:
        if type(ref) is EvidenceReference:
            retained = input.evidence
        elif type(ref) is ContextReference:
            retained = input.contexts
        else:
            raise SupportError("input_changed")
        ref = _validated(ref, type(ref))
        if ref not in retained:
            raise SupportError("input_changed")
        if ref.target_id != input.record.target_id:
            raise SupportError("input_changed")
        bundles = [b for b in input.sources.bundles if b.document.doc_id == ref.doc_id]
        if len(bundles) != 1:
            raise SupportError("input_changed")
        bundle = bundles[0]
        document = _validated(bundle.document, CanonicalDocument)
        elements = [e for e in bundle.elements if e.element_id == ref.element_id]
        if (
            document.canonical_hash != ref.canonical_hash
            or len(elements) != 1
            or not (0 <= ref.start < ref.end <= len(document.canonical_text))
            or elements[0].doc_id != ref.doc_id
            or not (
                elements[0].span.start <= ref.start < ref.end <= elements[0].span.end
            )
        ):
            raise SupportError("input_changed")
        text = document.canonical_text[ref.start : ref.end]
        if sha256_hex(text.encode("utf-8")) != ref.text_hash:
            raise SupportError("input_changed")
        return text
    except (SupportError, AttributeError, TypeError, ValueError, OverflowError):
        raise SupportError("input_changed") from None


def evidence_text(input: ResolvedInput, ref: EvidenceReference) -> str:
    """Materialize the original quote slice, never its containing context."""
    if type(ref) is not EvidenceReference:
        raise SupportError("input_changed")
    return _canonical_slice(input, ref)


def context_text(input: ResolvedInput, ref: ContextReference) -> str:
    """Materialize a separately tagged attribution block or heading."""
    if type(ref) is not ContextReference:
        raise SupportError("input_changed")
    return _canonical_slice(input, ref)


def joint_premise(input: ResolvedInput) -> str:
    """Preserve noncontiguous quotes as individually bounded document-order passages."""
    if len(input.evidence) == 1:
        return evidence_text(input, input.evidence[0])
    return "\n\n".join(
        f"PASSAGE {index} [{ref.quote_id}]\n{evidence_text(input, ref)}\nEND PASSAGE {index}"
        for index, ref in enumerate(input.evidence, 1)
    )


def render_judge(
    input: ResolvedInput, policy: SupportPolicy, presentation: Presentation | str
) -> JudgeRequest:
    """Reverify evidence and render identical JSON blocks in two independent orders."""
    checked = reverify_input(input)
    if isinstance(checked, RefusedTarget):
        raise SupportError(checked.outcome.missing[0])
    policy = _validated(policy, SupportPolicy)
    if sha256_hex(policy.prompt_text.encode("utf-8")) != policy.prompt_hash:
        raise SupportError("input_changed")
    try:
        order = Presentation(presentation)
    except (ValueError, TypeError):
        raise SupportError("malformed_record") from None
    evidence = {
        "tag": "quoted_evidence_and_context",
        "quoted_evidence": [
            {**ref.model_dump(mode="json"), "text": evidence_text(checked, ref)}
            for ref in checked.evidence
        ],
        "attribution_context": [
            {**ref.model_dump(mode="json"), "text": context_text(checked, ref)}
            for ref in checked.contexts
        ],
    }
    claim = {
        "tag": "claim_and_frozen_theme",
        "claim": checked.claim,
        "frozen_theme": checked.record.theme.model_dump(mode="json"),
    }
    blocks = (
        [evidence, claim] if order == Presentation.EVIDENCE_FIRST else [claim, evidence]
    )
    schema = JudgeAnswer.model_json_schema()
    return JudgeRequest(
        messages=(
            Message(role="system", content=policy.prompt_text),
            Message(role="user", content=canonical_json(blocks).decode("utf-8")),
        ),
        reply_schema=schema,
        parameters=policy.parameters,
        subject=JudgeSubject(
            target_id=checked.record.target_id,
            input_hash=checked.record.input_hash,
            codebook_hash=checked.record.target.codebook.content_hash,
            presentation=order,
            prompt_hash=policy.prompt_hash,
            schema_hash=digest(schema),
            validator_version=VALIDATOR_VERSION,
        ),
    )
