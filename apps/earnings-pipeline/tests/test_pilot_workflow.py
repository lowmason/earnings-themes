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


def runtime(config, phases, claims=1):
    candidates = [
        {
            "quote_labels": ["U1"],
            "claim": "Invented expansion." if n == 0 else f"Invented expansion {n}.",
        }
        for n in range(claims)
    ]
    extractor = ScriptedAdapter(
        lambda request: (
            phases.append("extract"),
            ModelReply(
                model="scripted",
                text=json.dumps({"candidates": candidates}),
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


def test_fresh_directory_without_resume_refuses_and_main_caches_survive(tmp_path):
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


@pytest.mark.parametrize("none", [False, True])
def test_fresh_policy_decides_without_changing_acquisition_state(tmp_path, none):
    """B7's fresh run decides under the calibration; a ``no_candidate`` artifact
    binds no policy, so every decision stays in review (D21-33)."""
    from earnings_pipeline.pilot_workflow import load_pass, make_pass, make_run
    from earnings_themes.coding.store import read_coding_run

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
    artifact = bound_artifact(config, load_pass(config, base), none=none)
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
    coding = read_coding_run(tmp_path / record.coding.directory)
    assert {d.status for d in coding.decisions} == (
        {"review"} if none else {"accepted"}
    )
    assert coding.record.cache_mode == "fresh"
    assert before == {
        p.name: p.read_bytes() for p in (tmp_path / config.states_dir).iterdir()
    }


def test_crash_resume_binds_policies_and_complete_requires_all_proposals(tmp_path):
    from dataclasses import replace

    from earnings_pipeline.pilot_workflow import (
        _complete,
        load_pass,
        make_pass,
        processed,
    )
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
    assert processed(loaded)
    assert not processed(replace(loaded, primary=truncated, alternative=truncated))
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


def test_run_gates_accept_a_classification_cut_at_the_request_ceiling(tmp_path):
    """D21-35: a document with more claims than its request ceiling still passes."""
    from earnings_pipeline.pilot_workflow import (
        _complete,
        load_pass,
        make_pass,
        make_run,
        processed,
    )

    config, _ = seed_case(tmp_path, seed=False, review=True)
    config = config.model_copy(
        update={
            "coding_ceilings": config.coding_ceilings.model_copy(
                update={"requests_per_document": 1}
            )
        }
    )
    rt = runtime(config, [], claims=3)
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
    classifications = loaded.proposal.classifications
    cut = [c for c in classifications if c.reason == "requests_exhausted"]
    assert passed.status == "partial"
    assert [c.status for c in classifications].count("completed") == 1
    assert len(cut) == 2
    assert all(c.status == "incomplete" for c in cut)
    assert not _complete(loaded.sources.stored_run, loaded.proposal)
    assert processed(loaded)
    # The Stage 10 gates behind `pilot21 run` accept the partial run.
    record = make_run(
        config,
        loaded,
        bound_artifact(config, loaded),
        directory=tmp_path / "data/runs/pilot/train/run",
        now=lambda: cases.NOW,
    )
    assert record.status == "partial"
    assert processed(loaded)


def cut_case(tmp_path, *, partition=Partition.TRAIN, fresh=None, claims=3):
    """An invented pass whose document has more claims than its request ceiling."""
    from earnings_pipeline.pilot_workflow import load_pass, make_pass

    config, _ = seed_case(tmp_path, seed=False, review=True)
    config = config.model_copy(
        update={
            "coding_ceilings": config.coding_ceilings.model_copy(
                update={"requests_per_document": 1}
            )
        }
    )
    rt = runtime(config, [], claims=claims)
    base = "dev/fresh/s-1" if fresh else f"{partition.value}"
    record = make_pass(
        config,
        rt,
        rt.scorer,
        partition=partition,
        directory=tmp_path / f"data/runs/pilot/{base}/pass"
        if not fresh
        else tmp_path / f"data/runs/pilot/{base}",
        fresh=fresh,
        support_ready=lambda: None,
        now=lambda: cases.NOW,
    )
    return config, load_pass(config, record)


@pytest.mark.parametrize("victim", ["completed", "unrecorded"])
def test_replay_still_refuses_a_miss_beyond_the_cut_claims(tmp_path, victim):
    """D21-35 tolerates only the claims the live pass cut, never another cache miss."""
    from earnings_pipeline.pilot_workflow import make_run
    from earnings_pipeline.theme_config import WorkflowError

    config, loaded = cut_case(tmp_path)
    cache = sorted((tmp_path / config.coding_cache).glob("*.json"))
    assert len(cache) == 1  # only the one classified claim sent a request
    if victim == "completed":
        cache[0].unlink()
        with pytest.raises(WorkflowError, match="replay_miss"):
            make_run(
                config,
                loaded,
                bound_artifact(config, loaded),
                directory=tmp_path / "data/runs/pilot/train/run",
                now=lambda: cases.NOW,
            )
    else:
        # A cut claim the live pass did not record as cut is a plain miss.
        from dataclasses import replace

        kept = tuple(
            c
            for c in loaded.proposal.classifications
            if c.reason != "requests_exhausted"
        )
        proposal = replace(loaded.proposal, classifications=kept)
        with pytest.raises(WorkflowError, match="replay_miss"):
            make_run(
                config,
                replace(loaded, proposal=proposal),
                bound_artifact(config, loaded),
                directory=tmp_path / "data/runs/pilot/train/run",
                now=lambda: cases.NOW,
            )


@pytest.mark.parametrize(
    ("classification", "decision", "failed"),
    [
        (("replay_miss", "replay_miss"), (), False),
        (("replay_miss",), (), False),
        (("replay_miss", "replay_miss", "replay_miss"), (), True),
        (("replay_miss", "replay_dispatch_forbidden"), (), True),
        (("replay_miss", "replay_miss"), ("replay_miss",), True),
        # Both cut claims replay as classified, and a claim that was NOT cut misses.
        ((None, None, "replay_miss"), (), True),
    ],
    ids=(
        "all_cut",
        "fewer_than_cut",
        "extra_miss",
        "dispatch",
        "decision_miss",
        "uncut_miss",
    ),
)
def test_replay_failed_counts_only_the_cut_claims_misses(
    classification, decision, failed
):
    from collections import Counter
    from types import SimpleNamespace

    from earnings_pipeline.pilot_workflow import _replay_failed

    cut = frozenset({("d", "c1"), ("d", "c2")})
    rows = tuple(
        SimpleNamespace(doc_id="d", claim_id=f"c{n}", reason=reason)
        for n, reason in enumerate(classification, 1)
    )
    coding = SimpleNamespace(
        classifications=rows,
        record=SimpleNamespace(
            counts_by_reason=tuple(Counter(r for r in classification if r).items()),
            counts_by_decision_reason=tuple(Counter(decision).items()),
        ),
    )
    assert _replay_failed(coding, cut) is failed


def test_fresh_run_accepts_a_classification_cut_at_the_request_ceiling(tmp_path):
    """The fresh branch finalizes the live proposal and never replays (D21-35)."""
    from earnings_pipeline.pilot_workflow import make_run, processed
    from earnings_themes.coding.store import read_coding_run

    config, loaded = cut_case(tmp_path, partition=Partition.DEV, fresh="s-1")
    assert loaded.record.status == "partial" and processed(loaded)
    record = make_run(
        config,
        loaded,
        bound_artifact(config, loaded),
        directory=tmp_path / "data/runs/pilot/dev/fresh/s-1",
        now=lambda: cases.NOW,
    )
    assert record.fresh == "s-1" and record.status == "partial"
    coding = read_coding_run(tmp_path / record.coding.directory)
    assert [c.reason for c in coding.classifications].count("requests_exhausted") == 2
    assert [d.status for d in coding.decisions] == ["accepted"]


def test_run_readers_accept_the_replayed_cut_run(tmp_path):
    """`load_run`'s deep checks run over a stored replay that holds `replay_miss` rows.

    The replay stores `replay_miss` where the live pass stored `requests_exhausted`.
    These are the two checks `pilot_reporting.load_run` makes on a stored run.
    """
    from earnings_pipeline.pilot_workflow import (
        bind_policy,
        make_run,
        phase_path,
        stored_directory,
    )
    from earnings_themes.coding import validate_proposal_support
    from earnings_themes.coding.store import read_coding_run, reverify_coding_run
    from earnings_themes.support import read_support_run

    config, loaded = cut_case(tmp_path)
    artifact = bound_artifact(config, loaded)
    record = make_run(
        config,
        loaded,
        artifact,
        directory=tmp_path / "data/runs/pilot/train/run",
        now=lambda: cases.NOW,
    )
    coding_dir = stored_directory(config, record.coding)
    primary = read_support_run(phase_path(config, coding_dir.parent / "support"))
    coding = read_coding_run(coding_dir)
    assert [c.reason for c in coding.classifications].count("replay_miss") == 2
    assert tuple(t.target for t in primary.targets) == loaded.proposal.targets
    validate_proposal_support(loaded.proposal, primary, loaded.sources)
    policy = bind_policy(config, loaded, artifact, replay=True)
    reverify_coding_run(coding, loaded.sources, primary, policy)


class Stop:
    """Count each scripted dispatch by phase; raise ``KeyboardInterrupt`` on one.

    ``Stop("classify", 2)`` raises on the second classifier dispatch of its process.
    A raised call returns no reply, so it is not counted as a dispatch.
    """

    def __init__(self, phase=None, at=1):
        self.phase, self.at = phase, at
        self.calls = []

    def wrap(self, phase, reply):
        def call(request):
            if phase == self.phase and self.calls.count(phase) + 1 == self.at:
                self.phase = None
                raise KeyboardInterrupt()
            self.calls.append(phase)
            return reply(request)

        return call


def stoppable(config, stop, claims=3):
    """An invented runtime and alternative scorer whose dispatches ``stop`` counts.

    The alternative scorer has its own identity, so the alternative phase
    dispatches its own scorer requests, as the pinned alternative does.
    """
    from dataclasses import replace

    from earnings_themes.support.scorers import ScriptedScorer

    rt = runtime(config, [], claims)
    rt.classifier.script = stop.wrap("classify", rt.classifier.script)
    for judge in rt.judges:
        judge.script = stop.wrap("judge", judge.script)
    other = coding_cases.make_support_parts()[0]
    identity = other.identity.model_copy(
        update={
            "runtime": other.identity.runtime.model_copy(
                update={"model_id": "invented-alternative"}
            )
        }
    )
    alternative = ScriptedScorer(
        stop.wrap(
            "alternative",
            lambda request: other.score(request).model_copy(
                update={"identity": identity}
            ),
        ),
        other.count_tokens,
        identity,
    )
    rt = replace(
        rt,
        extractor=ScriptedAdapter(
            stop.wrap("extract", rt.extractor.complete), rt.extractor.identity
        ),
        scorer=ScriptedScorer(
            stop.wrap("score", rt.scorer.score),
            rt.scorer.count_tokens,
            rt.scorer.identity,
        ),
    )
    return rt, alternative


def fresh_pass(config, tmp_path, fresh, stop, *, resume=False, support_ready=None):
    from earnings_pipeline.pilot_workflow import make_pass

    rt, alternative = stoppable(config, stop)
    return make_pass(
        config,
        rt,
        alternative,
        partition=Partition.DEV,
        directory=tmp_path / f"data/runs/pilot/dev/fresh/{fresh}/pass",
        fresh=fresh,
        support_ready=support_ready or (lambda: None),
        now=lambda: cases.NOW,
        resume=resume,
    )


def main_caches(config, tmp_path):
    return {
        p.relative_to(tmp_path): p.read_bytes()
        for kind in (config.extraction_cache, config.coding_cache, config.support_cache)
        for p in (tmp_path / kind).iterdir()
        if p.is_file()
    }


def outcome(config, record):
    """A processed pass's IDs and statuses, then the same rows without their IDs."""
    from earnings_pipeline.pilot_workflow import load_pass, processed

    loaded = load_pass(config, record)
    assert processed(loaded)
    classifications = loaded.proposal.classifications
    runs = (loaded.primary, loaded.alternative)
    ids = (
        tuple((c.classification_id, c.status) for c in classifications),
        tuple(t.target_id for t in loaded.primary.targets),
        *(tuple((o.target_id, o.status) for o in run.outcomes) for run in runs),
    )
    content = (
        tuple(
            (c.doc_id, c.claim_id, c.status, c.reason, c.theme_ids)
            for c in classifications
        ),
        tuple(t.target for t in loaded.primary.targets),
        *(tuple(o.status for o in run.outcomes) for run in runs),
    )
    return ids, content


def reference(tmp_path):
    """An uninterrupted fresh run of the same ID in its own invented repository,
    and its dispatch counts. Each ID folds in the stability run ID, so only a run
    of the same ID can show the same IDs."""
    from collections import Counter

    root = tmp_path / "reference"
    root.mkdir()
    config, _ = seed_case(root, seed=True, review=True)
    stop = Stop()
    record = fresh_pass(config, root, "s-1", stop)
    assert record.status == "complete"
    return outcome(config, record), Counter(stop.calls)


def interrupt(config, tmp_path, fresh, stop, *, resume=False):
    """One process of a fresh run that stops at ``stop``; its dispatch counts."""
    from collections import Counter

    with pytest.raises(KeyboardInterrupt):
        fresh_pass(config, tmp_path, fresh, stop, resume=resume)
    return Counter(stop.calls)


STOPS = {
    "extraction": ("extract", 1),
    "classification": ("classify", 2),
    "support": ("score", 2),
    "alternative": ("alternative", 2),
}


@pytest.mark.parametrize(
    "stop",
    [
        "extraction",
        "extraction_write",
        "classification",
        "after_proposals",
        "support",
        "alternative",
    ],
)
def test_resume_matches_an_uninterrupted_run_after_a_stop(tmp_path, monkeypatch, stop):
    """D21-38: a resumed fresh run equals an uninterrupted one and dispatches only
    what its first process did not."""
    from collections import Counter

    from earnings_pipeline.pilot_workflow import load_pass, make_pass
    from earnings_themes.extraction import store

    config, _ = seed_case(tmp_path, seed=True, review=True)
    before = main_caches(config, tmp_path)
    expected, dispatched = reference(tmp_path)
    first = Stop(*STOPS.get(stop, (None, 1)))
    if stop == "extraction_write":
        real = store.os.rename
        raised = []

        def rename(source, target, *args, **kwargs):
            if not raised and str(source).rsplit("/", 1)[-1].startswith(".extraction-"):
                raised.append(source)
                raise KeyboardInterrupt()
            return real(source, target, *args, **kwargs)

        monkeypatch.setattr(store.os, "rename", rename)
    if stop == "after_proposals":
        rt, alternative = stoppable(config, first)

        def ready():
            raise KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            make_pass(
                config,
                rt,
                alternative,
                partition=Partition.DEV,
                directory=tmp_path / "data/runs/pilot/dev/fresh/s-1/pass",
                fresh="s-1",
                support_ready=ready,
                now=lambda: cases.NOW,
            )
        calls = Counter(first.calls)
    else:
        calls = interrupt(config, tmp_path, "s-1", first)
    pass_dir = tmp_path / "data/runs/pilot/dev/fresh/s-1/pass"
    if stop == "extraction_write":
        assert raised
        assert not (pass_dir / "extraction").exists()
        assert not [p for p in pass_dir.iterdir() if p.name.startswith(".")]
    second = Stop()
    record = fresh_pass(config, tmp_path, "s-1", second, resume=True)
    assert record.status == "complete"
    assert record.mode == "fresh" and record.stability_run_id == "s-1"
    ids, content = outcome(config, record)
    assert content == expected[1]
    if stop == "extraction_write":
        # D21-38 rule 4: extraction counts restart with each process, so the
        # resumed extraction counts the stored reply as a cache hit. Every ID that
        # folds in the extraction record then differs from an uninterrupted run's.
        extraction = load_pass(config, record).sources.stored_run.record
        assert (extraction.requests, extraction.cache_hits) == (0, 1)
    else:
        assert ids == expected[0]
    assert calls + Counter(second.calls) == dispatched
    assert before == main_caches(config, tmp_path)


def test_two_stops_then_a_resume_finish_the_run(tmp_path):
    from collections import Counter

    config, _ = seed_case(tmp_path, seed=True, review=True)
    before = main_caches(config, tmp_path)
    expected, dispatched = reference(tmp_path)
    calls = interrupt(config, tmp_path, "s-1", Stop("classify", 2))
    calls += interrupt(config, tmp_path, "s-1", Stop("score", 2), resume=True)
    last = Stop()
    record = fresh_pass(config, tmp_path, "s-1", last, resume=True)
    assert record.status == "complete"
    assert outcome(config, record) == expected
    assert calls + Counter(last.calls) == dispatched
    assert before == main_caches(config, tmp_path)


def test_resume_with_no_state_refuses_and_dispatches_nothing(tmp_path):
    """A typo in the ID never starts a new run silently (D21-38)."""
    from earnings_pipeline.pilot_workflow import fresh_state_exists
    from earnings_pipeline.theme_config import WorkflowError

    config, _ = seed_case(tmp_path, seed=True, review=True)
    stop = Stop()
    directory = tmp_path / "data/runs/pilot/dev/fresh/typo-1/pass"
    with pytest.raises(WorkflowError, match="malformed_record"):
        fresh_pass(config, tmp_path, "typo-1", stop, resume=True)
    assert stop.calls == []
    assert not fresh_state_exists(config, directory, "typo-1")


def test_resume_ignores_debris_from_a_hard_stop(tmp_path):
    """A hard stop can leave temporary directories and ``.partial`` cache files."""
    from collections import Counter

    from earnings_pipeline.pilot_workflow import load_pass, make_run

    config, _ = seed_case(tmp_path, seed=True, review=True)
    before = main_caches(config, tmp_path)
    expected, dispatched = reference(tmp_path)
    calls = interrupt(config, tmp_path, "s-1", Stop("score", 2))
    root = tmp_path / "data/runs/pilot/dev/fresh/s-1"
    for name in (".extraction-debris", ".support-debris", ".alternative-debris"):
        (root / "pass" / name).mkdir(parents=True)
    (root / "run/.coding-debris").mkdir(parents=True)
    for kind in (config.extraction_cache, config.coding_cache, config.support_cache):
        (tmp_path / kind / "fresh/s-1" / ("ab" * 32 + ".x.partial")).write_bytes(b"x")
    last = Stop()
    record = fresh_pass(config, tmp_path, "s-1", last, resume=True)
    assert record.status == "complete"
    assert outcome(config, record) == expected
    assert calls + Counter(last.calls) == dispatched
    loaded = load_pass(config, record)
    run = make_run(
        config,
        loaded,
        bound_artifact(config, loaded),
        directory=root / "run",
        now=lambda: cases.NOW,
    )
    assert run.fresh == "s-1" and run.status == "complete"
    assert before == main_caches(config, tmp_path)


@pytest.mark.parametrize(
    ("partition", "fresh"),
    [(Partition.DEV, None), (Partition.TRAIN, None), (Partition.TRAIN, "s-1")],
)
def test_resume_without_fresh_or_off_dev_refuses_malformed_record(
    tmp_path, partition, fresh
):
    from earnings_pipeline.pilot_workflow import make_pass
    from earnings_pipeline.theme_config import WorkflowError

    config, _ = seed_case(tmp_path, seed=True, review=True)
    stop = Stop()
    rt, alternative = stoppable(config, stop)
    directory = tmp_path / f"data/runs/pilot/{partition.value}/pass"
    directory.mkdir(parents=True)
    with pytest.raises(WorkflowError, match="malformed_record"):
        make_pass(
            config,
            rt,
            alternative,
            partition=partition,
            directory=directory,
            fresh=fresh,
            support_ready=lambda: None,
            now=lambda: cases.NOW,
            resume=True,
        )
    assert stop.calls == []
    assert not (directory / "extraction").exists()


@pytest.mark.parametrize(
    "where", ["none", "pass", "extraction_cache", "coding_cache", "support_cache"]
)
def test_fresh_state_is_the_pass_or_any_fresh_cache_directory(tmp_path, where):
    """D21-38 rule 2: state is the pass directory or a ``fresh/<id>`` cache
    directory; without ``--resume`` any of them still refuses."""
    from earnings_pipeline.pilot_workflow import fresh_state_exists
    from earnings_pipeline.theme_config import WorkflowError

    config, _ = seed_case(tmp_path, seed=True, review=True)
    directory = tmp_path / "data/runs/pilot/dev/fresh/s-1/pass"
    if where == "pass":
        directory.mkdir(parents=True)
    elif where != "none":
        (tmp_path / getattr(config, where) / "fresh/s-1").mkdir(parents=True)
    assert fresh_state_exists(config, directory, "s-1") is (where != "none")
    assert not fresh_state_exists(config, directory.parent.parent / "s-2", "s-2")
    if where == "none":
        return
    stop = Stop()
    with pytest.raises(WorkflowError, match="state_run_conflict"):
        fresh_pass(config, tmp_path, "s-1", stop)
    assert stop.calls == []


def fresh_run_inputs(root, *, none=False, decided=True):
    """An invented dev repository at ``root`` with a finished fresh pass ``s-1``.

    Returns its config, the pass record, the bound calibration and the run directory.
    With ``decided=False`` the classifier finds no theme, so the run has no decision
    row and its tables hold nothing that binds the record's own fields.
    """
    from earnings_pipeline.pilot_workflow import load_pass, make_pass

    config, _ = seed_case(root, seed=True, review=True)
    rt, alternative = stoppable(config, Stop())
    if not decided:
        model = config.classifier_identity.runtime.model_id
        rt.classifier.script = lambda request: ModelReply(
            model=model, text=json.dumps({"theme_ids": [], "attributes": {}})
        )
    record = make_pass(
        config,
        rt,
        alternative,
        partition=Partition.DEV,
        directory=root / "data/runs/pilot/dev/fresh/s-1/pass",
        fresh="s-1",
        support_ready=lambda: None,
        now=lambda: cases.NOW,
    )
    assert record.status == "complete"
    artifact = bound_artifact(config, load_pass(config, record), none=none)
    return config, record, artifact, root / "data/runs/pilot/dev/fresh/s-1/run"


def run_again(config, record, artifact, directory):
    """One process of ``make_run``: it loads the pass again, as a new process does."""
    from earnings_pipeline.pilot_workflow import load_pass, make_run

    return make_run(
        config,
        load_pass(config, record),
        artifact,
        directory=directory,
        now=lambda: cases.NOW,
    )


def stop_before_run_record(monkeypatch):
    """Make the first write of ``run-record.json`` raise ``KeyboardInterrupt``."""
    from earnings_pipeline import pilot_workflow

    real = pilot_workflow.write_new
    stopped = []

    def write_new(path, payload):
        if path.name == "run-record.json" and not stopped:
            stopped.append(path)
            raise KeyboardInterrupt()
        return real(path, payload)

    monkeypatch.setattr(pilot_workflow, "write_new", write_new)
    return stopped


def stop_after_coding(monkeypatch, config, record, artifact, directory):
    """Stop a run after it published ``run/coding`` and before ``run-record.json``."""
    stopped = stop_before_run_record(monkeypatch)
    with pytest.raises(KeyboardInterrupt):
        run_again(config, record, artifact, directory)
    assert stopped
    assert (directory / "coding/run.json").is_file()
    assert not (directory / "run-record.json").exists()


def coding_files(directory):
    return {p.name: p.read_bytes() for p in (directory / "coding").iterdir()}


def test_a_stop_after_coding_is_published_resumes_to_the_same_record(
    tmp_path, monkeypatch
):
    """D21-38: a stop between ``run/coding`` and ``run-record.json`` resumes at the
    record stage and writes the record of a run that never stopped."""
    from earnings_pipeline import pilot_workflow

    root = tmp_path / "reference"
    root.mkdir()
    expected = run_again(*fresh_run_inputs(root))
    config, record, artifact, directory = fresh_run_inputs(tmp_path)
    writes = []
    real = pilot_workflow.write_coding_run
    monkeypatch.setattr(
        pilot_workflow,
        "write_coding_run",
        lambda *args, **kwargs: (writes.append(args), real(*args, **kwargs))[1],
    )
    stop_after_coding(monkeypatch, config, record, artifact, directory)
    published = coding_files(directory)
    assert len(writes) == 1
    resumed = run_again(config, record, artifact, directory)
    assert resumed == expected
    assert (directory / "run-record.json").read_bytes() == (
        root / "data/runs/pilot/dev/fresh/s-1/run/run-record.json"
    ).read_bytes()
    assert len(writes) == 1
    assert coding_files(directory) == published


@pytest.mark.parametrize(
    ("published_none", "resumed_none"), [(False, True), (True, False)]
)
def test_a_published_coding_run_from_another_policy_refuses_input_changed(
    tmp_path, monkeypatch, published_none, resumed_none
):
    from earnings_pipeline.pilot_workflow import load_pass
    from earnings_pipeline.theme_config import WorkflowError

    config, record, artifact, directory = fresh_run_inputs(
        tmp_path, none=published_none
    )
    other = bound_artifact(config, load_pass(config, record), none=resumed_none)
    stop_after_coding(monkeypatch, config, record, artifact, directory)
    published = coding_files(directory)
    with pytest.raises(WorkflowError, match="input_changed"):
        run_again(config, record, other, directory)
    assert not (directory / "run-record.json").exists()
    assert coding_files(directory) == published


def test_the_read_back_path_runs_the_consuming_gate(tmp_path, monkeypatch):
    """``write_coding_run`` runs ``reverify_coding_run`` before it publishes; a
    resume over a published ``run/coding`` must run it on what it read back."""
    from earnings_pipeline import pilot_workflow
    from earnings_pipeline.pilot_workflow import bind_policy, load_pass

    config, record, artifact, directory = fresh_run_inputs(tmp_path)
    calls = []
    real = pilot_workflow.reverify_coding_run
    monkeypatch.setattr(
        pilot_workflow,
        "reverify_coding_run",
        lambda *args: (calls.append(args), real(*args))[1],
    )
    stop_after_coding(monkeypatch, config, record, artifact, directory)
    assert calls == []
    run_again(config, record, artifact, directory)
    assert len(calls) == 1
    stored, sources, support, policy = calls[0]
    loaded = load_pass(config, record)
    assert any(name.endswith(".parquet") for name, _ in stored.record.artifact_hashes)
    assert sources.provenance_hash == loaded.sources.provenance_hash
    assert support.record == loaded.primary.record
    assert (
        policy.reference
        == bind_policy(config, loaded, artifact, replay=False).reference
    )


def altered_proposal(proposal, how):
    """The same proposal run with one part changed, and the run still self-consistent.

    ``finalize_coding`` and ``write_coding_run`` hash and check it as given, so it
    publishes; only a comparison with the current proposal run can refuse it.
    """
    from dataclasses import replace

    from earnings_themes.coding.records import CodingAttributes

    if how == "table":
        row = proposal.attributes[0].model_copy(
            update={"attributes": CodingAttributes(topic="invented topic")}
        )
        return replace(proposal, attributes=(row, *proposal.attributes[1:]))
    if how == "started_at":
        update = {"started_at": proposal.record.started_at.replace(year=2001)}
    else:
        hashes = [
            (name, "f" * 64 if name == proposal.record.artifact_hashes[0][0] else value)
            for name, value in proposal.record.artifact_hashes
        ]
        assert hashes[0][0].startswith("raw/")
        assert hashes != list(proposal.record.artifact_hashes)
        update = {"artifact_hashes": tuple(hashes)}
    return replace(proposal, record=proposal.record.model_copy(update=update))


@pytest.mark.parametrize("decided", [True, False])
@pytest.mark.parametrize("how", ["table", "started_at", "raw_hash"])
def test_a_published_coding_run_that_differs_in_any_part_refuses_input_changed(
    tmp_path, how, decided
):
    """The comparison covers each table, the record, and the ``raw/`` hashes the
    record keeps; only the ``*.parquet`` hashes are left out. Decision rows bind
    the record's proposal hash, so a run without them needs the record compared."""
    from earnings_pipeline.pilot_workflow import (
        bind_policy,
        load_pass,
        write_coding_run,
    )
    from earnings_pipeline.theme_config import WorkflowError
    from earnings_pipeline.theme_workflow import finalize_coding

    config, record, artifact, directory = fresh_run_inputs(tmp_path, decided=decided)
    loaded = load_pass(config, record)
    assert bool(loaded.proposal.proposals) is decided
    policy = bind_policy(config, loaded, artifact, replay=False)
    other = finalize_coding(
        altered_proposal(loaded.proposal, how), loaded.primary, loaded.sources, policy
    )
    write_coding_run(
        directory / "coding", other, loaded.sources, loaded.primary, policy
    )
    published = coding_files(directory)
    with pytest.raises(WorkflowError, match="input_changed"):
        run_again(config, record, artifact, directory)
    assert not (directory / "run-record.json").exists()
    assert coding_files(directory) == published


def test_a_damaged_published_coding_run_refuses_storage_corrupt(tmp_path, monkeypatch):
    """A published ``run/coding`` that no longer reads back keeps its own closed
    reason, and the run neither rewrites it nor writes a record."""
    from earnings_themes.coding.records import CodingError

    config, record, artifact, directory = fresh_run_inputs(tmp_path)
    stop_after_coding(monkeypatch, config, record, artifact, directory)
    (directory / "coding/attempts.parquet").write_bytes(b"INVENTED")
    damaged = coding_files(directory)
    with pytest.raises(CodingError, match="storage_corrupt"):
        run_again(config, record, artifact, directory)
    assert not (directory / "run-record.json").exists()
    assert coding_files(directory) == damaged
