from __future__ import annotations

from enum import Enum
from typing import Any, Generic, TypeVar, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import ValidationInfo

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

    model_config = ConfigDict(extra="forbid")

    ref: str = Field(..., alias="$ref")


class StrictBaseModel(BaseModel):
    """Base model with extra fields forbidden."""

    model_config = ConfigDict(extra="forbid")

    @field_validator("*", mode="before")  # type: ignore
    @classmethod
    def normalize_string_references(cls, v: Any, info: ValidationInfo) -> Any:
        """
        A generic validator that runs on all fields. It checks if the field's
        type annotation is a Union that includes a Reference type and a string.
        If so, and if the input value is a string, it automatically wraps it
        in a Reference object.

        Also handles list[Reference[T] | str] | None by transforming each string
        element in the list.

        Note: Skips 'type' field as it's used as a discriminator in some models.
        """
        # Skip the 'type' field as it's used as a discriminator
        if info.field_name == "type":  # type: ignore
            return v

        # Helper function to check if a type is a Union with Reference and str
        def is_ref_str_union(annotation: Any) -> bool:
            if get_origin(annotation) is not Union:
                return False
            args = get_args(annotation)
            has_str = str in args
            has_ref = any(
                hasattr(arg, "__name__") and arg.__name__ == "Reference"
                for arg in args
            )
            return has_str and has_ref

        # 1. Handle list[Reference[T] | str] | None case
        if isinstance(v, list):
            origin = get_origin(info.annotation)
            if origin is list:
                # Get the inner type of the list
                inner_args = get_args(info.annotation)
                if inner_args and is_ref_str_union(inner_args[0]):
                    # Transform each string in the list to a Reference
                    return [
                        {"$ref": item} if isinstance(item, str) else item
                        for item in v
                    ]
            # If it's a list but not a list[Union[Reference, str]], handle as Union[list, None]
            elif origin is Union:
                # Check if any arg is list[Union[Reference, str]]
                for arg in get_args(info.annotation):
                    if get_origin(arg) is list:
                        inner_args = get_args(arg)
                        if inner_args and is_ref_str_union(inner_args[0]):
                            return [
                                {"$ref": item}
                                if isinstance(item, str)
                                else item
                                for item in v
                            ]
            return v

        # 2. Handle direct Union[Reference[T], str] case (existing behavior)
        if not isinstance(v, str):
            return v

        if is_ref_str_union(info.annotation):
            return {"$ref": v}

        # 3. Otherwise, return the value as-is.
        return v
