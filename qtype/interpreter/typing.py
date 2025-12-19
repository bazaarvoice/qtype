from __future__ import annotations

import uuid
from typing import Any, Type, get_origin

from pydantic import BaseModel, Field, TypeAdapter, create_model

from qtype.dsl.model import ListType, PrimitiveTypeEnum
from qtype.dsl.model import Variable as DSLVariable
from qtype.dsl.types import PRIMITIVE_TO_PYTHON_TYPE
from qtype.interpreter.types import FlowMessage, Session
from qtype.semantic.model import Flow, Variable


def _get_variable_type(var: DSLVariable) -> tuple[Type, dict[str, Any]]:
    """Get the Python type and metadata for a variable.

    Returns:
        Tuple of (python_type, field_metadata) where field_metadata contains
        information about the original QType type.
    """
    field_metadata = {}

    if isinstance(var.type, PrimitiveTypeEnum):
        python_type = PRIMITIVE_TO_PYTHON_TYPE.get(var.type, str)
        field_metadata["qtype_type"] = var.type.value
    elif isinstance(var.type, ListType):
        python_type = list[
            _get_variable_type(DSLVariable(id="", type=var.type.element_type))[
                0
            ]
        ]
        field_metadata["qtype_type"] = f"list[{var.type.element_type}]"
    elif (
        isinstance(var.type, type)
        and issubclass(var.type, BaseModel)
        and hasattr(var.type, "__name__")
    ):
        python_type = var.type
        field_metadata["qtype_type"] = var.type.__name__
    else:
        raise ValueError(f"Unsupported variable type: {var.type}")

    return python_type, field_metadata


def _fields_from_variables(variables: list[Variable]) -> dict:
    fields = {}
    for var in variables:
        python_type, type_metadata = _get_variable_type(var)

        # Add UI config to schema if present (OpenAPI x- extension pattern)
        if var.ui is not None:
            type_metadata["x-ui"] = var.ui

        field_info = Field(
            title=var.id,
            json_schema_extra=type_metadata,
        )
        fields[var.id] = (python_type, field_info)
    return fields


def create_output_shape(flow: Flow) -> Type[BaseModel]:
    return create_model(
        f"{flow.id}Result",
        __base__=BaseModel,
        **_fields_from_variables(flow.outputs),
    )  # type: ignore


def create_output_container_type(flow: Flow) -> Type[BaseModel]:
    """Dynamically create a Pydantic response model for a flow.

    Always returns a batch-style response with a list of outputs.
    """
    output_shape: Type[BaseModel] = create_output_shape(flow)

    fields: dict[str, tuple[Any, Any]] = {}
    fields["errors"] = (
        list[dict[Any, Any]],
        Field(description="List of errored execution outputs"),
    )
    fields["outputs"] = (
        list[output_shape],
        Field(description="List of successful execution outputs"),
    )
    return create_model(f"{flow.id}Response", __base__=BaseModel, **fields)  # type: ignore


def create_input_shape(flow: Flow) -> Type[BaseModel]:
    """Dynamically create a Pydantic request model for a flow."""
    return create_model(
        f"{flow.id}Request",
        __base__=BaseModel,
        **_fields_from_variables(flow.inputs),
    )  # type: ignore


def request_to_flow_message(request: BaseModel, **kwargs) -> FlowMessage:
    """
    Convert API input data into a FlowMessage for the interpreter.

    Args:
        flow: The flow being executed
        request: Input Request
        session_id: Optional session ID for conversational flows

    Returns:
        FlowMessage ready for execution
    """
    session_id = kwargs.get("session_id", str(uuid.uuid4()))
    conversation_history = kwargs.get("conversation_history", [])

    session = Session(
        session_id=session_id, conversation_history=conversation_history
    )

    variables = {}
    for id in request.model_dump().keys():
        variables[id] = getattr(request, id)

    return FlowMessage(session=session, variables=variables)


def flow_results_to_output_container(
    messages: list[FlowMessage],
    output_shape: Type[BaseModel],
    output_container: Type[BaseModel],
):
    outputs = []
    errors = []
    for m in messages:
        if m.is_failed() and m.error is not None:
            errors.append(m.error.model_dump())
        else:
            output_instance = output_shape(**m.variables)
            outputs.append(output_instance.model_dump())

    return output_container(outputs=outputs, errors=errors)


def instantiate_variable(variable: DSLVariable, value: Any) -> Any:
    """
    Unified contract to ensure data matches its QType definition.
    Handles CustomTypes, DomainTypes, and Primitives.
    """
    target_type, _ = _get_variable_type(variable)

    # 1. Handle the 'Parameterized Generic' Check (The isinstance fix)
    # We check if target_type is a generic (like list[T]) vs a simple class.
    origin = get_origin(target_type)

    if origin is None:
        # It's a simple type (int, RAGChunk, etc.)
        if isinstance(value, target_type):
            return value
    else:
        # It's a generic (list[str], etc.).
        # We skip the identity check and let TypeAdapter handle it.
        pass

    # 2. Handle Pydantic Models (Custom/Domain Types)
    if hasattr(target_type, "model_validate"):
        return target_type.model_validate(value)

    # 3. Handle Primitives & Complex Python Types (List, Optional, Union)
    try:
        # TypeAdapter is the "V2 way" to validate things that aren't
        # full Pydantic models (like List[int] or Optional[str])
        return TypeAdapter(target_type).validate_python(value)
    except Exception:
        # Fallback to your original manual cast if TypeAdapter is overkill
        if isinstance(target_type, type):
            return target_type(value)
        raise ValueError(f"Unsupported target type: {target_type}")
