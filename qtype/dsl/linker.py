from typing import Any, Dict, Type

from pydantic import BaseModel, RootModel

import qtype.base.types as base_types
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
            f"Duplicate component with ID {obj_id} found:\n"
            + str(found_obj.model_dump_json())
            + "\nAlready exists:\n"
            + str(existing_obj.model_dump_json())
        )


class ComponentNotFoundError(QTypeValidationError):
    """Raised when a component is not found in the DSL Application."""

    def __init__(self, component_name: str):
        super().__init__(
            f"Component with name '{component_name}' not found in the DSL Application."
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
        if isinstance(obj, str) or isinstance(obj, base_types.Reference):
            # If the object is a string, we assume it is an ID and skip it.
            # This is a special case where we do not want to add the string itself.
            continue
        # Note: There is no current abstraction for the `id` field, so we assume it exists.
        obj_id = obj.id  # type: ignore[attr-defined]
        # If the object already exists in the map, we check if it is the same object.
        # If it is not the same object, we raise an error.
        # This ensures that we do not have duplicate components with the same ID.
        if obj_id in current_map and id(current_map[obj_id]) != id(obj):
            raise DuplicateComponentError(obj.id, obj, current_map[obj_id])  # type: ignore
        else:
            current_map[obj_id] = obj


def _collect_components_from_object(
    obj: qtype.dsl.domain_types.StrictBaseModel,
) -> list[qtype.dsl.domain_types.StrictBaseModel]:
    """
    Collect all components from an object that have IDs.
    This includes the object itself and any nested components.

    Args:
        obj: The object to extract components from.

    Returns:
        List of components with IDs.
    """
    components = []

    # Add the object itself if it has an ID
    if hasattr(obj, "id"):
        components.append(obj)

    # For Flow, also collect embedded steps, inputs, and outputs
    if isinstance(obj, dsl.Flow):
        components.extend(obj.steps or [])  # type: ignore
        components.extend(obj.inputs or [])  # type: ignore
        components.extend(obj.outputs or [])  # type: ignore

    return components


def _update_maps_with_embedded_objects(
    lookup_map: Dict[str, qtype.dsl.domain_types.StrictBaseModel],
    embedded_objects: list[qtype.dsl.domain_types.StrictBaseModel],
) -> None:
    """
    Update lookup maps with embedded objects.
    Embedded objects are when the user specifies the object and not just the ID.

    Args:
        lookup_maps: The current lookup maps to update.
        embedded_objects: List of embedded objects to add to the maps.
    """
    for obj in embedded_objects:
        components = _collect_components_from_object(obj)
        _update_map_with_unique_check(lookup_map, components)


def _build_lookup_maps(
    document: Any,
    lookup_map: Dict[str, qtype.dsl.domain_types.StrictBaseModel]
    | None = None,
) -> Dict[str, qtype.dsl.domain_types.StrictBaseModel]:
    """
    Build lookup map for all objects in a DSL Document.
    This function creates a dictionary of id -> component, where each key is a
    component id and the value is the component.

    Works with any Document type (Application, Flow, *List types, etc.).

    Args:
        document: The DSL Document to build lookup maps for.
                 Can be Application, Flow, or any RootModel list type.

    Returns:
        Dict[str, dsl.StrictBaseModel]: A dictionary of lookup maps

    Throws:
        QTypeValidationError: If there are duplicate components with the same ID.
    """
    if lookup_map is None:
        lookup_map = {}

    # Handle Application specially since it has multiple component lists
    if isinstance(document, dsl.Application):
        component_names = {
            f
            for f in dsl.Application.model_fields.keys()
            if f not in {"id", "references", "description"}
        }

        for component_name in component_names:
            if not hasattr(document, component_name):
                raise ComponentNotFoundError(component_name)
            components = getattr(document, component_name) or []
            if not isinstance(components, list):
                components = [components]  # Ensure we have a list
            _update_map_with_unique_check(lookup_map, components)
            _update_maps_with_embedded_objects(lookup_map, components)

        # Handle references (which can contain nested Applications or other documents)
        for ref in document.references or []:
            ref = ref.root  # type: ignore
            _build_lookup_maps(ref, lookup_map)

        lookup_map[document.id] = document

    # Handle RootModel list types (e.g., AuthorizationProviderList, IndexList, etc.)
    elif hasattr(document, "root") and isinstance(
        getattr(document, "root"), list
    ):
        root_list = getattr(document, "root")
        _update_map_with_unique_check(lookup_map, root_list)
        _update_maps_with_embedded_objects(lookup_map, root_list)

    # Handle single component documents (e.g., Flow, Agent, etc.)
    else:
        components = _collect_components_from_object(document)
        _update_map_with_unique_check(lookup_map, components)

    return lookup_map


def _resolve_all_references(
    model: BaseModel,
    lookup_map: Dict[str, Any],
):
    """Walks a Pydantic model tree and resolves all Reference objects."""

    def resolve_reference(ref: str, type_hint: Type) -> Any:
        resolved_obj = lookup_map.get(ref)
        if resolved_obj is None:
            raise ReferenceNotFoundError(ref, str(type_hint))
        return resolved_obj

    # Check if this is a RootModel (list-based document like ModelList, ToolList, etc.)
    if isinstance(model, RootModel):
        # For RootModel, __iter__() yields the items directly, not (name, value) tuples
        root_list = model.root  # type: ignore
        if isinstance(root_list, list):
            for i, item in enumerate(root_list):
                if isinstance(item, base_types.Reference):
                    root_list[i] = resolve_reference(item.ref, type(item))
                elif isinstance(item, BaseModel):
                    _resolve_all_references(item, lookup_map)
        return

    # For regular BaseModel types, iterate over fields
    for field_name, field_value in model.__iter__():
        if isinstance(field_value, base_types.Reference):
            setattr(
                model,
                field_name,
                resolve_reference(field_value.ref, type(field_value)),
            )

        elif isinstance(field_value, BaseModel):
            # Recurse into nested models
            _resolve_all_references(field_value, lookup_map)

        elif isinstance(field_value, list) and len(field_value) > 0:
            # Recurse into lists
            for i, item in enumerate(field_value):
                if isinstance(item, base_types.Reference):
                    field_value[i] = resolve_reference(item.ref, type(item))
                elif isinstance(item, BaseModel):
                    _resolve_all_references(item, lookup_map)
        elif isinstance(field_value, dict):
            for k, v in field_value.items():
                if isinstance(v, base_types.Reference):
                    field_value[k] = resolve_reference(v.ref, type(v))
                elif isinstance(v, BaseModel):
                    _resolve_all_references(v, lookup_map)


def link(document: dsl.DocumentType) -> dsl.DocumentType:
    """
    Links (resolves) all ID references in a DSL Document to their actual objects.

    Works with any DocumentType:
    - Application: Full application with all components
    - Flow: Individual flow definition
    - Agent: Individual agent definition
    - AuthorizationProviderList: List of authorization providers
    - IndexList: List of indexes
    - ModelList: List of models
    - ToolList: List of tools
    - TypeList: List of custom types
    - VariableList: List of variables

    IMPORTANT: The returned object breaks the type safety of the original.
    All Reference[T] fields will be replaced with actual T objects, which
    violates the original type signatures. This is intentional for the
    linking phase before transformation to semantic IR.

    Args:
        document: Any valid DSL DocumentType (one of the 9 possible document structures).

    Returns:
        The same document with all internal references resolved to actual objects.

    Raises:
        DuplicateComponentError: If there are duplicate components with the same ID.
        ReferenceNotFoundError: If a reference cannot be resolved.
        ComponentNotFoundError: If an expected component is missing.
    """

    # First, make a lookup map of all objects in the document.
    # This ensures that all object ids are unique.
    lookup_map = _build_lookup_maps(document)

    # Now we resolve all ID references in the document.
    # All DocumentType variants are BaseModel instances (including RootModel-based *List types)
    if isinstance(document, BaseModel):
        _resolve_all_references(document, lookup_map)

    return document  # type: ignore[return-value]
