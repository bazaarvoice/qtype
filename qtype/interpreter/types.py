from typing import Any, Dict, Literal, Optional, Protocol, Union

from pydantic import BaseModel, ConfigDict, Field, model_serializer

from qtype.base.types import StrictBaseModel
from qtype.dsl.domain_types import ChatMessage
from qtype.semantic.model import Step


class _UnsetType:
    """Sentinel representing an unset variable.

    Distinguishes between:
    - Variable never mentioned (not in dict)
    - Variable explicitly unset (UNSET value in dict)
    - Variable set to None (None value in dict)
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNSET"

    def __bool__(self) -> bool:
        return False


UNSET = _UnsetType()


# Stream Event Types (Discriminated Union)
# These events are emitted by executors during flow execution
# and can be converted to Vercel UI chunks for frontend display


class BaseStreamEvent(BaseModel):
    """
    Base class for all stream events.

    Provides common metadata field for telemetry and other contextual data.
    The metadata dict typically contains:
    - span_id: OpenTelemetry span ID (16 hex chars)
    - trace_id: OpenTelemetry trace ID (32 hex chars)
    """

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata for telemetry and context tracking",
    )


class TextStreamStartEvent(BaseStreamEvent):
    """Signals the start of incremental text streaming.

    Use this when beginning to stream LLM-generated content or other
    incremental text output. Must be followed by TextStreamDeltaEvents
    and eventually a TextStreamEndEvent with the same stream_id.

    Maps to: TextStartChunk in Vercel protocol
    """

    type: Literal["text_stream_start"] = "text_stream_start"
    step: Step
    stream_id: str = Field(
        description="Unique ID to correlate start/delta/end events"
    )


class TextStreamDeltaEvent(BaseStreamEvent):
    """Carries an incremental chunk of text content.

    Use this for streaming LLM responses or other incremental text.
    The delta represents a small piece of text to append to the stream.

    Maps to: TextDeltaChunk in Vercel protocol
    """

    type: Literal["text_stream_delta"] = "text_stream_delta"
    step: Step
    stream_id: str = Field(
        description="Must match the stream_id from TextStreamStartEvent"
    )
    delta: str = Field(description="Incremental text content to append")


class TextStreamEndEvent(BaseStreamEvent):
    """Signals the completion of incremental text streaming.

    Use this to mark the end of a text stream. After this event,
    no more deltas should be sent for this stream_id.

    Maps to: TextEndChunk in Vercel protocol
    """

    type: Literal["text_stream_end"] = "text_stream_end"
    step: Step
    stream_id: str = Field(
        description="Must match the stream_id from TextStreamStartEvent"
    )


class ReasoningStreamStartEvent(BaseStreamEvent):
    """Signals the start of incremental reasoning streaming.

    Use this when an agent begins outputting reasoning/thinking steps.
    Must be followed by ReasoningStreamDeltaEvents and eventually
    a ReasoningStreamEndEvent with the same stream_id.

    Maps to: ReasoningStartChunk in Vercel protocol
    """

    type: Literal["reasoning_stream_start"] = "reasoning_stream_start"
    step: Step
    stream_id: str = Field(
        description="Unique ID to correlate start/delta/end events"
    )


class ReasoningStreamDeltaEvent(BaseStreamEvent):
    """Carries an incremental chunk of reasoning content.

    Use this for streaming agent reasoning/thinking steps.
    The delta represents a small piece of reasoning text to append.

    Maps to: ReasoningDeltaChunk in Vercel protocol
    """

    type: Literal["reasoning_stream_delta"] = "reasoning_stream_delta"
    step: Step
    stream_id: str = Field(
        description="Must match the stream_id from ReasoningStreamStartEvent"
    )
    delta: str = Field(description="Incremental reasoning content to append")


class ReasoningStreamEndEvent(BaseStreamEvent):
    """Signals the completion of incremental reasoning streaming.

    Use this to mark the end of a reasoning stream. After this event,
    no more deltas should be sent for this stream_id.

    Maps to: ReasoningEndChunk in Vercel protocol
    """

    type: Literal["reasoning_stream_end"] = "reasoning_stream_end"
    step: Step
    stream_id: str = Field(
        description="Must match the stream_id from ReasoningStreamStartEvent"
    )


class StatusEvent(BaseStreamEvent):
    """Reports a complete status message from a step.

    Use this for non-streaming status updates like:
    - "Writing 3 records to file.csv"
    - "Processing document..."
    - "Search completed: found 5 results"

    Maps to: StartStepChunk + TextStartChunk + TextDeltaChunk +
             TextEndChunk + FinishStepChunk (wrapped as a complete step)
    """

    type: Literal["status"] = "status"
    step: Step
    message: str = Field(description="Complete status message to display")


class StepStartEvent(BaseStreamEvent):
    """Marks the beginning of a logical step boundary.

    Use this to group related events together visually in the UI.
    Must be paired with a StepEndEvent.

    Maps to: StartStepChunk in Vercel protocol
    """

    type: Literal["step_start"] = "step_start"
    step: Step


class StepEndEvent(BaseStreamEvent):
    """Marks the end of a logical step boundary.

    Use this to close a step boundary opened by StepStartEvent.

    Maps to: FinishStepChunk in Vercel protocol
    """

    type: Literal["step_end"] = "step_end"
    step: Step


class ToolExecutionStartEvent(BaseStreamEvent):
    """Signals the start of tool execution.

    Use this when a tool is about to be invoked, either by an LLM
    or by a tool executor.

    Maps to: ToolInputAvailableChunk in Vercel protocol
    """

    type: Literal["tool_execution_start"] = "tool_execution_start"
    step: Step
    tool_call_id: str = Field(description="Unique identifier for this call")
    tool_name: str = Field(description="Name of the tool being executed")
    tool_input: dict[str, Any] = Field(
        description="Input parameters for the tool"
    )


class ToolExecutionEndEvent(BaseStreamEvent):
    """Signals the completion of tool execution.

    Use this when a tool has finished executing successfully.

    Maps to: ToolOutputAvailableChunk in Vercel protocol
    """

    type: Literal["tool_execution_end"] = "tool_execution_end"
    step: Step
    tool_call_id: str = Field(
        description="Must match tool_call_id from ToolExecutionStartEvent"
    )
    tool_output: Any = Field(description="Output returned by the tool")


class ToolExecutionErrorEvent(BaseStreamEvent):
    """Signals that tool execution failed.

    Use this when a tool encounters an error during execution.

    Maps to: ToolOutputErrorChunk in Vercel protocol
    """

    type: Literal["tool_execution_error"] = "tool_execution_error"
    step: Step
    tool_call_id: str = Field(
        description="Must match tool_call_id from ToolExecutionStartEvent"
    )
    error_message: str = Field(description="Description of the error")


class ErrorEvent(BaseStreamEvent):
    """Signals a general error occurred during step execution.

    Use this for errors that aren't specific to tool execution.

    Maps to: ErrorChunk in Vercel protocol
    """

    type: Literal["error"] = "error"
    step: Step
    error_message: str = Field(description="Description of the error")


# Union type for all stream events
StreamEvent = Union[
    TextStreamStartEvent,
    TextStreamDeltaEvent,
    ReasoningStreamStartEvent,
    ReasoningStreamDeltaEvent,
    ReasoningStreamEndEvent,
    TextStreamEndEvent,
    ReasoningStreamStartEvent,
    ReasoningStreamEndEvent,
    StatusEvent,
    StepStartEvent,
    StepEndEvent,
    ToolExecutionStartEvent,
    ToolExecutionEndEvent,
    ToolExecutionErrorEvent,
    ErrorEvent,
]


class StreamingCallback(Protocol):
    """The async callback protocol for handling real-time stream events."""

    async def __call__(self, event: StreamEvent) -> None: ...


class ProgressCallback(Protocol):
    """
    A protocol representing a callback function for reporting progress during a multi-step process.

    The callback is called with the following arguments:
        step_id (str): Identifier for the current step or phase.
        items_processed (int): Number of items processed so far in the current step.
        total_items (int | None): Total number of items to process in the current step, or None if unknown.

    Implementations should use this callback to provide progress updates, such as updating a progress bar or logging progress information.
    """

    def __call__(
        self,
        step_id: str,
        items_processed: int,
        items_in_error: int,
        items_succeeded: int,
        total_items: int | None,
        cache_hits: int | None,
        cache_misses: int | None,
    ) -> None: ...


class StepError(BaseModel):
    """A structured error object attached to a failed FlowState."""

    step_id: str
    error_message: str
    exception_type: str


class Session(StrictBaseModel):
    model_config = ConfigDict(extra="forbid")
    """Represents a user session, encapsulating all relevant state and context."""
    session_id: str = Field(
        ..., description="Unique identifier for the session."
    )
    conversation_history: list[ChatMessage] = Field(
        default_factory=list,
        description="History of messages in the conversation.",
    )


class FlowMessage(BaseModel):
    """
    Represents the complete state of one execution path at a point in time.
    This object is the primary data structure passed between StepExecutors.
    """

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,  # Allow UNSET sentinel
    )

    session: Session
    variables: Dict[str, Any] = Field(
        default_factory=dict,
        description="Mapping of variable IDs to their values.",
    )
    error: Optional[StepError] = None
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata for telemetry, span IDs, and other system-level data.",
    )

    def is_failed(self) -> bool:
        """Checks if this state has encountered an error."""
        return self.error is not None

    def is_set(self, var_id: str) -> bool:
        """Check if a variable is set (not UNSET, may be None)."""
        value = self.variables.get(var_id, UNSET)
        return value is not UNSET

    def get_variable(self, var_id: str, *, default: Any = UNSET) -> Any:
        """Get variable value, raising if unset and no default provided.

        Args:
            var_id: Variable identifier
            default: Value to return if variable is unset. If not provided,
                    raises ValueError on unset variables.

        Returns:
            Variable value (may be None if explicitly set to None)

        Raises:
            ValueError: If variable is unset and no default provided

        Examples:
            # Required variable - throws if unset
            value = message.get_variable("user_input")

            # Optional variable - returns None if unset
            value = message.get_variable("optional_field", default=None)

            # Optional with custom default
            value = message.get_variable("count", default=0)
        """
        value = self.variables.get(var_id, UNSET)

        if value is UNSET:
            if default is UNSET:
                raise ValueError(
                    (
                        f"Required variable '{var_id}' is not set. "
                        f"Available variables: {list(self.variables.keys())}"
                    )
                )
            return default

        return value

    def copy_with_error(self, step_id: str, exc: Exception) -> "FlowMessage":
        """Returns a copy of this state marked as failed."""
        return self.model_copy(
            update={
                "error": StepError(
                    step_id=step_id,
                    error_message=str(exc),
                    exception_type=type(exc).__name__,
                )
            }
        )

    def copy_with_variables(
        self, new_variables: dict[str, Any]
    ) -> "FlowMessage":
        """Create a new FlowMessage with updated variables.

        Note: Can set variables to UNSET to explicitly mark them as unset.
        """
        new_vars = self.variables.copy()
        new_vars.update(new_variables)
        new_state = self.model_copy(update={"variables": new_vars})
        return new_state

    @model_serializer
    def serialize_model(self):
        """Custom serialization that excludes UNSET variables."""
        return {
            "session": self.session,
            "variables": {
                k: v for k, v in self.variables.items() if v is not UNSET
            },
            "error": self.error,
        }


class InterpreterError(Exception):
    """Base exception class for ProtoGen interpreter errors."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details
