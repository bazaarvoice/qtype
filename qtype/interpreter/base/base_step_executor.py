from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator

from aiostream import stream

from qtype.interpreter.base.progress_tracker import ProgressTracker
from qtype.interpreter.base.stream_emitter import StreamEmitter
from qtype.interpreter.types import (
    FlowMessage,
    ProgressCallback,
    StreamingCallback,
)
from qtype.semantic.model import Step

logger = logging.getLogger(__name__)


class StepExecutor(ABC):
    """
    Base class for step executors that process individual messages.

    This executor processes messages one at a time, supporting both sequential
    and concurrent execution based on the step's concurrency_config.

    **Execution Flow:**
    1. Failed messages are filtered out and collected for re-emission
    2. Valid messages are processed individually via `process_message()`
    3. Messages can be processed concurrently based on num_workers configuration
    4. Results are streamed back with progress updates
    5. Failed messages are emitted first (ordering not guaranteed with successes)
    6. Optional finalization step runs after all processing completes

    **Subclass Requirements:**
    - Must implement `process_message()` to handle individual message processing
    - Can optionally implement `finalize()` for cleanup/terminal operations

    Args:
        step: The semantic step model defining behavior and configuration
        on_stream_event: Optional callback for real-time streaming events
        on_progress: Optional callback for progress updates
        **dependencies: Executor-specific dependencies (e.g., LLM clients,
            database connections). These are injected by the executor factory
            and stored for use during execution.
    """

    def __init__(
        self,
        step: Step,
        on_stream_event: StreamingCallback | None = None,
        on_progress: ProgressCallback | None = None,
        **dependencies: Any,
    ):
        self.step = step
        self.dependencies = dependencies
        self.progress = ProgressTracker(step.id)
        self.on_stream_event = on_stream_event
        self.on_progress = on_progress
        self.stream_emitter = StreamEmitter(step, on_stream_event)
        # Hook for subclasses to customize the processing function
        # Base uses process_message, BatchedStepExecutor uses process_batch
        self._processor = self.process_message

    async def _filter_and_collect_errors(
        self,
        message_stream: AsyncIterator[FlowMessage],
        failed_messages: list[FlowMessage],
    ) -> AsyncIterator[FlowMessage]:
        """
        Filter out failed messages from the stream and collect them separately.

        This allows failed messages to be re-emitted at the end of processing
        while valid messages proceed through the execution pipeline.

        Note: Progress tracking for errors is NOT done here - it's handled
        in the main execute() loop to consolidate all progress updates.

        Args:
            message_stream: The input stream of messages
            failed_messages: List to collect failed messages into

        Yields:
            Only messages that have not failed
        """
        async for msg in message_stream:
            if msg.is_failed():
                logger.debug(
                    "Skipping failed message for step %s: %s",
                    self.step.id,
                    msg.error,
                )
                failed_messages.append(msg)
            else:
                yield msg

    def _prepare_message_stream(
        self, valid_messages: AsyncIterator[FlowMessage]
    ) -> AsyncIterator[Any]:
        """
        Prepare the valid message stream for processing.

        This is a hook for subclasses to transform the message stream before
        processing. The base implementation returns messages unchanged.
        BatchedStepExecutor overrides this to chunk messages into batches.

        Args:
            valid_messages: Stream of valid (non-failed) messages

        Returns:
            Transformed stream ready for processing (same type for base,
            AsyncIterator[list[FlowMessage]] for batched)
        """
        return valid_messages

    async def execute(
        self,
        message_stream: AsyncIterator[FlowMessage],
    ) -> AsyncIterator[FlowMessage]:
        """
        Execute the step with the given message stream.

        This is the main execution pipeline that orchestrates message processing.
        The specific behavior (individual vs batched) is controlled by
        _prepare_message_stream() and self._processor.

        The execution flow:
        1. Filter out failed messages and collect them
        2. Prepare valid messages for processing (hook for batching)
        3. Process messages with optional concurrency
        4. Emit failed messages first (no ordering guarantee)
        5. Emit processed results
        6. Run finalization hook
        7. Track progress for all emitted messages

        Args:
            message_stream: Input stream of messages to process
        Yields:
            Processed messages, with failed messages emitted first
        """
        # Collect failed messages to re-emit at the end
        failed_messages: list[FlowMessage] = []
        valid_messages = self._filter_and_collect_errors(
            message_stream, failed_messages
        )

        # Determine concurrency from step configuration
        num_workers = 1
        if (
            hasattr(self.step, "concurrency_config")
            and self.step.concurrency_config is not None  # type: ignore[attr-defined]
        ):
            num_workers = self.step.concurrency_config.num_workers  # type: ignore[attr-defined]

        # Prepare messages for processing (batching hook)
        prepared_messages = self._prepare_message_stream(valid_messages)

        # Apply processor with concurrency control
        # Create wrapper to handle the async generator protocol
        async def process_item(
            item: Any, *args: Any
        ) -> AsyncIterator[FlowMessage]:
            async for msg in self._processor(item):
                yield msg

        result_stream = stream.flatmap(
            prepared_messages, process_item, task_limit=num_workers
        )

        # Combine all streams in the following order:
        # 1. Failed messages (emitted first)
        # 2. Processed results
        # 3. Finalization results (runs after all processing completes)
        #
        # Note: Output message order does NOT match input message order.
        # With concurrent processing (num_workers > 1), results arrive as
        # they complete. Even with sequential processing, steps may emit
        # multiple messages per input or transform message order.
        async def emit_failed_messages() -> AsyncIterator[FlowMessage]:
            for msg in failed_messages:
                yield msg

        all_results = stream.concat(
            stream.iterate([result_stream, emit_failed_messages()])
        )

        # Stream results and track progress
        # The context manager ensures proper cleanup of stream resources
        async with all_results.stream() as streamer:
            result: FlowMessage
            async for result in streamer:
                self.progress.update_for_message(result, self.on_progress)
                yield result

        async for msg in self.finalize():
            yield msg

    @abstractmethod
    async def process_message(
        self, message: FlowMessage
    ) -> AsyncIterator[FlowMessage]:
        """
        Process a single message.

        Subclasses MUST implement this method to define how individual
        messages are processed.

        This is a one-to-many operation: a single input message may yield
        zero, one, or multiple output messages. For example, a document
        splitter might yield multiple chunks from one document.

        Args:
            message: The input message to process
            on_stream_event: Optional callback for streaming events

        Yields:
            Zero or more processed messages
        """
        yield  # type: ignore[misc]

    async def finalize(self) -> AsyncIterator[FlowMessage]:
        """
        Optional finalization hook called after all input processing completes.

        This method is called once after the input stream is exhausted and all
        messages have been processed. It can be used for:
        - Cleanup operations
        - Emitting summary/aggregate results
        - Flushing buffers
        - Terminal operations (e.g., writing final output)

        The default implementation yields nothing. Subclasses can override
        to provide custom finalization behavior.

        Yields:
            Zero or more final messages to emit
        """
        # Make this an async generator for type checking
        # The return here makes this unreachable, but we need the yield
        # to make this function an async generator
        return
        yield  # type: ignore[unreachable]
