"""A2's live runtime, built from invented model files under a temporary models root,
with injected tokenizers, scorer runtimes and an httpx mock transport: no weights,
no optional runtime, and no model server (the Stage 11 spec, A2; plan 18)."""

import json
import subprocess
import sys
from datetime import date
from hashlib import sha256
from pathlib import Path
from types import ModuleType, SimpleNamespace

import httpx
import pytest
import tomllib
from earnings_pipeline.model_runtime import CHAT_ENCODING, build_runtime
from earnings_pipeline.theme_config import WorkflowError
from earnings_themes.extraction.adapters import (
    Message,
    ModelReply,
    ModelRequest,
    RequestSubject,
    ScriptedAdapter,
)
from earnings_themes.extraction.cache import CachedAdapter
from earnings_themes.extraction.records import Parameters
from earnings_themes.support import nli
from earnings_themes.support.model_files import files_hash
from earnings_themes.support.nli import (
    ALTERNATIVE_REVISION,
    PRIMARY_REVISION,
    RUNTIME_VERSIONS,
)
from earnings_themes.support.records import FileHash
from earnings_themes.tomlfile import dumps

LICENSE = {
    "source_url": "https://example.test/license",
    "terms_reference": "invented fixture only",
    "intended_use": "offline test",
    "verified_on": date(2026, 10, 12),
    "permits_use": True,
}
WEIGHTS = {"model.gguf": b"invented weights"}
TOKENIZER = {"tokenizer.json": b"{}", "tokenizer_config.json": b"{}"}
SCORER_FILES = {
    "minicheck": (
        "config.json",
        "tokenizer_config.json",
        "tokenizer.json",
        "pytorch_model.bin",
    ),
    "deberta": (
        "config.json",
        "tokenizer_config.json",
        "tokenizer.json",
        "model.safetensors",
    ),
}
CHAT = ("gemma", "judge-a", "judge-b")


def hashes(directory: Path, files: dict[str, bytes]) -> list[dict]:
    directory.mkdir(parents=True)
    for name, data in files.items():
        (directory / name).write_bytes(data)
    return [
        {"relative_path": name, "sha256": sha256(data).hexdigest()}
        for name, data in sorted(files.items())
    ]


def chat_file(models: Path, name: str, family: str, port: int) -> dict:
    return {
        "family": family,
        "base_url": f"http://127.0.0.1:{port}/v1",
        "model_id": f"{name}-model",
        "runtime": "llama.cpp",
        "runtime_version": "invented-1",
        "revision": "invented-revision",
        "device": "metal",
        "precision": "q4_0",
        "input_limit": 8192,
        "output_limit": 1024,
        "weights_directory": f"{name}/weights",
        "weights": hashes(models / name / "weights", WEIGHTS),
        "tokenizer_directory": f"{name}/tokenizer",
        "tokenizer_files": hashes(models / name / "tokenizer", TOKENIZER),
        "weight_license": LICENSE,
    }


def scorer_file(models: Path, kind: str) -> dict:
    primary = kind == "minicheck"
    return {
        "kind": kind,
        "directory": kind,
        "revision": PRIMARY_REVISION if primary else ALTERNATIVE_REVISION,
        "files": hashes(models / kind, dict.fromkeys(SCORER_FILES[kind], b"{}")),
        "runtime_versions": [list(pair) for pair in RUNTIME_VERSIONS],
        "device": "cpu",
        "precision": "float32",
        "input_limit": 512,
        "encoding_version": "minicheck-first-step/1" if primary else "deberta-pair/1",
        "label_mapping": [3, 209] if primary else [0, 1, 2],
        "weight_license": LICENSE,
    }


def write(path: Path, data: dict) -> None:
    path.write_text(dumps(data), encoding="utf-8")


def layout(tmp_path: Path, families=CHAT) -> tuple[Path, Path]:
    """A manifest and a models root; the extractor and classifier share one file."""
    models, config = tmp_path / "models", tmp_path / "config"
    config.mkdir()
    for port, (name, family) in enumerate(zip(CHAT, families, strict=True), 8080):
        write(config / f"{name}.toml", chat_file(models, name, family, port))
    for kind in SCORER_FILES:
        write(config / f"{kind}.toml", scorer_file(models, kind))
    write(
        config / "runtime.toml",
        {
            "extractor": "gemma.toml",
            "classifier": "gemma.toml",
            "judges": ["judge-a.toml", "judge-b.toml"],
            "scorer": "minicheck.toml",
            "alternative_scorer": "deberta.toml",
        },
    )
    return config / "runtime.toml", models


class ChatTokenizer:
    chat_template = "invented"

    def __init__(self, calls: list) -> None:
        self.calls = calls

    def apply_chat_template(self, messages, **options):
        self.calls.append("render")
        return " ".join(m["content"] for m in messages)

    def __call__(self, text, **options):
        self.calls.append("encode")
        return {"input_ids": text.split()}


def scorer_runtime(loaded: list):
    """MiniCheck's and DeBERTa's checked metadata, by directory name."""

    def tokenizer(path, **options):
        loaded.append(Path(path).name)
        return SimpleNamespace(
            eos_token="</s>",
            pad_token_id=0,
            eos_token_id=1,
            model_max_length=512,
            convert_ids_to_tokens=lambda ids: ["▁", "▁1"],
        )

    def model(path, **options):
        primary = Path(path).name == "minicheck"
        loaded_model = SimpleNamespace(
            config=SimpleNamespace(
                model_type="t5" if primary else "deberta-v2",
                architectures=[
                    "T5ForConditionalGeneration"
                    if primary
                    else "DebertaV2ForSequenceClassification"
                ],
                decoder_start_token_id=0,
                pad_token_id=0,
                eos_token_id=1,
                id2label={0: "entailment", 1: "neutral", 2: "contradiction"},
                max_position_embeddings=512,
            )
        )
        loaded_model.to = lambda **kwargs: loaded_model
        loaded_model.eval = lambda: loaded_model
        return loaded_model

    return (SimpleNamespace(float32="float32"), tokenizer, model)


def failing(calls: list) -> httpx.MockTransport:
    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        raise AssertionError("no request may be sent")

    return httpx.MockTransport(handle)


def build(manifest, models, *, transport=None, calls=None, loaded=None):
    calls = [] if calls is None else calls
    return build_runtime(
        manifest,
        models,
        transport=transport or failing(calls),
        _tokenizer_loader=lambda path, **options: ChatTokenizer(calls),
        _scorer_runtime=scorer_runtime([] if loaded is None else loaded),
    )


def request() -> ModelRequest:
    return ModelRequest(
        messages=(
            Message(role="system", content="Invented system text."),
            Message(role="user", content="[U1] Invented unit."),
        ),
        reply_schema={"type": "object"},
        parameters=Parameters(),
        subject=RequestSubject(
            doc_id="doc@walker-1#0123456789abcdef",
            canonical_hash="a" * 64,
            window_id="w-0-10",
            unit_ids=("sentence-0-10",),
            window_budget=4000,
            claim_limit=500,
            prompt_sha256="b" * 64,
            extractor_version="pointer-traversal/1",
            validator_version="3",
        ),
    )


def test_builds_every_role_from_its_file_and_calls_nothing(tmp_path: Path) -> None:
    manifest, models = layout(tmp_path)
    calls: list = []
    loaded: list = []
    live = build(manifest, models, calls=calls, loaded=loaded)
    runtime = live.workflow
    extractor = runtime.extractor.identity
    assert (extractor.adapter_kind, extractor.model_id, extractor.weights_sha256) == (
        "local",
        "gemma-model",
        sha256(WEIGHTS["model.gguf"]).hexdigest(),
    )
    classifier = runtime.classifier.identity
    tokenizer = tuple(
        FileHash(relative_path=name, sha256=sha256(data).hexdigest())
        for name, data in sorted(TOKENIZER.items())
    )
    assert (classifier.family, classifier.hosting, classifier.runtime.model_id) == (
        "gemma",
        "local",
        "gemma-model",
    )
    assert classifier.runtime.encoding_version == CHAT_ENCODING + files_hash(tokenizer)
    assert [j.identity.family for j in runtime.judges] == ["judge-a", "judge-b"]
    assert (runtime.scorer.identity.kind, live.alternative_scorer.identity.kind) == (
        "minicheck",
        "deberta",
    )
    assert (live.extractor_family, runtime.assignment_policy, runtime.renderer) == (
        "gemma",
        None,
        None,
    )
    assert sorted(loaded) == ["deberta", "minicheck"]
    assert calls == []


def test_the_extractor_dispatches_through_the_given_transport(tmp_path: Path) -> None:
    manifest, models = layout(tmp_path)
    sent: list = []

    def serve(request: httpx.Request) -> httpx.Response:
        sent.append((str(request.url), json.loads(request.content)["model"]))
        return httpx.Response(
            200,
            json={"model": "gemma-model", "choices": [{"message": {"content": "{}"}}]},
        )

    live = build(manifest, models, transport=httpx.MockTransport(serve))
    reply = live.workflow.extractor.complete(request())
    assert (reply.text, reply.model) == ("{}", "gemma-model")
    assert sent == [("http://127.0.0.1:8080/v1/chat/completions", "gemma-model")]


@pytest.mark.parametrize(
    "families", [("gemma", "judge-a", "judge-a"), ("gemma", "gemma", "gemma")]
)
def test_a_panel_that_breaks_stage_8_s_family_rules_is_refused_first(
    tmp_path: Path, families
) -> None:
    """D18-11: the panel is checked before any model file is hashed or loaded, so
    with every model file gone the refusal is still invalid_panel."""
    manifest, models = layout(tmp_path, families)
    for path in models.rglob("*"):
        if path.is_file():
            path.unlink()
    calls: list = []
    loaded: list = []
    with pytest.raises(WorkflowError, match="^invalid_panel$"):
        build(manifest, models, calls=calls, loaded=loaded)
    assert (calls, loaded) == ([], [])


@pytest.mark.parametrize("directory", ["judge-b/weights", "judge-b/tokenizer"])
@pytest.mark.parametrize("change", ["edit", "extra"])
def test_a_model_directory_that_does_not_match_its_file_is_refused(
    tmp_path: Path, directory, change
) -> None:
    manifest, models = layout(tmp_path)
    target = models / directory
    if change == "edit":
        first = min(p for p in target.iterdir() if p.is_file())
        first.write_bytes(b"changed bytes")
    else:
        (target / "README.md").write_bytes(b"an unlisted file")
    with pytest.raises(WorkflowError, match="^model_mismatch$"):
        build(manifest, models)


@pytest.mark.parametrize(
    "name,field,value",
    [
        ("judge-a.toml", "weights_directory", "../elsewhere"),
        ("judge-a.toml", "tokenizer_directory", "/absolute"),
        ("minicheck.toml", "directory", "../elsewhere"),
    ],
)
def test_a_directory_outside_the_models_root_is_refused(
    tmp_path: Path, name, field, value
) -> None:
    manifest, models = layout(tmp_path)
    path = manifest.parent / name
    write(path, {**tomllib.loads(path.read_text(encoding="utf-8")), field: value})
    with pytest.raises(WorkflowError, match="^malformed_record$"):
        build(manifest, models)


def test_a_scorer_file_never_names_an_absolute_local_directory(tmp_path: Path) -> None:
    """D18-9: no committed file holds a path on this machine."""
    manifest, models = layout(tmp_path)
    path = manifest.parent / "minicheck.toml"
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    write(path, {**data, "local_directory": str(models / "minicheck")})
    with pytest.raises(WorkflowError, match="^malformed_record$"):
        build(manifest, models)


@pytest.mark.parametrize(
    "changes",
    [
        {"judges": ["judge-a.toml", "judge-b.toml", "gemma.toml"]},
        {"scorer": "absent.toml"},
        {"extractor": "../gemma.toml"},
    ],
)
def test_a_manifest_that_does_not_read_is_refused(tmp_path: Path, changes) -> None:
    manifest, models = layout(tmp_path)
    data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    write(manifest, {**data, **changes})
    with pytest.raises(WorkflowError, match="^malformed_record$"):
        build(manifest, models)


@pytest.mark.parametrize("role", ["extractor", "scorer"])
def test_a_model_file_that_is_a_directory_is_refused_without_its_path(
    tmp_path: Path, role
) -> None:
    """A refusal is a closed reason, never an operating-system error that carries a
    path on this machine: a chat model's file and a scorer's file are read the same
    way, so both are checked."""
    manifest, models = layout(tmp_path)
    (manifest.parent / "a-directory.toml").mkdir()
    data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    write(manifest, {**data, role: "a-directory.toml"})
    with pytest.raises(WorkflowError, match="^malformed_record$") as caught:
        build(manifest, models)
    assert caught.value.__suppress_context__
    assert str(tmp_path) not in str(caught.value)


def fake_transformers(monkeypatch: pytest.MonkeyPatch, touched: list, **names):
    """A stand-in ``transformers`` module that records each name looked up in it,
    so no real runtime is imported."""
    module = ModuleType("transformers")
    vars(module).update(names)

    def missing(name: str):
        touched.append(name)
        raise AttributeError(name)

    module.__getattr__ = missing
    monkeypatch.setitem(sys.modules, "transformers", module)


def test_without_an_injected_tokenizer_loader_the_pinned_runtime_is_checked_first(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The application owns the default tokenizer loader, since the themes package
    confines transformers imports to the two NLI scorer constructors: the builder
    checks the pinned runtime versions first, so an unapproved runtime is
    model_mismatch before transformers is touched, a request is sent or anything
    loads."""
    manifest, models = layout(tmp_path)
    monkeypatch.setattr(nli, "version", lambda name: "unapproved")
    touched: list = []
    fake_transformers(monkeypatch, touched)
    calls: list = []
    loaded: list = []
    with pytest.raises(WorkflowError, match="^model_mismatch$"):
        build_runtime(
            manifest,
            models,
            transport=failing(calls),
            _scorer_runtime=scorer_runtime(loaded),
        )
    assert (touched, calls, loaded) == ([], [], [])


def test_without_an_injected_tokenizer_loader_transformers_loads_each_tokenizer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Once the pinned versions check out, each chat model's tokenizer loads through
    transformers' ``AutoTokenizer.from_pretrained``, from its own directory and
    from local files only."""
    manifest, models = layout(tmp_path)
    monkeypatch.setattr(nli, "version", dict(RUNTIME_VERSIONS).__getitem__)
    seen: list = []

    def from_pretrained(directory, **options):
        seen.append((Path(directory).relative_to(models).as_posix(), options))
        return ChatTokenizer([])

    fake_transformers(
        monkeypatch,
        [],
        AutoTokenizer=SimpleNamespace(from_pretrained=from_pretrained),
    )
    build_runtime(
        manifest,
        models,
        transport=failing([]),
        _scorer_runtime=scorer_runtime([]),
    )
    assert sorted(seen) == [
        (f"{name}/tokenizer", {"local_files_only": True, "trust_remote_code": False})
        for name in sorted(CHAT)
    ]


def test_a_transformers_that_will_not_import_is_model_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The pinned versions check out but the runtime itself fails to import, as a
    broken install does: the refusal is still a closed reason, with nothing sent and
    nothing loaded, and not the ImportError."""
    manifest, models = layout(tmp_path)
    monkeypatch.setattr(nli, "version", dict(RUNTIME_VERSIONS).__getitem__)
    monkeypatch.setitem(sys.modules, "transformers", None)
    calls: list = []
    loaded: list = []
    with pytest.raises(WorkflowError, match="^model_mismatch$") as caught:
        build_runtime(
            manifest,
            models,
            transport=failing(calls),
            _scorer_runtime=scorer_runtime(loaded),
        )
    assert caught.value.__suppress_context__
    assert (calls, loaded) == ([], [])


def test_a_runtime_built_for_replay_needs_no_server(tmp_path: Path) -> None:
    """A2: building sends nothing and counts nothing, and a replay through the built
    extractor dispatches nothing, over transports that fail on any call."""
    manifest, models = layout(tmp_path)
    calls: list = []
    extractor = build(manifest, models, calls=calls).workflow.extractor
    stored = ModelReply(text="{}", model="gemma-model")
    CachedAdapter(
        ScriptedAdapter(lambda _: stored, extractor.identity),
        tmp_path / "cache",
        "live",
    ).complete(request())
    replayed = CachedAdapter(extractor, tmp_path / "cache", "replay").complete(
        request()
    )
    assert replayed == stored.model_copy(update={"cached": True})
    assert calls == []


def test_importing_the_builder_loads_no_adapter_or_runtime() -> None:
    """When A8 wires the builder into the CLI, ``--help`` must still load neither
    the local adapter nor the NLI module (test_import_boundaries.py's
    test_ordinary_cli_help_loads_no_concrete_runtime): both load inside the builder."""
    code = (
        "import json, sys; import earnings_pipeline.model_runtime; "
        "print(json.dumps(sorted(sys.modules)))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    loaded = set(json.loads(result.stdout))
    assert {
        "earnings_themes.extraction.local",
        "earnings_themes.support.nli",
        "transformers",
        "torch",
    }.isdisjoint(loaded)
