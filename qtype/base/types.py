"""Common type definitions for qtype."""

from __future__ import annotations

import pathlib
import types
import typing
from enum import Enum
from typing import Any, Generic, Type, TypeVar, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic import ConfigDict as PydanticConfigDict
from pydantic import Field, model_validator

# JSON-serializable value types
JSONValue = Union[
    str,
    int,
    float,
    bool,
    None,
    dict[str, "JSONValue"],
    list["JSONValue"],
]

# Path-like type (string or Path object)
PathLike = Union[str, pathlib.Path]
CustomTypeRegistry = dict[str, Type[BaseModel]]
# Configuration dictionary type
ConfigDict = dict[str, Any]


# ---------------- Shared Base Types and Enums ----------------


class PrimitiveTypeEnum(str, Enum):
    """Represents the type of data a user or system input can accept within the DSL."""

    audio = "audio"
    boolean = "boolean"
    bytes = "bytes"
    date = "date"
    datetime = "datetime"
    int = "int"
    file = "file"
    float = "float"
    image = "image"
    text = "text"
    time = "time"
    video = "video"


class StepCardinality(str, Enum):
    """Does this step emit 1 (one) or 0...N (many) items?"""

    one = "one"
    many = "many"


ReferenceT = TypeVar("ReferenceT")


class Reference(BaseModel, Generic[ReferenceT]):
    """Represents a reference to another component by its ID."""

    # model_config = PydanticConfigDict(extra="forbid")

    ref: str = Field(..., alias="$ref")


def _contains_reference_and_str(type_hint: Any) -> bool:
    """Check if type contains both Reference and str in a union."""
    # Get union args (handles Union, | syntax, and Optional)
    origin = get_origin(type_hint)
    if origin not in (Union, None) and not isinstance(
        type_hint, types.UnionType
    ):
        return False

    args = get_args(type_hint)
    if not args:
        return False

    has_str = str in args
    has_ref = any(
        get_origin(arg) is Reference
        or (hasattr(arg, "__mro__") and Reference in arg.__mro__)
        for arg in args
    )
    return has_str and has_ref


def _should_transform_field(type_hint: Any) -> tuple[bool, bool]:
    """
    Check if field should be transformed.
    Returns: (should_transform, is_list)
    """
    # Check direct union: Reference[T] | str
    if _contains_reference_and_str(type_hint):
        return True, False

    # Check list of union: list[Reference[T] | str]
    origin = get_origin(type_hint)
    if origin is list:
        args = get_args(type_hint)
        if args and _contains_reference_and_str(args[0]):
            return True, True

    # Check optional list: list[Reference[T] | str] | None
    if origin is Union or isinstance(type_hint, types.UnionType):
        for arg in get_args(type_hint):
            if get_origin(arg) is list:
                inner_args = get_args(arg)
                if inner_args and _contains_reference_and_str(inner_args[0]):
                    return True, True

    return False, False


class StrictBaseModel(BaseModel):
    """Base model with extra fields forbidden."""

    model_config = PydanticConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def normalize_string_references(cls, data: Any) -> Any:
        """
        Normalize string references to Reference objects before validation.

        Transforms:
        - `field: "ref_id"` -> `field: {"$ref": "ref_id"}`
        - `field: ["ref1", "ref2"]` -> `field: [{"$ref": "ref1"}, {"$ref": "ref2"}]`

        Only applies to fields typed as `Reference[T] | str` or `list[Reference[T] | str]`.
        """
        if not isinstance(data, dict):
            return data

        # Get type hints (evaluates ForwardRefs)
        hints = typing.get_type_hints(cls)

        # Transform fields
        for field_name, field_value in data.items():
            if field_name == "type" or field_name not in hints:
                continue

            should_transform, is_list = _should_transform_field(
                hints[field_name]
            )
            if not should_transform:
                continue

            if is_list and isinstance(field_value, list):
                data[field_name] = [
                    {"$ref": item} if isinstance(item, str) else item
                    for item in field_value
                ]
            elif not is_list and isinstance(field_value, str):
                data[field_name] = {"$ref": field_value}

        return data
