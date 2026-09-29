from __future__ import annotations

from collections.abc import Callable
from typing import Any, Awaitable, ParamSpec, TypeVar

from agentidem.errors import TracedExecutionError
from agentidem.faults.context import reset_operation_index
from agentidem.runtime.context import reset_recorder, set_recorder
from agentidem.trace.models import Trace
from agentidem.trace.recorder import TraceRecorder


P = ParamSpec("P")
R = TypeVar("R")


def run_traced(
        target: str,
        func: Callable[P, R],
        *args: P.args,
        **kwargs: P.kwargs,
) -> tuple[R, Trace]:
    recorder = TraceRecorder(target)
    token = set_recorder(recorder)

    reset_operation_index()

    try:
        result = func(*args, **kwargs)

    except Exception as exc:
        trace = recorder.finish()

        raise TracedExecutionError(
            f"Traced execution failed for {target}",
            trace=trace,
            cause=exc,
        ) from exc

    else:
        trace = recorder.finish()
        return result, trace

    finally:
        reset_recorder(token)


async def run_traced_async(
        target: str,
        func: Callable[..., Awaitable[R]],
        *args: Any,
        **kwargs: Any,
) -> tuple[R, Trace]:
    recorder = TraceRecorder(target)
    token = set_recorder(recorder)

    reset_operation_index()

    try:
        result = await func(*args, **kwargs)

    except Exception as exc:
        trace = recorder.finish()

        raise TracedExecutionError(
            f"Traced execution failed for {target}",
            trace=trace,
            cause=exc,
        ) from exc

    else:
        trace = recorder.finish()
        return result, trace

    finally:
        reset_recorder(token)