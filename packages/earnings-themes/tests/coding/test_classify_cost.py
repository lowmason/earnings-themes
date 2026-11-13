"""One classification gate checks each claim's bundle once (plan 23, Task 5).

`propose_run` resolves each claim for every approved theme, and `classify_claim`
checks that input again at each request step. Each `resolve_target` validated the
whole document anew, so one claim ran it about 74 times. These tests count the
module-level check body, `_checked_bundle`, over invented sources only (GS13).
`propose_run` opens a gate for its claims' resolution and one for its final checks,
and `classify_claim` opens one for each claim. Each gate checks a bundle once.
"""

from importlib import import_module

import pytest

from .cases import invented_bundle, make_proposal_job, make_sources
from .test_decide_cost import count_calls

_resolve = import_module("earnings_themes.support.resolve")

THREE_CLAIMS = (
    "An invented equipment claim.",
    "A second invented equipment claim.",
    "A third invented equipment claim.",
)


def test_each_claim_checks_its_bundle_once(
    coding_case, template, coding_policy, classifier_identity, tmp_path
):
    sources = make_sources(
        coding_case.codebook,
        invented_bundle(),
        template,
        claim_texts=THREE_CLAIMS,
    )
    assert len(sources.stored_run.claims) == 3
    assert len(sources.codebook.themes) == 2
    assert len(sources.bundles) == 1
    job = make_proposal_job(sources, coding_policy, classifier_identity, tmp_path)
    reply = {"theme_ids": ["capacity"], "attributes": {}}
    live, live_calls = job.run([reply] * 3)
    assert live_calls == 3
    with pytest.MonkeyPatch.context() as patch:
        calls = count_calls(patch, _resolve, "_checked_bundle")
        replay, replay_calls = job.run([], "replay")
    assert replay_calls == 0
    assert replay.proposals == live.proposals
    assert len(replay.proposals) == 3
    # The gate before the loop, one gate for each claim, and the gate after the loop.
    assert len(calls) == 1 + 3 + 1
