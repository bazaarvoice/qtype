"""
Pydantic models for Vercel AI SDK UI types.

This module reproduces the exact TypeScript type shapes from the AI SDK UI
as Pydantic models for use in Python implementations.

Based on Vercel AI SDK v5.0.2:
https://github.com/vercel/ai/tree/ai@5.0.2/packages/ai/src/ui

## Streaming Protocol

The Vercel AI SDK uses Server-Sent Events (SSE) to stream UIMessageChunks
from the server to the client. Each chunk must be sent as:

    data: {chunk_json}\\n\\n

## Understanding Steps

Steps are visual grouping markers in the UI. The StartStepChunk and
FinishStepChunk are added to the UIMessage.parts array alongside content
chunks (text, reasoning, tools) to create visual groupings.

How it works:
1. Send StartStepChunk - adds a 'step-start' marker to message.parts
2. Send content chunks - text/reasoning/tool chunks are added to message.parts
3. Send FinishStepChunk - adds a boundary AND resets activeTextParts/activeReasoningParts

The final UIMessage.parts array will contain ALL parts in sequence:
    [
        { type: 'step-start' },
        { type: 'text', text: 'Hello world', state: 'done' },
        { type: 'step-start' },
        { type: 'text', text: 'Step 2', state: 'done' },
    ]

Streaming Example - LLM generating a response as a step:
    StartStepChunk()                                    # Marker added to parts
    TextStartChunk(id="llm-response")                   # Text part added to parts
    TextDeltaChunk(id="llm-response", delta="The ")     # Updates text in parts
    TextDeltaChunk(id="llm-response", delta="answer ")  # Updates text in parts
    TextDeltaChunk(id="llm-response", delta="is 42")    # Updates text in parts
    TextEndChunk(id="llm-response")                     # Marks text as done
    FinishStepChunk()                                   # Resets active parts

Streaming Example - File writer status as a step:
    StartStepChunk()                                    # Marker added to parts
    TextStartChunk(id="file-status")                    # Text part added to parts
    TextDeltaChunk(id="file-status", delta="Writing 3 records...")
    TextEndChunk(id="file-status")                      # Marks text as done
    FinishStepChunk()                                   # Resets active parts

Streaming Example - Multiple steps in sequence:
    StartStepChunk()                                    # Step 1 marker
    TextStartChunk(id="step1")
    TextDeltaChunk(id="step1", delta="Step 1 content")
    TextEndChunk(id="step1")
    FinishStepChunk()                                   # Resets for next step

    StartStepChunk()                                    # Step 2 marker
    TextStartChunk(id="step2")
    TextDeltaChunk(id="step2", delta="Step 2 content")
    TextEndChunk(id="step2")
    FinishStepChunk()                                   # Resets for next step

## Tool Execution

Tools have a multi-stage lifecycle:

1. ToolInputStartChunk - Begin receiving tool input
2. ToolInputDeltaChunk - Incremental input text (JSON being parsed)
3. ToolInputAvailableChunk - Complete input ready, tool can execute
4. ToolOutputAvailableChunk - Tool completed successfully
   OR ToolOutputErrorChunk - Tool execution failed

## Complete Message Stream Pattern

    StartChunk(messageId="msg-123")
    StartStepChunk()
    TextStartChunk(id="text-1")
    TextDeltaChunk(id="text-1", delta="Hello")
    TextDeltaChunk(id="text-1", delta=" world")
    TextEndChunk(id="text-1")
    FinishStepChunk()
    FinishChunk()
"""

from __future__ import annotations

from typing import Any, Literal, Union

from pydantic import BaseModel, Field


# Provider metadata
class ProviderMetadata(BaseModel):
    """Provider-specific metadata.

    Reproduces: ProviderMetadata
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/types/provider-metadata.ts
    """

    model_config = {"extra": "allow"}


# UI Message Parts (final state in UIMessage.parts)
# https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui/ui-messages.ts
class TextUIPart(BaseModel):
    """A text part of a message.

    Reproduces: TextUIPart
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui/ui-messages.ts
    """

    type: Literal["text"] = "text"
    text: str
    state: Literal["streaming", "done"] | None = None
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class ReasoningUIPart(BaseModel):
    """A reasoning part of a message.

    Reproduces: ReasoningUIPart
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui/ui-messages.ts
    """

    type: Literal["reasoning"] = "reasoning"
    text: str
    state: Literal["streaming", "done"] | None = None
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class SourceUrlUIPart(BaseModel):
    """A source URL part of a message.

    Reproduces: SourceUrlUIPart
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui/ui-messages.ts
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

    Reproduces: SourceDocumentUIPart
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui/ui-messages.ts
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

    Reproduces: FileUIPart
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui/ui-messages.ts
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

    Reproduces: StepStartUIPart
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui/ui-messages.ts
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

    Reproduces: UIMessage
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui/ui-messages.ts
    """

    id: str
    role: Literal["system", "user", "assistant"]
    metadata: dict[str, Any] | None = None
    parts: list[UIMessagePart]


# Chat Request (the request body sent from frontend)
class ChatRequest(BaseModel):
    """Chat request format sent from AI SDK UI/React.

    Reproduces: ChatRequest
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui/chat-transport.ts
    """

    id: str  # chatId
    messages: list[UIMessage]
    trigger: Literal["submit-message", "regenerate-message"]
    message_id: str | None = Field(default=None, alias="messageId")


class CompletionRequest(BaseModel):
    """Completion request format sent from AI SDK UI/React useCompletion hook.

    The useCompletion hook sends { prompt: string, ...body } where body can
    contain any additional fields needed by the flow.

    Reproduces: Request body from useCompletion
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui/call-completion-api.ts
    """

    prompt: str
    model_config = {"extra": "allow"}  # Allow arbitrary additional fields


# UI Message Chunks (streaming events)
# https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts


class TextStartChunk(BaseModel):
    """Text start chunk - begins a text content section.

    Reproduces: UIMessageChunk (text-start variant)
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts
    """

    type: Literal["text-start"] = "text-start"
    id: str
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class TextDeltaChunk(BaseModel):
    """Text delta chunk - incremental text content.

    Reproduces: UIMessageChunk (text-delta variant)
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts
    """

    type: Literal["text-delta"] = "text-delta"
    id: str
    delta: str
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class TextEndChunk(BaseModel):
    """Text end chunk - completes a text content section.

    Reproduces: UIMessageChunk (text-end variant)
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts
    """

    type: Literal["text-end"] = "text-end"
    id: str
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class ReasoningStartChunk(BaseModel):
    """Reasoning start chunk - begins a reasoning section.

    Reproduces: UIMessageChunk (reasoning-start variant)
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts
    """

    type: Literal["reasoning-start"] = "reasoning-start"
    id: str
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class ReasoningDeltaChunk(BaseModel):
    """Reasoning delta chunk - incremental reasoning content.

    Reproduces: UIMessageChunk (reasoning-delta variant)
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts
    """

    type: Literal["reasoning-delta"] = "reasoning-delta"
    id: str
    delta: str
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class ReasoningEndChunk(BaseModel):
    """Reasoning end chunk - completes a reasoning section.

    Reproduces: UIMessageChunk (reasoning-end variant)
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts
    """

    type: Literal["reasoning-end"] = "reasoning-end"
    id: str
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class ToolInputStartChunk(BaseModel):
    """Tool input start chunk - begins tool input streaming.

    Reproduces: UIMessageChunk (tool-input-start variant)
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts
    """

    type: Literal["tool-input-start"] = "tool-input-start"
    tool_call_id: str = Field(alias="toolCallId")
    tool_name: str = Field(alias="toolName")
    provider_executed: bool | None = Field(
        default=None, alias="providerExecuted"
    )
    dynamic: bool | None = None


class ToolInputDeltaChunk(BaseModel):
    """Tool input delta chunk - incremental tool input text.

    Reproduces: UIMessageChunk (tool-input-delta variant)
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts
    """

    type: Literal["tool-input-delta"] = "tool-input-delta"
    tool_call_id: str = Field(alias="toolCallId")
    input_text_delta: str = Field(alias="inputTextDelta")


class ToolInputAvailableChunk(BaseModel):
    """Tool input available chunk - complete tool input ready.

    Reproduces: UIMessageChunk (tool-input-available variant)
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts
    """

    type: Literal["tool-input-available"] = "tool-input-available"
    tool_call_id: str = Field(alias="toolCallId")
    tool_name: str = Field(alias="toolName")
    input: Any
    provider_executed: bool | None = Field(
        default=None, alias="providerExecuted"
    )
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )
    dynamic: bool | None = None


class ToolOutputAvailableChunk(BaseModel):
    """Tool output available chunk - tool execution completed.

    Reproduces: UIMessageChunk (tool-output-available variant)
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts
    """

    type: Literal["tool-output-available"] = "tool-output-available"
    tool_call_id: str = Field(alias="toolCallId")
    output: Any
    provider_executed: bool | None = Field(
        default=None, alias="providerExecuted"
    )
    dynamic: bool | None = None


class ToolOutputErrorChunk(BaseModel):
    """Tool output error chunk - tool execution failed.

    Reproduces: UIMessageChunk (tool-output-error variant)
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts
    """

    type: Literal["tool-output-error"] = "tool-output-error"
    tool_call_id: str = Field(alias="toolCallId")
    error_text: str = Field(alias="errorText")
    provider_executed: bool | None = Field(
        default=None, alias="providerExecuted"
    )
    dynamic: bool | None = None


class SourceUrlChunk(BaseModel):
    """Source URL chunk - references a URL source.

    Reproduces: UIMessageChunk (source-url variant)
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts
    """

    type: Literal["source-url"] = "source-url"
    source_id: str = Field(alias="sourceId")
    url: str
    title: str | None = None
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class SourceDocumentChunk(BaseModel):
    """Source document chunk - references a document source.

    Reproduces: UIMessageChunk (source-document variant)
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts
    """

    type: Literal["source-document"] = "source-document"
    source_id: str = Field(alias="sourceId")
    media_type: str = Field(alias="mediaType")
    title: str
    filename: str | None = None
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class FileChunk(BaseModel):
    """File chunk - includes a file in the message.

    Reproduces: UIMessageChunk (file variant)
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts
    """

    type: Literal["file"] = "file"
    url: str
    media_type: str = Field(alias="mediaType")
    provider_metadata: ProviderMetadata | None = Field(
        default=None, alias="providerMetadata"
    )


class ErrorChunk(BaseModel):
    """Error chunk - signals an error occurred.

    Reproduces: UIMessageChunk (error variant)
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts
    """

    type: Literal["error"] = "error"
    error_text: str = Field(alias="errorText")


class StartStepChunk(BaseModel):
    """Start step chunk - marks the beginning of a step boundary.

    This is a boundary marker with NO fields. Content between
    start-step and finish-step is grouped as a single step in the UI.

    Reproduces: UIMessageChunk (start-step variant)
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts

    Example usage:
        StartStepChunk()
        TextStartChunk(id="step-1-text")
        TextDeltaChunk(id="step-1-text", delta="Processing...")
        TextEndChunk(id="step-1-text")
        FinishStepChunk()
    """

    type: Literal["start-step"] = "start-step"


class FinishStepChunk(BaseModel):
    """Finish step chunk - marks the end of a step boundary.

    This is a boundary marker with NO fields. When received, it
    resets activeTextParts and activeReasoningParts in the processor.

    Reproduces: UIMessageChunk (finish-step variant)
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts
    """

    type: Literal["finish-step"] = "finish-step"


class StartChunk(BaseModel):
    """Start chunk - marks the beginning of message streaming.

    Reproduces: UIMessageChunk (start variant)
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts
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
    """Finish chunk - marks the completion of message streaming.

    Reproduces: UIMessageChunk (finish variant)
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts
    """

    type: Literal["finish"] = "finish"
    message_metadata: dict[str, Any] | None = Field(
        default=None, alias="messageMetadata"
    )


class AbortChunk(BaseModel):
    """Abort chunk - signals streaming was aborted.

    Reproduces: UIMessageChunk (abort variant)
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts
    """

    type: Literal["abort"] = "abort"


class MessageMetadataChunk(BaseModel):
    """Message metadata chunk - updates message metadata during stream.

    Reproduces: UIMessageChunk (message-metadata variant)
    https://github.com/vercel/ai/blob/ai@5.0.2/packages/ai/src/ui-message-stream/ui-message-chunks.ts
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
    ToolInputStartChunk,
    ToolInputDeltaChunk,
    ToolInputAvailableChunk,
    ToolOutputAvailableChunk,
    ToolOutputErrorChunk,
    SourceUrlChunk,
    SourceDocumentChunk,
    FileChunk,
    ErrorChunk,
    StartStepChunk,
    FinishStepChunk,
    StartChunk,
    FinishChunk,
    AbortChunk,
    MessageMetadataChunk,
]
