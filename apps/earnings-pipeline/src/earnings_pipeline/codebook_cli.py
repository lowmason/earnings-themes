"""``earnings-pipeline codebook``: codebook v0's freeze and check (the Stage 6 spec,
§The codebook; GS9; plan 9).

    uv run --locked earnings-pipeline codebook freeze
    uv run --locked earnings-pipeline codebook freeze --adr docs/adr/0003-...md \\
        --approver "Lowell Mason" --approved-on 2026-10-02
    uv run --locked earnings-pipeline codebook validate

``freeze`` reads the user's working copy, ``data/runs/gold/drafts/
codebook.working.toml``, anchors each example in the training bundles, and prints
the content hash. It writes nothing until ADR 0003 is named: then it checks that
the ADR cites that hash, and writes ``codebooks/djia-pilot/codebook-v0.toml`` once,
approved. Before printing the hash, it checks the codebook against every text the
committed wording guard reads. ``validate`` rechecks the committed version against
the local documents. Neither prints a document's text.
"""

from datetime import date
from pathlib import Path
from typing import Annotated

import typer
from earnings_themes.anchoring import Bundle
from earnings_themes.codebook import (
    Approval,
    Codebook,
    codebook_toml,
    freeze_codebook,
    load_codebook,
    load_codebook_draft,
    validate_codebook,
)
from earnings_themes.records import RecordError
from earnings_themes.split import Partition, SplitManifest, load_split

from earnings_pipeline.stage6 import (
    CODEBOOK_FILE,
    GOLD_RUNS,
    Layout,
    Pinned,
    documents,
    fail,
    guarded,
    load_bundle,
    load_pinned,
    options,
    record_error,
    refuse,
    wording_refusals,
    wording_texts,
    write_once,
)

codebook = typer.Typer(no_args_is_help=True, help="Stage 6's codebook v0.")
codebook.callback()(options)
WORKING = GOLD_RUNS / "drafts" / "codebook.working.toml"


def pinned_split(layout: Layout, pinned: Pinned) -> SplitManifest:
    """The frozen split of the pinned pilot, or a refusal."""
    try:
        split = load_split(pinned.split_path)
    except RecordError as error:
        typer.echo(f"problem: {error}", err=True)
        fail(
            f"Refused: {layout.shown(pinned.split_path)} is not frozen: run pilot split"
        )
    if split.pin != pinned.pin:
        fail(f"Refused: {layout.shown(pinned.split_path)} names another pin")
    return split


def training(layout: Layout, pinned: Pinned, split: SplitManifest) -> dict[str, Bundle]:
    """Each training event with a parsed document; an event without one is named."""
    doc_ids = documents(layout, pinned)
    bundles = {}
    for event_id in split.events_in(Partition.TRAIN):
        if event_id in doc_ids:
            bundles[event_id] = load_bundle(layout, doc_ids, event_id)
        else:
            typer.echo(f"no parsed document  {event_id}")
    return bundles


def _examples(made: Codebook) -> int:
    return sum(len(t.positive_examples) + len(t.hard_negatives) for t in made.themes)


@codebook.command("freeze")
@guarded
def freeze_command(
    context: typer.Context,
    working: Annotated[Path, typer.Option(help="The user's working copy.")] = WORKING,
    adr: Annotated[
        Path | None, typer.Option(help="ADR 0003, which cites the content hash.")
    ] = None,
    approver: Annotated[str | None, typer.Option(help="Who approved.")] = None,
    approved_on: Annotated[
        str | None, typer.Option(help="The approval's date, YYYY-MM-DD.")
    ] = None,
) -> None:
    """Anchor and check the working copy; with --adr, write the approved v0."""
    layout: Layout = context.obj
    pinned = load_pinned(layout)
    split = pinned_split(layout, pinned)
    bundles = training(layout, pinned, split)
    try:
        draft = load_codebook_draft(layout.repo / working)
    except RecordError as error:
        record_error(error)
    approval = None
    if adr is not None:
        if approver is None or approved_on is None:
            fail("Refused: --adr needs --approver and --approved-on")
        try:
            day = date.fromisoformat(approved_on)
        except ValueError:
            fail(f"Refused: {approved_on} is not a date such as 2026-10-02")
        approval = Approval(approver=approver, approved_on=day, adr=adr.as_posix())
    made = freeze_codebook(
        draft, pin=pinned.pin, split=split, bundles=bundles, approval=approval
    )
    if isinstance(made, list):
        refuse(made)
    if found := wording_refusals(made, wording_texts(layout, pinned)):
        refuse(found)
    typer.echo(
        f"codebook {made.codebook_id} v{made.codebook_version}: {len(made.themes)}"
        f" themes, {_examples(made)} examples, from {len(bundles)} training bundles"
    )
    typer.echo(f"content_hash  {made.content_hash}")
    if approval is None:
        typer.echo(
            "not written: ADR 0003 cites this hash; then run freeze again with --adr,"
            " --approver, and --approved-on"
        )
        return
    adr_path = layout.repo / adr
    if not adr_path.is_file() or made.content_hash not in adr_path.read_text(
        encoding="utf-8"
    ):
        fail(f"Refused: {adr} does not cite {made.content_hash}")
    path = layout.repo / CODEBOOK_FILE
    created = write_once(path, codebook_toml(made).encode(), layout)
    verb = "froze" if created else "unchanged:"
    typer.echo(f"{verb} {made.codebook_id} v{made.codebook_version}, approved")
    typer.echo(f"{layout.shown(path)}  {made.content_hash}")


def pinned_codebook(layout: Layout) -> Codebook:
    """The committed codebook version, or a refusal."""
    path = layout.repo / CODEBOOK_FILE
    if not path.is_file():
        fail(f"Refused: {layout.shown(path)} is not frozen: run codebook freeze")
    try:
        return load_codebook(path)
    except RecordError as error:
        record_error(error)


@codebook.command("validate")
@guarded
def validate_command(context: typer.Context) -> None:
    """Recheck the committed version against the local training bundles."""
    layout: Layout = context.obj
    pinned = load_pinned(layout)
    split = pinned_split(layout, pinned)
    made = pinned_codebook(layout)
    bundles = training(layout, pinned, split)
    adr_text = None
    if made.approval is not None and (layout.repo / made.approval.adr).is_file():
        adr_text = (layout.repo / made.approval.adr).read_text(encoding="utf-8")
    refusals = validate_codebook(
        made, pin=pinned.pin, split=split, bundles=bundles, adr_text=adr_text
    )
    found = wording_refusals(made, wording_texts(layout, pinned))
    refusals += [refusal for refusal in found if refusal not in refusals]
    if refusals:
        refuse(refusals, "changed")
    approval = made.approval
    assert approval is not None
    typer.echo(
        f"valid: {made.codebook_id} v{made.codebook_version}, {len(made.themes)}"
        f" themes, approved by {approval.approver} on {approval.approved_on}"
    )
    typer.echo(f"{layout.shown(layout.repo / CODEBOOK_FILE)}  {made.content_hash}")
