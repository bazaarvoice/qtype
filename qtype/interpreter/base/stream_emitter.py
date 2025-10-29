"""
Context managers for emitting streaming events during step execution.

This module provides a clean, idiomatic Python API for executors to emit
streaming events without directly handling the StreamEvent types.

Usage Example:
    ```python
    class MyExecutor(StepExecutor):
        async def process_message(self, message: FlowMessage):
            emitter = self.stream_emitter

            # Status update
            await emitter.status("Processing started...")

            # Text streaming
            async with emitter.text_stream("response-1") as streamer:
                async for chunk in some_generator():
                    await streamer.delta(chunk)

            # Tool execution
            async with emitter.tool_execution(
                tool_call_id="tool-1",
                tool_name="search",
                tool_input={"query": "test"}
            ) as tool_ctx:
                result = await execute_tool()
                await tool_ctx.complete(result)

            yield message
    ```
"""

from __future__ import annotations

from typing import Any

from qtype.interpreter.types import (
    ErrorEvent,
    ReasoningStreamDeltaEvent,
    ReasoningStreamEndEvent,
    ReasoningStreamStartEvent,
    StatusEvent,
    StepEndEvent,
    StepStartEvent,
    StreamingCallback,
    TextStreamDeltaEvent,
    TextStreamEndEvent,
    TextStreamStartEvent,
    ToolExecutionEndEvent,
    ToolExecutionErrorEvent,
    ToolExecutionStartEvent,
)
from qtype.semantic.model import Step


class TextStreamContext:
    """
    Async context manager for text streaming.

    Automatically emits TextStreamStartEvent on entry and TextStreamEndEvent
    on exit. Provides delta() method for emitting text chunks.

    Example:
        ```python
        async with emitter.text_stream("llm-response") as streamer:
            async for chunk in llm_client.stream():
                await streamer.delta(chunk.text)
        ```
    """

    def __init__(
        self,
        step: Step,
        stream_id: str,
        on_stream_event: StreamingCallback | None,
    ):
        self.step = step
        self.stream_id = stream_id
        self.on_stream_event = on_stream_event

    async def __aenter__(self) -> TextStreamContext:
        """Emit TextStreamStartEvent when entering context."""
        if self.on_stream_event:
            await self.on_stream_event(
                TextStreamStartEvent(step=self.step, stream_id=self.stream_id)
            )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> bool:
        """Emit TextStreamEndEvent when exiting context."""
        if self.on_stream_event:
            await self.on_stream_event(
                TextStreamEndEvent(step=self.step, stream_id=self.stream_id)
            )
        return False

    async def delta(self, text: str) -> None:
        """
        Emit a text delta chunk.

        Args:
            text: The incremental text content to append to the stream
        """
        if self.on_stream_event:
            await self.on_stream_event(
                TextStreamDeltaEvent(
                    step=self.step,
                    stream_id=self.stream_id,
                    delta=text,
                )
            )


class ReasoningStreamContext:
    """
    Async context manager for reasoning streaming.

    Automatically emits ReasoningStreamStartEvent on entry and
    ReasoningStreamEndEvent on exit. Provides delta() method for emitting
    reasoning chunks.

    Example:
        ```python
        async with emitter.reasoning_stream("agent-reasoning") as streamer:
            async for chunk in agent.stream_reasoning():
                await streamer.delta(chunk.text)
        ```
    """

    def __init__(
        self,
        step: Step,
        stream_id: str,
        on_stream_event: StreamingCallback | None,
    ):
        self.step = step
        self.stream_id = stream_id
        self.on_stream_event = on_stream_event

    async def __aenter__(self) -> ReasoningStreamContext:
        """Emit ReasoningStreamStartEvent when entering context."""
        if self.on_stream_event:
            await self.on_stream_event(
                ReasoningStreamStartEvent(
                    step=self.step, stream_id=self.stream_id
                )
            )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> bool:
        """Emit ReasoningStreamEndEvent when exiting context."""
        if self.on_stream_event:
            await self.on_stream_event(
                ReasoningStreamEndEvent(
                    step=self.step, stream_id=self.stream_id
                )
            )
        return False

    async def delta(self, text: str) -> None:
        """
        Emit a reasoning delta chunk.

        Args:
            text: The incremental reasoning content to append to the stream
        """
        if self.on_stream_event:
            await self.on_stream_event(
                ReasoningStreamDeltaEvent(
                    step=self.step,
                    stream_id=self.stream_id,
                    delta=text,
                )
            )


class StepBoundaryContext:
    """
    Async context manager for step boundaries.

    Automatically emits StepStartEvent on entry and StepEndEvent on exit.
    Use this to group related events together visually in the UI.

    Example:
        ```python
        async with emitter.step_boundary():
            await emitter.status("Step 1: Loading data...")
            # ... do work ...
            await emitter.status("Step 1: Complete")
        ```
    """

    def __init__(
        self,
        step: Step,
        on_stream_event: StreamingCallback | None,
    ):
        self.step = step
        self.on_stream_event = on_stream_event

    async def __aenter__(self) -> StepBoundaryContext:
        """Emit StepStartEvent when entering context."""
        if self.on_stream_event:
            await self.on_stream_event(StepStartEvent(step=self.step))
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> bool:
        """Emit StepEndEvent when exiting context."""
        if self.on_stream_event:
            await self.on_stream_event(StepEndEvent(step=self.step))
        return False


class ToolExecutionContext:
    """
    Async context manager for tool execution.

    Automatically emits ToolExecutionStartEvent on entry. On exit, if an
    exception occurred, emits ToolExecutionErrorEvent. Otherwise, you must
    call complete() or error() explicitly.

    Example:
        ```python
        async with emitter.tool_execution(
            tool_call_id="tool-1",
            tool_name="search",
            tool_input={"query": "test"}
        ) as tool_ctx:
            result = await execute_tool()
            await tool_ctx.complete(result)
        ```
    """

    def __init__(
        self,
        step: Step,
        tool_call_id: str,
        tool_name: str,
        tool_input: dict[str, Any],
        on_stream_event: StreamingCallback | None,
    ):
        self.step = step
        self.tool_call_id = tool_call_id
        self.tool_name = tool_name
        self.tool_input = tool_input
        self.on_stream_event = on_stream_event
        self._completed = False

    async def __aenter__(self) -> ToolExecutionContext:
        """Emit ToolExecutionStartEvent when entering context."""
        if self.on_stream_event:
            await self.on_stream_event(
                ToolExecutionStartEvent(
                    step=self.step,
                    tool_call_id=self.tool_call_id,
                    tool_name=self.tool_name,
                    tool_input=self.tool_input,
                )
            )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> bool:
        """
        Emit ToolExecutionErrorEvent if exception occurred.

        If no exception and complete()/error() wasn't called, this is a
        programming error but we don't raise to avoid masking other issues.
        """
        if exc_type is not None and self.on_stream_event:
            await self.on_stream_event(
                ToolExecutionErrorEvent(
                    step=self.step,
                    tool_call_id=self.tool_call_id,
                    error_message=str(exc_val),
                )
            )
            self._completed = True
        return False

    async def complete(self, output: Any) -> None:
        """
        Mark tool execution as complete with successful output.

        Args:
            output: The result returned by the tool
        """
        if self._completed:
            return
        if self.on_stream_event:
            await self.on_stream_event(
                ToolExecutionEndEvent(
                    step=self.step,
                    tool_call_id=self.tool_call_id,
                    tool_output=output,
                )
            )
        self._completed = True

    async def error(self, error_message: str) -> None:
        """
        Mark tool execution as failed.

        Args:
            error_message: Description of the error that occurred
        """
        if self._completed:
            return
        if self.on_stream_event:
            await self.on_stream_event(
                ToolExecutionErrorEvent(
                    step=self.step,
                    tool_call_id=self.tool_call_id,
                    error_message=error_message,
                )
            )
        self._completed = True


class StreamEmitter:
    """
    Factory for creating streaming context managers.

    This class is instantiated once per StepExecutor and provides factory
    methods for creating context managers and convenience methods for
    one-shot events.

    The executor can access this via self.stream_emitter.

    Example:
        ```python
        class MyExecutor(StepExecutor):
            async def process_message(self, message: FlowMessage):
                # One-shot status
                await self.stream_emitter.status("Processing...")

                # Text streaming
                async with self.stream_emitter.text_stream("id") as s:
                    await s.delta("Hello")

                # Step boundary
                async with self.stream_emitter.step_boundary():
                    await self.stream_emitter.status("Step content")

                # Tool execution
                async with self.stream_emitter.tool_execution(
                    "tool-1", "search", {"q": "test"}
                ) as tool:
                    result = await run_tool()
                    await tool.complete(result)

                yield message
        ```
    """

    def __init__(
        self,
        step: Step,
        on_stream_event: StreamingCallback | None,
    ):
        self.step = step
        self.on_stream_event = on_stream_event

    def text_stream(self, stream_id: str) -> TextStreamContext:
        """
        Create a context manager for text streaming.

        Args:
            stream_id: Unique identifier for this text stream

        Returns:
            Context manager that emits start/delta/end events
        """
        return TextStreamContext(self.step, stream_id, self.on_stream_event)

    def reasoning_stream(self, stream_id: str) -> ReasoningStreamContext:
        """
        Create a context manager for reasoning streaming.

        Args:
            stream_id: Unique identifier for this reasoning stream

        Returns:
            Context manager that emits start/delta/end events for reasoning
        """
        return ReasoningStreamContext(
            self.step, stream_id, self.on_stream_event
        )

    def step_boundary(self) -> StepBoundaryContext:
        """
        Create a context manager for step boundaries.

        Returns:
            Context manager that emits step start/end events
        """
        return StepBoundaryContext(self.step, self.on_stream_event)

    def tool_execution(
        self,
        tool_call_id: str,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> ToolExecutionContext:
        """
        Create a context manager for tool execution.

        Args:
            tool_call_id: Unique identifier for this tool call
            tool_name: Name of the tool being executed
            tool_input: Input parameters for the tool

        Returns:
            Context manager that emits tool execution events
        """
        return ToolExecutionContext(
            self.step,
            tool_call_id,
            tool_name,
            tool_input,
            self.on_stream_event,
        )

    async def status(self, message: str) -> None:
        """
        Emit a complete status message.

        This is a convenience method for simple status updates that don't
        require streaming.

        Args:
            message: The status message to display
        """
        if self.on_stream_event:
            await self.on_stream_event(
                StatusEvent(step=self.step, message=message)
            )

    async def error(self, error_message: str) -> None:
        """
        Emit an error event.

        Args:
            error_message: Description of the error
        """
        if self.on_stream_event:
            await self.on_stream_event(
                ErrorEvent(step=self.step, error_message=error_message)
            )
