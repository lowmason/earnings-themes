"""Strict local A8 records and intake guards, entirely invented."""

import importlib
import json

import pytest
from earnings_core import sha256_hex
from earnings_pipeline.theme_config import WorkflowError
from earnings_themes.records import RecordError
from pydantic import ValidationError

cases = importlib.import_module("apps.earnings-pipeline.tests.test_theme_workflow")


def test_settings_confine_all_files_and_bind_bytes(tmp_path):
    from earnings_pipeline.pilot_records import PilotSettings, load_settings

    config, _ = cases.seed_case(tmp_path, seed=False, review=True)
    path = tmp_path / "workflow.json"
    path.write_text(config.model_dump_json())
    selected = {"path": "workflow.json", "sha256": sha256_hex(path.read_bytes())}
    fields = {
        "train": selected,
        "dev": selected,
        "runtime_manifest": selected,
        "alternative_scorer": {
            **config.scorer_identity.model_dump(mode="json"),
            "kind": "deberta",
        },
    }
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(json.dumps(fields))
    settings = load_settings(settings_path, repo=tmp_path)
    assert isinstance(settings, PilotSettings)
    fields["train"]["path"] = "../outside.json"
    settings_path.write_text(json.dumps(fields))
    with pytest.raises(WorkflowError, match="malformed_record"):
        load_settings(settings_path, repo=tmp_path)


def test_pass_record_requires_dev_fresh_and_checked_hash(tmp_path):
    from earnings_pipeline.pilot_records import PassRecord, read_json
    from earnings_themes.records import sealed

    selected = {
        "directory": "data/runs/pilot/train/pass/extraction",
        "sha256": "a" * 64,
    }
    fields = {
        "partition": "train",
        "mode": "fresh",
        "stability_run_id": "fresh-1",
        "event_ids": ["invented:event"],
        "configuration_hash": "b" * 64,
        "extraction": selected,
        "proposals": {
            "path": "data/runs/pilot/train/pass/proposals.json",
            "sha256": "c" * 64,
        },
        "primary": selected,
        "alternative": selected,
        "status": "complete",
        "content_hash": "0" * 64,
    }
    with pytest.raises(ValidationError):
        PassRecord.model_validate_json(json.dumps(fields))
    fields.update(partition="dev")
    record = sealed(PassRecord.model_validate_json(json.dumps(fields)))
    path = tmp_path / "pass.json"
    path.write_text(record.model_dump_json())
    assert read_json(path, PassRecord, "pass") == record
    fields = record.model_dump(mode="json")
    fields["status"] = "partial"
    path.write_text(json.dumps(fields))
    with pytest.raises(RecordError):
        read_json(path, PassRecord, "pass")


def test_calibration_reader_redacts_untrusted_bytes_and_checks_hash(tmp_path):
    from earnings_pipeline.pilot_records import read_calibration

    path = tmp_path / "calibration.json"
    path.write_text('"INVENTED_SOURCE_SENTINEL"')
    with pytest.raises(RecordError) as caught:
        read_calibration(path)
    assert "INVENTED_SOURCE_SENTINEL" not in str(caught.value)

    from earnings_themes.evaluation import CalibrationArtifact
    from earnings_themes.records import sealed

    artifact = sealed(
        CalibrationArtifact(
            calibration_version=1,
            preregistration_hash="a" * 64,
            labels_hash="b" * 64,
            configuration_hash="c" * 64,
            train_labels=0,
            usable_labels=0,
            families=(),
            candidates=(),
            outcome="no_candidate",
            selection=None,
            scorers=(),
            content_hash="0" * 64,
        )
    )
    path.write_text(artifact.model_dump_json())
    assert read_calibration(path) == artifact
    fields = artifact.model_dump(mode="json")
    assert fields["content_hash"] != "0" * 64
    fields["content_hash"] = "0" * 64
    path.write_text(json.dumps(fields))
    with pytest.raises(RecordError) as caught:
        read_calibration(path)
    assert caught.value.problems == ("does not hash to its content_hash",)
