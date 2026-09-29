from agentidem import Trace, invariant, run_traced, write, ObservationStatus, OperationStatus
from agentidem.faults.suite import run_lost_ack_suite
from agentidem.faults.injector import InjectedFaultError
@invariant
def at_most_one_write(trace: Trace) -> None:
    writes = [
        operation
        for operation in trace.operations
        if operation.name == "first_write"
    ]

    assert len(writes) <= 1, "first_write executed more than once."


def test_run_lost_ack_suite_runs_all_successful_writes() -> None:
    calls: list[str] = []

    @write
    def first_write() -> str:
        calls.append("first")
        return "first-ok"

    @write
    def second_write() -> str:
        calls.append("second")
        return "second-ok"

    def agent_run() -> str:
        first_write()
        return second_write()

    _, baseline = run_traced(
        "tests.test_fault_suite:agent_run",
        agent_run,
    )

    calls.clear()

    results = run_lost_ack_suite(
        "tests.test_fault_suite:agent_run",
        agent_run,
        baseline,
        invariants=[
            at_most_one_write,
        ],
    )

    assert len(results) == 2

    assert results[0].plan.operation_name == "first_write"
    assert results[0].failed is True
    assert results[0].safe is True

    assert results[1].plan.operation_name == "second_write"
    assert results[1].failed is True
    assert results[1].safe is True

    assert len(results[0].invariants) == 1
    assert results[0].invariants[0].name == "at_most_one_write"
    assert results[0].invariants[0].passed is True


def test_run_lost_ack_suite_returns_empty_without_writes() -> None:
    def agent_run() -> str:
        return "done"

    _, baseline = run_traced(
        "tests.test_fault_suite:agent_run",
        agent_run,
    )

    results = run_lost_ack_suite(
        "tests.test_fault_suite:agent_run",
        agent_run,
        baseline,
        invariants=[
            at_most_one_write,
        ],
    )

    assert results == []

def test_run_lost_ack_suite_reports_unsafe_invariant() -> None:
    @write
    def refund_order() -> str:
        return "refunded"

    def agent_run() -> str:
        refund_order()
        refund_order()

        return "done"

    @invariant
    def only_one_refund(trace: Trace) -> None:
        refunds = [
            operation
            for operation in trace.operations
            if operation.name == "refund_order"
        ]

        assert len(refunds) <= 1, "Refund executed more than once."

    _, baseline = run_traced(
        "tests.test_fault_suite:agent_run",
        agent_run,
    )

    results = run_lost_ack_suite(
        "tests.test_fault_suite:agent_run",
        agent_run,
        baseline,
        invariants=[
            only_one_refund,
        ],
    )

    assert len(results) == 2

    first_result = results[0]
    second_result = results[1]

    assert first_result.plan.operation_index == 0
    assert first_result.safe is True
    assert first_result.invariants[0].passed is True

    assert second_result.plan.operation_index == 1
    assert second_result.safe is False

    invariant_result = second_result.invariants[0]

    assert invariant_result.name == "only_one_refund"
    assert invariant_result.passed is False
    assert invariant_result.message == "Refund executed more than once."

def test_lost_ack_retry_causes_duplicate_write() -> None:
    @write
    def refund_order() -> str:
        return "refunded"

    def agent_run() -> str:
        try:
            return refund_order()
        except InjectedFaultError:
            return refund_order()

    @invariant
    def only_one_refund(trace: Trace) -> None:
        refunds = [
            operation
            for operation in trace.operations
            if operation.name == "refund_order"
        ]

        assert len(refunds) <= 1, "Refund executed more than once."

    _, baseline = run_traced(
        "tests.test_fault_suite:agent_run",
        agent_run,
    )

    results = run_lost_ack_suite(
        "tests.test_fault_suite:agent_run",
        agent_run,
        baseline,
        invariants=[
            only_one_refund,
        ],
    )

    assert len(results) == 1

    result = results[0]

    assert result.failed is False
    assert result.safe is False

    assert len(result.trace.operations) == 2

    first_operation = result.trace.operations[0]
    second_operation = result.trace.operations[1]

    assert first_operation.name == "refund_order"
    assert first_operation.status == OperationStatus.SUCCESS
    assert first_operation.observation == ObservationStatus.LOST

    assert second_operation.name == "refund_order"
    assert second_operation.status == OperationStatus.SUCCESS
    assert second_operation.observation == ObservationStatus.RECEIVED

    assert len(result.invariants) == 1

    invariant_result = result.invariants[0]

    assert invariant_result.name == "only_one_refund"
    assert invariant_result.passed is False
    assert invariant_result.message == "Refund executed more than once."