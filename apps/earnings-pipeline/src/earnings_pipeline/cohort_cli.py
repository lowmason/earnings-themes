"""``earnings-pipeline cohort``: acquire, cite, build, and freeze the DJIA cohort.

    earnings-pipeline cohort fetch SOURCE_ID URL...        # through robots.txt
    earnings-pipeline cohort register SOURCE_ID FILE --url URL
    earnings-pipeline cohort fetch-sec                      # the shared SEC client
    earnings-pipeline cohort cite SOURCE_ID SHA256 --find TEXT [--line]
    earnings-pipeline cohort build
    earnings-pipeline cohort freeze
    earnings-pipeline cohort terms URL [--saved FILE]
    earnings-pipeline cohort verify-live

Only ``fetch``, ``fetch-sec``, ``terms``, and ``verify-live`` use the network, each
through its client's access policy, and ``terms --saved`` hashes a copy saved in a
browser without it; ``build`` and ``freeze`` read committed files and saved
artifacts alone. ``cite`` prints the TOML to commit on stdout and the cited text
on stderr only, so no source wording is pasted into a committed file by accident.
``fetch`` and ``fetch-sec`` refuse a ``--store`` that does not resolve under
``data/raw``, before any client opens, and every command prints a path outside the
repository in full (``earnings_pipeline.paths``).
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, NoReturn
from urllib.parse import urlsplit

import typer
from earnings_ingestion.cohort.acquire import (
    check_media_type,
    cite,
    fetch_page,
    fetch_sec,
    register_saved,
    terms_digest,
)
from earnings_ingestion.cohort.build import (
    COHORT_STORE,
    CohortBuild,
    CohortError,
    build,
)
from earnings_ingestion.cohort.config import UNIVERSE_DIR, load_cohort_config
from earnings_ingestion.cohort.freeze import FreezeRefused, freeze
from earnings_ingestion.cohort.live import ANY, run_live
from earnings_ingestion.cohort.records import LocatorKind
from earnings_ingestion.cohort.register import (
    MEMBERSHIP_REGISTER,
    SEC_REGISTER,
    Registers,
    load_registers,
)
from earnings_ingestion.cohort.web import open_web_client
from earnings_ingestion.fetch.client import AccessStop, UnexpectedResponse
from earnings_ingestion.fetch.store import ArtifactStore
from earnings_ingestion.sec.client import open_sec_client
from earnings_ingestion.sec.urls import is_sec_host

from earnings_pipeline.paths import raw_store_refusal, shown

cohort = typer.Typer(no_args_is_help=True, help="Stage 4's point-in-time DJIA cohort.")
FETCHING = frozenset({"fetch", "fetch-sec"})
"""The commands that save fetched bytes under ``--store``."""


@dataclass(frozen=True)
class Layout:
    repo: Path
    config_dir: Path
    store_root: Path
    register: Path
    sec_register: Path

    def options(self) -> dict[str, Path]:
        return {
            "config_dir": self.config_dir,
            "store_root": self.store_root,
            "register": self.register,
            "sec_register": self.sec_register,
        }

    def store(self) -> ArtifactStore:
        return ArtifactStore(self.repo / self.store_root, self.repo)

    def registers(self) -> Registers:
        return load_registers(self.repo, self.register, self.sec_register)


@cohort.callback()
def main(
    context: typer.Context,
    repo: Annotated[Path, typer.Option(help="The repository root.")] = Path(),
    config_dir: Annotated[Path, typer.Option(help="The curated files.")] = UNIVERSE_DIR,
    store: Annotated[Path, typer.Option(help="The artifact store.")] = COHORT_STORE,
    register: Annotated[
        Path, typer.Option(help="The membership source register.")
    ] = MEMBERSHIP_REGISTER,
    sec_register: Annotated[
        Path, typer.Option(help="The register holding sec-edgar.")
    ] = SEC_REGISTER,
) -> None:
    """Paths are relative to --repo; the defaults are the real cohort's."""
    layout = Layout(repo.resolve(), config_dir, store, register, sec_register)
    if context.invoked_subcommand in FETCHING and (
        refusal := raw_store_refusal(layout.repo, store)
    ):
        _fail(refusal)
    context.obj = layout


def _fail(message: str) -> NoReturn:
    typer.echo(message, err=True)
    raise typer.Exit(1)


@cohort.command("fetch")
def fetch_command(
    context: typer.Context,
    source_id: str,
    urls: Annotated[list[str], typer.Argument(help="Pages of that source.")],
) -> None:
    """Save pages of a registered source, each after its robots.txt allows it."""
    layout: Layout = context.obj
    registers = layout.registers()
    hosts = sorted({urlsplit(url).hostname or "" for url in urls})
    try:
        with open_web_client(hosts) as web:
            for url in urls:
                ref = fetch_page(web.fetch, layout.store(), registers, source_id, url)
                typer.echo(f"{ref.content_sha256}  {ref.storage_ref}  {url}")
    except (AccessStop, UnexpectedResponse, ValueError) as error:
        _fail(f"Stopped: {error}")


@cohort.command("register")
def register_command(
    context: typer.Context,
    source_id: str,
    path: Path,
    url: Annotated[str, typer.Option(help="Where the page was saved from.")],
    media_type: Annotated[str, typer.Option()] = "text/html",
    saved_at: Annotated[
        datetime | None,
        typer.Option(help="When it was saved, in UTC; default the file's time."),
    ] = None,
) -> None:
    """Save a page a person saved in a browser, recording that nothing was fetched."""
    layout: Layout = context.obj
    when = saved_at or datetime.fromtimestamp(path.stat().st_mtime, UTC)
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    try:
        ref = register_saved(
            layout.store(),
            layout.registers(),
            source_id,
            path.read_bytes(),
            url=url,
            media_type=media_type,
            saved_at=when.astimezone(UTC),
        )
    except ValueError as error:
        _fail(f"Refused: {error}")
    typer.echo(f"{ref.content_sha256}  {ref.storage_ref}  {url}")


@cohort.command("fetch-sec")
def fetch_sec_command(context: typer.Context) -> None:
    """Save the SEC records the build reads, through the shared SEC client."""
    layout: Layout = context.obj
    config = load_cohort_config(layout.repo / layout.config_dir)
    try:
        with open_sec_client() as sec:
            result = fetch_sec(sec.fetch, layout.store(), layout.registers(), config)
            requests = sec.throttle.count
    except (AccessStop, UnexpectedResponse, ValueError) as error:
        _fail(f"Stopped: {error}")
    typer.echo(f"fetched {len(result.fetched)}, already saved {len(result.kept)}")
    typer.echo(f"requests sent: {requests}")


@cohort.command("cite")
def cite_command(
    context: typer.Context,
    source_id: str,
    sha256: str,
    find: Annotated[str | None, typer.Option(help="Text to find.")] = None,
    occurrence: Annotated[int, typer.Option(help="Which occurrence, from 1.")] = 1,
    span: Annotated[
        tuple[int, int] | None, typer.Option(help="START END offsets.")
    ] = None,
    pointer: Annotated[str | None, typer.Option(help="A JSON pointer.")] = None,
    line: Annotated[
        bool, typer.Option(help="Cite the whole line holding --find: a table row.")
    ] = False,
) -> None:
    """Print the locator to commit (stdout) and the cited text (stderr only)."""
    layout: Layout = context.obj
    try:
        locator, text = cite(
            layout.store(),
            layout.registers(),
            source_id,
            sha256,
            find=find,
            occurrence=occurrence,
            span=span,
            pointer=pointer,
            line=line,
        )
    except (FileNotFoundError, ValueError) as error:
        _fail(f"Refused: {error}")
    if locator.kind is LocatorKind.TEXT_SPAN:
        typer.echo(f'canonical_sha256 = "{locator.canonical_sha256}"')
        typer.echo(f"span = [{locator.start}, {locator.end}]")
    else:
        typer.echo(f'pointer = "{locator.pointer}"')
    typer.echo(f'cited_sha256 = "{locator.cited_sha256}"')
    typer.echo(f"cited text, not for committing: {text!r}", err=True)


def _build(layout: Layout) -> CohortBuild:
    try:
        return build(layout.repo, **layout.options())
    except CohortError as error:
        for problem in error.problems:
            typer.echo(f"problem: {problem}", err=True)
        raise typer.Exit(1) from error


@cohort.command("build")
def build_command(context: typer.Context) -> None:
    """Build from committed files and saved artifacts; print what holds the freeze."""
    built = _build(context.obj)
    for finding in built.report.findings:
        state = (
            "BLOCKING"
            if finding.holds_freeze
            else "resolved"
            if finding.resolved_by
            else "noted"
        )
        typer.echo(f"{state}  {finding.finding_id}  digest {finding.digest}")
        typer.echo(f"    {finding.detail}")
    for override_id in built.stale_acknowledgements:
        typer.echo(f"STALE  {override_id} acknowledges a finding that has changed")
    typer.echo(
        f"{len(built.intervals)} intervals, {len(built.candidate_issuer_ids)} candidate"
        f" issuers, {len(built.report.blocking)} blocking findings,"
        f" content {built.content_hash}"
    )
    if built.report.blocking or built.stale_acknowledgements:
        raise typer.Exit(1)


@cohort.command("freeze")
def freeze_command(context: typer.Context) -> None:
    """Freeze the build as a new version, or name the version that already holds it."""
    layout: Layout = context.obj
    built = _build(layout)
    try:
        frozen = freeze(
            built,
            layout.repo / layout.config_dir / "manifests",
            now=datetime.now(UTC),
        )
    except FreezeRefused as error:
        for finding in error.blocking:
            typer.echo(f"BLOCKING  {finding.finding_id}: {finding.detail}", err=True)
        for override_id in error.stale:
            typer.echo(f"STALE  {override_id}", err=True)
        raise typer.Exit(1) from error
    verb = "froze" if frozen.created else "unchanged:"
    definition = frozen.manifest.definition
    typer.echo(f"{verb} {definition.universe_id} v{definition.universe_version}")
    typer.echo(f"{shown(frozen.path, layout.repo)}  {definition.content_hash}")


@cohort.command("terms")
def terms_command(
    context: typer.Context,
    url: str,
    saved: Annotated[
        Path | None,
        typer.Option(help="A copy saved in a browser: hash it, and send nothing."),
    ] = None,
    media_type: Annotated[str, typer.Option(help="The saved copy's type.")] = (
        "text/html"
    ),
) -> None:
    """Print the hash a register records for a terms page: fetched from URL, or
    read from a copy that a person saved in a browser (plan 6, P6-24)."""
    if saved is not None:
        body = saved.read_bytes()
        try:
            check_media_type(body, media_type)
            digest = terms_digest(body, media_type)
        except ValueError as error:
            _fail(f"Refused: {error}")
        typer.echo(f'terms_sha256 = "{digest}"')
        return
    host = urlsplit(url).hostname or ""
    try:
        if is_sec_host(host):
            with open_sec_client() as sec:
                fetched = sec.fetch(url, ANY)
        else:
            with open_web_client([host]) as web:
                fetched = web.fetch(url, ANY)
    except (AccessStop, UnexpectedResponse, ValueError) as error:
        _fail(f"Stopped: {error}")
    digest = terms_digest(fetched.body, fetched.retrieval.media_type)
    typer.echo(f'terms_sha256 = "{digest}"')


@cohort.command("verify-live")
def verify_live_command(context: typer.Context) -> None:
    """The opt-in live verification (P-VL); saves its record under data/runs/."""
    layout: Layout = context.obj
    try:
        result, path = run_live(layout.repo)
    except (AccessStop, ValueError) as error:
        _fail(f"Stopped: {error}")
    for check in result.checks:
        typer.echo(
            f"{check.outcome:9}  {check.purpose:8}  {check.source_id}  {check.url}"
        )
    typer.echo(
        f"rebuilt {result.rebuilt_content_hash}; frozen {result.frozen_content_hash}"
    )
    typer.echo(f"record: {shown(path, layout.repo)}")
