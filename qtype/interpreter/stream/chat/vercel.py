"""
Pydantic models for Vercel AI SDK UI types.

This module reproduces the exact TypeScript type shapes from the AI SDK UI
as Pydantic models for use in Python implementations.
"""

from __future__ import annotations

from typing import Any, Literal, Union

from pydantic import BaseModel, Field


# Provider metadata
class ProviderMetadata(BaseModel):
    """Provider-specific metadata.

    Reproduces: ProviderMetadata from ui/ui-message-chunks.ts
    """

    model_config = {"extra": "allow"}


# UI Message Parts
class TextUIPart(BaseModel):
    """A text part of a message.

    Reproduces: TextUIPart from ui/ui-messages.ts
    """

    type: Literal["text"] = "text"
    text: str
    state: Literal["streaming", "done"] | None = None
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class ReasoningUIPart(BaseModel):
    """A reasoning part of a message.

    Reproduces: ReasoningUIPart from ui/ui-messages.ts
    """

    type: Literal["reasoning"] = "reasoning"
    text: str
    state: Literal["streaming", "done"] | None = None
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class SourceUrlUIPart(BaseModel):
    """A source URL part of a message.

    Reproduces: SourceUrlUIPart from ui/ui-messages.ts
    """

    type: Literal["source-url"] = "source-url"
    source_id: str = Field(alias="sourceId")
    url: str
    title: str | None = None
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class SourceDocumentUIPart(BaseModel):
    """A document source part of a message.

    Reproduces: SourceDocumentUIPart from ui/ui-messages.ts
    """

    type: Literal["source-document"] = "source-document"
    source_id: str = Field(alias="sourceId")
    media_type: str = Field(alias="mediaType")
    title: str
    filename: str | None = None
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class FileUIPart(BaseModel):
    """A file part of a message.

    Reproduces: FileUIPart from ui/ui-messages.ts
    """

    type: Literal["file"] = "file"
    media_type: str = Field(alias="mediaType")
    filename: str | None = None
    url: str
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class StepStartUIPart(BaseModel):
    """A step boundary part of a message.

    Reproduces: StepStartUIPart from ui/ui-messages.ts
    """

    type: Literal["step-start"] = "step-start"


# Union type for UI message parts
UIMessagePart = Union[
    TextUIPart,
    ReasoningUIPart,
    SourceUrlUIPart,
    SourceDocumentUIPart,
    FileUIPart,
    StepStartUIPart,
]


# UI Message
class UIMessage(BaseModel):
    """AI SDK UI Message.

    Reproduces: UIMessage from ui/ui-messages.ts
    """

    id: str
    role: Literal["system", "user", "assistant"]
    metadata: dict[str, Any] | None = None
    parts: list[UIMessagePart]


# Chat Request (the request body sent from frontend)
class ChatRequest(BaseModel):
    """Chat request format sent from AI SDK UI/React.

    Reproduces: ChatRequest from ui/chat-transport.ts
    """

    id: str  # chatId
    messages: list[UIMessage]
    trigger: Literal["submit-message", "regenerate-message"]
    message_id: str | None = Field(default=None, alias="messageId")


# UI Message Chunks (streaming events)
class TextStartChunk(BaseModel):
    """Text start chunk.

    Reproduces: TextStartChunk from ui/ui-message-chunks.ts
    """

    type: Literal["text-start"] = "text-start"
    id: str
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class TextDeltaChunk(BaseModel):
    """Text delta chunk.

    Reproduces: TextDeltaChunk from ui/ui-message-chunks.ts
    """

    type: Literal["text-delta"] = "text-delta"
    id: str
    delta: str
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class TextEndChunk(BaseModel):
    """Text end chunk.

    Reproduces: TextEndChunk from ui/ui-message-chunks.ts
    """

    type: Literal["text-end"] = "text-end"
    id: str
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class ReasoningStartChunk(BaseModel):
    """Reasoning start chunk.

    Reproduces: ReasoningStartChunk from ui/ui-message-chunks.ts
    """

    type: Literal["reasoning-start"] = "reasoning-start"
    id: str
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class ReasoningDeltaChunk(BaseModel):
    """Reasoning delta chunk.

    Reproduces: ReasoningDeltaChunk from ui/ui-message-chunks.ts
    """

    type: Literal["reasoning-delta"] = "reasoning-delta"
    id: str
    delta: str
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class ReasoningEndChunk(BaseModel):
    """Reasoning end chunk.

    Reproduces: ReasoningEndChunk from ui/ui-message-chunks.ts
    """

    type: Literal["reasoning-end"] = "reasoning-end"
    id: str
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class ErrorChunk(BaseModel):
    """Error chunk.

    Reproduces: ErrorChunk from ui/ui-message-chunks.ts
    """

    type: Literal["error"] = "error"
    error_text: str = Field(alias="errorText")


class StartStepChunk(BaseModel):
    """Start step chunk.

    Reproduces: StartStepChunk from ui/ui-message-chunks.ts
    """

    type: Literal["start-step"] = "start-step"


class FinishStepChunk(BaseModel):
    """Finish step chunk.

    Reproduces: FinishStepChunk from ui/ui-message-chunks.ts
    """

    type: Literal["finish-step"] = "finish-step"


class StartChunk(BaseModel):
    """Start chunk.

    Reproduces: StartChunk from ui/ui-message-chunks.ts
    """

    type: Literal["start"] = "start"
    message_id: str | None = Field(default=None, alias="messageId")
    message_metadata: dict[str, Any] | None = Field(
        default=None, alias="messageMetadata"
    )

# temp
class ToolStarted(BaseModel):
    """Start chunk.

    Reproduces: Tool Started from ui/ui-message-chunks.ts
    """

    type: Literal["tool_started"] = "tool_started"
    message_id: str | None = Field(default=None, alias="messageId")
    message_metadata: dict[str, Any] | None = Field(
        default=None, alias="messageMetadata"
    )

class ToolResultReceived(BaseModel):
    """Start chunk.

    Reproduces: Tool Result Received from ui/ui-message-chunks.ts
    """

    type: Literal["tool_result_received"] = "tool_result_received"
    message_id: str | None = Field(default=None, alias="messageId")
    message_metadata: dict[str, Any] | None = Field(
        default=None, alias="messageMetadata"
    )

class FinishChunk(BaseModel):
    """Finish chunk.

    Reproduces: FinishChunk from ui/ui-message-chunks.ts
    """

    type: Literal["finish"] = "finish"
    message_metadata: dict[str, Any] | None = Field(
        default=None, alias="messageMetadata"
    )


class AbortChunk(BaseModel):
    """Abort chunk.

    Reproduces: AbortChunk from ui/ui-message-chunks.ts
    """

    type: Literal["abort"] = "abort"


class MessageMetadataChunk(BaseModel):
    """Message metadata chunk.

    Reproduces: MessageMetadataChunk from ui/ui-message-chunks.ts
    """

    type: Literal["message-metadata"] = "message-metadata"
    message_metadata: dict[str, Any] = Field(alias="messageMetadata")


# Union type for all UI message chunks
UIMessageChunk = Union[
    TextStartChunk,
    TextDeltaChunk,
    TextEndChunk,
    ReasoningStartChunk,
    ReasoningDeltaChunk,
    ReasoningEndChunk,
    ErrorChunk,
    StartStepChunk,
    FinishStepChunk,
    StartChunk,
    FinishChunk,
    AbortChunk,
    MessageMetadataChunk,
]
