from qtype.interpreter.types import FlowMessage, ProgressCallback


class ProgressTracker:
    """
    Tracks progress for step execution.

    This class encapsulates all progress tracking logic, separating it from
    the execution logic in StepExecutor.

    Attributes:
        step_id: ID of the step being tracked
        items_processed: Total number of items processed
        items_in_error: Number of items that encountered errors
        total_items: Total expected items (None if unknown)
    """

    def __init__(self, step_id: str, total_items: int | None = None):
        self.step_id = step_id
        self.items_processed = 0
        self.items_in_error = 0
        self.total_items = total_items

    @property
    def items_succeeded(self) -> int:
        """
        Number of items successfully processed.

        This is derived from items_processed and items_in_error to avoid
        state inconsistency.
        """
        return self.items_processed - self.items_in_error

    def update(
        self,
        on_progress: ProgressCallback | None,
        processed_delta: int,
        error_delta: int,
    ) -> None:
        """
        Update progress counters and invoke the progress callback.

        Internal state is always updated regardless of whether a callback
        is provided. This ensures the aggregator can access accurate counts.

        Args:
            on_progress: Optional callback to notify of progress updates
            processed_delta: Number of items processed in this update
            error_delta: Number of items that failed in this update
        """
        self.items_processed += processed_delta
        self.items_in_error += error_delta

        if on_progress:
            on_progress(
                self.step_id,
                self.items_processed,
                self.items_in_error,
                self.items_succeeded,
                self.total_items,
            )

    def update_for_message(
        self,
        message: FlowMessage,
        on_progress: ProgressCallback | None,
    ) -> None:
        """
        Update progress based on a single message result.

        Args:
            message: The message to check for success/failure
            on_progress: Optional callback to notify of progress updates
        """
        self.update(on_progress, 1, 1 if message.is_failed() else 0)
