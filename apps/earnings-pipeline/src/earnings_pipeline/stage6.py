"""What Stage 6's commands share: the pin, the paths, and loading (the Stage 6
spec, §The pin and §Drafting and tools; GS2, GS13, GS14; plan 9).

- **The pin.** Every command loads pilot v1 and universe v1 by path, never the
  current version, and refuses a pilot whose content hash is not the pin's.
  ``load_pilot`` rechecks the chain, the universe's operative hash included, and
  selects the pilot again (P8-3).
- **Where things are.** Paths are relative to ``--repo``, and a file named for an
  event takes ``file_stem(event_id)``, its colon as an underscore. Committed:
  ``evaluation/<corpus>/pilot-v<N>/`` holds the split, the coverage report, the
  gold, and the briefs; ``codebooks/djia-pilot/`` codebook v0; and
  ``tests/fixtures/gold/`` the curated hard negatives. Local only:
  ``data/runs/events/`` holds the states and canonical documents, and
  ``data/runs/gold/`` the drafts, anchored files, views, and texts.
- **Before a record is written.** A command checks it against every text the
  committed wording guard reads, each parsed pilot document and each Stage 1
  fixture, so no record it writes fails the guard later (GS3).
- **What they print.** IDs, counts, reasons, paths, and hashes, never a document's
  text. A refusal names its item and reason; a file that does not load is named,
  never quoted; and an unforeseen error is named by its type alone (``guarded``).
  Text is written only to views and texts under ``data/runs/gold/``, which the user
  opens (GS13).
"""

import functools
import os
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, NoReturn

import tomllib
import typer
from earnings_ingestion.canonical.serialize import from_fixture_json
from earnings_ingestion.cohort.config import UNIVERSE_DIR
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.events.build import CORPUS_DIR
from earnings_ingestion.events.coverage import PilotPin, parsed_documents, pilot_pin
from earnings_ingestion.events.freeze import load_event_manifest, manifest_path
from earnings_ingestion.events.pilot import load_pilot
from earnings_ingestion.events.records import EventManifest, PilotManifest
from earnings_ingestion.events.state_table import read_runs
from earnings_ingestion.events.states import StateTransition
from earnings_ingestion.fetch.store import write_new
from earnings_themes.anchoring import Bundle
from earnings_themes.codebook import CODEBOOK_ID, CODEBOOK_VERSION
from earnings_themes.problems import Problem, Refusal
from earnings_themes.records import Pin, RecordError
from earnings_themes.wording import labelled_strings, shared
from pydantic import BaseModel

from earnings_pipeline.paths import shown

PILOT_V1_HASH = "3839c800151cc646f11064efdce583f988e511265f8893c90e9a2f2549145926"
"""GS2: the pin, pilot v1's content hash."""
UNIVERSE_V1 = UNIVERSE_DIR / "manifests" / "djia-2024q3-2026q2-v1.json"
PILOT_V1 = CORPUS_DIR / "pilot-v1.json"
EVENT_RUNS = Path("data") / "runs" / "events"
GOLD_RUNS = Path("data") / "runs" / "gold"
CODEBOOK_FILE = Path("codebooks") / CODEBOOK_ID / f"codebook-v{CODEBOOK_VERSION}.toml"
FIXTURE_MANIFEST = Path("tests") / "fixtures" / "releases" / "manifest.toml"
CANONICAL_FIXTURES = Path("tests") / "fixtures" / "canonical"
HARD_NEGATIVES = Path("tests") / "fixtures" / "gold" / "hard-negatives.toml"


@dataclass(frozen=True)
class Layout:
    repo: Path
    universe: Path
    pilot: Path
    pilot_hash: str

    def shown(self, path: Path) -> str:
        return shown(path, self.repo)

    @property
    def drafts(self) -> Path:
        return self.repo / GOLD_RUNS / "drafts"

    @property
    def gold_runs(self) -> Path:
        return self.repo / GOLD_RUNS


@dataclass(frozen=True)
class Pinned:
    """Pilot v1 with its chain, and where its evaluation records live."""

    pilot: PilotManifest
    events: EventManifest
    pin: Pin
    coverage_pin: PilotPin
    evaluation: Path

    @property
    def split_path(self) -> Path:
        return self.evaluation / "split-v1.json"

    @property
    def coverage_path(self) -> Path:
        return self.evaluation / "coverage-v1.json"

    @property
    def gold_dir(self) -> Path:
        return self.evaluation / "gold"


def file_stem(event_id: str) -> str:
    """An event's Stage 6 file name: its ID with the colon as an underscore, since
    Git on Windows cannot check out a path with a colon (P9-3). The ID inside each
    file is unchanged."""
    return event_id.replace(":", "_")


def fail(message: str) -> NoReturn:
    typer.echo(message, err=True)
    raise typer.Exit(1)


def guarded[**P](command: Callable[P, None]) -> Callable[P, None]:
    """``command``, with an unforeseen error named by its type alone: a message,
    such as a validation error's, may quote a document (GS13)."""

    @functools.wraps(command)
    def run(*args: P.args, **kwargs: P.kwargs) -> None:
        try:
            command(*args, **kwargs)
        except typer.Exit:
            raise
        except Exception as error:  # noqa: BLE001 - withheld by design (GS13)
            fail(
                f"Refused: an unforeseen {type(error).__name__}; its message is"
                " withheld, since it may quote a document (GS13)"
            )

    return run


def refuse(refusals: list[Refusal], verb: str = "written") -> NoReturn:
    """Print each refusal by item and reason, and stop with nothing written."""
    for refusal in refusals:
        typer.echo(f"refused: {refusal}", err=True)
    fail(f"Refused: {len(refusals)} problem(s); nothing {verb}")


def record_error(error: RecordError) -> NoReturn:
    for problem in error.problems:
        typer.echo(f"problem: {error.name}: {problem}", err=True)
    fail(f"Refused: {error.name} does not read as its record")


def options(
    context: typer.Context,
    repo: Annotated[Path, typer.Option(help="The repository root.")] = Path(),
    universe: Annotated[
        Path, typer.Option(help="The pinned universe, by path.")
    ] = UNIVERSE_V1,
    pilot: Annotated[Path, typer.Option(help="The pinned pilot, by path.")] = PILOT_V1,
    pilot_hash: Annotated[
        str, typer.Option(help="The pin: the pilot's content hash.")
    ] = PILOT_V1_HASH,
) -> None:
    """Paths are relative to --repo; the defaults are GS2's pin, pilot v1."""
    context.obj = Layout(repo.resolve(), universe, pilot, pilot_hash)


def load_pinned(layout: Layout) -> Pinned:
    """The pinned pilot, with its chain checked, or a refusal."""
    path = layout.repo / layout.pilot
    try:
        universe = load_manifest(layout.repo / layout.universe)
        pilot = load_pilot(path, universe)
        version = pilot.definition.event_manifest_version
        events = load_event_manifest(manifest_path(path.parent, version))
        coverage_pin = pilot_pin(pilot, events, universe)
    except (OSError, ValueError) as error:
        fail(f"Refused: {error}")
    if pilot.definition.content_hash != layout.pilot_hash:
        fail(
            f"Refused: {layout.shown(path)} holds pilot"
            f" {pilot.definition.content_hash}, not the pin's {layout.pilot_hash}"
        )
    definition = pilot.definition
    evaluation = (
        layout.repo
        / "evaluation"
        / events.definition.corpus_id
        / f"pilot-v{definition.pilot_version}"
    )
    pin = Pin.model_validate_json(coverage_pin.model_dump_json())
    return Pinned(pilot, events, pin, coverage_pin, evaluation)


def transitions(layout: Layout) -> list[StateTransition]:
    try:
        return read_runs(layout.repo / EVENT_RUNS / "states")
    except (OSError, ValueError) as error:
        fail(f"Refused: {error}")


def documents(layout: Layout, pinned: Pinned) -> dict[str, str]:
    """Each pilot event with a parsed document, and its ``doc_id``."""
    return parsed_documents(transitions(layout), pinned.pin.pilot_hash)


def _bundle(path: Path, name: str, layout: Layout, doc_id: str | None) -> Bundle:
    try:
        result = from_fixture_json(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(
            f"Refused: {name}: {layout.shown(path)} is not here; it regenerates"
            " offline from the saved exhibit through canonicalize"
        )
    except (ValueError, UnicodeDecodeError):
        fail(f"Refused: {name}: {path.name} does not load as a canonical document")
    if doc_id is not None and result.document.doc_id != doc_id:
        fail(f"Refused: {name}: {path.name} holds another document")
    return Bundle(name, result.document, result.elements, result.masked.masks)


def load_bundle(layout: Layout, doc_ids: dict[str, str], event_id: str) -> Bundle:
    """One pilot event's canonical document, by the ``doc_id`` its state names."""
    doc_id = doc_ids.get(event_id)
    if doc_id is None:
        fail(f"Refused: {event_id} is not a pilot event with a parsed document")
    path = layout.repo / EVENT_RUNS / "canonical" / f"{doc_id}.json"
    return _bundle(path, event_id, layout, doc_id)


def load_fixture(layout: Layout, fixture_id: str) -> Bundle:
    """One of Stage 1's committed canonical fixtures."""
    path = layout.repo / CANONICAL_FIXTURES / f"{fixture_id}.json"
    return _bundle(path, fixture_id, layout, None)


def wording_texts(layout: Layout, pinned: Pinned) -> dict[str, str]:
    """Every text the committed wording guard reads (the Stage 6 spec, §Wording
    guard): each parsed pilot document's, by event ID, and each Stage 1 fixture's,
    by fixture ID."""
    doc_ids = documents(layout, pinned)
    found = {
        event_id: load_bundle(layout, doc_ids, event_id).document.canonical_text
        for event_id in sorted(doc_ids)
    }
    for path in sorted((layout.repo / CANONICAL_FIXTURES).glob("*.json")):
        found[path.stem] = load_fixture(layout, path.stem).document.canonical_text
    return found


def wording_refusals(record: BaseModel, texts: Mapping[str, str]) -> list[Refusal]:
    """Each string of ``record`` that shares F20's window with one of ``texts``,
    named by its field and the text's ID, never quoted (GS3, GS13)."""
    found = shared(labelled_strings(record.model_dump(mode="json")), texts.items())
    return [
        Refusal(f"{label} ({name})", Problem.SOURCE_WORDING)
        for label, name in sorted(found)
    ]


def fixture_event_ids(layout: Layout, events: EventManifest) -> frozenset[str]:
    """The events whose release is a Stage 1 fixture, matched by accession: each is
    ``train_or_exclude`` (GS10). The fixtures' manifest names no event."""
    path = layout.repo / FIXTURE_MANIFEST
    try:
        fixtures = tomllib.loads(path.read_text(encoding="utf-8"))["fixtures"]
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        fail(f"Refused: {layout.shown(path)} does not list Stage 1's fixtures")
    accessions = {
        fixture["accession"]
        for fixture in fixtures
        if fixture.get("pilot_split") == "train_or_exclude"
    }
    return frozenset(
        row.event_id for row in events.rows if row.release_accession in accessions
    )


def write_once(path: Path, data: bytes, layout: Layout) -> bool:
    """A committed record, written once: the same bytes again change nothing."""
    existed = path.exists()
    try:
        write_new(path, data)
    except FileExistsError:
        fail(
            f"Refused: {layout.shown(path)} holds other content; a changed record is"
            " a new version, never an edit"
        )
    return not existed


def replace(path: Path, text: str) -> None:
    """A local file under ``data/runs/gold/``, replaced atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    with os.fdopen(handle, "w", encoding="utf-8") as out:
        out.write(text)
    Path(temporary).replace(path)
