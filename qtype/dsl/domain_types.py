from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field

from qtype.base.types import PrimitiveTypeEnum, StrictBaseModel


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
    mime_type: str | None = Field(
        default=None, description="The MIME type of the content, if known."
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


class RAGDocument(StrictBaseModel):
    """A standard, built-in representation of a document used in Retrieval-Augmented Generation (RAG)."""

    content: Any = Field(..., description="The main content of the document.")
    file_id: str = Field(..., description="An unique identifier for the file.")
    file_name: str = Field(..., description="The name of the file.")
    uri: str | None = Field(
        None, description="The URI where the document can be found."
    )
    metadata: dict[str, Any] | None = Field(
        None, description="Optional metadata associated with the document."
    )
    type: PrimitiveTypeEnum = Field(
        ...,
        description="The type of the document content (e.g., 'text', 'image').",
    )


class RAGChunk(StrictBaseModel):
    """A standard, built-in representation of a chunk of a document used in Retrieval-Augmented Generation (RAG)."""

    content: str = Field(..., description="The text content of the chunk.")
    chunk_id: str = Field(
        ..., description="An unique identifier for the chunk."
    )
    document_id: str = Field(
        ..., description="The identifier of the parent document."
    )
    embedding: Embedding | None = Field(
        None, description="Optional embedding associated with the chunk."
    )
    metadata: dict[str, Any] | None = Field(
        None, description="Optional metadata associated with the chunk."
    )
