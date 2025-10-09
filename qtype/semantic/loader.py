"""
Semantic model loading and resolution.
"""

from __future__ import annotations

from qtype.base.types import CustomTypeRegistry
from qtype.dsl import model as dsl
from qtype.dsl.loader import load_document
from qtype.dsl.validator import validate
from qtype.semantic.model import Application
from qtype.semantic.resolver import resolve


def load(content: str) -> tuple[Application, CustomTypeRegistry]:
    """
    Load a QType YAML file, validate it, and return the resolved semantic Application.

    Args:
        content: Either a fsspec uri/file path to load, or a string containing YAML content.

    Returns:
        A tuple of (Application, CustomTypeRegistry).

    Raises:
        ValueError: If the root document is not an Application or validation fails.
        FileNotFoundError: If the YAML file or included files don't exist.
        yaml.YAMLError: If the YAML file is malformed.
    """
    root, dynamic_types_registry = load_document(content)
    if not isinstance(root, dsl.Application):
        raise ValueError(
            f"Root document is not an Application, found {type(root)}."
        )
    root = validate(root)
    return resolve(root), dynamic_types_registry
