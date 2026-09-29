from __future__ import annotations

import importlib
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any


class TargetLoadError(RuntimeError):
    pass


def load_target(target: str) -> Callable[..., Any]:
    if ":" not in target:
        raise TargetLoadError(
            "Target must use the format 'module.path:function'."
        )

    module_name, object_name = target.split(":", 1)

    if not module_name:
        raise TargetLoadError("Target module cannot be empty.")

    if not object_name:
        raise TargetLoadError("Target function cannot be empty.")

    cwd = str(Path.cwd())

    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        raise TargetLoadError(
            f"Failed to import module '{module_name}': {exc}"
        ) from exc

    try:
        obj = getattr(module, object_name)
    except AttributeError as exc:
        raise TargetLoadError(
            f"Module '{module_name}' has no attribute '{object_name}'."
        ) from exc

    if not callable(obj):
        raise TargetLoadError(
            f"Target '{target}' is not callable."
        )

    return obj