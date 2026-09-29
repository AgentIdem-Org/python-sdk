from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, TypeVar

from agentidem.errors import IdentityResolutionError
from agentidem.faults.context import advance_operation_index
from agentidem.faults.injector import InjectedFaultError, inject_if_planned
from agentidem.faults.plan import FaultPhase
from agentidem.runtime.context import get_recorder
from agentidem.trace.models import (
    ObservationStatus,
    OperationKind,
    OperationStatus,
    TraceOperation,
)


T = TypeVar("T")


def _resolve_identity(
        name: str,
        identity_func: Callable[..., Any] | None,
        *args: Any,
        **kwargs: Any,
) -> Any | None:
    if identity_func is None:
        return None

    try:
        return identity_func(*args, **kwargs)
    except Exception as exc:
        raise IdentityResolutionError(
            name,
            cause=exc,
        ) from exc


def execute_operation(
        name: str,
        kind: OperationKind,
        func: Callable[..., T],
        identity_func: Callable[..., Any] | None,
        *args: Any,
        **kwargs: Any,
) -> T:
    recorder = get_recorder()
    operation_index = advance_operation_index()

    operation_identity = _resolve_identity(
        name,
        identity_func,
        *args,
        **kwargs,
    )

    operation = TraceOperation(
        name=name,
        kind=kind,
        args={
            "args": list(args),
            "kwargs": kwargs,
        },
        identity=operation_identity,
        status=OperationStatus.SUCCESS,
        observation=ObservationStatus.RECEIVED,
    )

    if recorder is not None:
        recorder.add_operation(operation)

    try:
        try:
            inject_if_planned(
                operation_index=operation_index,
                operation_name=name,
                phase=FaultPhase.BEFORE_OPERATION,
            )

        except InjectedFaultError as exc:
            operation.status = OperationStatus.FAILED
            operation.observation = ObservationStatus.FAILED
            operation.error = f"{type(exc).__name__}: {exc}"

            raise

        result = func(*args, **kwargs)

        operation.result = result
        operation.status = OperationStatus.SUCCESS

        try:
            inject_if_planned(
                operation_index=operation_index,
                operation_name=name,
                phase=FaultPhase.AFTER_OPERATION,
            )

        except InjectedFaultError:
            operation.observation = ObservationStatus.LOST
            raise

        return result

    except InjectedFaultError:
        raise

    except Exception as exc:
        operation.status = OperationStatus.FAILED
        operation.observation = ObservationStatus.FAILED
        operation.error = f"{type(exc).__name__}: {exc}"

        raise

    finally:
        operation.completed_at = datetime.now(timezone.utc)


async def execute_operation_async(
        name: str,
        kind: OperationKind,
        func: Callable[..., Any],
        identity_func: Callable[..., Any] | None,
        *args: Any,
        **kwargs: Any,
) -> Any:
    recorder = get_recorder()
    operation_index = advance_operation_index()

    operation_identity = _resolve_identity(
        name,
        identity_func,
        *args,
        **kwargs,
    )

    operation = TraceOperation(
        name=name,
        kind=kind,
        args={
            "args": list(args),
            "kwargs": kwargs,
        },
        identity=operation_identity,
        status=OperationStatus.SUCCESS,
        observation=ObservationStatus.RECEIVED,
    )

    if recorder is not None:
        recorder.add_operation(operation)

    try:
        try:
            inject_if_planned(
                operation_index=operation_index,
                operation_name=name,
                phase=FaultPhase.BEFORE_OPERATION,
            )

        except InjectedFaultError as exc:
            operation.status = OperationStatus.FAILED
            operation.observation = ObservationStatus.FAILED
            operation.error = f"{type(exc).__name__}: {exc}"

            raise

        result = await func(*args, **kwargs)

        operation.result = result
        operation.status = OperationStatus.SUCCESS

        try:
            inject_if_planned(
                operation_index=operation_index,
                operation_name=name,
                phase=FaultPhase.AFTER_OPERATION,
            )

        except InjectedFaultError:
            operation.observation = ObservationStatus.LOST
            raise

        return result

    except InjectedFaultError:
        raise

    except Exception as exc:
        operation.status = OperationStatus.FAILED
        operation.observation = ObservationStatus.FAILED
        operation.error = f"{type(exc).__name__}: {exc}"

        raise

    finally:
        operation.completed_at = datetime.now(timezone.utc)