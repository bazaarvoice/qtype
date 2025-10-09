from __future__ import annotations

from enum import Enum
from typing import Any, Generic, TypeVar, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, Field, model_validator

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

    @model_validator(mode="before")
    @classmethod
    def normalize_string_references(cls, data: Any) -> Any:
        """
        Normalize string references to Reference objects before validation.

        This validator processes all fields in the model data (except 'type'
        which is used as a discriminator) and transforms:
        - `field: "ref_id"` -> `field: {"$ref": "ref_id"}`
        - `field: ["ref1", "ref2"]` -> `field: [{"$ref": "ref1"}, {"$ref": "ref2"}]`

        This only applies to fields that are typed as Union[Reference[T], str]
        or list[Union[Reference[T], str]].
        """
        if not isinstance(data, dict):
            return data

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

        # Get the field annotations from the class
        annotations = getattr(cls, "__annotations__", {})

        # Process each field in the data
        for field_name, field_value in data.items():
            # Skip the 'type' field as it's used as a discriminator
            if field_name == "type":
                continue

            # Skip if field is not in annotations
            if field_name not in annotations:
                continue

            annotation = annotations[field_name]

            # Handle list[Reference[T] | str] | None case
            if isinstance(field_value, list):
                origin = get_origin(annotation)
                if origin is list:
                    # Get the inner type of the list
                    inner_args = get_args(annotation)
                    if inner_args and is_ref_str_union(inner_args[0]):
                        # Transform each string in the list to a Reference
                        data[field_name] = [
                            {"$ref": item} if isinstance(item, str) else item
                            for item in field_value
                        ]
                # Handle Union[list[Union[Reference, str]], None]
                elif origin is Union:
                    # Check if any arg is list[Union[Reference, str]]
                    for arg in get_args(annotation):
                        if get_origin(arg) is list:
                            inner_args = get_args(arg)
                            if inner_args and is_ref_str_union(inner_args[0]):
                                data[field_name] = [
                                    {"$ref": item}
                                    if isinstance(item, str)
                                    else item
                                    for item in field_value
                                ]
                                break

            # Handle direct Union[Reference[T], str] case
            elif isinstance(field_value, str) and is_ref_str_union(annotation):
                data[field_name] = {"$ref": field_value}

        return data
