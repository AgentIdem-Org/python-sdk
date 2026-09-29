from __future__ import annotations

from rich.console import Console
from rich.table import Table

from agentidem.testing.models import TestReport


console = Console()
error_console = Console(stderr=True)


def render_test_report(
        target: str,
        report: TestReport,
) -> None:
    if report.baseline_failure is not None:
        render_baseline_failure(
            target,
            report,
        )
        return

    status = "SAFE" if report.safe else "UNSAFE"

    console.print()
    console.print(
        f"[bold]{status}[/bold]  {target}"
    )

    console.print(
        f"Fault cases: {report.fault_count}  "
        f"Unsafe: {report.unsafe_count}"
    )

    if not report.results:
        return

    table = Table(
        title="Fault scenarios",
        show_header=True,
        header_style="bold",
    )

    table.add_column("Scenario")
    table.add_column("Status")
    table.add_column("Execution")
    table.add_column("Findings", justify="right")

    for result in report.results:
        scenario_status = (
            "SAFE"
            if result.safe
            else "UNSAFE"
        )

        execution_status = (
            "FAILED"
            if result.failed
            else "COMPLETED"
        )

        table.add_row(
            result.case.scenario,
            scenario_status,
            execution_status,
            str(len(result.findings)),
        )

    console.print(table)


def render_baseline_failure(
        target: str,
        report: TestReport,
) -> None:
    failure = report.baseline_failure

    if failure is None:
        return

    error_console.print()
    error_console.print(
        f"[bold]BASELINE FAILED[/bold]  {target}"
    )

    error_console.print(
        f"{failure.error_type}: {failure.message}"
    )


def render_target_error(
        message: str,
) -> None:
    error_console.print(
        f"[bold]ERROR[/bold]  {message}"
    )