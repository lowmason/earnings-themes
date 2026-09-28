"""The committed synthetic event corpus (the Stage 5 spec, §The synthetic event layer;
P-VI).

``write_fixture(repo, universe)`` writes ``tests/fixtures/events/`` from the synthetic
event layer, reviewed and frozen:

- ``raw/``, the layer's saved responses (``write_layer``);
- ``overrides.toml``, the reviewer's decisions against the first build (``review``);
- ``events-v1.json`` and ``events-v1.evidence.json``, the frozen event manifest and
  its evidence record;
- ``pilot-v1.json``, the frozen pilot, which is underfilled;
- the pilot's exhibits, which acquisition saves under ``raw/`` from the layer's
  ``exhibit_bodies`` (plan 8, P8-10), and ``acquisition.json``, that run's
  transitions, which offline replay reproduces.

``universe`` is the synthetic cohort's committed manifest. Nothing is written under
``tests/fixtures/cohort/``, and every file regenerates byte for byte.
"""

import json
import tempfile
from collections.abc import Sequence
from datetime import UTC, date, datetime
from pathlib import Path

from earnings_ingestion.cohort.records import UniverseManifest
from earnings_ingestion.events.acquire import acquire
from earnings_ingestion.events.build import EventBuild, build_events, load_overrides
from earnings_ingestion.events.freeze import freeze_events
from earnings_ingestion.events.layer import exhibit_bodies, review, write_layer
from earnings_ingestion.events.pilot import FrozenPilot, freeze_pilot, select_pilot
from earnings_ingestion.events.records import (
    AcquisitionOverridesFile,
    EventOverride,
    EventOverridesFile,
)
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.events.states import StateTransition
from earnings_ingestion.events.synthetic import serve

FIXTURE_DIR = Path("tests") / "fixtures" / "events"
COHORT_MANIFEST = (
    Path("tests") / "fixtures" / "cohort" / "manifests" / "djia-synthetic-v1.json"
)
SYNTHETIC_CORPUS = "djia-synthetic"
FROZEN_AT = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)
ACQUIRED_AT = datetime(2026, 9, 29, 13, 0, tzinfo=UTC)
ACQUISITION_RUN = "acquire-synthetic"
ACQUISITION = "acquisition.json"


def _toml(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return json.dumps(str(value))
    raise TypeError(f"no TOML form for {type(value).__name__}")


def write_overrides(path: Path, overrides: Sequence[EventOverride]) -> None:
    """``overrides.toml`` for ``overrides``, as ``load_overrides`` reads it."""
    lines = ["# Synthetic review.", "schema_version = 1"]

    def table(header: str, data: dict) -> None:
        lines.extend(["", header, *(f"{key} = {_toml(v)}" for key, v in data.items())])

    for override in overrides:
        data = override.model_dump(exclude_none=True)
        citations = data.pop("citations")
        table("[[overrides]]", data)
        for citation in citations:
            locator = citation.pop("locator", None)
            table("[[overrides.citations]]", citation)
            if locator is not None:
                table("[overrides.citations.locator]", locator)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def transitions_json(transitions: Sequence[StateTransition]) -> str:
    """A run's transitions as indented JSON with sorted keys."""
    data = [transition.model_dump(mode="json") for transition in transitions]
    return json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def load_transitions(path: Path) -> tuple[StateTransition, ...]:
    """The transitions ``transitions_json`` wrote."""
    return tuple(
        StateTransition.model_validate_json(json.dumps(item))
        for item in json.loads(path.read_text(encoding="utf-8"))
    )


def write_fixture(
    repo: Path, universe: UniverseManifest, directory: Path = FIXTURE_DIR
) -> FrozenPilot:
    """Write the committed fixture under ``repo / directory``; return the pilot."""
    root = repo / directory
    saved = SavedResponses(write_layer(root / "raw", repo).store)

    def build(overrides: EventOverridesFile) -> EventBuild:
        return build_events(universe, saved, overrides, corpus_id=SYNTHETIC_CORPUS)

    first = build(EventOverridesFile(schema_version=1))
    write_overrides(root / "overrides.toml", review(first))
    reviewed = build(load_overrides(root / "overrides.toml"))
    frozen = freeze_events(reviewed, saved, root, now=FROZEN_AT)
    pilot = select_pilot(frozen.manifest, universe)
    selected = freeze_pilot(pilot, universe, root, now=FROZEN_AT)
    with tempfile.TemporaryDirectory() as scratch:
        run = acquire(
            frozen.manifest,
            selected.manifest,
            universe,
            saved.store,
            serve(exhibit_bodies(), ACQUIRED_AT),
            overrides=AcquisitionOverridesFile(schema_version=1),
            states_dir=Path(scratch) / "states",
            canonical_dir=Path(scratch) / "canonical",
            run_id=ACQUISITION_RUN,
            now=lambda: ACQUIRED_AT,
        )
    (root / ACQUISITION).write_text(transitions_json(run.transitions), encoding="utf-8")
    return selected
