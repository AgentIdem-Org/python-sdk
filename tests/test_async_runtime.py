import pytest

from agentidem import (
    OperationKind,
    OperationStatus,
    read,
    run_traced_async,
    write,
)
from agentidem.errors import TracedExecutionError


@read
async def get_order(order_id: str) -> dict[str, object]:
    return {
        "id": order_id,
        "refunded": False,
    }


@write
async def refund_order(
        order_id: str,
        amount: float,
) -> dict[str, object]:
    return {
        "order_id": order_id,
        "amount": amount,
        "status": "refunded",
    }


async def agent_run() -> dict[str, object]:
    order = await get_order("ord_42")

    if not order["refunded"]:
        return await refund_order(
            "ord_42",
            50.0,
        )

    return order


@pytest.mark.asyncio
async def test_run_traced_async_records_operations() -> None:
    result, trace = await run_traced_async(
        "tests.test_async_runtime:agent_run",
        agent_run,
    )

    assert result["status"] == "refunded"

    assert trace.target == "tests.test_async_runtime:agent_run"
    assert trace.completed_at is not None
    assert len(trace.operations) == 2

    read_operation = trace.operations[0]
    write_operation = trace.operations[1]

    assert read_operation.name == "get_order"
    assert read_operation.kind == OperationKind.READ
    assert read_operation.status == OperationStatus.SUCCESS

    assert write_operation.name == "refund_order"
    assert write_operation.kind == OperationKind.WRITE
    assert write_operation.status == OperationStatus.SUCCESS


@pytest.mark.asyncio
async def test_failed_async_operation_preserves_trace() -> None:
    @write
    async def failing_write() -> None:
        raise RuntimeError("database unavailable")

    async def failing_agent() -> None:
        await failing_write()

    with pytest.raises(TracedExecutionError) as exc_info:
        await run_traced_async(
            "tests.test_async_runtime:failing_agent",
            failing_agent,
        )

    error = exc_info.value

    assert isinstance(error.cause, RuntimeError)
    assert str(error.cause) == "database unavailable"

    assert len(error.trace.operations) == 1

    operation = error.trace.operations[0]

    assert operation.name == "failing_write"
    assert operation.kind == OperationKind.WRITE
    assert operation.status == OperationStatus.FAILED