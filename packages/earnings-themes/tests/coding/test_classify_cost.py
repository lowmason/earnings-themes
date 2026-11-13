"""One classification gate checks each claim's bundle once (plan 23, Task 5).

`propose_run` resolves each claim for every approved theme, and `classify_claim`
checks that input again at each request step. Each `resolve_target` validated the
whole document anew, so one claim ran it about 74 times. These tests count the
module-level check body, `_checked_bundle`, over invented sources only (GS13).
`propose_run` opens a gate for its claims' resolution and two for its final checks,
and `classify_claim` opens one for each claim. Each gate checks a bundle once.

The last tests hold that a change made in place to a bundle while the final checks
run is refused, not published. Those checks are the last before publication, so
no later gate would catch it (D21-34).
"""

from importlib import import_module

import pytest
from earnings_themes.coding.cache import CodingCache
from earnings_themes.coding.records import CodingError
from earnings_themes.extraction.adapters import ModelReply

from .cases import invented_bundle, make_proposal_job, make_sources
from .test_decide_cost import count_calls
from .test_run import EMPTY, run_with

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
    # The gate before the loop, one gate for each claim, and two gates after the
    # loop. The second one opens before the final identity read, so its bundle
    # check runs after that external code and is not a hit from the first (D21-34).
    assert len(calls) == 1 + 3 + 2


@pytest.mark.parametrize("read", ["identity", "cache"])
def test_a_bundle_change_during_the_final_checks_is_refused(
    read, coding_case, coding_policy, classifier_identity, tmp_path, monkeypatch
):
    """A change that stays is refused as ``input_changed`` and nothing is published.

    It is made after the first final check has checked the bundle: during the final
    identity read, or during the final raw-cache read that precedes it.
    """
    document = coding_case.bundles[0].document

    def change_bundle():
        object.__setattr__(document, "canonical_text", document.canonical_text + " x")

    class CallbackClassifier:
        def __init__(self):
            self.requests = []
            self.armed = self.changed = False

        @property
        def identity(self):
            if self.armed:
                self.armed = False
                self.changed = True
                change_bundle()
            return classifier_identity

        def count_tokens(self, request):
            return 5

        def complete(self, request):
            self.requests.append(request)
            return ModelReply(text=EMPTY, model=classifier_identity.runtime.model_id)

    def execute(directory, last_read=None):
        classifier = CallbackClassifier()
        cache = CodingCache(directory, "live")
        original_get = cache.get
        reads = []

        def get(request, identity):
            entry = original_get(request, identity)
            reads.append(entry)
            if len(reads) == last_read:
                if read == "identity":
                    classifier.armed = True
                else:
                    classifier.changed = True
                    change_bundle()
            return entry

        monkeypatch.setattr(cache, "get", get)
        return (
            classifier,
            reads,
            lambda: run_with(coding_case, coding_policy, classifier, cache),
        )

    _, baseline_reads, baseline = execute(tmp_path / "baseline")
    baseline()
    # The last raw-cache read is the one in the final checks.
    classifier, _, changed = execute(tmp_path / "changed", len(baseline_reads))
    with pytest.raises(CodingError, match="^input_changed$"):
        changed()
    assert classifier.changed
    assert len(classifier.requests) == 1
