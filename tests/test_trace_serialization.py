from pathlib import Path

from agentidem.trace.models import (
    ObservationStatus,
    OperationKind,
    OperationStatus,
    Trace,
    TraceOperation,
)
from agentidem.trace.serialization import load_trace, save_trace


def test_trace_round_trip_preserves_operation_data(
        tmp_path: Path,
) -> None:
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
                identity="ord_42",
                result={
                    "status": "refunded",
                },
                status=OperationStatus.SUCCESS,
                observation=ObservationStatus.LOST,
            ),
        ],
    )

    path = tmp_path / "trace.json"

    save_trace(trace, path)

    loaded = load_trace(path)

    assert loaded.target == trace.target
    assert loaded.id == trace.id
    assert len(loaded.operations) == 1

    operation = loaded.operations[0]

    assert operation.name == "refund_order"
    assert operation.kind == OperationKind.WRITE
    assert operation.status == OperationStatus.SUCCESS
    assert operation.observation == ObservationStatus.LOST
    assert operation.identity == "ord_42"

    assert operation.args == {
        "args": ["ord_42", 50.0],
        "kwargs": {},
    }

    assert operation.result == {
        "status": "refunded",
    }