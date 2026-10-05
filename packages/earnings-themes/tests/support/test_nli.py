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
