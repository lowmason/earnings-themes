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
  symlinked prefix, prints in full.
"""

from pathlib import Path

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
