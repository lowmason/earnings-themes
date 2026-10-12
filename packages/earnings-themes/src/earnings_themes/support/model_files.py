"""Model files on local disk: the check that a directory holds exactly its listed
files, and the one hash that names several (the Stage 11 spec, A2; plan 18).

The NLI scorers, the judges' weights binding, the chat token counter and the live
runtime's builder share them. Importing this module loads no runtime. ``nli.py``
imports it, never the reverse, since no ordinary module may load ``nli.py``.
"""

from hashlib import file_digest
from pathlib import Path

from earnings_core import digest

from earnings_themes.support.problems import SupportError
from earnings_themes.support.records import FileHash


def verify_files(directory: str | Path, files: tuple[FileHash, ...]) -> None:
    """Every file under ``directory`` is listed in ``files``, none is a symlink or
    leaves it, and each matches its SHA-256. Anything else, a missing directory
    included, is ``model_mismatch``, with no file diagnostic."""
    try:
        root = Path(directory).resolve(strict=True)
        expected = {f.relative_path: f.sha256 for f in files}
        actual = {
            p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()
        }
        if actual != set(expected):
            raise SupportError("model_mismatch")
        for name, checksum in expected.items():
            path = root / name
            if path.is_symlink() or not path.resolve(strict=True).is_relative_to(root):
                raise SupportError("model_mismatch")
            with path.open("rb") as stream:
                if file_digest(stream, "sha256").hexdigest() != checksum:
                    raise SupportError("model_mismatch")
    except Exception:  # noqa: BLE001 - redact arbitrary file diagnostics
        raise SupportError("model_mismatch") from None


def files_hash(files: tuple[FileHash, ...]) -> str:
    """One file's SHA-256, or, for several, the canonical digest of their path/hash
    records sorted by relative path. No file at all is ``model_mismatch``."""
    if not files:
        raise SupportError("model_mismatch")
    if len(files) == 1:
        return files[0].sha256
    return digest(
        [
            f.model_dump(mode="json")
            for f in sorted(files, key=lambda f: f.relative_path)
        ]
    )
