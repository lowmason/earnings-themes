"""Paths the commands check and print (PR #6's review, F19 and F38).

- **Where fetched bytes go.** A command that saves fetched bytes refuses a store root
  that does not resolve under ``<repo>/data/raw``, which Git ignores, before any
  client opens: ``tests/fixtures/`` is committed, so fetched SEC or index pages saved
  there would reach this public repository. Paths are resolved only for the check;
  the store keeps the root as given, so a symlinked ``data/`` still works.
- **Where run outputs go.** ``events acquire`` refuses a runs directory that does not
  resolve under ``<repo>/data/runs``: the canonical documents it writes hold
  filings' text, which is local-only and never committed (plan 8, P8-13).
- **What a command prints.** A path under the repository prints relative to it, and
  any other path, such as a corpus directory outside it or one spelled through a
  symlinked prefix, prints in full. An error prints as ``error_lines`` splits it, so
  each line can carry the ``problem:`` prefix. A save that moves damaged bytes aside
  prints ``quarantined_lines``, one line for each file it moved, after the request
  count and before it on a stop (plan 26).
"""

from pathlib import Path

from earnings_ingestion.fetch.store import ArtifactStore
from pydantic import ValidationError

RAW = Path("data") / "raw"
RUNS = Path("data") / "runs"


def raw_store_refusal(repo: Path, store: Path) -> str | None:
    """Why fetched bytes may not be saved under ``repo / store``, or ``None``."""
    if (repo / store).resolve().is_relative_to((repo / RAW).resolve()):
        return None
    return (
        f"Refused: {store} does not resolve under {RAW}, where fetched bytes are"
        " kept out of Git"
    )


def runs_refusal(repo: Path, runs: Path) -> str | None:
    """Why run outputs may not be written under ``repo / runs``, or ``None``."""
    if (repo / runs).resolve().is_relative_to((repo / RUNS).resolve()):
        return None
    return (
        f"Refused: {runs} does not resolve under {RUNS}, where canonical documents,"
        " which hold filings' text, are kept out of Git"
    )


def shown(path: Path, repo: Path) -> str:
    """``path`` relative to ``repo`` when it lies under it, and in full otherwise."""
    return str(path.relative_to(repo)) if path.is_relative_to(repo) else str(path)


def quarantined_lines(store: ArtifactStore, repo: Path) -> list[str]:
    """One ``quarantined:`` line for each damaged file a save of ``store`` moved into
    ``quarantine/``, once, in the order moved. Only this process knows of a move, so
    every exit prints them."""
    return [
        f"quarantined: {shown(path, repo)}" for path in dict.fromkeys(store.quarantined)
    ]


def error_lines(error: BaseException) -> list[str]:
    """The lines to print for ``error``, one for each problem it reports.

    A pydantic ``ValidationError`` gives one ``location: message`` line for each of
    its entries, or the message alone when an entry has no location. Its text would
    add a header, the rejected input, and a documentation URL. Any other error gives
    the non-empty lines of its text, and its type name when it has none."""
    if isinstance(error, ValidationError):
        lines = []
        for entry in error.errors():
            location = ".".join(str(part) for part in entry["loc"])
            lines.append(f"{location}: {entry['msg']}" if location else entry["msg"])
        return lines
    lines = [line for line in str(error).splitlines() if line.strip()]
    return lines or [type(error).__name__]
