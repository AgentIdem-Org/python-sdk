from __future__ import annotations

from agentidem.trace.models import Trace


DUPLICATE_DELIVERY_SCENARIO = "duplicate_delivery"


def combine_duplicate_delivery_traces(
        first: Trace,
        second: Trace,
) -> Trace:
    if first.target != second.target:
        raise ValueError(
            "Duplicate delivery traces must have the same target."
        )

    return Trace(
        target=first.target,
        started_at=first.started_at,
        completed_at=second.completed_at,
        operations=[
            *first.operations,
            *second.operations,
        ],
    )