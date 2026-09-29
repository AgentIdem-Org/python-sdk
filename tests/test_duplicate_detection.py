from agentidem.detection import detect_duplicate_writes
from agentidem.trace.models import (
    OperationKind,
    OperationStatus,
    Trace,
    TraceOperation,
)

from pydantic import BaseModel


def test_detect_duplicate_writes_finds_matching_successful_writes() -> None:
    trace = Trace(
        target="tests.example:run",
        operations=[
            TraceOperation(
                name="refund_order",
                kind=OperationKind.WRITE,
                args={
                    "args": ["ord_42", 50.0],
                    "kwargs": {},
                },
                status=OperationStatus.SUCCESS,
            ),
            TraceOperation(
                name="refund_order",
                kind=OperationKind.WRITE,
                args={
                    "args": ["ord_42", 50.0],
                    "kwargs": {},
                },
                status=OperationStatus.SUCCESS,
            ),
        ],
    )

    duplicates = detect_duplicate_writes(trace)

    assert len(duplicates) == 1

    duplicate = duplicates[0]

    assert duplicate.operation_name == "refund_order"
    assert duplicate.count == 2
    assert duplicate.args == {
        "args": ["ord_42", 50.0],
        "kwargs": {},
    }
    assert len(duplicate.operations) == 2


def test_detect_duplicate_writes_ignores_different_arguments() -> None:
    trace = Trace(
        target="tests.example:run",
        operations=[
            TraceOperation(
                name="refund_order",
                kind=OperationKind.WRITE,
                args={
                    "args": ["ord_42", 50.0],
                    "kwargs": {},
                },
                status=OperationStatus.SUCCESS,
            ),
            TraceOperation(
                name="refund_order",
                kind=OperationKind.WRITE,
                args={
                    "args": ["ord_43", 50.0],
                    "kwargs": {},
                },
                status=OperationStatus.SUCCESS,
            ),
        ],
    )

    duplicates = detect_duplicate_writes(trace)

    assert duplicates == []


def test_detect_duplicate_writes_ignores_reads() -> None:
    trace = Trace(
        target="tests.example:run",
        operations=[
            TraceOperation(
                name="get_order",
                kind=OperationKind.READ,
                args={
                    "args": ["ord_42"],
                    "kwargs": {},
                },
                status=OperationStatus.SUCCESS,
            ),
            TraceOperation(
                name="get_order",
                kind=OperationKind.READ,
                args={
                    "args": ["ord_42"],
                    "kwargs": {},
                },
                status=OperationStatus.SUCCESS,
            ),
        ],
    )

    duplicates = detect_duplicate_writes(trace)

    assert duplicates == []


def test_detect_duplicate_writes_ignores_failed_writes() -> None:
    trace = Trace(
        target="tests.example:run",
        operations=[
            TraceOperation(
                name="refund_order",
                kind=OperationKind.WRITE,
                args={
                    "args": ["ord_42", 50.0],
                    "kwargs": {},
                },
                status=OperationStatus.SUCCESS,
            ),
            TraceOperation(
                name="refund_order",
                kind=OperationKind.WRITE,
                args={
                    "args": ["ord_42", 50.0],
                    "kwargs": {},
                },
                status=OperationStatus.FAILED,
                error="RuntimeError: refund failed",
            ),
        ],
    )

    duplicates = detect_duplicate_writes(trace)

    assert duplicates == []

from agentidem import run_traced, write


def test_custom_identity_detects_duplicate_writes_with_different_args() -> None:
    @write(identity=lambda order_id, amount: order_id)
    def refund_order(order_id: str, amount: float) -> str:
        return f"refunded:{order_id}:{amount}"

    def agent_run() -> None:
        refund_order("ord_42", 50.0)
        refund_order("ord_42", 75.0)

    _, trace = run_traced(
        "tests.test_duplicate_detection:agent_run",
        agent_run,
    )

    duplicates = detect_duplicate_writes(trace)

    assert len(duplicates) == 1

    duplicate = duplicates[0]

    assert duplicate.operation_name == "refund_order"
    assert duplicate.count == 2

    assert duplicate.operations[0].identity == "ord_42"
    assert duplicate.operations[1].identity == "ord_42"

def test_custom_identity_keeps_different_logical_writes_separate() -> None:
    @write(identity=lambda order_id, amount: order_id)
    def refund_order(order_id: str, amount: float) -> str:
        return f"refunded:{order_id}:{amount}"

    def agent_run() -> None:
        refund_order("ord_42", 50.0)
        refund_order("ord_43", 50.0)

    _, trace = run_traced(
        "tests.test_duplicate_detection:agent_run",
        agent_run,
    )

    duplicates = detect_duplicate_writes(trace)

    assert duplicates == []

def test_custom_identity_supports_pydantic_models() -> None:
    class RefundIdentity(BaseModel):
        order_id: str
    @write(identity=lambda order_id, amount: RefundIdentity(order_id=order_id))
    def refund_order(order_id: str, amount: float) -> str:
        return f"refunded:{order_id}:{amount}"

    def agent_run() -> None:
        refund_order("ord_42", 50.0)
        refund_order("ord_42", 75.0)
    _, trace = run_traced(
        "tests.test_duplicate_detection:agent_run",
        agent_run,
    )
    duplicates = detect_duplicate_writes(trace)
    assert len(duplicates) == 1
    assert duplicates[0].operation_name == "refund_order"
    assert duplicates[0].count == 2