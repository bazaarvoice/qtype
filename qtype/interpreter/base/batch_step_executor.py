from abc import abstractmethod
from typing import Any, AsyncIterator

from aiostream import stream

from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.types import FlowMessage


class BatchedStepExecutor(StepExecutor):
    """
    Executor for steps that benefit from API-level batching.

    This executor groups messages into batches and processes them together,
    which is useful for operations that can leverage batch APIs for better
    performance (e.g., GPU operations, bulk database operations, batch inference).

    Like StepExecutor, this supports concurrent processing, but the unit of
    concurrency is the batch rather than individual messages.

    **Subclass Requirements:**
    - Must implement `process_batch()` to handle batch processing
    - Must NOT implement `process_message()` (it's handled automatically)
    - Can optionally implement `finalize()` for cleanup/terminal operations

    Args:
        step: The semantic step model defining behavior and configuration
        on_stream_event: Optional callback for real-time streaming events
        on_progress: Optional callback for progress updates
        **dependencies: Executor-specific dependencies
    """

    def __init__(
        self,
        step: Any,
        **dependencies: Any,
    ):
        super().__init__(step, **dependencies)
        # Override the processor to use batch processing instead of message processing
        self._processor = self.process_batch

    def _prepare_message_stream(
        self, valid_messages: AsyncIterator[FlowMessage]
    ) -> Any:
        """
        Prepare messages by chunking them into batches.

        Overrides the base implementation to group messages into batches
        based on the step's batch_config.

        Args:
            valid_messages: Stream of valid (non-failed) messages

        Returns:
            Stream of message batches (AsyncIterable[list[FlowMessage]])
        """
        # Determine batch size from step configuration
        batch_size = 1
        if (
            hasattr(self.step, "batch_config")
            and self.step.batch_config is not None  # type: ignore[attr-defined]
        ):
            batch_size = self.step.batch_config.batch_size  # type: ignore[attr-defined]

        # Group messages into batches
        return stream.chunks(valid_messages, batch_size)

    async def process_message(
        self, message: FlowMessage
    ) -> AsyncIterator[FlowMessage]:
        """
        Process a single message by wrapping it in a batch of one.

        This method is implemented automatically to satisfy the base class
        contract. Subclasses should NOT override this method.

        Args:
            message: The input message to process

        Yields:
            Processed messages from the batch
        """
        raise NotImplementedError(
            "Batch executors should call process_batch, not process_message."
        )
        yield  # type: ignore[misc]

    @abstractmethod
    async def process_batch(
        self, batch: list[FlowMessage]
    ) -> AsyncIterator[FlowMessage]:
        """
        Process a batch of messages as a single API call.

        Subclasses MUST implement this method to define how batches are
        processed together for improved performance.

        This is a many-to-many operation: a batch of input messages yields
        a corresponding set of output messages. Messages should be yielded
        as they become available to maintain memory efficiency (don't collect
        all results before yielding).

        Args:
            batch: List of input messages to process as a batch

        Yields:
            Processed messages corresponding to the input batch
        """
        yield  # type: ignore[misc]
