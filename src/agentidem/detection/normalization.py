from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID
from pydantic import BaseModel

def normalize_value(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value

    if isinstance(value, Enum):
        return normalize_value(value.value)

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, Path):
        return str(value)

    if is_dataclass(value) and not isinstance(value, type):
        return normalize_value(asdict(value))

    if isinstance(value, BaseModel):
        return normalize_value(
            value.model_dump(
                mode="python",
                by_alias=True,
            )
        )

    if isinstance(value, Mapping):
        return {
            str(key): normalize_value(item)
            for key, item in sorted(
                value.items(),
                key=lambda item: str(item[0]),
            )
        }

    if isinstance(value, set | frozenset):
        normalized = [
            normalize_value(item)
            for item in value
        ]

        return sorted(
            normalized,
            key=lambda item: json.dumps(
                item,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )

    if isinstance(value, Sequence) and not isinstance(
            value,
            str | bytes | bytearray,
    ):
        return [
            normalize_value(item)
            for item in value
        ]

    return {
        "__type__": (
            f"{type(value).__module__}."
            f"{type(value).__qualname__}"
        ),
        "__repr__": repr(value),
    }


def canonicalize_args(args: dict[str, Any]) -> str:
    normalized = normalize_value(args)

    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )