from __future__ import annotations

import asyncio
import inspect
import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, cast

import typer

from agentidem import (
    test_agent,
    test_agent_async,
)
from agentidem.cli.loader import (
    TargetLoadError,
    load_target,
)
from agentidem.cli.output import (
    render_target_error,
    render_test_report,
)
from agentidem.testing.models import TestReport
from agentidem.testing.serialization import (
    report_to_dict,
    save_report,
)


def _run_target(
        target: str,
        func: Callable[..., Any],
) -> TestReport:
    if inspect.iscoroutinefunction(func):
        async_func = cast(
            Callable[..., Awaitable[Any]],
            func,
        )

        return asyncio.run(
            test_agent_async(
                target,
                async_func,
            )
        )

    return test_agent(
        target,
        func,
    )


def test_command(
        target: str = typer.Argument(
            ...,
            help="Python target in module.path:function format.",
        ),
        out: Path | None = typer.Option(
            None,
            "--out",
            help="Write the test report to a JSON file.",
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            help="Print the test report as JSON.",
        ),
) -> None:
    """
    Test an agent for retry and side effect safety.
    """
    try:
        func = load_target(target)

    except TargetLoadError as exc:
        render_target_error(str(exc))
        raise typer.Exit(code=2) from exc

    report = _run_target(
        target,
        func,
    )

    if out is not None:
        save_report(
            report,
            out,
        )

    if json_output:
        typer.echo(
            json.dumps(
                report_to_dict(report),
                indent=2,
            )
        )
    else:
        render_test_report(
            target,
            report,
        )

    if report.baseline_failure is not None:
        raise typer.Exit(code=2)

    if report.safe:
        raise typer.Exit(code=0)

    raise typer.Exit(code=1)