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
from agentidem.cli.output import render_target_error
from agentidem.errors import TracedExecutionError
from agentidem.runtime.runner import (
    run_traced,
    run_traced_async,
)
from agentidem.trace.models import Trace, TraceOperation
from agentidem.trace.serialization import load_trace


def _operation_signature(
        operation: TraceOperation,
) -> tuple[Any, ...]:
    return (
        operation.name,
        operation.kind,
        operation.args,
        operation.identity,
        operation.result,
        operation.error,
        operation.status,
        operation.observation,
    )


def _traces_match(
        expected: Trace,
        actual: Trace,
) -> bool:
    if expected.target != actual.target:
        return False

    if len(expected.operations) != len(actual.operations):
        return False

    return all(
        _operation_signature(expected_operation)
        == _operation_signature(actual_operation)
        for expected_operation, actual_operation in zip(
            expected.operations,
            actual.operations,
            strict=True,
        )
    )


def _run_replay_target(
        target: str,
        func: Callable[..., Any],
) -> Trace:
    if inspect.iscoroutinefunction(func):
        async_func = cast(
            Callable[..., Awaitable[Any]],
            func,
        )

        try:
            _, trace = asyncio.run(
                run_traced_async(
                    target,
                    async_func,
                )
            )
        except TracedExecutionError as exc:
            return exc.trace

        return trace

    try:
        _, trace = run_traced(
            target,
            func,
        )
    except TracedExecutionError as exc:
        return exc.trace

    return trace


def replay_command(
        trace_path: Path = typer.Argument(
            ...,
            help="Path to a recorded AgentIdem trace.",
        ),
) -> None:
    """
    Re-run a recorded target and compare its execution trace.
    """
    try:
        expected_trace = load_trace(trace_path)
    except Exception as exc:
        render_target_error(
            f"Failed to load trace '{trace_path}': {exc}"
        )
        raise typer.Exit(code=2) from exc

    try:
        func = load_target(expected_trace.target)
    except TargetLoadError as exc:
        render_target_error(str(exc))
        raise typer.Exit(code=2) from exc

    actual_trace = _run_replay_target(
        expected_trace.target,
        func,
    )

    if _traces_match(
            expected_trace,
            actual_trace,
    ):
        typer.echo(
            f"REPLAY MATCH: {expected_trace.target}"
        )
        raise typer.Exit(code=0)

    typer.echo(
        f"REPLAY MISMATCH: {expected_trace.target}"
    )
    raise typer.Exit(code=1)