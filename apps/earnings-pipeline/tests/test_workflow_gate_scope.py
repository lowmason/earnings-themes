"""A recorded deviation in the workflow's consuming gate (plan 23, Task 6).

The workflow checks the inputs once, then builds one evidence view per quote in
the same gate. Invented text only (GS13).
"""

import importlib
from dataclasses import replace

import pytest
from earnings_pipeline.evidence_views import make_evidence_view
from earnings_themes.analysis import AnalysisError, reverify_analysis_inputs
from earnings_themes.scope import gate

cases = importlib.import_module("packages.earnings-themes.tests.analysis.cases")
fixtures = importlib.import_module("packages.earnings-themes.tests.conftest")
probes = importlib.import_module(
    "packages.earnings-themes.tests.analysis.test_gate_scope"
)


def test_recorded_deviation_raw_snapshot_change_in_the_workflow_gate(
    tmp_path, monkeypatch
):
    # RECORDED DEVIATION (controller's ruling, plan 23 Task 6 review round 1,
    # Important 2). A policy changes the caller's raw snapshot bytes on its last
    # read in the gate's first check. Base refused input_changed later in the
    # gate, at the view's raw-snapshot compare. Now the check's end compare sees
    # the change, and its fresh check refuses storage_corrupt (the snapshot no
    # longer matches its artifact). Both refuse before any write. In
    # write_analysis_run both builds refuse storage_corrupt. The ruling accepts
    # this difference and forbids codes that depend on the gate.
    inputs = cases.make_inputs(
        fixtures.codebook.__wrapped__(),
        fixtures.template.__wrapped__(),
        tmp_path / "invented",
    )
    snapshot = inputs.raw_snapshots[0]
    policy = probes.LastReadPolicy(
        inputs.assignment_policy,
        probes.reads_per_check(inputs),
        lambda: object.__setattr__(snapshot, "data", snapshot.data + b"!"),
        wanted=probes.first_check,
    )
    probes.watch_checks(monkeypatch, policy)
    changed = replace(inputs, assignment_policy=policy)
    with pytest.raises(AnalysisError, match="^storage_corrupt$"), gate():
        bound = reverify_analysis_inputs(changed)
        for quote in changed.sources.stored_run.quotes:
            make_evidence_view(
                bound,
                quote.span.doc_id,
                quote.quote_id,
                audience="local",
                raw_snapshot=next(
                    s for s in changed.raw_snapshots if s.doc_id == quote.span.doc_id
                ),
            )
    assert policy.fired
