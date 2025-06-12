from enum import Enum
from typing import List, Optional, Dict, Union, Any
from pydantic import BaseModel, Field
from abc import ABC



class VariableType(str, Enum):
    """Type of input expected from the user."""

    text = "text"
    number = "number"
    file = "file"
    image = "image"
    date = "date"
    time = "time"
    datetime = "datetime"
    video = "video"
    audio = "audio"


class DisplayType(str, Enum):
    """Display type hint for rendering input UI components."""

    text = "text"
    textarea = "textarea"
    dropdown = "dropdown"
    file_upload = "file_upload"
    checkbox = "checkbox"
    slider = "slider"
    radio = "radio"
    group = "group"
    section = "section"


class DisplayMetadata(BaseModel):
    """UI display hints for rendering an input field."""

    placeholder: Optional[str] = Field(
        None, description="Placeholder text shown inside the input field."
    )
    tooltip: Optional[str] = Field(None, description="Tooltip shown on hover.")
    default_value: Optional[Any] = Field(
        None, description="Default value if the user doesn't supply one."
    )
    min_value: Optional[Union[int, float]] = Field(
        None, description="Minimum value for numeric inputs."
    )
    max_value: Optional[Union[int, float]] = Field(
        None, description="Maximum value for numeric inputs."
    )
    step: Optional[Union[int, float]] = Field(
        None, description="Step size for numeric inputs."
    )
    allowed_types: Optional[List[str]] = Field(
        None, description="Allowed file types for file upload."
    )
    options: Optional[List[str]] = Field(
        None, description="Options for dropdowns, radios, or checkboxes."
    )
    group: Optional[str] = Field(
        None, description="Grouping section this input belongs to."
    )
    section: Optional[str] = Field(
        None, description="Section name used to visually separate inputs."
    )
    icon: Optional[str] = Field(
        None, description="Icon shown alongside input (optional)."
    )
    css_class: Optional[str] = Field(
        None, description="Optional CSS class for advanced styling."
    )


class Input(BaseModel):
    """Represents an input field provided by the user or external system."""

    id: str = Field(
        ..., description="Unique ID of the input. Referenced in prompts or steps."
    )
    type: VariableType = Field(..., description="Type of data expected.")
    display_name: Optional[str] = Field(None, description="Label shown in the UI.")
    display_type: Optional[DisplayType] = Field(
        None, description="Hint for how to render this input."
    )
    display_metadata: Optional[DisplayMetadata] = Field(
        None, description="Additional UI hints."
    )


class Output(BaseModel):
    """Defines the structure of a single output."""

    id: str = Field(
        ...,
        description="Unique ID of the output. Referenced by prompt outputs or step responses.",
    )
    type: VariableType = Field(
        ..., description="Type of output produced (e.g., text, image, json)."
    )


class Prompt(BaseModel):
    """Points to a prompt template used for generation."""

    id: str = Field(..., description="Unique ID for the prompt.")
    path: Optional[str] = Field(None, description="File path to the prompt template.")
    template: Optional[str] = Field(
        None, description="Inline template string for the prompt."
    )
    input_vars: List[str] = Field(
        ..., description="List of input variable IDs this prompt expects."
    )
    output_vars: Optional[List[str]] = Field(
        None, description="Optional list of output variable IDs this prompt generates."
    )


class Model(BaseModel):
    """Represents a generative model configuration."""

    id: str = Field(..., description="Unique ID for the model.")
    provider: str = Field(
        ..., description="Name of the provider, e.g., openai or anthropic."
    )
    model_id: Optional[str] = Field(
        None,
        description="The specific model name or ID for the provider. If None, id is used",
    )
    inference_params: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional inference parameters like temperature or max_tokens.",
    )


class EmbeddingModel(Model):
    """Describes a model used for embedding text for vector search or memory."""
    dimensions: int = Field(
        ..., description="Dimensionality of the embedding vectors produced by this model."
    )


class BaseRetriever(BaseModel, ABC):
    """Abstract base class for retrievers that fetch supporting documents."""

    id: str = Field(..., description="Unique ID of the retriever.")
    index: str = Field(..., description="ID of the index this retriever uses.")


class VectorDBRetriever(BaseRetriever):
    """Retriever that queries a vector database using an embedding-based search."""

    embedding_model: str = Field(
        ..., description="ID of the embedding model used to vectorize the query."
    )
    top_k: int = Field(5, description="Number of top documents to retrieve.")


class SearchRetriever(BaseRetriever):
    """Retriever that queries a keyword or hybrid search engine."""

    top_k: int = Field(5, description="Number of top documents to retrieve.")
    query_prompt: Optional[str] = Field(
        None, description="Prompt ID used to generate the search query."
    )


class MemoryType(str, Enum):
    """Enum for memory types."""

    vector = "vector"


class Memory(BaseModel):
    """Persistent or session-level memory context for a user or flow."""

    id: str = Field(..., description="Unique ID of the memory block.")
    type: MemoryType = Field(..., description="The type of memory to store context.")
    embedding_model: str = Field(
        ..., description="Embedding model ID used for storage."
    )
    persist: bool = Field(
        default=False, description="Whether memory persists across sessions."
    )
    ttl_minutes: Optional[int] = Field(
        None, description="Optional TTL for temporary memory."
    )
    use_for_context: bool = Field(
        default=True, description="Whether this memory should be injected as context."
    )


class Tool(BaseModel):
    """A single callable tool/function exposed to the model."""

    id: str = Field(..., description="Unique ID of the tool.")
    name: str = Field(..., description="Name of the tool function.")
    description: str = Field(..., description="Description of what the tool does.")
    input_schema: Dict[str, Any] = Field(
        ..., 
        description="JSON Schema describing the input parameters for the API endpoint."
    )
    output_schema: Dict[str, Any] = Field(
        ..., 
        description="JSON Schema describing the response structure from the API endpoint."
    )


class ToolProvider(BaseModel):
    """Wraps and authenticates access to a set of tools (often from a single API or OpenAPI spec)."""

    id: str = Field(..., description="Unique ID of the tool provider.")
    name: str = Field(..., description="Name of the tool provider.")
    tools: List[Tool] = Field(
        ..., description="List of tools exposed by this provider."
    )
    openapi_spec: Optional[str] = Field(
        None,
        description="Optional path or URL to an OpenAPI spec to auto-generate tools.",
    )
    include_tags: Optional[List[str]] = Field(
        None, description="Limit tool generation to specific OpenAPI tags."
    )
    exclude_paths: Optional[List[str]] = Field(
        None, description="Exclude specific endpoints by path."
    )
    auth: Optional[str] = Field(
        None, description="AuthorizationProvider ID used to authenticate tool access."
    )


class AuthorizationProvider(BaseModel):
    """Represents credentials and auth settings for accessing protected APIs."""

    id: str = Field(..., description="Unique ID of the authorization configuration.")
    type: str = Field(
        ..., description="Authorization method, e.g., 'oauth2' or 'api_key'."
    )
    host: Optional[str] = Field(None, description="Base URL or domain of the provider.")
    client_id: Optional[str] = Field(None, description="OAuth2 client ID.")
    client_secret: Optional[str] = Field(None, description="OAuth2 client secret.")
    token_url: Optional[str] = Field(None, description="Token endpoint URL.")
    scopes: Optional[List[str]] = Field(None, description="OAuth2 scopes required.")
    api_key: Optional[str] = Field(
        None, description="API key if using token-based auth."
    )


class FeedbackType(str, Enum):
    """Types of feedback mechanisms available."""
    
    THUMBS = "thumbs"
    STAR = "star" 
    TEXT = "text"
    RATING = "rating"
    CHOICE = "choice"
    BOOLEAN = "boolean"


class Feedback(BaseModel):
    """Describes how and where to collect feedback on generated responses."""

    id: str = Field(..., description="Unique ID of the feedback config.")
    type: FeedbackType = Field(
        ..., description="Feedback mechanism type."
    )
    question: Optional[str] = Field(
        None, description="Question to show user for qualitative feedback."
    )
    prompt: Optional[str] = Field(
        None, description="ID of prompt used to generate a follow-up based on feedback."
    )


class Condition(BaseModel):
    """Conditional logic for branching execution within a flow."""

    if_var: str = Field(..., description="ID of the variable to evaluate.")
    equals: Optional[Union[str, int, float, bool]] = Field(
        None, description="Match condition for equality check."
    )
    exists: Optional[bool] = Field(
        None, description="Condition to check existence of a variable."
    )
    then: List[str] = Field(
        ..., description="List of step IDs to run if condition matches."
    )
    else_: Optional[List[str]] = Field(
        None,
        alias="else",
        description="Optional list of step IDs to run if condition fails.",
    )


class Step(BaseModel):
    """A single execution step within a flow (e.g., prompt, tool call, or memory update)."""

    id: str = Field(..., description="Unique ID of the step.")
    input_vars: Optional[List[str]] = Field(
        None, description="Input variable IDs required by this step."
    )
    output_vars: Optional[List[str]] = Field(
        None, description="Variable IDs where output is stored."
    )
    component: Optional[str] = Field(
        None, description="ID of the component to invoke (e.g., prompt ID, tool ID)."
    )


class FlowMode(str, Enum):
    """Execution mode for a flow."""

    chat = "chat"
    complete = "complete"
    api = "api"


class Flow(Step):
    """A flow represents the full composition of steps a user or system interacts with."""

    mode: FlowMode = Field(..., description="Interaction mode for the flow.")
    inputs: Optional[List[str]] = Field(
        None, description="Input variable IDs accepted by the flow."
    )
    outputs: Optional[List[str]] = Field(
        None, description="Output variable IDs produced by the flow."
    )
    steps: List[Union[Step, str]] = Field(
        ..., description="List of steps or nested flow IDs."
    )
    conditions: Optional[List[Condition]] = Field(
        None, description="Optional conditional logic within the flow."
    )
    memory: Optional[List[str]] = Field(
        None, description="List of memory IDs to include (chat mode only)."
    )

class QTypeSpec(BaseModel):
    """
    The top-level definition of a QType specification.

    This class represents the full configuration of a generative AI application,
    including models, inputs, prompts, tools, flows, and supporting infrastructure.

    Only one `QTypeSpec` should exist per YAML spec file.
    """

    version: str = Field(
        ..., description="Version of the QType specification schema used."
    )
    models: Optional[List[Model]] = Field(
        None,
        description="List of generative models available for use, including their providers and inference parameters.",
    )
    inputs: Optional[List[Input]] = Field(
        None, description="User-facing inputs or parameters exposed by the application."
    )
    prompts: Optional[List[Prompt]] = Field(
        None,
        description="Prompt templates used in generation steps or tools, referencing input and output variables.",
    )
    retrievers: Optional[List[BaseRetriever]] = Field(
        None,
        description="Document retrievers used to fetch context from indexes (e.g., vector search, keyword search).",
    )
    tools: Optional[List[ToolProvider]] = Field(
        None,
        description="Tool providers with optional OpenAPI specs, exposing callable tools for the model.",
    )
    flows: Optional[List[Flow]] = Field(
        None,
        description="Entry points to application logic. Each flow defines an executable composition of steps.",
    )
    feedback: Optional[List[Feedback]] = Field(
        None,
        description="Feedback configurations for collecting structured or unstructured user reactions to outputs.",
    )
    memory: Optional[List[Memory]] = Field(
        None,
        description="Session-level memory contexts, only used in chat-mode flows to persist state across turns.",
    )
    auth: Optional[List[AuthorizationProvider]] = Field(
        None,
        description="Authorization providers and credentials used to access external APIs or cloud services.",
    )
