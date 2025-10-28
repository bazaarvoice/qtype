"""
Semantic model loading and resolution.
"""

from __future__ import annotations

from qtype.base.types import CustomTypeRegistry
from qtype.dsl.linker import link
from qtype.dsl.loader import load_document
from qtype.semantic.checker import check
from qtype.semantic.model import DocumentType
from qtype.semantic.resolver import resolve


def load(content: str) -> tuple[DocumentType, CustomTypeRegistry]:
    """
    Load a QType YAML file, validate it, and return the resolved semantic Document.

    Args:
        content: Either a fsspec uri/file path to load, or a string containing YAML content.

    Returns:
        A tuple of (Document, CustomTypeRegistry).

    Raises:
        YAMLLoadError: If YAML parsing fails.
        ValueError: If the root document is not an Document or validation fails.
        FileNotFoundError: If the YAML file or included files don't exist.
        QTypeSemanticError: If the loaded spec violates semantic rules.
    """
    root, dynamic_types_registry = load_document(content)
    dsl_doc = link(root)
    semantic_doc = resolve(dsl_doc)
    check(semantic_doc)
    return semantic_doc, dynamic_types_registry
