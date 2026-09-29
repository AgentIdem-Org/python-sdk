import pytest

from agentidem import OperationStatus, test_agent_async, write
from agentidem.faults.injector import InjectedFaultError


@pytest.mark.asyncio
async def test_test_agent_async_detects_duplicate_retry() -> None:
    @write
    async def refund_order(order_id: str) -> str:
        return f"refunded:{order_id}"

    async def agent_run() -> str:
        try:
            return await refund_order("ord_42")
        except InjectedFaultError:
            return await refund_order("ord_42")

    report = await test_agent_async(
        "tests.test_async_testing_runner:agent_run",
        agent_run,
    )

    assert report.fault_count == 3
    assert report.unsafe_count == 2
    assert report.safe is False

    lost_ack = next(
        result
        for result in report.results
        if result.case.scenario == "lost_acknowledgement"
    )

    before_failure = next(
        result
        for result in report.results
        if result.case.scenario == "before_operation_failure"
    )

    duplicate_delivery = next(
        result
        for result in report.results
        if result.case.scenario == "duplicate_delivery"
    )

    assert lost_ack.failed is False
    assert lost_ack.safe is False
    assert len(lost_ack.duplicates) == 1

    lost_ack_duplicate = lost_ack.duplicates[0]

    assert lost_ack_duplicate.operation_name == "refund_order"
    assert lost_ack_duplicate.count == 2

    assert before_failure.failed is False
    assert before_failure.safe is True
    assert before_failure.duplicates == []

    assert duplicate_delivery.failed is False
    assert duplicate_delivery.safe is False
    assert len(duplicate_delivery.duplicates) == 1

    duplicate_delivery_duplicate = duplicate_delivery.duplicates[0]

    assert duplicate_delivery_duplicate.operation_name == "refund_order"
    assert duplicate_delivery_duplicate.count == 2


@pytest.mark.asyncio
async def test_test_agent_async_returns_baseline_failure_report() -> None:
    @write
    async def failing_write() -> None:
        raise RuntimeError("async database unavailable")

    async def agent_run() -> None:
        await failing_write()

    report = await test_agent_async(
        "tests.test_async_testing_runner:agent_run",
        agent_run,
    )

    assert report.baseline_succeeded is False
    assert report.safe is False

    assert report.fault_count == 0
    assert report.unsafe_count == 0
    assert report.results == ()

    assert report.baseline_failure is not None
    assert report.baseline_failure.error_type == "RuntimeError"
    assert report.baseline_failure.message == "async database unavailable"

    assert report.baseline_failure.trace is report.baseline
    assert len(report.baseline.operations) == 1

    operation = report.baseline.operations[0]

    assert operation.name == "failing_write"
    assert operation.status == OperationStatus.FAILED