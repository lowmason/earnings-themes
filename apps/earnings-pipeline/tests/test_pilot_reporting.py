"""Counts-only collectors, strict run intake, and complete fresh-run membership."""

import importlib
from types import SimpleNamespace

import pytest
from earnings_themes.records import RecordError
from earnings_themes.split import Partition

cases = importlib.import_module("apps.earnings-pipeline.tests.test_pilot_labels")


def test_retention_counts_quote_occurrences_and_retry_rejections():
    from earnings_pipeline.pilot_reporting import quote_retention

    source = SimpleNamespace(
        claims=(
            SimpleNamespace(doc_id="d", quote_ids=("q1", "q2")),
            SimpleNamespace(doc_id="d", quote_ids=("q1",)),
            SimpleNamespace(doc_id="other", quote_ids=("q3",)),
        ),
        rejections=(
            SimpleNamespace(doc_id="d", candidate_index=0, labels=("q1", "q2")),
            SimpleNamespace(doc_id="d", candidate_index=0, labels=("q1",)),
            SimpleNamespace(doc_id="d", candidate_index=None, labels=("whole",)),
        ),
    )
    assert quote_retention(source, "d") == (3, 6)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("status", "partial"),
        ("partition", Partition.TRAIN),
        ("event_ids", ("changed-event",)),
        ("configuration_hash", "c" * 64),
        ("calibration_hash", "d" * 64),
    ),
    ids=("partial", "wrong_partition", "inventory", "configuration", "calibration"),
)
def test_stability_refuses_partial_duplicate_or_changed_inventory_before_figures(
    field, value
):
    from earnings_pipeline.pilot_reporting import checked_stability

    record = SimpleNamespace(
        partition=Partition.DEV,
        fresh="r1",
        status="complete",
        event_ids=("e1",),
        configuration_hash="a" * 64,
        calibration_hash="b" * 64,
    )
    loaded = SimpleNamespace(record=record)
    with pytest.raises(RecordError, match="complete_fresh_runs"):
        checked_stability((loaded, loaded, loaded), ("e1",), "a" * 64, "b" * 64)
    records = [
        SimpleNamespace(record=SimpleNamespace(**{**record.__dict__, "fresh": f"r{i}"}))
        for i in range(3)
    ]
    assert checked_stability(records, ("e1",), "a" * 64, "b" * 64) == ("r0", "r1", "r2")
    setattr(records[1].record, field, value)
    with pytest.raises(RecordError, match="complete_fresh_runs") as refused:
        checked_stability(records, ("e1",), "a" * 64, "b" * 64)
    assert refused.value.name == "stability"
    assert len(refused.value.problems) == 1
    assert refused.value.problems[0] == "complete_fresh_runs"


def test_loaded_run_checks_calibration_head_and_pass_binding_before_coding(
    tmp_path, monkeypatch
):
    import earnings_pipeline.pilot_reporting as module
    from earnings_pipeline.pilot_records import RunRecord, read_json
    from earnings_pipeline.pilot_workflow import make_run

    intake, loaded = cases.make_case(tmp_path)
    artifact = cases.cases.bound_artifact(intake.config, loaded)
    record = make_run(
        intake.config,
        loaded,
        artifact,
        directory=tmp_path / "data/runs/pilot/train/run",
        now=lambda: cases.cases.cases.NOW,
    )
    path = tmp_path / "data/runs/pilot/train/run/run-record.json"

    def refuse(*args):
        raise RecordError("calibration", ("not_committed",))

    monkeypatch.setattr(module, "require_committed", refuse)
    monkeypatch.setattr(
        module,
        "read_calibration",
        lambda *args: pytest.fail("artifact read preceded HEAD gate"),
    )
    with pytest.raises(RecordError, match="not_committed"):
        module.load_run(intake, path)
    assert read_json(path, RunRecord, "run") == record


def test_coverage_and_recount_gates_precede_every_share_figure(tmp_path, monkeypatch):
    import earnings_pipeline.pilot_reporting as module
    from earnings_themes.split import Partition

    current = SimpleNamespace(
        preregistration=SimpleNamespace(content_hash="a" * 64),
        partition=Partition.TRAIN,
    )
    dev = SimpleNamespace(
        preregistration=current.preregistration,
        partition=Partition.DEV,
        config=SimpleNamespace(selected_event_ids=("e1",)),
    )
    base = SimpleNamespace(
        record=SimpleNamespace(
            fresh=None, calibration_hash="b" * 64, configuration_hash="c" * 64
        )
    )
    monkeypatch.setattr(
        module, "evaluation_path", lambda *args: tmp_path / "report.json"
    )
    monkeypatch.setattr(module, "checked_stability", lambda *args: ("r1", "r2", "r3"))
    monkeypatch.setattr(
        module,
        "coverage_gate",
        lambda *args: (_ for _ in ()).throw(
            RecordError("coverage", ("binding_mismatch",))
        ),
    )
    monkeypatch.setattr(
        module,
        "recount_all",
        lambda *args: pytest.fail("recount preceded coverage gate"),
    )
    monkeypatch.setattr(
        module,
        "partition_report",
        lambda *args, **kwargs: pytest.fail("figures preceded gates"),
    )
    with pytest.raises(RecordError, match="binding_mismatch"):
        module.write_report(current, dev, base, base, ())
    monkeypatch.setattr(module, "coverage_gate", lambda *args: None)
    monkeypatch.setattr(
        module,
        "recount_all",
        lambda *args: (_ for _ in ()).throw(RecordError("gold", ("counts_mismatch",))),
    )
    with pytest.raises(RecordError, match="counts_mismatch"):
        module.write_report(current, dev, base, base, ())


def test_complete_normal_run_collects_live_labels_and_replay_decisions(
    tmp_path, monkeypatch
):
    from datetime import date

    import earnings_pipeline.pilot_calibration as calibration
    import earnings_pipeline.pilot_reporting as module
    from earnings_core import sha256_hex
    from earnings_pipeline.pilot_labels import check_working, write_view
    from earnings_pipeline.pilot_records import json_bytes
    from earnings_pipeline.pilot_workflow import make_run
    from earnings_themes.records import sealed

    intake, passed = cases.make_case(tmp_path)
    write_view(intake, passed, 0, date(2026, 10, 13))
    label_path = check_working(intake, passed, 0)
    artifact = sealed(
        cases.cases.bound_artifact(intake.config, passed).model_copy(
            update={
                "preregistration_hash": intake.preregistration.content_hash,
                "labels_hash": sha256_hex(label_path.read_bytes()),
            }
        )
    )
    artifact_path = intake.pinned.evaluation / "calibration-v1.json"
    artifact_path.write_bytes(json_bytes(artifact))
    monkeypatch.setattr(module, "require_committed", lambda *args: None)
    monkeypatch.setattr(calibration, "require_committed", lambda *args: None)
    make_run(
        intake.config,
        passed,
        artifact,
        directory=tmp_path / "data/runs/pilot/train/run",
        now=lambda: cases.cases.cases.NOW,
    )
    run = module.load_run(
        intake, tmp_path / "data/runs/pilot/train/run/run-record.json"
    )
    from earnings_themes.evaluation import load_labels

    targets = module.labelled_targets(intake, run, load_labels(label_path))
    assert len(targets) == 1
    assert set(targets[0].scores) == {"minicheck", "deberta"}
    assert targets[0].accepted
    assert run.record.status == "complete"


def test_observations_retention_excludes_flagged_refused_and_incomplete(monkeypatch):
    import earnings_pipeline.pilot_reporting as module
    from earnings_themes.support.records import ReviewStatus

    doc_id = "invented-doc"
    event_id = "invented-event"
    outcomes = tuple(
        SimpleNamespace(target_id=f"target-{i}", status=status)
        for i, status in enumerate(
            (
                ReviewStatus.ASSESSED,
                ReviewStatus.ASSESSED,
                ReviewStatus.FLAGGED,
                ReviewStatus.REFUSED,
                ReviewStatus.INCOMPLETE,
                ReviewStatus.ASSESSED,
            )
        )
    )
    targets = tuple(
        SimpleNamespace(
            target_id=outcome.target_id,
            target=SimpleNamespace(doc_id=doc_id if i < 5 else "other-doc"),
        )
        for i, outcome in enumerate(outcomes)
    )
    source = SimpleNamespace(doc_id=doc_id, event_id=event_id)
    sources = SimpleNamespace(
        stored_run=SimpleNamespace(claims=(), rejections=(), quotes=()),
        bundles=(SimpleNamespace(document=SimpleNamespace(doc_id=doc_id)),),
        provenance_hash="a" * 64,
    )
    intake = SimpleNamespace(
        config=SimpleNamespace(
            repo=module.Path("/private/tmp"),
            states_dir="invented-states",
            sources=(source,),
        ),
        gold=(SimpleNamespace(event_id=event_id),),
    )
    run = SimpleNamespace(
        record=SimpleNamespace(fresh=None),
        passed=SimpleNamespace(sources=sources),
        primary=SimpleNamespace(targets=targets, outcomes=outcomes),
        coding=SimpleNamespace(
            decisions=(
                SimpleNamespace(
                    doc_id=doc_id,
                    status="accepted",
                    theme_id="invented-theme",
                    supporting_quote_ids=(),
                ),
                SimpleNamespace(doc_id=doc_id, status="rejected"),
            )
        ),
    )
    state = SimpleNamespace(
        doc_id=doc_id,
        to_state=SimpleNamespace(value="parsed"),
        attempts=(),
        accession="invented-accession",
        exhibit="invented-exhibit",
        artifact_sha256="b" * 64,
    )
    monkeypatch.setattr(module, "checked_pass", lambda *args, **kwargs: None)
    monkeypatch.setattr(module, "replay_runtime", lambda *args: None)
    monkeypatch.setattr(module, "load_workflow_inputs", lambda *args: sources)
    monkeypatch.setattr(module, "_checked_history", lambda *args: ())
    monkeypatch.setattr(
        module, "_baseline", lambda *args: ({event_id + ":release": state}, None)
    )
    monkeypatch.setattr(module, "unit_index", lambda *args: None)

    observed = module.observations(intake, run)
    assert len(observed) == 1
    assert observed[0].targets == (1, 2)
