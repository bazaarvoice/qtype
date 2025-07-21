"""
Semantic resolution logic for QType.

This module contains functions to transform DSL QTypeSpec objects into their
semantic intermediate representation equivalents, where all ID references
are resolved to actual object references.
"""

import logging
from typing import Any

import qtype.dsl.domain_types
import qtype.dsl.model as dsl
from qtype.dsl.validator import _is_dsl_type, _resolve_forward_ref
from qtype.semantic import model as ir
from qtype.semantic.errors import SemanticResolutionError

logger = logging.getLogger(__name__)

FIELDS_TO_IGNORE = {"Application.references"}


def to_semantic_ir(
    dslobj: qtype.dsl.domain_types.StrictBaseModel,
    symbol_table: dict[str, Any],
) -> Any:
    """
    Convert a DSL QTypeSpec object to its semantic intermediate representation (IR).

    Args:
        dsl: The DSL QTypeSpec object to convert.

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

    if isinstance(dslobj, dsl.Enum):
        # if the variable is an enum, just return it. The semantic classes use the same class
        return dslobj

    if _is_dsl_type(_resolve_forward_ref(type(dslobj))):
        # If the object is a DSL type, we will resolve it to its semantic IR.
        # First get the constructor with the same class name. i.e., dsl.Application -> ir.Application
        class_name = dslobj.__class__.__name__
        ir_class = getattr(ir, class_name, None)
        if not ir_class:
            raise SemanticResolutionError(
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
    elif isinstance(dslobj, list):
        return [to_semantic_ir(item, symbol_table) for item in dslobj]  # type: ignore
    else:
        return dslobj


def resolve(application: dsl.Application) -> ir.Application:
    """
    Resolve a DSL Application into its semantic intermediate representation.

    This function transforms the DSL Application into its IR equivalent,
    resolving all ID references to actual object references.

    Args:
        application: The DSL Application to transform

    Returns:
        dsl.Application: The resolved IR application
    """
    # Next, we'll build up the semantic representation.
    # This will create a map of all objects by their ID, ensuring that we can resolve
    # references to actual objects.
    result = to_semantic_ir(application, {})
    if not isinstance(result, ir.Application):
        raise SemanticResolutionError(
            "The root object must be an Application, but got: "
            f"{type(result).__name__}"
        )
    return result
