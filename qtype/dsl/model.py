from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    """Base model with extra fields forbidden."""

    model_config = ConfigDict(extra="forbid")


class VariableType(str, Enum):
    """Represents the type of data a user or system input can accept within the DSL.
    Used for schema validation and UI rendering of input fields."""

    text = "text"
    number = "number"
    file = "file"
    image = "image"
    date = "date"
    time = "time"
    datetime = "datetime"
    video = "video"
    audio = "audio"


class Variable(StrictBaseModel):
    """Schema for a variable that can serve as input, output, or parameter within the DSL."""

    id: str = Field(
        ...,
        description="Unique ID of the variable. Referenced in prompts or steps.",
    )
    type: VariableType = Field(
        ..., description="Type of data expected or produced."
    )


class Prompt(StrictBaseModel):
    """References a prompt template, either inline or from file, along with expected input and output variable bindings."""

    id: str = Field(..., description="Unique ID for the prompt.")
    path: str | None = Field(
        default=None, description="File path to the prompt template."
    )
    template: str | None = Field(
        default=None, description="Inline template string for the prompt."
    )
    inputs: list[str] = Field(
        ..., description="List of input variable IDs this prompt expects."
    )
    outputs: list[str] | None = Field(
        default=None,
        description="Optional list of output variable IDs this prompt generates.",
    )


class Model(StrictBaseModel):
    """Describes a generative model configuration, including provider and model ID."""

    id: str = Field(..., description="Unique ID for the model.")
    provider: str = Field(
        ..., description="Name of the provider, e.g., openai or anthropic."
    )
    model_id: str | None = Field(
        default=None,
        description="The specific model name or ID for the provider. If None, id is used",
    )
    inference_params: dict[str, Any] | None = Field(
        default=None,
        description="Optional inference parameters like temperature or max_tokens.",
    )
    dimensions: int | None = Field(
        default=None,
        description="Dimensionality of the embedding vectors produced by this model if an embedding model.",
    )

class VectorDBRetriever(StrictBaseModel):
    """Retriever that fetches top-K documents using a vector database and embedding-based similarity search."""

    type: Literal["vector_retrieve"] = "vector_retrieve"
    id: str = Field(..., description="Unique ID of the retriever.")
    index: str = Field(..., description="ID of the index this retriever uses.")
    embedding_model: str = Field(
        ...,
        description="ID of the embedding model used to vectorize the query.",
    )
    top_k: int = Field(5, description="Number of top documents to retrieve.")
    args: dict[str, Any] | None = Field(
        default=None,
        description="Arbitrary arguments as JSON/YAML for custom retriever configuration.",
    )
    inputs: list[str] | None = Field(
        default=None,
        description="Input variable IDs required by this retriever.",
    )
    outputs: list[str] | None = Field(
        default=None,
        description="Optional list of output variable IDs this prompt generates.",
    )


class MemoryType(str, Enum):
    """Enum to differentiate supported memory types, such as vector memory for embedding-based recall."""

    vector = "vector"


class Memory(StrictBaseModel):
    """Session or persistent memory used to store relevant conversation or state data across steps or turns."""

    id: str = Field(..., description="Unique ID of the memory block.")
    type: MemoryType = Field(
        ..., description="The type of memory to store context."
    )
    embedding_model: str = Field(
        ..., description="Embedding model ID used for storage."
    )
    persist: bool = Field(
        default=False, description="Whether memory persists across sessions."
    )
    ttl_minutes: int | None = Field(
        default=None, description="Optional TTL for temporary memory."
    )
    use_for_context: bool = Field(
        default=True,
        description="Whether this memory should be injected as context.",
    )

class Tool(StrictBaseModel):
    """Callable function or external operation available to the model. Input/output shapes are described via JSON Schema."""

    type: Literal["tool"]
    id: str = Field(..., description="Unique ID of the tool.")
    name: str = Field(..., description="Name of the tool function.")
    description: str = Field(
        ..., description="Description of what the tool does."
    )
    inputs: list[str] = Field(
        ..., description="List of input variable IDs this prompt expects."
    )
    outputs: list[str] = Field(
        ...,
        description="Optional list of output variable IDs this prompt generates.",
    )


class ToolProvider(StrictBaseModel):
    """Logical grouping of tools, often backed by an API or OpenAPI spec, and optionally authenticated.

    This should show the Pydantic fields."""

    id: str = Field(..., description="Unique ID of the tool provider.")
    name: str = Field(..., description="Name of the tool provider.")
    tools: list[Tool] = Field(
        ..., description="List of tools exposed by this provider."
    )
    openapi_spec: str | None = Field(
        default=None,
        description="Optional path or URL to an OpenAPI spec to auto-generate tools.",
    )
    include_tags: list[str] | None = Field(
        default=None,
        description="Limit tool generation to specific OpenAPI tags.",
    )
    exclude_paths: list[str] | None = Field(
        default=None, description="Exclude specific endpoints by path."
    )
    auth: str | None = Field(
        default=None,
        description="AuthorizationProvider ID used to authenticate tool access.",
    )


class AuthorizationProvider(StrictBaseModel):
    """Defines how tools or providers authenticate with APIs, such as OAuth2 or API keys."""

    id: str = Field(
        ..., description="Unique ID of the authorization configuration."
    )
    type: str = Field(
        ..., description="Authorization method, e.g., 'oauth2' or 'api_key'."
    )
    host: str | None = Field(
        default=None, description="Base URL or domain of the provider."
    )
    client_id: str | None = Field(
        default=None, description="OAuth2 client ID."
    )
    client_secret: str | None = Field(
        default=None, description="OAuth2 client secret."
    )
    token_url: str | None = Field(
        default=None, description="Token endpoint URL."
    )
    scopes: list[str] | None = Field(
        default=None, description="OAuth2 scopes required."
    )
    api_key: str | None = Field(
        default=None, description="API key if using token-based auth."
    )


class TelemetrySink(StrictBaseModel):
    """Defines an observability endpoint for collecting telemetry data from the QType runtime."""

    id: str = Field(
        ..., description="Unique ID of the telemetry sink configuration."
    )
    endpoint: str = Field(
        ..., description="URL endpoint where telemetry data will be sent."
    )
    auth: str | None = Field(
        default=None,
        description="AuthorizationProvider ID used to authenticate telemetry data transmission.",
    )


class FeedbackType(str, Enum):
    """Enum of supported feedback mechanisms such as thumbs, stars, or text responses."""

    THUMBS = "thumbs"
    STAR = "star"
    TEXT = "text"
    RATING = "rating"
    CHOICE = "choice"
    BOOLEAN = "boolean"


class Feedback(StrictBaseModel):
    """Schema to define how user feedback is collected, structured, and optionally used to guide future prompts."""

    id: str = Field(..., description="Unique ID of the feedback config.")
    type: FeedbackType = Field(..., description="Feedback mechanism type.")
    question: str | None = Field(
        default=None,
        description="Question to show user for qualitative feedback.",
    )
    prompt: str | None = Field(
        default=None,
        description="ID of prompt used to generate a follow-up based on feedback.",
    )


class Condition(StrictBaseModel):
    """Conditional logic gate within a flow. Supports branching logic for execution based on variable values."""

    if_var: str = Field(..., description="ID of the variable to evaluate.")
    equals: str | int | float | bool | None = Field(
        default=None, description="Match condition for equality check."
    )
    exists: bool | None = Field(
        default=None, description="Condition to check existence of a variable."
    )
    then: list[str] = Field(
        ..., description="List of step IDs to run if condition matches."
    )
    else_: list[str] | None = Field(
        default=None,
        alias="else",
        description="Optional list of step IDs to run if condition fails.",
    )


class Actionable(StrictBaseModel):
    """Base class for components that can be executed with inputs and outputs."""

    id: str = Field(..., description="Unique ID of this component.")
    inputs: list[str] | None = Field(
        default=None,
        description="Input variable IDs required by this component.",
    )
    outputs: list[str] | None = Field(
        default=None, description="Variable IDs where output is stored."
    )


class FlowMode(str, Enum):
    """Execution context for the flow. `chat` maintains history, while `complete` operates statelessly."""

    chat = "chat"
    complete = "complete"


class Flow(Actionable):
    """Composable structure that defines the interaction logic for a generative AI application.
    Supports branching, memory, and sequencing of steps."""

    mode: FlowMode = Field(..., description="Interaction mode for the flow.")
    steps: list["Step | str"] = Field(
        default_factory=list, description="List of steps or nested step IDs."
    )
    conditions: list[Condition] | None = Field(
        default=None, description="Optional conditional logic within the flow."
    )
    memory: list[str] | None = Field(
        default=None,
        description="List of memory IDs to include (chat mode only).",
    )


class Agent(Actionable):
    type: Literal["agent"] = "agent"
    model: str = Field(
        ..., description="The id of the model for this agent to use."
    )
    prompt: str = Field(
        ..., description="The id of the prompt for this agent to use"
    )
    tools: list[str] | None = Field(
        default=None, description="Tools that this agent has access to"
    )


Step = Annotated[Agent | Tool | VectorDBRetriever, Field(discriminator="type")]


class QTypeSpec(StrictBaseModel):
    """The root configuration object for a QType AI application. Includes flows, models, tools, and more.
    This object is expected to be serialized into YAML and consumed by the QType runtime."""

    version: str = Field(
        ..., description="Version of the QType specification schema used."
    )
    models: list[Model] | None = Field(
        default=None,
        description="List of generative models available for use, including their providers and inference parameters.",
    )
    variables: list[Variable] | None = Field(
        default=None,
        description="Variables or parameters exposed by the application.",
    )
    prompts: list[Prompt] | None = Field(
        default=None,
        description="Prompt templates used in generation steps or tools, referencing input and output variables.",
    )
    tool_providers: list[ToolProvider] | None = Field(
        default=None,
        description="Tool providers with optional OpenAPI specs, exposing callable tools for the model.",
    )
    flows: list[Flow] | None = Field(
        default=None,
        description="Entry points to application logic. Each flow defines an executable composition of steps.",
    )
    agents: list[Agent] | None = Field(
        default=None,
        description="AI agents with specific models, prompts, and tools for autonomous task execution.",
    )
    feedback: list[Feedback] | None = Field(
        default=None,
        description="Feedback configurations for collecting structured or unstructured user reactions to outputs.",
    )
    memory: list[Memory] | None = Field(
        default=None,
        description="Session-level memory contexts, only used in chat-mode flows to persist state across turns.",
    )
    auth: list[AuthorizationProvider] | None = Field(
        default=None,
        description="Authorization providers and credentials used to access external APIs or cloud services.",
    )
    telemetry: list[TelemetrySink] | None = Field(
        default=None,
        description="Telemetry sinks for collecting observability data from the QType runtime.",
    )
