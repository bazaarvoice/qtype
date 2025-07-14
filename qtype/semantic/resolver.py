"""
Semantic resolution logic for QType.

This module contains functions to transform DSL QTypeSpec objects into their
semantic intermediate representation equivalents, where all ID references
are resolved to actual object references.
"""

from typing import Any
import qtype.dsl.model as dsl
from qtype.semantic import model as ir
from qtype.semantic.errors import SemanticResolutionError
from qtype.semantic.validator import (
    _is_dsl_type,
    dsl_to_semantic_type_name,
    validate,
)
import logging

logger = logging.getLogger(__name__)


def to_semantic_ir(
    dslobj: Any,
    symbol_table: dict[str, Any],
    dsl_lookup_table: dict[str, Any],
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

    if isinstance(dslobj, str) and dslobj in dsl_lookup_table:
        # If the object itself is in the DSL lookup table, then we've hit a reference in the DSL.
        # We will resolve it to the semantic IR.
        return to_semantic_ir(
            dsl_lookup_table[dslobj], symbol_table, dsl_lookup_table
        )

    if dslobj is None:
        # If the object is None, return it
        return None

    if isinstance(dslobj, list):
        # If the object is a list, we will resolve each item in the list.
        return [
            to_semantic_ir(item, symbol_table, dsl_lookup_table)
            for item in dslobj
        ]  # type: ignore

    if isinstance(dslobj, dict):
        # If the object is a dict, we will resolve each value in the dict.
        return {
            k: to_semantic_ir(v, symbol_table, dsl_lookup_table)
            for k, v in dslobj.items()
        }  # type: ignore

    if _is_dsl_type(type(dslobj)) and obj_id is not None:
        # If the object is a DSL type and has an ID, we will resolve it to the semantic IR.
        # Get the type name of the DSL object
        type_name = dsl_to_semantic_type_name(type(dslobj))
        # Get the constructor for the type
        constructor = getattr(ir, type_name)
        # Handle the parameters
        params = {}
        for param_name, param in constructor.model_fields.items():
            if type_name == "TelemetrySink":
                pass
            if param_name not in {"self"}:
                # If the parameter is not self, we will resolve it.
                param_value = getattr(dslobj, param_name)
                semantic_type_name = dsl_to_semantic_type_name(
                    param.annotation
                )
                if semantic_type_name.startswith("list["):
                    if param_value is None:
                        # If the parameter is None but the annotation is a list, we will use an empty list.
                        params[param_name] = []
                    else:
                        params[param_name] = to_semantic_ir(
                            param_value, symbol_table, dsl_lookup_table
                        )
                elif semantic_type_name.startswith("dict["):
                    if param_value is None:
                        # If the parameter is None but the annotation is a dict, we will use an empty dict.
                        params[param_name] = {}
                    else:
                        params[param_name] = to_semantic_ir(
                            param_value, symbol_table, dsl_lookup_table
                        )
                elif semantic_type_name != "str" and isinstance(param_value, str) and param_value in dsl_lookup_table:
                    # We've hit a reference in the DSL, so we will resolve it.
                    params[param_name] = to_semantic_ir(
                        dsl_lookup_table[param_value],
                        symbol_table,
                        dsl_lookup_table,
                    )
                else:
                    # resolve the parameter value if it's a DSL type
                    if _is_dsl_type(type(param_value)):
                        params[param_name] = to_semantic_ir(
                            param_value, symbol_table, dsl_lookup_table
                        )
                    else:
                        # If the parameter is not a DSL type, we will just use the value as is.
                        params[param_name] = param_value
        # Create the semantic object using the constructor and the resolved parameters
        result = constructor(**params)
        # Save it in the symbol table so it is not created again.
        symbol_table[obj_id] = result
        return result
    else:
        # Just return the object as is since we don't know how to resolve it.
        # It is likely an enum or a primitive type.
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

    # First run semantic validation to ensure the application is valid.
    dsl_lookup = validate(application)

    # If any flows have no steps, we raise an error.
    for flow in application.flows or []:
        if not flow.steps:
            raise SemanticResolutionError(
                f"Flow {flow.id} has no steps defined."
            )
        # If any flow doesn't have inputs, copy the inputs from the first step.
        if not flow.inputs:
            first_step = (
                dsl_lookup[flow.steps[0]]
                if isinstance(flow.steps[0], str)
                else flow.steps[0]
            )
            flow.inputs = first_step.inputs or []  # type: ignore

        # If any flow doesn't have outputs, copy them from the last step.
        if not flow.outputs:
            last_step = (
                dsl_lookup[flow.steps[-1]]
                if isinstance(flow.steps[-1], str)
                else flow.steps[-1]
            )
            flow.outputs = last_step.outputs or []  # type: ignore

    # Next, we'll build up the semantic representation.
    # This will create a map of all objects by their ID, ensuring that we can resolve
    # references to actual objects.
    symbol_table = {}
    return to_semantic_ir(application, symbol_table, dsl_lookup)
