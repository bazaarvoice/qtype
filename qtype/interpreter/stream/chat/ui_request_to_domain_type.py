from __future__ import annotations

from qtype.dsl.base_types import PrimitiveTypeEnum
from qtype.dsl.domain_types import ChatContent, ChatMessage, MessageRole
from qtype.interpreter.stream.chat.file_conversions import file_to_content
from qtype.interpreter.stream.chat.vercel import (
    ChatRequest,
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
