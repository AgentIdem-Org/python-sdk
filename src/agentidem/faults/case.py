from __future__ import annotations

from dataclasses import dataclass

from agentidem.faults.plan import FaultPhase


@dataclass(frozen=True)
class FaultCase:
    scenario: str
    operation_index: int | None = None
    operation_name: str | None = None
    phase: FaultPhase | None = None
    message: str | None = None