"""A2's local chat token counter, over invented files and an injected tokenizer: no
optional installation, no weights, no server (the Stage 11 spec, A2; plan 18)."""

from hashlib import sha256
from types import SimpleNamespace

import pytest
from earnings_themes.extraction.adapters import Message
from earnings_themes.support.chat_tokens import ChatTokenCounter, ChatTokenizerConfig
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import FileHash
from pydantic import ValidationError

FILES = {"tokenizer.json": b"{}", "tokenizer_config.json": b"{}"}
REQUEST = SimpleNamespace(
    messages=(
        Message(role="system", content="Count these words."),
        Message(role="user", content="One two three."),
    )
)


def config(directory, files=FILES):
    for name, data in files.items():
        (directory / name).write_bytes(data)
    hashes = tuple(
        FileHash(relative_path=name, sha256=sha256(data).hexdigest())
        for name, data in sorted(files.items())
    )
    return ChatTokenizerConfig(local_directory=str(directory), files=hashes)


class Tokenizer:
    """Renders each message as its role and words, and counts words."""

    chat_template = "invented"

    def __init__(self):
        self.calls = []

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        self.calls.append((tokenize, add_generation_prompt))
        turns = [f"<{m['role']}> {m['content']}" for m in messages]
        return " ".join([*turns, "<model>"] if add_generation_prompt else turns)

    def __call__(self, text, *, add_special_tokens):
        self.calls.append(add_special_tokens)
        return {"input_ids": text.split()}


def loader(tokenizer, options):
    def load(path, **kwargs):
        options.append((path, kwargs))
        return tokenizer

    return load


def test_counts_the_rendered_template_with_the_generation_prompt(tmp_path, no_network):
    tokenizer, options = Tokenizer(), []
    counter = ChatTokenCounter(config(tmp_path), loader=loader(tokenizer, options))
    # "<system> Count these words. <user> One two three. <model>": 9 words.
    assert counter(REQUEST) == 9
    assert tokenizer.calls == [(False, True), False]
    assert options == [
        (str(tmp_path), {"local_files_only": True, "trust_remote_code": False})
    ]
    assert no_network == []


@pytest.mark.parametrize("change", ["edit", "extra"])
def test_refuses_files_that_do_not_match_their_hashes(tmp_path, change):
    checked = config(tmp_path)
    options = []
    if change == "edit":
        (tmp_path / "tokenizer.json").write_bytes(b"changed")
    else:
        (tmp_path / "README.md").write_bytes(b"an unlisted file")
    with pytest.raises(SupportError, match="^model_mismatch$"):
        ChatTokenCounter(checked, loader=loader(Tokenizer(), options))
    # The files are checked before the loader reads any of them (verify, then load).
    assert options == []


def test_refuses_a_tokenizer_without_a_chat_template(tmp_path):
    tokenizer = Tokenizer()
    tokenizer.chat_template = None
    with pytest.raises(SupportError, match="^model_mismatch$"):
        ChatTokenCounter(config(tmp_path), loader=loader(tokenizer, []))


def test_a_loader_that_raises_is_model_mismatch_without_its_message(tmp_path):
    """A runtime's own error may name a path on this machine: the refusal is the
    closed reason alone, with the error suppressed."""

    def load(path, **options):
        raise OSError("/sentinel/secret/path")

    with pytest.raises(SupportError, match="^model_mismatch$") as caught:
        ChatTokenCounter(config(tmp_path), loader=load)
    assert caught.value.__suppress_context__
    assert "/sentinel" not in str(caught.value)


def test_the_caller_must_supply_the_loader(tmp_path):
    """Themes holds no default loader: the application's builder passes one, after
    it checks the pinned runtime versions (the import-scan rule, GS17)."""
    with pytest.raises(TypeError):
        ChatTokenCounter(config(tmp_path))


def test_a_config_names_an_absolute_directory_and_both_tokenizer_files(tmp_path):
    with pytest.raises(ValidationError):
        ChatTokenizerConfig(local_directory="relative", files=config(tmp_path).files)
    one = tmp_path / "one"
    one.mkdir()
    with pytest.raises(ValidationError):
        config(one, files={"tokenizer.json": b"{}"})
