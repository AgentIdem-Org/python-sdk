from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from typing import Any, TypeVar

from agentidem.faults.case import FaultCase
from agentidem.faults.runner import (
    FaultRunResult,
    build_fault_result,
    run_fault,
    run_fault_async,
)
from agentidem.faults.scenarios import (
    DUPLICATE_DELIVERY_SCENARIO,
    build_before_operation_failure_plans,
    build_lost_ack_plans,
    combine_duplicate_delivery_traces,
)
from agentidem.invariants.api import InvariantFunction
from agentidem.runtime.runner import (
    run_traced,
    run_traced_async,
)
from agentidem.trace.models import Trace


R = TypeVar("R")


def run_lost_ack_suite(
        target: str,
        func: Callable[..., R],
        baseline: Trace,
        *args: Any,
        invariants: Iterable[InvariantFunction] = (),
        **kwargs: Any,
) -> list[FaultRunResult]:
    plans = build_lost_ack_plans(baseline)

    results: list[FaultRunResult] = []

    for plan in plans:
        result = run_fault(
            target,
            func,
            plan,
            *args,
            invariants=invariants,
            **kwargs,
        )

        results.append(result)

    return results


async def run_lost_ack_suite_async(
        target: str,
        func: Callable[..., Awaitable[R]],
        baseline: Trace,
        *args: Any,
        invariants: Iterable[InvariantFunction] = (),
        **kwargs: Any,
) -> list[FaultRunResult]:
    plans = build_lost_ack_plans(baseline)

    results: list[FaultRunResult] = []

    for plan in plans:
        result = await run_fault_async(
            target,
            func,
            plan,
            *args,
            invariants=invariants,
            **kwargs,
        )

        results.append(result)

    return results


def run_before_operation_failure_suite(
        target: str,
        func: Callable[..., R],
        baseline: Trace,
        *args: Any,
        invariants: Iterable[InvariantFunction] = (),
        **kwargs: Any,
) -> list[FaultRunResult]:
    plans = build_before_operation_failure_plans(baseline)

    results: list[FaultRunResult] = []

    for plan in plans:
        result = run_fault(
            target,
            func,
            plan,
            *args,
            invariants=invariants,
            **kwargs,
        )

        results.append(result)

    return results


async def run_before_operation_failure_suite_async(
        target: str,
        func: Callable[..., Awaitable[R]],
        baseline: Trace,
        *args: Any,
        invariants: Iterable[InvariantFunction] = (),
        **kwargs: Any,
) -> list[FaultRunResult]:
    plans = build_before_operation_failure_plans(baseline)

    results: list[FaultRunResult] = []

    for plan in plans:
        result = await run_fault_async(
            target,
            func,
            plan,
            *args,
            invariants=invariants,
            **kwargs,
        )

        results.append(result)

    return results


def run_duplicate_delivery_suite(
        target: str,
        func: Callable[..., R],
        *args: Any,
        invariants: Iterable[InvariantFunction] = (),
        **kwargs: Any,
) -> list[FaultRunResult]:
    _, first_trace = run_traced(
        target,
        func,
        *args,
        **kwargs,
    )

    _, second_trace = run_traced(
        target,
        func,
        *args,
        **kwargs,
    )

    combined_trace = combine_duplicate_delivery_traces(
        first_trace,
        second_trace,
    )

    case = FaultCase(
        scenario=DUPLICATE_DELIVERY_SCENARIO,
        message="The same agent invocation was delivered twice.",
    )

    result = build_fault_result(
        case=case,
        trace=combined_trace,
        invariants=invariants,
    )

    return [result]


async def run_duplicate_delivery_suite_async(
        target: str,
        func: Callable[..., Awaitable[R]],
        *args: Any,
        invariants: Iterable[InvariantFunction] = (),
        **kwargs: Any,
) -> list[FaultRunResult]:
    _, first_trace = await run_traced_async(
        target,
        func,
        *args,
        **kwargs,
    )

    _, second_trace = await run_traced_async(
        target,
        func,
        *args,
        **kwargs,
    )

    combined_trace = combine_duplicate_delivery_traces(
        first_trace,
        second_trace,
    )

    case = FaultCase(
        scenario=DUPLICATE_DELIVERY_SCENARIO,
        message="The same agent invocation was delivered twice.",
    )

    result = build_fault_result(
        case=case,
        trace=combined_trace,
        invariants=invariants,
    )

    return [result]