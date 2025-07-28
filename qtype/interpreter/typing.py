from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel, Field, create_model

from qtype.converters.types import PRIMITIVE_TO_PYTHON_TYPE
from qtype.dsl.model import DOMAIN_CLASSES, PrimitiveTypeEnum
from qtype.semantic.model import Flow, Variable


def _get_variable_type(var: Variable) -> Type:
    if isinstance(var.type, PrimitiveTypeEnum):
        return PRIMITIVE_TO_PYTHON_TYPE.get(var.type, str)
    elif var.type.__name__ in DOMAIN_CLASSES:
        return DOMAIN_CLASSES[var.type.__name__]
    else:
        # TODO: handle custom TypeDefinition...
        raise ValueError(f"Unsupported variable type: {var.type}")


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
            python_type = _get_variable_type(var)
            field_info = Field(
                description=f"Output for {var.id}",
                title=var.id,
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
        python_type = _get_variable_type(var)  # type: ignore
        field_info = Field(
            description=f"Input for {var.id}",
            title=var.id,
        )
        fields[var.id] = (python_type, field_info)

    return create_model(f"{flow.id}Request", __base__=BaseModel, **fields)  # type: ignore
