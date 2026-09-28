"""The committed synthetic event corpus (the Stage 5 spec, §The synthetic event layer;
P-VI).

``write_fixture(repo, universe)`` writes ``tests/fixtures/events/`` from the synthetic
event layer, reviewed and frozen:

- ``raw/``, the layer's saved responses (``write_layer``);
- ``overrides.toml``, the reviewer's decisions against the first build (``review``);
- ``events-v1.json`` and ``events-v1.evidence.json``, the frozen event manifest and
  its evidence record;
- ``pilot-v1.json``, the frozen pilot, which is underfilled.

``universe`` is the synthetic cohort's committed manifest. Nothing is written under
``tests/fixtures/cohort/``, and every file regenerates byte for byte.
"""

import json
from collections.abc import Sequence
from datetime import UTC, date, datetime
from pathlib import Path

from earnings_ingestion.cohort.records import UniverseManifest
from earnings_ingestion.events.build import EventBuild, build_events, load_overrides
from earnings_ingestion.events.freeze import freeze_events
from earnings_ingestion.events.layer import review, write_layer
from earnings_ingestion.events.pilot import FrozenPilot, freeze_pilot, select_pilot
from earnings_ingestion.events.records import EventOverride, EventOverridesFile
from earnings_ingestion.events.saved import SavedResponses

FIXTURE_DIR = Path("tests") / "fixtures" / "events"
COHORT_MANIFEST = (
    Path("tests") / "fixtures" / "cohort" / "manifests" / "djia-synthetic-v1.json"
)
SYNTHETIC_CORPUS = "djia-synthetic"
FROZEN_AT = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)


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
    return freeze_pilot(pilot, universe, root, now=FROZEN_AT)
