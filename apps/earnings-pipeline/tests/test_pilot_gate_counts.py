"""One pilot run checks each input once per gate (plan 23, Task 6).

Task 1's tiny ``make_pass`` and ``make_run`` (replay, train) run over invented text
only (GS13). The test counts the module-level check bodies through their modules'
globals while ``make_run`` runs. Before plan 23 that run called
``_proposal_support_inputs`` 67 times, swept the raw caches
(``_cache_verification``) 192 times and ran the analysis check
(``_reverify_analysis_inputs``) 64 times. Plan 23's Task 4 already cut the
support check (``_reverify_support_run``) from 473 to 333. Each spec-named gate
still checks in full (D21-34). Only a repeat inside one gate reuses the gate's
first check (D23-1).
"""

import importlib
from collections import Counter

import pytest
from earnings_themes.split import Partition

workflow = importlib.import_module("apps.earnings-pipeline.tests.test_pilot_workflow")

BODIES = (
    ("earnings_themes.coding.decide", "_proposal_support_inputs"),
    ("earnings_themes.analysis.consume", "_cache_verification"),
    ("earnings_themes.analysis.consume", "_reverify_analysis_inputs"),
    ("earnings_themes.support.store", "_reverify_support_run"),
)
# Plan 23's bounds were 12, 8, 8 and 30. The sweep count is 12, not 8 or less.
# Each full check sweeps before the policy runs and again after its last policy
# read. A memo of that last sweep would hide a cache change made on that read
# (packages/earnings-themes/tests/analysis/test_gate_scope.py). The analysis
# checks are 6 gates: the workflow's consuming gate, write_analysis_run,
# reverify_analysis_run, and write_theme_report's own check plus its two
# read-back gates, which are fresh.
EXPECTED = {
    # 3 before analysis (finalize_coding's decide, the coding write's re-check and
    # the workflow's re-check), plus one decide per full analysis check.
    "_proposal_support_inputs": 3 + 6,
    # 2 sweeps for each full analysis check. The sweep after the votes reuses the
    # first, because the cache objects and the raw bindings did not change.
    "_cache_verification": 2 * 6,
    # One full check for each analysis gate.
    "_reverify_analysis_inputs": 6,
    # 13 before analysis (support write and re-check, finalize_coding, the coding
    # write and re-check), plus 2 per full analysis check: one in the gate's scope
    # and one in decide's fresh end check.
    "_reverify_support_run": 13 + 2 * 6,
}


def now():
    return workflow.cases.NOW


@pytest.mark.parametrize(
    "none", [pytest.param(False, id="selected"), pytest.param(True, id="none")]
)
def test_one_pilot_run_counts_its_gates(tmp_path, none):
    from earnings_pipeline.pilot_workflow import load_pass, make_pass, make_run

    config, _ = workflow.seed_case(tmp_path, seed=False, review=True)
    rt = workflow.runtime(config, [])
    passed = make_pass(
        config,
        rt,
        rt.scorer,
        partition=Partition.TRAIN,
        directory=tmp_path / "data/runs/pilot/train/pass",
        fresh=None,
        support_ready=lambda: None,
        now=now,
    )
    loaded = load_pass(config, passed)
    artifact = workflow.bound_artifact(config, loaded, none=none)
    calls = Counter()
    with pytest.MonkeyPatch.context() as patch:
        for module_name, name in BODIES:
            module = importlib.import_module(module_name)
            original = getattr(module, name)

            def counted(*args, _original=original, _name=name, **kwargs):
                calls[_name] += 1
                return _original(*args, **kwargs)

            patch.setattr(module, name, counted)
        record = make_run(
            config,
            loaded,
            artifact,
            directory=tmp_path / "data/runs/pilot/train/run",
            now=now,
        )
    assert record.fresh is None
    assert dict(calls) == EXPECTED
