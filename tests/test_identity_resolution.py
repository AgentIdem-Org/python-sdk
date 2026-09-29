import pytest

from agentidem import test_agent, test_agent_async, write
from agentidem.errors import IdentityResolutionError


def test_sync_identity_resolution_failure_is_structured() -> None:
    @write(identity=lambda order_id: 1 / 0)
    def refund_order(order_id: str) -> str:
        return f"refunded:{order_id}"

    def agent_run() -> str:
        return refund_order("ord_42")

    report = test_agent(
        "tests.test_identity_resolution:agent_run",
        agent_run,
    )

    assert report.baseline_succeeded is False
    assert report.safe is False
    assert report.fault_count == 0

    assert report.baseline_failure is not None
    assert report.baseline_failure.error_type == "IdentityResolutionError"

    assert (
            report.baseline_failure.message
            == (
                "Failed to resolve identity for write 'refund_order': "
                "ZeroDivisionError: division by zero"
            )
    )

    # The write never actually started, so no operation should be recorded.
    assert report.baseline.operations == []


@pytest.mark.asyncio
async def test_async_identity_resolution_failure_is_structured() -> None:
    @write(identity=lambda order_id: 1 / 0)
    async def refund_order(order_id: str) -> str:
        return f"refunded:{order_id}"

    async def agent_run() -> str:
        return await refund_order("ord_42")

    report = await test_agent_async(
        "tests.test_identity_resolution:agent_run",
        agent_run,
    )

    assert report.baseline_succeeded is False
    assert report.safe is False
    assert report.fault_count == 0

    assert report.baseline_failure is not None
    assert report.baseline_failure.error_type == "IdentityResolutionError"

    assert (
            report.baseline_failure.message
            == (
                "Failed to resolve identity for write 'refund_order': "
                "ZeroDivisionError: division by zero"
            )
    )

    assert report.baseline.operations == []


def test_identity_resolution_error_preserves_original_cause() -> None:
    error = IdentityResolutionError(
        "refund_order",
        cause=ValueError("invalid identity"),
    )

    assert error.operation_name == "refund_order"
    assert isinstance(error.cause, ValueError)
    assert str(error.cause) == "invalid identity"

    assert str(error) == (
        "Failed to resolve identity for write 'refund_order': "
        "ValueError: invalid identity"
    )