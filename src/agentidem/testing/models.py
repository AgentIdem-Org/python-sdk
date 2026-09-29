from __future__ import annotations

from dataclasses import dataclass

from agentidem.faults.runner import FaultRunResult
from agentidem.trace.models import Trace


@dataclass(frozen=True)
class BaselineFailure:
    error_type: str
    message: str
    trace: Trace


@dataclass(frozen=True)
class TestReport:
    baseline: Trace
    results: tuple[FaultRunResult, ...]
    baseline_failure: BaselineFailure | None = None

    @property
    def baseline_succeeded(self) -> bool:
        return self.baseline_failure is None

    @property
    def safe(self) -> bool:
        if self.baseline_failure is not None:
            return False

        return all(
            result.safe
            for result in self.results
        )

    @property
    def unsafe_count(self) -> int:
        return sum(
            not result.safe
            for result in self.results
        )

    @property
    def fault_count(self) -> int:
        return len(self.results)