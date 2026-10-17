import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools import stage11_fixture_smoke as smoke


def test_smoke_limits_are_documented():
    path = Path(__file__).resolve().parents[2] / "docs/data-dictionary.md"
    text = path.read_text()
    heading = "## Stage 11 fixture-smoke limits"
    assert text.count(heading) == 1
    section = text.split(heading, 1)[1].split("\n## ", 1)[0]
    assert all(f"`{name}`" in section for name in smoke.Limits.model_fields)


def test_unknown_fixture_refuses_before_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(
        smoke, "committed", lambda *args: b'[[fixtures]]\nfixture_id="invented"\n'
    )
    called = []
    with pytest.raises(smoke.SmokeRefused, match="^fixture_not_allowlisted$"):
        smoke.smoke(
            tmp_path,
            "config/models/runtime.toml",
            tmp_path / "models",
            "not-allowlisted",
            "limits.json",
            "test",
            builder=lambda *a: called.append(1),
        )
    assert called == []
    assert not (tmp_path / "data").exists()


def test_changed_fixture_bytes_refuse_before_runtime(tmp_path, monkeypatch):
    path = tmp_path / "tests/fixtures/canonical/invented.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"changed fixture")
    manifest = b'[[fixtures]]\nfixture_id="invented"\n'

    def git_show(args, **kwargs):
        value = manifest if args[-1].endswith("manifest.toml") else b"HEAD fixture"
        return SimpleNamespace(returncode=0, stdout=value)

    manifest_path = tmp_path / "tests/fixtures/releases/manifest.toml"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_bytes(manifest)
    monkeypatch.setattr(smoke.subprocess, "run", git_show)
    called = []
    with pytest.raises(smoke.SmokeRefused, match="^fixture_not_committed$"):
        smoke.smoke(
            tmp_path,
            "config/models/runtime.toml",
            tmp_path / "models",
            "invented",
            "limits.json",
            "test",
            builder=lambda *a: called.append(1),
        )
    assert called == []


def test_panel_refuses_either_judge_matching_extractor_before_builder(
    tmp_path, monkeypatch
):
    model_cases = importlib.import_module(
        "apps.earnings-pipeline.tests.test_model_runtime"
    )
    root = tmp_path / "config/models/panel"
    root.mkdir(parents=True)
    manifest, _ = model_cases.layout(root, families=("gemma", "gemma", "other"))
    with pytest.raises(smoke.SmokeRefused, match="^judge_family_conflict$"):
        smoke.panel(tmp_path, manifest)


def test_measurement_never_emits_exception_wording():
    class Failing:
        identity = object()

        def count_tokens(self, request):
            return 7

        def complete(self, request):
            raise RuntimeError("INVENTED_SOURCE_SENTINEL")

    rows, printed = [], []
    wrapped = smoke.Measured(Failing(), "judge_a", rows, printed.append)
    with pytest.raises(RuntimeError):
        wrapped.complete(object())
    assert rows[0]["status"] == "failed"
    assert isinstance(rows[0]["elapsed_ms"], int)
    assert "INVENTED_SOURCE_SENTINEL" not in json.dumps(printed)


def test_main_closes_python_and_native_diagnostics(monkeypatch, capfd):
    def noisy(*args, **kwargs):
        import os

        print("INVENTED_SOURCE_SENTINEL")
        os.write(2, b"INVENTED_SOURCE_SENTINEL")
        raise RuntimeError("INVENTED_SOURCE_SENTINEL")

    monkeypatch.setattr(smoke, "smoke", noisy)
    options = [
        "--manifest",
        "a",
        "--models-root",
        "b",
        "--fixture-id",
        "c",
        "--limits",
        "d",
        "--run-id",
        "e",
    ]
    assert smoke.main(options) == 1
    captured = capfd.readouterr()
    assert "smoke_failed" in captured.out
    assert "INVENTED_SOURCE_SENTINEL" not in captured.out + captured.err


def invented_setup(tmp_path, monkeypatch):
    cases = importlib.import_module("apps.earnings-pipeline.tests.test_theme_workflow")
    pilot_cases = importlib.import_module(
        "apps.earnings-pipeline.tests.test_pilot_workflow"
    )
    config, _ = cases.seed_case(tmp_path, seed=False, review=True)
    contents = {
        "tests/fixtures/releases/manifest.toml": b'[[fixtures]]\nfixture_id="invented"\n',
        "tests/fixtures/canonical/invented.json": (
            tmp_path / config.sources[0].canonical.path
        ).read_bytes(),
        "prompts/extraction/pointer-1.md": (
            tmp_path / config.extraction_prompt.path
        ).read_bytes(),
        "prompts/coding/deductive-1.md": config.coding_policy.prompt_text.encode(),
        "prompts/support/judge-1.md": config.support_policy.prompt_text.encode(),
        "codebooks/djia-pilot/codebook-v0.toml": (
            tmp_path / config.codebook.path
        ).read_bytes(),
        "uv.lock": b"invented lock identity",
    }
    for name, data in contents.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    path = tmp_path / "config/models/runtime.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("invented manifest; panel checked separately")
    limits = smoke.Limits(
        extraction_policy=config.extraction_policy,
        extraction_ceilings=config.extraction_ceilings,
        coding_parameters=config.coding_policy.parameters,
        coding_ceilings=config.coding_ceilings,
        support_parameters=config.support_policy.parameters,
        support_ceilings=config.support_ceilings,
    )
    (tmp_path / "limits.json").write_text(limits.model_dump_json())
    monkeypatch.setattr(smoke, "committed", lambda repo, name: contents[name])
    monkeypatch.setattr(smoke, "panel", lambda *args: None)
    phases = []
    from earnings_themes.support.records import ScorerIdentity
    from earnings_themes.support.scorers import ScoreReply, ScriptedScorer

    workflow = pilot_cases.runtime(config, phases)
    # The alternative must have a distinct identity or its scorer calls hit the primary cache.
    fields = workflow.scorer.identity.model_dump(mode="json")
    fields["runtime"]["model_id"] = "invented-alternative"
    alternative_identity = ScorerIdentity.model_validate_json(json.dumps(fields))
    alternative = ScriptedScorer(
        lambda request: ScoreReply(
            score=0.25,
            reason=None,
            input_tokens=5,
            latency_ms=1,
            identity=alternative_identity,
            input_hash=request.input_hash,
        ),
        lambda request: 5,
        alternative_identity,
    )
    rt = SimpleNamespace(
        workflow=workflow,
        alternative_scorer=alternative,
        extractor_family=config.extractor_family,
    )
    return rt, phases


def test_real_library_smoke_on_invented_inputs(tmp_path, monkeypatch):
    rt, phases = invented_setup(tmp_path, monkeypatch)
    rows = []
    result = smoke.smoke(
        tmp_path,
        "config/models/runtime.toml",
        tmp_path / "models",
        "invented",
        "limits.json",
        "test",
        builder=lambda *args: rt,
        ready=lambda: phases.append("ready") or True,
        sink=rows.append,
    )
    assert result["status"] == "complete"
    assert set(result["role_calls"]) == {
        "extractor",
        "classifier",
        "judge_a",
        "judge_b",
        "minicheck",
        "deberta",
    }
    assert all(count > 0 for count in result["role_calls"].values())
    assert phases.index("extract") < phases.index("classify") < phases.index("ready")
    assert (tmp_path / "data/runs/stage11-fixture-smoke/test/summary.json").is_file()
    assert not (tmp_path / "data/runs/pilot").exists()
    assert "Invented expansion" not in json.dumps(rows)


def test_existing_run_refuses_before_runtime(tmp_path, monkeypatch):
    invented_setup(tmp_path, monkeypatch)
    (tmp_path / "data/runs/stage11-fixture-smoke/test").mkdir(parents=True)
    called = []
    with pytest.raises(smoke.SmokeRefused, match="^output_exists$"):
        smoke.smoke(
            tmp_path,
            "config/models/runtime.toml",
            tmp_path / "models",
            "invented",
            "limits.json",
            "test",
            builder=lambda *args: called.append(1),
        )
    assert called == []


def test_unconfirmed_operator_checkpoint_does_not_dispatch_support(
    tmp_path, monkeypatch
):
    rt, _ = invented_setup(tmp_path, monkeypatch)
    rows = []
    with pytest.raises(smoke.SmokeRefused, match="^support_not_ready$"):
        smoke.smoke(
            tmp_path,
            "config/models/runtime.toml",
            tmp_path / "models",
            "invented",
            "limits.json",
            "test",
            builder=lambda *args: rt,
            ready=lambda: False,
            sink=rows.append,
        )
    assert {row["role"] for row in rows} == {"extractor", "classifier"}
    assert not (tmp_path / "data/runs/stage11-fixture-smoke/test/summary.json").exists()


@pytest.mark.parametrize("empty_stage", ["extraction", "classification"])
def test_empty_stage_cannot_claim_an_all_role_smoke(tmp_path, monkeypatch, empty_stage):
    from dataclasses import replace

    from earnings_themes.coding.adapters import ScriptedClassifier
    from earnings_themes.extraction.adapters import ModelReply, ScriptedAdapter

    rt, _ = invented_setup(tmp_path, monkeypatch)
    if empty_stage == "extraction":
        adapter = ScriptedAdapter(
            lambda request: ModelReply(
                model="scripted",
                text='{"candidates":[]}',
            )
        )
        rt.workflow = replace(rt.workflow, extractor=adapter)
        reason = "extraction_incomplete_or_empty"
    else:
        adapter = ScriptedClassifier(
            lambda request: ModelReply(
                model=rt.workflow.classifier.identity.runtime.model_id,
                text='{"theme_ids":[],"attributes":{}}',
            ),
            lambda request: 5,
            rt.workflow.classifier.identity,
        )
        rt.workflow = replace(rt.workflow, classifier=adapter)
        reason = "classification_incomplete_or_empty"
    rows = []
    with pytest.raises(smoke.SmokeRefused, match="^" + reason + "$"):
        smoke.smoke(
            tmp_path,
            "config/models/runtime.toml",
            tmp_path / "models",
            "invented",
            "limits.json",
            "test",
            builder=lambda *args: rt,
            ready=lambda: True,
            sink=rows.append,
        )
    assert not any(
        row["role"] in {"minicheck", "deberta", "judge_a", "judge_b"} for row in rows
    )
    assert not (tmp_path / "data/runs/stage11-fixture-smoke/test/summary.json").exists()


@pytest.mark.parametrize(
    "families",
    [("gemma", "gemma", "other"), ("gemma", "other", "gemma")],
    ids=["first-judge-gemma", "second-judge-gemma"],
)
def test_smoke_rejects_gemma_judge_before_runtime(tmp_path, monkeypatch, families):
    real_panel = smoke.panel
    invented_setup(tmp_path, monkeypatch)
    monkeypatch.setattr(smoke, "panel", real_panel)
    model_cases = importlib.import_module(
        "apps.earnings-pipeline.tests.test_model_runtime"
    )
    root = tmp_path / "config/models/panel"
    root.mkdir(parents=True)
    manifest, _ = model_cases.layout(root, families=families)
    called = []

    def forbidden_builder(*args):
        called.append(1)
        raise AssertionError("runtime_constructed_before_panel_refusal")

    with pytest.raises(smoke.SmokeRefused, match="^judge_family_conflict$"):
        smoke.smoke(
            tmp_path,
            manifest.relative_to(tmp_path).as_posix(),
            tmp_path / "models",
            "invented",
            "limits.json",
            "test",
            builder=forbidden_builder,
        )
    assert called == []
    assert not (tmp_path / "data/runs/stage11-fixture-smoke/test").exists()
