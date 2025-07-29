from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _make_hashable(value: Any) -> Any:
    """Convert a value to a hashable equivalent."""
    if isinstance(value, BaseModel):
        # Handle Pydantic models by iterating over their fields
        hashable_values = []
        for field_name, field_value in value.model_dump().items():
            hashable_values.append((field_name, _make_hashable(field_value)))
        return tuple(sorted(hashable_values))
    elif isinstance(value, dict):
        return frozenset(
            (k, _make_hashable(v)) for k, v in sorted(value.items())
        )
    elif isinstance(value, list):
        return tuple(_make_hashable(item) for item in value)
    elif isinstance(value, set):
        return frozenset(_make_hashable(item) for item in value)
    elif hasattr(value, "__dict__"):
        # Handle nested objects
        return tuple(
            sorted(
                (k, _make_hashable(v))
                for k, v in value.__dict__.items()
                if not k.startswith("_")
            )
        )
    else:
        # Value is already hashable (int, str, tuple, etc.)
        return value


class ImmutableModel(BaseModel):
    """Base model that can't be mutated but can be cached."""

    id: str = Field(..., description="Unique ID of this model.")

    model_config = ConfigDict(frozen=True)

    def __hash__(self) -> int:
        """Hash based on all model fields."""
        return hash(_make_hashable(self))
