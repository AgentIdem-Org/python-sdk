from __future__ import annotations

from contextvars import ContextVar, Token

from agentidem.faults.plan import FaultPlan


_active_fault_plan: ContextVar[FaultPlan | None] = ContextVar(
    "agentidem_active_fault_plan",
    default=None,
)

_operation_index: ContextVar[int] = ContextVar(
    "agentidem_operation_index",
    default=0,
)


def get_fault_plan() -> FaultPlan | None:
    return _active_fault_plan.get()


def set_fault_plan(plan: FaultPlan) -> Token:
    return _active_fault_plan.set(plan)


def reset_fault_plan(token: Token) -> None:
    _active_fault_plan.reset(token)


def get_operation_index() -> int:
    return _operation_index.get()


def advance_operation_index() -> int:
    current = _operation_index.get()
    _operation_index.set(current + 1)
    return current


def reset_operation_index() -> None:
    _operation_index.set(0)