"""One decide gate re-verifies the support run once at each end (plan 23, Task 4).

`decide_assignments` used to re-verify the whole support run after each target's
vote, so its cost grew with the square of the target count, and `resolve_target`
validated the whole document again for each (claim, theme). These tests count the
module-level check bodies, `_reverify_support_run` and `_checked_bundle`, over
invented sources only (GS13). They also hold the other side: a call outside a gate
checks every time, and a refusal is never remembered as a pass.
"""

from importlib import import_module

import pytest
from earnings_themes.anchoring import Bundle
from earnings_themes.scope import gate
from earnings_themes.support import resolve_target, reverify_support_run
from earnings_themes.support.records import (
    CodebookReference,
    RefusedTarget,
    ResolvedInput,
    Target,
)

from .cases import FixturePolicy, invented_bundle, invented_codebook, make_sources

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
