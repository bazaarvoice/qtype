from typing import AsyncIterator

from qtype.dsl.domain_types import AggregateStats
from qtype.interpreter.base.batch_step_executor import BatchedStepExecutor
from qtype.interpreter.base.executor_context import ExecutorContext
from qtype.interpreter.types import FlowMessage, Session
from qtype.semantic.model import Aggregate


class AggregateExecutor(BatchedStepExecutor):
    """
    Executor for the Aggregate step.

    This is a terminal, many-to-one operation that reduces an entire stream
    to a single summary message containing counts of successful and failed
    messages. It processes all messages without modification during the
    processing phase, then emits a single aggregate summary during finalization.
    """

    def __init__(
        self, step: Aggregate, context: ExecutorContext, **dependencies
    ):
        super().__init__(step, context, **dependencies)
        if not isinstance(step, Aggregate):
            raise ValueError(
                "AggregateExecutor can only execute Aggregate steps."
            )
        self.step: Aggregate = step
        self.last_session: Session | None = None

    async def process_batch(
        self,
        batch: list[FlowMessage],
    ) -> AsyncIterator[FlowMessage]:
        """
        Process messages by passing them through unchanged.

        The aggregate step doesn't modify messages - it just passes them
        through. All counting is handled by the base class's ProgressTracker,
        which is updated as messages flow through execute(). The actual
        aggregation happens in finalize(), which runs after all progress
        tracking is complete.

        Note: Failed messages are filtered out by the base class before
        reaching this method, so all messages in the batch are successful.

        Args:
            batch: List of messages to process (all successful)

        Yields:
            Each message unchanged (pass-through)
        """
        for msg in batch:
            # Track the last session seen for use in finalize
            self.last_session = msg.session

            # Pass message through unchanged
            yield msg

    async def finalize(
        self,
    ) -> AsyncIterator[FlowMessage]:
        """
        Emit a single summary message with aggregate statistics.

        This runs after all messages have been processed and counted by the
        base class's ProgressTracker. The summary includes counts of
        successful, failed, and total messages.

        Yields:
            A single FlowMessage containing the aggregate statistics
        """
        if not self.last_session:
            # If no messages were processed, create a summary with all zeros
            # using a default session
            session = Session(session_id="aggregate-no-input")
        else:
            session = self.last_session

        # Create the aggregate stats output using counts from ProgressTracker.
        # Since finalize() now runs AFTER all progress tracking is complete,
        # self.progress has accurate counts of all messages processed.
        variable_name = self.step.outputs[0].id
        yield FlowMessage(
            session=session,
            variables={
                variable_name: AggregateStats(
                    num_successful=self.progress.items_succeeded,
                    num_failed=self.progress.items_in_error,
                    num_total=self.progress.items_processed,
                )
            },
        )
