"""Utility types and functions for the DSL."""

from __future__ import annotations

from datetime import date, datetime, time

from qtype.base.types import PrimitiveTypeEnum

# Mapping of QType primitive types to Python types for internal representations
PRIMITIVE_TO_PYTHON_TYPE = {
    PrimitiveTypeEnum.audio: bytes,
    PrimitiveTypeEnum.boolean: bool,
    PrimitiveTypeEnum.bytes: bytes,
    PrimitiveTypeEnum.date: date,
    PrimitiveTypeEnum.datetime: datetime,
    PrimitiveTypeEnum.int: int,
    PrimitiveTypeEnum.file: bytes,  # Use bytes for file content
    PrimitiveTypeEnum.float: float,
    PrimitiveTypeEnum.image: bytes,  # Use bytes for image data
    PrimitiveTypeEnum.text: str,
    PrimitiveTypeEnum.time: time,  # Use time for time representation
    PrimitiveTypeEnum.video: bytes,  # Use bytes for video data
}

PYTHON_TYPE_TO_PRIMITIVE_TYPE = {
    bytes: PrimitiveTypeEnum.file,
    bool: PrimitiveTypeEnum.boolean,
    str: PrimitiveTypeEnum.text,
    int: PrimitiveTypeEnum.int,
    float: PrimitiveTypeEnum.float,
    date: PrimitiveTypeEnum.date,
    datetime: PrimitiveTypeEnum.datetime,
    time: PrimitiveTypeEnum.time,
    # TODO: decide on internal representation for images, video, and audio,
    # or use annotation/hinting
}


def python_type_for_list(element_type: PrimitiveTypeEnum) -> type:
    """
    Get the Python list type for a given QType primitive element type.

    Args:
        element_type: The primitive type of the list elements

    Returns:
        The corresponding Python list type (e.g., list[str] for text elements)
    """
    element_python_type = PRIMITIVE_TO_PYTHON_TYPE[element_type]
    return list[element_python_type]
