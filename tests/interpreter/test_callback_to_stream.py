"""Tests for callback_to_async_iterator utility."""

from __future__ import annotations

import pytest

from qtype.interpreter.stream.utils.callback_to_stream import (
    callback_to_async_iterator,
)


class TestCallbackToAsyncIterator:
    """Tests for callback_to_async_iterator function."""

    @pytest.mark.asyncio
    async def test_basic_conversion(self):
        """Test basic callback to async iterator conversion."""
        events = []

        async def task_with_callback(callback):  # type: ignore[no-untyped-def]
            await callback("event1")
            await callback("event2")
            await callback("event3")

        async for event in callback_to_async_iterator(task_with_callback):
            events.append(event)

        assert events == ["event1", "event2", "event3"]

    @pytest.mark.asyncio
    async def test_empty_stream(self):
        """Test conversion with no events."""
        events = []

        async def task_with_callback(callback):  # type: ignore[no-untyped-def]
            # Don't call callback at all
            pass

        async for event in callback_to_async_iterator(task_with_callback):
            events.append(event)

        assert events == []

    @pytest.mark.asyncio
    async def test_exception_in_task(self):
        """Test that exceptions from task are propagated."""

        async def failing_task(callback):  # type: ignore[no-untyped-def]
            await callback("event1")
            raise ValueError("Task failed")

        with pytest.raises(ValueError, match="Task failed"):
            async for event in callback_to_async_iterator(failing_task):
                pass  # Just consume the iterator

    @pytest.mark.asyncio
    async def test_complex_objects(self):
        """Test with complex event objects."""
        events = []

        async def task_with_callback(callback):  # type: ignore[no-untyped-def]
            await callback({"type": "start", "id": 1})
            await callback({"type": "data", "value": "test"})
            await callback({"type": "end", "id": 1})

        async for event in callback_to_async_iterator(task_with_callback):
            events.append(event)

        assert len(events) == 3
        assert events[0]["type"] == "start"
        assert events[1]["value"] == "test"
        assert events[2]["type"] == "end"

    @pytest.mark.asyncio
    async def test_multiple_iterations(self):
        """Test that iterator can only be consumed once."""
        call_count = 0

        async def task_with_callback(callback):  # type: ignore[no-untyped-def]
            nonlocal call_count
            call_count += 1
            await callback("event")

        # First consumption
        iterator = callback_to_async_iterator(task_with_callback)
        events1 = [e async for e in iterator]
        assert events1 == ["event"]
        assert call_count == 1

        # Can't iterate again (iterator exhausted)
        events2 = [e async for e in iterator]
        assert events2 == []
        assert call_count == 1  # Task not called again
