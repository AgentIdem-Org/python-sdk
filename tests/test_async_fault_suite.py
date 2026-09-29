import pytest

from agentidem import ObservationStatus, OperationStatus, run_traced_async, write
from agentidem.faults.injector import InjectedFaultError
from agentidem.faults.suite import run_lost_ack_suite_async


@pytest.mark.asyncio
async def test_async_lost_ack_retry_causes_duplicate_write() -> None:
    @write
    async def refund_order(order_id: str) -> str:
        return f"refunded:{order_id}"

    async def agent_run() -> str:
        try:
            return await refund_order("ord_42")
        except InjectedFaultError:
            return await refund_order("ord_42")

    _, baseline = await run_traced_async(
        "tests.test_async_fault_suite:agent_run",
        agent_run,
    )

    results = await run_lost_ack_suite_async(
        "tests.test_async_fault_suite:agent_run",
        agent_run,
        baseline,
    )

    assert len(results) == 1

    result = results[0]

    assert result.failed is False
    assert result.safe is False

    assert len(result.duplicates) == 1

    duplicate = result.duplicates[0]

    assert duplicate.operation_name == "refund_order"
    assert duplicate.count == 2

    first_operation = duplicate.operations[0]
    second_operation = duplicate.operations[1]

    assert first_operation.status == OperationStatus.SUCCESS
    assert first_operation.observation == ObservationStatus.LOST

    assert second_operation.status == OperationStatus.SUCCESS
    assert second_operation.observation == ObservationStatus.RECEIVED