from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field

from qtype.dsl.base_types import PrimitiveTypeEnum, StrictBaseModel


class Embedding(StrictBaseModel):
    """A standard, built-in representation of a vector embedding."""

    vector: list[float] = Field(
        ..., description="The vector representation of the embedding."
    )
    source_text: str | None = Field(
        None, description="The original text that was embedded."
    )
    metadata: dict[str, str] | None = Field(
        None, description="Optional metadata associated with the embedding."
    )


class MessageRole(str, Enum):
    assistant = "assistant"
    chatbot = "chatbot"
    developer = "developer"
    function = "function"
    model = "model"
    system = "system"
    tool = "tool"
    user = "user"


class ChatContent(StrictBaseModel):
    type: PrimitiveTypeEnum = Field(
        ..., description="The type of content, such as 'text', 'image', etc."
    )
    content: Any = Field(
        ...,
        description="The actual content, which can be a string, image data, etc.",
    )


class ChatMessage(StrictBaseModel):
    """A standard, built-in representation of a chat message."""

    role: MessageRole = Field(
        ...,
        description="The role of the message sender (e.g., 'user', 'assistant').",
    )
    blocks: list[ChatContent] = Field(
        ...,
        description="The content blocks of the chat message, which can include text, images, or other media.",
    )
