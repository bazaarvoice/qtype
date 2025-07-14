"""
Semantic resolution logic for QType.

This module contains functions to transform DSL QTypeSpec objects into their
semantic intermediate representation equivalents, where all ID references
are resolved to actual object references.
"""

from typing import Any, Union, get_args, get_origin
import qtype.dsl.model as dsl
from qtype.dsl.validator import _is_dsl_type
from qtype.semantic import model as ir
from qtype.semantic.errors import SemanticResolutionError
import logging

logger = logging.getLogger(__name__)


def dsl_to_semantic_type_name(field_type: Any) -> str:
    """Transform a DSL field type to a semantic field type."""

    # Handle ForwardRef objects
    if hasattr(field_type, "__forward_arg__"):
        # Extract the string from ForwardRef and process it
        forward_ref_str = field_type.__forward_arg__
        actual_type = eval(forward_ref_str, dict(vars(dsl)))
        return dsl_to_semantic_type_name(actual_type)

    # Handle Union types (including | syntax)
    origin = get_origin(field_type)
    args = get_args(field_type)

    if origin is Union or (
        hasattr(field_type, "__class__")
        and field_type.__class__.__name__ == "UnionType"
    ):
        return _transform_union_type(args)

    # Handle list types
    if origin is list:
        if args:
            inner_type = dsl_to_semantic_type_name(args[0])
            return f"list[{inner_type}]"
        return "list"

    # Handle dict types
    if origin is dict:
        if len(args) == 2:
            key_type = dsl_to_semantic_type_name(args[0])
            value_type = dsl_to_semantic_type_name(args[1])
            return f"dict[{key_type}, {value_type}]"
        return "dict"

    # Handle basic types
    if hasattr(field_type, "__name__"):
        type_name = field_type.__name__
        if _is_dsl_type(field_type) and type_name not in TYPES_TO_IGNORE:
            return type_name
        if type_name == "NoneType":
            return "None"
        return type_name

    return str(field_type)


def to_semantic_ir(dslobj: Any, symbol_table: dict[str, Any]) -> Any:
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

    if dslobj is None:
        # If the object is None, return it
        return None

    if isinstance(dslobj, list):
        # If the object is a list, we will resolve each item in the list.
        return [to_semantic_ir(item, symbol_table) for item in dslobj]  # type: ignore

    if isinstance(dslobj, dict):
        # If the object is a dict, we will resolve each value in the dict.
        return {k: to_semantic_ir(v, symbol_table) for k, v in dslobj.items()}  # type: ignore

    if _is_dsl_type(type(dslobj)) and obj_id is not None:
        # If the object is a DSL type and has an ID, we will resolve it to the semantic IR.
        # Get the type name of the DSL object
        type_name = dsl_to_semantic_type_name(type(dslobj))
        # Get the constructor for the type
        constructor = getattr(ir, type_name)
        # Handle the parameters
        params = {}
        for param_name, param in constructor.model_fields.items():
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
                            param_value, symbol_table
                        )
                elif semantic_type_name.startswith("dict["):
                    if param_value is None:
                        # If the parameter is None but the annotation is a dict, we will use an empty dict.
                        params[param_name] = {}
                    else:
                        params[param_name] = to_semantic_ir(
                            param_value, symbol_table
                        )
                elif (
                    semantic_type_name != "str"
                    and isinstance(param_value, str)
                    and param_value in dsl_lookup_table
                ):
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

    # Next, we'll build up the semantic representation.
    # This will create a map of all objects by their ID, ensuring that we can resolve
    # references to actual objects.
    symbol_table = {}
    return to_semantic_ir(application, symbol_table)


TYPES_TO_IGNORE = {
    "Document",
    "StrictBaseModel",
    "VariableTypeEnum",
    "DecoderFormat",
    "VariableTypeEnum",
    "VariableType",
    "DecoderFormat",
}
DSL_ONLY_UNION_TYPES = {
    get_args(dsl.ToolType): "Tool",
    get_args(dsl.StepType): "Step",
    get_args(dsl.IndexType): "Index",
    get_args(dsl.ModelType): "Model",
}


def _transform_union_type(args: tuple) -> str:
    """Transform Union types, handling string ID references."""

    args_without_str_none = tuple(
        arg for arg in args if arg is not str and arg is not type(None)
    )
    has_none = any(arg is type(None) for arg in args)
    has_str = any(arg is str for arg in args)

    # First see if this is a DSL-only union type
    # If so, just return the corresponding semantic type
    if args_without_str_none in DSL_ONLY_UNION_TYPES:
        if has_none:
            # If we have a DSL type and None, we return the DSL type with None
            return DSL_ONLY_UNION_TYPES[args_without_str_none] + " | None"
        else:
            # Note we don't handle the case where we have a DSL type and str,
            # because that would indicate a reference to an ID, which we handle separately.
            return DSL_ONLY_UNION_TYPES[args_without_str_none]

    # Handle the case where we have a list | None, which in the dsl is needed, but here we will just have an empty list.
    if len(args) == 2:
        list_elems = [
            arg for arg in args if get_origin(arg) in set([list, dict])
        ]
        if len(list_elems) > 0 and has_none:
            # If we have a list and None, we return the list type
            # This is to handle cases like List[SomeType] | None
            # which in the DSL is needed, but here we will just have an empty list.
            return dsl_to_semantic_type_name(list_elems[0])

    # If the union contains a DSL type and a str, we need to drop the str
    if any(_is_dsl_type(arg) for arg in args) and has_str:
        # There is a DSL type and a str, which indicates something that can reference an ID.
        # drop the str
        args = tuple(arg for arg in args if arg is not str)

    return " | ".join(dsl_to_semantic_type_name(a) for a in args)
