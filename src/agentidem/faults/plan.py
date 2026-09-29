from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FaultPhase(str, Enum):
    BEFORE_OPERATION = "before_operation"
    AFTER_OPERATION = "after_operation"


@dataclass(frozen=True)
class FaultPlan:
    scenario: str
    operation_index: int
    operation_name: str
    phase: FaultPhase

    message: str | None = None