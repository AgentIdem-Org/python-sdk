from __future__ import annotations

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar, overload

from agentidem.runtime.operations import (
    execute_operation,
    execute_operation_async,
)
from agentidem.trace.models import OperationKind


P = ParamSpec("P")
R = TypeVar("R")


def read(func: Callable[P, R]) -> Callable[P, R]:
    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(
                *args: P.args,
                **kwargs: P.kwargs,
        ) -> Any:
            return await execute_operation_async(
                func.__name__,
                OperationKind.READ,
                func,
                None,
                *args,
                **kwargs,
            )

        return async_wrapper  # type: ignore[return-value]

    @wraps(func)
    def wrapper(
            *args: P.args,
            **kwargs: P.kwargs,
    ) -> R:
        return execute_operation(
            func.__name__,
            OperationKind.READ,
            func,
            None,
            *args,
            **kwargs,
        )

    return wrapper


@overload
def write(func: Callable[P, R]) -> Callable[P, R]:
    ...


@overload
def write(
        *,
        identity: Callable[..., Any] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    ...


def write(
        func: Callable[P, R] | None = None,
        *,
        identity: Callable[..., Any] | None = None,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(target: Callable[P, R]) -> Callable[P, R]:
        if inspect.iscoroutinefunction(target):

            @wraps(target)
            async def async_wrapper(
                    *args: P.args,
                    **kwargs: P.kwargs,
            ) -> Any:
                return await execute_operation_async(
                    target.__name__,
                    OperationKind.WRITE,
                    target,
                    identity,
                    *args,
                    **kwargs,
                )

            return async_wrapper  # type: ignore[return-value]

        @wraps(target)
        def wrapper(
                *args: P.args,
                **kwargs: P.kwargs,
        ) -> R:
            return execute_operation(
                target.__name__,
                OperationKind.WRITE,
                target,
                identity,
                *args,
                **kwargs,
            )

        return wrapper

    if func is not None:
        return decorator(func)

    return decorator