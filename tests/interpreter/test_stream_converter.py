"""
Tests for StreamEventConverter.
"""

from __future__ import annotations

import pytest

from qtype.interpreter.stream.chat.converter import StreamEventConverter
from qtype.interpreter.stream.chat.vercel import (
    ErrorChunk,
    FinishStepChunk,
    MessageMetadataChunk,
    StartStepChunk,
    TextDeltaChunk,
    TextEndChunk,
    TextStartChunk,
    ToolInputAvailableChunk,
    ToolInputDeltaChunk,
    ToolInputStartChunk,
    ToolOutputAvailableChunk,
    ToolOutputErrorChunk,
)
from qtype.interpreter.types import (
    ErrorEvent,
    StatusEvent,
    StepEndEvent,
    StepStartEvent,
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
    return Step(id="test-step", type="test")


@pytest.fixture
def converter():
    """Create a fresh converter for each test."""
    return StreamEventConverter()


class TestTextStreamConversion:
    """Tests for text streaming event conversion."""

    def test_text_stream_start_creates_text_start_chunk(
        self, converter, mock_step
    ):
        """TextStreamStartEvent should yield TextStartChunk."""
        event = TextStreamStartEvent(step=mock_step, stream_id="stream-1")

        chunks = list(converter.convert(event))

        assert len(chunks) == 1
        assert isinstance(chunks[0], TextStartChunk)
        assert chunks[0].id  # Should have generated an ID

    def test_text_stream_delta_creates_text_delta_chunk(
        self, converter, mock_step
    ):
        """TextStreamDeltaEvent should yield TextDeltaChunk."""
        # First start the stream
        start_event = TextStreamStartEvent(
            step=mock_step, stream_id="stream-1"
        )
        start_chunks = list(converter.convert(start_event))
        chunk_id = start_chunks[0].id

        # Now send a delta
        delta_event = TextStreamDeltaEvent(
            step=mock_step, stream_id="stream-1", delta="Hello"
        )
        chunks = list(converter.convert(delta_event))

        assert len(chunks) == 1
        assert isinstance(chunks[0], TextDeltaChunk)
        assert chunks[0].id == chunk_id
        assert chunks[0].delta == "Hello"

    def test_text_stream_end_creates_text_end_chunk(
        self, converter, mock_step
    ):
        """TextStreamEndEvent should yield TextEndChunk."""
        # First start the stream
        start_event = TextStreamStartEvent(
            step=mock_step, stream_id="stream-1"
        )
        start_chunks = list(converter.convert(start_event))
        chunk_id = start_chunks[0].id

        # Now end the stream
        end_event = TextStreamEndEvent(step=mock_step, stream_id="stream-1")
        chunks = list(converter.convert(end_event))

        assert len(chunks) == 1
        assert isinstance(chunks[0], TextEndChunk)
        assert chunks[0].id == chunk_id

    def test_text_stream_maintains_id_consistency(self, converter, mock_step):
        """All chunks in a text stream should use the same ID."""
        stream_id = "stream-1"

        # Start
        start_event = TextStreamStartEvent(step=mock_step, stream_id=stream_id)
        start_chunks = list(converter.convert(start_event))
        chunk_id = start_chunks[0].id

        # Multiple deltas
        for text in ["Hello", " ", "World"]:
            delta_event = TextStreamDeltaEvent(
                step=mock_step, stream_id=stream_id, delta=text
            )
            delta_chunks = list(converter.convert(delta_event))
            assert delta_chunks[0].id == chunk_id

        # End
        end_event = TextStreamEndEvent(step=mock_step, stream_id=stream_id)
        end_chunks = list(converter.convert(end_event))
        assert end_chunks[0].id == chunk_id

    def test_multiple_concurrent_streams_have_different_ids(
        self, converter, mock_step
    ):
        """Different streams should get different chunk IDs."""
        # Start two streams
        stream1 = TextStreamStartEvent(step=mock_step, stream_id="stream-1")
        stream2 = TextStreamStartEvent(step=mock_step, stream_id="stream-2")

        chunks1 = list(converter.convert(stream1))
        chunks2 = list(converter.convert(stream2))

        assert chunks1[0].id != chunks2[0].id


class TestStatusConversion:
    """Tests for status event conversion."""

    def test_status_creates_message_metadata_chunk(self, converter, mock_step):
        """StatusEvent should yield MessageMetadataChunk with statusMessage."""
        event = StatusEvent(step=mock_step, message="Processing data...")

        chunks = list(converter.convert(event))

        assert len(chunks) == 1
        assert isinstance(chunks[0], MessageMetadataChunk)
        assert (
            chunks[0].message_metadata["statusMessage"] == "Processing data..."
        )


class TestStepBoundaryConversion:
    """Tests for step boundary event conversion."""

    def test_step_start_creates_start_step_chunk(self, converter, mock_step):
        """StepStartEvent should yield StartStepChunk and MessageMetadataChunk."""
        event = StepStartEvent(step=mock_step)

        chunks = list(converter.convert(event))

        assert len(chunks) == 2
        assert isinstance(chunks[0], StartStepChunk)
        assert isinstance(chunks[1], MessageMetadataChunk)
        assert chunks[1].message_metadata["step_id"] == mock_step.id

    def test_step_end_creates_finish_step_chunk(self, converter, mock_step):
        """StepEndEvent should yield FinishStepChunk."""
        event = StepEndEvent(step=mock_step)

        chunks = list(converter.convert(event))

        assert len(chunks) == 1
        assert isinstance(chunks[0], FinishStepChunk)


class TestToolExecutionConversion:
    """Tests for tool execution event conversion."""

    def test_tool_execution_start_creates_input_available_chunk(
        self, converter, mock_step
    ):
        """ToolExecutionStartEvent should yield 3-chunk sequence."""
        event = ToolExecutionStartEvent(
            step=mock_step,
            tool_call_id="tool-1",
            tool_name="search",
            tool_input={"query": "test"},
        )

        chunks = list(converter.convert(event))

        assert len(chunks) == 3
        assert isinstance(chunks[0], ToolInputStartChunk)
        assert chunks[0].tool_call_id == "tool-1"
        assert chunks[0].tool_name == "search"

        assert isinstance(chunks[1], ToolInputDeltaChunk)
        assert chunks[1].tool_call_id == "tool-1"

        assert isinstance(chunks[2], ToolInputAvailableChunk)
        assert chunks[2].tool_call_id == "tool-1"
        assert chunks[2].tool_name == "search"
        assert chunks[2].input == {"query": "test"}

    def test_tool_execution_end_creates_output_available_chunk(
        self, converter, mock_step
    ):
        """ToolExecutionEndEvent should yield ToolOutputAvailableChunk."""
        event = ToolExecutionEndEvent(
            step=mock_step,
            tool_call_id="tool-1",
            tool_output={"results": ["a", "b"]},
        )

        chunks = list(converter.convert(event))

        assert len(chunks) == 1
        assert isinstance(chunks[0], ToolOutputAvailableChunk)
        assert chunks[0].tool_call_id == "tool-1"
        assert chunks[0].output == {"results": ["a", "b"]}

    def test_tool_execution_error_creates_output_error_chunk(
        self, converter, mock_step
    ):
        """ToolExecutionErrorEvent should yield ToolOutputErrorChunk."""
        event = ToolExecutionErrorEvent(
            step=mock_step,
            tool_call_id="tool-1",
            error_message="Connection timeout",
        )

        chunks = list(converter.convert(event))

        assert len(chunks) == 1
        assert isinstance(chunks[0], ToolOutputErrorChunk)
        assert chunks[0].tool_call_id == "tool-1"
        assert chunks[0].error_text == "Connection timeout"


class TestErrorConversion:
    """Tests for error event conversion."""

    def test_error_creates_error_chunk(self, converter, mock_step):
        """ErrorEvent should yield ErrorChunk."""
        event = ErrorEvent(
            step=mock_step, error_message="Something went wrong"
        )

        chunks = list(converter.convert(event))

        assert len(chunks) == 1
        assert isinstance(chunks[0], ErrorChunk)
        assert chunks[0].error_text == "Something went wrong"


class TestIntegrationScenarios:
    """Integration tests for realistic conversion scenarios."""

    def test_llm_streaming_scenario(self, converter, mock_step):
        """Test converting a complete LLM streaming scenario."""
        events = [
            StepStartEvent(step=mock_step),
            TextStreamStartEvent(step=mock_step, stream_id="llm-1"),
            TextStreamDeltaEvent(
                step=mock_step, stream_id="llm-1", delta="The "
            ),
            TextStreamDeltaEvent(
                step=mock_step, stream_id="llm-1", delta="answer "
            ),
            TextStreamDeltaEvent(
                step=mock_step, stream_id="llm-1", delta="is 42"
            ),
            TextStreamEndEvent(step=mock_step, stream_id="llm-1"),
            StepEndEvent(step=mock_step),
        ]

        all_chunks = []
        for event in events:
            all_chunks.extend(converter.convert(event))

        # StepStart (2) + TextStart (1) + TextDelta (3) + TextEnd (1) + StepEnd (1) = 8
        assert len(all_chunks) == 8
        assert isinstance(all_chunks[0], StartStepChunk)
        assert isinstance(all_chunks[1], MessageMetadataChunk)  # step_id
        assert isinstance(all_chunks[2], TextStartChunk)
        assert isinstance(all_chunks[3], TextDeltaChunk)
        assert all_chunks[3].delta == "The "
        assert isinstance(all_chunks[4], TextDeltaChunk)
        assert all_chunks[4].delta == "answer "
        assert isinstance(all_chunks[5], TextDeltaChunk)
        assert all_chunks[5].delta == "is 42"
        assert isinstance(all_chunks[6], TextEndChunk)
        assert isinstance(all_chunks[7], FinishStepChunk)

    def test_file_writer_status_scenario(self, converter, mock_step):
        """Test converting file writer status messages."""
        events = [
            StatusEvent(
                step=mock_step, message="Writing 3 records to file.csv"
            ),
            StatusEvent(step=mock_step, message="Wrote 3 records to file.csv"),
        ]

        all_chunks = []
        for event in events:
            all_chunks.extend(converter.convert(event))

        # Each status becomes 1 MessageMetadataChunk
        assert len(all_chunks) == 2

        # First status
        assert isinstance(all_chunks[0], MessageMetadataChunk)
        assert (
            "Writing 3 records"
            in all_chunks[0].message_metadata["statusMessage"]
        )

        # Second status
        assert isinstance(all_chunks[1], MessageMetadataChunk)
        assert (
            "Wrote 3 records"
            in all_chunks[1].message_metadata["statusMessage"]
        )

    def test_tool_execution_scenario(self, converter, mock_step):
        """Test converting a complete tool execution."""
        events = [
            StatusEvent(step=mock_step, message="Executing search tool..."),
            ToolExecutionStartEvent(
                step=mock_step,
                tool_call_id="search-1",
                tool_name="search",
                tool_input={"query": "Python tutorials"},
            ),
            ToolExecutionEndEvent(
                step=mock_step,
                tool_call_id="search-1",
                tool_output={"results": ["result1", "result2"]},
            ),
            StatusEvent(step=mock_step, message="Search complete"),
        ]

        all_chunks = []
        for event in events:
            all_chunks.extend(converter.convert(event))

        # Status (1) + ToolStart+Delta+Available (3) + ToolOutput (1) + Status (1) = 6
        assert len(all_chunks) == 6
        assert isinstance(all_chunks[0], MessageMetadataChunk)  # Status
        assert isinstance(all_chunks[1], ToolInputStartChunk)  # Tool start
        assert isinstance(all_chunks[2], ToolInputDeltaChunk)  # Tool delta
        assert isinstance(
            all_chunks[3], ToolInputAvailableChunk
        )  # Tool available
        assert isinstance(
            all_chunks[4], ToolOutputAvailableChunk
        )  # Tool output
        assert isinstance(all_chunks[5], MessageMetadataChunk)  # Status
