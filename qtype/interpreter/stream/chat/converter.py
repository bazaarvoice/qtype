"""
Converter for transforming StreamEvents to Vercel AI SDK UIMessageChunks.

This module provides a stateful converter that transforms internal StreamEvent
types (emitted by step executors) into Vercel AI SDK UIMessageChunk types
suitable for streaming to the frontend via SSE.

Usage:
    converter = StreamEventConverter()
    for event in stream_events:
        for chunk in converter.convert(event):
            # Send chunk to frontend
            yield f"data: {chunk.model_dump_json(by_alias=True)}\n\n"
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Iterator
from typing import Any

from qtype.interpreter.stream.chat.vercel import (
    ErrorChunk,
    FinishChunk,
    FinishStepChunk,
    MessageMetadataChunk,
    ReasoningDeltaChunk,
    ReasoningEndChunk,
    ReasoningStartChunk,
    StartChunk,
    StartStepChunk,
    TextDeltaChunk,
    TextEndChunk,
    TextStartChunk,
    ToolInputAvailableChunk,
    ToolInputDeltaChunk,
    ToolInputStartChunk,
    ToolOutputAvailableChunk,
    ToolOutputErrorChunk,
    UIMessageChunk,
)
from qtype.interpreter.types import (
    ErrorEvent,
    ReasoningStreamDeltaEvent,
    ReasoningStreamEndEvent,
    ReasoningStreamStartEvent,
    StatusEvent,
    StepEndEvent,
    StepStartEvent,
    StreamEvent,
    TextStreamDeltaEvent,
    TextStreamEndEvent,
    TextStreamStartEvent,
    ToolExecutionEndEvent,
    ToolExecutionErrorEvent,
    ToolExecutionStartEvent,
)


class StreamEventConverter:
    """
    Converts internal StreamEvents to Vercel AI SDK UIMessageChunks.

    This converter maintains state to track active text streams and generates
    appropriate Vercel chunks for each event type. Some events map to multiple
    chunks (e.g., StatusEvent becomes a wrapped step with text chunks).

    Example:
        ```python
        converter = StreamEventConverter()

        # Convert a status message
        event = StatusEvent(step=step, message="Processing...")
        for chunk in converter.convert(event):
            # Yields: StartStepChunk, TextStartChunk, TextDeltaChunk,
            #         TextEndChunk, FinishStepChunk
            send_to_client(chunk)

        # Convert text streaming
        start_event = TextStreamStartEvent(step=step, stream_id="s1")
        for chunk in converter.convert(start_event):
            # Yields: TextStartChunk
            send_to_client(chunk)

        delta_event = TextStreamDeltaEvent(
            step=step, stream_id="s1", delta="Hello"
        )
        for chunk in converter.convert(delta_event):
            # Yields: TextDeltaChunk
            send_to_client(chunk)
        ```
    """

    def __init__(self) -> None:
        """Initialize the converter with empty state."""
        # Map stream_id to Vercel chunk_id for all streams (text, reasoning, etc.)
        self._active_streams: dict[str, str] = {}

    def convert(self, event: StreamEvent) -> Iterator[UIMessageChunk]:
        """
        Convert a StreamEvent to one or more Vercel UIMessageChunks.

        Args:
            event: The StreamEvent to convert

        Yields:
            One or more UIMessageChunk instances
        """
        # Use pattern matching for clean dispatch
        match event.type:
            case "text_stream_start":
                yield from self._convert_text_stream_start(event)  # type: ignore[arg-type]
            case "text_stream_delta":
                yield from self._convert_text_stream_delta(event)  # type: ignore[arg-type]
            case "text_stream_end":
                yield from self._convert_text_stream_end(event)  # type: ignore[arg-type]
            case "reasoning_stream_start":
                yield from self._convert_reasoning_stream_start(event)  # type: ignore[arg-type]
            case "reasoning_stream_delta":
                yield from self._convert_reasoning_stream_delta(event)  # type: ignore[arg-type]
            case "reasoning_stream_end":
                yield from self._convert_reasoning_stream_end(event)  # type: ignore[arg-type]
            case "status":
                yield from self._convert_status(event)  # type: ignore[arg-type]
            case "step_start":
                yield from self._convert_step_start(event)  # type: ignore[arg-type]
            case "step_end":
                yield from self._convert_step_end(event)  # type: ignore[arg-type]
            case "tool_execution_start":
                yield from self._convert_tool_execution_start(event)  # type: ignore[arg-type]
            case "tool_execution_end":
                yield from self._convert_tool_execution_end(event)  # type: ignore[arg-type]
            case "tool_execution_error":
                yield from self._convert_tool_execution_error(event)  # type: ignore[arg-type]
            case "error":
                yield from self._convert_error(event)  # type: ignore[arg-type]
            case _:
                # Unknown event type - log warning but don't fail
                pass

    def _convert_text_stream_start(
        self, event: TextStreamStartEvent
    ) -> Iterator[UIMessageChunk]:
        """
        Convert TextStreamStartEvent to TextStartChunk.

        Registers the stream_id and creates a new Vercel chunk ID.
        """
        chunk_id = str(uuid.uuid4())
        self._active_streams[event.stream_id] = chunk_id
        yield TextStartChunk(id=chunk_id)

    def _convert_text_stream_delta(
        self, event: TextStreamDeltaEvent
    ) -> Iterator[UIMessageChunk]:
        """
        Convert TextStreamDeltaEvent to TextDeltaChunk.

        Uses the chunk ID registered during text_stream_start.
        """
        chunk_id = self._active_streams.get(event.stream_id)
        if chunk_id:
            yield TextDeltaChunk(id=chunk_id, delta=event.delta)

    def _convert_reasoning_stream_delta(
        self, event: ReasoningStreamDeltaEvent
    ) -> Iterator[UIMessageChunk]:
        """
        Convert ReasoningStreamDeltaEvent to ReasoningDeltaChunk.

        Uses the chunk ID registered during text_stream_start.
        """
        chunk_id = self._active_streams.get(event.stream_id)
        if chunk_id:
            yield ReasoningDeltaChunk(id=chunk_id, delta=event.delta)

    def _convert_text_stream_end(
        self, event: TextStreamEndEvent
    ) -> Iterator[UIMessageChunk]:
        """
        Convert TextStreamEndEvent to TextEndChunk.

        Cleans up the stream_id registration.
        """
        chunk_id = self._active_streams.pop(event.stream_id, None)
        if chunk_id:
            yield TextEndChunk(id=chunk_id)

    def _convert_reasoning_stream_start(
        self, event: ReasoningStreamStartEvent
    ) -> Iterator[UIMessageChunk]:
        """
        Convert ReasoningStreamStartEvent to ReasoningStartChunk.

        Registers the stream_id and creates a new Vercel chunk ID for reasoning.
        """
        chunk_id = str(uuid.uuid4())
        self._active_streams[event.stream_id] = chunk_id
        yield ReasoningStartChunk(id=chunk_id)

    def _convert_reasoning_stream_delta(
        self, event: ReasoningStreamDeltaEvent
    ) -> Iterator[UIMessageChunk]:
        """
        Convert ReasoningStreamDeltaEvent to ReasoningDeltaChunk.

        Uses the chunk ID registered during reasoning_stream_start.
        """
        chunk_id = self._active_streams.get(event.stream_id)
        if chunk_id:
            yield ReasoningDeltaChunk(id=chunk_id, delta=event.delta)

    def _convert_reasoning_stream_end(
        self, event: ReasoningStreamEndEvent
    ) -> Iterator[UIMessageChunk]:
        """
        Convert ReasoningStreamEndEvent to ReasoningEndChunk.

        Cleans up the stream_id registration.
        """
        chunk_id = self._active_streams.pop(event.stream_id, None)
        if chunk_id:
            yield ReasoningEndChunk(id=chunk_id)

    def _convert_status(self, event: StatusEvent) -> Iterator[UIMessageChunk]:
        """
        Convert StatusEvent to MessageMetadataChunk.

        Status messages are sent as message metadata with the 'statusMessage'
        key, allowing the frontend to display them separately from content.
        """
        yield MessageMetadataChunk(
            messageMetadata={"statusMessage": event.message}
        )

    def _convert_step_start(
        self, event: StepStartEvent
    ) -> Iterator[UIMessageChunk]:
        """Convert StepStartEvent to StartStepChunk."""
        yield StartStepChunk()
        yield MessageMetadataChunk(messageMetadata={"step_id": event.step.id})

    def _convert_step_end(
        self, event: StepEndEvent
    ) -> Iterator[UIMessageChunk]:
        """Convert StepEndEvent to FinishStepChunk."""
        yield FinishStepChunk()

    def _convert_tool_execution_start(
        self, event: ToolExecutionStartEvent
    ) -> Iterator[UIMessageChunk]:
        """
        Convert ToolExecutionStartEvent to proper tool input sequence.

        Following Vercel's protocol:
        1. ToolInputStartChunk - Begin receiving tool input
        2. ToolInputDeltaChunk - Incremental input text (JSON being parsed)
        3. ToolInputAvailableChunk - Complete input ready, tool can execute
        """
        # 1. Start tool input streaming
        yield ToolInputStartChunk(
            toolCallId=event.tool_call_id,
            toolName=event.tool_name,
            providerExecuted=True,  # Tools are executed on the server
        )

        # 2. Stream the input as JSON text delta
        import json

        input_json = json.dumps(event.tool_input)
        yield ToolInputDeltaChunk(
            toolCallId=event.tool_call_id,
            inputTextDelta=input_json,
        )

        # 3. Signal input is complete and ready for execution
        yield ToolInputAvailableChunk(
            toolCallId=event.tool_call_id,
            toolName=event.tool_name,
            input=event.tool_input,
            providerExecuted=True,  # Tools are executed on the server
        )

    def _convert_tool_execution_end(
        self, event: ToolExecutionEndEvent
    ) -> Iterator[UIMessageChunk]:
        """
        Convert ToolExecutionEndEvent to ToolOutputAvailableChunk.

        Signals successful tool completion with output.
        """
        yield ToolOutputAvailableChunk(
            toolCallId=event.tool_call_id,
            output=event.tool_output,
            providerExecuted=True,  # Tools are executed on the server
        )

    def _convert_tool_execution_error(
        self, event: ToolExecutionErrorEvent
    ) -> Iterator[UIMessageChunk]:
        """
        Convert ToolExecutionErrorEvent to ToolOutputErrorChunk.

        Signals tool execution failure with error message.
        """
        yield ToolOutputErrorChunk(
            toolCallId=event.tool_call_id,
            errorText=event.error_message,
            providerExecuted=True,  # Tools are executed on the server
        )

    def _convert_error(self, event: ErrorEvent) -> Iterator[UIMessageChunk]:
        """
        Convert ErrorEvent to ErrorChunk.

        General error that occurred during execution.
        """
        yield ErrorChunk(errorText=event.error_message)


async def format_stream_events_as_sse(
    event_stream: AsyncIterator[StreamEvent | None],
    message_id: str | None = None,
    output_metadata: dict[str, Any] | None = None,
) -> AsyncIterator[str]:
    """
    Convert a stream of StreamEvents to SSE-formatted strings.

    This function orchestrates the conversion of StreamEvents to
    UIMessageChunks and formats them as Server-Sent Events for
    the Vercel AI SDK protocol.

    Args:
        event_stream: Async iterator yielding StreamEvents (None signals end)
        message_id: Optional message ID (generated if not provided)
        output_metadata: Optional dict to include in FinishChunk metadata

    Yields:
        SSE formatted strings (data: {json}\\n\\n)

    Example:
        ```python
        async def stream_events():
            yield StatusEvent(step=step, message="Processing...")
            yield TextStreamStartEvent(step=step, stream_id="s1")
            yield TextStreamDeltaEvent(step=step, stream_id="s1", delta="Hi")
            yield TextStreamEndEvent(step=step, stream_id="s1")
            yield None  # Signal completion

        async for sse_line in format_stream_events_as_sse(
            stream_events(),
            output_metadata={"result": "success"}
        ):
            # Send to client via StreamingResponse
            pass
        ```
    """
    # Start message with unique ID
    if message_id is None:
        message_id = str(uuid.uuid4())

    start_chunk = StartChunk(messageId=message_id)  # type: ignore[arg-type]
    yield (
        f"data: "
        f"{start_chunk.model_dump_json(by_alias=True, exclude_none=True)}"
        f"\n\n"
    )

    # Create converter for stateful event-to-chunk conversion
    converter = StreamEventConverter()

    # Process events and convert to chunks
    async for event in event_stream:
        if event is None:
            break  # End of stream

        # Convert event to chunks and yield as SSE
        for chunk in converter.convert(event):
            yield (
                f"data: "
                f"{chunk.model_dump_json(by_alias=True, exclude_none=True)}"
                f"\n\n"
            )

    # End message stream with optional metadata
    finish_chunk = FinishChunk(messageMetadata=output_metadata)  # type: ignore[arg-type]
    yield (
        f"data: "
        f"{finish_chunk.model_dump_json(by_alias=True, exclude_none=True)}"
        f"\n\n"
    )
