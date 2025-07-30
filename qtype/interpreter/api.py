from typing import Optional

from fastapi import FastAPI, HTTPException

from qtype.interpreter.flow import execute_flow
from qtype.interpreter.typing import (
    create_input_type_model,
    create_output_type_model,
)
from qtype.semantic.model import Application, Flow


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

    def create_app(
        self,
        name: Optional[str],
        fast_api_args: dict = {
            "docs_url": "/docs",
            "redoc_url": "/redoc",
        },
    ) -> FastAPI:
        """Create FastAPI app with dynamic endpoints."""
        app = FastAPI(title=name or "QType API", **fast_api_args)

        flows = self.definition.flows if self.definition.flows else []

        # Dynamically generate POST endpoints for each flow
        for flow in flows:
            self._create_flow_endpoint(app, flow)

        return app

    def _create_flow_endpoint(self, app: FastAPI, flow: Flow) -> None:
        """Create a dynamic POST endpoint for a specific flow."""
        flow_id = flow.id

        # Create dynamic request and response models for this flow
        RequestModel = create_input_type_model(flow)
        ResponseModel = create_output_type_model(flow)

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
