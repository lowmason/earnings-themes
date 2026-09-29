"""``earnings-pipeline pilot``: Stage 6's split and coverage report (the Stage 6
spec, §The split and §The coverage report; plan 9).

    uv run --locked earnings-pipeline pilot split
    uv run --locked earnings-pipeline pilot coverage

Both read the pinned pilot by path and write a frozen record under
``evaluation/<corpus>/pilot-v<N>/``, once: running either again with the same result
changes nothing, and a different result is refused. Neither reads a document,
selects anything, or sends a request (P-C7). ``coverage`` reads the state table; a
rebuild reads only the runs the report names.
"""

import typer
from earnings_ingestion.events.coverage import build_coverage, load_coverage
from earnings_ingestion.events.freeze import serialize
from earnings_themes.records import record_json
from earnings_themes.split import (
    SPLIT_POLICY,
    Partition,
    SplitEvent,
    split_events,
)

from earnings_pipeline.stage6 import (
    Layout,
    Pinned,
    fail,
    fixture_event_ids,
    guarded,
    load_pinned,
    options,
    transitions,
    write_once,
)

pilot = typer.Typer(
    no_args_is_help=True, help="Stage 6's split and coverage report, over the pin."
)
pilot.callback()(options)


def _said(pinned: Pinned, layout: Layout) -> None:
    pin = pinned.pin
    typer.echo(f"pilot {pin.pilot_id} v{pin.pilot_version}  {pin.pilot_hash}")


@pilot.command("split")
@guarded
def split_command(context: typer.Context) -> None:
    """Split the pinned pilot by issuer-time/1, and freeze split-v1.json."""
    layout: Layout = context.obj
    pinned = load_pinned(layout)
    rows = {row.event_id: row for row in pinned.events.rows}
    events = [
        SplitEvent(
            event_id=row.event_id,
            issuer_id=rows[row.event_id].issuer_id,
            period_end=rows[row.event_id].period_end,
        )
        for row in pinned.pilot.rows
    ]
    try:
        manifest = split_events(
            events,
            pinned.pin,
            fixture_event_ids=fixture_event_ids(layout, pinned.events),
        )
    except ValueError as error:
        fail(f"Refused: {error}")
    created = write_once(pinned.split_path, record_json(manifest), layout)
    _said(pinned, layout)
    for partition in Partition:
        typer.echo(f"{partition}  {len(manifest.events_in(partition))}")
    for row in manifest.rows:
        if row.reason is not None:
            typer.echo(f"excluded  {row.event_id}  {row.reason}")
    verb = "froze" if created else "unchanged:"
    typer.echo(f"{verb} split v{manifest.split_version} by {SPLIT_POLICY}")
    typer.echo(f"{layout.shown(pinned.split_path)}  {manifest.content_hash}")


@pilot.command("coverage")
@guarded
def coverage_command(context: typer.Context) -> None:
    """Count the pinned pilot's documents by state, and freeze coverage-v1.json."""
    layout: Layout = context.obj
    pinned = load_pinned(layout)
    path = pinned.coverage_path
    try:
        run_ids = load_coverage(path).run_ids if path.exists() else None
        report = build_coverage(
            pinned.pilot, pinned.coverage_pin, transitions(layout), run_ids=run_ids
        )
    except ValueError as error:
        fail(f"Refused: {error}")
    created = write_once(path, serialize(report), layout)
    _said(pinned, layout)
    for count in report.states:
        if count.count:
            typer.echo(f"{count.state}  {count.count}")
    for gap in report.gaps:
        typer.echo(f"gap  {gap.state}  ({gap.basis}: never repaired by reselecting)")
    for override in report.overrides:
        typer.echo(
            f"override  {override.override_id}  {override.document_id}"
            f"  {override.verdict}"
        )
    typer.echo(f"runs  {', '.join(report.run_ids)}")
    verb = "froze" if created else "unchanged:"
    typer.echo(
        f"{verb} coverage v{report.coverage_version}: {report.documents} documents"
    )
    typer.echo(f"{layout.shown(path)}  {report.content_hash}")
