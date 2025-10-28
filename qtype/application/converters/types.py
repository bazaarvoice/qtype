"""
Re-export type mappings from DSL layer for backward compatibility.

This module maintains the application layer's interface while delegating
to the DSL layer where these mappings are now defined.
"""

from qtype.dsl.types import (
    PRIMITIVE_TO_PYTHON_TYPE,
    PYTHON_TYPE_TO_PRIMITIVE_TYPE,
    python_type_for_list,
)

__all__ = [
    "PRIMITIVE_TO_PYTHON_TYPE",
    "PYTHON_TYPE_TO_PRIMITIVE_TYPE",
    "python_type_for_list",
]
