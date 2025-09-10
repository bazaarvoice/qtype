"""Common type definitions for qtype."""

from __future__ import annotations

import pathlib
from typing import Any, Type, Union

from pydantic import BaseModel

from qtype.dsl import model as dsl

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
CustomTypeRegistry = dict[str, Type[BaseModel]]
DocumentRootType = dsl.Agent | dsl.Application | dsl.Flow | list
