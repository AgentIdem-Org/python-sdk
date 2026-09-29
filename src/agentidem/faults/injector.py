from __future__ import annotations

from agentidem.faults.context import get_fault_plan
from agentidem.faults.plan import FaultPhase


class InjectedFaultError(RuntimeError):
    """Raised when AgentIdem intentionally injects a fault."""


def should_inject(
        *,
        operation_index: int,
        operation_name: str,
        phase: FaultPhase,
) -> bool:
    plan = get_fault_plan()

    if plan is None:
        return False

    return (
            plan.operation_index == operation_index
            and plan.operation_name == operation_name
            and plan.phase == phase
    )


def inject_if_planned(
        *,
        operation_index: int,
        operation_name: str,
        phase: FaultPhase,
) -> None:
    plan = get_fault_plan()

    if plan is None:
        return

    if not should_inject(
            operation_index=operation_index,
            operation_name=operation_name,
            phase=phase,
    ):
        return

    raise InjectedFaultError(
        plan.message
        or (
            f"Injected fault '{plan.scenario}' at "
            f"{operation_name} ({phase.value})"
        )
    )