import pytest

from agentidem import (
    ObservationStatus,
    OperationStatus,
    run_traced,
    run_traced_async,
    write,
)
from agentidem.faults.scenarios import build_before_operation_failure_plans
from agentidem.faults.suite import (
    run_before_operation_failure_suite,
    run_before_operation_failure_suite_async,
)


def test_before_operation_failure_does_not_execute_write() -> None:
    calls: list[str] = []

    @write
    def refund_order(order_id: str) -> str:
        calls.append(order_id)
        return f"refunded:{order_id}"

    _, baseline = run_traced(
        "tests.test_before_operation_failure:refund_order",
        refund_order,
        "ord_42",
    )

    plans = build_before_operation_failure_plans(baseline)

    assert len(plans) == 1

    calls.clear()

    results = run_before_operation_failure_suite(
        "tests.test_before_operation_failure:refund_order",
        refund_order,
        baseline,
        "ord_42",
    )

    assert len(results) == 1

    result = results[0]

    assert result.failed is True
    assert result.safe is True

    assert calls == []

    assert len(result.trace.operations) == 1

    operation = result.trace.operations[0]

    assert operation.name == "refund_order"
    assert operation.status == OperationStatus.FAILED
    assert operation.observation == ObservationStatus.FAILED
    assert operation.result is None

    assert result.duplicates == []
    assert result.findings == []


@pytest.mark.asyncio
async def test_async_before_operation_failure_does_not_execute_write() -> None:
    calls: list[str] = []

    @write
    async def refund_order(order_id: str) -> str:
        calls.append(order_id)
        return f"refunded:{order_id}"

    _, baseline = await run_traced_async(
        "tests.test_before_operation_failure:refund_order",
        refund_order,
        "ord_42",
    )

    calls.clear()

    results = await run_before_operation_failure_suite_async(
        "tests.test_before_operation_failure:refund_order",
        refund_order,
        baseline,
        "ord_42",
    )

    assert len(results) == 1

    result = results[0]

    assert result.failed is True
    assert result.safe is True

    assert calls == []

    assert len(result.trace.operations) == 1

    operation = result.trace.operations[0]

    assert operation.name == "refund_order"
    assert operation.status == OperationStatus.FAILED
    assert operation.observation == ObservationStatus.FAILED
    assert operation.result is None

    assert result.duplicates == []
    assert result.findings == []