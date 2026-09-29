from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class OperationKind(str, Enum):
    READ = "read"
    WRITE = "write"


class OperationStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class ObservationStatus(str, Enum):
    RECEIVED = "received"
    LOST = "lost"
    FAILED = "failed"


class TraceOperation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    kind: OperationKind

    args: dict[str, Any] = Field(default_factory=dict)

    identity: Any | None = None

    result: Any | None = None
    error: str | None = None

    status: OperationStatus
    observation: ObservationStatus = ObservationStatus.RECEIVED

    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: datetime | None = None

class Trace(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    target: str

    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: datetime | None = None

    operations: list[TraceOperation] = Field(default_factory=list)