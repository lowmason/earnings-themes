"""Same content and roles, explicit source boundaries; all examples are invented."""

import json
from dataclasses import replace
from pathlib import Path

import pytest
from earnings_core import sha256_hex
from earnings_themes.extraction.records import Parameters
from earnings_themes.support import prompt
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import SupportPolicy

from .cases import resolved_case


@pytest.fixture
def policy():
    text = (
        Path(__file__).resolve().parents[4] / "prompts/support/judge-1.md"
    ).read_text()
    return SupportPolicy(
        support_version="semantic-support/1",
        prompt_text=text,
        prompt_hash=sha256_hex(text.encode()),
        parameters=Parameters(),
    )


def test_order_changes_blocks_only(case, policy):
    resolved = resolved_case(*case)
    first = prompt.render_judge(resolved, policy, "evidence_first")
    second = prompt.render_judge(resolved, policy, "claim_theme_first")
    assert first.messages[0] == second.messages[0]
    assert first.reply_schema == second.reply_schema
    assert first.parameters == second.parameters
    a = json.loads(first.messages[1].content)
    b = json.loads(second.messages[1].content)
    assert a[0] == b[1] and a[1] == b[0]
    assert [q["quote_id"] for q in a[0]["quoted_evidence"]] == [
        r.quote_id for r in resolved.evidence
    ]
    assert a[1]["claim"] == resolved.claim
    assert "examples" not in a[1]["frozen_theme"]
    assert set(first.subject.model_dump()) == {
        "target_id",
        "input_hash",
        "codebook_hash",
        "presentation",
        "prompt_hash",
        "schema_hash",
        "support_version",
        "validator_version",
    }
    for forbidden in (
        "extractor",
        "rationale",
        "entailment",
        "previous_trial",
        "window_id",
    ):
        assert forbidden not in first.model_dump_json()


def test_context_is_separately_tagged(one_quote, policy):
    request = prompt.render_judge(one_quote, policy, "evidence_first")
    evidence, _ = json.loads(request.messages[1].content)
    assert (
        "INVENTED_CONTEXT_ONLY_ASSERTION" not in evidence["quoted_evidence"][0]["text"]
    )
    assert any(
        "INVENTED_CONTEXT_ONLY_ASSERTION" in c["text"]
        for c in evidence["attribution_context"]
    )
    assert request.messages[0].content == policy.prompt_text


@pytest.mark.parametrize("change", ["prompt", "claim", "evidence", "presentation"])
def test_changed_inputs_refuse(case, policy, change):
    resolved = resolved_case(*case)
    presentation = "evidence_first"
    if change == "prompt":
        policy = policy.model_copy(update={"prompt_hash": "0" * 64})
    elif change == "claim":
        resolved = replace(resolved, claim="Invented tampering.")
    elif change == "evidence":
        resolved = replace(
            resolved, evidence=(resolved.evidence[0].model_copy(update={"start": 0}),)
        )
    else:
        presentation = "unknown"
    with pytest.raises(SupportError):
        prompt.render_judge(resolved, policy, presentation)
