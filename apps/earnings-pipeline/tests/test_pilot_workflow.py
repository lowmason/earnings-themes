"""A8 phase order and zero-dispatch replay over entirely invented source text."""

import importlib
import json
import shutil

import pytest
from earnings_pipeline.theme_workflow import WorkflowRuntime, replay_runtime
from earnings_themes.coding.adapters import ScriptedClassifier
from earnings_themes.extraction.adapters import ModelReply, ScriptedAdapter
from earnings_themes.split import Partition

cases = importlib.import_module("apps.earnings-pipeline.tests.test_theme_workflow")
coding_cases = importlib.import_module("packages.earnings-themes.tests.coding.cases")


def seed_case(tmp_path, **kwargs):
    config, payload = cases.seed_case(tmp_path, **kwargs)
    updates = {}
    for name in ("extraction_cache", "coding_cache", "support_cache"):
        path = tmp_path / config.__getattribute__(name)
        target = tmp_path / "data/runs/pilot/caches" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            shutil.move(str(path), str(target))
        updates[name] = target.relative_to(tmp_path).as_posix()
    return config.model_copy(update=updates), payload


def runtime(config, phases):
    extractor = ScriptedAdapter(
        lambda request: (
            phases.append("extract"),
            ModelReply(
                model="scripted",
                text=json.dumps(
                    {
                        "candidates": [
                            {"quote_labels": ["U1"], "claim": "Invented expansion."}
                        ]
                    }
                ),
            ),
        )[1]
    )
    classifier = ScriptedClassifier(
        lambda request: (
            phases.append("classify"),
            ModelReply(
                model=config.classifier_identity.runtime.model_id,
                text=json.dumps({"theme_ids": ["capacity"], "attributes": {}}),
            ),
        )[1],
        lambda request: 5,
        config.classifier_identity,
    )
    scorer, judges = coding_cases.make_support_parts()
    return WorkflowRuntime(extractor, classifier, scorer, judges, None, None)


def test_pass_stores_phases_without_decisions_or_state_and_resume_uses_cache(tmp_path):
    from earnings_pipeline.pilot_workflow import load_pass, make_pass

    config, _ = seed_case(tmp_path, seed=False, review=True)
    phases = []
    rt = runtime(config, phases)
    alternative = coding_cases.make_support_parts()[0]
    before = {p.name: p.read_bytes() for p in (tmp_path / config.states_dir).iterdir()}
    record = make_pass(
        config,
        rt,
        alternative,
        partition=Partition.TRAIN,
        directory=tmp_path / "data/runs/pilot/train/pass",
        fresh=None,
        support_ready=lambda: phases.append("ready"),
        now=lambda: cases.NOW,
    )
    assert record.status == "complete"
    assert phases.index("extract") < phases.index("classify") < phases.index("ready")
    loaded = load_pass(config, record)
    assert loaded.proposal.record.run_id == config.coding_run_id
    assert loaded.primary.targets
    assert not (tmp_path / "data/runs/pilot/train/pass/coding").exists()
    assert before == {
        p.name: p.read_bytes() for p in (tmp_path / config.states_dir).iterdir()
    }
    again = make_pass(
        config,
        replay_runtime(config),
        alternative,
        partition=Partition.TRAIN,
        directory=tmp_path / "data/runs/pilot/train/pass",
        fresh=None,
        support_ready=lambda: None,
        now=lambda: cases.NOW,
    )
    assert again == record


def test_unacknowledged_checkpoint_never_calls_support(tmp_path):
    from earnings_pipeline.pilot_workflow import make_pass

    config, _ = seed_case(tmp_path, seed=False, review=True)
    phases = []
    rt = runtime(config, phases)

    def refused():
        raise RuntimeError("INVENTED_EXCEPTION_SENTINEL")

    with pytest.raises(RuntimeError):
        make_pass(
            config,
            rt,
            rt.scorer,
            partition=Partition.TRAIN,
            directory=tmp_path / "data/runs/pilot/train/pass",
            fresh=None,
            support_ready=refused,
            now=lambda: cases.NOW,
        )
    assert not (tmp_path / "data/runs/pilot/train/pass/support").exists()


def test_fresh_directory_is_never_resumed_and_main_caches_survive(tmp_path):
    from earnings_pipeline.pilot_workflow import make_pass
    from earnings_pipeline.theme_config import WorkflowError

    config, _ = seed_case(tmp_path, seed=True, review=True)
    phases = []
    rt = runtime(config, phases)
    before = {
        p.relative_to(tmp_path): p.read_bytes()
        for kind in (config.extraction_cache, config.coding_cache, config.support_cache)
        for p in (tmp_path / kind).glob("*.json")
    }
    directory = tmp_path / "data/runs/pilot/dev/fresh/stability-1"
    record = make_pass(
        config,
        rt,
        rt.scorer,
        partition=Partition.DEV,
        directory=directory,
        fresh="stability-1",
        support_ready=lambda: None,
        now=lambda: cases.NOW,
    )
    assert record.mode == "fresh"
    assert phases
    assert before == {p: (tmp_path / p).read_bytes() for p in before}
    with pytest.raises(WorkflowError, match="state_run_conflict"):
        make_pass(
            config,
            rt,
            rt.scorer,
            partition=Partition.DEV,
            directory=directory,
            fresh="stability-1",
            support_ready=lambda: None,
            now=lambda: cases.NOW,
        )


def bound_artifact(config, loaded, *, none=False):
    from earnings_themes.evaluation import frozen_configuration, sealed
    from earnings_themes.evaluation.calibration import configuration_hash

    factory = importlib.import_module(
        "packages.earnings-themes.tests.evaluation.test_policy"
    )
    artifact = factory.artifact_with(0.2)
    selection = None if none else artifact.selection
    fields = artifact.model_dump(mode="json")
    fields.update(
        selection=None if selection is None else selection.model_dump(mode="json"),
        outcome="no_candidate" if none else "selected",
        configuration_hash=configuration_hash(
            frozen_configuration(
                loaded.sources.stored_run.record,
                loaded.proposal.record,
                loaded.primary.record,
                config.support_policy,
            ),
            selection,
        ),
    )
    from earnings_themes.evaluation import CalibrationArtifact

    return sealed(CalibrationArtifact.model_validate_json(json.dumps(fields)))


@pytest.mark.parametrize("none", [False, True])
def test_normal_run_reuses_live_pass_and_replays_without_dispatch(tmp_path, none):
    from earnings_pipeline.pilot_workflow import load_pass, make_pass, make_run
    from earnings_themes.coding.store import read_coding_run

    config, _ = seed_case(tmp_path, seed=False, review=True)
    rt = runtime(config, [])
    passed = make_pass(
        config,
        rt,
        rt.scorer,
        partition=Partition.TRAIN,
        directory=tmp_path / "data/runs/pilot/train/pass",
        fresh=None,
        support_ready=lambda: None,
        now=lambda: cases.NOW,
    )
    loaded = load_pass(config, passed)
    artifact = bound_artifact(config, loaded, none=none)
    record = make_run(
        config,
        loaded,
        artifact,
        directory=tmp_path / "data/runs/pilot/train/run",
        now=lambda: cases.NOW,
    )
    assert record.fresh is None
    coding = read_coding_run(tmp_path / record.coding.directory)
    assert {d.status for d in coding.decisions} == (
        {"review"} if none else {"accepted"}
    )
    assert coding.record.cache_mode == "replay"
    assert coding.record.cache_hits > 0
    assert coding.record.requests == 0


@pytest.mark.parametrize("cache", ["coding_cache", "support_cache"])
def test_policy_tamper_and_missing_replay_entry_are_refused(tmp_path, cache):
    from earnings_pipeline.pilot_workflow import load_pass, make_pass, make_run
    from earnings_pipeline.theme_config import WorkflowError
    from earnings_themes.records import RecordError

    config, _ = seed_case(tmp_path, seed=False, review=True)
    rt = runtime(config, [])
    passed = make_pass(
        config,
        rt,
        rt.scorer,
        partition=Partition.TRAIN,
        directory=tmp_path / "data/runs/pilot/train/pass",
        fresh=None,
        support_ready=lambda: None,
        now=lambda: cases.NOW,
    )
    loaded = load_pass(config, passed)
    artifact = bound_artifact(config, loaded)
    with pytest.raises(RecordError):
        make_run(
            config,
            loaded,
            artifact.model_copy(update={"usable_labels": 59}),
            directory=tmp_path / "data/runs/pilot/train/tamper",
            now=lambda: cases.NOW,
        )
    for entry in (tmp_path / getattr(config, cache)).glob("*.json"):
        entry.unlink()
    before = {p.name: p.read_bytes() for p in (tmp_path / config.states_dir).iterdir()}
    with pytest.raises(WorkflowError, match="replay_miss"):
        make_run(
            config,
            loaded,
            artifact,
            directory=tmp_path / "data/runs/pilot/train/missing",
            now=lambda: cases.NOW,
        )

    assert not (tmp_path / "data/runs/pilot/train/missing").exists()
    assert before == {
        p.name: p.read_bytes() for p in (tmp_path / config.states_dir).iterdir()
    }


@pytest.mark.parametrize(
    "child", ["extraction", "proposals.json", "support", "alternative"]
)
def test_interrupted_pass_refuses_phase_symlink_before_source_read(tmp_path, child):
    from earnings_pipeline.pilot_workflow import make_pass
    from earnings_pipeline.theme_config import WorkflowError

    config, _ = seed_case(tmp_path, seed=False, review=True)
    root = tmp_path / "data/runs/pilot/train/pass"
    root.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / child).symlink_to(outside)
    rt = runtime(config, [])
    with pytest.raises(WorkflowError, match="malformed_record"):
        make_pass(
            config,
            rt,
            rt.scorer,
            partition=Partition.TRAIN,
            directory=root,
            fresh=None,
            support_ready=lambda: None,
            now=lambda: cases.NOW,
        )


def test_scorer_cache_corruption_refuses_before_publication(tmp_path):
    from earnings_pipeline.pilot_workflow import load_pass, make_pass, make_run
    from earnings_pipeline.theme_config import WorkflowError

    config, _ = seed_case(tmp_path, seed=False, review=True)
    rt = runtime(config, [])
    record = make_pass(
        config,
        rt,
        rt.scorer,
        partition=Partition.TRAIN,
        directory=tmp_path / "data/runs/pilot/train/pass",
        fresh=None,
        support_ready=lambda: None,
        now=lambda: cases.NOW,
    )
    loaded = load_pass(config, record)
    artifact = bound_artifact(config, loaded)
    scorer = next(
        p
        for p in (tmp_path / config.support_cache).glob("*.json")
        if json.loads(p.read_bytes())["kind"] == "scorer"
    )
    scorer.write_text("INVENTED_CORRUPT_SENTINEL")
    with pytest.raises(WorkflowError, match="cache_corrupt"):
        make_run(
            config,
            loaded,
            artifact,
            directory=tmp_path / "data/runs/pilot/train/corrupt",
            now=lambda: cases.NOW,
        )
    assert not (tmp_path / "data/runs/pilot/train/corrupt").exists()


def test_fresh_policy_decides_without_changing_acquisition_state(tmp_path):
    from earnings_pipeline.pilot_workflow import load_pass, make_pass, make_run

    config, _ = seed_case(tmp_path, seed=False, review=True)
    rt = runtime(config, [])
    base = make_pass(
        config,
        rt,
        rt.scorer,
        partition=Partition.DEV,
        directory=tmp_path / "data/runs/pilot/dev/pass",
        fresh=None,
        support_ready=lambda: None,
        now=lambda: cases.NOW,
    )
    artifact = bound_artifact(config, load_pass(config, base))
    before = {p.name: p.read_bytes() for p in (tmp_path / config.states_dir).iterdir()}
    directory = tmp_path / "data/runs/pilot/dev/fresh/s-1"
    fresh = make_pass(
        config,
        rt,
        rt.scorer,
        partition=Partition.DEV,
        directory=directory,
        fresh="s-1",
        support_ready=lambda: None,
        now=lambda: cases.NOW,
    )
    record = make_run(
        config,
        load_pass(config, fresh),
        artifact,
        directory=directory,
        now=lambda: cases.NOW,
    )
    assert record.fresh == "s-1" and record.status == "complete"
    assert before == {
        p.name: p.read_bytes() for p in (tmp_path / config.states_dir).iterdir()
    }


def test_crash_resume_binds_policies_and_complete_requires_all_proposals(tmp_path):
    from dataclasses import replace

    from earnings_pipeline.pilot_workflow import _complete, load_pass, make_pass
    from earnings_pipeline.theme_config import WorkflowError

    config, _ = seed_case(tmp_path, seed=False, review=True)
    rt = runtime(config, [])
    directory = tmp_path / "data/runs/pilot/train/pass"
    record = make_pass(
        config,
        rt,
        rt.scorer,
        partition=Partition.TRAIN,
        directory=directory,
        fresh=None,
        support_ready=lambda: None,
        now=lambda: cases.NOW,
    )
    loaded = load_pass(config, record)
    truncated = replace(
        loaded.primary,
        targets=(),
        evidence=(),
        contexts=(),
        entailment=(),
        trials=(),
        attempts=(),
        usage=(),
        outcomes=(),
    )
    assert not _complete(
        loaded.sources.stored_run, loaded.proposal, truncated, truncated
    )
    (directory / "pass.json").unlink()
    changed = config.model_copy(
        update={
            "support_ceilings": config.support_ceilings.model_copy(
                update={"scorer_per_run": config.support_ceilings.scorer_per_run + 1}
            )
        }
    )
    with pytest.raises(WorkflowError, match="input_changed"):
        make_pass(
            changed,
            rt,
            rt.scorer,
            partition=Partition.TRAIN,
            directory=directory,
            fresh=None,
            support_ready=lambda: None,
            now=lambda: cases.NOW,
        )


@pytest.mark.parametrize("identity", ["stability_run_id", "configured_run_id"])
def test_load_pass_refuses_resealed_proposal_identity_mismatch(tmp_path, identity):
    from earnings_core import digest
    from earnings_pipeline.pilot_records import ProposalSnapshot, json_bytes, read_json
    from earnings_pipeline.pilot_workflow import load_pass, make_pass, selected_file
    from earnings_pipeline.theme_config import WorkflowError
    from earnings_themes.records import sealed

    config, _ = seed_case(tmp_path, seed=False, review=True)
    rt = runtime(config, [])
    directory = tmp_path / "data/runs/pilot/dev/fresh/identity-1"
    record = make_pass(
        config,
        rt,
        rt.scorer,
        partition=Partition.DEV,
        directory=directory,
        fresh="identity-1",
        support_ready=lambda: None,
        now=lambda: cases.NOW,
    )
    snapshot_path = tmp_path / record.proposals.path
    snapshot = read_json(snapshot_path, ProposalSnapshot, "proposals", seal=False)
    if identity == "stability_run_id":
        proposal_record = sealed(
            snapshot.record.model_copy(update={"stability_run_id": "identity-2"})
        )
        snapshot = snapshot.model_copy(update={"record": proposal_record})
        snapshot_path.write_bytes(json_bytes(snapshot))
    else:
        config = config.model_copy(update={"coding_run_id": "other-coding-run"})
    record = sealed(
        record.model_copy(
            update={
                "configuration_hash": digest(config.model_dump(mode="json")),
                "proposals": selected_file(config, snapshot_path),
            }
        )
    )
    with pytest.raises(WorkflowError, match="input_changed"):
        load_pass(config, record)
