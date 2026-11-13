"""One decide gate re-verifies the support run once at each end (plan 23, Task 4).

`decide_assignments` used to re-verify the whole support run after each target's
vote, so its cost grew with the square of the target count, and `resolve_target`
validated the whole document again for each (claim, theme). These tests count the
module-level check bodies, `_reverify_support_run` and `_checked_bundle`, over
invented sources only (GS13). They also hold the other side: a call outside a gate
checks every time, and a refusal is never remembered as a pass.

The per-target re-check compares content digests instead (D21-34, D23-1). The last
tests hold that each vote still reads only rows equal to the checked ones, and that
a change keeps base's refusal code: changed or unreadable rows refuse as
``input_changed``.
"""

from importlib import import_module

import pytest
from earnings_themes.anchoring import Bundle
from earnings_themes.coding.records import CodingError
from earnings_themes.scope import gate
from earnings_themes.support import resolve_target, reverify_support_run
from earnings_themes.support.records import (
    CodebookReference,
    RefusedTarget,
    ResolvedInput,
    Target,
)

from .cases import (
    FixturePolicy,
    invented_bundle,
    invented_codebook,
    make_assessed_case,
    make_sources,
)

_resolve = import_module("earnings_themes.support.resolve")
_store = import_module("earnings_themes.support.store")

THREE_CLAIMS = (
    "An invented equipment claim.",
    "A second invented equipment claim.",
    "A third invented equipment claim.",
)


def count_calls(monkeypatch, module, name):
    """Count calls to one module-level function, looked up through its globals.

    The patch must not undo the ``no_network`` guards, so a test that patches more
    than once uses its own ``pytest.MonkeyPatch.context()``.
    """
    calls = []
    original = getattr(module, name)

    def counted(*args, **kwargs):
        calls.append(name)
        return original(*args, **kwargs)

    monkeypatch.setattr(module, name, counted)
    return calls


def every_target(sources):
    """Each claim crossed with each frozen theme: the targets a gate resolves."""
    book = sources.codebook
    reference = CodebookReference(
        codebook_id=book.codebook_id,
        codebook_version=book.codebook_version,
        content_hash=book.content_hash,
    )
    return tuple(
        Target(
            source_run_id=sources.stored_run.record.run_id,
            doc_id=claim.doc_id,
            claim_id=claim.claim_id,
            theme_id=theme.theme_id,
            codebook=reference,
        )
        for claim in sources.stored_run.claims
        for theme in book.themes
    )


def resolve(sources, target):
    return resolve_target(
        sources.stored_run,
        sources.bundles,
        sources.codebook,
        target,
        provenance_hash=sources.provenance_hash,
    )


def test_decide_reverifies_the_support_run_twice_at_any_size(
    assignment_case_factory,
):
    counts = {}
    for themes in (("capacity",), ("capacity", "demand")):
        case = assignment_case_factory(claims=THREE_CLAIMS, themes=themes)
        size = len(case.support.targets)
        with pytest.MonkeyPatch.context() as patch:
            calls = count_calls(patch, _store, "_reverify_support_run")
            result = case.decide(FixturePolicy(case.proposals, case.support))
        assert [row.status for row in result.decisions] == ["accepted"] * size
        counts[size] = len(calls)
    assert counts == {3: 2, 6: 2}


def test_a_gate_validates_each_bundle_once(coding_case, template, monkeypatch):
    sources = make_sources(
        coding_case.codebook,
        invented_bundle(),
        template,
        claim_texts=("An invented equipment claim.", "An invented order claim."),
    )
    targets = every_target(sources)
    assert len(targets) == 4
    assert len({t.doc_id for t in targets}) == 1
    calls = count_calls(monkeypatch, _resolve, "_checked_bundle")
    with gate():
        resolved = [resolve(sources, target) for target in targets]
    assert all(isinstance(result, ResolvedInput) for result in resolved)
    assert len(calls) == 1


def test_reverify_outside_a_gate_still_checks_each_call(assessed_case, monkeypatch):
    calls = count_calls(monkeypatch, _store, "_reverify_support_run")
    first = reverify_support_run(assessed_case.support, assessed_case.sources)
    second = reverify_support_run(assessed_case.support, assessed_case.sources)
    assert first == second == assessed_case.support.outcomes
    assert len(calls) == 2


def test_a_refused_bundle_is_checked_again_inside_a_gate(
    codebook, template, monkeypatch
):
    bundle = invented_bundle()
    sources = make_sources(invented_codebook(codebook), bundle, template)
    changed = bundle.document.model_copy(
        update={"canonical_text": "Changed invented text of the same document."}
    )
    broken = Bundle(bundle.name, changed, bundle.elements, bundle.masks)
    sources = type(sources)(
        sources.stored_run, (broken,), sources.codebook, sources.provenance_hash
    )
    target = every_target(sources)[0]
    calls = count_calls(monkeypatch, _resolve, "_checked_bundle")
    with gate():
        first = resolve(sources, target)
        second = resolve(sources, target)
    assert isinstance(first, RefusedTarget)
    assert isinstance(second, RefusedTarget)
    assert first.outcome.missing == second.outcome.missing == ("malformed_record",)
    assert len(calls) == 2


class SteppedPolicy:
    """The fixture policy, with a step run at a chosen read of ``reference`` and at
    each vote. ``decide_assignments`` reads ``reference`` once at the start, once
    before the loop, once after each vote and once at the end."""

    def __init__(self, case, *, on_read=None, on_vote=None):
        self.actual = FixturePolicy(case.proposals, case.support)
        self.on_read = on_read or {}
        self.on_vote = on_vote
        self.reads = 0
        self.voted = []

    @property
    def reference(self):
        self.reads += 1
        step = self.on_read.get(self.reads)
        if step is not None:
            step(self)
        return self.actual.reference

    def evaluate(self, view):
        self.voted.append(view.target.target_id)
        if self.on_vote is not None:
            self.on_vote(self, view)
        return self.actual.evaluate(view)


@pytest.fixture
def two_targets(proposal_job, tmp_path):
    """One claim proposed for both themes: two assessed targets in one gate."""
    proposals, _ = proposal_job.run(
        [{"theme_ids": ["capacity", "demand"], "attributes": {}}]
    )
    case = make_assessed_case(proposals, proposal_job.sources, tmp_path)
    assert len(case.support.targets) == 2
    return case


def later_rows(case, policy, table):
    """The rows of ``table`` that belong to a target not yet voted on."""
    return [
        row for row in getattr(case.support, table) if row.target_id not in policy.voted
    ]


def test_a_later_targets_rows_changed_and_restored_are_refused(two_targets):
    case = two_targets
    saved = {}

    def change(policy):
        for signal in later_rows(case, policy, "entailment"):
            saved[signal.signal_id] = (signal, signal.score)
            signal.__dict__["score"] = 0.99

    def restore(policy):
        for signal, score in saved.values():
            signal.__dict__["score"] = score

    assert all(signal.score != 0.99 for signal in case.support.entailment)
    # Read 3 follows the first vote, and read 4 follows the second one.
    policy = SteppedPolicy(case, on_read={3: change, 4: restore})
    with pytest.raises(CodingError, match="^input_changed$"):
        case.decide(policy)
    assert len(policy.voted) == 1


@pytest.mark.parametrize("write", ["trial_answer", "evidence_quote"])
def test_inconsistent_later_rows_refuse_as_input_changed(two_targets, write):
    case = two_targets

    def change(policy, view):
        if write == "trial_answer":
            for trial in later_rows(case, policy, "trials"):
                trial.__dict__["answer"] = None
        else:
            for reference in later_rows(case, policy, "evidence"):
                reference.__dict__["quote_id"] = "q-0-1"

    policy = SteppedPolicy(case, on_vote=change)
    with pytest.raises(CodingError, match="^input_changed$"):
        case.decide(policy)
    assert len(policy.voted) == 1


@pytest.mark.parametrize(
    "write", ["source_on_read", "source_on_vote", "later_proposal_on_vote"]
)
def test_an_unserializable_change_refuses_as_input_changed(two_targets, write):
    case = two_targets
    claim = case.sources.stored_run.claims[0]

    def change_source(*args):
        claim.__dict__["claim"] = object()

    def change_later_proposal(policy, view):
        for proposal in case.proposals.proposals:
            if proposal.target != view.target.target:
                proposal.__dict__["input_hash"] = object()

    if write == "source_on_read":
        policy = SteppedPolicy(case, on_read={1: change_source})
    elif write == "source_on_vote":
        policy = SteppedPolicy(case, on_vote=change_source)
    else:
        policy = SteppedPolicy(case, on_vote=change_later_proposal)
    with pytest.raises(CodingError, match="^input_changed$") as failure:
        case.decide(policy)
    assert failure.value.__cause__ is None
    assert failure.value.__suppress_context__


@pytest.mark.parametrize(
    ("table", "field"),
    [
        ("targets", "claim_hash"),
        ("outcomes", "status"),
        ("entailment", "score"),
        ("trials", "reason"),
    ],
)
def test_an_unserializable_later_support_row_keeps_its_base_code(
    two_targets, table, field
):
    """Base refused an unreadable support row from its content hash, outside the
    change mapping, so the code stays ``unexpected_error``. Only source and proposal
    digests map such a value to ``input_changed``."""
    case = two_targets

    def change(policy, view):
        for row in later_rows(case, policy, table):
            row.__dict__[field] = object()

    policy = SteppedPolicy(case, on_vote=change)
    with pytest.raises(CodingError, match="^unexpected_error$"):
        case.decide(policy)
    assert len(policy.voted) == 1


def test_a_run_id_changed_after_a_vote_and_restored_is_refused(two_targets):
    case = two_targets
    record = case.proposals.record
    run_id = record.run_id

    def change(policy):
        record.__dict__["run_id"] = "invented-other-run"

    def restore(policy):
        record.__dict__["run_id"] = run_id

    # Read 3 follows the first vote, and read 4 follows the second one.
    policy = SteppedPolicy(case, on_read={3: change, 4: restore})
    with pytest.raises(CodingError, match="^input_changed$"):
        case.decide(policy)
    assert len(policy.voted) == 1


def test_an_outcome_changed_through_its_view_after_the_vote_is_refused(two_targets):
    """The view's outcome is the gate's own copy, and the decision reads it after
    the vote. A policy that keeps the view and changes it then is refused, as a
    change during ``evaluate`` is."""
    case = two_targets
    views = []

    def keep(policy, view):
        views.append(view)

    def change(policy):
        views[0].outcome.__dict__["missing"] = ("invented_missing",)

    # Read 3 follows the first vote.
    policy = SteppedPolicy(case, on_read={3: change}, on_vote=keep)
    with pytest.raises(CodingError, match="^input_changed$"):
        case.decide(policy)
    assert len(policy.voted) == 1


def test_a_view_changed_while_its_vote_is_read_is_refused(two_targets):
    """``decision_vote`` reads a returned vote through its ``model_dump``, which a
    policy's own vote class can run. A view changed then is refused, even when the
    next ``reference`` read restores it."""
    from earnings_themes.coding.records import PolicyVote

    case = two_targets
    views = []
    saved = []

    class ChangingVote(PolicyVote):
        def model_dump(self, **kwargs):
            saved.append(views[-1].eligible_quote_ids)
            object.__setattr__(views[-1], "eligible_quote_ids", ("q-0-1",))
            return super().model_dump(**kwargs)

    def restore(policy):
        object.__setattr__(views[-1], "eligible_quote_ids", saved[-1])

    def evaluate(view):
        views.append(view)
        return ChangingVote(action="accept", supporting_quote_ids=("q-0-1",))

    # Read 3 follows the first vote.
    policy = SteppedPolicy(case, on_read={3: restore})
    policy.evaluate = evaluate
    assert all(e.quote_id != "q-0-1" for e in case.support.evidence)
    with pytest.raises(CodingError, match="^input_changed$"):
        case.decide(policy)
    assert len(views) == 1


@pytest.mark.parametrize("where", ["own_scope", "outer_scope", "outer_scope_before"])
def test_another_targets_outcome_copy_changed_during_a_vote_is_not_used(
    two_targets, where
):
    """``reverify_support_run`` gives each call its own outcome copies, as base did,
    so a policy that changes the copies it got cannot reach the ones the gate reads.
    The decisions stay those of the stored outcomes, also when an outer scope that
    holds the memo is open, and when the change is made there before the gate."""
    from earnings_themes.support.records import ReviewStatus

    case = two_targets

    def change(outcomes, voted):
        for outcome in outcomes:
            if outcome.target_id not in voted:
                outcome.__dict__["status"] = ReviewStatus.FLAGGED
                outcome.__dict__["flags"] = ("invented_flag",)

    def on_vote(policy, view):
        change(reverify_support_run(case.support, case.sources), policy.voted)

    if where == "own_scope":
        policy = SteppedPolicy(case, on_vote=on_vote)
        result = case.decide(policy)
    else:
        with gate():
            shared = reverify_support_run(case.support, case.sources)
            if where == "outer_scope_before":
                change(shared, ())
                policy = SteppedPolicy(case)
            else:
                policy = SteppedPolicy(case, on_vote=on_vote)
            result = case.decide(policy)
    stored = {row.target_id: row for row in case.support.outcomes}
    assert len(policy.voted) == 2
    assert [row.status for row in result.decisions] == ["accepted", "accepted"]
    for row in result.decisions:
        outcome = stored[row.target_id]
        assert (row.support_status, row.flags, row.missing) == (
            outcome.status,
            outcome.flags,
            outcome.missing,
        )


@pytest.mark.parametrize(
    "check",
    [
        test_a_later_targets_rows_changed_and_restored_are_refused,
        test_a_run_id_changed_after_a_vote_and_restored_is_refused,
        test_an_outcome_changed_through_its_view_after_the_vote_is_refused,
        test_a_view_changed_while_its_vote_is_read_is_refused,
    ],
    ids=["restored_rows", "restored_run_id", "outcome_through_view", "vote_read"],
)
def test_the_per_target_checks_hold_in_an_outer_scope(two_targets, check):
    """The same refusals, inside an outer scope that already holds the memo."""
    with gate():
        reverify_support_run(two_targets.support, two_targets.sources)
        check(two_targets)


def test_each_reverify_call_in_a_gate_gets_its_own_outcome_copies(
    assessed_case, monkeypatch
):
    calls = count_calls(monkeypatch, _store, "_reverify_support_run")
    with gate():
        first = reverify_support_run(assessed_case.support, assessed_case.sources)
        second = reverify_support_run(assessed_case.support, assessed_case.sources)
    assert len(calls) == 1
    assert first == second == assessed_case.support.outcomes
    assert all(a is not b for a, b in zip(first, second, strict=True))


def test_every_outcome_field_is_immutable(assessed_case):
    """A shallow ``model_copy`` keeps copies apart only if no field holds a mutable
    value, such as a list or a dict, that the copies would share."""
    from typing import Literal, get_args, get_origin

    from earnings_themes.support.records import ReviewOutcome

    def immutable(annotation) -> bool:
        if get_origin(annotation) is Literal:
            return all(isinstance(arg, int | str) for arg in get_args(annotation))
        if get_origin(annotation) is tuple:
            return True
        return isinstance(annotation, type) and issubclass(annotation, int | str)

    for name, field in ReviewOutcome.model_fields.items():
        assert immutable(field.annotation), name
    for outcome in assessed_case.support.outcomes:
        for name in ReviewOutcome.model_fields:
            value = getattr(outcome, name)
            assert isinstance(value, int | str | tuple), name
            if isinstance(value, tuple):
                assert all(isinstance(item, str) for item in value), name


def test_an_outcome_copy_dumps_as_its_stored_row(assessed_case):
    """The per-target check compares each outcome copy with its stored row's digest,
    so the two must dump alike, for a run read back and for one built in memory."""
    for support in (assessed_case.support, _store._stored(assessed_case.result)):
        copies = reverify_support_run(support, assessed_case.sources)
        assert [o.model_dump(mode="json") for o in copies] == [
            o.model_dump(mode="json") for o in support.outcomes
        ]


def test_a_support_changed_in_an_outer_scope_before_decide_is_refused(two_targets):
    """An outer scope checked the run, and then the run changed in place into
    another valid run: the later target is now ``flagged``. The scope's outcomes
    are stale, so the gate refuses rather than decide on them (D21-34)."""
    from earnings_themes.support.assess import derive_outcome
    from earnings_themes.support.records import ReviewOutcome
    from earnings_themes.support.run import accounting

    case = two_targets
    support = case.support
    later = support.targets[1]
    policy = SteppedPolicy(case)
    with gate():
        reverify_support_run(support, case.sources)
        trial_ids = {
            t.trial_id for t in support.trials if t.target_id == later.target_id
        }
        for row in (*support.trials, *support.attempts):
            if row.trial_id in trial_ids and row.answer is not None:
                row.answer.__dict__["claim_support"] = "unsupported"
        outcome = derive_outcome(
            later.target_id,
            tuple(s for s in support.entailment if s.target_id == later.target_id),
            tuple(t for t in support.trials if t.target_id == later.target_id),
            later.evidence_ids,
        )
        assert outcome.status == "flagged"
        row = next(o for o in support.outcomes if o.target_id == later.target_id)
        for name in ReviewOutcome.model_fields:
            row.__dict__[name] = getattr(outcome, name)
        for key, value in accounting(
            _store._assessments(support), support.usage
        ).items():
            support.record.__dict__[key] = value
        with gate(fresh=True):
            fresh = reverify_support_run(support, case.sources)
        assert {o.target_id: o.status for o in fresh}[later.target_id] == "flagged"
        with pytest.raises(CodingError, match="^input_changed$"):
            case.decide(policy)
