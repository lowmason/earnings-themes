"""Saved-input V8 integration; assertion outputs expose metadata only."""

import importlib
import json

import pytest
from earnings_core import sha256_hex
from earnings_ingestion.events.state_table import read_runs
from earnings_ingestion.events.states import current_states
from earnings_pipeline.theme_config import load_workflow_config
from earnings_themes.analysis import read_analysis_run

from tests.integration import stage10_cases
from tests.integration.stage10_cases import VerticalCase

no_network = stage10_cases.no_network
vertical_case = stage10_cases.vertical_case


def test_v8_raw_fixture_to_cited_report(vertical_case, no_network):
    result = vertical_case.invoke_replay_cli()
    assert result.exit_code == 0
    summary = vertical_case.safe_summary()
    assert summary["scope"] == "fixture"
    assert summary["processing_schema"] == 2
    assert summary["observation_grain_unique"] is True
    assert summary["all_original_links_preserved"] is True
    assert summary["exact_spans_reverified"] is True
    assert summary["exact_span_rate"] == 1.0
    assert summary["source_and_snapshot_citations"] is True
    assert summary["highlight_occurrence"] is True
    assert summary["immutable_inputs_unchanged"] is True
    assert summary["dispatch_calls"] == summary["count_calls"] == 0
    assert summary["quote_count"] == 1 and summary["theme_count"] == 2
    assert summary["claim_link_count"] == 2 and summary["assignment_claim_count"] == 4
    assert summary["transcript_claim_count"] == 0
    assert summary["fixture_policy"] is True and summary["source_hash_bound"] is True
    assert no_network == []


def test_full_replay_inner_transports_raise_without_dispatch(vertical_case):
    assert vertical_case.invoke_replay_cli().exit_code == 0
    assert len(vertical_case.transports) == 5
    assert all(t.dispatch_calls == t.count_calls == 0 for t in vertical_case.transports)
    for transport in vertical_case.transports:
        with pytest.raises(ValueError, match="^replay_dispatch_forbidden$"):
            transport.count_tokens(None)


def test_partial_replay_cache_miss_never_becomes_no_theme(
    tmp_path, monkeypatch, no_network
):
    case = VerticalCase(tmp_path, monkeypatch, seed=False)
    result = case.invoke_replay_cli()
    assert result.exit_code == 0
    states = current_states(
        read_runs(tmp_path / case.config.states_dir), case.config.pilot_hash
    )
    processing = [s for s in states.values() if s.schema_version == 2]
    assert len(processing) == 1 and processing[0].to_state.value == "failed"
    stored = read_analysis_run(tmp_path / case.config.output_dir / "analysis")
    assert stored.tables.frames["quotes"].height == 0
    assert stored.tables.frames["coverage"]["observable"].sum() == 0
    assert all(t.dispatch_calls == t.count_calls == 0 for t in case.transports)


def test_empty_completed_reply_keeps_exact_rate_undefined(
    tmp_path, monkeypatch, no_network
):
    case = VerticalCase(tmp_path, monkeypatch, empty=True)
    assert case.invoke_replay_cli().exit_code == 0
    summary = case.safe_summary()
    assert summary["exact_span_rate"] is None and summary["quote_count"] == 0
    states = current_states(
        read_runs(tmp_path / case.config.states_dir), case.config.pilot_hash
    )
    assert sum(s.to_state.value == "partial" for s in states.values()) == 1
    assert sum(s.to_state.value == "completed-no-theme" for s in states.values()) == 0


def test_unexpected_abort_preserves_unreported_usage(tmp_path, monkeypatch, no_network):
    case = VerticalCase(tmp_path, monkeypatch, seed=False)
    workflow = importlib.import_module("earnings_pipeline.theme_workflow")

    def abort(*args, **kwargs):
        raise RuntimeError("Invented private failure sentinel")

    monkeypatch.setattr(workflow, "extract_run", abort)
    result = case.invoke_replay_cli()
    assert result.exit_code == 1 and "reason=unexpected_error" in result.output
    assert "private failure" not in result.output
    paths = tuple((tmp_path / case.config.output_dir).glob("failure-*.json"))
    assert len(paths) == 1
    record = workflow.WorkflowFailure.model_validate_json(paths[0].read_bytes())
    assert record.phase == "extraction" and record.usage_availability == "unreported"
    assert not (tmp_path / case.config.output_dir / "extraction/run.json").exists()


def test_publication_pending_then_retry_preserves_inputs_and_analysis(
    vertical_case, monkeypatch
):
    workflow = importlib.import_module("earnings_pipeline.theme_workflow")
    real = workflow.write_theme_report

    def fail(*args, **kwargs):
        raise OSError("Invented private publication sentinel")

    monkeypatch.setattr(workflow, "write_theme_report", fail)
    assert vertical_case.invoke_replay_cli().exit_code == 1
    output = vertical_case.root / vertical_case.config.output_dir
    before = sha256_hex((output / "analysis/run.json").read_bytes())
    first = {p.name for p in output.glob("receipt-*.json")}
    monkeypatch.setattr(workflow, "write_theme_report", real)
    assert vertical_case.invoke_replay_cli().exit_code == 0
    assert sha256_hex((output / "analysis/run.json").read_bytes()) == before
    assert first < {p.name for p in output.glob("receipt-*.json")}
    assert vertical_case.before == vertical_case.input_hashes()


def test_state_pending_then_retry_appends_once(vertical_case, monkeypatch):
    workflow = importlib.import_module("earnings_pipeline.theme_workflow")
    real = workflow.write_processing_run

    def fail(*args, **kwargs):
        raise OSError("Invented private state sentinel")

    monkeypatch.setattr(workflow, "write_processing_run", fail)
    assert vertical_case.invoke_replay_cli().exit_code == 1
    output = vertical_case.root / vertical_case.config.output_dir
    before = sha256_hex((output / "analysis/run.json").read_bytes())
    monkeypatch.setattr(workflow, "write_processing_run", real)
    assert vertical_case.invoke_replay_cli().exit_code == 0
    states = current_states(
        read_runs(vertical_case.root / vertical_case.config.states_dir),
        vertical_case.config.pilot_hash,
    )
    assert sum(s.schema_version == 2 for s in states.values()) == 1
    assert sha256_hex((output / "analysis/run.json").read_bytes()) == before
    assert vertical_case.before == vertical_case.input_hashes()


def test_export_withholds_local_only_evidence(tmp_path, monkeypatch, no_network):
    case = VerticalCase(tmp_path, monkeypatch, local_only=True)
    case.payload["audience"] = "export"
    case.path.write_text(json.dumps(case.payload))
    case.config = load_workflow_config(case.path, repo=tmp_path)
    assert case.invoke_replay_cli().exit_code == 0
    stored = read_analysis_run(tmp_path / case.config.output_dir / "analysis")
    evidence = stored.tables.frames["evidence"]
    assert evidence.height == 1 and set(evidence["status"]) == {"withheld"}
    assert set(evidence["reason"]) == {"rights_restricted"}
    assert evidence["view_artifact"].null_count() == 1
    assert all(t.dispatch_calls == 0 for t in case.transports)


def test_absent_browser_keeps_canonical_fallback_and_pending_v5(vertical_case):
    assert vertical_case.invoke_replay_cli().exit_code == 0
    output = vertical_case.root / vertical_case.config.output_dir
    receipts = tuple(output.glob("receipt-*.json"))
    assert len(receipts) == 1
    workflow = importlib.import_module("earnings_pipeline.theme_workflow")
    receipt = workflow.WorkflowReceipt.model_validate_json(receipts[0].read_bytes())
    assert "browser_observation_not_supplied" in receipt.limitations
    assert "capture_not_supplied" in receipt.limitations
    evidence = read_analysis_run(output / "analysis").tables.frames["evidence"]
    assert (
        set(evidence["status"]) == {"available"}
        and evidence["view_artifact"].null_count() == 0
    )
