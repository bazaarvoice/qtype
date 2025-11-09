from __future__ import annotations

from pydantic import BaseModel

from qtype.base.types import PrimitiveTypeEnum
from qtype.dsl.domain_types import ChatContent, ChatMessage, MessageRole
from qtype.interpreter.stream.chat.file_conversions import file_to_content
from qtype.interpreter.stream.chat.vercel import (
    ChatRequest,
    CompletionRequest,
    UIMessage,
)


def ui_request_to_domain_type(request: ChatRequest) -> list[ChatMessage]:
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
            blocks.append(
                file_to_content(part.url)  # type: ignore
            )
        elif part.type == "source-url":
            # Source URLs are references that might be displayed as citations
            # Store as structured citation data
            citation_data = {
                "source_id": part.source_id,  # type: ignore
                "url": part.url,  # type: ignore
                "title": part.title,  # type: ignore
            }
            blocks.append(
                ChatContent(
                    type=PrimitiveTypeEnum.citation_url,
                    content=citation_data,
                )
            )
        elif part.type == "source-document":
            # Source documents are references to documents
            # Store as structured citation data
            citation_data = {
                "source_id": part.source_id,  # type: ignore
                "title": part.title,  # type: ignore
                "filename": part.filename,  # type: ignore
                "media_type": part.media_type,  # type: ignore
            }
            blocks.append(
                ChatContent(
                    type=PrimitiveTypeEnum.citation_document,
                    content=citation_data,
                )
            )
        elif part.type == "step-start":
            # Step boundaries might not need content blocks
            continue
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


def completion_request_to_input_model(
    request: CompletionRequest, input_model: type[BaseModel]
) -> BaseModel:
    """
    Convert a CompletionRequest to a flow's input model.

    The CompletionRequest has a required 'prompt' field.
    This function maps the request data to the flow's input shape.

    Args:
        request: The Vercel CompletionRequest with prompt and additional fields
        input_model: The Pydantic model class created by create_input_shape()

    Returns:
        An instance of input_model with data from the request

    Raises:
        ValueError: If required fields are missing or data doesn't match schema
    """

    prompt_str = request.prompt

    # Get the field name from the input model
    # The semantic checker ensures there's exactly one field for Complete flows
    field_names = list(input_model.model_fields.keys())
    if len(field_names) != 1:
        raise ValueError(
            (
                f"Expected exactly one input field for Complete flow, "
                f"found {len(field_names)}: {field_names}"
            )
        )
    field_name = field_names[0]

    # Create instance of the input model with the prompt mapped to the field
    try:
        return input_model(**{field_name: prompt_str})
    except Exception as e:
        raise ValueError(
            f"Failed to map CompletionRequest to input model: {e}"
        ) from e
