import pytest

from agentidem.cli.loader import TargetLoadError, load_target


def test_load_target_loads_callable() -> None:
    target = load_target("math:sqrt")

    assert callable(target)
    assert target(9) == 3


def test_load_target_requires_colon_separator() -> None:
    with pytest.raises(
            TargetLoadError,
            match="module.path:function",
    ):
        load_target("math.sqrt")


def test_load_target_rejects_empty_module() -> None:
    with pytest.raises(
            TargetLoadError,
            match="Target module cannot be empty.",
    ):
        load_target(":sqrt")


def test_load_target_rejects_empty_function() -> None:
    with pytest.raises(
            TargetLoadError,
            match="Target function cannot be empty.",
    ):
        load_target("math:")


def test_load_target_rejects_missing_module() -> None:
    with pytest.raises(
            TargetLoadError,
            match="Failed to import module",
    ):
        load_target(
            "this_module_definitely_does_not_exist:run"
        )


def test_load_target_rejects_missing_attribute() -> None:
    with pytest.raises(
            TargetLoadError,
            match="has no attribute",
    ):
        load_target("math:this_does_not_exist")


def test_load_target_rejects_non_callable_attribute() -> None:
    with pytest.raises(
            TargetLoadError,
            match="is not callable",
    ):
        load_target("math:pi")