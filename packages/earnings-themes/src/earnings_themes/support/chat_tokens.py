"""A chat model's local token counter: its own tokenizer and chat template, from
files the caller hashes (the Stage 11 spec, A2; plan 18). The caller supplies the
tokenizer loader: the application's builder passes ``AutoTokenizer.from_pretrained``
after it checks the pinned runtime versions. So importing this module, or building a
counter, imports no runtime here, and the import-scan rule holds (heavy runtimes only
in the two scorer constructors of ``nli.py``). Counting makes no server call, so a
runtime built for replay needs no model server.

The count is the chat template rendered over the request's messages with the
generation prompt, then encoded without adding special tokens again, since the
template writes them. A structured reply adds nothing to it: llama.cpp constrains a
``response_format`` schema by grammar, not by prompt text. Plan B's smoke compares
the count with the server's reported prompt tokens, since a GGUF's embedded template
can differ from its repository's.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any, Self

from pydantic import Field, model_validator

from earnings_themes.extraction.adapters import ChatRequest
from earnings_themes.support.model_files import verify_files
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import FileHash, SafePart
from earnings_themes.support.resolve import _validated

REQUIRED_FILES = frozenset({"tokenizer.json", "tokenizer_config.json"})


class ChatTokenizerConfig(SafePart):
    """A chat model's tokenizer directory and every file in it, by hash."""

    local_directory: str = Field(repr=False)
    files: tuple[FileHash, ...]

    @model_validator(mode="after")
    def _pinned(self) -> Self:
        names = [f.relative_path for f in self.files]
        if (
            not Path(self.local_directory).is_absolute()
            or len(names) != len(set(names))
            or not REQUIRED_FILES <= set(names)
        ):
            raise ValueError("model_mismatch")
        return self


class ChatTokenCounter:
    """``counter(request) -> int``, a ``token_counter`` for ``ClassifierBinding`` and
    ``JudgeBinding``. Construction checks every file's hash and refuses a tokenizer
    with no chat template (``model_mismatch``). ``loader`` is required, with
    ``AutoTokenizer.from_pretrained``'s signature; the caller, not this module,
    imports the runtime."""

    def __init__(
        self, config: ChatTokenizerConfig, *, loader: Callable[..., Any]
    ) -> None:
        try:
            checked = _validated(config, ChatTokenizerConfig)
            verify_files(checked.local_directory, checked.files)
            tokenizer = loader(
                checked.local_directory, local_files_only=True, trust_remote_code=False
            )
            if not getattr(tokenizer, "chat_template", None):
                raise SupportError("model_mismatch")
        except Exception:  # noqa: BLE001 - redact arbitrary runtime/file diagnostics
            raise SupportError("model_mismatch") from None
        self._tokenizer = tokenizer

    def __call__(self, request: ChatRequest) -> int:
        text = self._tokenizer.apply_chat_template(
            [message.model_dump() for message in request.messages],
            tokenize=False,
            add_generation_prompt=True,
        )
        return len(self._tokenizer(text, add_special_tokens=False)["input_ids"])

    def __repr__(self) -> str:
        return "ChatTokenCounter()"

    __str__ = __repr__
