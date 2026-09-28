"""The ``earnings-pipeline`` command line.

    uv run --locked --all-packages earnings-pipeline browser setup
    uv run --locked --all-packages earnings-pipeline cohort --help
    uv run --locked --all-packages earnings-pipeline events --help

``browser setup`` is the only command that downloads the pinned Chrome for Testing and
chromedriver (B8). It checks each archive against the committed manifest and installs
into a cache outside the repository; a capture never downloads anything. ``cohort``
holds Stage 4's commands (``earnings_pipeline.cohort_cli``), and ``events`` Stage 5's
(``earnings_pipeline.events_cli``).
"""

from pathlib import Path
from typing import Annotated

import typer
from earnings_ingestion.browser.install import (
    default_cache,
    download,
    install,
    load_pin,
)

from earnings_pipeline.cohort_cli import cohort
from earnings_pipeline.events_cli import events

app = typer.Typer(no_args_is_help=True, help="The earnings pipeline.")
browser = typer.Typer(
    no_args_is_help=True, help="The pinned browser for Stage 3's diagnostic path."
)
app.add_typer(browser, name="browser")
app.add_typer(cohort, name="cohort")
app.add_typer(events, name="events")


@browser.command()
def setup(
    cache: Annotated[
        Path | None,
        typer.Option(help="Install here instead of the default cache directory."),
    ] = None,
) -> None:
    """Download, check, and install the pinned Chrome for Testing and chromedriver."""
    pin = load_pin()
    if pin is None:
        typer.echo("No Chrome for Testing build is pinned for this platform.", err=True)
        raise typer.Exit(1)
    try:
        binaries = install(pin, cache or default_cache(), download)
    except ValueError as error:
        typer.echo(f"Refused: {error}", err=True)
        raise typer.Exit(1) from error
    typer.echo(f"Chrome for Testing {pin.version} ({pin.platform})")
    typer.echo(f"browser: {binaries.browser}")
    typer.echo(f"driver: {binaries.driver}")
