"""Explicit, local-only raw NLI adapters. Importing this module loads no runtime."""

from hashlib import file_digest
from importlib.metadata import version
from math import isfinite
from pathlib import Path
from time import perf_counter
from typing import Any, Literal, Self

from pydantic import Field, PositiveInt, model_validator

from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import (
    FileHash,
    RuntimeIdentity,
    SafePart,
    ScorerIdentity,
    WeightLicense,
    parse_support,
)
from earnings_themes.support.resolve import _validated
from earnings_themes.support.scorers import ScoreReply, ScoreRequest, _request

PRIMARY_REVISION = "96eafd01cee2d16cf81aaa2fb226b14f422a37b3"
ALTERNATIVE_REVISION = "6f5cf0a2b59cabb106aca4c287eed12e357e90eb"
RUNTIME_VERSIONS = (
    ("torch", "2.14.1"),
    ("transformers", "5.18.0"),
    ("sentencepiece", "0.2.2"),
    ("tokenizers", "0.23.2"),
    ("safetensors", "0.8.0"),
)


class LocalScorerConfig(SafePart):
    kind: Literal["minicheck", "deberta"]
    local_directory: str = Field(repr=False)
    revision: str
    files: tuple[FileHash, ...]
    runtime_versions: tuple[tuple[str, str], ...]
    device: Literal["cpu", "mps"]
    precision: Literal["float32"]
    input_limit: PositiveInt
    encoding_version: Literal["minicheck-first-step/1", "deberta-pair/1"]
    label_mapping: tuple[int, ...]
    weight_license: WeightLicense

    @model_validator(mode="after")
    def _pinned(self) -> Self:
        primary = self.kind == "minicheck"
        if (
            not Path(self.local_directory).is_absolute()
            or self.revision != (PRIMARY_REVISION if primary else ALTERNATIVE_REVISION)
            or self.runtime_versions != RUNTIME_VERSIONS
            or self.encoding_version
            != ("minicheck-first-step/1" if primary else "deberta-pair/1")
            or self.label_mapping != ((3, 209) if primary else (0, 1, 2))
            or (primary and self.input_limit > 512)
        ):
            raise ValueError("model_mismatch")
        names = [f.relative_path for f in self.files]
        if len(names) != len(set(names)) or not {
            "config.json",
            "tokenizer_config.json",
            "tokenizer.json",
            "pytorch_model.bin" if primary else "model.safetensors",
        } <= set(names):
            raise ValueError("model_mismatch")
        return self


def _verify_files(config: LocalScorerConfig) -> None:
    root = Path(config.local_directory).resolve(strict=True)
    expected = {f.relative_path: f.sha256 for f in config.files}
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    if actual != set(expected):
        raise SupportError("model_mismatch")
    for name, checksum in expected.items():
        path = root / name
        if path.is_symlink() or not path.resolve(strict=True).is_relative_to(root):
            raise SupportError("model_mismatch")
        with path.open("rb") as stream:
            if file_digest(stream, "sha256").hexdigest() != checksum:
                raise SupportError("model_mismatch")


def _prepare_config(
    config: LocalScorerConfig, kind: Literal["minicheck", "deberta"]
) -> LocalScorerConfig:
    """Apply the same configuration/file identity gate to either constructor."""
    try:
        checked = _validated(config, LocalScorerConfig)
        if checked.kind != kind:
            raise SupportError("model_mismatch")
        _verify_files(checked)
        return checked
    except Exception:  # noqa: BLE001 - redact arbitrary configuration/file errors
        raise SupportError("model_mismatch") from None


def _verify_runtime_versions() -> None:
    """Require the pinned installed runtime before either heavyweight import."""
    try:
        if any(version(name) != pin for name, pin in RUNTIME_VERSIONS):
            raise SupportError("model_mismatch")
    except Exception:  # noqa: BLE001 - redact arbitrary packaging diagnostics
        raise SupportError("model_mismatch") from None


class _LocalScorer:
    def _initialize(
        self,
        config: LocalScorerConfig,
        runtime: tuple[Any, Any, Any],
        kind: Literal["minicheck", "deberta"],
    ) -> None:
        try:
            self.config = config
            self.torch, tokenizer_loader, model_loader = runtime
            options = {"local_files_only": True, "trust_remote_code": False}
            self.tokenizer = tokenizer_loader(self.config.local_directory, **options)
            self.model = model_loader(
                self.config.local_directory,
                **options,
                use_safetensors=(kind == "deberta"),
                weights_only=True,
            )
            self.model.to(device=self.config.device, dtype=self.torch.float32)
            self.model.eval()
            self._check_metadata(kind)
            limit = self.config.input_limit
            if kind == "deberta":
                limit = min(limit, self.model.config.max_position_embeddings)
            self._identity = ScorerIdentity(
                kind=kind,
                input_limit=limit,
                runtime=RuntimeIdentity(
                    model_id="lytang/MiniCheck-Flan-T5-Large"
                    if kind == "minicheck"
                    else "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli",
                    revision=self.config.revision,
                    files=self.config.files,
                    runtime=";".join(n for n, _ in self.config.runtime_versions),
                    runtime_version=";".join(
                        v for _, v in self.config.runtime_versions
                    ),
                    device=self.config.device,
                    precision=self.config.precision,
                    encoding_version=self.config.encoding_version
                    + (
                        ";pytorch-weights-only"
                        if kind == "minicheck"
                        else ";safetensors"
                    ),
                ),
            )
        except Exception:  # noqa: BLE001 - redact arbitrary runtime/file diagnostics
            raise SupportError("model_mismatch") from None

    def _check_metadata(self, kind: Literal["minicheck", "deberta"]) -> None:
        model = self.model.config
        if kind == "minicheck":
            valid = (
                model.model_type == "t5"
                and model.architectures == ["T5ForConditionalGeneration"]
                and model.decoder_start_token_id == 0
                and model.pad_token_id == 0
                and model.eos_token_id == 1
                and self.tokenizer.eos_token == "</s>"
                and self.tokenizer.pad_token_id == 0
                and self.tokenizer.eos_token_id == 1
                and self.tokenizer.model_max_length == 512
                and self.tokenizer.convert_ids_to_tokens([3, 209]) == ["▁", "▁1"]
            )
        else:
            valid = (
                model.model_type == "deberta-v2"
                and model.architectures == ["DebertaV2ForSequenceClassification"]
                and model.id2label
                == {0: "entailment", 1: "neutral", 2: "contradiction"}
                and type(model.max_position_embeddings) is int
                and model.max_position_embeddings == 512
            )
        if not valid:
            raise SupportError("model_mismatch")

    @property
    def identity(self) -> ScorerIdentity:
        return self._identity

    def _encode(self, request: ScoreRequest) -> dict[str, Any]:
        request = parse_support(request.model_dump(mode="json"), ScoreRequest)
        if (
            request.input_hash
            != _request(request.premise, request.hypothesis).input_hash
        ):
            raise SupportError("input_changed")
        args = (
            (
                "predict: "
                + request.premise
                + self.tokenizer.eos_token
                + request.hypothesis,
            )
            if self.config.kind == "minicheck"
            else (request.premise, request.hypothesis)
        )
        return self.tokenizer(*args, return_tensors="pt", truncation=False)

    def count_tokens(self, request: ScoreRequest) -> int:
        try:
            return int(self._encode(request)["input_ids"].shape[-1])
        except Exception:  # noqa: BLE001 - redact arbitrary runtime/file diagnostics
            raise SupportError("scorer_failed") from None

    def score(self, request: ScoreRequest) -> ScoreReply:
        started = perf_counter()
        tokens = None
        score = None
        reason = None
        try:
            encoded = self._encode(request)
            tokens = int(encoded["input_ids"].shape[-1])
            if tokens > self.identity.input_limit:
                reason = "input_too_long"
            else:
                with self.torch.inference_mode():
                    inputs = {k: v.to(self.config.device) for k, v in encoded.items()}
                    if self.config.kind == "minicheck":
                        inputs["decoder_input_ids"] = self.torch.tensor(
                            [[0]], device=self.config.device
                        )
                        logits = self.model(**inputs).logits[0, 0, [3, 209]]
                        score = float(self.torch.softmax(logits, dim=-1)[1].cpu())
                    else:
                        logits = self.model(**inputs).logits[0]
                        score = float(self.torch.softmax(logits, dim=-1)[0].cpu())
                if not isfinite(score) or not 0 <= score <= 1:
                    score = None
                    reason = "scorer_failed"
        except Exception:  # noqa: BLE001 - redact arbitrary runtime/file diagnostics
            score = None
            reason = "scorer_failed"
        return ScoreReply(
            score=score,
            reason=reason,
            input_tokens=tokens,
            latency_ms=max(0, int((perf_counter() - started) * 1000)),
            identity=self.identity,
            input_hash=request.input_hash,
        )


class MiniCheckScorer(_LocalScorer):
    def __init__(
        self, config: LocalScorerConfig, *, _runtime: tuple[Any, Any, Any] | None = None
    ) -> None:
        config = _prepare_config(config, "minicheck")
        if _runtime is None:
            _verify_runtime_versions()
            try:
                import torch
                from transformers import AutoTokenizer, T5ForConditionalGeneration

                _runtime = (
                    torch,
                    AutoTokenizer.from_pretrained,
                    T5ForConditionalGeneration.from_pretrained,
                )
            except Exception:  # noqa: BLE001 - redact arbitrary runtime/file diagnostics
                raise SupportError("model_mismatch") from None
        self._initialize(config, _runtime, "minicheck")


class DebertaScorer(_LocalScorer):
    def __init__(
        self, config: LocalScorerConfig, *, _runtime: tuple[Any, Any, Any] | None = None
    ) -> None:
        config = _prepare_config(config, "deberta")
        if _runtime is None:
            _verify_runtime_versions()
            try:
                import torch
                from transformers import (
                    AutoTokenizer,
                    DebertaV2ForSequenceClassification,
                )

                _runtime = (
                    torch,
                    AutoTokenizer.from_pretrained,
                    DebertaV2ForSequenceClassification.from_pretrained,
                )
            except Exception:  # noqa: BLE001 - redact arbitrary runtime/file diagnostics
                raise SupportError("model_mismatch") from None
        self._initialize(config, _runtime, "deberta")
