from __future__ import annotations

import inspect
from datetime import date, datetime, time
from typing import Any, Type, Union, get_args, get_origin

from pydantic import BaseModel

# Assuming the following models are in a file named 'model.py'
# I've copied the necessary definitions from your file for this example to be self-contained.
from qtype.dsl.model import (
    ArrayTypeDefinition,
    ObjectTypeDefinition,
    PrimitiveTypeEnum,
    VariableType,
)

VARIABLE_TO_TYPE = {
    # VariableTypeEnum.audio: bytes, # TODO: Define a proper audio type
    PrimitiveTypeEnum.boolean: bool,  # No boolean type in enum, using Python's
    PrimitiveTypeEnum.bytes: bytes,
    PrimitiveTypeEnum.date: date,
    PrimitiveTypeEnum.datetime: datetime,
    PrimitiveTypeEnum.embedding: list[
        float
    ],  # Assuming embeddings are lists of floats
    PrimitiveTypeEnum.int: int,
    # VariableTypeEnum.file: bytes,  # TODO: Define a proper file type
    # VariableTypeEnum.image: bytes,  # TODO: Define a proper image type
    PrimitiveTypeEnum.float: float,
    PrimitiveTypeEnum.text: str,
    PrimitiveTypeEnum.time: time,
    # VariableTypeEnum.video: bytes,  # TODO: Define a proper video type
}

TYPE_TO_VARIABLE = {v: k for k, v in VARIABLE_TO_TYPE.items()}

assert len(VARIABLE_TO_TYPE) == len(
    TYPE_TO_VARIABLE
), "Variable to type mapping is not one-to-one"


def _map_type_to_dsl(
    pydantic_type: Type[Any], model_name: str
) -> VariableType | str:
    """
    Recursively maps a Python/Pydantic type to a DSL Type Definition.

    Args:
        pydantic_type: The type hint to map (e.g., str, list[int], MyPydanticModel).
        model_name: The name of the model being processed, for generating unique IDs.

    Returns:
        A PrimitiveTypeEnum member, an ObjectTypeDefinition, an ArrayTypeDefinition,
        or a string reference to another type.
    """
    origin = get_origin(pydantic_type)
    args = get_args(pydantic_type)

    # --- Handle Lists ---
    if origin in (list, list):
        if not args:
            raise TypeError(
                "List types must be parameterized, e.g., list[str]."
            )

        # Recursively map the inner type of the list
        inner_type = _map_type_to_dsl(args[0], model_name)

        # Create a unique ID for this specific array definition
        array_id = (
            f"{model_name}.{getattr(inner_type, 'id', str(inner_type))}_Array"
        )

        return ArrayTypeDefinition(
            id=array_id,
            type=inner_type,
            description=f"An array of {getattr(inner_type, 'id', inner_type)}.",
        )

    # --- Handle Unions (specifically for Optional[T]) ---
    if origin is Union:
        # Filter out NoneType to handle Optional[T]
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return _map_type_to_dsl(non_none_args[0], model_name)
        else:
            # For more complex unions, you might decide on a specific handling strategy.
            # For now, we'll raise an error as it's ambiguous.
            raise TypeError(
                "Complex Union types are not supported for automatic conversion."
            )

    # --- Handle Nested Pydantic Models ---
    if inspect.isclass(pydantic_type) and issubclass(pydantic_type, BaseModel):
        # If it's a nested model, recursively call the main function.
        # This returns a full definition for the nested object.
        return pydantic_to_object_definition(pydantic_type)

    # --- Handle Primitive Types ---
    # This could be expanded with more sophisticated mapping.

    if pydantic_type in TYPE_TO_VARIABLE:
        return TYPE_TO_VARIABLE[pydantic_type]

    raise TypeError(f"Unsupported type for DSL conversion: {pydantic_type}")


def pydantic_to_object_definition(
    model_cls: Type[BaseModel],
) -> ObjectTypeDefinition:
    """
    Converts a Pydantic BaseModel class into a QType ObjectTypeDefinition.

    This function introspects the model's fields, recursively converting them
    into the appropriate DSL type definitions (primitive, object, or array).

    Args:
        model_cls: The Pydantic model class to convert.

    Returns:
        An ObjectTypeDefinition representing the Pydantic model.
    """
    properties = {}
    model_name = model_cls.__name__

    for field_name, field_info in model_cls.model_fields.items():
        # Use the annotation (the type hint) for the field
        field_type = field_info.annotation
        if field_type is None:
            raise TypeError(
                f"Field '{field_name}' in '{model_name}' must have a type hint."
            )

        properties[field_name] = _map_type_to_dsl(field_type, model_name)

    return ObjectTypeDefinition(
        id=model_name,
        description=model_cls.__doc__ or f"A definition for {model_name}.",
        properties=properties,
    )
