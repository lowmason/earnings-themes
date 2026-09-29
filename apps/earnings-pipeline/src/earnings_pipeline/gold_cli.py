"""``earnings-pipeline gold``: anchoring, views, and validation of Stage 6's gold
(the Stage 6 spec, §Anchoring and validation and §Drafting and tools; GS4, GS5,
GS13; plan 9).

    uv run --locked earnings-pipeline gold show --text --training
    uv run --locked earnings-pipeline gold anchor cik-0000051143:2024-12-31
    uv run --locked earnings-pipeline gold show cik-0000051143:2024-12-31
    uv run --locked earnings-pipeline gold validate

A drafting session writes ``data/runs/gold/drafts/<name>.draft.toml``, which stays
unchanged, and the user edits ``<name>.working.toml`` beside it; ``<name>`` is an
event's ``file_stem``, such as ``cik-0000051143_2024-12-31``, or ``hard-negatives``
for the curated set. ``anchor`` anchors the working copy and writes the result to
``data/runs/gold/anchored/<name>.toml``; once the
working copy is signed, it also writes the committed record, once. Before either
write it checks the record against every text the committed wording guard reads,
and a signed record that differs from the one already written is refused before
anything changes. ``show`` writes
the local views and texts the user and the drafting sessions open. ``validate``
rechecks committed records against their local documents. No command prints a
document's text (GS13).
"""

from pathlib import Path
from typing import Annotated

import tomllib
import typer
from earnings_themes.anchoring import Bundle
from earnings_themes.annotation import (
    build_curated,
    build_gold,
    load_curated_draft,
    load_gold_draft,
    signed,
    validate_curated,
    validate_gold,
)
from earnings_themes.codebook import Codebook
from earnings_themes.gold import (
    DraftCounts,
    Gold,
    HardNegativeSet,
    gold_toml,
    load_gold,
    load_hard_negatives,
)
from earnings_themes.records import RecordError
from earnings_themes.split import Partition, SplitManifest
from earnings_themes.view import render_curated_view, render_text, render_view

from earnings_pipeline.codebook_cli import pinned_codebook, pinned_split
from earnings_pipeline.stage6 import (
    CODEBOOK_FILE,
    FIXTURE_MANIFEST,
    HARD_NEGATIVES,
    Layout,
    Pinned,
    documents,
    fail,
    file_stem,
    guarded,
    load_bundle,
    load_fixture,
    load_pinned,
    options,
    record_error,
    refuse,
    replace,
    wording_refusals,
    wording_texts,
    write_once,
)

gold = typer.Typer(no_args_is_help=True, help="Stage 6's gold set.")
gold.callback()(options)
CURATED = "hard-negatives"

Events = Annotated[list[str] | None, typer.Argument(help="Event IDs.")]
Curated = Annotated[
    bool, typer.Option("--hard-negatives", help="The curated hard negatives.")
]


def fixture_bundles(layout: Layout) -> dict[str, Bundle]:
    """Stage 1's canonical fixtures, by the IDs the fixtures' manifest lists."""
    path = layout.repo / FIXTURE_MANIFEST
    try:
        fixtures = tomllib.loads(path.read_text(encoding="utf-8"))["fixtures"]
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        fail(f"Refused: {layout.shown(path)} does not list Stage 1's fixtures")
    ids = sorted(fixture["fixture_id"] for fixture in fixtures)
    return {fixture_id: load_fixture(layout, fixture_id) for fixture_id in ids}


def readable(partition: Partition, codebook_frozen: bool) -> str | None:
    """Why an event's text or gold may not be touched yet, or ``None``. No session
    reads a dev bundle before codebook v0 is approved, or a test bundle before Stage
    14 freezes its configuration (GS13, GS18); an excluded event has no gold (GS7)."""
    if partition is Partition.EXCLUDED:
        return "is excluded, so it has no gold"
    if partition is Partition.TEST:
        return "is a test bundle, which waits for Stage 14 (GS18)"
    if partition is Partition.DEV and not codebook_frozen:
        return "is a dev bundle, which waits for codebook v0's approval (GS13)"
    return None


def _open(layout: Layout, split: SplitManifest, event_id: str) -> None:
    """Refuse an event outside the split, or one ``readable`` holds back."""
    try:
        partition = split.partition_of(event_id)
    except KeyError:
        fail(f"Refused: {event_id} is not in the split")
    reason = readable(partition, (layout.repo / CODEBOOK_FILE).is_file())
    if reason is not None:
        fail(f"Refused: {event_id} {reason}")


def _drafts(layout: Layout, name: str, check: bool) -> tuple[Path, Path]:
    """The kept draft and the working copy. ``--check`` without a working copy
    checks the draft alone, as a drafting session checks its own."""
    drafted = layout.drafts / f"{file_stem(name)}.draft.toml"
    working = layout.drafts / f"{file_stem(name)}.working.toml"
    if check and drafted.is_file() and not working.is_file():
        typer.echo(f"checking the draft alone: {name} has no working copy yet")
        working = drafted
    for path in (drafted, working):
        if not path.is_file():
            fail(
                f"Refused: {name}: {layout.shown(path)} is not here; a drafting"
                " session writes the draft, and the working copy starts as a copy"
                " of it"
            )
    return drafted, working


def _counts(counts: DraftCounts) -> str:
    return (
        f"accepted {counts.accepted}, edited {counts.edited}, rejected"
        f" {counts.rejected}, added {counts.added}"
    )


def _write(
    layout: Layout, name: str, text: str, committed: Path, is_signed: bool, check: bool
) -> None:
    if check:
        typer.echo(f"checked {name}: nothing written")
        return
    if is_signed and committed.is_file() and committed.read_bytes() != text.encode():
        fail(
            f"Refused: {layout.shown(committed)} holds other content; a changed"
            " record is a new version, never an edit"
        )
    anchored = layout.gold_runs / "anchored" / f"{file_stem(name)}.toml"
    replace(anchored, text)
    typer.echo(f"anchored  {layout.shown(anchored)}")
    if not is_signed:
        typer.echo(
            f"unsigned: {name} is not committed until the working copy's annotator"
            " is signed"
        )
        return
    created = write_once(committed, text.encode(), layout)
    typer.echo(f"{'froze' if created else 'unchanged:'} {layout.shown(committed)}")


def _anchor_event(
    layout: Layout,
    pinned: Pinned,
    codebook: Codebook,
    doc_ids: dict[str, str],
    texts: dict[str, str],
    event_id: str,
    check: bool,
) -> None:
    split = pinned_split(layout, pinned)
    _open(layout, split, event_id)
    bundle = load_bundle(layout, doc_ids, event_id)
    drafted_path, working_path = _drafts(layout, event_id, check)
    try:
        drafted = load_gold_draft(drafted_path)
        working = load_gold_draft(working_path)
    except RecordError as error:
        record_error(error)
    made = build_gold(
        drafted, working, bundle=bundle, pin=pinned.pin, split=split, codebook=codebook
    )
    if isinstance(made, list):
        refuse(made)
    if found := wording_refusals(made, texts):
        refuse(found)
    typer.echo(
        f"{event_id} ({made.partition}): {len(made.quotes)} quotes, {len(made.claims)}"
        f" claims, {len(made.assignments)} assignments, {len(made.hard_negatives)}"
        f" hard negatives; no_theme {str(made.no_theme).lower()}"
    )
    typer.echo(f"origins: {_counts(made.counts)}")
    committed = pinned.gold_dir / f"{file_stem(event_id)}.toml"
    _write(layout, event_id, gold_toml(made), committed, signed(made.annotator), check)


def _anchor_curated(
    layout: Layout,
    pinned: Pinned,
    codebook: Codebook,
    texts: dict[str, str],
    check: bool,
) -> None:
    drafted_path, working_path = _drafts(layout, CURATED, check)
    try:
        drafted = load_curated_draft(drafted_path)
        working = load_curated_draft(working_path)
    except RecordError as error:
        record_error(error)
    bundles = fixture_bundles(layout)
    made = build_curated(
        drafted, working, bundles=bundles, pin=pinned.pin, codebook=codebook
    )
    if isinstance(made, list):
        refuse(made)
    if found := wording_refusals(made, texts):
        refuse(found)
    negatives = [n for d in made.documents for n in d.hard_negatives]
    kinds = ", ".join(
        f"{kind} {sum(1 for n in negatives if n.negative_kind == kind)}"
        for kind in sorted({n.negative_kind for n in negatives})
    )
    typer.echo(
        f"{CURATED}: {len(made.documents)} fixtures, {len(negatives)} hard negatives"
        f" ({kinds})"
    )
    typer.echo(f"origins: {_counts(made.counts)}")
    committed = layout.repo / HARD_NEGATIVES
    _write(layout, CURATED, gold_toml(made), committed, signed(made.annotator), check)


@gold.command("anchor")
@guarded
def anchor_command(
    context: typer.Context,
    event_ids: Events = None,
    hard_negatives: Curated = False,
    check: Annotated[
        bool, typer.Option("--check", help="Anchor and check; write nothing.")
    ] = False,
) -> None:
    """Anchor each working copy; commit the record once it is signed."""
    layout: Layout = context.obj
    if not event_ids and not hard_negatives:
        fail("Refused: name the events to anchor, or --hard-negatives")
    codebook = pinned_codebook(layout)
    pinned = load_pinned(layout)
    texts = wording_texts(layout, pinned)
    if hard_negatives:
        _anchor_curated(layout, pinned, codebook, texts, check)
    if event_ids:
        doc_ids = documents(layout, pinned)
        for event_id in event_ids:
            _anchor_event(layout, pinned, codebook, doc_ids, texts, event_id, check)


def _latest(layout: Layout, name: str, committed: Path) -> Path:
    anchored = layout.gold_runs / "anchored" / f"{file_stem(name)}.toml"
    for path in (anchored, committed):
        if path.is_file():
            return path
    fail(f"Refused: {name} is not anchored: run gold anchor")


def _show_texts(
    layout: Layout,
    pinned: Pinned,
    event_ids: list[str],
    training: bool,
    hard_negatives: bool,
) -> None:
    written = 0
    if event_ids or training:
        doc_ids = documents(layout, pinned)
        split = pinned_split(layout, pinned)
        if training:
            event_ids = [
                e for e in split.events_in(Partition.TRAIN) if e in doc_ids
            ] + event_ids
        for event_id in dict.fromkeys(event_ids):
            _open(layout, split, event_id)
            bundle = load_bundle(layout, doc_ids, event_id)
            path = layout.gold_runs / "texts" / f"{file_stem(event_id)}.md"
            replace(path, render_text(bundle))
            written += 1
    if hard_negatives:
        for fixture_id, bundle in fixture_bundles(layout).items():
            path = layout.gold_runs / "texts" / "fixtures" / f"{fixture_id}.md"
            replace(path, render_text(bundle))
            written += 1
    texts = "text" if written == 1 else "texts"
    typer.echo(
        f"wrote {written} {texts} under {layout.shown(layout.gold_runs / 'texts')}"
    )


@gold.command("show")
@guarded
def show_command(
    context: typer.Context,
    event_ids: Events = None,
    text: Annotated[
        bool, typer.Option("--text", help="Write texts for drafting, not views.")
    ] = False,
    training: Annotated[
        bool, typer.Option("--training", help="With --text: every training event.")
    ] = False,
    hard_negatives: Curated = False,
) -> None:
    """Write local views (or, with --text, texts) under data/runs/gold/."""
    layout: Layout = context.obj
    event_ids = event_ids or []
    if training and not text:
        fail("Refused: --training writes texts; add --text")
    if not event_ids and not training and not hard_negatives:
        fail("Refused: name the events to show, or --training, or --hard-negatives")
    pinned = load_pinned(layout)
    if text:
        _show_texts(layout, pinned, event_ids, training, hard_negatives)
        return
    views = layout.gold_runs / "views"
    if hard_negatives:
        path = _latest(layout, CURATED, layout.repo / HARD_NEGATIVES)
        try:
            curated = load_hard_negatives(path)
        except RecordError as error:
            record_error(error)
        bundles = fixture_bundles(layout)
        for document in curated.documents:
            bundle = bundles.get(document.fixture_id)
            if bundle is None:
                fail(f"Refused: {document.fixture_id} is not a Stage 1 fixture")
            out = views / CURATED / f"{document.fixture_id}.md"
            replace(out, render_curated_view(bundle, document))
            typer.echo(f"view  {layout.shown(out)}")
    if event_ids:
        doc_ids = documents(layout, pinned)
        split = pinned_split(layout, pinned)
        for event_id in event_ids:
            _open(layout, split, event_id)
            committed = pinned.gold_dir / f"{file_stem(event_id)}.toml"
            path = _latest(layout, event_id, committed)
            try:
                record = load_gold(path)
            except RecordError as error:
                record_error(error)
            bundle = load_bundle(layout, doc_ids, event_id)
            out = views / f"{file_stem(event_id)}.md"
            replace(out, render_view(bundle, record))
            typer.echo(f"view  {layout.shown(out)}")


def _validate_event(
    layout: Layout,
    pinned: Pinned,
    codebook: Codebook,
    doc_ids: dict[str, str],
    texts: dict[str, str],
    path: Path,
) -> int:
    try:
        record: Gold = load_gold(path)
    except RecordError as error:
        record_error(error)
    if path.stem != file_stem(record.event_id):
        fail(f"Refused: {layout.shown(path)} holds the gold of {record.event_id}")
    split = pinned_split(layout, pinned)
    bundle = load_bundle(layout, doc_ids, record.event_id)
    refusals = validate_gold(
        record, bundle=bundle, pin=pinned.pin, split=split, codebook=codebook
    )
    found = wording_refusals(record, texts)
    refusals += [refusal for refusal in found if refusal not in refusals]
    for refusal in refusals:
        typer.echo(f"refused: {record.event_id} {refusal}", err=True)
    if not refusals:
        typer.echo(
            f"valid: {record.event_id} ({record.partition}), {len(record.quotes)}"
            f" quotes, {len(record.claims)} claims, signed"
        )
    return len(refusals)


def _validate_curated(layout: Layout, pinned: Pinned, codebook: Codebook) -> int:
    """Offline, so the default suite runs it: the wording is checked against Stage
    1's fixtures, which are committed; ``gold anchor`` checked it against the
    pilot's documents too, and the wording guard's local leg does."""
    path = layout.repo / HARD_NEGATIVES
    if not path.is_file():
        fail(f"Refused: {layout.shown(path)} is not committed")
    try:
        record: HardNegativeSet = load_hard_negatives(path)
    except RecordError as error:
        record_error(error)
    refusals = validate_curated(
        record, bundles=fixture_bundles(layout), pin=pinned.pin, codebook=codebook
    )
    for refusal in refusals:
        typer.echo(f"refused: {CURATED} {refusal}", err=True)
    if not refusals:
        negatives = sum(len(d.hard_negatives) for d in record.documents)
        typer.echo(
            f"valid: {CURATED}, {len(record.documents)} fixtures, {negatives} hard"
            " negatives, signed"
        )
    return len(refusals)


@gold.command("validate")
@guarded
def validate_command(
    context: typer.Context, event_ids: Events = None, hard_negatives: Curated = False
) -> None:
    """Recheck committed gold (every file, unless events are named)."""
    layout: Layout = context.obj
    codebook = pinned_codebook(layout)
    pinned = load_pinned(layout)
    problems = 0
    if hard_negatives:
        problems += _validate_curated(layout, pinned, codebook)
    if event_ids or not hard_negatives:
        if event_ids:
            paths = [pinned.gold_dir / f"{file_stem(e)}.toml" for e in event_ids]
            missing = [p for p in paths if not p.is_file()]
            if missing:
                fail(f"Refused: {layout.shown(missing[0])} is not committed")
        else:
            paths = sorted(pinned.gold_dir.glob("*.toml"))
            if not paths:
                typer.echo(f"no gold committed under {layout.shown(pinned.gold_dir)}")
        doc_ids = documents(layout, pinned) if paths else {}
        texts = wording_texts(layout, pinned) if paths else {}
        for path in paths:
            problems += _validate_event(layout, pinned, codebook, doc_ids, texts, path)
    if problems:
        fail(f"Refused: {problems} problem(s)")
