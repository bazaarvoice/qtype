from abc import abstractmethod
from typing import Any, AsyncIterator

from aiostream import stream
from opentelemetry.trace import Status, StatusCode

from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
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
        context: ExecutorContext,
        **dependencies: Any,
    ):
        super().__init__(step, context, **dependencies)
        # Override the processor to use batch processing with telemetry
        # instead of message processing
        self._processor = self._process_batch_with_telemetry

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

        This method is automatically wrapped with telemetry tracing when
        called through the executor's execution pipeline.

        Args:
            batch: List of input messages to process as a batch

        Yields:
            Processed messages corresponding to the input batch
        """
        yield  # type: ignore[misc]

    async def _process_batch_with_telemetry(
        self, batch: list[FlowMessage]
    ) -> AsyncIterator[FlowMessage]:
        """
        Internal wrapper that adds telemetry tracing to process_batch.

        This method creates a span for batch processing operations,
        automatically recording batch size, errors, and success metrics.
        """
        span = self._tracer.start_span(
            f"step.{self.step.id}.process_batch",
            attributes={
                "batch.size": len(batch),
            },
        )

        try:
            output_count = 0
            error_count = 0

            async for output_msg in self.process_batch(batch):
                output_count += 1
                if output_msg.is_failed():
                    error_count += 1
                    span.add_event(
                        "message_failed",
                        {
                            "error": str(output_msg.error),
                        },
                    )
                yield output_msg

            # Record processing metrics
            span.set_attribute("batch.outputs", output_count)
            span.set_attribute("batch.errors", error_count)

            if error_count > 0:
                span.set_status(
                    Status(
                        StatusCode.ERROR,
                        f"{error_count} of {output_count} messages failed",
                    )
                )
            else:
                span.set_status(Status(StatusCode.OK))

        except Exception as e:
            span.record_exception(e)
            span.set_status(
                Status(StatusCode.ERROR, f"Batch processing failed: {e}")
            )
            raise
        finally:
            span.end()
