from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class FindingSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    severity: FindingSeverity
    details: dict[str, Any]