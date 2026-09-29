import json
from pathlib import Path

from agentidem import (
    OperationStatus,
    Trace,
    invariant,
    test_agent,
    write,
)
from agentidem.faults.injector import InjectedFaultError
from agentidem.testing.serialization import report_to_dict, save_report


def test_report_to_dict_contains_fault_details() -> None:
    @write
    def refund_order(order_id: str) -> str:
        return f"refunded:{order_id}"

    def agent_run() -> str:
        try:
            return refund_order("ord_42")
        except InjectedFaultError:
            return refund_order("ord_42")

    @invariant
    def only_one_refund(trace: Trace) -> None:
        refunds = [
            operation
            for operation in trace.operations
            if operation.name == "refund_order"
               and operation.status == OperationStatus.SUCCESS
        ]

        assert len(refunds) <= 1, "Refund executed more than once."

    report = test_agent(
        "tests.test_report_serialization:agent_run",
        agent_run,
        invariants=[
            only_one_refund,
        ],
    )

    data = report_to_dict(report)

    assert data["safe"] is False
    assert data["fault_count"] == 3
    assert data["unsafe_count"] == 2

    assert data["baseline"]["target"] == (
        "tests.test_report_serialization:agent_run"
    )

    assert len(data["results"]) == 3

    lost_ack = next(
        result
        for result in data["results"]
        if result["scenario"] == "lost_acknowledgement"
    )

    assert lost_ack["operation_index"] == 0
    assert lost_ack["operation_name"] == "refund_order"
    assert lost_ack["phase"] == "after_operation"

    assert lost_ack["safe"] is False
    assert lost_ack["failed"] is False
    assert lost_ack["error"] is None

    assert len(lost_ack["invariants"]) == 1
    assert lost_ack["invariants"][0] == {
        "name": "only_one_refund",
        "passed": False,
        "message": "Refund executed more than once.",
    }

    assert len(lost_ack["duplicates"]) == 1

    duplicate = lost_ack["duplicates"][0]

    assert duplicate["operation_name"] == "refund_order"
    assert duplicate["count"] == 2

    assert duplicate["args"] == {
        "args": ["ord_42"],
        "kwargs": {},
    }

    assert len(duplicate["operation_ids"]) == 2

    before_failure = next(
        result
        for result in data["results"]
        if result["scenario"] == "before_operation_failure"
    )

    assert before_failure["safe"] is True
    assert before_failure["duplicates"] == []
    assert before_failure["findings"] == []

    duplicate_delivery = next(
        result
        for result in data["results"]
        if result["scenario"] == "duplicate_delivery"
    )

    assert duplicate_delivery["safe"] is False
    assert len(duplicate_delivery["duplicates"]) == 1


def test_save_report_writes_valid_json(
        tmp_path: Path,
) -> None:
    @write
    def save_order(order_id: str) -> str:
        return f"saved:{order_id}"

    def agent_run() -> str:
        return save_order("ord_42")

    report = test_agent(
        "tests.test_report_serialization:agent_run",
        agent_run,
    )

    path = tmp_path / "report.json"

    save_report(report, path)

    assert path.exists()

    data = json.loads(
        path.read_text(encoding="utf-8")
    )

    assert data["safe"] is False
    assert data["fault_count"] == 3
    assert data["unsafe_count"] == 1
    assert data["schema_version"] == "1"
    assert data["baseline_succeeded"] is True
    assert data["baseline_failure"] is None

    assert data["baseline"]["target"] == (
        "tests.test_report_serialization:agent_run"
    )

    assert len(data["results"]) == 3

    lost_ack = next(
        result
        for result in data["results"]
        if result["scenario"] == "lost_acknowledgement"
    )

    assert lost_ack["safe"] is True
    assert lost_ack["findings"] == []
    assert lost_ack["duplicates"] == []

    before_failure = next(
        result
        for result in data["results"]
        if result["scenario"] == "before_operation_failure"
    )

    assert before_failure["safe"] is True
    assert before_failure["findings"] == []
    assert before_failure["duplicates"] == []

    duplicate_delivery = next(
        result
        for result in data["results"]
        if result["scenario"] == "duplicate_delivery"
    )

    assert duplicate_delivery["safe"] is False
    assert len(duplicate_delivery["duplicates"]) == 1
    assert len(duplicate_delivery["findings"]) == 1


def test_report_serializes_duplicate_delivery_case() -> None:
    @write(identity=lambda order_id: order_id)
    def refund_order(order_id: str) -> str:
        return f"refunded:{order_id}"

    def agent_run() -> str:
        return refund_order("ord_42")

    report = test_agent(
        "tests.test_report_serialization:agent_run",
        agent_run,
    )

    data = report_to_dict(report)

    duplicate_delivery = next(
        result
        for result in data["results"]
        if result["scenario"] == "duplicate_delivery"
    )

    assert duplicate_delivery["operation_index"] is None
    assert duplicate_delivery["operation_name"] is None
    assert duplicate_delivery["phase"] is None

    assert duplicate_delivery["safe"] is False
    assert duplicate_delivery["failed"] is False
    assert duplicate_delivery["error"] is None

    assert len(duplicate_delivery["duplicates"]) == 1
    assert len(duplicate_delivery["findings"]) == 1

    duplicate = duplicate_delivery["duplicates"][0]

    assert duplicate["operation_name"] == "refund_order"
    assert duplicate["count"] == 2

    finding = duplicate_delivery["findings"][0]

    assert finding["code"] == "duplicate_write"
    assert finding["severity"] == "error"