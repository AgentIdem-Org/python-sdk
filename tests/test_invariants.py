from agentidem import Trace, TraceOperation, invariant
from agentidem.invariants import evaluate_invariant, evaluate_invariants
from agentidem.trace.models import OperationKind, OperationStatus


@invariant
def one_refund_per_order(trace: Trace) -> None:
    refunds = [
        operation
        for operation in trace.operations
        if operation.name == "refund_order"
    ]

    assert len(refunds) <= 1, "Order was refunded more than once."


def test_invariant_passes() -> None:
    trace = Trace(
        target="tests.example:run",
        operations=[
            TraceOperation(
                name="refund_order",
                kind=OperationKind.WRITE,
                status=OperationStatus.SUCCESS,
            ),
        ],
    )

    result = evaluate_invariant(
        one_refund_per_order,
        trace,
    )

    assert result.name == "one_refund_per_order"
    assert result.passed is True
    assert result.message is None


def test_invariant_fails() -> None:
    trace = Trace(
        target="tests.example:run",
        operations=[
            TraceOperation(
                name="refund_order",
                kind=OperationKind.WRITE,
                status=OperationStatus.SUCCESS,
            ),
            TraceOperation(
                name="refund_order",
                kind=OperationKind.WRITE,
                status=OperationStatus.SUCCESS,
            ),
        ],
    )

    result = evaluate_invariant(
        one_refund_per_order,
        trace,
    )

    assert result.name == "one_refund_per_order"
    assert result.passed is False
    assert result.message == "Order was refunded more than once."


def test_evaluate_multiple_invariants() -> None:
    @invariant
    def has_write(trace: Trace) -> None:
        assert any(
            operation.kind == OperationKind.WRITE
            for operation in trace.operations
        ), "Trace contains no writes."

    trace = Trace(
        target="tests.example:run",
        operations=[
            TraceOperation(
                name="refund_order",
                kind=OperationKind.WRITE,
                status=OperationStatus.SUCCESS,
            ),
        ],
    )

    results = evaluate_invariants(
        [
            one_refund_per_order,
            has_write,
        ],
        trace,
    )

    assert len(results) == 2
    assert all(result.passed for result in results)