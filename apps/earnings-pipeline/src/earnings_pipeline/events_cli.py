"""``earnings-pipeline events``: discover, build, and freeze Stage 5's event manifest,
and select and freeze its pilot (plan 7, P7-18).

    earnings-pipeline events discover --max-requests N    # the shared SEC client
    earnings-pipeline events discover --filing CIK ACCESSION    # at most 2 requests
    earnings-pipeline events build
    earnings-pipeline events freeze
    earnings-pipeline events select

Only ``discover`` uses the network, through the shared SEC client. It states its
request budget before it sends anything, and each phase's count before that phase,
and a rerun fetches only what the store lacks. Its budget is ``--max-requests``, the
count the user approved. ``--filing`` caps itself at 2, or at ``--max-requests`` if
that is smaller, so no approval is ever exceeded. It names one filing, since each is
approved on its own, and a second ``--filing`` is refused. ``build``, ``freeze``, and
``select`` read committed files and saved responses alone. ``build`` exits 1 while
anything holds the freeze.

The universe is the latest frozen manifest in ``--universe-dir``, which holds one
universe's versions; ``select`` reads the version its event manifest read.
``--corpus-dir`` holds one corpus's versions: ``freeze`` refuses a build of another
corpus, and ``select`` refuses unless the latest event manifest is ``--corpus-id``'s.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, NoReturn

import typer
from earnings_ingestion.cohort.config import UNIVERSE_DIR
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.cohort.records import UniverseManifest
from earnings_ingestion.events.build import (
    CORPUS_DIR,
    CORPUS_ID,
    EVENTS_STORE,
    EventBuild,
    EventBuildError,
    build_events,
    load_overrides,
)
from earnings_ingestion.events.discover import discover, discover_filing
from earnings_ingestion.events.freeze import (
    EventFreezeRefused,
    freeze_events,
    frozen_event_manifests,
)
from earnings_ingestion.events.pilot import freeze_pilot, select_pilot
from earnings_ingestion.events.records import EventStatus
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.fetch.client import AccessStop, UnexpectedResponse
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.client import open_sec_client
from typer.core import TyperCommand

events = typer.Typer(
    no_args_is_help=True, help="Stage 5's events: discovery, eligibility, the pilot."
)
FILING_REQUESTS = 2
"""What ``discover --filing`` fetches at most: an index page and an 8-K document."""


@dataclass(frozen=True)
class Layout:
    repo: Path
    universe_dir: Path
    corpus_dir: Path
    store_root: Path
    corpus_id: str

    def store(self) -> ArtifactStore:
        return ArtifactStore(self.repo / self.store_root, self.repo)

    def corpus(self) -> Path:
        return self.repo / self.corpus_dir

    def universes(self) -> list[UniverseManifest]:
        """Every frozen version in ``universe_dir``, oldest first."""
        found = [
            load_manifest(path)
            for path in sorted((self.repo / self.universe_dir).glob("*-v*.json"))
        ]
        if len({m.definition.universe_id for m in found}) > 1:
            _fail(f"Refused: {self.universe_dir} holds more than one universe")
        if not found:
            _fail(f"Refused: {self.universe_dir} holds no frozen universe")
        return sorted(found, key=lambda m: m.definition.universe_version)


@events.callback()
def main(
    context: typer.Context,
    repo: Annotated[Path, typer.Option(help="The repository root.")] = Path(),
    universe_dir: Annotated[
        Path, typer.Option(help="The frozen universe's manifests.")
    ] = UNIVERSE_DIR / "manifests",
    corpus_dir: Annotated[
        Path, typer.Option(help="Overrides and frozen manifests.")
    ] = CORPUS_DIR,
    store: Annotated[Path, typer.Option(help="The saved responses.")] = EVENTS_STORE,
    corpus_id: Annotated[str, typer.Option(help="The corpus.")] = CORPUS_ID,
) -> None:
    """Paths are relative to --repo; the defaults are the real corpus's."""
    context.obj = Layout(repo.resolve(), universe_dir, corpus_dir, store, corpus_id)


def _fail(message: str) -> NoReturn:
    typer.echo(message, err=True)
    raise typer.Exit(1)


class _OneFiling(TyperCommand):
    """``discover``, which refuses a second ``--filing`` before any client opens. The
    option takes one CIK and accession, and Click keeps only the last of several, so
    the others would be dropped unfetched and unreported."""

    def parse_args(self, ctx, args: list[str]) -> list[str]:
        options = args[: args.index("--")] if "--" in args else args
        named = [arg for arg in options if arg.split("=", 1)[0] == "--filing"]
        if len(named) > 1:
            _fail("Refused: pass one --filing; each filing is approved on its own")
        return super().parse_args(ctx, args)


@events.command("discover", cls=_OneFiling)
def discover_command(
    context: typer.Context,
    max_requests: Annotated[
        int | None,
        typer.Option(
            help="The request count approved at the gate; the client's cap. With"
            " --filing, the cap is 2, or this count if it is smaller."
        ),
    ] = None,
    filing: Annotated[
        tuple[str, str] | None,
        typer.Option(help="CIK ACCESSION: one filing's index page and 8-K document."),
    ] = None,
) -> None:
    """Save what the build reads from SEC, through the shared SEC client."""
    layout: Layout = context.obj
    universe = layout.universes()[-1]
    if filing is None:
        budget = max_requests
    elif max_requests is None:
        budget = FILING_REQUESTS
    else:
        budget = min(max_requests, FILING_REQUESTS)
    if budget is None:
        _fail("Refused: pass --max-requests, the request count the user approved")
    typer.echo(f"at most {budget} requests to SEC, through the shared client")
    sent = 0
    try:
        with open_sec_client(max_requests=budget) as sec:
            try:
                if filing is not None:
                    result = discover_filing(
                        universe, *filing, sec.fetch, layout.store(), say=typer.echo
                    )
                else:
                    result = discover(
                        universe, sec.fetch, layout.store(), say=typer.echo
                    )
            finally:
                sent = sec.throttle.count
    except (AccessStop, UnexpectedResponse, ValueError, RuntimeError) as error:
        typer.echo(f"requests sent: {sent}; a rerun fetches only what is missing")
        _fail(f"Stopped: {error}")
    typer.echo(f"fetched {len(result.fetched)}; requests sent: {sent}")


def _build(layout: Layout) -> tuple[EventBuild, SavedResponses]:
    saved = SavedResponses(layout.store())
    try:
        built = build_events(
            layout.universes()[-1],
            saved,
            load_overrides(layout.corpus() / "overrides.toml"),
            corpus_id=layout.corpus_id,
        )
    except EventBuildError as error:
        for problem in error.problems:
            typer.echo(f"problem: {problem}", err=True)
        raise typer.Exit(1) from error
    return built, saved


@events.command("build")
def build_command(context: typer.Context) -> None:
    """Build offline; print every row, candidate, and finding, and what holds the
    freeze, with each blocking finding's digest."""
    built, _ = _build(context.obj)
    for line in built.report():
        typer.echo(line)
    for finding in built.blocking:
        typer.echo(f"acknowledge {finding.finding_id} with digest {finding.digest}")
    eligible = [r for r in built.rows if r.eligibility_status is EventStatus.ELIGIBLE]
    typer.echo(
        f"{len(built.rows)} events, {len(eligible)} eligible,"
        f" content {built.content_hash}"
    )
    if built.holds_freeze:
        raise typer.Exit(1)


@events.command("freeze")
def freeze_command(context: typer.Context) -> None:
    """Freeze the event manifest and its evidence, or name the version holding it."""
    layout: Layout = context.obj
    built, saved = _build(layout)
    try:
        frozen = freeze_events(built, saved, layout.corpus(), now=datetime.now(UTC))
    except EventFreezeRefused as error:
        for reason in error.reasons:
            typer.echo(f"HOLDS  {reason}", err=True)
        raise typer.Exit(1) from error
    except ValueError as error:
        _fail(f"Refused: {error}")
    definition = frozen.manifest.definition
    verb = "froze" if frozen.created else "unchanged:"
    typer.echo(f"{verb} {definition.corpus_id} v{definition.event_manifest_version}")
    typer.echo(f"{frozen.path.relative_to(layout.repo)}  {definition.content_hash}")
    typer.echo(f"{frozen.evidence_path.relative_to(layout.repo)}")


@events.command("select")
def select_command(context: typer.Context) -> None:
    """Run djia-pilot/1 on the latest frozen event manifest, and freeze the pilot."""
    layout: Layout = context.obj
    try:
        manifests = frozen_event_manifests(layout.corpus())
    except ValueError as error:
        _fail(f"Refused: {error}")
    if not manifests:
        _fail(f"Refused: no frozen event manifest in {layout.corpus_dir}")
    frozen_events = manifests[-1]
    read = frozen_events.definition
    if read.corpus_id != layout.corpus_id:
        _fail(
            f"Refused: {layout.corpus_dir} holds corpus {read.corpus_id},"
            f" not {layout.corpus_id}"
        )
    matching = [
        m
        for m in layout.universes()
        if (m.definition.universe_id, m.definition.universe_version)
        == (read.universe_id, read.universe_version)
    ]
    if not matching:
        _fail(
            f"Refused: {layout.universe_dir} holds no {read.universe_id}"
            f" v{read.universe_version}, which the event manifest read"
        )
    universe = matching[0]
    try:
        pilot = select_pilot(frozen_events, universe)
        frozen = freeze_pilot(pilot, universe, layout.corpus(), now=datetime.now(UTC))
    except ValueError as error:
        _fail(f"Refused: {error}")
    manifest = frozen.manifest
    for row in manifest.rows:
        typer.echo(f"{row.selection_order:>3}  {row.event_id}  {row.selection_reason}")
    for transition in manifest.unmatched_transitions:
        typer.echo(
            f"reported: {transition.issuer_id}'s {transition.kind} on"
            f" {transition.effective_date} has no eligible event on its member side"
        )
    definition = manifest.definition
    verb = "froze" if frozen.created else "unchanged:"
    filled = ", underfilled" if definition.underfilled else ""
    typer.echo(
        f"{verb} {definition.pilot_id} v{definition.pilot_version}:"
        f" {len(manifest.rows)} of target {definition.target}{filled}"
    )
    typer.echo(f"{frozen.path.relative_to(layout.repo)}  {definition.content_hash}")
