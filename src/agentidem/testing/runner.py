from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from typing import Any, TypeVar

from agentidem.errors import TracedExecutionError
from agentidem.faults.suite import (
    run_before_operation_failure_suite,
    run_before_operation_failure_suite_async,
    run_duplicate_delivery_suite,
    run_duplicate_delivery_suite_async,
    run_lost_ack_suite,
    run_lost_ack_suite_async,
)
from agentidem.invariants.api import InvariantFunction
from agentidem.runtime.runner import (
    run_traced,
    run_traced_async,
)
from agentidem.testing.models import (
    BaselineFailure,
    TestReport,
)


R = TypeVar("R")


def test_agent(
        target: str,
        func: Callable[..., R],
        *args: Any,
        invariants: Iterable[InvariantFunction] = (),
        **kwargs: Any,
) -> TestReport:
    try:
        _, baseline = run_traced(
            target,
            func,
            *args,
            **kwargs,
        )

    except TracedExecutionError as exc:
        return TestReport(
            baseline=exc.trace,
            results=(),
            baseline_failure=BaselineFailure(
                error_type=type(exc.cause).__name__,
                message=str(exc.cause),
                trace=exc.trace,
            ),
        )

    results = [
        *run_lost_ack_suite(
            target,
            func,
            baseline,
            *args,
            invariants=invariants,
            **kwargs,
        ),
        *run_before_operation_failure_suite(
            target,
            func,
            baseline,
            *args,
            invariants=invariants,
            **kwargs,
        ),
        *run_duplicate_delivery_suite(
            target,
            func,
            *args,
            invariants=invariants,
            **kwargs,
        ),
    ]

    return TestReport(
        baseline=baseline,
        results=tuple(results),
    )


async def test_agent_async(
        target: str,
        func: Callable[..., Awaitable[R]],
        *args: Any,
        invariants: Iterable[InvariantFunction] = (),
        **kwargs: Any,
) -> TestReport:
    try:
        _, baseline = await run_traced_async(
            target,
            func,
            *args,
            **kwargs,
        )

    except TracedExecutionError as exc:
        return TestReport(
            baseline=exc.trace,
            results=(),
            baseline_failure=BaselineFailure(
                error_type=type(exc.cause).__name__,
                message=str(exc.cause),
                trace=exc.trace,
            ),
        )

    lost_ack_results = await run_lost_ack_suite_async(
        target,
        func,
        baseline,
        *args,
        invariants=invariants,
        **kwargs,
    )

    before_failure_results = (
        await run_before_operation_failure_suite_async(
            target,
            func,
            baseline,
            *args,
            invariants=invariants,
            **kwargs,
        )
    )

    duplicate_delivery_results = (
        await run_duplicate_delivery_suite_async(
            target,
            func,
            *args,
            invariants=invariants,
            **kwargs,
        )
    )

    results = [
        *lost_ack_results,
        *before_failure_results,
        *duplicate_delivery_results,
    ]

    return TestReport(
        baseline=baseline,
        results=tuple(results),
    )


setattr(test_agent, "__test__", False)
setattr(test_agent_async, "__test__", False)