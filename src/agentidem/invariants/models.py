from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InvariantResult:
    name: str
    passed: bool
    message: str | None = None