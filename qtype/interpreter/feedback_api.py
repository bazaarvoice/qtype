from __future__ import annotations

import logging
from typing import Annotated, Any, Literal, Union
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from qtype.semantic.model import TelemetrySink

logger = logging.getLogger(__name__)


def _format_feedback_label(feedback: FeedbackData) -> str:
    """Format feedback data into a human-readable label."""
    if isinstance(feedback, ThumbsFeedbackData):
        return "👍" if feedback.value else "👎"
    elif isinstance(feedback, RatingFeedbackData):
        return str(feedback.score)
    elif isinstance(feedback, CategoryFeedbackData):
        return ", ".join(feedback.categories)
    return "unknown"


class ThumbsFeedbackData(BaseModel):
    """Thumbs up/down feedback data."""

    type: Literal["thumbs"] = "thumbs"
    value: bool = Field(
        ..., description="True for thumbs up, False for thumbs down."
    )
    explanation: str | None = Field(
        default=None, description="Optional text explanation for the feedback."
    )


class RatingFeedbackData(BaseModel):
    """Numeric rating feedback data."""

    type: Literal["rating"] = "rating"
    score: int = Field(..., description="Numeric rating score (e.g., 1-5).")
    explanation: str | None = Field(
        default=None, description="Optional text explanation for the feedback."
    )


class CategoryFeedbackData(BaseModel):
    """Category selection feedback data."""

    type: Literal["category"] = "category"
    categories: list[str] = Field(
        ..., description="List of selected category labels."
    )
    explanation: str | None = Field(
        default=None, description="Optional text explanation for the feedback."
    )


FeedbackData = Annotated[
    Union[ThumbsFeedbackData, RatingFeedbackData, CategoryFeedbackData],
    Field(discriminator="type"),
]


class FeedbackRequest(BaseModel):
    """Request model for submitting user feedback on a flow output."""

    span_id: str = Field(..., description="Span ID of the output being rated.")
    trace_id: str = Field(..., description="Trace ID of the flow execution.")
    feedback: FeedbackData = Field(
        ..., description="Feedback data (type determined by discriminator)."
    )


class FeedbackResponse(BaseModel):
    """Response model for feedback submission."""

    status: Literal["success"] = "success"
    message: str = "Feedback submitted successfully"


def create_feedback_endpoint(
    app: FastAPI, telemetry: TelemetrySink, secret_manager: Any
) -> None:
    """
    Register the feedback submission endpoint with the FastAPI application.

    This creates a POST /feedback endpoint that accepts feedback submissions
    and forwards them to the configured telemetry backend.

    Args:
        app: FastAPI application instance.
        telemetry: Telemetry sink configuration.
        secret_manager: Secret manager for resolving secret references.
    """
    # Create client based on provider
    client = None

    if telemetry.provider == "Phoenix":
        from phoenix.client import Client

        # Resolve endpoint in case it's a secret reference
        args = {"base_url": telemetry.endpoint}
        args = secret_manager.resolve_secrets_in_dict(
            args, f"telemetry sink '{telemetry.id}' endpoint"
        )

        # Phoenix Client expects just the base URL (e.g., http://localhost:6006)
        # Parse the URL and reconstruct with just scheme and netloc (host:port)
        parsed = urlparse(args["base_url"])
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        client = Client(base_url=base_url)
    elif telemetry.provider == "Langfuse":
        logger.warning(
            "Langfuse feedback not yet implemented. "
            "Feedback endpoint will not be created."
        )
        return
    else:
        logger.warning(
            f"Feedback endpoint not created: unsupported telemetry "
            f"provider '{telemetry.provider}'."
        )
        return

    @app.post(
        "/feedback",
        response_model=FeedbackResponse,
        tags=["feedback"],
        summary="Submit user feedback on flow outputs",
        description=(
            "Submit user feedback (thumbs, rating, or category) on a "
            "specific flow output. Feedback is sent to the telemetry "
            "backend as span annotations."
        ),
    )
    async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
        """
        Submit user feedback on a flow output.

        The feedback is recorded as a span annotation in the telemetry backend.
        """
        try:
            if telemetry.provider == "Phoenix":
                # Submit to Phoenix using span annotations API
                label = _format_feedback_label(request.feedback)
                explanation = getattr(request.feedback, "explanation", None)

                # Calculate score based on feedback type
                score = None
                if isinstance(request.feedback, ThumbsFeedbackData):
                    score = 1.0 if request.feedback.value else 0.0
                elif isinstance(request.feedback, RatingFeedbackData):
                    score = float(request.feedback.score)

                client.spans.add_span_annotation(
                    span_id=request.span_id,
                    annotation_name="user_feedback",
                    label=label,
                    score=score,
                    explanation=explanation,
                    annotator_kind="HUMAN",
                )

                logger.info(
                    f"Feedback submitted to Phoenix for span {request.span_id}: "
                    f"{request.feedback.type} = {label}"
                )

            elif telemetry.provider == "Langfuse":
                # TODO: Implement Langfuse feedback submission
                raise NotImplementedError(
                    "Langfuse feedback not yet implemented"
                )

            return FeedbackResponse()

        except Exception as e:
            logger.error(f"Failed to submit feedback: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to submit feedback.",
            ) from e
