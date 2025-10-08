"""Unit tests for the BatchedStepExecutor class.

These tests focus specifically on batch-specific functionality. General
executor behavior (error handling, progress, streaming events, etc.) is
covered by test_step_executor.py since BatchedStepExecutor extends StepExecutor.
"""

from __future__ import annotations

import pytest

from qtype.base.types import BatchConfig, ConcurrencyConfig, StepCardinality
from qtype.interpreter.base.batch_step_executor import BatchedStepExecutor
from qtype.interpreter.types import FlowMessage, Session
from qtype.semantic.model import Step

pytestmark = pytest.mark.asyncio


# Test Step Models


class BatchableStep(Step):
    """Step configured for batch processing."""

    type: str = "BatchableStep"
    batch_config: BatchConfig


class ConcurrentBatchableStep(Step):
    """Step configured for both batching and concurrency."""

    type: str = "ConcurrentBatchableStep"
    batch_config: BatchConfig
    concurrency_config: ConcurrencyConfig


# Note: We don't need extensive mock executors here since we're only testing
# batch-specific behavior. The tests use inline TrackingExecutor classes.


# Fixtures


@pytest.fixture
def session():
    """Shared session for all tests."""
    return Session(session_id="test-session")


@pytest.fixture
def batchable_step():
    """Step configured with batch_size=3."""
    return BatchableStep(
        id="batch-step",
        type="BatchableStep",
        cardinality=StepCardinality.one,
        inputs=[],
        outputs=[],
        batch_config=BatchConfig(batch_size=3),
    )


# Helper Functions


async def collect_stream(
    executor: BatchedStepExecutor,
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


class TestBatchedStepExecutor:
    """
    Test suite for BatchedStepExecutor batch-specific functionality.

    Note: General executor functionality (error handling, progress callbacks,
    finalize, dependencies, etc.) is already tested in test_step_executor.py.
    These tests focus specifically on batching behavior.
    """

    async def test_batch_size_configuration(self, session):
        """Test that configured batch size is respected."""
        step = BatchableStep(
            id="batch-step",
            type="BatchableStep",
            cardinality=StepCardinality.one,
            inputs=[],
            outputs=[],
            batch_config=BatchConfig(batch_size=2),
        )

        # Track actual batch sizes seen during processing
        batch_sizes = []

        class TrackingExecutor(BatchedStepExecutor):
            async def process_batch(self, batch):
                batch_sizes.append(len(batch))
                for msg in batch:
                    yield msg

        executor = TrackingExecutor(step, on_stream_event=None)
        results = await collect_stream(
            executor, ["msg1", "msg2", "msg3"], session
        )

        assert len(results) == 3
        # With batch_size=2 and 3 messages: [2, 1]
        assert batch_sizes == [2, 1]

    async def test_default_batch_size(self, session):
        """Test that default batch_size=1 is used when no batch_config."""
        step = Step(
            id="no-batch-config",
            type="SimpleStep",
            cardinality=StepCardinality.one,
            inputs=[],
            outputs=[],
        )

        batch_sizes = []

        class TrackingExecutor(BatchedStepExecutor):
            async def process_batch(self, batch):
                batch_sizes.append(len(batch))
                for msg in batch:
                    yield msg

        executor = TrackingExecutor(step, on_stream_event=None)
        results = await collect_stream(executor, ["msg1", "msg2"], session)

        assert len(results) == 2
        # Each message should be its own batch of size 1
        assert batch_sizes == [1, 1]

    async def test_batch_with_concurrency(self, session):
        """Test that batching works correctly with concurrent processing."""
        step = ConcurrentBatchableStep(
            id="concurrent-batch-step",
            type="ConcurrentBatchableStep",
            cardinality=StepCardinality.one,
            inputs=[],
            outputs=[],
            batch_config=BatchConfig(batch_size=2),
            concurrency_config=ConcurrencyConfig(num_workers=2),
        )

        batch_sizes = []

        class TrackingExecutor(BatchedStepExecutor):
            async def process_batch(self, batch):
                batch_sizes.append(len(batch))
                for msg in batch:
                    yield msg

        executor = TrackingExecutor(step, on_stream_event=None)
        results = await collect_stream(
            executor, ["msg1", "msg2", "msg3", "msg4"], session
        )

        # All messages should complete
        assert len(results) == 4
        # Should have created 2 batches of size 2
        assert sorted(batch_sizes) == [2, 2]
