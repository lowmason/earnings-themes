"""A8's shared workflow seams, with invented sources and no concrete runtime."""

import importlib
import json

import pytest
from earnings_core import digest
from earnings_pipeline.model_runtime import ChatModelFile
from earnings_pipeline.theme_config import WorkflowError, load_workflow_config
from pydantic import ValidationError

cases = importlib.import_module("apps.earnings-pipeline.tests.test_theme_workflow")
model_cases = importlib.import_module("apps.earnings-pipeline.tests.test_model_runtime")


def test_family_is_id_safe_before_hashing_or_loading(tmp_path):
    fields = model_cases.chat_file(tmp_path, "invented", "unsafe family", 8080)
    with pytest.raises(ValidationError):
        ChatModelFile.model_validate_json(json.dumps(fields, default=str))


def test_metadata_loader_shares_parse_confine_and_preserves_extract_policy_gate(
    tmp_path,
):
    from earnings_pipeline.theme_config import parse_workflow_config
    from earnings_themes.coding.records import PolicyReference

    config, _ = cases.seed_case(tmp_path, seed=False, review=True)
    path = tmp_path / "bound.json"
    config = config.model_copy(
        update={
            "policy_reference": PolicyReference(
                policy_id="calibrated-invented",
                policy_hash="a" * 64,
                kind="calibrated",
                codebook={
                    "codebook_id": "invented",
                    "codebook_version": 0,
                    "content_hash": "a" * 64,
                },
                classifier_configuration_hash="b" * 64,
                support_configuration_hash="c" * 64,
                calibration_reference="d" * 64,
            )
        }
    )
    path.write_text(config.model_dump_json())
    parsed = parse_workflow_config(path, repo=tmp_path)
    assert parsed.policy_reference == config.policy_reference
    assert parsed.repo == tmp_path
    with pytest.raises(WorkflowError, match="policy_unavailable"):
        load_workflow_config(path, repo=tmp_path)


def test_typed_inputs_and_hashes_use_the_same_library_configuration(tmp_path):
    from earnings_pipeline.theme_workflow import (
        load_workflow_inputs,
        replay_runtime,
        workflow_configuration_hashes,
    )
    from earnings_themes.coding.cache import CodingCache
    from earnings_themes.coding.run import propose_run
    from earnings_themes.support.records import SupportSources, support_configuration

    config, _ = cases.seed_case(tmp_path, review=True)
    runtime = replay_runtime(config)
    loaded = load_workflow_inputs(config, runtime)
    from earnings_themes.extraction.cache import CachedAdapter
    from earnings_themes.extraction.run import extract_run
    from earnings_themes.extraction.store import StoredRun

    extraction = StoredRun.of(
        extract_run(
            loaded.bundles,
            CachedAdapter(
                runtime.extractor, tmp_path / config.extraction_cache, "replay"
            ),
            config.extraction_policy,
            loaded.template,
            config.extraction_ceilings,
            run_id=config.extraction_run_id,
            started_at=config.fixture_started_at,
            software=config.software,
        )
    )
    sources = SupportSources(
        extraction, loaded.bundles, loaded.codebook, loaded.provenance_hash
    )
    proposal = propose_run(
        config.coding_run_id,
        sources,
        tuple((c.doc_id, c.claim_id) for c in extraction.claims),
        runtime.classifier,
        config.coding_policy,
        config.coding_ceilings,
        cache=CodingCache(tmp_path / config.coding_cache, "replay"),
        started_at=extraction.record.started_at,
        software=config.software,
    )
    coding_hash, support_hash = workflow_configuration_hashes(config, sources)
    assert coding_hash == proposal.record.configuration_hash
    assert support_hash == digest(
        support_configuration(
            config.support_policy,
            config.support_ceilings,
            config.scorer_identity,
            config.judge_identities,
            config.extractor_family,
            "replay",
        )
    )
    assert all(
        a.dispatch_calls == a.count_calls == 0
        for a in (
            runtime.extractor,
            runtime.classifier,
            runtime.scorer,
            *runtime.judges,
        )
    )
    assert loaded.acquisition
    assert isinstance(loaded.provenance_hash, str)


def test_shared_policy_reference_gate_refuses_unbound_policy(tmp_path):
    from earnings_pipeline.theme_workflow import validate_workflow_policy

    config, _ = cases.seed_case(tmp_path, seed=False, review=True)
    validate_workflow_policy(config, None)
    with pytest.raises(WorkflowError, match="policy_mismatch"):
        validate_workflow_policy(config, object())
    config = config.model_copy(update={"policy_reference": object()})
    with pytest.raises(WorkflowError, match="policy_unavailable"):
        validate_workflow_policy(config, None)
