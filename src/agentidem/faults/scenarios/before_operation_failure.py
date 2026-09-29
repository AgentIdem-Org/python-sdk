from __future__ import annotations

from agentidem.faults.plan import FaultPhase, FaultPlan
from agentidem.trace.models import OperationKind, OperationStatus, Trace


def build_before_operation_failure_plans(
        trace: Trace,
) -> list[FaultPlan]:
    plans: list[FaultPlan] = []

    for index, operation in enumerate(trace.operations):
        if operation.kind != OperationKind.WRITE:
            continue

        if operation.status != OperationStatus.SUCCESS:
            continue

        plans.append(
            FaultPlan(
                scenario="before_operation_failure",
                operation_index=index,
                operation_name=operation.name,
                phase=FaultPhase.BEFORE_OPERATION,
                message=(
                    f"Failure injected before write: "
                    f"{operation.name}"
                ),
            )
        )

    return plans