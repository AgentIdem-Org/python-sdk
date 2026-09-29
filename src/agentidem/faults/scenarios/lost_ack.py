from __future__ import annotations

from agentidem.faults.plan import FaultPhase, FaultPlan
from agentidem.trace.models import OperationKind, OperationStatus, Trace


def build_lost_ack_plans(trace: Trace) -> list[FaultPlan]:
    plans: list[FaultPlan] = []

    for index, operation in enumerate(trace.operations):
        if operation.kind != OperationKind.WRITE:
            continue

        if operation.status != OperationStatus.SUCCESS:
            continue

        plans.append(
            FaultPlan(
                scenario="lost_acknowledgement",
                operation_index=index,
                operation_name=operation.name,
                phase=FaultPhase.AFTER_OPERATION,
                message=(
                    f"Acknowledgement lost after successful write: "
                    f"{operation.name}"
                ),
            )
        )

    return plans