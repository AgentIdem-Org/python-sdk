from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from agentidem.trace.models import Trace


@dataclass(frozen=True)
class FaultResult:
    scenario: str
    passed: bool
    trace: Trace
    message: str | None = None


class FaultScenario(ABC):
    name: str

    @abstractmethod
    def run(self, trace: Trace) -> FaultResult:
        """Execute this fault scenario against a trace."""
        raise NotImplementedError