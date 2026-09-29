from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, cast

import typer

from agentidem.cli.loader import (
    TargetLoadError,
    load_target,
)
from agentidem.cli.output import (
    render_target_error,
)
from agentidem.errors import TracedExecutionError
from agentidem.runtime.runner import (
    run_traced,
    run_traced_async,
)
from agentidem.trace.models import Trace
from agentidem.trace.serialization import save_trace


def _record_target(
        target: str,
        func: Callable[..., Any],
) -> Trace:
    if inspect.iscoroutinefunction(func):
        async_func = cast(
            Callable[..., Awaitable[Any]],
            func,
        )

        _, trace = asyncio.run(
            run_traced_async(
                target,
                async_func,
            )
        )

        return trace

    _, trace = run_traced(
        target,
        func,
    )

    return trace


def record_command(
        target: str = typer.Argument(
            ...,
            help="Python target in module.path:function format.",
        ),
        out: Path = typer.Option(
            Path("trace.json"),
            "--out",
            help="Write the recorded trace to a JSON file.",
        ),
) -> None:
    """
    Run an agent once and record its execution trace.
    """
    try:
        func = load_target(target)

    except TargetLoadError as exc:
        render_target_error(str(exc))
        raise typer.Exit(code=2) from exc

    try:
        trace = _record_target(
            target,
            func,
        )

    except TracedExecutionError as exc:
        save_trace(
            exc.trace,
            out,
        )

        render_target_error(
            f"{type(exc.cause).__name__}: {exc.cause}"
        )

        raise typer.Exit(code=2) from exc

    save_trace(
        trace,
        out,
    )

    typer.echo(
        f"Recorded trace to {out}"
    )