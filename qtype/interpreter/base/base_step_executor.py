from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator

from aiostream import stream
from openinference.semconv.trace import (
    OpenInferenceSpanKindValues,
    SpanAttributes,
)
from opentelemetry import context, trace
from opentelemetry.trace import Status, StatusCode

from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.base.progress_tracker import ProgressTracker
from qtype.interpreter.base.step_cache import (
    cache_key,
    create_cache,
    from_cache_value,
    to_cache_value,
)
from qtype.interpreter.base.stream_emitter import StreamEmitter
from qtype.interpreter.types import FlowMessage
from qtype.semantic.model import SecretReference, Step

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
    - Can optionally override `span_kind` to set appropriate OpenInference span type

    Args:
        step: The semantic step model defining behavior and configuration
        context: ExecutorContext with cross-cutting concerns
        **dependencies: Executor-specific dependencies (e.g., LLM clients,
            database connections). These are injected by the executor factory
            and stored for use during execution.
    """

    # Subclasses can override this to set the appropriate span kind
    span_kind: OpenInferenceSpanKindValues = (
        OpenInferenceSpanKindValues.UNKNOWN
    )

    def __init__(
        self,
        step: Step,
        context: ExecutorContext,
        **dependencies: Any,
    ):
        self.step = step
        self.context = context
        self.dependencies = dependencies
        self.progress = ProgressTracker(step.id)
        self.stream_emitter = StreamEmitter(step, context.on_stream_event)
        # Hook for subclasses to customize the processing function
        # Base uses process_message with telemetry wrapping,
        # BatchedStepExecutor uses process_batch
        self._processor = self._process_message_with_cache
        # Convenience properties from context
        self._secret_manager = context.secret_manager
        self._tracer = context.tracer or trace.get_tracer(__name__)

    def _resolve_secret(self, value: str | SecretReference) -> str:
        """
        Resolve a value that may be a string or a SecretReference.

        This is a convenience wrapper that adds step context to error messages.

        Args:
            value: Either a plain string or a SecretReference

        Returns:
            The resolved string value

        Raises:
            SecretResolutionError: If secret resolution fails
        """
        context = f"step '{self.step.id}'"
        return self._secret_manager(value, context)

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
        1. Start step boundary for visual grouping
        2. Filter out failed messages and collect them
        3. Prepare valid messages for processing (hook for batching)
        4. Process messages with optional concurrency
        5. Emit failed messages first (no ordering guarantee)
        6. Emit processed results
        7. Run finalization hook
        8. End step boundary
        9. Track progress for all emitted messages

        Args:
            message_stream: Input stream of messages to process
        Yields:
            Processed messages, with failed messages emitted first
        """
        # Start a span for tracking
        # Note: We manually manage the span lifecycle to allow yielding
        span = self._tracer.start_span(
            f"step.{self.step.id}",
            attributes={
                "step.id": self.step.id,
                "step.type": self.step.__class__.__name__,
                SpanAttributes.OPENINFERENCE_SPAN_KIND: self.span_kind.value,
            },
        )

        # Make this span the active context so child spans will nest under it
        # Only attach if span is recording (i.e., real tracer is configured)
        ctx = trace.set_span_in_context(span)
        token = context.attach(ctx) if span.is_recording() else None

        # Initialize the cache
        # this is done once per execution so re-runs are fast
        self.cache = create_cache(self.step.cache_config, self.step.id)

        # Start step boundary for visual grouping in UI
        async with self.stream_emitter.step_boundary():
            try:
                # Collect failed messages to re-emit at the end
                failed_messages: list[FlowMessage] = []
                valid_messages = self._filter_and_collect_errors(
                    message_stream, failed_messages
                )

                # Determine concurrency from step configuration
                num_workers = 1
                if hasattr(self.step, "concurrency_config") and (
                    self.step.concurrency_config is not None  # type: ignore[attr-defined]
                ):
                    num_workers = (
                        self.step.concurrency_config.num_workers  # type: ignore[attr-defined]
                    )
                span.set_attribute("step.concurrency", num_workers)

                # Prepare messages for processing (batching hook)
                prepared_messages = self._prepare_message_stream(
                    valid_messages
                )

                # Apply processor with concurrency control
                async def process_item(
                    item: Any, *args: Any
                ) -> AsyncIterator[FlowMessage]:
                    async for msg in self._processor(item):
                        yield msg

                result_stream = stream.flatmap(
                    prepared_messages, process_item, task_limit=num_workers
                )

                # Combine all streams
                async def emit_failed_messages() -> AsyncIterator[FlowMessage]:
                    for msg in failed_messages:
                        yield msg

                all_results = stream.concat(
                    stream.iterate([result_stream, emit_failed_messages()])
                )

                # Track message counts for telemetry
                message_count = 0
                error_count = len(failed_messages)

                # Stream results and track progress
                async with all_results.stream() as streamer:
                    result: FlowMessage
                    async for result in streamer:
                        message_count += 1
                        if result.is_failed():
                            error_count += 1
                        self.progress.update_for_message(
                            result, self.context.on_progress
                        )
                        yield result

                # Finalize and track those messages too
                async for msg in self.finalize():
                    message_count += 1
                    if msg.is_failed():
                        error_count += 1
                    yield msg

                # Close the cache
                if self.cache:
                    self.cache.close()

                # Record metrics in span
                span.set_attribute("step.messages.total", message_count)
                span.set_attribute("step.messages.errors", error_count)

                # Set span status based on errors
                if error_count > 0:
                    span.set_status(
                        Status(
                            StatusCode.ERROR,
                            f"{error_count} of {message_count} messages failed",
                        )
                    )
                else:
                    span.set_status(Status(StatusCode.OK))

            except Exception as e:
                # Record the exception and set error status
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, f"Step failed: {e}"))
                raise
            finally:
                # Detach the context and end the span
                # Only detach if we successfully attached (span was recording)
                if token is not None:
                    context.detach(token)
                span.end()

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

        This method is automatically wrapped with telemetry tracing when
        called through the executor's execution pipeline.

        Args:
            message: The input message to process

        Yields:
            Zero or more processed messages
        """
        yield  # type: ignore[misc]

    async def _process_message_with_cache(
        self, message: FlowMessage
    ) -> AsyncIterator[FlowMessage]:
        downstream = self._process_message_with_telemetry
        if self.cache is None:
            async for output_msg in downstream(message):
                yield output_msg
        else:
            key = cache_key(message, self.step)
            cached_result = self.cache.get(key)
            if cached_result is not None:
                result = [from_cache_value(d, message) for d in cached_result]  # type: ignore
                self.progress.increment_cache(
                    self.context.on_progress,
                    hit_delta=len(result),
                    miss_delta=0,
                )
                # cache hit
                for msg in result:
                    yield msg
            else:
                # cache miss -- process downstream and store result
                buf = []
                async for output_msg in downstream(message):
                    buf.append(output_msg)
                    yield output_msg

                self.progress.increment_cache(
                    self.context.on_progress, hit_delta=0, miss_delta=len(buf)
                )
                # store the results in the cache of there are no errors or if instructed to do so
                if (
                    all(not msg.is_failed() for msg in buf)
                    or self.step.cache_config.on_error == "Cache"  # type: ignore
                ):
                    serialized = [to_cache_value(m, self.step) for m in buf]
                    self.cache.set(
                        key, serialized, expire=self.step.cache_config.ttl
                    )  # type: ignore

    async def _process_message_with_telemetry(
        self, message: FlowMessage
    ) -> AsyncIterator[FlowMessage]:
        """
        Internal wrapper that adds telemetry tracing to process_message.

        This method creates a child span for each message processing
        operation, automatically recording errors and success metrics.
        The child span will automatically be nested under the current
        active span in the context.
        """
        # Get current context and create child span within it
        span = self._tracer.start_span(
            f"step.{self.step.id}.process_message",
            attributes={
                "session.id": message.session.session_id,
            },
        )

        try:
            output_count = 0
            error_occurred = False

            async for output_msg in self.process_message(message):
                output_count += 1
                if output_msg.is_failed():
                    error_occurred = True
                    span.add_event(
                        "message_failed",
                        {
                            "error": str(output_msg.error),
                        },
                    )
                yield output_msg

            # Record processing metrics
            span.set_attribute("message.outputs", output_count)

            if error_occurred:
                span.set_status(
                    Status(StatusCode.ERROR, "Message processing had errors")
                )
            else:
                span.set_status(Status(StatusCode.OK))

        except Exception as e:
            span.record_exception(e)
            span.set_status(
                Status(StatusCode.ERROR, f"Processing failed: {e}")
            )
            raise
        finally:
            span.end()

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
