from __future__ import annotations

from typing import Any, Optional, Type

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, create_model

from qtype.converters.types import PRIMITIVE_TO_PYTHON_TYPE
from qtype.dsl.model import DOMAIN_CLASSES, PrimitiveTypeEnum
from qtype.interpreter.flow import execute_flow
from qtype.semantic.model import Application, Flow, Variable


def _get_variable_type(var: Variable) -> Type:
    if isinstance(var.type, PrimitiveTypeEnum):
        return PRIMITIVE_TO_PYTHON_TYPE.get(var.type, str)
    elif var.type.__name__ in DOMAIN_CLASSES:
        return DOMAIN_CLASSES[var.type.__name__]
    else:
        # TODO: handle custom TypeDefinition...
        raise ValueError(f"Unsupported variable type: {var.type}")


def _create_request_model(flow: Flow) -> Type[BaseModel]:
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

    return create_model(f"{flow.id}Request", __base__=BaseModel, **fields)


def _create_response_model(flow: Flow) -> Type[BaseModel]:
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
        )
        fields["outputs"] = (
            outputs_model,
            Field(description="Flow execution outputs"),
        )
    else:
        fields["outputs"] = (
            dict[str, Any],
            Field(description="Flow execution outputs"),
        )

    return create_model(f"{flow.id}Response", __base__=BaseModel, **fields)


class APIExecutor:
    """API executor for QType definitions with dynamic endpoint generation."""

    def __init__(
        self,
        definition: Application,
        host: str = "localhost",
        port: int = 8000,
    ):
        self.definition = definition
        self.host = host
        self.port = port

    def create_app(self, name: Optional[str]) -> FastAPI:
        """Create FastAPI app with dynamic endpoints."""
        app = FastAPI(
            title=name or "QType API",
            docs_url="/docs",  # Swagger UI
            redoc_url="/redoc",
        )

        flows = self.definition.flows if self.definition.flows else []

        # Dynamically generate POST endpoints for each flow
        for flow in flows:
            self._create_flow_endpoint(app, flow)

        return app

    def _create_flow_endpoint(self, app: FastAPI, flow: Flow) -> None:
        """Create a dynamic POST endpoint for a specific flow."""
        flow_id = flow.id

        # Create dynamic request and response models for this flow
        RequestModel = _create_request_model(flow)
        ResponseModel = _create_response_model(flow)

        # Create the endpoint function with proper model binding
        def execute_flow_endpoint(request: RequestModel) -> ResponseModel:  # type: ignore
            """Execute the specific flow with provided inputs."""
            try:
                # Make a copy of the flow to avoid modifying the original
                # TODO: just store this in case we're using memory / need state.
                # TODO: Store memory and session info in a cache to enable this kind of stateful communication.
                flow_copy = flow.model_copy(deep=True)
                # Set input values on the flow variables
                if flow_copy.inputs:
                    for var in flow_copy.inputs:
                        # Get the value from the request using the variable ID
                        request_dict = request.model_dump()  # type: ignore
                        if var.id in request_dict:
                            var.value = getattr(request, var.id)
                        elif not var.is_set():
                            raise HTTPException(
                                status_code=400,
                                detail=f"Required input '{var.id}' not provided",
                            )

                # Execute the flow
                result_vars = execute_flow(flow_copy)

                # Extract output values
                outputs = {var.id: var.value for var in result_vars}

                response_data = {
                    "flow_id": flow_id,
                    "outputs": outputs,
                    "status": "success",
                }

                # Return the response using the dynamic model
                return ResponseModel(**response_data)  # type: ignore

            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Flow execution failed: {str(e)}"
                )

        # Set the function annotations properly for FastAPI
        execute_flow_endpoint.__annotations__ = {
            "request": RequestModel,
            "return": ResponseModel,
        }

        # Add the endpoint with explicit models
        app.post(
            f"/flows/{flow_id}",
            tags=["flow"],
            summary=f"Execute {flow_id} flow",
            description=f"Execute the '{flow_id}' flow with the provided input parameters.",
            response_model=ResponseModel,
        )(execute_flow_endpoint)
