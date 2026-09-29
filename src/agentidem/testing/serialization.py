from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agentidem.testing.models import TestReport

REPORT_SCHEMA_VERSION = "1"

def report_to_dict(report: TestReport) -> dict[str, Any]:
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "safe": report.safe,
        "fault_count": report.fault_count,
        "unsafe_count": report.unsafe_count,
        "baseline_succeeded": report.baseline_succeeded,
        "baseline_failure": (
            {
                "error_type": report.baseline_failure.error_type,
                "message": report.baseline_failure.message,
            }
            if report.baseline_failure is not None
            else None
        ),
        "baseline": report.baseline.model_dump(mode="json"),
        "results": [
            {
                "scenario": result.case.scenario,
                "operation_index": result.case.operation_index,
                "operation_name": result.case.operation_name,
                "phase": (
                    result.case.phase.value
                    if result.case.phase is not None
                    else None
                ),
                "safe": result.safe,
                "failed": result.failed,
                "error": (
                    f"{type(result.error).__name__}: {result.error}"
                    if result.error is not None
                    else None
                ),
                "trace": result.trace.model_dump(mode="json"),
                "invariants": [
                    {
                        "name": invariant.name,
                        "passed": invariant.passed,
                        "message": invariant.message,
                    }
                    for invariant in result.invariants
                ],
                "duplicates": [
                    {
                        "operation_name": duplicate.operation_name,
                        "args": duplicate.args,
                        "count": duplicate.count,
                        "operation_ids": [
                            str(operation.id)
                            for operation in duplicate.operations
                        ],
                    }
                    for duplicate in result.duplicates
                ],
                "findings": [
                    {
                        "code": finding.code,
                        "message": finding.message,
                        "severity": finding.severity.value,
                        "details": finding.details,
                    }
                    for finding in result.findings
                ],
            }
            for result in report.results
        ],
    }


def save_report(
        report: TestReport,
        path: str | Path,
) -> None:
    target = Path(path)

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    target.write_text(
        json.dumps(
            report_to_dict(report),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )