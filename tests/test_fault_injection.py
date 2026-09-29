import pytest

from agentidem import ObservationStatus, OperationStatus, run_traced, write
from agentidem.errors import TracedExecutionError
from agentidem.faults.context import reset_fault_plan, set_fault_plan
from agentidem.faults.injector import InjectedFaultError
from agentidem.faults.plan import FaultPhase, FaultPlan


def test_lost_ack_preserves_successful_write() -> None:
    calls: list[str] = []

    @write
    def refund_order(order_id: str) -> str:
        calls.append(order_id)
        return "refunded"

    plan = FaultPlan(
        scenario="lost_acknowledgement",
        operation_index=0,
        operation_name="refund_order",
        phase=FaultPhase.AFTER_OPERATION,
        message="Acknowledgement lost after refund.",
    )

    token = set_fault_plan(plan)

    try:
        with pytest.raises(TracedExecutionError) as exc_info:
            run_traced(
                "tests.test_fault_injection:refund_order",
                refund_order,
                "ord_42",
            )
    finally:
        reset_fault_plan(token)

    error = exc_info.value

    assert isinstance(error.cause, InjectedFaultError)

    assert calls == ["ord_42"]

    assert len(error.trace.operations) == 1

    operation = error.trace.operations[0]

    assert operation.name == "refund_order"
    assert operation.status == OperationStatus.SUCCESS
    assert operation.observation == ObservationStatus.LOST
    assert operation.result == "refunded"
    assert operation.error is None