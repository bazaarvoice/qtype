"""
Semantic resolution logic for QType.

This module contains functions to transform DSL QTypeSpec objects into their
semantic intermediate representation equivalents, where all ID references
are resolved to actual object references.
"""

import logging
from typing import Any

from pydantic import BaseModel

import qtype.base.types as base_types
import qtype.dsl.model as dsl
import qtype.semantic.model as ir
from qtype.base.exceptions import SemanticError

logger = logging.getLogger(__name__)

FIELDS_TO_IGNORE = {"Application.references"}


def _is_dsl_type(type_obj: Any) -> bool:
    """Check if a type is a DSL type that should be converted to semantic."""
    if not hasattr(type_obj, "__name__"):
        return False

    # Check if it's defined in the DSL module
    return (
        hasattr(type_obj, "__module__")
        and (
            type_obj.__module__ == dsl.__name__
            or type_obj.__module__ == base_types.__name__
        )
        and not type_obj.__name__.startswith("_")
    )


def _resolve_forward_ref(field_type: Any) -> Any:
    """
    Resolve a ForwardRef type to its actual type.
    This is used to handle cases where the type is a string that refers to a class.
    """
    if hasattr(field_type, "__forward_arg__"):
        # Extract the string from ForwardRef and process it
        forward_ref_str = field_type.__forward_arg__
        # Use eval to get the actual type from the string
        return eval(forward_ref_str, dict(vars(dsl)))
    return field_type


def to_semantic_ir(
    dslobj: BaseModel,
    symbol_table: dict[str, Any],
) -> Any:
    """
    Convert a DSL object to its semantic intermediate representation (IR).

    Handles both regular BaseModel types and RootModel types (like *List documents).

    Args:
        dslobj: The DSL object to convert (StrictBaseModel or RootModel).

    Returns:
        ir.Application: The semantic IR representation of the DSL object.
    """

    obj_id = getattr(dslobj, "id", None)
    if obj_id and obj_id in symbol_table:
        # If the object is already in the symbol table, return it.
        return symbol_table[obj_id]

    if isinstance(dslobj, list):
        # If the object is a list, we will resolve each item in the list.
        return [to_semantic_ir(item, symbol_table) for item in dslobj]  # type: ignore

    # Return these types as-is as they are not changed
    if isinstance(dslobj, dsl.Enum) or isinstance(
        dslobj, base_types.CacheConfig
    ):
        return dslobj

    if _is_dsl_type(_resolve_forward_ref(type(dslobj))):
        # If the object is a DSL type, we will resolve it to its semantic IR.
        # First get the constructor with the same class name. i.e., dsl.Application -> ir.Application
        class_name = dslobj.__class__.__name__
        ir_class = getattr(ir, class_name, None)
        if not ir_class:
            raise SemanticError(
                f"Could not find Semantic class for DSL type: {class_name}"
            )
        # iterate over the parameters of the DSL object and convert them to their semantic IR equivalents.
        params = {
            name: to_semantic_ir(value, symbol_table)
            for name, value in dslobj
            if f"{class_name}.{name}" not in FIELDS_TO_IGNORE
        }
        ir.Variable.model_rebuild()
        result = ir_class(**params)
        symbol_table[obj_id] = result  # type: ignore
        return result
    else:
        return dslobj


def resolve(document: dsl.DocumentType) -> ir.DocumentType:
    """
    Resolve a DSL Document into its semantic intermediate representation.

    This function transforms any DSL DocumentType (Application, ModelList, etc.)
    into its IR equivalent, resolving all ID references to actual object references.

    Args:
        document: The DSL Document to transform (Application or any *List type)

    Returns:
        ir.DocumentType: The resolved IR document
    """
    # Build up the semantic representation.
    # This will create a map of all objects by their ID, ensuring that we can resolve
    # references to actual objects.
    result = to_semantic_ir(document, {})

    # Verify the result is one of the valid DocumentType variants
    if not isinstance(
        result,
        (
            ir.Application,
            ir.AuthorizationProviderList,
            ir.ModelList,
            ir.ToolList,
            ir.TypeList,
            ir.VariableList,
        ),
    ):
        raise SemanticError(
            f"The root object must be a valid DocumentType, but got: "
            f"{type(result).__name__}"
        )
    return result
