"""Unit tests for the AggregateExecutor class."""

from __future__ import annotations

import pytest

from qtype.base.types import StepCardinality
from qtype.dsl.domain_types import AggregateStats
from qtype.interpreter.executors.aggregate_executor import AggregateExecutor
from qtype.interpreter.types import FlowMessage, Session
from qtype.semantic.model import Aggregate, Variable

pytestmark = pytest.mark.asyncio


@pytest.fixture
def session():
    """Shared session for all tests."""
    return Session(session_id="test-session")


@pytest.fixture
def aggregate_step():
    """Create an Aggregate step for testing."""
    return Aggregate(
        id="aggregate-step",
        type="Aggregate",
        cardinality=StepCardinality.one,
        inputs=[],
        outputs=[Variable(id="stats", type="AggregateStats", value=None)],
    )


async def create_message_stream(
    session: Session, num_success: int, num_failed: int
):
    """Helper to create a stream with specified success/failure counts."""
    for i in range(num_success):
        yield FlowMessage(session=session, variables={"input": f"success_{i}"})

    for i in range(num_failed):
        failed_msg = FlowMessage(
            session=session, variables={"input": f"failed_{i}"}
        )
        failed_msg.set_error("test-step", ValueError(f"Error {i}"))
        yield failed_msg


class TestAggregateExecutor:
    """Test suite for AggregateExecutor functionality."""

    async def test_aggregate_all_successful(
        self, aggregate_step, session, executor_context
    ):
        """Test aggregation with all successful messages."""
        executor = AggregateExecutor(aggregate_step, executor_context)

        results = [
            r
            async for r in executor.execute(
                create_message_stream(session, num_success=5, num_failed=0)
            )
        ]

        # Should get 5 pass-through messages + 1 aggregate summary
        assert len(results) == 6

        # Last message should be the aggregate summary
        summary = results[-1]
        assert "stats" in summary.variables
        stats = summary.variables["stats"]
        assert isinstance(stats, AggregateStats)
        assert stats.num_successful == 5
        assert stats.num_failed == 0
        assert stats.num_total == 5

    async def test_aggregate_all_failed(
        self, aggregate_step, session, executor_context
    ):
        """Test aggregation with all failed messages.

        Note: Failed messages are filtered by the base executor and passed
        through without going through process_batch(), but they ARE counted
        by the ProgressTracker.
        """
        executor = AggregateExecutor(aggregate_step, executor_context)

        results = [
            r
            async for r in executor.execute(
                create_message_stream(session, num_success=0, num_failed=3)
            )
        ]

        # Should get 3 pass-through failed messages + 1 aggregate summary
        assert len(results) == 4

        # First 3 should be the failed messages
        for i in range(3):
            assert results[i].is_failed()

        # Last message should be the aggregate summary
        summary = results[-1]
        stats = summary.variables["stats"]
        assert stats.num_successful == 0
        assert stats.num_failed == 3
        assert stats.num_total == 3

    async def test_aggregate_mixed_success_and_failure(
        self, aggregate_step, session, executor_context
    ):
        """Test aggregation with mix of successful and failed messages.

        Failed messages are filtered and emitted first, then successful
        messages are processed and emitted, then the aggregate summary.
        """
        executor = AggregateExecutor(aggregate_step, executor_context)

        results = [
            r
            async for r in executor.execute(
                create_message_stream(session, num_success=7, num_failed=3)
            )
        ]

        # Should get 10 pass-through messages + 1 aggregate summary
        assert len(results) == 11

        # Count the actual failures and successes in pass-through messages
        pass_through = results[:-1]
        failed_count = sum(1 for msg in pass_through if msg.is_failed())
        success_count = sum(1 for msg in pass_through if not msg.is_failed())
        assert failed_count == 3
        assert success_count == 7

        # Verify aggregate summary has correct counts from ProgressTracker
        summary = results[-1]
        stats = summary.variables["stats"]
        assert stats.num_successful == 7
        assert stats.num_failed == 3
        assert stats.num_total == 10

    async def test_aggregate_empty_stream(
        self, aggregate_step, executor_context
    ):
        """Test aggregation with no messages."""
        executor = AggregateExecutor(aggregate_step, executor_context)

        async def empty_stream():
            if False:
                yield

        results = [r async for r in executor.execute(empty_stream())]

        # Should get 1 aggregate summary with zeros
        assert len(results) == 1
        summary = results[0]
        stats = summary.variables["stats"]
        assert stats.num_successful == 0
        assert stats.num_failed == 0
        assert stats.num_total == 0

    async def test_aggregate_finalize_runs_after_processing(
        self, aggregate_step, session, executor_context
    ):
        """Test that finalize emits the summary after all messages.

        The finalize() method should emit exactly one message with the
        aggregate stats, and it should come last.
        """
        executor = AggregateExecutor(aggregate_step, executor_context)

        results = [
            r
            async for r in executor.execute(
                create_message_stream(session, num_success=3, num_failed=0)
            )
        ]

        # Should get 3 pass-through + 1 summary (finalize runs last)
        assert len(results) == 4

        # First 3 are pass-through messages
        for i in range(3):
            assert "input" in results[i].variables
            assert not results[i].is_failed()

        # Last message is the aggregate summary from finalize()
        summary = results[-1]
        assert "stats" in summary.variables
        stats = summary.variables["stats"]
        assert stats.num_total == 3
        assert stats.num_successful == 3
        assert stats.num_failed == 0
