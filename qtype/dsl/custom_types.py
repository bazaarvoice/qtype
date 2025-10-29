from typing import Any, ForwardRef, Type, Union

from pydantic import BaseModel, create_model

from qtype.dsl.types import PRIMITIVE_TO_PYTHON_TYPE

# --- This would be in your interpreter's logic ---


def build_dynamic_types(
    type_definitions: list[dict],
) -> dict[str, Type[BaseModel]]:
    """
    Parses a list of simplified type definitions and dynamically creates
    Pydantic BaseModel classes. It handles out-of-order definitions using
    a two-pass approach with ForwardRef.
    """
    created_models: dict[str, Type[BaseModel]] = {}

    PRIMITIVE_MAP = {k.value: v for k, v in PRIMITIVE_TO_PYTHON_TYPE.items()}

    def _parse_type_string(type_str: str) -> tuple[Any, bool]:
        """
        Parses a type string and returns the resolved type and a boolean
        indicating if the type is optional.
        """
        is_optional = False
        if type_str.endswith("?"):
            is_optional = True
            type_str = type_str[:-1]

        if type_str.startswith("list[") and type_str.endswith("]"):
            inner_type_name = type_str[5:-1]
            inner_type, _ = _parse_type_string(inner_type_name)
            resolved_type: Any = list[inner_type]  # type: ignore[misc, valid-type]
        elif type_str in PRIMITIVE_MAP:
            resolved_type = PRIMITIVE_MAP[type_str]
        elif type_str in created_models:
            resolved_type = created_models[type_str]
        else:
            # If the type isn't defined yet, create a ForwardRef placeholder.
            # This is the key to handling out-of-order definitions.
            resolved_type = ForwardRef(type_str)

        if is_optional:
            return Union[resolved_type, None], True

        return resolved_type, False

    # --- Pass 1: Create all models, using ForwardRef for unresolved types ---
    for type_def in type_definitions:
        model_name = type_def["id"]
        field_definitions = {}

        if "properties" in type_def:
            for field_name, type_str in type_def["properties"].items():
                resolved_type, is_optional = _parse_type_string(type_str)
                default_value = None if is_optional else ...
                field_definitions[field_name] = (resolved_type, default_value)

        # Pass the created_models dict as the local namespace for resolution
        DynamicModel = create_model(
            model_name,
            **field_definitions,
            __localns=created_models,  # type: ignore[call-overload]
        )
        created_models[model_name] = DynamicModel

    # --- Pass 2: Resolve all ForwardRef placeholders ---
    # This rebuilds the models, linking the placeholders to the actual classes.
    # We pass `created_models` as the types_namespace for resolution in Pydantic V2.
    for model in created_models.values():
        model.model_rebuild(_types_namespace=created_models)

    return created_models
