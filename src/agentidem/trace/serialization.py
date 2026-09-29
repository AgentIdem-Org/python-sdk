from pathlib import Path

from agentidem.trace.models import Trace


def save_trace(trace: Trace, path: str | Path) -> None:
    target = Path(path)

    target.parent.mkdir(parents=True, exist_ok=True)

    target.write_text(
        trace.model_dump_json(indent=2),
        encoding="utf-8",
    )


def load_trace(path: str | Path) -> Trace:
    source = Path(path)

    data = source.read_text(encoding="utf-8")

    return Trace.model_validate_json(data)