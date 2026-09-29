from __future__ import annotations

from agentidem import write
from agentidem.faults.injector import InjectedFaultError


def safe_agent() -> str:
    return "ok"


@write
def save_order(order_id: str) -> str:
    return f"saved:{order_id}"


def unsafe_agent() -> str:
    return save_order("ord_42")


@write
def refund_order(order_id: str) -> str:
    return f"refunded:{order_id}"


def retrying_agent() -> str:
    try:
        return refund_order("ord_42")
    except InjectedFaultError:
        return refund_order("ord_42")


@write
def failing_write() -> None:
    raise RuntimeError("database unavailable")


def failing_agent() -> None:
    failing_write()

# Async functions

async def async_safe_agent() -> str:
    return "ok"


@write
async def async_save_order(order_id: str) -> str:
    return f"saved:{order_id}"


async def async_unsafe_agent() -> str:
    return await async_save_order("ord_42")