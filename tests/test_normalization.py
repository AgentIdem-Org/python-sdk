from enum import Enum
from pathlib import Path
from uuid import UUID
from dataclasses import dataclass
from pydantic import BaseModel, Field

from agentidem.detection.normalization import canonicalize_args, normalize_value


class ExampleStatus(str, Enum):
    READY = "ready"

def test_normalize_value_handles_dataclass_instances() -> None:
    @dataclass
    class RefundRequest:
        order_id: str
        amount: float

    value = RefundRequest(
        order_id="ord_42",
        amount=50.0,
    )

    normalized = normalize_value(value)

    assert normalized == {
        "amount": 50.0,
        "order_id": "ord_42",
    }

def test_canonicalize_args_is_stable_across_dict_order() -> None:
    first = {
        "kwargs": {
            "order_id": "ord_42",
            "amount": 50,
        },
        "args": [],
    }

    second = {
        "args": [],
        "kwargs": {
            "amount": 50,
            "order_id": "ord_42",
        },
    }

    assert canonicalize_args(first) == canonicalize_args(second)


def test_normalize_value_handles_nested_structures() -> None:
    value = {
        "items": [
            {"b": 2, "a": 1},
            {"status": ExampleStatus.READY},
        ],
        "flags": {"beta", "alpha"},
    }

    normalized = normalize_value(value)

    assert normalized == {
        "flags": ["alpha", "beta"],
        "items": [
            {
                "a": 1,
                "b": 2,
            },
            {
                "status": "ready",
            },
        ],
    }


def test_normalize_value_handles_uuid_and_path() -> None:
    value = {
        "id": UUID("12345678-1234-5678-1234-567812345678"),
        "path": Path("/tmp/agentidem"),
    }

    normalized = normalize_value(value)

    assert normalized == {
        "id": "12345678-1234-5678-1234-567812345678",
        "path": "/tmp/agentidem",
    }


def test_normalize_value_preserves_sequence_order() -> None:
    value = [
        "first",
        "second",
        "third",
    ]

    normalized = normalize_value(value)

    assert normalized == [
        "first",
        "second",
        "third",
    ]


def test_unknown_object_uses_typed_repr_fallback() -> None:
    class CustomObject:
        def __repr__(self) -> str:
            return "CustomObject(example)"

    normalized = normalize_value(CustomObject())

    assert normalized == {
        "__type__": (
            f"{CustomObject.__module__}."
            f"{CustomObject.__qualname__}"
        ),
        "__repr__": "CustomObject(example)",
    }

def test_canonicalize_args_matches_equivalent_dataclasses() -> None:
    @dataclass
    class RefundRequest:
        order_id: str
        amount: float

    first = {
        "args": [
            RefundRequest(
                order_id="ord_42",
                amount=50.0,
            )
        ],
        "kwargs": {},
    }

    second = {
        "args": [
            RefundRequest(
                order_id="ord_42",
                amount=50.0,
            )
        ],
        "kwargs": {},
    }

    assert canonicalize_args(first) == canonicalize_args(second)

def test_normalize_value_handles_pydantic_model() -> None:
    class RefundRequest(BaseModel):
        order_id: str
        amount: float

    value = RefundRequest(
        order_id="ord_42",
        amount=50.0,
    )

    normalized = normalize_value(value)

    assert normalized == {
        "amount": 50.0,
        "order_id": "ord_42",
    }

def test_canonicalize_args_matches_equivalent_pydantic_models() -> None:
    class RefundRequest(BaseModel):
        order_id: str
        amount: float

    first = {
        "args": [
            RefundRequest(
                order_id="ord_42",
                amount=50.0,
            )
        ],
        "kwargs": {},
    }

    second = {
        "args": [
            RefundRequest(
                order_id="ord_42",
                amount=50.0,
            )
        ],
        "kwargs": {},
    }

    assert canonicalize_args(first) == canonicalize_args(second)