"""Invented inputs and injected runtimes; no optional installation or weights."""

import json
from contextlib import contextmanager
from datetime import date
from hashlib import sha256
from importlib import import_module
from types import SimpleNamespace

import pytest
from earnings_themes.support.problems import SupportError
from earnings_themes.support.scorers import _request


def api():
    return import_module("earnings_themes.support.nli")


class Tensor:
    def __init__(self, values):
        self.values = values
        self.shape = (1, len(values))

    def to(self, *args, **kwargs):
        return self

    def __getitem__(self, key):
        if isinstance(key, tuple):
            self.selection = key
            return Tensor([0.0, 2.0])
        return (
            Tensor([self.values[key]]) if isinstance(self.values[key], float) else self
        )

    def cpu(self):
        return self

    def __float__(self):
        return float(self.values[0])


class Tokenizer:
    eos_token = "</s>"
    eos_token_id = 1
    pad_token_id = 0
    model_max_length = 512

    def convert_ids_to_tokens(self, ids):
        return ["▁", "▁1"]

    def __call__(self, *texts, **options):
        self.last_options = options
        self.texts = texts
        return {"input_ids": Tensor(list(range(sum(len(t.split()) for t in texts))))}


def fixture(tmp_path, kind="minicheck", limit=512):
    module = api()
    files = []
    for name in [
        "config.json",
        "tokenizer_config.json",
        "tokenizer.json",
        "pytorch_model.bin" if kind == "minicheck" else "model.safetensors",
    ]:
        (tmp_path / name).write_bytes(b"{}")
        files.append({"relative_path": name, "sha256": sha256(b"{}").hexdigest()})
    config = module.LocalScorerConfig.model_validate_json(
        json.dumps(
            {
                "kind": kind,
                "local_directory": str(tmp_path),
                "files": files,
                "revision": module.PRIMARY_REVISION
                if kind == "minicheck"
                else module.ALTERNATIVE_REVISION,
                "runtime_versions": [[n, v] for n, v in module.RUNTIME_VERSIONS],
                "device": "cpu",
                "precision": "float32",
                "input_limit": limit,
                "encoding_version": "minicheck-first-step/1"
                if kind == "minicheck"
                else "deberta-pair/1",
                "label_mapping": [3, 209] if kind == "minicheck" else [0, 1, 2],
                "weight_license": {
                    "source_url": "https://example.org/rights",
                    "terms_reference": "invented fixture only",
                    "intended_use": "offline test",
                    "verified_on": str(date(2026, 10, 5)),
                    "permits_use": True,
                },
            }
        )
    )
    tokenizer = Tokenizer()
    model = SimpleNamespace(
        config=SimpleNamespace(
            decoder_start_token_id=0,
            pad_token_id=0,
            eos_token_id=1,
            model_type="t5",
            architectures=["T5ForConditionalGeneration"],
            id2label={0: "entailment", 1: "neutral", 2: "contradiction"},
            max_position_embeddings=512,
        ),
        forward_calls=0,
    )
    if kind == "deberta":
        model.config.model_type = "deberta-v2"
        model.config.architectures = ["DebertaV2ForSequenceClassification"]
        tokenizer.model_max_length = 10**30
    model.eval = lambda: model
    model.to = lambda *a, **k: model

    class Model:
        config = model.config

        def eval(self):
            model.evaluated = True
            return self

        def to(self, *a, **k):
            return self

        def __call__(self, **kwargs):
            model.forward_calls += 1
            model.kwargs = kwargs
            assert model.inference_active
            model.logits = Tensor([0.0, 2.0, 1.0])
            return SimpleNamespace(logits=model.logits)

    calls = []

    def load_tokenizer(path, **options):
        calls.append(options)
        return tokenizer

    def load_model(path, **options):
        calls.append(options)
        return Model()

    @contextmanager
    def inference_mode():
        model.inference_active = True
        try:
            yield
        finally:
            model.inference_active = False

    torch = SimpleNamespace(
        inference_mode=inference_mode,
        tensor=lambda *a, **k: Tensor([0]),
        float32="float32",
        softmax=lambda *a, **k: Tensor([0.2, 0.8, 0.0]),
    )
    scorer = (module.MiniCheckScorer if kind == "minicheck" else module.DebertaScorer)(
        config, _runtime=(torch, load_tokenizer, load_model)
    )
    return scorer, model, tokenizer, calls, config


def test_primary_counts_full_input_before_forward(tmp_path):
    scorer, model, tokenizer, _, _ = fixture(tmp_path, limit=4)
    reply = scorer.score(_request("a b c d e", "The imagined claim."))
    assert reply.score is None and reply.reason == "input_too_long"
    assert model.forward_calls == 0
    assert tokenizer.last_options["truncation"] is False
    assert reply.input_tokens > 4


def test_primary_first_decoder_position_raw_score(tmp_path):
    scorer, model, tokenizer, calls, _ = fixture(tmp_path)
    request = _request("Invented workshop sells blue gadgets.", "The gadgets are blue.")
    reply = scorer.score(request)
    assert reply.score == 0.8
    assert reply.input_hash == request.input_hash and reply.identity == scorer.identity
    assert model.evaluated and model.forward_calls == 1
    assert model.inference_active is False
    assert model.logits.selection == (0, 0, [3, 209])
    assert "decoder_input_ids" in model.kwargs
    assert tokenizer.texts == (
        "predict: " + request.premise + "</s>" + request.hypothesis,
    )
    assert calls[1]["use_safetensors"] is False
    assert calls[1]["weights_only"] is True
    assert all(c["local_files_only"] and c["trust_remote_code"] is False for c in calls)


def test_alternative_model_positions_bound_sentinel(tmp_path):
    scorer, model, _, _, _ = fixture(tmp_path, kind="deberta", limit=1024)
    assert scorer.identity.input_limit == 512
    reply = scorer.score(_request("word " * 513, "Invented hypothesis."))
    assert reply.reason == "input_too_long" and model.forward_calls == 0


def test_hash_mismatch_refuses_before_runtime(tmp_path):
    _, _, _, _, config = fixture(tmp_path)
    (tmp_path / "pytorch_model.bin").write_bytes(b"changed")
    with pytest.raises(SupportError, match="model_mismatch"):
        api().MiniCheckScorer(config, _runtime=(None, None, None))


def test_missing_primary_never_falls_back(tmp_path):
    _, _, _, _, config = fixture(tmp_path)
    (tmp_path / "pytorch_model.bin").unlink()
    with pytest.raises(SupportError, match="model_mismatch"):
        api().MiniCheckScorer(config, _runtime=(None, None, None))


@pytest.mark.parametrize(
    "field,value",
    [
        ("revision", "main"),
        ("label_mapping", [209, 3]),
        ("input_limit", 513),
        ("encoding_version", "deberta-pair/1"),
        ("runtime_versions", [["torch", "other"]]),
        ("local_directory", "relative"),
        ("input_limit", True),
    ],
)
def test_closed_config_refuses_changed_pins(tmp_path, field, value):
    _, _, _, _, config = fixture(tmp_path)
    payload = config.model_dump(mode="json")
    payload[field] = value
    from earnings_themes.support.records import parse_support

    with pytest.raises(SupportError, match="malformed_record"):
        parse_support(payload, api().LocalScorerConfig)


def test_unmanifested_file_refused(tmp_path):
    _, _, _, _, config = fixture(tmp_path)
    (tmp_path / "handler.py").write_text("invented untrusted code", encoding="utf-8")
    with pytest.raises(SupportError, match="model_mismatch"):
        api().MiniCheckScorer(config, _runtime=(None, None, None))


def test_symlink_weight_refused(tmp_path):
    _, _, _, _, config = fixture(tmp_path)
    weights = tmp_path / "pytorch_model.bin"
    weights.unlink()
    weights.symlink_to(tmp_path / "config.json")
    with pytest.raises(SupportError, match="model_mismatch"):
        api().MiniCheckScorer(config, _runtime=(None, None, None))


def test_alternative_pair_and_raw_entailment_probability(tmp_path):
    scorer, model, tokenizer, calls, _ = fixture(tmp_path, kind="deberta")
    request = _request("Imagined source.", "Imagined claim.")
    reply = scorer.score(request)
    assert reply.score == 0.2
    assert tokenizer.texts == (request.premise, request.hypothesis)
    assert "decoder_input_ids" not in model.kwargs
    assert calls[1]["use_safetensors"] is True


def test_bad_model_metadata_refused(tmp_path):
    scorer, _, _, _, _ = fixture(tmp_path)
    scorer.model.config.decoder_start_token_id = 9
    with pytest.raises(SupportError, match="model_mismatch"):
        scorer._check_metadata("minicheck")


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -0.1, 1.1])
def test_nonfinite_or_out_of_range_raw_score_is_unavailable(tmp_path, value):
    scorer, _, _, _, _ = fixture(tmp_path)
    scorer.torch.softmax = lambda *a, **k: Tensor([0.0, value])
    reply = scorer.score(_request("Imagined premise.", "Imagined claim."))
    assert reply.reason == "scorer_failed" and reply.score is None


def test_runtime_error_has_fixed_safe_reply(tmp_path):
    scorer, _, _, _, _ = fixture(tmp_path)

    def fail(*a, **k):
        raise RuntimeError("INVENTED_SECRET_RUNTIME")

    scorer.torch.softmax = fail
    reply = scorer.score(_request("Imagined premise.", "Imagined claim."))
    assert reply.reason == "scorer_failed" and "INVENTED_SECRET" not in repr(reply)


def test_config_roundtrip_safe_render_and_manifest_binding(tmp_path):
    scorer, _, _, _, config = fixture(tmp_path)
    from earnings_themes.support.records import SupportRunRecord, parse_support

    from .test_records import payloads

    assert (
        parse_support(config.model_dump(mode="json"), api().LocalScorerConfig) == config
    )
    assert str(tmp_path) not in repr(config)
    payload = payloads()["SupportRunRecord"]
    payload["scorer_identity"] = scorer.identity.model_dump(mode="json")
    record = parse_support(payload, SupportRunRecord)
    assert record.scorer_identity == scorer.identity


def test_optional_runtime_imports_and_real_softmax_when_installed(tmp_path):
    import importlib.util

    if importlib.util.find_spec("torch") is None:
        pytest.skip("optional runtime absent; default adapter mocks remain enabled")
    import safetensors
    import sentencepiece
    import tokenizers
    import torch
    from transformers import (
        AutoTokenizer,
        DebertaV2ForSequenceClassification,
        T5ForConditionalGeneration,
    )

    assert torch.__version__ == "2.14.1"
    assert all(
        x is not None
        for x in (
            T5ForConditionalGeneration,
            DebertaV2ForSequenceClassification,
            AutoTokenizer,
            sentencepiece,
            tokenizers,
            safetensors,
        )
    )
    assert float(torch.softmax(torch.tensor([0.0, 2.0]), dim=-1)[1]) == pytest.approx(
        0.880797, abs=1e-6
    )


def smoke_environment(monkeypatch):
    from . import test_nli_live

    class DeniedSocket:
        def connect(self, *args):
            raise PermissionError("denied")

        def connect_ex(self, *args):
            raise PermissionError("denied")

        def close(self):
            pass

    monkeypatch.setattr(test_nli_live.socket, "socket", DeniedSocket)
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    return test_nli_live


def test_live_missing_weights_visibly_skip(tmp_path, monkeypatch):
    _, _, _, _, config = fixture(tmp_path)
    config_path = tmp_path.parent / (tmp_path.name + "-config.json")
    config_path.write_text(config.model_dump_json(), encoding="utf-8")
    (tmp_path / "pytorch_model.bin").unlink()
    smoke = smoke_environment(monkeypatch)
    monkeypatch.setenv("INVENTED_CONFIG", str(config_path))
    with pytest.raises(
        pytest.skip.Exception, match="checkpoint absent; V4 remains pending"
    ):
        smoke._local_smoke("INVENTED_CONFIG", "minicheck", monkeypatch)


def test_live_invalid_weights_fail_instead_of_skip(tmp_path, monkeypatch):
    _, _, _, _, config = fixture(tmp_path)
    config_path = tmp_path.parent / (tmp_path.name + "-config.json")
    config_path.write_text(config.model_dump_json(), encoding="utf-8")
    (tmp_path / "pytorch_model.bin").write_bytes(b"changed")
    smoke = smoke_environment(monkeypatch)
    monkeypatch.setenv("INVENTED_CONFIG", str(config_path))
    with pytest.raises(SupportError, match="model_mismatch"):
        smoke._local_smoke("INVENTED_CONFIG", "minicheck", monkeypatch)


@pytest.mark.parametrize("resolved", [False, True])
def test_live_data_config_path_refused_before_read(tmp_path, monkeypatch, resolved):
    data_path = tmp_path / "data" / "config.json"
    data_path.parent.mkdir()
    data_path.write_text("{}", encoding="utf-8")
    config_path = data_path
    if resolved:
        config_path = tmp_path / "linked.json"
        config_path.symlink_to(data_path)
    smoke = smoke_environment(monkeypatch)
    monkeypatch.setenv("INVENTED_CONFIG", str(config_path))
    reads = []

    def refuse_read(path):
        reads.append(1)
        raise AssertionError("forbidden_read")

    monkeypatch.setattr(type(config_path), "read_bytes", refuse_read)
    with pytest.raises(pytest.fail.Exception, match="forbidden_local_path"):
        smoke._local_smoke("INVENTED_CONFIG", "minicheck", monkeypatch)
    assert reads == []


@pytest.mark.parametrize("resolved", [False, True])
def test_live_data_model_directory_refused_before_read_or_constructor(
    tmp_path, monkeypatch, resolved
):
    _, _, _, _, config = fixture(tmp_path)
    data_path = tmp_path / "data" / "checkpoint"
    data_path.mkdir(parents=True)
    model_path = data_path
    if resolved:
        model_path = tmp_path / "linked-checkpoint"
        model_path.symlink_to(data_path, target_is_directory=True)
    config_path = tmp_path / "external-config.json"
    payload = config.model_dump(mode="json")
    payload["local_directory"] = str(model_path)
    config_path.write_text(json.dumps(payload), encoding="utf-8")
    smoke = smoke_environment(monkeypatch)
    monkeypatch.setenv("INVENTED_CONFIG", str(config_path))
    original_read = type(config_path).read_bytes
    reads = []
    constructs = []

    def checked_read(path):
        reads.append(path)
        assert path == config_path
        return original_read(path)

    def refuse_constructor(*args, **kwargs):
        constructs.append(1)
        raise AssertionError("constructor_called")

    monkeypatch.setattr(type(config_path), "read_bytes", checked_read)
    monkeypatch.setattr(api(), "MiniCheckScorer", refuse_constructor)
    with pytest.raises(pytest.fail.Exception, match="forbidden_local_path"):
        smoke._local_smoke("INVENTED_CONFIG", "minicheck", monkeypatch)
    assert reads == [config_path] and constructs == []


@pytest.mark.parametrize("kind", ["minicheck", "deberta"])
def test_shared_constructor_gate_refuses_hash_change_for_both_kinds(tmp_path, kind):
    _, _, _, _, config = fixture(tmp_path, kind=kind)
    (tmp_path / "config.json").write_bytes(b"changed")
    with pytest.raises(SupportError, match="model_mismatch"):
        api()._prepare_config(config, kind)


def test_shared_runtime_version_gate_redacts_failures(monkeypatch):
    module = api()
    monkeypatch.setattr(module, "version", lambda name: "unapproved")
    with pytest.raises(SupportError, match="model_mismatch"):
        module._verify_runtime_versions()

    def failed_version(name):
        raise RuntimeError("INVENTED_RUNTIME_SENTINEL")

    monkeypatch.setattr(module, "version", failed_version)
    with pytest.raises(SupportError, match="model_mismatch") as caught:
        module._verify_runtime_versions()
    assert "INVENTED_RUNTIME_SENTINEL" not in repr(caught.value)
    assert caught.value.__suppress_context__


@pytest.mark.parametrize(
    "update",
    [
        {"INVENTED_EXTRA_SENTINEL": "INVENTED_PRIVATE_VALUE"},
        {"label_mapping": [3, 209]},
    ],
)
def test_shared_preflight_rejects_forged_raw_state_before_serializing(tmp_path, update):
    import warnings

    _, _, _, _, config = fixture(tmp_path)
    forged = config.model_copy(update=update)
    with (
        warnings.catch_warnings(record=True) as recorded,
        pytest.raises(SupportError, match="model_mismatch"),
    ):
        api()._prepare_config(forged, "minicheck")
    assert recorded == []
