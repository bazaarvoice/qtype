"""Common type definitions for qtype."""

from __future__ import annotations

import pathlib
from typing import Any, Union

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

# Configuration dictionary type
ConfigDict = dict[str, Any]

# Path-like type (string or Path object)
PathLike = Union[str, pathlib.Path]
