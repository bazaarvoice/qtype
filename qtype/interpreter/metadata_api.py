"""Metadata API endpoints for flow discovery."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from qtype.interpreter.typing import create_input_shape, create_output_shape
from qtype.semantic.model import Application, Flow


class FlowEndpoints(BaseModel):
    """Available endpoints for a flow."""

    rest: str = Field(..., description="REST execution endpoint")
    stream: str | None = Field(
        None,
        description="Streaming endpoint (SSE) if flow has an interface",
    )


class FlowMetadata(BaseModel):
    """Metadata about a flow for frontend discovery."""

    id: str = Field(..., description="Flow ID")
    description: str | None = Field(None, description="Flow description")
    interface_type: str | None = Field(
        None,
        description="Interface type: 'Complete' or 'Conversational'",
    )
    session_inputs: list[str] = Field(
        default_factory=list,
        description="Input variables that persist across session",
    )
    endpoints: FlowEndpoints = Field(
        ..., description="Available API endpoints"
    )
    input_schema: dict[str, Any] = Field(
        ..., description="JSON schema for input"
    )
    output_schema: dict[str, Any] = Field(
        ..., description="JSON schema for output"
    )


def create_metadata_endpoints(app: FastAPI, application: Application) -> None:
    """
    Create metadata endpoints for flow discovery.

    Args:
        app: FastAPI application instance
        application: QType Application with flows
    """

    @app.get(
        "/flows",
        tags=["flows"],
        summary="List all flows",
        description="Get metadata for all available flows",
        response_model=list[FlowMetadata],
    )
    async def list_flows() -> list[FlowMetadata]:
        """List all flows with their metadata."""
        flows_metadata = []

        for flow in application.flows:
            metadata = _create_flow_metadata(flow)
            flows_metadata.append(metadata)

        return flows_metadata


def _create_flow_metadata(flow: Flow) -> FlowMetadata:
    """
    Create metadata for a single flow.

    Args:
        flow: Flow to create metadata for

    Returns:
        FlowMetadata with all information
    """
    # Determine interface type
    interface_type = None
    session_inputs = []
    if flow.interface:
        interface_type = flow.interface.type
        session_inputs = [
            var.id if hasattr(var, "id") else str(var)
            for var in flow.interface.session_inputs
        ]

    # Create schemas
    input_model = create_input_shape(flow)
    output_model = create_output_shape(flow)

    # Determine streaming endpoint availability
    stream_endpoint = (
        f"/flows/{flow.id}/stream" if flow.interface is not None else None
    )

    return FlowMetadata(
        id=flow.id,
        description=flow.description,
        interface_type=interface_type,
        session_inputs=session_inputs,
        endpoints=FlowEndpoints(
            rest=f"/flows/{flow.id}",
            stream=stream_endpoint,
        ),
        input_schema=input_model.model_json_schema(),
        output_schema=output_model.model_json_schema(),
    )
