"""
Parse YAML dictionaries into DSL models.

This module handles the conversion of loaded YAML data into validated
Pydantic DSL models, including custom type extraction and building.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from qtype.base.types import CustomTypeRegistry
from qtype.dsl import model as dsl
from qtype.dsl.custom_types import build_dynamic_types


def _extract_type_definitions(data: dict[str, Any] | list) -> list[dict]:
    """
    Extract all custom type definitions from document.

    Recursively finds type definitions in the document and any references.

    Args:
        data: Parsed YAML dictionary or list

    Returns:
        List of custom type definition dictionaries
    """
    types = []

    # Handle list documents (e.g., ToolList, ModelList)
    if isinstance(data, list):
        return types

    # Add types from Application documents
    if isinstance(data, dict):
        types.extend(data.get("types", []))

    # Handle TypeList documents (root is a list of types)
    if "root" in data:
        root = data["root"]
        if (
            isinstance(root, list)
            and len(root) > 0
            and "properties" in root[0]
        ):
            types.extend(root)

    # Recursively handle references
    for ref in data.get("references", []):
        types.extend(_extract_type_definitions(ref))

    return types


def _simplify_field_path(loc: tuple) -> str:
    """
    Simplify a Pydantic error location path for readability.

    Removes verbose union type names and formats array indices.

    Args:
        loc: Error location tuple from Pydantic

    Returns:
        Simplified, readable field path string
    """
    simplified = []
    for part in loc:
        part_str = str(part)

        # Skip union type discriminator paths (too verbose)
        if "tagged-union" in part_str or "Union[" in part_str:
            continue

        # Skip Reference wrapper types
        if part_str.startswith("Reference["):
            continue

        # Format numeric indices as array indices
        if isinstance(part, int):
            simplified.append(f"[{part}]")
        else:
            simplified.append(part_str)

    return " -> ".join(simplified).replace(" -> [", "[")


def _is_relevant_error(error: dict | Any) -> bool:
    """
    Determine if a validation error is relevant to show.

    Filters out noise from union type matching attempts.

    Args:
        error: Pydantic error dictionary

    Returns:
        True if error should be shown to user
    """
    loc_str = " -> ".join(str(loc) for loc in error["loc"])
    error_type = error["type"]

    # Filter out "should be a valid list" errors for document types
    # These are just union matching attempts
    if error_type == "list_type" and any(
        doc_type in loc_str
        for doc_type in [
            "AuthorizationProviderList",
            "ModelList",
            "ToolList",
            "TypeList",
            "VariableList",
            "AgentList",
            "FlowList",
            "IndexList",
        ]
    ):
        return False

    # Filter out Reference wrapper errors about $ref field
    # These are duplicates of actual validation errors
    if "Reference[" in loc_str and "$ref" in error["loc"][-1]:
        return False

    return True


def _format_validation_errors(
    validation_error: ValidationError, source_name: str | None
) -> str:
    """
    Format Pydantic validation errors in user-friendly way.

    Args:
        validation_error: ValidationError from Pydantic
        source_name: Optional source file name for context

    Returns:
        Formatted error message string
    """
    # Filter and collect relevant errors
    relevant_errors = [
        error
        for error in validation_error.errors()
        if _is_relevant_error(error)
    ]

    if not relevant_errors:
        # Fallback if all errors were filtered
        error_msg = "Validation failed (see details above)"
    else:
        error_msg = "Validation failed:\n"
        for error in relevant_errors[:5]:  # Show max 5 errors
            loc_path = _simplify_field_path(error["loc"])
            error_msg += f"  {loc_path}: {error['msg']}\n"

        if len(relevant_errors) > 5:
            error_msg += f"  ... and {len(relevant_errors) - 5} more errors\n"

    if source_name:
        error_msg = f"In {source_name}:\n{error_msg}"

    return error_msg


def parse_document(
    yaml_data: dict[str, Any], source_name: str | None = None
) -> tuple[dsl.DocumentType, CustomTypeRegistry]:
    """
    Parse validated YAML dictionary into DSL document.

    Args:
        yaml_data: Pre-loaded YAML dictionary
        source_name: Optional source name for error messages

    Returns:
        Tuple of (DocumentType, CustomTypeRegistry)

    Raises:
        ValueError: If validation fails
    """
    # Extract and build custom types
    type_defs = _extract_type_definitions(yaml_data)
    custom_types = build_dynamic_types(type_defs)

    # Validate with Pydantic
    try:
        document = dsl.Document.model_validate(
            yaml_data, context={"custom_types": custom_types}
        )
    except ValidationError as e:
        # Format validation errors nicely
        error_msg = _format_validation_errors(e, source_name)
        raise ValueError(error_msg) from e

    # Extract root document from wrapper
    return document.root, custom_types
