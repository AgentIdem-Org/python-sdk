from agentidem import OperationStatus, Trace, invariant, test_agent, write
from agentidem.faults.injector import InjectedFaultError


def test_test_agent_detects_non_idempotent_write() -> None:
    @write
    def save_order(order_id: str) -> str:
        return f"saved:{order_id}"

    def agent_run() -> str:
        return save_order("ord_42")

    report = test_agent(
        "tests.test_testing_runner:agent_run",
        agent_run,
    )

    assert report.fault_count == 3
    assert report.unsafe_count == 1
    assert report.safe is False

    assert len(report.baseline.operations) == 1
    assert len(report.results) == 3

    scenarios = {
        result.case.scenario
        for result in report.results
    }

    assert scenarios == {
        "lost_acknowledgement",
        "before_operation_failure",
        "duplicate_delivery",
    }

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

    assert lost_ack.safe is True
    assert before_failure.safe is True

    assert duplicate_delivery.safe is False
    assert len(duplicate_delivery.duplicates) == 1
    assert duplicate_delivery.duplicates[0].operation_name == "save_order"
    assert duplicate_delivery.duplicates[0].count == 2


def test_test_agent_detects_duplicate_retry() -> None:
    @write
    def refund_order(order_id: str) -> str:
        return f"refunded:{order_id}"

    def agent_run() -> str:
        try:
            return refund_order("ord_42")
        except InjectedFaultError:
            return refund_order("ord_42")

    report = test_agent(
        "tests.test_testing_runner:agent_run",
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

    # The first write commits, its acknowledgement is lost,
    # and the agent retries the same write.
    assert lost_ack.failed is False
    assert lost_ack.safe is False
    assert len(lost_ack.duplicates) == 1

    lost_ack_duplicate = lost_ack.duplicates[0]

    assert lost_ack_duplicate.operation_name == "refund_order"
    assert lost_ack_duplicate.count == 2

    # The first write never executes, so the retry is the only
    # successful side effect.
    assert before_failure.failed is False
    assert before_failure.safe is True
    assert before_failure.duplicates == []

    # Two complete deliveries each execute the refund once.
    assert duplicate_delivery.failed is False
    assert duplicate_delivery.safe is False
    assert len(duplicate_delivery.duplicates) == 1

    delivery_duplicate = duplicate_delivery.duplicates[0]

    assert delivery_duplicate.operation_name == "refund_order"
    assert delivery_duplicate.count == 2


def test_test_agent_evaluates_invariants() -> None:
    @write
    def send_email(address: str) -> str:
        return f"sent:{address}"

    def agent_run() -> str:
        return send_email("user@example.com")

    @invariant
    def at_most_one_email_write(trace: Trace) -> None:
        writes = [
            operation
            for operation in trace.operations
            if operation.name == "send_email"
               and operation.status == OperationStatus.SUCCESS
        ]

        assert len(writes) <= 1, "Email write executed more than once."

    report = test_agent(
        "tests.test_testing_runner:agent_run",
        agent_run,
        invariants=[
            at_most_one_email_write,
        ],
    )

    assert report.fault_count == 3
    assert report.unsafe_count == 1
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

    assert lost_ack.invariants[0].passed is True
    assert before_failure.invariants[0].passed is True

    assert duplicate_delivery.invariants[0].name == "at_most_one_email_write"
    assert duplicate_delivery.invariants[0].passed is False
    assert (
            duplicate_delivery.invariants[0].message
            == "Email write executed more than once."
    )

    assert duplicate_delivery.safe is False


def test_test_agent_returns_baseline_failure_report() -> None:
    @write
    def failing_write() -> None:
        raise RuntimeError("database unavailable")

    def agent_run() -> None:
        failing_write()

    report = test_agent(
        "tests.test_testing_runner:agent_run",
        agent_run,
    )

    assert report.baseline_succeeded is False
    assert report.safe is False

    # Fault testing never begins because the original execution failed.
    assert report.fault_count == 0
    assert report.unsafe_count == 0
    assert report.results == ()

    assert report.baseline_failure is not None
    assert report.baseline_failure.error_type == "RuntimeError"
    assert report.baseline_failure.message == "database unavailable"

    assert report.baseline_failure.trace is report.baseline
    assert len(report.baseline.operations) == 1

    operation = report.baseline.operations[0]

    assert operation.name == "failing_write"
    assert operation.status == OperationStatus.FAILED