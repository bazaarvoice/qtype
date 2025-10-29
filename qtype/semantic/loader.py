"""
Semantic model loading and resolution.

This is the main entry point for loading QType specifications.
Coordinates the pipeline: load → parse → link → resolve → check
"""

from __future__ import annotations

from pathlib import Path

from qtype.base.types import CustomTypeRegistry
from qtype.dsl.linker import link
from qtype.dsl.loader import load_yaml_file, load_yaml_string
from qtype.dsl.parser import parse_document
from qtype.semantic.checker import check
from qtype.semantic.model import DocumentType
from qtype.semantic.resolver import resolve


def load(
    source: str | Path,
) -> tuple[DocumentType, CustomTypeRegistry]:
    """
    Load a QType YAML file, validate it, and return resolved semantic model.

    This function coordinates the complete loading pipeline:
    1. Load YAML (with env vars and includes)
    2. Parse into DSL models (with custom type building)
    3. Link references (resolve IDs to objects)
    4. Resolve to semantic models (DSL → IR)
    5. Check semantic rules

    Args:
        source: File path (str or Path) to load. Use load_from_string()
                for raw YAML content.

    Returns:
        Tuple of (SemanticDocumentType, CustomTypeRegistry)

    Raises:
        YAMLLoadError: If YAML parsing fails
        ValueError: If validation fails
        DuplicateComponentError: If duplicate IDs found
        ReferenceNotFoundError: If reference resolution fails
        QTypeSemanticError: If semantic rules violated
    """
    # Load from file path
    if isinstance(source, Path):
        yaml_data = load_yaml_file(source)
    else:
        # Assume str is a file path
        yaml_data = load_yaml_file(source)

    dsl_doc, types = parse_document(yaml_data)
    linked_doc = link(dsl_doc)
    semantic_doc = resolve(linked_doc)
    check(semantic_doc)
    return semantic_doc, types


def load_from_string(
    content: str, base_path: str | Path | None = None
) -> tuple[DocumentType, CustomTypeRegistry]:
    """
    Load a QType YAML from string content.

    This function coordinates the complete loading pipeline:
    1. Load YAML (with env vars and includes)
    2. Parse into DSL models (with custom type building)
    3. Link references (resolve IDs to objects)
    4. Resolve to semantic models (DSL → IR)
    5. Check semantic rules

    Args:
        content: Raw YAML content as string
        base_path: Base path for resolving relative includes (default: cwd)

    Returns:
        Tuple of (SemanticDocumentType, CustomTypeRegistry)

    Raises:
        YAMLLoadError: If YAML parsing fails
        ValueError: If validation fails
        DuplicateComponentError: If duplicate IDs found
        ReferenceNotFoundError: If reference resolution fails
        QTypeSemanticError: If semantic rules violated
    """
    yaml_data = load_yaml_string(content, base_path=base_path)

    dsl_doc, types = parse_document(yaml_data)
    linked_doc = link(dsl_doc)
    semantic_doc = resolve(linked_doc)
    check(semantic_doc)
    return semantic_doc, types
