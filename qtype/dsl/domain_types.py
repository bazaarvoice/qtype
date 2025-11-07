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
    content: Any | None = Field(
        None, description="The original content that was embedded."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata associated with the embedding.",
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
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata associated with the document.",
    )
    type: PrimitiveTypeEnum = Field(
        ...,
        description="The type of the document content (e.g., 'text', 'image').",
    )


class RAGChunk(Embedding):
    """A standard, built-in representation of a chunk of a document used in Retrieval-Augmented Generation (RAG)."""

    chunk_id: str = Field(
        ..., description="An unique identifier for the chunk."
    )
    document_id: str = Field(
        ..., description="The identifier of the parent document."
    )
    vector: list[float] | None = Field(
        None, description="Optional vector embedding for the chunk."
    )


class RAGSearchResult(StrictBaseModel):
    """A standard, built-in representation of a search result from a RAG vector search."""

    chunk: RAGChunk = Field(
        ..., description="The RAG chunk returned as a search result."
    )
    score: float = Field(
        ...,
        description="The similarity score of the chunk with respect to the query.",
    )


class AggregateStats(StrictBaseModel):
    """A standard, built-in representation of aggregate statistics."""

    num_successful: int = Field(
        ..., description="The count of successful messages processed."
    )
    num_failed: int = Field(
        ..., description="The count of failed messages processed."
    )
    num_total: int = Field(
        ..., description="The total count of messages processed."
    )
