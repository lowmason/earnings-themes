"""Explicit invented JSON configuration; no implicit source or model discovery."""

import importlib
import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_core import sha256_hex
from earnings_themes.analysis import AnalysisPolicy
from earnings_themes.coding.records import CodingCeilings, CodingPolicy
from earnings_themes.extraction.records import (
    AdapterIdentity,
    Ceilings,
    ExtractionPolicy,
    Parameters,
)
from earnings_themes.support.records import (
    JudgeIdentity,
    RuntimeIdentity,
    ScorerIdentity,
    SupportCeilings,
    SupportPolicy,
)


def module():
    assert importlib.util.find_spec("earnings_pipeline.theme_config") is not None, (
        "config_missing"
    )
    return importlib.import_module("earnings_pipeline.theme_config")


def invented_replay_config(tmp_path):
    runtime = RuntimeIdentity(
        model_id="invented-support",
        revision="fixture-1",
        files=(),
        runtime="scripted",
        runtime_version="1",
        device="cpu",
        precision="float32",
        encoding_version="fixture-1",
    )

    def pin(path):
        return {"path": path, "sha256": "a" * 64}

    coding = "Invented classification instructions."
    support = "Invented support instructions."
    return {
        "schema_version": 1,
        "run_id": "invented-workflow",
        "scope": "fixture",
        "mode": "replay",
        "fixture_started_at": "2026-10-07T12:00:00Z",
        "input_root": "inputs",
        "universe": pin("inputs/djia-synthetic-v1.json"),
        "universe_hash": "a" * 64,
        "events": pin("inputs/events-v1.json"),
        "event_hash": "a" * 64,
        "pilot": pin("inputs/pilot-v1.json"),
        "pilot_hash": "a" * 64,
        "selected_event_ids": ["invented-event"],
        "states_dir": "data/runs/events/states",
        "acquisition_files": [pin("data/runs/events/states/invented-acquire.parquet")],
        "sources": [],
        "codebook": pin("inputs/book.json"),
        "extraction_prompt": pin("inputs/extraction.md"),
        "coding_prompt": pin("inputs/coding.md"),
        "support_prompt": pin("inputs/support.md"),
        "extraction_policy": ExtractionPolicy(
            parameters=Parameters(max_tokens=64)
        ).model_dump(mode="json"),
        "extraction_ceilings": Ceilings(
            requests_per_document=8, requests_per_run=40, tokens_per_run=100000
        ).model_dump(mode="json"),
        "extraction_identity": AdapterIdentity(
            adapter_kind="scripted", model_id="scripted"
        ).model_dump(mode="json"),
        "extractor_family": "invented-extractor",
        "coding_policy": CodingPolicy(
            prompt_text=coding,
            prompt_hash=sha256_hex(coding.encode()),
            parameters=Parameters(max_tokens=64),
        ).model_dump(mode="json"),
        "coding_ceilings": CodingCeilings(
            requests_per_claim=2,
            requests_per_document=20,
            requests_per_run=40,
            tokens_per_document=100000,
            tokens_per_run=200000,
        ).model_dump(mode="json"),
        "classifier_identity": JudgeIdentity(
            family="invented-classifier",
            runtime=runtime,
            input_limit=100000,
            output_limit=2048,
            hosting="scripted",
            weight_license=None,
        ).model_dump(mode="json"),
        "support_policy": SupportPolicy(
            support_version="semantic-support/1",
            prompt_text=support,
            prompt_hash=sha256_hex(support.encode()),
            parameters=Parameters(max_tokens=64),
        ).model_dump(mode="json"),
        "support_ceilings": SupportCeilings(
            scorer_per_target=40,
            scorer_per_document=40,
            scorer_per_run=40,
            judge_per_target=40,
            judge_per_document=40,
            judge_per_run=40,
            tokens_per_document=200000,
            tokens_per_run=200000,
        ).model_dump(mode="json"),
        "scorer_identity": ScorerIdentity(
            kind="scripted", runtime=runtime, input_limit=100000
        ).model_dump(mode="json"),
        "judge_identities": [
            JudgeIdentity(
                family=f"invented-family-{i}",
                runtime=runtime,
                input_limit=100000,
                output_limit=2048,
                hosting="scripted",
                weight_license=None,
            ).model_dump(mode="json")
            for i in range(2)
        ],
        "extraction_run_id": "invented-extraction",
        "coding_run_id": "invented-coding",
        "support_run_id": "invented-support",
        "extraction_cache": "data/runs/caches/extraction",
        "coding_cache": "data/runs/caches/coding",
        "support_cache": "data/runs/caches/support",
        "stored_extraction": None,
        "stored_support": None,
        "stored_coding": None,
        "stored_analysis": None,
        "assignment_policy": "fixture-supporting/1",
        "policy_reference": None,
        "analysis_policy": AnalysisPolicy(
            population_id="djia-synthetic",
            event_ids=("invented-event",),
            population_hash="a" * 64,
            mask_policy_id="invented-mask",
            mask_policy_version="1",
            include_family_view=False,
            scope="fixture",
        ).model_dump(mode="json"),
        "families": None,
        "copies": [],
        "no_theme": [],
        "audience": "local",
        "output_dir": "data/runs/workflows/invented-workflow",
        "capture": False,
        "capture_policy": None,
        "installed_binary_reference": None,
        "software": {"fixture": "1", "lock_hash": "a" * 64},
        "lockfile": pin("uv.lock"),
    }


def write_config(tmp_path, payload):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_live_mode_refuses_before_input_loading(tmp_path):
    m = module()
    payload = invented_replay_config(tmp_path)
    payload["mode"] = "live"
    with pytest.raises(m.WorkflowError, match="^malformed_record$"):
        m.load_workflow_config(write_config(tmp_path, payload), repo=tmp_path)
    assert not (tmp_path / "data/runs").exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("output_dir", "../outside"),
        ("extraction_cache", "/tmp/cache"),
        ("run_id", "../run"),
        ("fixture_started_at", "2026-10-07T12:00:00+01:00"),
        ("mode", "hosted"),
    ],
    ids=["traversal", "absolute", "run", "clock", "hosted"],
)
def test_config_refuses_unsafe_selection(tmp_path, field, value):
    m = module()
    payload = invented_replay_config(tmp_path)
    payload[field] = value
    with pytest.raises(m.WorkflowError):
        m.load_workflow_config(write_config(tmp_path, payload), repo=tmp_path)
    assert not (tmp_path / "data/runs").exists()


def test_config_replay_is_explicit_and_confined(tmp_path):
    m = module()
    config = m.load_workflow_config(
        write_config(tmp_path, invented_replay_config(tmp_path)), repo=tmp_path
    )
    assert config.mode == "replay" and config.scope == "fixture"


def test_symlink_escape_refuses_without_inputs(tmp_path):
    m = module()
    (tmp_path / "inputs").symlink_to(tmp_path.parent, target_is_directory=True)
    with pytest.raises(m.WorkflowError):
        m.load_workflow_config(
            write_config(tmp_path, invented_replay_config(tmp_path)), repo=tmp_path
        )


def test_missing_calibrated_policy_is_unavailable_before_loading(tmp_path):
    m = module()
    payload = invented_replay_config(tmp_path)
    payload["assignment_policy"] = None
    payload["policy_reference"] = {
        "policy_id": "invented-calibrated",
        "policy_hash": "a" * 64,
        "kind": "calibrated",
        "codebook": {
            "codebook_id": "invented",
            "codebook_version": 0,
            "content_hash": "a" * 64,
        },
        "classifier_configuration_hash": "a" * 64,
        "support_configuration_hash": "a" * 64,
        "calibration_reference": "a" * 64,
    }
    with pytest.raises(m.WorkflowError, match="^policy_unavailable$"):
        m.load_workflow_config(write_config(tmp_path, payload), repo=tmp_path)
    assert not (tmp_path / "data/runs").exists()


def test_research_cannot_use_fixture_policy_or_clock(tmp_path):
    m = module()
    payload = invented_replay_config(tmp_path)
    payload["scope"] = payload["analysis_policy"]["scope"] = "research"
    with pytest.raises(m.WorkflowError, match="^malformed_record$"):
        m.load_workflow_config(write_config(tmp_path, payload), repo=tmp_path)


@pytest.mark.parametrize(
    "input_root", ["data", "data/invented"], ids=["exact-root", "descendant"]
)
def test_actual_protected_fixture_root_refuses_before_source_loading(
    tmp_path, monkeypatch, input_root
):
    m = module()
    workflow = importlib.import_module("earnings_pipeline.theme_workflow")
    repo = Path(m.__file__).resolve().parents[4]
    payload = invented_replay_config(tmp_path)
    payload["input_root"] = input_root
    for name in (
        "universe",
        "events",
        "pilot",
        "codebook",
        "extraction_prompt",
        "coding_prompt",
        "support_prompt",
    ):
        payload[name]["path"] = payload[name]["path"].replace(
            "inputs/", input_root + "/"
        )
    selected_reads = []

    def forbidden_reader(*args):
        selected_reads.append(True)
        raise RuntimeError("invented-reader-sentinel")

    monkeypatch.setattr(workflow, "_load_metadata", forbidden_reader)
    config = m.WorkflowConfig.model_validate_json(json.dumps(payload))
    config._repo = repo
    with pytest.raises(m.WorkflowError, match="^malformed_record$"):
        workflow.run_theme_workflow(
            config,
            workflow.replay_runtime(config),
            now=lambda: datetime(2026, 10, 7, tzinfo=UTC),
        )
    assert selected_reads == []
    with pytest.raises(m.WorkflowError, match="^malformed_record$"):
        m.load_workflow_config(write_config(tmp_path, payload), repo=repo)


def test_invented_miniature_repository_data_root_remains_allowed(tmp_path):
    m = module()
    payload = invented_replay_config(tmp_path)
    payload["input_root"] = "data"
    for name in (
        "universe",
        "events",
        "pilot",
        "codebook",
        "extraction_prompt",
        "coding_prompt",
        "support_prompt",
    ):
        payload[name]["path"] = payload[name]["path"].replace("inputs/", "data/")
    config = m.load_workflow_config(write_config(tmp_path, payload), repo=tmp_path)
    assert config.repo == tmp_path.resolve() and config.input_root == "data"
