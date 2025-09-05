"""
Streaming helpers for bridging callback-based execution with generator patterns.

This module provides utilities to convert callback-based streaming functions
into generators that can be used with FastAPI's StreamingResponse.
"""

from __future__ import annotations

import queue
import threading
from collections.abc import Callable, Generator
from concurrent.futures import Future
from typing import Any, TypeVar

from qtype.dsl.domain_types import ChatMessage
from qtype.semantic.model import Step

T = TypeVar("T")


def create_streaming_generator(
    execution_func: Callable[..., T],
    *args: Any,
    timeout: float = 30.0,
    join_timeout: float = 5.0,
    **kwargs: Any,
) -> tuple[Generator[tuple[Step, ChatMessage | str], None, None], Future[T]]:
    """
    Convert a callback-based streaming function into a generator with result future.

    This function executes the provided function in a separate thread and
    converts its stream_fn callback pattern into a generator that yields
    (step, message) tuples. Additionally returns a Future that will contain
    the execution function's return value.

    Args:
        execution_func: Function to execute that accepts a stream_fn parameter
        *args: Positional arguments to pass to execution_func
        timeout: Timeout in seconds for queue.get() operations
        join_timeout: Timeout in seconds for thread.join()
        **kwargs: Keyword arguments to pass to execution_func

    Returns:
        Tuple of (generator, future) where:
        - generator yields (Step, ChatMessage | str) tuples from streaming callback
        - future will contain the return value of execution_func

    Example:
        ```python
        def my_flow_execution(flow: Flow, stream_fn: Callable | None = None):
            # Some execution logic that calls stream_fn(step, message)
            return {"status": "completed", "steps_executed": 3}

        # Convert to generator with result
        stream_gen, result_future = create_streaming_generator(
            my_flow_execution,
            flow_copy,
            some_other_arg="value"
        )

        # Process streaming data
        for step, message in stream_gen:
            print(f"Step {step.id}: {message}")

        # Get final result (blocks until execution completes)
        final_result = result_future.result(timeout=10.0)
        print(f"Execution result: {final_result}")
        ```
    """
    # Create thread-safe queue for communication
    stream_queue: queue.Queue[tuple[Step, ChatMessage | str] | None] = (
        queue.Queue()
    )

    # Create future for the return value
    result_future: Future[T] = Future()

    def stream_callback(step: Step, msg: ChatMessage | str) -> None:
        """Callback function that pushes data to the queue."""
        stream_queue.put((step, msg))

    def execution_task() -> None:
        """Execute the function in a separate thread."""
        try:
            # Add the stream_fn callback to kwargs
            kwargs_with_callback = kwargs.copy()
            kwargs_with_callback["stream_fn"] = stream_callback

            # Execute the function with the callback and capture result
            result = execution_func(*args, **kwargs_with_callback)
            result_future.set_result(result)
        except Exception as e:
            # Set exception on future if execution fails
            result_future.set_exception(e)
        finally:
            # Signal end of stream
            stream_queue.put(None)

    # Start execution in separate thread
    execution_thread = threading.Thread(target=execution_task)
    execution_thread.start()

    def generator() -> Generator[tuple[Step, ChatMessage | str], None, None]:
        """Generator that yields streaming data from the queue."""
        try:
            # Yield data as it becomes available
            while True:
                try:
                    # Wait for data with timeout to avoid hanging
                    data = stream_queue.get(timeout=timeout)
                    if data is None:
                        # End of stream signal
                        break
                    yield data
                except queue.Empty:
                    # Handle timeout - break and let thread cleanup
                    break
        finally:
            # Ensure thread cleanup
            execution_thread.join(timeout=join_timeout)

    return generator(), result_future
