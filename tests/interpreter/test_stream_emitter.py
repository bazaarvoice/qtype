"""
Tests for stream emitter context managers.
"""

from __future__ import annotations

import pytest

from qtype.dsl.model import StepCardinality
from qtype.interpreter.base.stream_emitter import (
    StepBoundaryContext,
    StreamEmitter,
    TextStreamContext,
    ToolExecutionContext,
)
from qtype.interpreter.types import (
    ErrorEvent,
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
from qtype.semantic.model import Step


@pytest.fixture
def mock_step():
    """Create a mock step for testing."""
    return Step(id="test-step", type="test", cardinality=StepCardinality.one)


@pytest.fixture
def event_collector():
    """Create a collector that captures emitted events."""
    events: list[StreamEvent] = []

    async def collect(event: StreamEvent) -> None:
        events.append(event)

    collect.events = events  # type: ignore[attr-defined]
    return collect


class TestTextStreamContext:
    """Tests for TextStreamContext."""

    async def test_text_stream_emits_start_and_end(
        self, mock_step, event_collector
    ):
        """Test that entering/exiting emits start and end events."""
        ctx = TextStreamContext(mock_step, "stream-1", event_collector)

        async with ctx:
            pass

        assert len(event_collector.events) == 2  # type: ignore[attr-defined]
        assert isinstance(
            event_collector.events[0],
            TextStreamStartEvent,  # type: ignore[attr-defined]
        )
        assert (
            event_collector.events[0].stream_id == "stream-1"  # type: ignore[attr-defined]
        )
        assert isinstance(
            event_collector.events[1],
            TextStreamEndEvent,  # type: ignore[attr-defined]
        )
        assert (
            event_collector.events[1].stream_id == "stream-1"  # type: ignore[attr-defined]
        )

    async def test_text_stream_delta(self, mock_step, event_collector):
        """Test that delta() emits delta events."""
        ctx = TextStreamContext(mock_step, "stream-1", event_collector)

        async with ctx as streamer:
            await streamer.delta("Hello ")
            await streamer.delta("world")

        events = event_collector.events  # type: ignore[attr-defined]
        assert len(events) == 4  # start, delta, delta, end
        assert isinstance(events[1], TextStreamDeltaEvent)
        assert events[1].delta == "Hello "
        assert isinstance(events[2], TextStreamDeltaEvent)
        assert events[2].delta == "world"

    async def test_text_stream_with_none_callback(self, mock_step):
        """Test that context manager works with None callback."""
        ctx = TextStreamContext(mock_step, "stream-1", None)

        async with ctx as streamer:
            await streamer.delta("Hello")

        # No errors should occur


class TestStepBoundaryContext:
    """Tests for StepBoundaryContext."""

    async def test_step_boundary_emits_start_and_end(
        self, mock_step, event_collector
    ):
        """Test that entering/exiting emits step start and end events."""
        ctx = StepBoundaryContext(mock_step, event_collector)

        async with ctx:
            pass

        assert len(event_collector.events) == 2  # type: ignore[attr-defined]
        assert isinstance(
            event_collector.events[0],
            StepStartEvent,  # type: ignore[attr-defined]
        )
        assert isinstance(
            event_collector.events[1],
            StepEndEvent,  # type: ignore[attr-defined]
        )

    async def test_step_boundary_with_none_callback(self, mock_step):
        """Test that context manager works with None callback."""
        ctx = StepBoundaryContext(mock_step, None)

        async with ctx:
            pass

        # No errors should occur


class TestToolExecutionContext:
    """Tests for ToolExecutionContext."""

    async def test_tool_execution_with_complete(
        self, mock_step, event_collector
    ):
        """Test tool execution that completes successfully."""
        ctx = ToolExecutionContext(
            mock_step,
            "tool-1",
            "search",
            {"query": "test"},
            event_collector,
        )

        async with ctx as tool_ctx:
            await tool_ctx.complete({"results": ["a", "b"]})

        events = event_collector.events  # type: ignore[attr-defined]
        assert len(events) == 2
        assert isinstance(events[0], ToolExecutionStartEvent)
        assert events[0].tool_call_id == "tool-1"
        assert events[0].tool_name == "search"
        assert events[0].tool_input == {"query": "test"}
        assert isinstance(events[1], ToolExecutionEndEvent)
        assert events[1].tool_output == {"results": ["a", "b"]}

    async def test_tool_execution_with_error(self, mock_step, event_collector):
        """Test tool execution that explicitly reports an error."""
        ctx = ToolExecutionContext(
            mock_step,
            "tool-1",
            "search",
            {"query": "test"},
            event_collector,
        )

        async with ctx as tool_ctx:
            await tool_ctx.error("Connection timeout")

        events = event_collector.events  # type: ignore[attr-defined]
        assert len(events) == 2
        assert isinstance(events[0], ToolExecutionStartEvent)
        assert isinstance(events[1], ToolExecutionErrorEvent)
        assert events[1].error_message == "Connection timeout"

    async def test_tool_execution_with_exception(
        self, mock_step, event_collector
    ):
        """Test tool execution that raises an exception."""
        ctx = ToolExecutionContext(
            mock_step,
            "tool-1",
            "search",
            {"query": "test"},
            event_collector,
        )

        with pytest.raises(ValueError, match="Something went wrong"):
            async with ctx:
                raise ValueError("Something went wrong")

        events = event_collector.events  # type: ignore[attr-defined]
        assert len(events) == 2
        assert isinstance(events[0], ToolExecutionStartEvent)
        assert isinstance(events[1], ToolExecutionErrorEvent)
        assert "Something went wrong" in events[1].error_message

    async def test_tool_execution_with_none_callback(self, mock_step):
        """Test that context manager works with None callback."""
        ctx = ToolExecutionContext(
            mock_step, "tool-1", "search", {"query": "test"}, None
        )

        async with ctx as tool_ctx:
            await tool_ctx.complete({"results": []})

        # No errors should occur


class TestStreamEmitter:
    """Tests for StreamEmitter."""

    async def test_stream_emitter_status(self, mock_step, event_collector):
        """Test that status() emits a status event."""
        emitter = StreamEmitter(mock_step, event_collector)
        await emitter.status("Processing...")

        events = event_collector.events  # type: ignore[attr-defined]
        assert len(events) == 1
        assert isinstance(events[0], StatusEvent)
        assert events[0].message == "Processing..."

    async def test_stream_emitter_error(self, mock_step, event_collector):
        """Test that error() emits an error event."""
        emitter = StreamEmitter(mock_step, event_collector)
        await emitter.error("Something failed")

        events = event_collector.events  # type: ignore[attr-defined]
        assert len(events) == 1
        assert isinstance(events[0], ErrorEvent)
        assert events[0].error_message == "Something failed"

    async def test_stream_emitter_text_stream_factory(
        self, mock_step, event_collector
    ):
        """Test that text_stream() returns a TextStreamContext."""
        emitter = StreamEmitter(mock_step, event_collector)
        ctx = emitter.text_stream("stream-1")

        assert isinstance(ctx, TextStreamContext)
        assert ctx.stream_id == "stream-1"

    async def test_stream_emitter_step_boundary_factory(
        self, mock_step, event_collector
    ):
        """Test that step_boundary() returns a StepBoundaryContext."""
        emitter = StreamEmitter(mock_step, event_collector)
        ctx = emitter.step_boundary()

        assert isinstance(ctx, StepBoundaryContext)

    async def test_stream_emitter_tool_execution_factory(
        self, mock_step, event_collector
    ):
        """Test that tool_execution() returns a ToolExecutionContext."""
        emitter = StreamEmitter(mock_step, event_collector)
        ctx = emitter.tool_execution("tool-1", "search", {"query": "test"})

        assert isinstance(ctx, ToolExecutionContext)
        assert ctx.tool_call_id == "tool-1"
        assert ctx.tool_name == "search"
        assert ctx.tool_input == {"query": "test"}

    async def test_stream_emitter_with_none_callback(self, mock_step):
        """Test that all methods work with None callback."""
        emitter = StreamEmitter(mock_step, None)

        await emitter.status("Processing...")
        await emitter.error("Something failed")

        async with emitter.text_stream("stream-1") as streamer:
            await streamer.delta("Hello")

        async with emitter.step_boundary():
            pass

        async with emitter.tool_execution(
            "tool-1", "search", {"query": "test"}
        ) as tool:
            await tool.complete({"results": []})

        # No errors should occur


class TestIntegrationScenarios:
    """Integration tests for realistic usage scenarios."""

    async def test_llm_inference_scenario(self, mock_step, event_collector):
        """Test a realistic LLM inference scenario with text streaming."""
        emitter = StreamEmitter(mock_step, event_collector)

        await emitter.status("Starting LLM inference...")

        async with emitter.step_boundary():
            async with emitter.text_stream("llm-response") as streamer:
                await streamer.delta("The ")
                await streamer.delta("answer ")
                await streamer.delta("is 42")

        await emitter.status("LLM inference complete")

        events = event_collector.events  # type: ignore[attr-defined]
        assert len(events) == 9
        assert isinstance(events[0], StatusEvent)
        assert isinstance(events[1], StepStartEvent)
        assert isinstance(events[2], TextStreamStartEvent)
        assert isinstance(events[3], TextStreamDeltaEvent)
        assert isinstance(events[4], TextStreamDeltaEvent)
        assert isinstance(events[5], TextStreamDeltaEvent)
        assert isinstance(events[6], TextStreamEndEvent)
        assert isinstance(events[7], StepEndEvent)
        assert isinstance(events[8], StatusEvent)

    async def test_tool_execution_scenario(self, mock_step, event_collector):
        """Test a realistic tool execution scenario."""
        emitter = StreamEmitter(mock_step, event_collector)

        await emitter.status("Executing search tool...")

        async with emitter.tool_execution(
            tool_call_id="search-1",
            tool_name="search",
            tool_input={"query": "Python tutorials"},
        ) as tool:
            # Simulate tool execution
            result = {"results": ["result1", "result2"]}
            await tool.complete(result)

        await emitter.status("Search complete")

        events = event_collector.events  # type: ignore[attr-defined]
        assert len(events) == 4
        assert isinstance(events[0], StatusEvent)
        assert isinstance(events[1], ToolExecutionStartEvent)
        assert isinstance(events[2], ToolExecutionEndEvent)
        assert isinstance(events[3], StatusEvent)
