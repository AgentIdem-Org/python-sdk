from agentidem import ObservationStatus, OperationStatus, write
from agentidem.faults.context import get_fault_plan
from agentidem.faults.injector import InjectedFaultError
from agentidem.faults.plan import FaultPhase, FaultPlan
from agentidem.faults.runner import run_fault
from agentidem.detection import FindingSeverity

def test_run_fault_injects_and_cleans_up_plan() -> None:
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

    result = run_fault(
        "tests.test_fault_runner:refund_order",
        refund_order,
        plan,
        "ord_42",
    )

    assert result.failed is True
    assert result.safe is True
    assert result.error is not None
    assert isinstance(result.error, InjectedFaultError)

    assert result.duplicates == []

    assert calls == ["ord_42"]

    assert len(result.trace.operations) == 1

    operation = result.trace.operations[0]

    assert operation.name == "refund_order"
    assert operation.status == OperationStatus.SUCCESS
    assert operation.observation == ObservationStatus.LOST
    assert operation.result == "refunded"

    assert get_fault_plan() is None


def test_run_fault_without_matching_operation_completes_normally() -> None:
    @write
    def refund_order(order_id: str) -> str:
        return f"refunded:{order_id}"

    plan = FaultPlan(
        scenario="lost_acknowledgement",
        operation_index=1,
        operation_name="refund_order",
        phase=FaultPhase.AFTER_OPERATION,
    )

    result = run_fault(
        "tests.test_fault_runner:refund_order",
        refund_order,
        plan,
        "ord_42",
    )

    assert result.failed is False
    assert result.safe is True
    assert result.error is None
    assert result.result == "refunded:ord_42"

    assert result.duplicates == []

    assert len(result.trace.operations) == 1

    operation = result.trace.operations[0]

    assert operation.status == OperationStatus.SUCCESS
    assert operation.observation == ObservationStatus.RECEIVED

    assert get_fault_plan() is None


def test_run_fault_detects_duplicate_writes() -> None:
    @write
    def refund_order(order_id: str) -> str:
        return f"refunded:{order_id}"

    def agent_run() -> str:
        try:
            return refund_order("ord_42")
        except InjectedFaultError:
            return refund_order("ord_42")

    plan = FaultPlan(
        scenario="lost_acknowledgement",
        operation_index=0,
        operation_name="refund_order",
        phase=FaultPhase.AFTER_OPERATION,
    )

    result = run_fault(
        "tests.test_fault_runner:agent_run",
        agent_run,
        plan,
    )

    assert result.failed is False
    assert result.safe is False

    assert len(result.duplicates) == 1

    duplicate = result.duplicates[0]

    assert duplicate.operation_name == "refund_order"
    assert duplicate.count == 2

    assert duplicate.args == {
        "args": ["ord_42"],
        "kwargs": {},
    }

    assert len(duplicate.operations) == 2

    first_operation = duplicate.operations[0]
    second_operation = duplicate.operations[1]

    assert first_operation.status == OperationStatus.SUCCESS
    assert first_operation.observation == ObservationStatus.LOST

    assert second_operation.status == OperationStatus.SUCCESS
    assert second_operation.observation == ObservationStatus.RECEIVED

    assert get_fault_plan() is None

    assert len(result.findings) == 1

    finding = result.findings[0]

    assert finding.code == "duplicate_write"
    assert finding.severity == FindingSeverity.ERROR
    assert finding.message == "Write 'refund_order' executed 2 times."

    assert finding.details["operation_name"] == "refund_order"
    assert finding.details["count"] == 2
    assert len(finding.details["operation_ids"]) == 2