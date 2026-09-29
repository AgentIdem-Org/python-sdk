from __future__ import annotations

from collections.abc import Callable
from functools import wraps

from agentidem.trace.models import Trace


InvariantFunction = Callable[[Trace], None]


def invariant(func: InvariantFunction) -> InvariantFunction:
    @wraps(func)
    def wrapper(trace: Trace) -> None:
        func(trace)

    return wrapper