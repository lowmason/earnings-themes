"""``earnings-pipeline pilot``: Stage 6's split and coverage report (the Stage 6
spec, §The split and §The coverage report; plan 9), and Stage 11's counts-only
recheck and coverage v2 (the Stage 11 spec, A6(4) and A7; plan 17).

    uv run --locked earnings-pipeline pilot split
    uv run --locked earnings-pipeline pilot coverage
    uv run --locked earnings-pipeline pilot coverage --version 2
    uv run --locked earnings-pipeline pilot recount

``split`` and ``coverage`` read the pinned pilot by path and write a frozen record
under ``evaluation/<corpus>/pilot-v<N>/``, once: running either again with the same
result changes nothing, and a different result is refused. Neither reads a document,
selects anything, or sends a request (P-C7). ``coverage`` reads the state table; a
rebuild reads only the runs the report names. Version 2 reads version 1's runs, and
each signed gold file's ``no_theme`` for train and dev, and refuses until every train
and dev bundle with a parsed document has signed gold (R12.4).

``recount`` rebuilds each committed gold file from its kept draft and working copy,
under ``data/runs/gold/drafts/``, and reports any count that differs, by event and
field. It reads each file's document, prints only IDs and counts, and writes nothing
(GS5, GS13).
"""

from pathlib import Path
from typing import Annotated

import typer
from earnings_ingestion.events.coverage import build_coverage, load_coverage
from earnings_ingestion.events.freeze import serialize
from earnings_themes.annotation import load_gold_draft, recount
from earnings_themes.codebook import Codebook
from earnings_themes.gold import load_gold
from earnings_themes.records import RecordError, record_json
from earnings_themes.split import (
    SPLIT_POLICY,
    Partition,
    SplitEvent,
    SplitManifest,
    split_events,
)

from earnings_pipeline.codebook_cli import pinned_codebook, pinned_split
from earnings_pipeline.stage6 import (
    Layout,
    Pinned,
    documents,
    fail,
    file_stem,
    fixture_event_ids,
    guarded,
    load_bundle,
    load_pinned,
    options,
    record_error,
    transitions,
    write_once,
)

pilot = typer.Typer(
    no_args_is_help=True,
    help="Stage 6's split and coverage report, and Stage 11's recount, over the pin.",
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


Events = Annotated[
    list[str] | None,
    typer.Argument(help="Event IDs; every committed gold file when none is named."),
]


def _recount(
    layout: Layout,
    pinned: Pinned,
    split: SplitManifest,
    codebook: Codebook,
    doc_ids: dict[str, str],
    path: Path,
) -> int:
    """One committed gold file, rebuilt from its kept draft and working copy: its
    counts printed when it rebuilds, each refusal by event and field when not."""
    try:
        record = load_gold(path)
    except RecordError as error:
        record_error(error)
    event_id = record.event_id
    if path.stem != file_stem(event_id):
        fail(f"Refused: {layout.shown(path)} holds the gold of {event_id}")
    kept = [
        layout.drafts / f"{file_stem(event_id)}.{kind}.toml"
        for kind in ("draft", "working")
    ]
    for draft in kept:
        if not draft.is_file():
            fail(
                f"Refused: {event_id}: {layout.shown(draft)} is not here; GS5's"
                " counts rebuild from the kept draft and its working copy"
            )
    try:
        drafted = load_gold_draft(kept[0])
        working = load_gold_draft(kept[1])
    except RecordError as error:
        record_error(error)
    refusals = recount(
        path.read_bytes(),
        drafted,
        working,
        bundle=load_bundle(layout, doc_ids, event_id),
        pin=pinned.pin,
        split=split,
        codebook=codebook,
    )
    for refusal in refusals:
        typer.echo(f"refused: {event_id} {refusal}", err=True)
    if not refusals:
        counts = record.counts
        typer.echo(
            f"recounted {event_id} ({record.partition}): accepted {counts.accepted},"
            f" edited {counts.edited}, rejected {counts.rejected}, added"
            f" {counts.added}"
        )
    return len(refusals)


@pilot.command("recount")
@guarded
def recount_command(context: typer.Context, event_ids: Events = None) -> None:
    """Rebuild each committed gold file's GS5 counts from its kept draft and working
    copy; write nothing."""
    layout: Layout = context.obj
    codebook = pinned_codebook(layout)
    pinned = load_pinned(layout)
    split = pinned_split(layout, pinned)
    if event_ids:
        paths = [pinned.gold_dir / f"{file_stem(e)}.toml" for e in event_ids]
        if missing := [p for p in paths if not p.is_file()]:
            fail(f"Refused: {layout.shown(missing[0])} is not committed")
    else:
        paths = sorted(pinned.gold_dir.glob("*.toml"))
        if not paths:
            fail(f"Refused: no gold is committed under {layout.shown(pinned.gold_dir)}")
    doc_ids = documents(layout, pinned)
    problems = sum(
        _recount(layout, pinned, split, codebook, doc_ids, path) for path in paths
    )
    if problems:
        fail(
            f"Refused: {problems} problem(s); GS5's shares wait until each is resolved"
        )
    typer.echo(f"recounted {len(paths)} file(s): each rebuilds from its kept draft")
