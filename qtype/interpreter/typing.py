from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel, Field, create_model

from qtype.application.converters.types import PRIMITIVE_TO_PYTHON_TYPE
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


def create_output_type_model(
    flow: Flow, is_batch: bool = False
) -> Type[BaseModel]:
    """Dynamically create a Pydantic response model for a flow."""
    fields: dict[str, tuple[Any, Any]] = {}

    # Always include flow_id and status
    fields["flow_id"] = (str, Field(description="ID of the executed flow"))
    fields["status"] = (str, Field(description="Execution status"))

    if is_batch:
        # Include information about the number of results, errors, etc.
        fields["num_inputs"] = (int, Field(description="Number of inputs."))
        fields["num_results"] = (int, Field(description="Number of results."))
        fields["num_errors"] = (int, Field(description="Number of errors."))
        fields["errors"] = (
            list[dict[Any, Any]],
            Field(description="All inputs with their associated errors."),
        )

    # Add dynamic output fields
    if flow.outputs:
        output_fields = {}
        for var in flow.outputs:
            python_type, type_metadata = _get_variable_type(var)

            # Make type optional for batch processing since rows might have missing values
            if is_batch:
                from typing import Union

                python_type = Union[python_type, type(None)]  # type: ignore

            field_info = Field(
                # TODO: grok the description from the variable if available
                # description=f"Output for {var.id}",
                title=var.id,
                json_schema_extra=type_metadata,
            )
            output_fields[var.id] = (python_type, field_info)

        # Create nested outputs model
        outputs_model: Type[BaseModel] = create_model(
            f"{flow.id}Outputs",
            __base__=BaseModel,
            **output_fields,
        )  # type: ignore
        if is_batch:
            fields["outputs"] = (
                list[outputs_model],  # type: ignore
                Field(description="List of flow execution outputs"),
            )
        else:
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


def create_input_type_model(flow: Flow, is_batch: bool) -> Type[BaseModel]:
    """Dynamically create a Pydantic request model for a flow."""
    if not flow.inputs and not is_batch:
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

    if is_batch:
        # For batch processing, wrap inputs in a list
        single_input_model: Type[BaseModel] = create_model(
            f"{flow.id}SingleInput", __base__=BaseModel, **fields
        )  # type: ignore
        fields = {
            "inputs": (
                list[single_input_model],  # type: ignore
                Field(description="List of inputs for batch processing"),
            )
        }

    return create_model(f"{flow.id}Request", __base__=BaseModel, **fields)  # type: ignore
