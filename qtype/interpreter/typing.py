from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel, Field, create_model

from qtype.converters.types import PRIMITIVE_TO_PYTHON_TYPE
from qtype.dsl.model import PrimitiveTypeEnum
from qtype.semantic.model import Flow, Variable


def _get_variable_type(var: Variable) -> tuple[Type, dict[str, Any]]:
    """Get the Python type and metadata for a variable.

    Returns:
        Tuple of (python_type, field_metadata) where field_metadata contains
        information about the original QType type.
    """
    field_metadata = {}

    if isinstance(var.type, PrimitiveTypeEnum):
        python_type = PRIMITIVE_TO_PYTHON_TYPE.get(var.type, str)
        field_metadata["qtype_type"] = var.type.value
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


def create_output_type_model(flow: Flow) -> Type[BaseModel]:
    """Dynamically create a Pydantic response model for a flow."""
    fields = {}

    # Always include flow_id and status
    fields["flow_id"] = (str, Field(description="ID of the executed flow"))
    fields["status"] = (str, Field(description="Execution status"))

    # Add dynamic output fields
    if flow.outputs:
        output_fields = {}
        for var in flow.outputs:
            python_type, type_metadata = _get_variable_type(var)
            field_info = Field(
                # TODO: grok the description from the variable if available
                # description=f"Output for {var.id}",
                title=var.id,
                json_schema_extra=type_metadata,
            )
            output_fields[var.id] = (python_type, field_info)

        # Create nested outputs model
        outputs_model = create_model(
            f"{flow.id}Outputs",
            __base__=BaseModel,
            **output_fields,
        )  # type: ignore
        fields["outputs"] = (
            outputs_model,
            Field(description="Flow execution outputs"),
        )
    else:
        fields["outputs"] = (
            dict[str, Any],
            Field(description="Flow execution outputs"),
        )  # type: ignore

    return create_model(f"{flow.id}Response", __base__=BaseModel, **fields)  # type: ignore


def create_input_type_model(flow: Flow) -> Type[BaseModel]:
    """Dynamically create a Pydantic request model for a flow."""
    if not flow.inputs:
        # Return a simple model with no required fields
        return create_model(
            f"{flow.id}Request",
            __base__=BaseModel,
        )

    fields = {}
    for var in flow.inputs:
        python_type, type_metadata = _get_variable_type(var)
        field_info = Field(
            # TODO: grok the description from the variable if available
            # description=f"Input for {var.id}",
            title=var.id,
            json_schema_extra=type_metadata,
        )
        fields[var.id] = (python_type, field_info)

    return create_model(f"{flow.id}Request", __base__=BaseModel, **fields)  # type: ignore
