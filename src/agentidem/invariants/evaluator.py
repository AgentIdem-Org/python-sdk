from __future__ import annotations

from collections.abc import Iterable

from agentidem.invariants.api import InvariantFunction
from agentidem.invariants.models import InvariantResult
from agentidem.trace.models import Trace


def evaluate_invariant(
        invariant_func: InvariantFunction,
        trace: Trace,
) -> InvariantResult:
    try:
        invariant_func(trace)

    except AssertionError as exc:
        raw_message = str(exc).strip()

        message = (
            raw_message.splitlines()[0]
            if raw_message
            else None
        )

        return InvariantResult(
            name=invariant_func.__name__,
            passed=False,
            message=message,
        )

    return InvariantResult(
        name=invariant_func.__name__,
        passed=True,
    )


def evaluate_invariants(
        invariants: Iterable[InvariantFunction],
        trace: Trace,
) -> list[InvariantResult]:
    return [
        evaluate_invariant(invariant_func, trace)
        for invariant_func in invariants
    ]