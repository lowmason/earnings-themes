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
from earnings_ingestion.events.coverage import (
    NoThemeCount,
    build_coverage,
    load_coverage,
    parsed_documents,
)
from earnings_ingestion.events.freeze import serialize
from earnings_themes.annotation import check_countable, load_gold_draft, recount
from earnings_themes.codebook import Codebook
from earnings_themes.gold import Gold, load_gold
from earnings_themes.problems import Refusal
from earnings_themes.records import RecordError, record_json
from earnings_themes.split import (
    SPLIT_POLICY,
    Partition,
    SplitManifest,
)

from earnings_pipeline.codebook_cli import pinned_codebook, pinned_split
from earnings_pipeline.stage6 import (
    Events,
    Layout,
    Pinned,
    committed_gold,
    derive_split,
    documents,
    fail,
    file_stem,
    guarded,
    kept_drafts,
    load_bundle,
    load_pinned,
    options,
    record_error,
    refuse,
    require_train_dev,
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
    try:
        manifest = derive_split(layout, pinned)
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


Version = Annotated[
    int,
    typer.Option(
        "--version", help="1, or 2 with train's and dev's no-theme counts (R12.4)."
    ),
]


def _no_theme(
    layout: Layout, pinned: Pinned, run_ids: tuple[str, ...]
) -> list[NoThemeCount]:
    """Train's and dev's no-theme rows over the bundles with a parsed document
    under ``run_ids``. Each bundle needs committed gold whose pin, split, partition,
    codebook, signature, and ``no_theme`` hold, read without its document (R12.4)."""
    under = [t for t in transitions(layout) if t.run_id in run_ids]
    parsed = parsed_documents(under, pinned.pin.pilot_hash)
    split = pinned_split(layout, pinned)
    codebook = pinned_codebook(layout)
    rows: list[NoThemeCount] = []
    unsigned: list[str] = []
    refusals: list[Refusal] = []
    for partition in (Partition.TRAIN, Partition.DEV):
        events = [e for e in split.events_in(partition) if e in parsed]
        flags = []
        for event_id in events:
            path = pinned.gold_dir / f"{file_stem(event_id)}.toml"
            if not path.is_file():
                unsigned.append(event_id)
                continue
            try:
                gold = load_gold(path)
            except RecordError as error:
                record_error(error)
            require_train_dev(event_id, split.partition_of(event_id))
            require_train_dev(event_id, gold.partition)
            found = check_countable(
                gold,
                event_id=event_id,
                pin=pinned.pin,
                split=split,
                codebook=codebook,
                doc_id=parsed[event_id],
            )
            refusals += [Refusal(f"{event_id} {r.subject}", r.reason) for r in found]
            flags.append(gold.no_theme)
        rows.append(
            NoThemeCount(
                partition=partition.value, bundles=len(events), no_theme=sum(flags)
            )
        )
    for event_id in unsigned:
        typer.echo(f"no signed gold  {event_id}", err=True)
    if unsigned:
        fail(
            f"Refused: {len(unsigned)} train and dev bundle(s) with a parsed document"
            " have no signed gold; coverage v2 waits for every one (R12.4)"
        )
    if refusals:
        refuse(refusals)
    return rows


@pilot.command("coverage")
@guarded
def coverage_command(context: typer.Context, version: Version = 1) -> None:
    """Count the pinned pilot's documents by state, and freeze coverage-v<N>.json;
    version 2 adds train's and dev's no-theme counts over version 1's runs."""
    layout: Layout = context.obj
    if version not in (1, 2):
        fail("Refused: coverage has versions 1 and 2")
    pinned = load_pinned(layout)
    first = pinned.coverage_file(1)
    if version == 2 and not first.is_file():
        fail(
            f"Refused: {layout.shown(first)} is not frozen; coverage v2 reads its"
            " runs: run pilot coverage"
        )
    try:
        run_ids = load_coverage(first).run_ids if first.is_file() else None
    except ValueError as error:
        fail(f"Refused: {error}")
    no_theme = _no_theme(layout, pinned, run_ids or ()) if version == 2 else []
    try:
        report = build_coverage(
            pinned.pilot,
            pinned.coverage_pin,
            transitions(layout),
            run_ids=run_ids,
            version=version,
            no_theme=no_theme,
        )
    except ValueError as error:
        fail(f"Refused: {error}")
    path = pinned.coverage_file(version)
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
    for row in report.no_theme:
        typer.echo(
            f"no_theme  {row.partition}  {row.no_theme} of {row.bundles} bundles"
        )
    typer.echo(f"runs  {', '.join(report.run_ids)}")
    verb = "froze" if created else "unchanged:"
    typer.echo(
        f"{verb} coverage v{report.coverage_version}: {report.documents} documents"
    )
    typer.echo(f"{layout.shown(path)}  {report.content_hash}")


def _recount(
    layout: Layout,
    pinned: Pinned,
    split: SplitManifest,
    codebook: Codebook,
    doc_ids: dict[str, str],
    path: Path,
    record: Gold,
) -> int:
    """One committed gold file, rebuilt from its kept draft and working copy: its
    counts printed when it rebuilds, each refusal by event and field when not."""
    event_id = record.event_id
    kept = kept_drafts(layout, event_id)
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
    records = committed_gold(layout, pinned, event_ids, require_nonempty=True)
    for _, record in records:
        event_id = record.event_id
        try:
            partition = split.partition_of(event_id)
        except KeyError:
            fail(f"Refused: {event_id} is not in the split")
        require_train_dev(event_id, partition)
        require_train_dev(event_id, record.partition)
    doc_ids = documents(layout, pinned)
    problems = sum(
        _recount(layout, pinned, split, codebook, doc_ids, path, record)
        for path, record in records
    )
    if problems:
        fail(
            f"Refused: {problems} problem(s); GS5's shares wait until each is resolved"
        )
    typer.echo(f"recounted {len(records)} file(s): each rebuilds from its kept draft")
