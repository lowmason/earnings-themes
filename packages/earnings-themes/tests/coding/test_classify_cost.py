"""One classification gate checks each claim's bundle once (plan 23, Task 5).

`propose_run` resolves each claim for every approved theme, and `classify_claim`
checks that input again at each request step. Each `resolve_target` validated the
whole document anew, so one claim ran it about 74 times. These tests count the
module-level check body, `_checked_bundle`, over invented sources only (GS13).
`propose_run` opens a gate for its claims' resolution and two for its final checks.
`classify_claim` opens one for each claim, and a second, fresh one for the claim's
last check. Each gate checks a bundle once.

Two tests hold that a change made in place to a bundle is refused as ``input_changed``,
the code that every check gave before the memo (D21-34). One is a change made while
the final checks run, which are the last before publication, so no later gate would
catch it. The other is a change that stays after a claim other than the last.
"""

from importlib import import_module

import pytest
from earnings_themes.coding.adapters import ScriptedClassifier
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
TWO_CLAIMS = THREE_CLAIMS[:2]


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
    # The gate before the loop, two gates for each claim, and two gates after the
    # loop. A claim's second gate holds its last check. It opens before the final
    # identity read, so its bundle check runs after that external code and is not a
    # hit from the claim's first gate. The last gate before publication is the same
    # (D21-34). The plan's first count was 5, then 6, and is now 9.
    assert len(calls) == 1 + 3 * 2 + 2


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


@pytest.mark.parametrize("memo", ["on", "off"])
@pytest.mark.parametrize("change", ["text", "element"])
def test_a_bundle_change_that_stays_is_refused_as_input_changed_after_its_claim(
    change,
    memo,
    coding_case,
    template,
    coding_policy,
    classifier_identity,
    tmp_path,
):
    """Claim 1's reply changes the bundle outside the quoted spans, and the change
    stays. The run refuses as ``input_changed`` after that one request, with the
    memo on or off. Without a full check at the end of claim 1, claim 2's first
    check would refuse it with the resolver's own reason (``malformed_record`` for
    changed text), which tells a reader that a stored record is malformed."""
    sources = make_sources(
        coding_case.codebook, invented_bundle(), template, claim_texts=TWO_CLAIMS
    )
    bundle = sources.bundles[0]

    def complete(request):
        if change == "text":
            document = bundle.document
            object.__setattr__(
                document, "canonical_text", document.canonical_text + " x"
            )
        else:
            element = bundle.elements[0]
            shorter = element.span.model_copy(update={"end": element.span.end - 1})
            object.__setattr__(element, "span", shorter)
        return ModelReply(text=EMPTY, model=classifier_identity.runtime.model_id)

    classifier = ScriptedClassifier(complete, lambda request: 5, classifier_identity)
    with pytest.MonkeyPatch.context() as patch:
        if memo == "off":
            patch.setattr(_resolve, "once", lambda kind, objects, compute: compute())
        with pytest.raises(CodingError, match="^input_changed$"):
            run_with(sources, coding_policy, classifier, CodingCache(tmp_path, "live"))
    assert len(classifier.requests) == 1
