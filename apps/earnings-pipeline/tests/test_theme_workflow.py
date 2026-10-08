"""Wholly invented replay composition; guarded public workflow contracts."""

import importlib
import importlib.util


def test_workflow_public_seam_exists():
    assert importlib.util.find_spec("earnings_pipeline.theme_workflow") is not None, (
        "workflow_missing"
    )
    module = importlib.import_module("earnings_pipeline.theme_workflow")
    for name in (
        "WorkflowRuntime",
        "WorkflowFailure",
        "WorkflowReceipt",
        "WorkflowResult",
        "run_theme_workflow",
        "replay_runtime",
    ):
        assert callable(getattr(module, name, None)), "workflow_contract_missing"


import json
import socket
from datetime import UTC, datetime
from pathlib import Path

import pytest
from earnings_core import sha256_hex
from earnings_ingestion.events.state_table import write_run
from earnings_ingestion.events.states import current_states

config_cases = importlib.import_module("apps.earnings-pipeline.tests.test_theme_config")
analysis_cases = importlib.import_module(
    "packages.earnings-themes.tests.analysis.cases"
)
coding_cases = importlib.import_module("packages.earnings-themes.tests.coding.cases")
theme_fixtures = importlib.import_module("packages.earnings-themes.tests.conftest")
NOW = datetime(2026, 10, 7, 13, tzinfo=UTC)
REPO = Path(__file__).resolve().parents[3]


@pytest.fixture(autouse=True)
def socket_guard(monkeypatch):
    trips = []

    def blocked(*args, **kwargs):
        trips.append(1)
        raise AssertionError("network_forbidden")

    for owner, name in (
        (socket.socket, "connect"),
        (socket.socket, "connect_ex"),
        (socket, "create_connection"),
        (socket, "getaddrinfo"),
    ):
        monkeypatch.setattr(owner, name, blocked)
    yield trips
    assert trips == []


def seed_case(tmp_path, *, seed=True, review=False, empty=False, local_only=False):
    """Copy only permitted frozen synthetic metadata; every canonical/source is invented."""
    from earnings_ingestion.cohort.freeze import load_manifest
    from earnings_ingestion.cohort.identity import operative_hash
    from earnings_ingestion.events.fixture import (
        COHORT_MANIFEST,
        FIXTURE_DIR,
        load_transitions,
    )
    from earnings_ingestion.events.freeze import load_event_manifest
    from earnings_ingestion.events.pilot import load_pilot
    from earnings_pipeline.theme_config import load_workflow_config
    from earnings_themes.analysis import (
        AcquisitionStatus,
        AnalysisPolicy,
        ExpectedEvent,
        analysis_provenance_hash,
    )
    from earnings_themes.coding.adapters import ScriptedClassifier
    from earnings_themes.coding.cache import CodingCache
    from earnings_themes.coding.run import propose_run
    from earnings_themes.extraction.adapters import ModelReply, ScriptedAdapter
    from earnings_themes.extraction.cache import CachedAdapter
    from earnings_themes.extraction.prompt import parse_template
    from earnings_themes.extraction.run import extract_run
    from earnings_themes.extraction.store import StoredRun
    from earnings_themes.support.cache import SupportCache
    from earnings_themes.support.records import SupportSources
    from earnings_themes.support.run import assess_run

    payload = config_cases.invented_replay_config(tmp_path)
    root = tmp_path / "inputs"
    root.mkdir()

    def save(relative, data):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return {"path": relative, "sha256": sha256_hex(data)}

    for field, path in (
        ("universe", REPO / COHORT_MANIFEST),
        ("events", REPO / FIXTURE_DIR / "events-v1.json"),
        ("pilot", REPO / FIXTURE_DIR / "pilot-v1.json"),
    ):
        payload[field] = save("inputs/" + path.name, path.read_bytes())
    universe = load_manifest(root / Path(payload["universe"]["path"]).name)
    events = load_event_manifest(root / "events-v1.json")
    pilot = load_pilot(root / "pilot-v1.json", universe)
    history = load_transitions(REPO / FIXTURE_DIR / "acquisition.json")
    latest = current_states(history, pilot.definition.content_hash)
    chosen = next(s for s in latest.values() if s.to_state.value == "parsed")
    missing = tuple(
        s for s in latest.values() if s.to_state.value in {"unavailable", "failed"}
    )
    selected = tuple(sorted((chosen.event_id, *(s.event_id for s in missing))))
    e = next(e for e in events.rows if e.event_id == chosen.event_id)
    expected = ExpectedEvent(
        event_id=e.event_id,
        entity_id=e.issuer_id,
        cik=e.cik,
        period_end=e.period_end,
        fiscal_year=e.reported_fiscal_year,
        fiscal_quarter={"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}.get(
            e.reported_fiscal_quarter
        ),
        eligibility_status=e.eligibility_status.value,
        eligibility_reason=e.eligibility_reason.value,
        membership_assertion_id=e.membership_assertion_id,
        event_manifest_hash=events.definition.content_hash,
        pilot_hash=pilot.definition.content_hash,
    )
    bundle = coding_cases.invented_bundle("invented-workflow-source")
    meta, raw = analysis_cases.metadata(bundle, expected)
    if local_only:
        from dataclasses import replace

        from earnings_core import RightsStatus

        artifact = raw.artifact.model_copy(
            update={"rights_status": RightsStatus.LOCAL_ONLY}
        )
        raw = replace(raw, artifact=artifact)
        meta = meta.model_copy(
            update={
                "rights_status": RightsStatus.LOCAL_ONLY,
                "raw_artifact": artifact,
                "export_text": False,
                "export_raw": False,
                "retain_capture": True,
            }
        )
    snap = analysis_cases.canonical_snapshot(bundle, meta, raw)
    from earnings_core import digest

    parsed_json = json.loads(snap.data)
    meta = meta.model_copy(
        update={
            "canonical_manifest_hash": digest(parsed_json["manifest"]),
            "mask_manifest_hash": analysis_cases.mask_hash(parsed_json),
            "filing_at": e.filing_acceptance_time.astimezone(UTC)
            if e.filing_acceptance_time
            else None,
            "published_at": e.first_publication_time.astimezone(UTC)
            if e.first_publication_time
            else None,
        }
    )
    payload["sources"] = [
        {
            "event_id": e.event_id,
            "doc_id": bundle.document.doc_id,
            "canonical": save("inputs/canonical.json", snap.data),
            "metadata": save("inputs/metadata.json", meta.model_dump_json().encode()),
            "raw": save("inputs/raw.txt", raw.data),
        }
    ]
    keep = {s.document_id for s in (chosen, *missing)}
    history = tuple(
        s.model_copy(
            update={
                "doc_id": bundle.document.doc_id,
                "artifact_sha256": meta.raw_hash,
                "retrieved_at": meta.retrieved_at,
            }
        )
        if s.document_id == chosen.document_id and s.to_state.value == "parsed"
        else s.model_copy(
            update={"artifact_sha256": meta.raw_hash, "retrieved_at": meta.retrieved_at}
        )
        if s.document_id == chosen.document_id and s.to_state.value == "acquired"
        else s
        for s in history
        if s.document_id in keep
    )
    path = write_run(tmp_path / payload["states_dir"], history)
    payload["acquisition_files"] = [
        {
            "path": path.relative_to(tmp_path).as_posix(),
            "sha256": sha256_hex(path.read_bytes()),
        }
    ]
    (path.parent / ".acquire.lock").touch()
    book = coding_cases.invented_codebook(theme_fixtures.codebook.__wrapped__())
    from earnings_themes.codebook import codebook_toml

    payload["codebook"] = save("inputs/book.toml", codebook_toml(book).encode())
    template_text = (REPO / "prompts/extraction/pointer-1.md").read_bytes()
    payload["extraction_prompt"] = save("inputs/extraction.md", template_text)
    payload["coding_prompt"] = save(
        "inputs/coding.md", payload["coding_policy"]["prompt_text"].encode()
    )
    payload["support_prompt"] = save(
        "inputs/support.md", payload["support_policy"]["prompt_text"].encode()
    )
    payload["lockfile"] = save("uv.lock", b"Invented lock identity")
    payload["software"]["lock_hash"] = payload["lockfile"]["sha256"]
    payload.update(
        universe_hash=operative_hash(universe),
        event_hash=events.definition.content_hash,
        pilot_hash=pilot.definition.content_hash,
        selected_event_ids=list(selected),
    )
    payload["analysis_policy"] = AnalysisPolicy(
        population_id="djia-synthetic",
        event_ids=selected,
        population_hash=pilot.definition.content_hash,
        mask_policy_id="invented-mask",
        mask_policy_version="1",
        include_family_view=False,
        scope="fixture",
    ).model_dump(mode="json")
    if review:
        payload["assignment_policy"] = None
    config = load_workflow_config(
        config_cases.write_config(tmp_path, payload), repo=tmp_path
    )
    if not seed:
        return config, payload
    started = config.fixture_started_at
    adapter = ScriptedAdapter(
        lambda request: ModelReply(
            model="scripted",
            text=json.dumps(
                {
                    "candidates": []
                    if empty
                    else [{"quote_labels": ["U1"], "claim": "Invented expansion."}]
                }
            ),
        )
    )

    def extract(mode):
        return StoredRun.of(
            extract_run(
                (bundle,),
                CachedAdapter(adapter, tmp_path / config.extraction_cache, mode),
                config.extraction_policy,
                parse_template(template_text.decode()),
                config.extraction_ceilings,
                run_id=config.extraction_run_id,
                started_at=started,
                software=config.software,
            )
        )

    extract("live")
    stored = extract("replay")
    by_event = {e.event_id: e for e in events.rows}
    expected_rows = tuple(
        ExpectedEvent(
            **(
                expected.model_dump()
                | {
                    "event_id": k,
                    "entity_id": by_event[k].issuer_id,
                    "cik": by_event[k].cik,
                    "period_end": by_event[k].period_end,
                    "fiscal_year": by_event[k].reported_fiscal_year,
                    "fiscal_quarter": {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}.get(
                        by_event[k].reported_fiscal_quarter
                    ),
                    "membership_assertion_id": by_event[k].membership_assertion_id,
                }
            )
        )
        for k in selected
    )
    current = current_states(history, config.pilot_hash)
    acquisitions = tuple(
        AcquisitionStatus(
            event_id=s.event_id,
            document_id=s.document_id,
            state=s.to_state.value,
            missing_reason=s.missing_reason.value if s.missing_reason else None,
            failure_reason=s.failure_reason.value if s.failure_reason else None,
            doc_id=s.doc_id,
            source_document_id=bundle.document.source_document_id if s.doc_id else None,
            raw_hash=s.artifact_sha256,
            accession=s.accession,
            exhibit=s.exhibit,
            retrieved_at=s.retrieved_at,
            state_run_id=s.run_id,
            state_schema_version=s.schema_version,
            pilot_hash=s.pilot_hash,
        )
        for s in sorted(current.values(), key=lambda s: s.document_id)
    )
    provenance = analysis_provenance_hash(
        selected_universe_hash=config.universe_hash,
        expected=expected_rows,
        acquisition=acquisitions,
        metadata=(meta,),
        canonical_snapshots=(snap,),
    )
    sources = SupportSources(stored, (bundle,), book, provenance)
    classifier = ScriptedClassifier(
        lambda request: ModelReply(
            model=config.classifier_identity.runtime.model_id,
            text=json.dumps({"theme_ids": ["capacity"], "attributes": {}}),
        ),
        lambda request: 5,
        config.classifier_identity,
    )

    def propose(mode):
        return propose_run(
            config.coding_run_id,
            sources,
            tuple((c.doc_id, c.claim_id) for c in stored.claims),
            classifier,
            config.coding_policy,
            config.coding_ceilings,
            cache=CodingCache(tmp_path / config.coding_cache, mode),
            started_at=started,
            software=config.software,
        )

    propose("live")
    proposal = propose("replay")
    scorer, judges = coding_cases.make_support_parts()
    assert scorer.identity == config.scorer_identity
    assert tuple(j.identity for j in judges) == config.judge_identities
    assess_run(
        config.support_run_id,
        sources,
        proposal.targets,
        scorer,
        judges,
        config.support_policy,
        config.support_ceilings,
        extractor_family=config.extractor_family,
        cache=SupportCache(tmp_path / config.support_cache, "live"),
        started_at=started,
        software=config.software,
    )
    return config, payload


def test_replay_composes_and_preserves_frozen_inputs(tmp_path):
    config, _ = seed_case(tmp_path)
    module = importlib.import_module("earnings_pipeline.theme_workflow")
    before = {
        p.name: sha256_hex(p.read_bytes()) for p in (tmp_path / "inputs").iterdir()
    }
    runtime = module.replay_runtime(config)
    result = module.run_theme_workflow(config, runtime, now=lambda: NOW)
    assert result.status == "state_recorded", "replay_success_required"
    assert result.state_count == 1
    assert all(
        a.dispatch_calls == a.count_calls == 0
        for a in (
            runtime.extractor,
            runtime.classifier,
            runtime.scorer,
            *runtime.judges,
        )
    )
    assert before == {
        p.name: sha256_hex(p.read_bytes()) for p in (tmp_path / "inputs").iterdir()
    }
    retry = module.run_theme_workflow(
        config, module.replay_runtime(config), now=lambda: NOW
    )
    assert retry.status == "state_recorded" and retry.state_hash == result.state_hash


def test_pending_receipt_retained_then_identical_state_retry(tmp_path, monkeypatch):
    config, _ = seed_case(tmp_path)
    module = importlib.import_module("earnings_pipeline.theme_workflow")
    real = module.write_processing_run
    monkeypatch.setattr(
        module,
        "write_processing_run",
        lambda *args: (_ for _ in ()).throw(
            OSError("Invented forbidden source sentinel")
        ),
    )
    first = module.run_theme_workflow(
        config, module.replay_runtime(config), now=lambda: NOW
    )
    assert first.status == "state_pending"
    monkeypatch.setattr(module, "write_processing_run", real)
    second = module.run_theme_workflow(
        config, module.replay_runtime(config), now=lambda: NOW
    )
    assert second.status == "state_recorded"
    assert first.analysis_hash == second.analysis_hash
    assert first.receipt_id != second.receipt_id


def test_review_and_empty_never_become_negative(tmp_path):
    config, _ = seed_case(tmp_path, review=True, empty=True)
    module = importlib.import_module("earnings_pipeline.theme_workflow")
    result = module.run_theme_workflow(
        config, module.replay_runtime(config), now=lambda: NOW
    )
    assert result.status == "state_recorded"
    from earnings_ingestion.events.state_table import read_runs

    latest = current_states(read_runs(tmp_path / config.states_dir), config.pilot_hash)
    assert sum(s.to_state.value == "partial" for s in latest.values()) == 1
    assert not any(s.to_state.value == "completed-no-theme" for s in latest.values())


def test_unexpected_abort_records_metadata_only_failure(tmp_path, monkeypatch):
    config, _ = seed_case(tmp_path, seed=False)
    module = importlib.import_module("earnings_pipeline.theme_workflow")
    monkeypatch.setattr(
        module,
        "extract_run",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            RuntimeError("Invented forbidden source sentinel")
        ),
    )
    result = module.run_theme_workflow(
        config, module.replay_runtime(config), now=lambda: NOW
    )
    assert result.status == "failed"
    assert result.reason == "unexpected_error"
    assert result.state_count == 1
    for p in (tmp_path / config.output_dir).glob("*.json"):
        assert b"forbidden source sentinel" not in p.read_bytes()


def test_replay_miss_is_visible_and_unobservable(tmp_path):
    config, _ = seed_case(tmp_path, seed=False)
    module = importlib.import_module("earnings_pipeline.theme_workflow")
    runtime = module.replay_runtime(config)
    result = module.run_theme_workflow(config, runtime, now=lambda: NOW)
    assert result.status == "state_recorded"
    from earnings_themes.analysis import read_analysis_run

    stored = read_analysis_run(tmp_path / config.output_dir / "analysis")
    release = stored.tables.frames["coverage"].filter(
        stored.tables.frames["coverage"]["doc_type"] == "release"
    )
    assert sum(release["observable"]) == 0
    assert "replay_miss" in {
        reason for reasons in release["missing_reasons"] for reason in reasons
    }
    assert all(
        a.dispatch_calls == a.count_calls == 0
        for a in (
            runtime.extractor,
            runtime.classifier,
            runtime.scorer,
            *runtime.judges,
        )
    )


def test_changed_config_refuses_completed_same_workflow(tmp_path):
    config, payload = seed_case(tmp_path)
    module = importlib.import_module("earnings_pipeline.theme_workflow")
    first = module.run_theme_workflow(
        config, module.replay_runtime(config), now=lambda: NOW
    )
    assert first.status == "state_recorded"
    payload["audience"] = "export"
    from earnings_pipeline.theme_config import load_workflow_config

    changed = load_workflow_config(
        config_cases.write_config(tmp_path, payload), repo=tmp_path
    )
    with pytest.raises(module.WorkflowError, match="^input_changed$"):
        module.run_theme_workflow(
            changed, module.replay_runtime(changed), now=lambda: NOW
        )


def test_other_workflow_requires_actual_stored_analysis_selection(tmp_path):
    config, payload = seed_case(tmp_path)
    module = importlib.import_module("earnings_pipeline.theme_workflow")
    result = module.run_theme_workflow(
        config, module.replay_runtime(config), now=lambda: NOW
    )
    assert result.status == "state_recorded"
    payload.update(
        run_id="invented-consumer", output_dir="data/runs/workflows/invented-consumer"
    )
    from earnings_pipeline.theme_config import load_workflow_config

    absent = load_workflow_config(
        config_cases.write_config(tmp_path, payload), repo=tmp_path
    )
    refused = module.run_theme_workflow(
        absent, module.replay_runtime(absent), now=lambda: NOW
    )
    assert refused.status == "failed" and refused.reason == "state_not_processable"
    assert refused.failure_hash is not None and refused.state_count == 0
    assert refused.analysis_hash is None and refused.state_hash is None
    for field, kind in (
        ("stored_extraction", "extraction"),
        ("stored_support", "support"),
        ("stored_coding", "coding"),
        ("stored_analysis", "analysis"),
    ):
        directory = Path(config.output_dir) / kind
        payload[field] = {
            "directory": directory.as_posix(),
            "sha256": sha256_hex((tmp_path / directory / "run.json").read_bytes()),
        }
    selected = load_workflow_config(
        config_cases.write_config(tmp_path, payload), repo=tmp_path
    )
    consumed = module.run_theme_workflow(
        selected, module.replay_runtime(selected), now=lambda: NOW
    )
    assert consumed.status == "no_state_change"
    assert consumed.state_count == 0 and consumed.state_hash == result.state_hash
    assert not (tmp_path / config.states_dir / "invented-consumer.parquet").exists()


def test_preflight_source_tampering_creates_no_output(tmp_path):
    config, _ = seed_case(tmp_path)
    module = importlib.import_module("earnings_pipeline.theme_workflow")
    (tmp_path / config.sources[0].canonical.path).write_bytes(
        b"Invented forbidden sentinel"
    )
    with pytest.raises(module.WorkflowError, match="^input_changed$"):
        module.run_theme_workflow(
            config, module.replay_runtime(config), now=lambda: NOW
        )
    assert not (tmp_path / config.output_dir).exists()


def test_workflow_records_reject_arbitrary_reason(tmp_path):
    module = importlib.import_module("earnings_pipeline.theme_workflow")
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        module.WorkflowFailure(
            run_id="invented",
            phase="extraction",
            event_ids=(),
            doc_ids=(),
            reason="Invented forbidden sentinel",
            completed_stages=(),
            usage_availability="unreported",
            created_at=NOW,
        )


def test_workflow_receipt_accepts_closed_state_failure_reason():
    module = importlib.import_module("earnings_pipeline.theme_workflow")
    receipt = module.WorkflowReceipt(
        run_id="invented",
        created_at=NOW,
        config_hash="a" * 64,
        scope="fixture",
        status="failed",
        analysis=None,
        report=None,
        failure=None,
        state=None,
        state_count=0,
        phase_counts=(),
        reason="state_not_processable",
        limitations=(),
    )
    assert receipt.reason == "state_not_processable"


def test_workflow_artifact_refuses_unconfined_identifier():
    module = importlib.import_module("earnings_pipeline.theme_workflow")
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        module.WorkflowArtifact(
            artifact_id="../Invented forbidden sentinel", sha256="a" * 64
        )


def test_failure_refuses_source_bearing_document_identifier():
    from pydantic import ValidationError

    module = importlib.import_module("earnings_pipeline.theme_workflow")
    with pytest.raises(ValidationError):
        module.WorkflowFailure(
            run_id="invented",
            phase="preflight",
            event_ids=("invented-event",),
            doc_ids=("source sentinel\nparagraph",),
            reason="state_not_processable",
            completed_stages=(),
            usage_availability="unreported",
            created_at=NOW,
        )


def test_receipt_refuses_negative_phase_count():
    from pydantic import ValidationError

    module = importlib.import_module("earnings_pipeline.theme_workflow")
    with pytest.raises(ValidationError):
        module.WorkflowReceipt(
            run_id="invented",
            created_at=NOW,
            config_hash="a" * 64,
            scope="fixture",
            status="failed",
            analysis=None,
            report=None,
            failure=None,
            state=None,
            state_count=0,
            phase_counts=(("extraction", -1),),
            reason="unexpected_error",
            limitations=(),
        )


@pytest.mark.parametrize(
    "changes",
    [{"receipt_id": None, "receipt_hash": None}, {"state_count": 1}],
    ids=["missing-receipt", "unbound-state-count"],
)
def test_result_refuses_unbound_required_artifacts(changes):
    module = importlib.import_module("earnings_pipeline.theme_workflow")
    payload = {
        "run_id": "invented",
        "status": "failed",
        "reason": "unexpected_error",
        "receipt_id": "receipt.json",
        "receipt_hash": "a" * 64,
        "analysis_id": None,
        "analysis_hash": None,
        "report_id": None,
        "report_hash": None,
        "failure_id": None,
        "failure_hash": None,
        "state_id": None,
        "state_hash": None,
        "state_count": 0,
        "phase_counts": (),
        "scope": "fixture",
    }
    with pytest.raises(module.WorkflowError, match="^malformed_record$"):
        module.WorkflowResult(**(payload | changes))


def test_source_selection_refuses_source_bearing_identity():
    from earnings_pipeline.theme_config import SourceSelection
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        SourceSelection(
            event_id="invented-event",
            doc_id="source sentinel\nparagraph",
            canonical={"path": "inputs/canonical.json", "sha256": "a" * 64},
            metadata={"path": "inputs/metadata.json", "sha256": "a" * 64},
            raw=None,
        )


@pytest.mark.parametrize(
    "kind",
    [
        "stored-extraction",
        "stored-support",
        "stored-coding",
        "stored-analysis",
        "own-extraction",
        "own-support",
        "own-coding",
        "own-analysis",
        "configuration",
        "report-manifest",
        "history",
        "extraction-cache",
        "support-cache",
        "coding-cache",
        "own-table-extraction",
        "own-table-support",
        "own-table-coding",
        "own-table-analysis",
    ],
    ids=lambda value: value,
)
def test_selected_child_symlink_refuses_before_any_external_reader(
    tmp_path, monkeypatch, kind
):
    config, payload = seed_case(tmp_path)
    module = importlib.import_module("earnings_pipeline.theme_workflow")
    external = tmp_path.parent / (tmp_path.name + "-invented-outside.json")
    external.write_bytes(b"Invented external fixture bytes")
    if kind.startswith("stored-"):
        stage = kind.removeprefix("stored-")
        directory = "data/runs/selected/" + stage
        child = tmp_path / directory / "run.json"
        payload["stored_" + stage] = {
            "directory": directory,
            "sha256": sha256_hex(b"Invented external fixture bytes"),
        }
        if stage == "analysis":
            for other in ("extraction", "support", "coding"):
                companion = tmp_path / "data/runs/selected" / other / "run.json"
                companion.parent.mkdir(parents=True, exist_ok=True)
                companion.write_bytes(b"Invented companion manifest")
                payload["stored_" + other] = {
                    "directory": "data/runs/selected/" + other,
                    "sha256": sha256_hex(b"Invented companion manifest"),
                }
    elif kind.startswith("own-table-"):
        stage = kind.removeprefix("own-table-")
        if stage == "analysis":
            from earnings_themes.analysis.records import TABLE_SCHEMAS

            names = TABLE_SCHEMAS
        else:
            names = importlib.import_module(
                "earnings_themes." + stage + ".store"
            ).SCHEMAS
        child = tmp_path / config.output_dir / stage / (next(iter(names)) + ".parquet")
    elif kind.startswith("own-"):
        child = tmp_path / config.output_dir / kind.removeprefix("own-") / "run.json"
    elif kind == "configuration":
        child = tmp_path / config.output_dir / "configuration.json"
    elif kind == "report-manifest":
        child = tmp_path / config.output_dir / "report/report.json"
    elif kind == "history":
        child = tmp_path / config.states_dir / "invented-extra.parquet"
    else:
        child = (
            tmp_path / getattr(config, kind.replace("-", "_")) / (("b" * 64) + ".json")
        )
    child.parent.mkdir(parents=True, exist_ok=True)
    child.symlink_to(external)
    from earnings_pipeline.theme_config import load_workflow_config

    selected = load_workflow_config(
        config_cases.write_config(tmp_path, payload), repo=tmp_path
    )
    trips = []
    original_bytes, original_text = Path.read_bytes, Path.read_text

    def guarded_bytes(path, *args, **kwargs):
        if path.resolve() == external:
            trips.append(True)
            raise RuntimeError("invented-external-read-sentinel")
        return original_bytes(path, *args, **kwargs)

    def guarded_text(path, *args, **kwargs):
        if path.resolve() == external:
            trips.append(True)
            raise RuntimeError("invented-external-read-sentinel")
        return original_text(path, *args, **kwargs)

    original_history = module.read_runs

    def guarded_history(directory):
        if kind == "history":
            trips.append(True)
            raise RuntimeError("invented-history-reader-sentinel")
        return original_history(directory)

    monkeypatch.setattr(Path, "read_bytes", guarded_bytes)
    monkeypatch.setattr(Path, "read_text", guarded_text)
    monkeypatch.setattr(module, "read_runs", guarded_history)
    output = tmp_path / config.output_dir
    before = (
        {p.relative_to(output).as_posix() for p in output.rglob("*")}
        if output.exists()
        else set()
    )
    with pytest.raises(module.WorkflowError, match="^malformed_record$"):
        module.run_theme_workflow(
            selected, module.replay_runtime(selected), now=lambda: NOW
        )
    assert trips == []
    after = (
        {p.relative_to(output).as_posix() for p in output.rglob("*")}
        if output.exists()
        else set()
    )
    assert before == after
    assert sorted(
        p.name for p in (tmp_path / config.states_dir).glob("*.parquet")
    ) == sorted(
        [Path(config.acquisition_files[0].path).name]
        + ([child.name] if kind == "history" else [])
    )


def test_optional_capture_skips_fully_withheld_export_view(tmp_path):
    from dataclasses import asdict, replace

    from earnings_ingestion.browser.policy import ISOLATED_1
    from earnings_pipeline.theme_config import load_workflow_config
    from earnings_themes.analysis import read_analysis_run

    _config, payload = seed_case(tmp_path, local_only=True)
    capture_policy = asdict(ISOLATED_1)
    capture_policy["required_resource_types"] = sorted(
        ISOLATED_1.required_resource_types
    )
    payload.update(
        audience="export",
        capture=True,
        capture_policy=capture_policy,
        installed_binary_reference={
            "path": "inputs/invented-browser-reference.json",
            "sha256": sha256_hex(b"Invented browser identity"),
        },
    )
    (tmp_path / payload["installed_binary_reference"]["path"]).write_bytes(
        b"Invented browser identity"
    )
    selected = load_workflow_config(
        config_cases.write_config(tmp_path, payload), repo=tmp_path
    )
    module = importlib.import_module("earnings_pipeline.theme_workflow")

    class ForbiddenRenderer:
        def __init__(self):
            self.calls = 0

        @property
        def environment(self):
            self.calls += 1
            raise RuntimeError("invented-renderer-sentinel")

        def capture(self, *args, **kwargs):
            self.calls += 1
            raise RuntimeError("invented-renderer-sentinel")

    renderer = ForbiddenRenderer()
    runtime = replace(module.replay_runtime(selected), renderer=renderer)
    result = module.run_theme_workflow(selected, runtime, now=lambda: NOW)
    assert result.status == "state_recorded" and result.failure_hash is None
    assert renderer.calls == 0
    stored = read_analysis_run(tmp_path / selected.output_dir / "analysis")
    rows = stored.tables.frames["evidence"].to_dicts()
    assert rows and all(
        row["status"] == "withheld" and row["reason"] == "rights_restricted"
        for row in rows
    )
    assert all(
        row["rights_status"] == "local_only"
        and all(
            row[key] is None
            for key in ("raw_artifact", "canonical_artifact", "view_artifact")
        )
        for row in rows
    )
    report = json.loads(
        (tmp_path / selected.output_dir / "report/report.json").read_bytes()
    )
    assert report["audience"] == "export" and report["scope"] == "fixture"
    receipt = json.loads((tmp_path / result.receipt_id).read_bytes())
    assert (
        "capture_nondurable" in receipt["limitations"]
        and "browser_observation_not_supplied" in receipt["limitations"]
    )
    latest = current_states(
        module.read_runs(tmp_path / selected.states_dir), selected.pilot_hash
    )
    assert any(row.to_state.value == "completed" for row in latest.values())


@pytest.mark.parametrize(
    "kind", ["report-artifact", "receipt"], ids=["report-artifact", "receipt"]
)
def test_existing_publication_child_symlink_refuses_before_new_publication(
    tmp_path, monkeypatch, kind
):
    config, _ = seed_case(tmp_path)
    module = importlib.import_module("earnings_pipeline.theme_workflow")
    first = module.run_theme_workflow(
        config, module.replay_runtime(config), now=lambda: NOW
    )
    assert first.status == "state_recorded"
    child = tmp_path / (
        first.receipt_id
        if kind == "receipt"
        else config.output_dir + "/report/report.html"
    )
    external = tmp_path.parent / (tmp_path.name + "-invented-published-target")
    external.write_bytes(child.read_bytes())
    child.unlink()
    child.symlink_to(external)
    trips = []
    original = Path.read_bytes

    def guarded(path, *args, **kwargs):
        if path.resolve() == external:
            trips.append(True)
            raise RuntimeError("invented-target-sentinel")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", guarded)
    output = tmp_path / config.output_dir
    before = {p.relative_to(output).as_posix() for p in output.rglob("*")}
    state_hash = sha256_hex((tmp_path / first.state_id).read_bytes())
    with pytest.raises(module.WorkflowError, match="^malformed_record$"):
        module.run_theme_workflow(
            config, module.replay_runtime(config), now=lambda: NOW
        )
    assert trips == []
    assert before == {p.relative_to(output).as_posix() for p in output.rglob("*")}
    assert state_hash == sha256_hex((tmp_path / first.state_id).read_bytes())


def test_permitted_optional_capture_dispatches_public_fake_renderer(tmp_path):
    from dataclasses import asdict, replace

    from earnings_ingestion.browser import CaptureEnvironment, CaptureStatus
    from earnings_ingestion.browser.policy import ISOLATED_1
    from earnings_ingestion.browser.records import CaptureReason
    from earnings_ingestion.browser.renderer import unrendered
    from earnings_pipeline.theme_config import load_workflow_config
    from earnings_themes.analysis import read_analysis_run

    _config, payload = seed_case(tmp_path, local_only=True)
    capture_policy = asdict(ISOLATED_1)
    capture_policy["required_resource_types"] = sorted(
        ISOLATED_1.required_resource_types
    )
    payload.update(
        capture=True,
        capture_policy=capture_policy,
        installed_binary_reference={
            "path": "inputs/invented-browser-reference.json",
            "sha256": sha256_hex(b"Invented browser identity"),
        },
    )
    (tmp_path / payload["installed_binary_reference"]["path"]).write_bytes(
        b"Invented browser identity"
    )
    selected = load_workflow_config(
        config_cases.write_config(tmp_path, payload), repo=tmp_path
    )
    module = importlib.import_module("earnings_pipeline.theme_workflow")

    class Renderer:
        environment = CaptureEnvironment(
            "invented", "1", "1", "1", "invented", "1", "invented"
        )

        def __init__(self):
            self.calls = []

        def capture(self, saved_html, capture_policy, *, source_document_id):
            self.calls.append(
                (sha256_hex(saved_html), source_document_id, capture_policy)
            )
            return unrendered(
                saved_html,
                capture_policy,
                self.environment,
                source_document_id=source_document_id,
                status=CaptureStatus.UNAVAILABLE,
                reason=CaptureReason.BROWSER_UNAVAILABLE,
                detail="Invented unavailable fake",
                captured_at=NOW,
            )

    renderer = Renderer()
    result = module.run_theme_workflow(
        selected,
        replace(module.replay_runtime(selected), renderer=renderer),
        now=lambda: NOW,
    )
    assert result.status == "state_recorded" and result.failure_hash is None
    assert len(renderer.calls) == 1 and renderer.calls[0][2] == ISOLATED_1
    stored = read_analysis_run(tmp_path / selected.output_dir / "analysis")
    evidence = stored.tables.frames["evidence"].to_dicts()
    assert len(evidence) == 1 and evidence[0]["status"] == "available"
    assert renderer.calls[0][:2] == (
        evidence[0]["view_artifact"]["content_sha256"],
        "invented-workflow-source",
    )
    receipt = json.loads((tmp_path / result.receipt_id).read_bytes())
    assert (
        "capture_nondurable" in receipt["limitations"]
        and "browser_observation_not_supplied" in receipt["limitations"]
    )
