"""Unit tests for the StepExecutor base class."""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from qtype.base.types import ConcurrencyConfig
from qtype.interpreter.base.base_step_executor import StepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.base.secrets import NoOpSecretManager
from qtype.interpreter.types import FlowMessage, Session
from qtype.semantic.model import Step

pytestmark = pytest.mark.asyncio


# Test Step Models


class SimpleStep(Step):
    """Minimal step for testing basic functionality."""

    type: str = "SimpleStep"


class ConcurrentStep(Step):
    """Step configured for concurrent processing."""

    type: str = "ConcurrentStep"
    concurrency_config: ConcurrencyConfig


# Mock Executors


class MockExecutor(StepExecutor):
    """Executor that appends a suffix to all variable values."""

    def __init__(
        self,
        step: Step,
        context: ExecutorContext,
        suffix: str = "_processed",
        **kwargs,
    ):
        super().__init__(step, context, **kwargs)
        self.suffix = suffix

    async def process_message(
        self, message: FlowMessage
    ) -> AsyncIterator[FlowMessage]:
        new_vars = {
            k: f"{v}{self.suffix}" for k, v in message.variables.items()
        }
        yield message.copy_with_variables(new_vars)


class FailingMockExecutor(StepExecutor):
    """Executor that fails on specific variable values."""

    def __init__(
        self,
        step: Step,
        context: ExecutorContext,
        fail_on_values: set[str] | None = None,
        **kwargs,
    ):
        super().__init__(step, context, **kwargs)
        self.fail_on_values = fail_on_values or set()

    async def process_message(
        self, message: FlowMessage
    ) -> AsyncIterator[FlowMessage]:
        for value in message.variables.values():
            if value in self.fail_on_values:
                yield message.copy_with_error(
                    self.step.id, ValueError(f"Failed: {value}")
                )
                return
        yield message


class FinalizingExecutor(StepExecutor):
    """Executor that emits a summary message during finalization."""

    async def process_message(
        self, message: FlowMessage
    ) -> AsyncIterator[FlowMessage]:
        yield message

    async def finalize(self) -> AsyncIterator[FlowMessage]:
        # Emit a final summary message
        # Note: items_processed should reflect all regular messages at this point
        count_at_finalize = self.progress.items_processed
        summary = FlowMessage(
            session=Session(session_id="summary"),
            variables={
                "processed_count": str(count_at_finalize),
                "finalized": "true",
            },
        )
        yield summary


class SleepingExecutor(StepExecutor):
    async def process_message(
        self, message: FlowMessage
    ) -> AsyncIterator[FlowMessage]:
        await asyncio.sleep(1)
        yield message


# Fixtures


@pytest.fixture
def session():
    """Shared session for all tests."""
    return Session(session_id="test-session")


@pytest.fixture
def simple_step():
    """Basic step without special configuration."""
    return SimpleStep(
        id="test-step",
        type="SimpleStep",
        inputs=[],
        outputs=[],
    )


@pytest.fixture
def concurrent_step():
    """Step configured for concurrent execution."""
    return ConcurrentStep(
        id="concurrent-step",
        type="ConcurrentStep",
        inputs=[],
        outputs=[],
        concurrency_config=ConcurrencyConfig(num_workers=2),
    )


# Helper Functions


async def collect_stream(
    executor: StepExecutor,
    messages: list[str],
    session: Session,
) -> list[FlowMessage]:
    """Helper to execute and collect all results from a message stream."""

    async def message_stream():
        for i, val in enumerate(messages):
            yield FlowMessage(
                session=session, variables={"input": val, "index": str(i)}
            )

    return [r async for r in executor.execute(message_stream())]


# Tests


class TestStepExecutor:
    """Test suite for StepExecutor base functionality."""

    async def test_basic_execution(
        self, simple_step, session, executor_context
    ):
        """Test basic message processing with transformation."""
        executor = MockExecutor(
            simple_step,
            executor_context,
            on_stream_event=None,
            suffix="_processed",
        )
        results = await collect_stream(
            executor, ["msg1", "msg2", "msg3"], session
        )

        assert len(results) == 3
        assert results[0].variables["input"] == "msg1_processed"
        assert results[1].variables["input"] == "msg2_processed"
        assert results[2].variables["input"] == "msg3_processed"

    async def test_concurrent_execution(
        self, concurrent_step, session, executor_context
    ):
        """Test that concurrent configuration is respected."""
        executor = MockExecutor(
            concurrent_step,
            executor_context,
            on_stream_event=None,
            suffix="_concurrent",
        )
        results = await collect_stream(
            executor, ["msg1", "msg2", "msg3", "msg4"], session
        )

        # All messages should complete successfully
        assert len(results) == 4
        assert all(not r.is_failed() for r in results)
        # Note: We can't easily verify actual parallel execution in unit tests

    async def test_error_handling(
        self, simple_step, session, executor_context
    ):
        """Test that errors are tracked and messages are marked as failed."""
        executor = FailingMockExecutor(
            simple_step,
            executor_context,
            on_stream_event=None,
            fail_on_values={"msg2", "msg4"},
        )
        results = await collect_stream(
            executor, ["msg1", "msg2", "msg3", "msg4", "msg5"], session
        )

        assert len(results) == 5
        # Check specific failure patterns
        assert not results[0].is_failed()  # msg1 succeeds
        assert results[1].is_failed()  # msg2 fails
        assert not results[2].is_failed()  # msg3 succeeds
        assert results[3].is_failed()  # msg4 fails
        assert not results[4].is_failed()  # msg5 succeeds

    async def test_all_messages_failed(
        self, simple_step, session, executor_context
    ):
        """Test execution when all messages fail."""
        executor = FailingMockExecutor(
            simple_step,
            executor_context,
            on_stream_event=None,
            fail_on_values={"msg1", "msg2", "msg3"},
        )
        results = await collect_stream(
            executor, ["msg1", "msg2", "msg3"], session
        )

        assert len(results) == 3
        assert all(r.is_failed() for r in results)

    async def test_pre_failed_messages(
        self, simple_step, session, executor_context
    ):
        """Test that messages arriving already-failed are properly emitted."""
        executor = MockExecutor(
            simple_step,
            executor_context,
            on_stream_event=None,
            suffix="_processed",
        )

        # Create a stream with mix of successful and pre-failed messages
        async def mixed_message_stream():
            # Success
            yield FlowMessage(session=session, variables={"input": "msg1"})
            # Success
            yield FlowMessage(session=session, variables={"input": "msg2"})
            # Pre-failed (marked as failed before processing)
            failed_msg1 = FlowMessage(
                session=session, variables={"input": "msg3"}
            )
            failed_msg1 = failed_msg1.copy_with_error(
                simple_step.id, ValueError("Pre-failed")
            )
            yield failed_msg1
            # Pre-failed
            failed_msg2 = FlowMessage(
                session=session, variables={"input": "msg4"}
            )
            failed_msg2 = failed_msg2.copy_with_error(
                simple_step.id, ValueError("Pre-failed")
            )
            yield failed_msg2

        results = [r async for r in executor.execute(mixed_message_stream())]

        # Should get all 4 messages back: 2 pre-failed + 2 processed
        assert len(results) == 4

        # Check that we have exactly 2 failed and 2 successful
        failed = [r for r in results if r.is_failed()]
        succeeded = [r for r in results if not r.is_failed()]
        assert len(failed) == 2
        assert len(succeeded) == 2

        # Failed messages should have original values (not processed)
        assert all(
            "msg3" in r.variables["input"] or "msg4" in r.variables["input"]
            for r in failed
        )

        # Successful messages should be processed (have suffix)
        assert all(
            r.variables["input"].endswith("_processed") for r in succeeded
        )

    async def test_progress_callback(
        self, simple_step, session, executor_context
    ):
        """Test that progress callbacks receive correct counts."""
        progress_calls = []

        def on_progress(
            step_id: str,
            items_processed: int,
            items_in_error: int,
            items_succeeded: int,
            total_items: int | None,
            cache_hits: int | None,
            cache_misses: int | None,
        ):
            progress_calls.append(
                {
                    "processed": items_processed,
                    "errors": items_in_error,
                    "succeeded": items_succeeded,
                    "cache_hits": cache_hits,
                    "cache_misses": cache_misses,
                }
            )

        context = ExecutorContext(
            secret_manager=NoOpSecretManager(),
            tracer=trace.get_tracer(__name__),
            on_progress=on_progress,
        )
        executor = FailingMockExecutor(
            simple_step,
            context,
            on_stream_event=None,
            fail_on_values={"msg2", "msg4"},
        )
        results = await collect_stream(
            executor,
            ["msg1", "msg2", "msg3", "msg4", "msg5"],
            session,
        )

        # Should have 5 progress updates (one per message)
        assert len(progress_calls) == 5
        # Final counts: 5 processed, 2 errors, 3 succeeded
        assert progress_calls[-1]["processed"] == 5
        assert progress_calls[-1]["errors"] == 2
        assert progress_calls[-1]["succeeded"] == 3
        assert len(results) == 5

    # async def test_streaming_events(self, simple_step, session, executor_context):
    #     """Test that streaming events are emitted during processing."""
    #     events = []

    #     async def on_stream_event(event):
    #         events.append(event.content)

    #     executor = MockExecutor(
    #         simple_step, on_stream_event=on_stream_event, suffix="_stream"
    #     )
    #     results = await collect_stream(
    #         executor,
    #         ["msg1", "msg2"],
    #         session,
    #     )

    #     assert len(results) == 2
    #     assert len(events) == 2
    #     assert events[0] == "Processing: msg1"
    #     assert events[1] == "Processing: msg2"

    async def test_finalize_hook(self, simple_step, session, executor_context):
        """Test that finalize() is called and can emit final messages."""
        executor = FinalizingExecutor(
            simple_step, executor_context, on_stream_event=None
        )
        results = await collect_stream(executor, ["msg1", "msg2"], session)

        # Should have 2 regular messages + 1 summary from finalize
        assert len(results) == 3
        # Verify the finalize message was emitted
        assert results[-1].variables.get("finalized") == "true"
        # Note: Progress count timing depends on stream implementation details

    async def test_span_metadata_enrichment(self, simple_step, session):
        """Test that span_id and trace_id are added to message metadata."""
        # Set up a real TracerProvider that records spans
        tracer_provider = TracerProvider()
        tracer = tracer_provider.get_tracer(__name__)

        # Create context with recording tracer
        context = ExecutorContext(
            secret_manager=NoOpSecretManager(),
            tracer=tracer,
        )

        executor = MockExecutor(
            simple_step,
            context,
            suffix="_processed",
        )
        results = await collect_stream(executor, ["msg1", "msg2"], session)

        assert len(results) == 2

        # Each message should have span_id and trace_id in metadata
        for result in results:
            assert "span_id" in result.metadata
            assert "trace_id" in result.metadata

            # Verify they are valid hex strings
            span_id = result.metadata["span_id"]
            trace_id = result.metadata["trace_id"]

            # span_id should be 16 hex chars (64-bit)
            assert len(span_id) == 16
            assert all(c in "0123456789abcdef" for c in span_id)

            # trace_id should be 32 hex chars (128-bit)
            assert len(trace_id) == 32
            assert all(c in "0123456789abcdef" for c in trace_id)

        # Each message should have a unique process_message span_id
        # (this allows per-message feedback instead of per-step)
        span_ids = [r.metadata["span_id"] for r in results]
        assert len(set(span_ids)) == len(results)

        # Trace ID should be the same for all messages in the same execution
        trace_ids = [r.metadata["trace_id"] for r in results]
        assert len(set(trace_ids)) == 1

    async def test_dependencies_injection(self, simple_step, executor_context):
        """Test that dependencies are injected and accessible."""
        test_dep = {"key": "value"}
        executor = MockExecutor(
            simple_step,
            executor_context,
            on_stream_event=None,
            test_dependency=test_dep,
        )

        assert "test_dependency" in executor.dependencies
        assert executor.dependencies["test_dependency"] == test_dep

    async def test_concurrent_execution_performance(
        self, session, executor_context
    ):
        """Test that num_workers actually provides concurrent execution.

        With 10 messages that each sleep for 1 second:
        - Sequential (num_workers=1): ~10 seconds
        - Concurrent (num_workers=10): ~1 second

        We verify execution with 10 workers takes < 5 seconds to prove
        concurrency is working.
        """
        import time

        concurrent_step = ConcurrentStep(
            id="perf-test-step",
            type="ConcurrentStep",
            inputs=[],
            outputs=[],
            concurrency_config=ConcurrencyConfig(num_workers=10),
        )

        executor = SleepingExecutor(
            concurrent_step, executor_context, on_stream_event=None
        )

        start_time = time.time()
        results = await collect_stream(
            executor,
            [f"msg{i}" for i in range(10)],
            session,
        )
        elapsed_time = time.time() - start_time

        # Should complete all 10 messages
        assert len(results) == 10
        assert all(not r.is_failed() for r in results)

        # With 10 workers processing 10 messages (1s each), should take ~1s
        # We allow up to 5s to account for overhead and CI/test environment
        # variability. If it takes >5s, concurrency is not working.
        assert elapsed_time < 5.0, (
            f"Expected < 5s with concurrency, took {elapsed_time:.2f}s"
        )
