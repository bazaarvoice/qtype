from typing import Any, Dict, Union, get_args, get_origin

import qtype.dsl.base_types as base_types
import qtype.dsl.domain_types
import qtype.dsl.model as dsl


class QTypeValidationError(Exception):
    """Raised when there's an error during QType validation."""

    pass


class DuplicateComponentError(QTypeValidationError):
    """Raised when there are duplicate components with the same ID."""

    def __init__(
        self,
        obj_id: str,
        found_obj: qtype.dsl.domain_types.StrictBaseModel,
        existing_obj: qtype.dsl.domain_types.StrictBaseModel,
    ):
        super().__init__(
            f"Duplicate component with ID '{obj_id}' found:\n{found_obj.model_dump_json()}\nAlready exists:\n{existing_obj.model_dump_json()}"
        )


class ComponentNotFoundError(QTypeValidationError):
    """Raised when a component is not found in the DSL Application."""

    def __init__(self, component_id: str):
        super().__init__(
            f"Component with ID '{component_id}' not found in the DSL Application."
        )


class ReferenceNotFoundError(QTypeValidationError):
    """Raised when a reference is not found in the lookup map."""

    def __init__(self, reference: str, type_hint: str | None = None):
        msg = (
            f"Reference '{reference}' not found in lookup map."
            if type_hint is None
            else f"Reference '{reference}' not found in lookup map for type '{type_hint}'."
        )
        super().__init__(msg)


class FlowHasNoStepsError(QTypeValidationError):
    """Raised when a flow has no steps defined."""

    def __init__(self, flow_id: str):
        super().__init__(f"Flow {flow_id} has no steps defined.")


# These types are used only for the DSL and should not be converted to semantic types
# They are used for JSON schema generation
# They will be switched to their semantic abstract class in the generation.
# i.e., `ToolType` will be switched to `Tool`
def _update_map_with_unique_check(
    current_map: Dict[str, qtype.dsl.domain_types.StrictBaseModel],
    new_objects: list[qtype.dsl.domain_types.StrictBaseModel],
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
            raise DuplicateComponentError(obj_id, obj, current_map[obj_id])
        else:
            current_map[obj_id] = obj


def _update_maps_with_embedded_objects(
    lookup_map: Dict[str, qtype.dsl.domain_types.StrictBaseModel],
    embedded_objects: list[qtype.dsl.domain_types.StrictBaseModel],
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
            # note inputs
            _update_map_with_unique_check(lookup_map, [obj.auth])  # type: ignore

        if isinstance(obj, dsl.Condition):
            # Conditions have inputs and outputs
            _update_map_with_unique_check(lookup_map, [obj.then, obj.else_])  # type: ignore
            _update_map_with_unique_check(lookup_map, [obj.equals])  # type: ignore
            if obj.then and isinstance(obj.then, dsl.Step):
                _update_maps_with_embedded_objects(lookup_map, [obj.then])
            if obj.else_ and isinstance(obj.else_, dsl.Step):
                _update_maps_with_embedded_objects(lookup_map, [obj.else_])

        if isinstance(obj, dsl.APITool):
            # API tools have inputs and outputs
            _update_map_with_unique_check(lookup_map, [obj.auth])  # type: ignore

        if isinstance(obj, dsl.LLMInference):
            # LLM Inference steps have inputs and outputs
            _update_map_with_unique_check(lookup_map, [obj.model])  # type: ignore
            _update_maps_with_embedded_objects(lookup_map, [obj.model])  # type: ignore
            _update_map_with_unique_check(lookup_map, [obj.memory])  # type: ignore

        if isinstance(obj, dsl.Agent):
            _update_map_with_unique_check(lookup_map, obj.tools or [])  # type: ignore
            _update_maps_with_embedded_objects(lookup_map, obj.tools or [])  # type: ignore

        if isinstance(obj, dsl.Flow):
            _update_map_with_unique_check(lookup_map, [obj])
            _update_map_with_unique_check(lookup_map, obj.steps or [])  # type: ignore
            _update_maps_with_embedded_objects(lookup_map, obj.steps or [])  # type: ignore

        if isinstance(obj, dsl.TelemetrySink):
            # Telemetry sinks may have auth references
            _update_map_with_unique_check(lookup_map, [obj.auth])  # type: ignore

        if isinstance(obj, dsl.Index):
            # Indexes may have auth references
            _update_map_with_unique_check(lookup_map, [obj.auth])  # type: ignore

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
            _update_map_with_unique_check(lookup_map, obj.root)  # type: ignore
            _update_maps_with_embedded_objects(lookup_map, obj.root)  # type: ignore

        if isinstance(obj, dsl.IndexList):
            # IndexList is a list of Index objects
            _update_map_with_unique_check(lookup_map, obj.root)  # type: ignore
            _update_maps_with_embedded_objects(lookup_map, obj.root)  # type: ignore

        if isinstance(obj, dsl.ModelList):
            # ModelList is a list of Model objects
            _update_map_with_unique_check(lookup_map, obj.root)  # type: ignore
            _update_maps_with_embedded_objects(lookup_map, obj.root)  # type: ignore

        if isinstance(obj, dsl.ToolList):
            # ToolList is a list of Tool objects
            _update_map_with_unique_check(lookup_map, obj.root)  # type: ignore
            _update_maps_with_embedded_objects(lookup_map, obj.root)  # type: ignore

        if isinstance(obj, dsl.TypeList):
            # TypeList is a list of Type objects
            _update_map_with_unique_check(lookup_map, obj.root)  # type: ignore

        if isinstance(obj, dsl.VariableList):
            # VariableList is a list of Variable objects
            _update_map_with_unique_check(lookup_map, obj.root)  # type: ignore

        if isinstance(obj, dsl.TelemetrySink):
            # TelemetrySink is a list of TelemetrySink objects
            _update_map_with_unique_check(lookup_map, [obj.auth])  # type: ignore


def _build_lookup_maps(
    dsl_application: dsl.Application,
    lookup_map: Dict[str, qtype.dsl.domain_types.StrictBaseModel]
    | None = None,
) -> Dict[str, qtype.dsl.domain_types.StrictBaseModel]:
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
            raise ComponentNotFoundError(component_name)
        components = getattr(dsl_application, component_name) or []
        if not isinstance(components, list):
            components = [components]  # Ensure we have a list
        _update_map_with_unique_check(lookup_map, components)
        _update_maps_with_embedded_objects(lookup_map, components)

    # now deal with the references.
    for ref in dsl_application.references or []:
        ref = ref.root  # type: ignore
        if isinstance(ref, dsl.Application):
            _build_lookup_maps(ref, lookup_map)

    # Anything in the reference list that is not an Application is handled by the embedded object resolver.
    _update_maps_with_embedded_objects(
        lookup_map,
        [
            ref.root  # type: ignore
            for ref in dsl_application.references or []
            if not isinstance(ref.root, dsl.Application)
        ],  # type: ignore
    )

    lookup_map[dsl_application.id] = dsl_application

    return lookup_map


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


def _is_union(type: Any) -> bool:
    """
    Indicates if the provided type is a Union type.
    """
    origin = get_origin(type)
    return origin is Union or (
        hasattr(type, "__class__") and type.__class__.__name__ == "UnionType"
    )


def _is_reference_type(field_type: Any) -> bool:
    """
    Indicates if the provided type can be a reference -- i.e., a union between a dsl type and a string.
    """
    field_type = _resolve_forward_ref(field_type)

    if _is_union(field_type):
        args = get_args(field_type)
        has_str = any(arg is str for arg in args)
        has_dsl_type = any(_is_dsl_type(arg) for arg in args)
        return has_str and has_dsl_type
    else:
        return False


def _resolve_id_references(
    dslobj: qtype.dsl.domain_types.StrictBaseModel | str,
    lookup_map: Dict[str, qtype.dsl.domain_types.StrictBaseModel],
) -> Any:
    """
    Resolves ID references in a DSL object such that all references are replaced with the actual object.
    """

    if isinstance(dslobj, str):
        # If the object is a string, we assume it is an ID and look it up in the map.
        if dslobj in lookup_map:
            return lookup_map[dslobj]
        else:
            raise ReferenceNotFoundError(dslobj)

    # iterate over all fields in the object
    def lookup_reference(val: str, typ: Any) -> Any:
        if (
            isinstance(val, str)
            and _is_reference_type(typ)
            and not _is_dsl_type(type(val))
        ):
            if val in lookup_map:
                return lookup_map[val]
            else:
                raise ReferenceNotFoundError(val, str(typ))
        return val

    for field_name, field_value in dslobj:
        field_info = dslobj.__class__.model_fields[field_name]
        field_type = _resolve_forward_ref(field_info.annotation)

        if isinstance(field_value, list):
            # If the field value is a list, resolve each item in the list
            # Get the type of the items of the list
            field_type = field_type.__args__[0]  # type: ignore
            if (
                get_origin(field_type) is list
            ):  # handles case where we have list[Class] | None -- in this case field_type is Union and item_type is now the list...
                field_type = field_type.__args__[0]
            resolved_list = [
                lookup_reference(item, field_type)  # type: ignore
                for item in field_value
            ]
            setattr(dslobj, field_name, resolved_list)
        elif isinstance(field_value, dict):
            field_type = field_type.__args__[0]
            if (
                get_origin(field_type) is dict
            ):  # handles case where we have dict[Class] | None -- in this case field_type is Union and item_type is now the dict...
                field_type = field_type.__args__[1]
            # If the field value is a dict, resolve each value in the dict
            resolved_dict = {
                k: lookup_reference(v, field_type)  # type: ignore
                for k, v in field_value.items()
            }
            setattr(dslobj, field_name, resolved_dict)
        elif field_value is None:
            # Convert lst | None to an empty list
            # and dict | None to an empty dict
            if _is_union(field_type):
                args = field_type.__args__  # type: ignore
                if any(str(arg).startswith("list") for arg in args):
                    setattr(dslobj, field_name, [])
                elif any(str(arg).startswith("dict") for arg in args):
                    setattr(dslobj, field_name, {})
        else:
            setattr(
                dslobj, field_name, lookup_reference(field_value, field_type)
            )

    return dslobj


def validate(
    dsl_application: dsl.Application,
) -> dsl.Application:
    """
    Validates the semantics of a DSL Application and returns a copy of it with all
    internal references resolved to their actual objects.
    Args:
        dsl_application: The DSL Application to validate.
    Returns:
        dsl.Application: A copy of the DSL Application with all internal references resolved.
    Throws:
        SemanticResolutionError: If there are semantic errors in the DSL Application.
    """

    # First, make a lookup map of all objects in the DSL Application.
    # This ensures that all object ids are unique.
    lookup_map = _build_lookup_maps(dsl_application)

    # If any flows have no steps, we raise an error.
    for flow in dsl_application.flows or []:
        if not flow.steps:
            raise FlowHasNoStepsError(flow.id)
        # If any flow doesn't have inputs, copy the inputs from the first step.
        if not flow.inputs:
            first_step = (
                lookup_map[flow.steps[0]]
                if isinstance(flow.steps[0], str)
                else flow.steps[0]
            )
            flow.inputs = first_step.inputs or []  # type: ignore

        # If any flow doesn't have outputs, copy them from the last step.
        if not flow.outputs:
            last_step = (
                lookup_map[flow.steps[-1]]
                if isinstance(flow.steps[-1], str)
                else flow.steps[-1]
            )
            flow.outputs = last_step.outputs or []  # type: ignore

    # Now we resolve all ID references in the DSL Application.
    lookup_map = {
        obj_id: _resolve_id_references(obj, lookup_map)
        for obj_id, obj in lookup_map.items()
    }

    return dsl_application
