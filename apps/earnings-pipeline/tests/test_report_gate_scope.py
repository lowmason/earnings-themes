"""A report's checks keep base's refusals for a change on a policy read (plan 23).

``write_theme_report`` runs the read-back gate (``reverify_analysis_run``) twice and
checks the current inputs for its views once, in its own scope. Each of those
starts with a full check whose last ``reference`` read runs after its last copy of
the caller's inputs. A change made there and left in place must refuse with base's
code, before any report file exists. The read-back gate turns every refusal into
``input_changed``. The report keeps the code of its own checks, so a cache change
on the views check stays ``storage_corrupt``. Invented text only (GS13).
"""

import importlib
from dataclasses import replace

import pytest
from earnings_themes.analysis import AnalysisError

report_cases = importlib.import_module("apps.earnings-pipeline.tests.test_theme_report")
probes = importlib.import_module(
    "packages.earnings-themes.tests.analysis.test_gate_scope"
)
theme_report = importlib.import_module("earnings_pipeline.theme_report")

EXPECTED = {
    ("cache", ("read-back", 1)): "input_changed",
    ("cache", "report"): "storage_corrupt",
    ("cache", ("read-back", 2)): "input_changed",
    ("publisher", ("read-back", 1)): "input_changed",
    ("publisher", "report"): "input_changed",
    ("publisher", ("read-back", 2)): "input_changed",
}


@pytest.mark.parametrize(("change", "place"), list(EXPECTED), ids=str)
def test_a_change_on_the_last_policy_read_refuses_the_report(
    tmp_path, monkeypatch, change, place
):
    inputs, families, views, stored = report_cases.setup_case(tmp_path, caches=True)
    root = tmp_path / "invented"
    action = (
        probes.change_publisher(inputs)
        if change == "publisher"
        else probes.tamper_cache(inputs, root)
    )
    policy = probes.LastReadPolicy(
        inputs.assignment_policy,
        probes.reads_per_check(inputs),
        action,
        wanted=lambda context, number: (context, number) == (place, 1),
    )
    policy.context = "report"
    probes.watch_checks(monkeypatch, policy)
    original = theme_report.reverify_analysis_run
    started = []

    def read_back(*args, **kwargs):
        started.append(True)
        policy.context = ("read-back", len(started))
        try:
            return original(*args, **kwargs)
        finally:
            policy.context = "report"

    monkeypatch.setattr(theme_report, "reverify_analysis_run", read_back)
    with pytest.raises(AnalysisError, match=f"^{EXPECTED[(change, place)]}$"):
        theme_report.write_theme_report(
            tmp_path / "report",
            stored,
            replace(inputs, assignment_policy=policy),
            inputs.analysis_policy,
            families,
            views,
            audience="export",
        )
    assert policy.fired
    assert not (tmp_path / "report").exists()


@pytest.mark.parametrize(("change", "place"), list(EXPECTED), ids=str)
def test_a_change_during_a_vote_refuses_the_report(
    tmp_path, monkeypatch, change, place
):
    # Base's second sweep, after the votes, saw a cache change made there. The
    # check's last sweep, after the policy's last read, must see it now.
    inputs, families, views, stored = report_cases.setup_case(tmp_path, caches=True)
    root = tmp_path / "invented"
    action = (
        probes.change_publisher(inputs)
        if change == "publisher"
        else probes.tamper_cache(inputs, root)
    )
    policy = probes.VotePolicy(
        inputs.assignment_policy,
        action,
        wanted=lambda context, number: (context, number) == (place, 1),
    )
    policy.context = "report"
    probes.watch_checks(monkeypatch, policy)
    original = theme_report.reverify_analysis_run
    started = []

    def read_back(*args, **kwargs):
        started.append(True)
        policy.context = ("read-back", len(started))
        try:
            return original(*args, **kwargs)
        finally:
            policy.context = "report"

    monkeypatch.setattr(theme_report, "reverify_analysis_run", read_back)
    with pytest.raises(AnalysisError, match=f"^{EXPECTED[(change, place)]}$"):
        theme_report.write_theme_report(
            tmp_path / "report",
            stored,
            replace(inputs, assignment_policy=policy),
            inputs.analysis_policy,
            families,
            views,
            audience="export",
        )
    assert policy.fired
    assert not (tmp_path / "report").exists()
