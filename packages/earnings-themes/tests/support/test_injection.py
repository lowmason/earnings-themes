"""Hostile invented judge replies cannot execute or change frozen inputs."""

import pytest
from earnings_core import digest

from . import cases
from .test_assess import assess
from .test_prompt import policy as policy  # noqa: PLC0414


@pytest.mark.parametrize(
    "kind",
    ["tool", "text", "claim", "definition", "theme", "ids", "accepted", "bypass"],
)
def test_hostile_reply_is_unusable_and_cannot_mutate(
    codebook, scorer, panel, policy, allowance, tmp_path, no_network, kind
):
    resolved = cases.resolved_case(*cases.injection_case(codebook))
    before = digest(
        {
            "claim": resolved.claim,
            "run": resolved.sources.stored_run.record.model_dump(mode="json"),
            "book": resolved.sources.codebook.model_dump(mode="json"),
            "document": resolved.sources.bundles[0].document.model_dump(mode="json"),
        }
    )
    for judge in panel:
        judge.script = cases.hostile_reply(kind)
    result = assess(resolved, scorer, panel, policy, allowance, tmp_path)
    after = digest(
        {
            "claim": resolved.claim,
            "run": resolved.sources.stored_run.record.model_dump(mode="json"),
            "book": resolved.sources.codebook.model_dump(mode="json"),
            "document": resolved.sources.bundles[0].document.model_dump(mode="json"),
        }
    )
    diagnostic = (
        before == after,
        result.outcome.status,
        len(result.attempts),
        all(a.answer is None for a in result.attempts),
        no_network,
    )
    assert diagnostic == (True, "incomplete", 8, True, [])
    assert all(a.raw_ref is not None for a in result.attempts)
    assert not hasattr(result.outcome, "accepted")
