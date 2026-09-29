from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agentidem.detection.models import Finding, FindingSeverity
from agentidem.detection.normalization import canonicalize_args, normalize_value
from agentidem.trace.models import (
    OperationKind,
    OperationStatus,
    Trace,
    TraceOperation,
)


@dataclass(frozen=True)
class DuplicateWrite:
    operation_name: str
    args: dict[str, Any]
    count: int
    operations: tuple[TraceOperation, ...]


def _operation_identity(operation: TraceOperation) -> str:
    if operation.identity is not None:
        return f"custom:{canonicalize_args({'identity': normalize_value(operation.identity)})}"

    return f"args:{canonicalize_args(operation.args)}"


def detect_duplicate_writes(trace: Trace) -> list[DuplicateWrite]:
    grouped: dict[
        tuple[str, str],
        list[TraceOperation],
    ] = {}

    for operation in trace.operations:
        if operation.kind != OperationKind.WRITE:
            continue

        if operation.status != OperationStatus.SUCCESS:
            continue

        key = (
            operation.name,
            _operation_identity(operation),
        )

        grouped.setdefault(key, []).append(operation)

    duplicates: list[DuplicateWrite] = []

    for operations in grouped.values():
        if len(operations) <= 1:
            continue

        first = operations[0]

        duplicates.append(
            DuplicateWrite(
                operation_name=first.name,
                args=first.args,
                count=len(operations),
                operations=tuple(operations),
            )
        )

    return duplicates


def duplicate_write_to_finding(
        duplicate: DuplicateWrite,
) -> Finding:
    return Finding(
        code="duplicate_write",
        message=(
            f"Write '{duplicate.operation_name}' "
            f"executed {duplicate.count} times."
        ),
        severity=FindingSeverity.ERROR,
        details={
            "operation_name": duplicate.operation_name,
            "args": duplicate.args,
            "count": duplicate.count,
            "operation_ids": [
                str(operation.id)
                for operation in duplicate.operations
            ],
        },
    )


def detect_duplicate_write_findings(
        trace: Trace,
) -> list[Finding]:
    return [
        duplicate_write_to_finding(duplicate)
        for duplicate in detect_duplicate_writes(trace)
    ]