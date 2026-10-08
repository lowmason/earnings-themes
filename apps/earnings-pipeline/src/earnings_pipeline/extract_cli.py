"""Offline extraction command with closed metadata-only diagnostics."""

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer

from earnings_pipeline.theme_config import WorkflowError, load_workflow_config
from earnings_pipeline.theme_workflow import (
    WorkflowResult,
    replay_runtime,
    run_theme_workflow,
)

extract = typer.Typer(
    no_args_is_help=True, help="Explicit saved-response theme extraction."
)


@extract.command()
def run(
    config: Annotated[Path, typer.Option(help="Explicit replay JSON configuration.")],
) -> None:
    try:
        selected = load_workflow_config(config, repo=Path.cwd())
        result = run_theme_workflow(
            selected, replay_runtime(selected), now=lambda: datetime.now(UTC)
        )
        if type(result) is not WorkflowResult:
            raise WorkflowError("malformed_record")
        result = replace(result)
        # Only fields produced by checked contracts reach Click's output boundary.
        typer.echo(
            f"run={result.run_id} scope={result.scope} status={result.status} reason={result.reason or 'none'} states={result.state_count}"
        )
        typer.echo(
            f"receipt=receipt-{result.receipt_hash} sha256={result.receipt_hash}"
        )
        for kind, value in (
            ("analysis", result.analysis_hash),
            ("report", result.report_hash),
            ("state", result.state_hash),
        ):
            if value is not None:
                typer.echo(f"{kind}={kind}-{value} sha256={value}")
        for phase, count in result.phase_counts:
            typer.echo(f"phase={phase} rows={count}")
        if result.failure_hash is not None:
            typer.echo(
                f"failure=failure-{result.failure_hash} sha256={result.failure_hash}"
            )
        if result.status in {"failed", "state_pending"}:
            raise typer.Exit(1)
    except typer.Exit:
        raise
    except WorkflowError as error:
        typer.echo(f"phase=preflight status=failed reason={error.reason}", err=True)
        raise typer.Exit(1) from None
    except Exception:  # noqa: BLE001 - final CLI boundary suppresses arbitrary diagnostic text.
        typer.echo("status=failed reason=unexpected_error", err=True)
        raise typer.Exit(1) from None
