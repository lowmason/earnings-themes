"""Thin A8 commands; every printed value is an ID, hash, count, or closed state."""

from __future__ import annotations

import functools
from collections.abc import Callable
from datetime import date, datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from earnings_core import canonical_json
from earnings_themes.coding.records import CodingError
from earnings_themes.evaluation import EvaluationError, evaluate_gates, load_gates
from earnings_themes.records import IdPart, RecordError
from earnings_themes.split import Partition
from earnings_themes.support.problems import SupportError

from earnings_pipeline.pilot_calibration import calibrate_pilot, checked_calibration
from earnings_pipeline.pilot_inputs import PilotIntake, open_pilot, require_committed
from earnings_pipeline.pilot_labels import (
    check_working,
    checked_pass,
    sample,
    write_view,
)
from earnings_pipeline.pilot_records import PassRecord, read_calibration, read_json
from earnings_pipeline.pilot_reporting import (
    independent_figures,
    load_run,
    write_gates,
    write_report,
)
from earnings_pipeline.pilot_workflow import (
    LoadedPass,
    bind_policy,
    load_pass,
    make_pass,
    make_run,
)
from earnings_pipeline.stage6 import Layout, guarded
from earnings_pipeline.theme_config import WorkflowError, confined_path, read_selected

if TYPE_CHECKING:
    from earnings_themes.evaluation import CalibrationArtifact

    from earnings_pipeline.model_runtime import LiveRuntime

commands = typer.Typer()
labels = typer.Typer(
    no_args_is_help=True, help="Sample, view and check support labels."
)
Settings = Annotated[
    Path, typer.Option("--settings", help="The local workflow selection JSON.")
]
PartitionOption = Annotated[str, typer.Option("--partition", help="train or dev.")]


def safe[**P](command: Callable[P, None]) -> Callable[P, None]:
    @functools.wraps(command)
    def run(*args: P.args, **kwargs: P.kwargs) -> None:
        try:
            command(*args, **kwargs)
        except RecordError as error:
            field = (
                error.name
                if error.name
                in {
                    "partition",
                    "fresh",
                    "labels",
                    "labelled_on",
                    "calibration",
                    "stability",
                    "visibility",
                    "preregistration",
                    "ledger",
                    "report",
                    "settings",
                    "pass",
                    "run",
                    "gold",
                    "coverage",
                }
                else "record.fields"
            )
            typer.echo(f"Refused: {field}: malformed_record", err=True)
            raise typer.Exit(1) from None
        except WorkflowError as error:
            typer.echo(f"Refused: configuration: {error.reason}", err=True)
            raise typer.Exit(1) from None
        except EvaluationError as error:
            typer.echo(f"Refused: evaluation: {error.problem.value}", err=True)
            raise typer.Exit(1) from None
        except (CodingError, SupportError):
            typer.echo("Refused: assessment: malformed_record", err=True)
            raise typer.Exit(1) from None

    return guarded(run)


def part(value: str) -> Partition:
    if value not in {"train", "dev"}:
        raise RecordError("partition", ("wrong_partition",))
    return Partition(value)


def identifier(value: str) -> str:
    # Parse the existing IdPart without defining a new record for CLI arguments.
    from pydantic import TypeAdapter, ValidationError

    try:
        return TypeAdapter(IdPart).validate_python(value, strict=True)
    except ValidationError:
        raise RecordError("fresh", ("malformed_record",)) from None


def intake(context: typer.Context, settings: Path, partition: str) -> PilotIntake:
    selected = part(partition)
    layout: Layout = context.obj
    path = confined_path(layout.repo, settings.as_posix())
    return open_pilot(layout, path, selected)


def baseline(current: PilotIntake) -> LoadedPass:
    path = current.local / current.partition.value / "pass/pass.json"
    record = read_json(
        confined_path(
            current.config.repo,
            path.relative_to(current.config.repo).as_posix(),
            "data/runs/pilot",
        ),
        PassRecord,
        "pass",
    )
    loaded = load_pass(current.config, record)
    checked_pass(current, loaded)
    return loaded


def artifact(current: PilotIntake) -> CalibrationArtifact:
    return checked_calibration(current)


def live(current: PilotIntake, models_root: Path) -> LiveRuntime:
    from earnings_pipeline.model_runtime import build_runtime

    selected = current.settings.runtime_manifest
    path = confined_path(current.config.repo, selected.path)
    require_committed(current.config.repo, path, "runtime_manifest")
    read_selected(current.config, selected)
    built = build_runtime(path, models_root)
    if (
        built.alternative_scorer.identity != current.settings.alternative_scorer
        or built.extractor_family != current.config.extractor_family
    ):
        raise WorkflowError("model_mismatch")
    return built


def support_checkpoint() -> None:
    typer.echo("checkpoint: extraction and classification complete")
    if not typer.confirm(
        "Unload Gemma, load both judges, and confirm support is ready", default=False
    ):
        raise WorkflowError("malformed_record")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@commands.command("pass")
@safe
def pass_command(
    context: typer.Context,
    settings: Settings,
    models_root: Annotated[Path, typer.Option("--models-root")],
    partition: PartitionOption = "train",
) -> None:
    current = intake(context, settings, partition)
    runtime = live(current, models_root)
    record = make_pass(
        current.config,
        runtime.workflow,
        runtime.alternative_scorer,
        partition=current.partition,
        directory=current.local / current.partition.value / "pass",
        fresh=None,
        support_ready=support_checkpoint,
        now=utc_now,
    )
    typer.echo(
        f"partition {record.partition.value} status {record.status} events {len(record.event_ids)}"
    )


@commands.command("run")
@safe
def run_command(
    context: typer.Context,
    settings: Settings,
    partition: PartitionOption = "train",
    fresh: Annotated[str | None, typer.Option("--fresh")] = None,
    models_root: Annotated[Path | None, typer.Option("--models-root")] = None,
) -> None:
    selected = part(partition)
    fresh_id = None if fresh is None else identifier(fresh)
    if fresh_id is not None and (selected is not Partition.DEV or models_root is None):
        raise RecordError("fresh", ("wrong_partition",))
    current = intake(context, settings, partition)
    loaded = baseline(current)
    calibration = artifact(current)
    # FP12: changed settings or artifact refuse BEFORE a fresh dispatch.
    bind_policy(current.config, loaded, calibration, replay=True)
    if fresh_id is not None:
        runtime = live(current, models_root)
        record = make_pass(
            current.config,
            runtime.workflow,
            runtime.alternative_scorer,
            partition=current.partition,
            directory=current.local / "fresh" / fresh_id / "pass",
            fresh=fresh_id,
            support_ready=support_checkpoint,
            now=utc_now,
        )
        loaded = load_pass(current.config, record)
        checked_pass(current, loaded, fresh=True)
    directory = (
        current.local / "fresh" / fresh_id / "run"
        if fresh_id
        else current.local / current.partition.value / "run"
    )
    result = make_run(
        current.config, loaded, calibration, directory=directory, now=utc_now
    )
    typer.echo(
        f"partition {result.partition.value} status {result.status} events {len(result.event_ids)} fresh {result.fresh or 'none'}"
    )


@labels.command("sample")
@safe
def sample_command(
    context: typer.Context,
    settings: Settings,
    partition: PartitionOption = "train",
    extensions: Annotated[int, typer.Option("--extensions")] = 0,
) -> None:
    current = intake(context, settings, partition)
    drawn = sample(current, baseline(current), extensions)
    typer.echo(f"partition {current.partition.value} targets {len(drawn)}")
    for target in drawn:
        typer.echo(target)


@labels.command("view")
@safe
def view_command(
    context: typer.Context,
    settings: Settings,
    labelled_on: Annotated[
        str,
        typer.Option(
            "--labelled-on", help="Your deliberate completion date, YYYY-MM-DD."
        ),
    ],
    partition: PartitionOption = "train",
    extensions: Annotated[int, typer.Option("--extensions")] = 0,
) -> None:
    selected = part(partition)
    try:
        completed = date.fromisoformat(labelled_on)
    except ValueError:
        raise RecordError("labelled_on", ("malformed_record",)) from None
    current = intake(context, settings, selected.value)
    loaded = baseline(current)
    write_view(current, loaded, extensions, completed)
    typer.echo(
        f"partition {current.partition.value} targets {len(sample(current, loaded, extensions))} local_views 1 working_labels 1"
    )


@labels.command("check")
@safe
def check_command(
    context: typer.Context,
    settings: Settings,
    partition: PartitionOption = "train",
    extensions: Annotated[int, typer.Option("--extensions")] = 0,
) -> None:
    current = intake(context, settings, partition)
    loaded = baseline(current)
    check_working(current, loaded, extensions)
    typer.echo(
        f"partition {current.partition.value} targets {len(sample(current, loaded, extensions))} labels checked"
    )


@commands.command("calibrate")
@safe
def calibrate_command(
    context: typer.Context, settings: Settings, partition: PartitionOption = "train"
) -> None:
    if part(partition) is not Partition.TRAIN:
        raise RecordError("partition", ("wrong_partition",))
    current = intake(context, settings, partition)
    path = calibrate_pilot(current, baseline(current))
    result = read_calibration(path)
    typer.echo(f"calibration {result.content_hash} outcome {result.outcome}")


@commands.command("independent")
@safe
def independent_command(
    context: typer.Context, settings: Settings, partition: PartitionOption = "dev"
) -> None:
    if part(partition) is not Partition.DEV:
        raise RecordError("partition", ("wrong_partition",))
    current = intake(context, settings, partition)
    figures = independent_figures(current, baseline(current))
    for figure in figures:
        typer.echo(canonical_json(figure.model_dump(mode="json")))


@commands.command("report")
@safe
def report_command(
    context: typer.Context,
    settings: Settings,
    fresh: Annotated[list[str] | None, typer.Option("--fresh")] = None,
    version: Annotated[int, typer.Option("--version")] = 1,
) -> None:
    ids = tuple(identifier(value) for value in (fresh or []))
    train = intake(context, settings, "train")
    dev = intake(context, settings, "dev")
    first = load_run(train, train.local / "train/run/run-record.json")
    second = load_run(dev, dev.local / "dev/run/run-record.json")
    reruns = tuple(
        load_run(dev, dev.local / "fresh" / run_id / "run/run-record.json")
        for run_id in ids
    )
    target = write_report(train, dev, first, second, reruns, version=version)
    from earnings_themes.evaluation import PilotReport

    report = read_json(target, PilotReport, "report")
    typer.echo(
        f"report {report.content_hash} partitions {len(report.partitions)} independent {len(report.independent)}"
    )


@commands.command("gates")
@safe
def gates_command(
    context: typer.Context,
    settings: Settings,
    report_version: Annotated[int, typer.Option("--report-version")] = 1,
    version: Annotated[int, typer.Option("--version")] = 1,
) -> None:
    current = intake(context, settings, "dev")
    target = write_gates(current, report_version=report_version, version=version)
    from earnings_themes.evaluation import PilotReport

    report = read_json(
        current.pinned.evaluation / f"report-v{report_version}.json",
        PilotReport,
        "report",
    )
    gates = load_gates(target)
    verdict = evaluate_gates(gates, report.partition(Partition.DEV))
    typer.echo(canonical_json(verdict.model_dump(mode="json")))


def register(pilot: typer.Typer) -> None:
    for command in commands.registered_commands:
        pilot.command(command.name)(command.callback)
    pilot.add_typer(labels, name="labels")
