"""
Semantic resolution logic for QType.

This module contains functions to transform DSL QTypeSpec objects into their
semantic intermediate representation equivalents, where all ID references
are resolved to actual object references.
"""

import inspect
from typing import Any, Dict, Union, get_args, get_origin

import qtype.dsl.model as dsl
from qtype.semantic.errors import SemanticResolutionError


def _update_map_with_unique_check(
    current_map: Dict[str, dsl.StrictBaseModel],
    new_objects,
) -> None:
    """
    Update a map with new objects, ensuring unique IDs.

    Args:
        current_map: The current map of objects by ID.
        new_objects: List of new objects to add to the map.

    Returns:
        Updated map with new objects added, ensuring unique IDs.
    """
    for obj in new_objects:
        if obj is None:
            # If the object is None, we skip it.
            continue
        if isinstance(obj, str):
            # If the object is a string, we assume it is an ID and skip it.
            # This is a special case where we do not want to add the string itself.
            continue
        # Note: There is no current abstraction for the `id` field, so we assume it exists.
        obj_id = obj.id
        # If the object already exists in the map, we check if it is the same object.
        # If it is not the same object, we raise an error.
        # This ensures that we do not have duplicate components with the same ID.
        if obj_id in current_map and id(current_map[obj_id]) != id(obj):
            raise SemanticResolutionError(
                f"Duplicate components with '{obj_id}' found:\n{obj.model_dump_json()}\nAlready exists:\n{current_map[obj_id].model_dump_json()}"
            )
        else:
            current_map[obj_id] = obj


def _update_maps_with_embedded_objects(
    lookup_map: Dict[str, dsl.StrictBaseModel],
    embedded_objects,
) -> None:
    """
    Update lookup maps with embedded objects.
    Embedded objects are when the user specifies the object and not just the ID.
    For example, a prompt template may have variables embedded:
    ```yaml
    steps:
    - id: my_prompt
       variables:
         - id: my_var
           type: text
       outputs:
         - id: my_output
           type: text
    ```

    Args:
        lookup_maps: The current lookup maps to update.
        embedded_objects: List of embedded objects to add to the maps.
    """
    for obj in embedded_objects:
        if isinstance(obj, dsl.Step):
            # All steps have inputs and outputs
            _update_map_with_unique_check(lookup_map, obj.inputs or [])  # type: ignore
            _update_map_with_unique_check(lookup_map, obj.outputs or [])  # type: ignore
            _update_map_with_unique_check(lookup_map, [obj])

        if isinstance(obj, dsl.Model):
            # note inputs/
            _update_map_with_unique_check(lookup_map, [obj.auth])

        if isinstance(obj, dsl.Condition):
            # Conditions have inputs and outputs
            _update_map_with_unique_check(lookup_map, [obj.then, obj.else_])
            _update_map_with_unique_check(lookup_map, [obj.equals])
            if obj.then and isinstance(obj.then, dsl.Step):
                _update_maps_with_embedded_objects(lookup_map, obj.then)
            if obj.else_ and isinstance(obj.else_, dsl.Step):
                _update_maps_with_embedded_objects(lookup_map, obj.else_)

        if isinstance(obj, dsl.APITool):
            # API tools have inputs and outputs
            _update_map_with_unique_check(lookup_map, [obj.auth])

        if isinstance(obj, dsl.LLMInference):
            # LLM Inference steps have inputs and outputs
            _update_map_with_unique_check(lookup_map, [obj.model])
            _update_map_with_unique_check(lookup_map, [obj.memory])

        if isinstance(obj, dsl.Agent):
            _update_map_with_unique_check(lookup_map, obj.tools or [])
            _update_maps_with_embedded_objects(lookup_map, obj.tools or [])

        if isinstance(obj, dsl.Flow):
            _update_map_with_unique_check(lookup_map, [obj])
            _update_map_with_unique_check(lookup_map, obj.steps or [])
            _update_maps_with_embedded_objects(lookup_map, obj.steps or [])

        if isinstance(obj, dsl.TelemetrySink):
            # Telemetry sinks may have auth references
            _update_map_with_unique_check(lookup_map, [obj.auth])

        if isinstance(obj, dsl.Index):
            # Indexes may have auth references
            _update_map_with_unique_check(lookup_map, [obj.auth])

        if isinstance(obj, dsl.VectorIndex):
            if isinstance(obj.embedding_model, dsl.EmbeddingModel):
                _update_map_with_unique_check(
                    lookup_map, [obj.embedding_model]
                )
                _update_maps_with_embedded_objects(
                    lookup_map, [obj.embedding_model]
                )

        if isinstance(obj, dsl.Search):
            if isinstance(obj.index, dsl.Index):
                _update_map_with_unique_check(lookup_map, [obj.index])
                _update_maps_with_embedded_objects(lookup_map, [obj.index])

        if isinstance(obj, dsl.AuthorizationProviderList):
            # AuthorizationProviderList is a list of AuthorizationProvider objects
            _update_map_with_unique_check(lookup_map, obj.root)
            _update_maps_with_embedded_objects(lookup_map, obj.root)

        if isinstance(obj, dsl.IndexList):
            # IndexList is a list of Index objects
            _update_map_with_unique_check(lookup_map, obj.root)
            _update_maps_with_embedded_objects(lookup_map, obj.root)

        if isinstance(obj, dsl.ModelList):
            # ModelList is a list of Model objects
            _update_map_with_unique_check(lookup_map, obj.root)
            _update_maps_with_embedded_objects(lookup_map, obj.root)

        if isinstance(obj, dsl.ToolList):
            # ToolList is a list of Tool objects
            _update_map_with_unique_check(lookup_map, obj.root)
            _update_maps_with_embedded_objects(lookup_map, obj.root)

        if isinstance(obj, dsl.VariableList):
            # VariableList is a list of Variable objects
            _update_map_with_unique_check(lookup_map, obj.root)


def _build_lookup_maps(
    dsl_application: dsl.Application,
    lookup_map: Dict[str, dsl.StrictBaseModel] | None = None,
) -> Dict[str, dsl.StrictBaseModel]:
    """
    Build lookup map for all objects in the DSL Application.
    This function creates a dictionary of id -> component, where each key is a
    component id and the value is the component.
    Args:
        dsl_application: The DSL Application to build lookup maps for.
    Returns:
        Dict[str, dsl.StrictBaseModel]: A dictionary of lookup maps
    Throws:
        SemanticResolutionError: If there are duplicate components with the same ID.
    """
    component_names = {
        f
        for f in dsl.Application.model_fields.keys()
        if f not in set(["id", "references"])
    }

    if lookup_map is None:
        lookup_map = {}

    for component_name in component_names:
        if not hasattr(dsl_application, component_name):
            raise SemanticResolutionError(
                f"Component '{component_name}' not found in the DSL Application."
            )
        components = getattr(dsl_application, component_name) or []
        if not isinstance(components, list):
            components = [components]  # Ensure we have a list
        _update_map_with_unique_check(lookup_map, components)
        _update_maps_with_embedded_objects(lookup_map, components)

    # now deal with the references.
    for ref in dsl_application.references or []:
        if isinstance(ref, dsl.Application):
            _build_lookup_maps(ref, lookup_map)

    # Anything in the reference list that is not an Application is handled by the embedded object resolver.
    _update_maps_with_embedded_objects(
        lookup_map,
        [
            ref
            for ref in dsl_application.references or []
            if not isinstance(ref, dsl.Application)
        ],
    )

    return lookup_map


def _is_dsl_type(type_obj: Any) -> bool:
    """Check if a type is a DSL type that should be converted to semantic."""
    if not hasattr(type_obj, "__name__"):
        return False

    # Check if it's defined in the DSL module
    return (
        hasattr(type_obj, "__module__")
        and type_obj.__module__ == dsl.__name__
        and not type_obj.__name__.startswith("_")
    )


def validate(
    dsl_application: dsl.Application,
) -> Dict[str, dsl.StrictBaseModel]:
    """
    Validate the semantics of a DSL Application and return its IR representation.

    Args:
        dsl_application: The DSL Application to validate.

    Returns:
        Dict[str, dsl.StrictBaseModel]: A dictionary of lookup maps for the DSL Application.
    Throws:
        SemanticResolutionError: If there are semantic errors in the DSL Application.
    """
    return _build_lookup_maps(dsl_application)


# These types are used only for the DSL and should not be converted to semantic types
# They are used for JSON schema generation
# They will be switched to their semantic abstract class in the generation.
# i.e., `ToolType` will be switched to `Tool`
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


TYPES_TO_IGNORE = {
    "Document",
    "StrictBaseModel",
    "VariableTypeEnum",
    "DecoderFormat",
    "VariableTypeEnum",
    "VariableType",
    "DecoderFormat",
}


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
