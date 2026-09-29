from __future__ import annotations

from contextvars import ContextVar, Token

from agentidem.trace.recorder import TraceRecorder


_active_recorder: ContextVar[TraceRecorder | None] = ContextVar(
    "agentidem_active_recorder",
    default=None,
)


def get_recorder() -> TraceRecorder | None:
    return _active_recorder.get()


def set_recorder(recorder: TraceRecorder) -> Token:
    return _active_recorder.set(recorder)


def reset_recorder(token: Token) -> None:
    _active_recorder.reset(token)