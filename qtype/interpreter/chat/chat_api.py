from __future__ import annotations

import logging
import uuid
from collections.abc import Generator
from typing import Any

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from qtype.dsl.base_types import PrimitiveTypeEnum
from qtype.dsl.domain_types import ChatContent, ChatMessage, MessageRole
from qtype.interpreter.chat.vercel import (
    ChatRequest,
    ErrorChunk,
    FinishChunk,
    StartChunk,
    TextDeltaChunk,
    TextEndChunk,
    TextStartChunk,
    UIMessage,
)
from qtype.interpreter.flow import execute_flow
from qtype.interpreter.streaming_helpers import create_streaming_generator
from qtype.semantic.model import Flow


def _ui_request_to_domain_type(request: ChatRequest) -> list[ChatMessage]:
    """
    Convert a ChatRequest to domain-specific ChatMessages.

    Processes all UI messages from the AI SDK UI/React request format.
    Returns the full conversation history for context.
    """
    if not request.messages:
        raise ValueError("No messages provided in request.")

    # Convert each UIMessage to a domain-specific ChatMessage
    return [
        _ui_message_to_domain_type(message) for message in request.messages
    ]


def _ui_message_to_domain_type(message: UIMessage) -> ChatMessage:
    """
    Convert a UIMessage to a domain-specific ChatMessage.

    Creates one block for each part in the message content.
    """
    blocks = []

    for part in message.parts:
        if part.type == "text":
            blocks.append(
                ChatContent(type=PrimitiveTypeEnum.text, content=part.text)
            )
        elif part.type == "reasoning":
            blocks.append(
                ChatContent(type=PrimitiveTypeEnum.text, content=part.text)
            )
        elif part.type == "file":
            raise NotImplementedError(
                "File part handling is not implemented yet."
            )
        elif part.type.startswith("tool-"):
            raise NotImplementedError(
                "Tool call part handling is not implemented yet."
            )
        elif part.type == "dynamic-tool":
            raise NotImplementedError(
                "Dynamic tool part handling is not implemented yet."
            )
        elif part.type == "step-start":
            # Step boundaries might not need content blocks
            continue
        elif part.type in ["source-url", "source-document"]:
            raise NotImplementedError(
                "Source part handling is not implemented yet."
            )
        elif part.type.startswith("data-"):
            raise NotImplementedError(
                "Data part handling is not implemented yet."
            )
        else:
            # Log unknown part types for debugging
            raise ValueError(f"Unknown part type: {part.type}")

    # If no blocks were created, raise an error
    if not blocks:
        raise ValueError(
            "No valid content blocks created from UIMessage parts."
        )

    return ChatMessage(
        role=MessageRole(message.role),
        blocks=blocks,
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

        # Convert AI SDK UI request to domain ChatMessages
        messages = _ui_request_to_domain_type(request)
        if not len(messages):
            raise ValueError("No input messages received")

        # Pop the last message as the current input
        current_input = messages.pop()
        if current_input.role != MessageRole.user:
            raise ValueError(
                f"Unexpected input {current_input} from non user role: {current_input.role}"
            )

        flow_copy = flow.model_copy(deep=True)

        input_variable = [
            var for var in flow_copy.inputs if var.type == ChatMessage
        ][0]
        input_variable.value = current_input

        # Pass conversation context to flow execution for memory population
        execution_kwargs: Any = {
            "session_id": request.id,  # Use request ID as session identifier
            "conversation_history": messages,
        }

        # Create a streaming generator for the flow execution
        stream_generator, result_future = create_streaming_generator(
            execute_flow, flow_copy, **execution_kwargs
        )

        # Create generator that formats messages according to AI SDK UI streaming protocol
        def vercel_ai_formatter() -> Generator[str, None, None]:
            """Format stream data according to AI SDK UI streaming protocol."""

            # Send start chunk
            start_chunk = StartChunk(messageId=str(uuid.uuid4()))  # type: ignore
            yield f"data: {start_chunk.model_dump_json(by_alias=True, exclude_none=True)}\n\n"

            # Track text content for proper streaming
            text_id = str(uuid.uuid4())
            text_started = False

            for step, message in stream_generator:
                if isinstance(message, ChatMessage):
                    # Convert ChatMessage to text content
                    content = " ".join(
                        [
                            block.content
                            for block in message.blocks
                            if hasattr(block, "content") and block.content
                        ]
                    )
                    if content.strip():
                        # Start text block if not started
                        if not text_started:
                            text_start = TextStartChunk(id=text_id)
                            yield f"data: {text_start.model_dump_json(by_alias=True, exclude_none=True)}\n\n"
                            text_started = True

                        # Send text delta
                        text_delta = TextDeltaChunk(id=text_id, delta=content)
                        yield f"data: {text_delta.model_dump_json(by_alias=True, exclude_none=True)}\n\n"
                else:
                    # Handle other message types as text deltas
                    text_content = str(message)
                    if text_content.strip():
                        # Start text block if not started
                        if not text_started:
                            text_start = TextStartChunk(id=text_id)
                            yield f"data: {text_start.model_dump_json(by_alias=True, exclude_none=True)}\n\n"
                            text_started = True

                        # Send text delta
                        text_delta = TextDeltaChunk(
                            id=text_id, delta=text_content
                        )
                        yield f"data: {text_delta.model_dump_json(by_alias=True, exclude_none=True)}\n\n"

            # End text block if it was started
            if text_started:
                text_end = TextEndChunk(id=text_id)
                yield f"data: {text_end.model_dump_json(by_alias=True, exclude_none=True)}\n\n"

            # Send finish chunk
            try:
                result_future.result(timeout=5.0)
                finish_chunk = FinishChunk()
                yield f"data: {finish_chunk.model_dump_json(by_alias=True, exclude_none=True)}\n\n"
            except Exception as e:
                # Send error
                error_chunk = ErrorChunk(errorText=str(e))
                logging.error(
                    f"Error during flow execution: {e}", exc_info=True
                )
                yield f"data: {error_chunk.model_dump_json(by_alias=True, exclude_none=True)}\n\n"

        response = StreamingResponse(
            vercel_ai_formatter(), media_type="text/plain; charset=utf-8"
        )
        response.headers["x-vercel-ai-ui-message-stream"] = "v1"
        return response

    # Add the endpoint to the FastAPI app
    app.post(
        f"/flows/{flow_id}/chat",
        tags=["chat"],
        summary=f"Chat with {flow_id} flow",
        description=f"Stream chat responses from the '{flow_id}' Flow using AI SDK UI transport protocol.",
        response_class=StreamingResponse,
    )(handle_chat_data)
