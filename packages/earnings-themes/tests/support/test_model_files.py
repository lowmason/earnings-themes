"""The model-file checks the scorers, the judges' weights binding, the chat token
counter and the live runtime share (the Stage 11 spec, A2; plan 18)."""

from hashlib import sha256

import pytest
from earnings_core import digest
from earnings_themes.support.model_files import files_hash, verify_files
from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import FileHash

FILES = {"model.gguf": b"invented weights", "nested/tokenizer.json": b"{}"}


def written(directory):
    for name, data in FILES.items():
        (directory / name).parent.mkdir(parents=True, exist_ok=True)
        (directory / name).write_bytes(data)
    return tuple(
        FileHash(relative_path=name, sha256=sha256(data).hexdigest())
        for name, data in sorted(FILES.items())
    )


def test_a_directory_that_holds_exactly_its_files_verifies(tmp_path):
    directory = tmp_path / "model"
    verify_files(str(directory), written(directory))
    verify_files(directory, written(directory))


@pytest.mark.parametrize("change", ["edit", "extra", "missing", "symlink", "absent"])
def test_anything_else_is_a_model_mismatch(tmp_path, change):
    directory = tmp_path / "model"
    files = written(directory)
    if change == "edit":
        (directory / "model.gguf").write_bytes(b"changed")
    elif change == "extra":
        (directory / "README.md").write_bytes(b"an unlisted file")
    elif change == "missing":
        (directory / "model.gguf").unlink()
    elif change == "symlink":
        outside = tmp_path / "outside.gguf"
        outside.write_bytes(FILES["model.gguf"])
        (directory / "model.gguf").unlink()
        (directory / "model.gguf").symlink_to(outside)
    else:
        directory = tmp_path / "absent"
    with pytest.raises(SupportError, match="^model_mismatch$") as caught:
        verify_files(str(directory), files)
    assert caught.value.__suppress_context__


def test_files_hash_is_one_file_s_hash_or_the_sorted_digest():
    a = FileHash(relative_path="a.gguf", sha256="a" * 64)
    b = FileHash(relative_path="b.gguf", sha256="b" * 64)
    assert files_hash((a,)) == "a" * 64
    assert files_hash((b, a)) == digest(
        [a.model_dump(mode="json"), b.model_dump(mode="json")]
    )
    with pytest.raises(SupportError, match="^model_mismatch$"):
        files_hash(())
