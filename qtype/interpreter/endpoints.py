"""Unified API endpoint for flow execution with streaming and REST support."""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse

from qtype.dsl.domain_types import ChatMessage, MessageRole
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.flow import run_flow
from qtype.interpreter.stream.chat import format_stream_events_as_sse
from qtype.interpreter.stream.chat.ui_request_to_domain_type import (
    completion_request_to_input_model,
    ui_request_to_domain_type,
)
from qtype.interpreter.stream.chat.vercel import ChatRequest, CompletionRequest
from qtype.interpreter.stream.utils import callback_to_async_iterator
from qtype.interpreter.types import FlowMessage, StreamEvent
from qtype.interpreter.typing import (
    create_input_shape,
    create_output_container_type,
    create_output_shape,
    flow_results_to_output_container,
    request_to_flow_message,
)
from qtype.semantic.model import Flow

logger = logging.getLogger(__name__)


async def _execute_flow_with_streaming(
    flow: Flow,
    initial_message: FlowMessage,
    context: ExecutorContext,
) -> AsyncIterator[StreamEvent]:
    """
    Execute flow and yield StreamEvents as they occur.

    This function converts run_flow's callback-based streaming to an
    async iterator. Executors emit StreamEvents (including ErrorEvents)
    through the on_stream_event callback.

    Args:
        flow: The flow to execute
        initial_message: Initial FlowMessage with inputs

    Yields:
        StreamEvent instances from executors
    """

    async def execute_with_callback(callback):  # type: ignore[no-untyped-def]
        """Execute flow with streaming callback."""
        # Update context with streaming callback
        stream_context = ExecutorContext(
            secret_manager=context.secret_manager,
            on_stream_event=callback,
            on_progress=context.on_progress,
            tracer=context.tracer,
        )
        await run_flow(
            flow,
            initial_message,
            context=stream_context,
        )

    # Convert callback-based streaming to async iterator
    async for event in callback_to_async_iterator(execute_with_callback):
        yield event


async def _stream_sse_response(
    flow: Flow,
    initial_message: FlowMessage,
    context: ExecutorContext,
    output_metadata: dict[str, Any] | None = None,
) -> AsyncIterator[str]:
    """
    Execute flow and stream Server-Sent Events using Vercel AI SDK protocol.

    This function orchestrates flow execution and formats the resulting
    StreamEvents as SSE for the Vercel AI SDK frontend.

    Args:
        flow: The flow to execute
        initial_message: Initial FlowMessage with inputs
        output_metadata: Optional metadata to include in FinishChunk

    Yields:
        SSE formatted strings (data: {json}\\n\\n)
    """
    # Execute flow and get event stream
    event_stream = _execute_flow_with_streaming(flow, initial_message, context)

    # Format events as SSE with metadata
    async for sse_line in format_stream_events_as_sse(
        event_stream, output_metadata=output_metadata
    ):
        yield sse_line


def _create_chat_streaming_endpoint(
    app: FastAPI, flow: Flow, context: ExecutorContext
) -> None:
    """
    Create streaming endpoint for Conversational flows.

    Args:
        app: FastAPI application instance
        flow: Flow with Conversational interface
        secret_manager: Optional secret manager for resolving secrets
    """
    flow_id = flow.id

    # Type narrowing for mypy
    if flow.interface is None:
        raise ValueError(f"Flow {flow_id} has no interface defined")
    interface = flow.interface

    async def stream_chat(request: ChatRequest) -> StreamingResponse:
        """Stream conversational flow with Vercel AI SDK protocol."""
        try:
            # Convert Vercel ChatRequest to ChatMessages
            messages = ui_request_to_domain_type(request)
            if not messages:
                raise ValueError("No input messages received")

            current_input = messages.pop()
            if current_input.role != MessageRole.user:
                raise ValueError(
                    f"Expected user message, got {current_input.role}"
                )

            # Find ChatMessage input variable
            chat_input_var = next(
                (var for var in flow.inputs if var.type == ChatMessage),
                None,
            )
            if not chat_input_var:
                raise ValueError("No ChatMessage input found in flow inputs")

            input_data = {chat_input_var.id: current_input}

            # Add session_inputs from interface
            for session_var in interface.session_inputs:
                if session_var.value is not None:
                    input_data[session_var.id] = session_var.value

            # Create a dynamic request model with the input data
            RequestModel = create_input_shape(flow)
            request_obj = RequestModel(**input_data)

            initial_message = request_to_flow_message(
                request=request_obj,
                session_id=request.id,
                conversation_history=messages,
            )

            return StreamingResponse(
                _stream_sse_response(
                    flow,
                    initial_message,
                    output_metadata=None,
                    context=context,
                ),
                media_type="text/plain; charset=utf-8",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "x-vercel-ai-ui-message-stream": "v1",
                },
            )

        except ValueError as ve:
            logger.error(f"Validation error: {ve}")
            raise HTTPException(status_code=400, detail=str(ve)) from ve
        except Exception as e:
            logger.error(
                f"Flow streaming failed for {flow_id}: {e}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=f"Flow streaming failed: {str(e)}",
            ) from e

    # Register streaming endpoint
    app.post(
        f"/flows/{flow_id}/stream",
        tags=["flows"],
        summary=f"Stream {flow_id} flow (Chat)",
        description=(
            flow.description or f"Stream the {flow_id} conversational flow"
        ),
    )(stream_chat)


def _create_completion_streaming_endpoint(
    app: FastAPI, flow: Flow, context: ExecutorContext
) -> None:
    """
    Create streaming endpoint for Complete flows.

    Args:
        app: FastAPI application instance
        flow: Flow with Complete interface
        secret_manager: Optional secret manager for resolving secrets
    """
    flow_id = flow.id

    async def stream_completion(
        request: CompletionRequest,
    ) -> StreamingResponse:
        """Stream completion flow with Vercel AI SDK protocol."""
        try:
            # Complete flows: convert CompletionRequest to input model
            InputModel = create_input_shape(flow)
            request_obj = completion_request_to_input_model(
                request, InputModel
            )
            initial_message = request_to_flow_message(request=request_obj)

            return StreamingResponse(
                _stream_sse_response(
                    flow,
                    initial_message,
                    output_metadata=None,
                    context=context,
                ),
                media_type="text/plain; charset=utf-8",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "x-vercel-ai-ui-message-stream": "v1",
                },
            )

        except ValueError as ve:
            logger.error(f"Validation error: {ve}")
            raise HTTPException(status_code=400, detail=str(ve)) from ve
        except Exception as e:
            logger.error(
                f"Flow streaming failed for {flow_id}: {e}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=f"Flow streaming failed: {str(e)}",
            ) from e

    # Register streaming endpoint
    app.post(
        f"/flows/{flow_id}/stream",
        tags=["flows"],
        summary=f"Stream {flow_id} flow (Complete)",
        description=(
            flow.description or f"Stream the {flow_id} completion flow"
        ),
    )(stream_completion)


def create_streaming_endpoint(
    app: FastAPI, flow: Flow, context: ExecutorContext
) -> None:
    """
    Create streaming endpoint for flow execution.

    Args:
        app: FastAPI application instance
        flow: Flow to create endpoint for
        secret_manager: Optional secret manager for resolving secrets
    """
    if flow.interface is None:
        raise ValueError(f"Flow {flow.id} has no interface defined")

    # Dispatch based on interface type
    interface_type = flow.interface.type
    if interface_type == "Conversational":
        _create_chat_streaming_endpoint(app, flow, context)
    elif interface_type == "Complete":
        _create_completion_streaming_endpoint(app, flow, context)
    else:
        raise ValueError(
            f"Unknown interface type for flow {flow.id}: {interface_type}"
        )


def create_rest_endpoint(
    app: FastAPI, flow: Flow, context: ExecutorContext
) -> None:
    """
    Create only the REST endpoint for flow execution.

    Args:
        app: FastAPI application instance
        flow: Flow to create endpoint for
        secret_manager: Optional secret manager for resolving secrets
    """
    RequestModel = create_input_shape(flow)
    ResultShape = create_output_shape(flow)
    ResponseModel = create_output_container_type(flow)

    async def execute_flow_rest(
        body: RequestModel,  # type: ignore[valid-type]
        request: Request,
    ) -> ResponseModel:  # type: ignore[valid-type]
        """Execute the flow and return JSON response."""
        try:
            # Only pass session_id if it's provided in headers
            kwargs = {}
            if "session_id" in request.headers:
                kwargs["session_id"] = request.headers["session_id"]

            initial_message = request_to_flow_message(request=body, **kwargs)

            # Execute flow
            results = await run_flow(flow, initial_message, context=context)

            if not results:
                raise HTTPException(
                    status_code=500, detail="No results returned"
                )

            return flow_results_to_output_container(
                results,
                output_shape=ResultShape,
                output_container=ResponseModel,
            )
        except ValueError as ve:
            logger.error(f"Validation error: {ve}")
            raise HTTPException(status_code=400, detail=str(ve)) from ve
        except Exception as e:
            logger.error(
                f"Flow execution failed for {flow.id}: {e}", exc_info=True
            )
            raise HTTPException(
                status_code=500, detail=f"Flow execution failed: {str(e)}"
            ) from e

    # Set annotations for REST endpoint
    execute_flow_rest.__annotations__ = {
        "body": RequestModel,
        "request": Request,
        "return": ResponseModel,
    }

    # Register REST endpoint
    app.post(
        f"/flows/{flow.id}",
        tags=["flows"],
        description=flow.description or f"Execute the {flow.id} flow",
        response_model=ResponseModel,
    )(execute_flow_rest)
