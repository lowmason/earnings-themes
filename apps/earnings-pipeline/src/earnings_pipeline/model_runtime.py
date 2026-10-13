"""The live runtime for scope ``research``, assembled from committed model files (the
Stage 11 spec, A2; plan 18).

- **Files.** A manifest names one model file for each role: the extractor, the
  classifier, two judges, the scorer and the alternative scorer. A chat model's file
  is a ``ChatModelFile``. A scorer's file is a ``LocalScorerConfig`` with a
  ``directory`` relative to the models root in place of its absolute
  ``local_directory``, so no committed file holds a path on this machine (D18-9).
- **Order.** So that a typo is found before multi-gigabyte weights are hashed:
  - The manifest and the chat models' files are read, and the panel is checked
    against Stage 8's family rules first (``invalid_panel``; D18-11).
  - Then the scorers' files are read and parsed, every model directory is confined
    to the models root, and every base URL is checked, before any model file is
    hashed or loaded. A file that does not read, a directory outside the models
    root, a scorer's file with a wrong pinned field (the revision, runtime versions,
    encoding version or label mapping, through ``parse_support``) and a base URL
    that is not on this machine are each ``malformed_record``.
  - Last, every chat model's weights and tokenizer files are hashed against its
    file and its tokenizer loads, and each scorer checks its kind, its own files and
    its installed runtime (``model_mismatch``).
- **No server call.** Building sends no request and counts no token: the token
  counters are local tokenizers, and each binding checks its transport's configured
  identity. So a runtime built for replay needs no model server. Every reply still
  names its model (``model_mismatch``), and plan B's smoke records the server's own
  build (D18-12).
- **Tokenizers.** The themes package confines its heavy runtime imports to the two
  NLI scorer constructors (its import-scan rule), so this module owns the default
  tokenizer loader: ``AutoTokenizer.from_pretrained``, handed to each
  ``ChatTokenCounter`` after the pinned runtime versions check out. A caller may
  inject its own, as the tests do.
- **Choice.** Nothing here chooses a model: plan B's ADR 0006 is to write the files
  (B1).
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from earnings_themes.analysis.records import AnalysisPart
from earnings_themes.coding.local import ClassifierBinding
from earnings_themes.coding.records import CodingError
from earnings_themes.extraction.records import LOCAL_STRUCTURED, LOCAL_TIMEOUT_S
from earnings_themes.records import IdPart, NonBlank, RecordError, parse
from earnings_themes.support.chat_tokens import ChatTokenCounter, ChatTokenizerConfig
from earnings_themes.support.judges import JudgeBinding, validate_panel
from earnings_themes.support.model_files import files_hash, verify_files
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import (
    FileHash,
    JudgeIdentity,
    RuntimeIdentity,
    WeightLicense,
    parse_support,
)
from earnings_themes.support.scorers import EntailmentScorer
from earnings_themes.tomlfile import read
from pydantic import Field, PositiveFloat, PositiveInt

from earnings_pipeline.theme_config import WorkflowError, confined_path
from earnings_pipeline.theme_workflow import WorkflowRuntime

if TYPE_CHECKING:
    import httpx
    from earnings_themes.extraction.local import LocalAdapter
    from earnings_themes.support.nli import LocalScorerConfig

CHAT_ENCODING = "chat-tokens/1:"
"""A chat model's ``encoding_version`` prefix. The rest is its tokenizer files'
``files_hash``, so its identity names the tokenizer that counts its requests
(D18-10)."""


class RuntimeManifest(AnalysisPart):
    """Which model file fills each role. Names are relative to the manifest's own
    directory."""

    extractor: NonBlank
    classifier: NonBlank
    judges: tuple[NonBlank, NonBlank]
    scorer: NonBlank
    alternative_scorer: NonBlank


class ChatModelFile(AnalysisPart):
    """One local chat model behind an OpenAI-compatible server: its endpoint, its
    identity, and its weights' and tokenizer's files, under directories relative to
    the models root."""

    family: IdPart
    base_url: NonBlank
    model_id: NonBlank
    runtime: NonBlank
    runtime_version: NonBlank
    structured: bool = LOCAL_STRUCTURED
    timeout_s: PositiveFloat = LOCAL_TIMEOUT_S
    revision: NonBlank
    device: NonBlank
    precision: NonBlank
    input_limit: PositiveInt
    output_limit: PositiveInt
    weights_directory: NonBlank
    weights: tuple[FileHash, ...] = Field(min_length=1)
    tokenizer_directory: NonBlank
    tokenizer_files: tuple[FileHash, ...] = Field(min_length=1)
    weight_license: WeightLicense


@dataclass(frozen=True, repr=False)
class LiveRuntime:
    """The models ``pilot pass`` and a stability run dispatch to (A2): the workflow's
    runtime, with no assignment policy and no renderer, and the alternative scorer
    for the second support run."""

    workflow: WorkflowRuntime
    alternative_scorer: EntailmentScorer
    extractor_family: str


def build_runtime(
    manifest: Path,
    models_root: Path,
    *,
    transport: httpx.BaseTransport | None = None,
    _tokenizer_loader: Callable[..., Any] | None = None,
    _scorer_runtime: tuple[Any, Any, Any] | None = None,
) -> LiveRuntime:
    """The live runtime ``manifest`` names, with every model directory under
    ``models_root``. ``transport`` replaces httpx's own, for tests, and the two
    private arguments replace the tokenizer loader and the scorers' runtime. A
    refusal is a ``WorkflowError``: ``invalid_panel``, ``model_mismatch`` or
    ``malformed_record``."""
    try:
        return _build(
            manifest, models_root, transport, _tokenizer_loader, _scorer_runtime
        )
    except WorkflowError:
        raise
    except (SupportError, CodingError) as error:
        raise WorkflowError(str(error)) from None
    except (RecordError, ValueError, OSError):
        # An OSError (a file that is a directory, or unreadable) carries a path on this
        # machine; the refusal names only its closed reason.
        raise WorkflowError("malformed_record") from None


def _build(manifest_path, models_root, transport, tokenizer_loader, scorer_runtime):
    # Imported here, never at module level: the CLI's --help loads neither
    # (test_import_boundaries.py, test_ordinary_cli_help_loads_no_concrete_runtime).
    from earnings_themes.extraction import local
    from earnings_themes.support import nli

    # The tokenizer and scorer configs require an absolute directory. A relative root
    # is taken from the working directory; abspath, unlike resolve, follows no symlink,
    # so confined_path still refuses a symlinked root.
    models_root = Path(os.path.abspath(models_root))
    root = manifest_path.parent
    manifest = _read(root, manifest_path.name, RuntimeManifest)
    names = dict.fromkeys((manifest.extractor, manifest.classifier, *manifest.judges))
    chat = {name: _read(root, name, ChatModelFile) for name in names}
    identities = {name: _identity(model) for name, model in chat.items()}
    family = chat[manifest.extractor].family
    panel = validate_panel(family, tuple(identities[n] for n in manifest.judges))

    # Every file is read and parsed, every directory confined and every base URL
    # checked before any model file is hashed or loaded (malformed_record), so a typo
    # is found before multi-gigabyte weights are hashed.
    weights = {
        name: confined_path(models_root, model.weights_directory)
        for name, model in chat.items()
    }
    tokenizers = {
        name: ChatTokenizerConfig(
            local_directory=str(confined_path(models_root, model.tokenizer_directory)),
            files=model.tokenizer_files,
        )
        for name, model in chat.items()
    }
    scorer_config = _scorer(root, manifest.scorer, models_root, nli.LocalScorerConfig)
    alternative_config = _scorer(
        root, manifest.alternative_scorer, models_root, nli.LocalScorerConfig
    )

    def adapter(name: str) -> LocalAdapter:
        model = chat[name]
        endpoint = local.LocalModelConfig(
            base_url=model.base_url,
            model_id=model.model_id,
            weights_sha256=files_hash(model.weights),
            runtime=model.runtime,
            runtime_version=model.runtime_version,
            structured=model.structured,
            timeout_s=model.timeout_s,
        )
        return local.LocalAdapter(endpoint, transport=transport)

    # One adapter per role: the extractor and the classifier may share a file, never
    # an instance.
    extractor = adapter(manifest.extractor)
    classifier_transport = adapter(manifest.classifier)
    judge_transports = tuple(adapter(name) for name in manifest.judges)

    # Then the hashes and the tokenizers (model_mismatch).
    loader = (
        _pinned_tokenizer_loader() if tokenizer_loader is None else tokenizer_loader
    )
    counters = {}
    for name, model in chat.items():
        verify_files(weights[name], model.weights)
        counters[name] = ChatTokenCounter(tokenizers[name], loader=loader)

    # Last, the bindings, and each scorer checks its kind, hashes its own files and
    # loads its runtime (model_mismatch).
    workflow = WorkflowRuntime(
        extractor=extractor,
        classifier=ClassifierBinding(
            identities[manifest.classifier],
            classifier_transport,
            counters[manifest.classifier],
        ),
        scorer=nli.MiniCheckScorer(scorer_config, _runtime=scorer_runtime),
        judges=tuple(
            JudgeBinding(identity, judge, counters[name])
            for name, identity, judge in zip(
                manifest.judges, panel, judge_transports, strict=True
            )
        ),
        assignment_policy=None,
        renderer=None,
    )
    alternative = nli.DebertaScorer(alternative_config, _runtime=scorer_runtime)
    return LiveRuntime(workflow, alternative, family)


def _pinned_tokenizer_loader() -> Callable[..., Any]:
    """transformers' ``AutoTokenizer.from_pretrained``, once the installed runtime
    versions are the approved ones (``model_mismatch`` otherwise, before anything
    loads). The application owns this default, since the themes package confines
    transformers imports to the two NLI scorer constructors; both imports stay
    inside, so importing this module loads neither ``nli.py`` nor a model runtime."""
    from earnings_themes.support import nli

    nli._verify_runtime_versions()
    try:
        from transformers import AutoTokenizer
    except Exception:  # noqa: BLE001 - redact arbitrary runtime diagnostics
        raise SupportError("model_mismatch") from None
    return AutoTokenizer.from_pretrained


def _read(directory: Path, name: str, model):
    path = confined_path(directory, name)
    return parse(read(path), model, path.name)


def _identity(model: ChatModelFile) -> JudgeIdentity:
    """The identity a classifier or judge binding checks its transport against."""
    return JudgeIdentity(
        family=model.family,
        runtime=RuntimeIdentity(
            model_id=model.model_id,
            revision=model.revision,
            files=model.weights,
            runtime=model.runtime,
            runtime_version=model.runtime_version,
            device=model.device,
            precision=model.precision,
            encoding_version=CHAT_ENCODING + files_hash(model.tokenizer_files),
        ),
        input_limit=model.input_limit,
        output_limit=model.output_limit,
        hosting="local",
        weight_license=model.weight_license,
    )


def _scorer(
    directory: Path, name: str, models_root: Path, config: type[LocalScorerConfig]
) -> LocalScorerConfig:
    """A scorer's file: a ``LocalScorerConfig`` whose ``directory``, relative to the
    models root, stands in for its absolute ``local_directory`` (D18-9). ``config``
    is the class, which the builder passes in so that this module never imports
    ``nli.py`` at import time."""
    path = confined_path(directory, name)
    data = read(path)
    reference = data.pop("directory", None)
    if "local_directory" in data or type(reference) is not str:
        raise WorkflowError("malformed_record")
    resolved = confined_path(models_root, reference)
    return parse_support({**data, "local_directory": str(resolved)}, config)
