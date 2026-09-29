import pytest

from agentidem import run_traced, run_traced_async, write
from agentidem.faults.suite import (
    run_duplicate_delivery_suite,
    run_duplicate_delivery_suite_async,
)


def test_duplicate_delivery_detects_duplicate_write() -> None:
    @write(identity=lambda order_id: order_id)
    def refund_order(order_id: str) -> str:
        return f"refunded:{order_id}"

    def agent_run() -> str:
        return refund_order("ord_42")

    results = run_duplicate_delivery_suite(
        "tests.test_duplicate_delivery:agent_run",
        agent_run,
    )

    assert len(results) == 1

    result = results[0]

    assert result.case.scenario == "duplicate_delivery"
    assert result.plan is None

    assert result.failed is False
    assert result.safe is False

    assert len(result.trace.operations) == 2
    assert len(result.duplicates) == 1
    assert len(result.findings) == 1

    duplicate = result.duplicates[0]

    assert duplicate.operation_name == "refund_order"
    assert duplicate.count == 2

    finding = result.findings[0]

    assert finding.code == "duplicate_write"
    assert finding.severity.value == "error"


def test_duplicate_delivery_is_safe_without_writes() -> None:
    def agent_run() -> str:
        return "done"

    results = run_duplicate_delivery_suite(
        "tests.test_duplicate_delivery:agent_run",
        agent_run,
    )

    assert len(results) == 1

    result = results[0]

    assert result.case.scenario == "duplicate_delivery"
    assert result.plan is None

    assert result.failed is False
    assert result.safe is True

    assert result.duplicates == []
    assert result.findings == []
    assert result.trace.operations == []


@pytest.mark.asyncio
async def test_async_duplicate_delivery_detects_duplicate_write() -> None:
    @write(identity=lambda order_id: order_id)
    async def refund_order(order_id: str) -> str:
        return f"refunded:{order_id}"

    async def agent_run() -> str:
        return await refund_order("ord_42")

    results = await run_duplicate_delivery_suite_async(
        "tests.test_duplicate_delivery:agent_run",
        agent_run,
    )

    assert len(results) == 1

    result = results[0]

    assert result.case.scenario == "duplicate_delivery"
    assert result.plan is None

    assert result.failed is False
    assert result.safe is False

    assert len(result.trace.operations) == 2
    assert len(result.duplicates) == 1
    assert len(result.findings) == 1

    duplicate = result.duplicates[0]

    assert duplicate.operation_name == "refund_order"
    assert duplicate.count == 2