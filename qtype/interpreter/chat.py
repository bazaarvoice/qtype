from __future__ import annotations

import json
from collections.abc import Generator
from enum import Enum
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from qtype.dsl.base_types import PrimitiveTypeEnum
from qtype.dsl.domain_types import ChatContent, ChatMessage, MessageRole
from qtype.interpreter.flow import execute_flow
from qtype.interpreter.streaming_helpers import create_streaming_generator
from qtype.semantic.model import ChatFlow


class ToolInvocationState(str, Enum):
    """State of a tool invocation."""

    CALL = "call"
    PARTIAL_CALL = "partial-call"
    RESULT = "result"


class ClientAttachment(BaseModel):
    """Client attachment for messages."""

    name: str
    content_type: str
    url: str


class ToolInvocation(BaseModel):
    """Tool invocation data."""

    state: ToolInvocationState
    tool_call_id: str
    tool_name: str
    args: Any
    result: Any


class ClientMessage(BaseModel):
    """Client message following Vercel AI SDK format."""

    role: str
    content: str
    experimental_attachments: list[ClientAttachment] | None = None
    tool_invocations: list[ToolInvocation] | None = None


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    messages: list[ClientMessage]

def _request_to_domain_type(request: ChatRequest) -> ChatMessage:
    """
    Convert a ChatRequest to a domain-specific ChatMessage.

    This is a placeholder function that will be replaced with actual
    conversion logic later.
    """
    roles = {m.role for m in request.messages}
    if len(roles) > 1:
        raise ValueError(
            "Multiple roles found in messages, expected single role."
        )
    else:
        # TODO: convert attachments to other blocks
        return ChatMessage(
            role=MessageRole(roles.pop()),
            blocks=[
                ChatContent(type=PrimitiveTypeEnum.text, content=m.content)
                for m in request.messages
            ],
        )


def create_chat_flow_endpoint(app: FastAPI, flow: ChatFlow) -> None:
    """
    Create a chat endpoint for the given ChatFlow.

    This creates an endpoint at /flows/{flow_id}/chat that follows the
    Vercel AI SDK streaming protocol.

    Args:
        app: The FastAPI application instance
        flow: The ChatFlow to create an endpoint for
    """
    flow_id = flow.id

    async def handle_chat_data(
        request: ChatRequest,
        protocol: str = Query("data", description="Streaming protocol to use"),
        # TODO: https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol#data-stream-protocol support protocol = text?
    ) -> StreamingResponse:
        """Handle chat requests for the specific flow."""
        input = _request_to_domain_type(request)
        flow_copy = flow.model_copy(deep=True)
        set_count = 0

        for var in flow_copy.inputs:
            if var.type == ChatMessage:
                # Convert the input ChatMessage to flow variables
                var.value = input
                set_count += 1

        if set_count == 0:
            raise HTTPException(
                status_code=400,
                detail="No valid input provided for the ChatFlow.",
            )
        elif set_count > 1:
            raise HTTPException(
                status_code=400,
                detail="Multiple inputs provided, expected a single ChatMessage.",
            )

        # Create a streaming generator for the flow execution
        stream_generator, result_future = create_streaming_generator(
            execute_flow, flow_copy
        )

        # create a new generator from the previous one that makes vercel AI SDK format
        def vercel_ai_formatter() -> Generator[str, None, None]:
            for step, message in stream_generator:
                if isinstance(message, ChatMessage):
                    # Convert ChatMessage to Vercel AI SDK format
                    content = " ".join(
                        [
                            block.content
                            for block in message.blocks
                            if hasattr(block, "content") and block.content
                        ]
                    )
                    yield f"0:{json.dumps(content)}\n"
                else:
                    # Handle other message types (e.g., text)
                    yield f"0:{json.dumps(message)}\n"
                # TODO: handle other types like tool invocations, etc.
                # See https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol#data-stream-protocol

            # Get execution result and create finish message
            try:
                _ = result_future.result(timeout=5.0)
                finish_data = {
                    "finishReason": "stop",
                    "usage": {"promptTokens": 0, "completionTokens": 0},
                    "isContinued": False,
                }
            except Exception as e:
                finish_data = {
                    "finishReason": "error",
                    "error": str(e),
                    "isContinued": False,
                }

            yield f"{json.dumps(finish_data)}\n"

        response = StreamingResponse(
            vercel_ai_formatter(), media_type="text/plain"
        )
        response.headers["x-vercel-ai-data-stream"] = "v1"
        return response

    # Add the endpoint to the FastAPI app
    app.post(
        f"/flows/{flow_id}/chat",
        tags=["chat"],
        summary=f"Chat with {flow_id} flow",
        description=f"Stream chat responses from the '{flow_id}' ChatFlow using Vercel AI SDK protocol.",
        response_class=StreamingResponse,
    )(handle_chat_data)
