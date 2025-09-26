from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from qtype.dsl.base_types import StepCardinality
from qtype.interpreter.batch.flow import batch_execute_flow
from qtype.interpreter.batch.types import BatchConfig, ErrorMode
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
        name: str | None = None,
        ui_enabled: bool = True,
        fast_api_args: dict | None = None,
        servers: list[dict] | None = None,
    ) -> FastAPI:
        """Create FastAPI app with dynamic endpoints."""
        if fast_api_args is None:
            fast_api_args = {
                "docs_url": "/docs",
                "redoc_url": "/redoc",
            }

        # Add servers to FastAPI kwargs if provided
        if servers is not None:
            fast_api_args["servers"] = servers

        app = FastAPI(title=name or "QType API", **fast_api_args)

        # Serve static UI files if they exist
        if ui_enabled:
            # Add CORS middleware only for localhost development
            if self.host in ("localhost", "127.0.0.1", "0.0.0.0"):
                app.add_middleware(
                    CORSMiddleware,
                    allow_origins=["*"],
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
            ui_dir = Path(__file__).parent / "ui"
            if ui_dir.exists():
                app.mount(
                    "/ui",
                    StaticFiles(directory=str(ui_dir), html=True),
                    name="ui",
                )
                app.get("/")(lambda: RedirectResponse(url="/ui"))

        flows = self.definition.flows if self.definition.flows else []

        # Dynamically generate POST endpoints for each flow
        for flow in flows:
            if flow.mode == "Chat":
                # For chat, we can create a single endpoint
                # that handles the chat interactions
                from qtype.interpreter.chat.chat_api import (
                    create_chat_flow_endpoint,
                )

                create_chat_flow_endpoint(app, flow)
            else:
                self._create_flow_endpoint(app, flow)

        return app

    def _create_flow_endpoint(self, app: FastAPI, flow: Flow) -> None:
        """Create a dynamic POST endpoint for a specific flow."""
        flow_id = flow.id

        # determine if this is a batch inference
        is_batch = flow.cardinality == StepCardinality.many

        # Create dynamic request and response models for this flow
        RequestModel = create_input_type_model(flow, is_batch)
        ResponseModel = create_output_type_model(flow, is_batch)

        # Create the endpoint function with proper model binding
        if is_batch:

            def execute_flow_endpoint(  # type: ignore
                request: RequestModel,  # type: ignore
                error_mode: ErrorMode = Query(
                    default=ErrorMode.FAIL,
                    description="Error handling mode for batch processing",
                ),
            ) -> ResponseModel:  # type: ignore
                try:
                    # Make a copy of the flow to avoid modifying the original
                    # TODO: Use session to ensure memory is not used across requests.
                    flow_copy = flow.model_copy(deep=True)
                    # convert the inputs into a dataframe with a single row
                    inputs = pd.DataFrame(
                        [i.model_dump() for i in request.inputs]  # type: ignore
                    )

                    # Execute the flow
                    results, errors = batch_execute_flow(
                        flow_copy,
                        inputs,
                        batch_config=BatchConfig(error_mode=error_mode),
                    )

                    response_data = {
                        "flow_id": flow_id,
                        "outputs": results.to_dict(orient="records"),
                        "errors": errors.to_dict(orient="records"),
                        "num_results": len(results),
                        "num_errors": len(errors),
                        "num_inputs": len(inputs),
                        "status": "success" if len(errors) == 0 else "partial",
                    }

                    # Return the response using the dynamic model
                    return ResponseModel(**response_data)  # type: ignore

                except Exception as e:
                    logging.error("Batch Flow Execution Failed", exc_info=e)
                    raise HTTPException(
                        status_code=500,
                        detail=f"Batch flow execution failed: {str(e)}",
                    )
        else:

            def execute_flow_endpoint(request: RequestModel) -> ResponseModel:  # type: ignore
                try:
                    # Make a copy of the flow to avoid modifying the original
                    # TODO: Use session to ensure memory is not used across requests.
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
                        status_code=500,
                        detail=f"Flow execution failed: {str(e)}",
                    )

        # Set the function annotations properly for FastAPI
        execute_flow_endpoint.__annotations__ = {
            "request": RequestModel,
            "error_mode": ErrorMode,
            "return": ResponseModel,
        }

        # Add the endpoint with explicit models
        app.post(
            f"/flows/{flow_id}",
            tags=["flow"],
            description=flow.description or "Execute a flow",
            response_model=ResponseModel,
        )(execute_flow_endpoint)
