from agentidem.faults import FaultPhase, build_lost_ack_plans
from agentidem.trace.models import (
    OperationKind,
    OperationStatus,
    Trace,
    TraceOperation,
)


def test_build_lost_ack_plans_only_targets_successful_writes() -> None:
    trace = Trace(
        target="tests.example:run",
        operations=[
            TraceOperation(
                name="get_order",
                kind=OperationKind.READ,
                status=OperationStatus.SUCCESS,
            ),
            TraceOperation(
                name="refund_order",
                kind=OperationKind.WRITE,
                status=OperationStatus.SUCCESS,
            ),
            TraceOperation(
                name="send_email",
                kind=OperationKind.WRITE,
                status=OperationStatus.FAILED,
                error="RuntimeError: email service unavailable",
            ),
        ],
    )

    plans = build_lost_ack_plans(trace)

    assert len(plans) == 1

    plan = plans[0]

    assert plan.scenario == "lost_acknowledgement"
    assert plan.operation_index == 1
    assert plan.operation_name == "refund_order"
    assert plan.phase == FaultPhase.AFTER_OPERATION


def test_build_lost_ack_plans_returns_empty_when_no_successful_writes() -> None:
    trace = Trace(
        target="tests.example:run",
        operations=[
            TraceOperation(
                name="get_order",
                kind=OperationKind.READ,
                status=OperationStatus.SUCCESS,
            ),
        ],
    )

    plans = build_lost_ack_plans(trace)

    assert plans == []