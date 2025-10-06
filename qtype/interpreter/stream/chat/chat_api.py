from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from qtype.dsl.domain_types import ChatMessage, MessageRole
from qtype.interpreter.stream.chat.ui_request_to_domain_type import ui_request_to_domain_type
from qtype.interpreter.stream.chat.vercel import (
    ChatRequest,
)
from qtype.interpreter.flow import execute_flow
from qtype.interpreter.streaming_helpers import create_streaming_generator
from qtype.semantic.model import Flow

from qtype.interpreter.stream.utils.init import (
    build_vercel_ai_formatter,
    create_streaming_response,
    error_streaming_response,
    default_chat_extract_text,
)

def create_chat_flow_endpoint(app: FastAPI, flow: Flow) -> None:
    """
    Create a chat endpoint for the given Flow.

    This creates an endpoint at /flows/{flow_id}/chat that follows the
    AI SDK UI/React request format and responds with streaming data.

    Args:
        app: The FastAPI application instance
        flow: The Flow to create an endpoint for
    """
    flow_id = flow.id
    async def handle_chat_data(request: ChatRequest) -> StreamingResponse:
        """Handle chat requests for the specific flow."""
        try:
            messages = ui_request_to_domain_type(request)
            if not messages:
                raise ValueError("No input messages received")
            current_input = messages.pop()
            if current_input.role != MessageRole.user:
                raise ValueError(
                    f"Unexpected input role '{current_input.role}', expected user"
                )

            flow_copy = flow.model_copy(deep=True)
            input_variable = [
                var for var in flow_copy.inputs if var.type == ChatMessage
            ][0]
            input_variable.value = current_input

            execution_kwargs: Any = {
                "session_id": request.id,
                "conversation_history": messages,
            }
            stream_generator, result_future = create_streaming_generator(
                execute_flow, flow_copy, **execution_kwargs
            )
        except Exception as e:
            return error_streaming_response(str(e))

        formatter = build_vercel_ai_formatter(
            stream_generator=stream_generator,
            result_future=result_future,
            extract_text=default_chat_extract_text,
        )
        return create_streaming_response(formatter)
    
    app.post(
        f"/flows/{flow_id}/chat/stream",
        tags=["chat"],
        summary=f"Stream {flow_id} flow output",
        description=flow.description,
        response_class=StreamingResponse,
    )(handle_chat_data)
