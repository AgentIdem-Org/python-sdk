from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from typing import Any, TypeVar

from agentidem.detection import (
    DuplicateWrite,
    Finding,
    detect_duplicate_write_findings,
    detect_duplicate_writes,
)
from agentidem.errors import TracedExecutionError
from agentidem.faults.case import FaultCase
from agentidem.faults.context import reset_fault_plan, set_fault_plan
from agentidem.faults.plan import FaultPlan
from agentidem.invariants.api import InvariantFunction
from agentidem.invariants.evaluator import evaluate_invariants
from agentidem.invariants.models import InvariantResult
from agentidem.runtime.runner import (
    run_traced,
    run_traced_async,
)
from agentidem.trace.models import Trace


R = TypeVar("R")


class FaultRunResult:
    def __init__(
            self,
            *,
            case: FaultCase,
            trace: Trace,
            plan: FaultPlan | None = None,
            result: object | None = None,
            error: Exception | None = None,
            invariants: list[InvariantResult] | None = None,
            duplicates: list[DuplicateWrite] | None = None,
            findings: list[Finding] | None = None,
    ) -> None:
        self.case = case
        self.plan = plan
        self.trace = trace
        self.result = result
        self.error = error
        self.invariants = invariants or []
        self.duplicates = duplicates or []
        self.findings = findings or []

    @property
    def failed(self) -> bool:
        return self.error is not None

    @property
    def safe(self) -> bool:
        invariants_passed = all(
            invariant.passed
            for invariant in self.invariants
        )

        no_error_findings = all(
            finding.severity.value != "error"
            for finding in self.findings
        )

        return invariants_passed and no_error_findings


def _case_from_plan(plan: FaultPlan) -> FaultCase:
    return FaultCase(
        scenario=plan.scenario,
        operation_index=plan.operation_index,
        operation_name=plan.operation_name,
        phase=plan.phase,
        message=plan.message,
    )


def build_fault_result(
        *,
        case: FaultCase,
        trace: Trace,
        plan: FaultPlan | None = None,
        result: object | None = None,
        error: Exception | None = None,
        invariants: Iterable[InvariantFunction] = (),
) -> FaultRunResult:
    invariant_results = evaluate_invariants(
        invariants,
        trace,
    )

    duplicates = detect_duplicate_writes(
        trace,
    )

    findings = detect_duplicate_write_findings(
        trace,
    )

    return FaultRunResult(
        case=case,
        plan=plan,
        trace=trace,
        result=result,
        error=error,
        invariants=invariant_results,
        duplicates=duplicates,
        findings=findings,
    )


def run_fault(
        target: str,
        func: Callable[..., R],
        plan: FaultPlan,
        *args: Any,
        invariants: Iterable[InvariantFunction] = (),
        **kwargs: Any,
) -> FaultRunResult:
    token = set_fault_plan(plan)
    case = _case_from_plan(plan)

    try:
        try:
            result, trace = run_traced(
                target,
                func,
                *args,
                **kwargs,
            )

        except TracedExecutionError as exc:
            return build_fault_result(
                case=case,
                plan=plan,
                trace=exc.trace,
                error=exc.cause,
                invariants=invariants,
            )

        return build_fault_result(
            case=case,
            plan=plan,
            trace=trace,
            result=result,
            invariants=invariants,
        )

    finally:
        reset_fault_plan(token)


async def run_fault_async(
        target: str,
        func: Callable[..., Awaitable[R]],
        plan: FaultPlan,
        *args: Any,
        invariants: Iterable[InvariantFunction] = (),
        **kwargs: Any,
) -> FaultRunResult:
    token = set_fault_plan(plan)
    case = _case_from_plan(plan)

    try:
        try:
            result, trace = await run_traced_async(
                target,
                func,
                *args,
                **kwargs,
            )

        except TracedExecutionError as exc:
            return build_fault_result(
                case=case,
                plan=plan,
                trace=exc.trace,
                error=exc.cause,
                invariants=invariants,
            )

        return build_fault_result(
            case=case,
            plan=plan,
            trace=trace,
            result=result,
            invariants=invariants,
        )

    finally:
        reset_fault_plan(token)