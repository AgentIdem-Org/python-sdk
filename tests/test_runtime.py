import pytest

from agentidem import OperationKind, OperationStatus, read, run_traced, write
from agentidem.errors import TracedExecutionError

@read
def get_order(order_id: str) -> dict[str, object]:
    return {
        "id": order_id,
        "refunded": False,
    }

@write
def refund_order(order_id: str, amount: float) -> dict[str, object]:
    return {
        "order_id": order_id,
        "amount": amount,
        "status": "refunded",
    }

def agent_run() -> dict[str, object]:
    order = get_order("ord_42")

    if not order["refunded"]:
        return refund_order("ord_42", 50.0)

    return order

def test_run_traced_records_operations() -> None:
    result, trace = run_traced(
        "tests.test_runtime:agent_run",
        agent_run,
    )

    assert result["status"] == "refunded"

    assert trace.target == "tests.test_runtime:agent_run"
    assert trace.completed_at is not None
    assert len(trace.operations) == 2

    read_operation = trace.operations[0]
    write_operation = trace.operations[1]

    assert read_operation.name == "get_order"
    assert read_operation.kind == OperationKind.READ
    assert read_operation.status == OperationStatus.SUCCESS
    assert read_operation.result == {
        "id": "ord_42",
        "refunded": False,
    }
    assert read_operation.completed_at is not None

    assert write_operation.name == "refund_order"
    assert write_operation.kind == OperationKind.WRITE
    assert write_operation.status == OperationStatus.SUCCESS
    assert write_operation.result == {
        "order_id": "ord_42",
        "amount": 50.0,
        "status": "refunded",
    }
    assert write_operation.completed_at is not None

def test_failed_operation_preserves_trace() -> None:
    @write
    def failing_write() -> None:
        raise RuntimeError("database unavailable")

    def failing_agent() -> None:
        failing_write()

    with pytest.raises(TracedExecutionError) as exc_info:
        run_traced(
            "tests.test_runtime:failing_agent",
            failing_agent,
        )

    error = exc_info.value

    assert str(error) == (
        "Traced execution failed for tests.test_runtime:failing_agent"
    )

    assert isinstance(error.cause, RuntimeError)
    assert str(error.cause) == "database unavailable"

    trace = error.trace

    assert trace.target == "tests.test_runtime:failing_agent"
    assert trace.completed_at is not None
    assert len(trace.operations) == 1

    operation = trace.operations[0]

    assert operation.name == "failing_write"
    assert operation.kind == OperationKind.WRITE
    assert operation.status == OperationStatus.FAILED
    assert operation.error == "RuntimeError: database unavailable"
    assert operation.completed_at is not None