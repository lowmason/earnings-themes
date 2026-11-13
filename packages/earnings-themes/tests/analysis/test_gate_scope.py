"""A gate's repeated checks reuse its first check, never a stale pass (plan 23, Task 6).

Inside one analysis gate, a repeated ``reverify_analysis_inputs`` reuses the gate's
first full check (D23-1). A bound policy is external code, and its ``reference``
property runs inside each full check, the last time after the check derived the
caller's inputs again. These tests change an input on exactly that last read of
the gate's first full check, and leave it changed. Base refused each change before
publication: a later full check in the same gate saw a changed input, and the
check's own last cache sweep saw a changed cache file. The refusal code and the
absence of written files must stay (D21-34): only the moment may move, to the end
of the gate. Invented text only (GS13).
"""

from dataclasses import replace
from importlib import import_module

import pytest
from earnings_themes.analysis import AnalysisError, build_analysis

consume = import_module("earnings_themes.analysis.consume")
store = import_module("earnings_themes.analysis.store")


class LastReadPolicy:
    """The real policy, plus one action on the last ``reference`` read of a chosen
    full check. ``per_check`` is the number of reads in one full check. A test may
    set ``context`` (for example, which read-back gate runs), and ``wanted`` gets
    the context and the number of full checks that started in it so far."""

    def __init__(self, actual, per_check, action, wanted):
        self.actual = actual
        self.per_check = per_check
        self.action = action
        self.wanted = wanted
        self.context = None
        self.counts = {}
        self.reads = 0
        self.armed = False
        self.fired = False

    def enter_check(self):
        self.counts[self.context] = self.counts.get(self.context, 0) + 1
        self.reads = 0
        self.armed = not self.fired and self.wanted(
            self.context, self.counts[self.context]
        )

    @property
    def reference(self):
        self.reads += 1
        if self.armed and self.reads == self.per_check:
            self.armed = False
            self.fired = True
            self.action()
        return self.actual.reference

    def evaluate(self, view):
        return self.actual.evaluate(view)


class CountingPolicy:
    def __init__(self, actual):
        self.actual = actual
        self.reads = 0

    @property
    def reference(self):
        self.reads += 1
        return self.actual.reference

    def evaluate(self, view):
        return self.actual.evaluate(view)


def reads_per_check(inputs):
    """The ``reference`` reads of one full check, outside any other gate."""
    counting = CountingPolicy(inputs.assignment_policy)
    consume.reverify_analysis_inputs(replace(inputs, assignment_policy=counting))
    assert counting.reads > 3
    return counting.reads


def watch_checks(monkeypatch, policy):
    """Tell the policy each time a full check of the inputs starts."""
    original = consume._reverify_analysis_inputs

    def watched(inputs):
        policy.enter_check()
        return original(inputs)

    monkeypatch.setattr(consume, "_reverify_analysis_inputs", watched)


def first_check(context, number):
    return number == 1


def change_publisher(inputs):
    return lambda: object.__setattr__(
        inputs.metadata[0], "publisher", "Invented changed publisher"
    )


def tamper_cache(inputs, root):
    path = root / "support-cache" / inputs.support.attempts[0].raw_ref
    return lambda: path.write_bytes(b'{"invented":"cache tamper"}')


@pytest.mark.parametrize("change", ["publisher", "cache"])
def test_a_change_on_the_last_policy_read_refuses_before_writes(
    analysis_input_factory, tmp_path, monkeypatch, change
):
    inputs, root = analysis_input_factory(caches=True)
    result = build_analysis(inputs, inputs.analysis_policy, None)
    action = (
        change_publisher(inputs)
        if change == "publisher"
        else tamper_cache(inputs, root)
    )
    policy = LastReadPolicy(
        inputs.assignment_policy,
        reads_per_check(inputs),
        action,
        wanted=first_check,
    )
    watch_checks(monkeypatch, policy)
    expected = "input_changed" if change == "publisher" else "storage_corrupt"
    with pytest.raises(AnalysisError, match=f"^{expected}$"):
        store.write_analysis_run(
            tmp_path / "changed",
            result,
            replace(inputs, assignment_policy=policy),
            inputs.analysis_policy,
            None,
            evidence=(),
        )
    assert policy.fired
    assert not (tmp_path / "changed").exists()


@pytest.mark.parametrize("change", ["publisher", "cache"])
def test_a_change_on_the_last_policy_read_fails_the_read_back(
    analysis_input_factory, tmp_path, monkeypatch, change
):
    inputs, root = analysis_input_factory(caches=True)
    result = build_analysis(inputs, inputs.analysis_policy, None)
    store.write_analysis_run(
        tmp_path / "analysis", result, inputs, inputs.analysis_policy, None, ()
    )
    stored = store.read_analysis_run(tmp_path / "analysis")
    action = (
        change_publisher(inputs)
        if change == "publisher"
        else tamper_cache(inputs, root)
    )
    policy = LastReadPolicy(
        inputs.assignment_policy,
        reads_per_check(inputs),
        action,
        wanted=first_check,
    )
    watch_checks(monkeypatch, policy)
    with pytest.raises(AnalysisError, match="^input_changed$"):
        store.reverify_analysis_run(
            stored,
            replace(inputs, assignment_policy=policy),
            inputs.analysis_policy,
            None,
        )
    assert policy.fired


class BindingChangePolicy:
    """The real policy; its first vote changes one judge raw-cache binding of the
    caller's support record and leaves it changed."""

    def __init__(self, actual, support):
        self.actual = actual
        self.support = support
        self.changed = False

    @property
    def reference(self):
        return self.actual.reference

    def evaluate(self, view):
        if not self.changed:
            self.changed = True
            record = self.support.record
            hashes = list(record.artifact_hashes)
            index = next(
                i for i, (name, _) in enumerate(hashes) if name.startswith("raw/")
            )
            hashes[index] = (hashes[index][0], "0" * 64)
            object.__setattr__(record, "artifact_hashes", tuple(hashes))
        return self.actual.evaluate(view)


def test_a_raw_binding_changed_during_a_vote_stays_storage_corrupt(
    analysis_input_factory,
):
    # The sweep after the votes reads the caller's changed binding through the
    # cache's reader, so the refusal is the cache's, before any binding compare.
    inputs, _ = analysis_input_factory(caches=True)
    policy = BindingChangePolicy(inputs.assignment_policy, inputs.support)
    with pytest.raises(AnalysisError, match="^storage_corrupt$"):
        consume.reverify_analysis_inputs(replace(inputs, assignment_policy=policy))
    assert policy.changed
