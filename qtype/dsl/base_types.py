from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict

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
    number = "number"
    text = "text"
    time = "time"
    video = "video"


class StrictBaseModel(BaseModel):
    """Base model with extra fields forbidden."""

    model_config = ConfigDict(extra="forbid")
