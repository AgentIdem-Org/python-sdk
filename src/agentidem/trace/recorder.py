from __future__ import annotations

from datetime import datetime, timezone

from agentidem.trace.models import Trace, TraceOperation


class TraceRecorder:
    def __init__(self, target: str) -> None:
        self._trace = Trace(target=target)

    @property
    def trace(self) -> Trace:
        return self._trace

    def add_operation(self, operation: TraceOperation) -> None:
        self._trace.operations.append(operation)

    def finish_operation(self, operation: TraceOperation) -> None:
        operation.completed_at = datetime.now(timezone.utc)

    def finish(self) -> Trace:
        self._trace.completed_at = datetime.now(timezone.utc)
        return self._trace