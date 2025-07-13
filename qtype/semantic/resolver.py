"""
Semantic resolution logic for QType.

This module contains functions to transform DSL QTypeSpec objects into their
semantic intermediate representation equivalents, where all ID references
are resolved to actual object references.
"""

from typing import Any, Dict, List

import qtype.dsl.model as dsl


class SemanticResolutionError(Exception):
    """Raised when there's an error during semantic resolution."""

    pass


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
    lookup_maps: Dict[str, Dict[str, dsl.StrictBaseModel]],
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
            _update_map_with_unique_check(
                lookup_maps["variables"], obj.inputs or []
            )  # type: ignore
            _update_map_with_unique_check(
                lookup_maps["variables"], obj.outputs or []
            )  # type: ignore
            _update_map_with_unique_check(lookup_maps["steps"], [obj])

        if isinstance(obj, dsl.Model):
            # note inputs/
            _update_map_with_unique_check(lookup_maps["auths"], [obj.auth])

        if isinstance(obj, dsl.Condition):
            # Conditions have inputs and outputs
            _update_map_with_unique_check(
                lookup_maps["steps"], [obj.then, obj.else_]
            )
            _update_map_with_unique_check(
                lookup_maps["variables"], [obj.equals]
            )
            if obj.then and isinstance(obj.then, dsl.Step):
                _update_maps_with_embedded_objects(lookup_maps, obj.then)
            if obj.else_ and isinstance(obj.else_, dsl.Step):
                _update_maps_with_embedded_objects(lookup_maps, obj.else_)

        if isinstance(obj, dsl.APITool):
            # API tools have inputs and outputs
            _update_map_with_unique_check(lookup_maps["auths"], [obj.auth])

        if isinstance(obj, dsl.LLMInference):
            # LLM Inference steps have inputs and outputs
            _update_map_with_unique_check(lookup_maps["models"], [obj.model])
            _update_map_with_unique_check(
                lookup_maps["memories"], [obj.memory]
            )

        if isinstance(obj, dsl.Agent):
            _update_map_with_unique_check(
                lookup_maps["tools"], obj.tools or []
            )
            _update_maps_with_embedded_objects(lookup_maps, obj.tools or [])

        if isinstance(obj, dsl.Flow):
            _update_map_with_unique_check(lookup_maps["flows"], [obj])
            _update_map_with_unique_check(
                lookup_maps["steps"], obj.steps or []
            )
            _update_maps_with_embedded_objects(lookup_maps, obj.steps or [])

        if isinstance(obj, dsl.TelemetrySink):
            # Telemetry sinks may have auth references
            _update_map_with_unique_check(lookup_maps["auths"], [obj.auth])

        if isinstance(obj, dsl.Index):
            # Indexes may have auth references
            _update_map_with_unique_check(lookup_maps["auths"], [obj.auth])

        if isinstance(obj, dsl.VectorIndex):
            if isinstance(obj.embedding_model, dsl.EmbeddingModel):
                _update_map_with_unique_check(
                    lookup_maps["models"], [obj.embedding_model]
                )
                _update_maps_with_embedded_objects(
                    lookup_maps, [obj.embedding_model]
                )

        if isinstance(obj, dsl.Search):
            if isinstance(obj.index, dsl.Index):
                _update_map_with_unique_check(
                    lookup_maps["indexes"], [obj.index]
                )
                _update_maps_with_embedded_objects(lookup_maps, [obj.index])

        if isinstance(obj, dsl.AuthorizationProviderList):
            # AuthorizationProviderList is a list of AuthorizationProvider objects
            _update_map_with_unique_check(lookup_maps["auths"], obj.root)
            _update_maps_with_embedded_objects(lookup_maps, obj.root)

        if isinstance(obj, dsl.IndexList):
            # IndexList is a list of Index objects
            _update_map_with_unique_check(lookup_maps["indexes"], obj.root)
            _update_maps_with_embedded_objects(lookup_maps, obj.root)

        if isinstance(obj, dsl.ModelList):
            # ModelList is a list of Model objects
            _update_map_with_unique_check(lookup_maps["models"], obj.root)
            _update_maps_with_embedded_objects(lookup_maps, obj.root)

        if isinstance(obj, dsl.ToolList):
            # ToolList is a list of Tool objects
            _update_map_with_unique_check(lookup_maps["tools"], obj.root)
            _update_maps_with_embedded_objects(lookup_maps, obj.root)

        if isinstance(obj, dsl.VariableList):
            # VariableList is a list of Variable objects
            _update_map_with_unique_check(lookup_maps["variables"], obj.root)


def _build_lookup_maps(
    dsl_application: dsl.Application,
    lookup_maps: Dict[str, Dict[str, dsl.StrictBaseModel]] | None = None,
) -> Dict[str, Dict[str, dsl.StrictBaseModel]]:
    """
    Build lookup maps for all objects in the DSL Application.
    This function creates a dictionary of dictionaries, where each key is a
    component type (e.g., "models", "variables", etc.) and the value is
    a dictionary mapping IDs to the corresponding objects.
    Args:
        dsl_application: The DSL Application to build lookup maps for.
    Returns:
        Dict[str, Dict[str, dsl.StrictBaseModel]]: A dictionary of lookup maps
    """
    map_keys = [
        f
        for f in dsl.Application.model_fields.keys()
        if f not in set(["id", "references"])
    ]

    # Add steps which are not part of the application, but are used in flows.
    map_keys.append("steps")

    # Generate a lookup map for each key in the application
    # This will allow us to resolve references to actual objects later.
    # We will also ensure that each map has unique IDs for its objects.
    if lookup_maps is None:
        lookup_maps = {key: {} for key in map_keys}
    for key, lookup_map in lookup_maps.items():
        if key == "steps":
            # Steps are not part of the application, but are used in flows.
            # We will handle them separately.
            continue
        components = getattr(dsl_application, key) or []
        if not isinstance(components, list):
            components = [components]  # Ensure we have a list
        _update_map_with_unique_check(lookup_map, components)

        # Handle any embedded objects in the application.
        _update_maps_with_embedded_objects(lookup_maps, components)

    # now deal with the references. These are a bit more complex because they can reference multiple types.
    for ref in dsl_application.references or []:
        if isinstance(ref, dsl.Application):
            _build_lookup_maps(ref, lookup_maps)

    # Anything in the reference list that is not an Application is handled by the embedded object resolver.
    _update_maps_with_embedded_objects(
        lookup_maps,
        [
            ref
            for ref in dsl_application.references or []
            if not isinstance(ref, dsl.Application)
        ],
    )

    return lookup_maps


def resolve(application: dsl.Application) -> dsl.Application:
    """
    Resolve a DSL Application into its semantic intermediate representation.

    This function transforms the DSL Application into its IR equivalent,
    resolving all ID references to actual object references.

    Args:
        application: The DSL Application to transform

    Returns:
        dsl.Application: The resolved IR application
    """

    # First, resolve the lookup maps. This will also ensure everything has a unique ID.
    lookup_maps = _build_lookup_maps(application)

    # Next, replace any reference with the actual objects.

    # We'll return the same type of object, but with all references resolved.
    # This allows us to use the same type system for both DSL and IR, while
    # ensuring that the IR is fully resolved and ready for execution or further processing.
    return application