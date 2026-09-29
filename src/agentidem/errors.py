from __future__ import annotations

from agentidem.trace.models import Trace


class AgentIdemError(Exception):
    """Base exception for AgentIdem errors."""


class IdentityResolutionError(AgentIdemError):
    """Raised when a write identity function cannot be evaluated."""

    def __init__(
            self,
            operation_name: str,
            *,
            cause: Exception,
    ) -> None:
        super().__init__(
            f"Failed to resolve identity for write '{operation_name}': "
            f"{type(cause).__name__}: {cause}"
        )

        self.operation_name = operation_name
        self.cause = cause


class TracedExecutionError(AgentIdemError):
    """Raised when a traced target fails during execution."""

    def __init__(
            self,
            message: str,
            *,
            trace: Trace,
            cause: Exception,
    ) -> None:
        super().__init__(message)

        self.trace = trace
        self.cause = cause