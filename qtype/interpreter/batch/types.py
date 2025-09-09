from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ErrorMode(str, Enum):
    """Error handling mode for batch processing."""

    FAIL = "fail"
    DROP = "drop"


class BatchConfig(BaseModel):
    """Configuration for batch execution.

    Attributes:
        num_workers: Number of async workers for batch operations.
        batch_size: Maximum number of rows to send to a step at a time.
        error_mode: Error handling mode for batch processing.
    """

    num_workers: int = Field(
        default=4,
        description="Number of async workers for batch operations",
        gt=0,
    )
    batch_size: int = Field(
        default=512,
        description="Max number of rows to send to a step at a time",
        gt=0,
    )
    error_mode: ErrorMode = Field(
        default=ErrorMode.FAIL,
        description="Error handling mode for batch processing",
    )
    write_errors_to: str | None = Field(
        default=None,
        description="If error mode is DROP, the errors for any step are saved to this directory",
    )
