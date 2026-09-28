"""``earnings-pipeline events``: discover, build, and freeze Stage 5's event manifest,
select and freeze its pilot (plan 7, P7-18), and acquire the pilot's releases (plan
8, P8-13).

    earnings-pipeline events discover --max-requests N    # the shared SEC client
    earnings-pipeline events discover --filing CIK ACCESSION    # at most 2 requests
    earnings-pipeline events build
    earnings-pipeline events freeze
    earnings-pipeline events select
    earnings-pipeline events acquire --max-requests N    # the shared SEC client

Only ``discover`` uses the network, through the shared SEC client. It states its
request budget before it sends anything, and each phase's count before that phase,
and a rerun fetches only what the store lacks. Its budget is ``--max-requests``, the
count the user approved. ``--filing`` caps itself at 2, or at ``--max-requests`` if
that is smaller, so no approval is ever exceeded. It names one filing, since each is
approved on its own, and a second ``--filing`` is refused. It prints the requests it
sent on every exit, a stop, a Ctrl-C, or an error no stop names included (PR #6's
review, F31; plan 8's final review). ``discover`` exits 1 and names each saved
submissions file, older page, index page, or primary document the build cannot read,
which no rerun fetches again, since it is saved.
``build``, ``freeze``, and ``select`` read committed files and saved responses alone.
``build`` exits 1 while anything holds the freeze.

``acquire`` reads the event manifest the build reproduces and the pilot frozen over
it, which ``load_pilot`` checks and reselects, and refuses otherwise. It states what
it would send before it opens the client: at most N requests, one per exhibit not
saved, and how many are first choices. With nothing to fetch the client stays
closed; otherwise ``--max-requests``, the count the user approved, is required and is
the client's cap. A retry after a 429 or a server error counts against it: a run the
cap stops keeps what it recorded, and a rerun at a newly approved count takes up the
rest. The client refuses a redirect before following it, so a redirect costs one
request. It
holds a lock on ``--runs-dir`` while it counts and acquires, so two runs never record
at once. It prints each pilot document's state, and its request count on every exit.
It writes its run under ``--runs-dir``, and exits 1 on a problem (plan 8's final
review).

``discover`` and ``acquire`` refuse a ``--store`` that does not resolve under
``data/raw``, and ``acquire`` a ``--runs-dir`` outside ``data/runs``, before any
client opens; every command prints a path outside the repository in full
(``earnings_pipeline.paths``).

The universe is the latest frozen manifest in ``--universe-dir``, which holds one
universe's versions; ``select`` reads the version its event manifest read.
``--corpus-dir`` holds one corpus's versions: ``freeze`` refuses a build of another
corpus, and ``select`` one whose ``--corpus-id`` is not the directory's. The build
decides which event manifest is current: ``select`` builds offline and reads the
version that holds the build's content, which a revert makes an earlier one, and
prints the version and hash it read (PR #6's review, F4; plan 8, P8-4).
"""

from collections import Counter
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, NoReturn

import typer
from earnings_ingestion.cohort.config import UNIVERSE_DIR
from earnings_ingestion.cohort.freeze import load_manifest
from earnings_ingestion.cohort.records import UniverseManifest
from earnings_ingestion.events.acquire import (
    OVERRIDES_FILE,
    acquire,
    load_acquisition_overrides,
    planned_requests,
)
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
    FrozenEvents,
    current_events,
    freeze_events,
)
from earnings_ingestion.events.pilot import current_pilot, freeze_pilot, select_pilot
from earnings_ingestion.events.records import (
    ACKNOWLEDGEABLE,
    EventFindingKind,
    EventStatus,
)
from earnings_ingestion.events.saved import SavedResponses
from earnings_ingestion.fetch.client import (
    AccessStop,
    ProcessLock,
    UnexpectedResponse,
)
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.client import open_sec_client
from typer.core import TyperCommand

from earnings_pipeline.paths import raw_store_refusal, runs_refusal, shown

events = typer.Typer(
    no_args_is_help=True, help="Stage 5's events: discovery, eligibility, the pilot."
)
FILING_REQUESTS = 2
"""What ``discover --filing`` fetches at most: an index page and an 8-K document."""
FETCHING = frozenset({"discover", "acquire"})
"""The commands that save fetched bytes under ``--store``."""
STOPS = (AccessStop, UnexpectedResponse, OSError, ValueError, RuntimeError)
"""What ends a live run with ``Stopped:`` and its request count; ``OSError`` covers a
full disk and a saved body that is gone."""
RUNS_DIR = Path("data") / "runs" / "events"
ACQUIRE_LOCK = ".acquire.lock"
"""In ``--runs-dir``: every ``acquire`` run holds it while it counts and records."""


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
    layout = Layout(repo.resolve(), universe_dir, corpus_dir, store, corpus_id)
    if context.invoked_subcommand in FETCHING and (
        refusal := raw_store_refusal(layout.repo, store)
    ):
        _fail(refusal)
    context.obj = layout


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
    """Save what the build reads from SEC, through the shared SEC client. Exit 1,
    naming each one, when a saved response cannot be read: a rerun cannot mend it."""
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
    except STOPS as error:
        typer.echo(f"requests sent: {sent}; a rerun fetches only what is missing")
        _fail(f"Stopped: {error}")
    except BaseException:
        typer.echo(f"requests sent: {sent}; a rerun fetches only what is missing")
        raise
    typer.echo(f"fetched {len(result.fetched)}; requests sent: {sent}")
    for problem in result.problems:
        typer.echo(f"problem: {problem}", err=True)
    if result.problems:
        raise typer.Exit(1)


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
    freeze, with each blocking finding's remedy. A ``period_gap`` or ``no_slots`` is
    acknowledged with its digest; an ``acceptance_time_unknown`` needs its filing's
    index page, which ``events discover --filing`` saves; and no override or
    discover run answers an ``acceptance_time_mismatch``."""
    built, _ = _build(context.obj)
    for line in built.report():
        typer.echo(line)
    for finding in built.blocking:
        if finding.kind in ACKNOWLEDGEABLE:
            typer.echo(f"acknowledge {finding.finding_id} with digest {finding.digest}")
        elif finding.kind is EventFindingKind.ACCEPTANCE_TIME_UNKNOWN:
            cik = built.issuers[finding.issuer_id].cik
            accession = finding.finding_id.removeprefix(f"{finding.kind}:")
            typer.echo(
                f"{finding.finding_id}: run events discover --filing {cik} {accession}"
            )
        elif finding.kind is EventFindingKind.ACCEPTANCE_TIME_MISMATCH:
            typer.echo(f"{finding.finding_id}: no override or discover run answers it")
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
        _holds(error)
    except ValueError as error:
        _fail(f"Refused: {error}")
    definition = frozen.manifest.definition
    verb = "froze" if frozen.created else "unchanged:"
    typer.echo(f"{verb} {definition.corpus_id} v{definition.event_manifest_version}")
    typer.echo(f"{shown(frozen.path, layout.repo)}  {definition.content_hash}")
    typer.echo(shown(frozen.evidence_path, layout.repo))


def _holds(error: EventFreezeRefused) -> NoReturn:
    for reason in error.reasons:
        typer.echo(f"HOLDS  {reason}", err=True)
    raise typer.Exit(1) from error


def _current(layout: Layout) -> tuple[FrozenEvents, UniverseManifest]:
    """The event manifest the build reproduces, printed with its version and hash,
    and the universe version it read (plan 8, P8-4)."""
    built, _ = _build(layout)
    try:
        current = current_events(built, layout.corpus())
    except EventFreezeRefused as error:
        _holds(error)
    except ValueError as error:
        _fail(f"Refused: {error}")
    read = current.manifest.definition
    typer.echo(f"reads {read.corpus_id} v{read.event_manifest_version}")
    typer.echo(f"{shown(current.path, layout.repo)}  {read.content_hash}")
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
    return current, matching[0]


@events.command("select")
def select_command(context: typer.Context) -> None:
    """Run djia-pilot/1 on the event manifest the build reproduces, and freeze the
    pilot."""
    layout: Layout = context.obj
    current, universe = _current(layout)
    try:
        pilot = select_pilot(current.manifest, universe)
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
    typer.echo(f"{shown(frozen.path, layout.repo)}  {definition.content_hash}")


def _closed(url: str, types) -> None:
    raise AccessStop(f"{url} was to be fetched, though nothing was counted to fetch")


@events.command("acquire")
def acquire_command(
    context: typer.Context,
    max_requests: Annotated[
        int | None,
        typer.Option(help="The request count approved at the gate; the client's cap."),
    ] = None,
    runs_dir: Annotated[
        Path, typer.Option(help="Where the state table and canonical documents go.")
    ] = RUNS_DIR,
) -> None:
    """Acquire the current pilot's release documents through the shared SEC client,
    and record each one's processing state."""
    layout: Layout = context.obj
    if refusal := runs_refusal(layout.repo, runs_dir):
        _fail(refusal)
    current, universe = _current(layout)
    try:
        pilot = current_pilot(layout.corpus(), current.manifest, universe)
        overrides = load_acquisition_overrides(layout.corpus() / OVERRIDES_FILE)
    except ValueError as error:
        _fail(f"Refused: {error}")
    definition = pilot.manifest.definition
    typer.echo(f"pilot {definition.pilot_id} v{definition.pilot_version}")
    typer.echo(f"{shown(pilot.path, layout.repo)}  {definition.content_hash}")
    runs = layout.repo / runs_dir
    arguments = (current.manifest, pilot.manifest, universe, layout.store())
    options = {
        "overrides": overrides,
        "states_dir": runs / "states",
        "canonical_dir": runs / "canonical",
        "run_id": f"acquire-{datetime.now(UTC):%Y%m%dT%H%M%S%fZ}",
    }
    with ExitStack() as held:
        try:
            held.enter_context(ProcessLock(runs / ACQUIRE_LOCK))
            first, most = planned_requests(
                current.manifest,
                pilot.manifest,
                layout.store(),
                runs / "states",
                overrides,
            )
        except (AccessStop, ValueError) as error:
            _fail(f"Refused: {error}")
        if most == 0:
            typer.echo("nothing to fetch; the client stays closed")
        else:
            typer.echo(
                f"at most {most} requests to SEC, through the shared client;"
                f" {first} first choices"
            )
            if max_requests is None:
                _fail(
                    "Refused: pass --max-requests, the request count the user approved"
                )
        sent = 0
        try:
            if most == 0:
                result = acquire(*arguments, _closed, **options)
            else:
                with open_sec_client(max_requests=max_requests) as sec:
                    try:
                        result = acquire(*arguments, sec.fetch, **options)
                    finally:
                        sent = sec.throttle.count
        except STOPS as error:
            typer.echo(f"requests sent: {sent}; a rerun attempts what is left")
            _fail(f"Stopped: {error}")
        except BaseException:
            typer.echo(f"requests sent: {sent}; a rerun attempts what is left")
            raise
    for row in pilot.manifest.rows:
        state = result.states[f"{row.event_id}:release"]
        reasons = [str(r) for r in (state.missing_reason, state.failure_reason) if r]
        said = ", ".join([str(state.to_state), *reasons])
        typer.echo(f"{row.selection_order:>3}  {state.document_id}  {said}")
        if state.corpus_error is not None:
            typer.echo(f"     corpus_error: {state.corpus_error}")
    counts = Counter(state.to_state for state in result.states.values())
    typer.echo(", ".join(f"{state} {n}" for state, n in counts.most_common()))
    typer.echo(f"fetched {len(result.fetched)}; requests sent: {sent}")
    if result.path is not None:
        typer.echo(shown(result.path, layout.repo))
    for problem in result.problems:
        typer.echo(f"problem: {problem}", err=True)
    if result.problems:
        raise typer.Exit(1)
