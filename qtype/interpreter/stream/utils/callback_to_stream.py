"""Utilities for converting callbacks to async iterators."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def callback_to_async_iterator(
    task_fn: Callable[[Callable[[T], Awaitable[None]]], Awaitable[None]],
) -> AsyncIterator[T]:
    """
    Convert a callback-based async function to an async iterator.

    This utility bridges callback-style APIs (where you provide a callback
    that gets called with events) to async iterator style (where you yield
    events).

    Args:
        task_fn: Async function that accepts a callback. The callback
            will be called with each event. The task_fn should complete
            when done producing events.

    Yields:
        Events that were passed to the callback

    Example:
        ```python
        async def execute_with_callback(callback):
            await callback("event1")
            await callback("event2")
            # Function completes when done

        async for event in callback_to_async_iterator(execute_with_callback):
            print(event)  # Prints "event1", "event2"
        ```
    """
    queue: asyncio.Queue[T | None] = asyncio.Queue()

    async def callback(item: T) -> None:
        """Queue items as they arrive."""
        await queue.put(item)

    async def run_task() -> None:
        """Execute the task and signal completion."""
        try:
            await task_fn(callback)
        finally:
            await queue.put(None)  # Signal completion

    # Start task in background
    task = asyncio.create_task(run_task())

    try:
        # Yield items from queue until None
        while True:
            item = await queue.get()
            if item is None:
                break
            yield item
    finally:
        # Ensure task completes
        await task
