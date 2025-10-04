"""
Semantic Intermediate Representation models.

This module contains the semantic models that represent a resolved QType
specification where all ID references have been replaced with actual object
references.

Generated automatically with command:
qtype generate semantic-model

Types are ignored since they should reflect dsl directly, which is type checked.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

# Import enums and type aliases from DSL
from qtype.dsl.model import VariableType  # noqa: F401
from qtype.dsl.model import (  # noqa: F401
    CustomType,
    DecoderFormat,
    ListType,
    PrimitiveTypeEnum,
    StepCardinality,
    StructuralTypeEnum,
    ToolParameter,
)
from qtype.dsl.model import Variable as DSLVariable  # noqa: F401
from qtype.semantic.base_types import ImmutableModel


class Variable(DSLVariable, BaseModel):
    """Semantic version of DSL Variable with ID references resolved."""

    value: Any | None = Field(None, description="The value of the variable")

    def is_set(self) -> bool:
        return self.value is not None


class AuthorizationProvider(ImmutableModel):
    """Base class for authentication providers."""

    id: str = Field(
        ..., description="Unique ID of the authorization configuration."
    )
    type: str = Field(..., description="Authorization method type.")


class Tool(ImmutableModel):
    """
    Base class for callable functions or external operations available to the model or as a step in a flow.
    """

    id: str = Field(..., description="Unique ID of this component.")
    name: str = Field(..., description="Name of the tool function.")
    description: str = Field(
        ..., description="Description of what the tool does."
    )
    inputs: dict[str, ToolParameter] = Field(
        {}, description="Input parameters required by this tool."
    )
    outputs: dict[str, ToolParameter] = Field(
        {}, description="Output parameters produced by this tool."
    )


class Application(BaseModel):
    """Defines a complete QType application specification.

    An Application is the top-level container of the entire
    program in a QType YAML file. It serves as the blueprint for your
    AI-powered application, containing all the models, flows, tools, data sources,
    and configuration needed to run your program. Think of it as the main entry
    point that ties together all components into a cohesive,
    executable system.
    """

    id: str = Field(..., description="Unique ID of the application.")
    description: str | None = Field(
        None, description="Optional description of the application."
    )
    memories: list[Memory] = Field(
        [], description="List of memory definitions used in this application."
    )
    models: list[Model] = Field(
        [], description="List of models used in this application."
    )
    types: list[CustomType] = Field(
        [], description="List of custom types defined in this application."
    )
    variables: list[Variable] = Field(
        [], description="List of variables used in this application."
    )
    flows: list[Flow] = Field(
        [], description="List of flows defined in this application."
    )
    auths: list[
        APIKeyAuthProvider
        | BearerTokenAuthProvider
        | AWSAuthProvider
        | OAuth2AuthProvider
    ] = Field(
        [], description="List of authorization providers used for API access."
    )
    tools: list[Tool] = Field(
        [], description="List of tools available in this application."
    )
    indexes: list[Index] = Field(
        [], description="List of indexes available for search operations."
    )
    telemetry: TelemetrySink | None = Field(
        None, description="Optional telemetry sink for observability."
    )


class Step(BaseModel):
    """Base class for components that take inputs and produce outputs."""

    id: str = Field(..., description="Unique ID of this component.")
    type: str = Field(..., description="Type of the step component.")
    cardinality: StepCardinality = Field(
        StepCardinality.one,
        description="Does this step emit 1 (one) or 0...N (many) instances of the outputs?",
    )
    inputs: list[Variable] = Field(
        [], description="Input variables required by this step."
    )
    outputs: list[Variable] = Field(
        [], description="Variable where output is stored."
    )


class Index(ImmutableModel):
    """Base class for searchable indexes that can be queried by search steps."""

    id: str = Field(..., description="Unique ID of the index.")
    args: dict[str, Any] = Field(
        {},
        description="Index-specific configuration and connection parameters.",
    )
    auth: (
        APIKeyAuthProvider
        | BearerTokenAuthProvider
        | AWSAuthProvider
        | OAuth2AuthProvider
        | None
    ) = Field(
        None, description="AuthorizationProvider for accessing the index."
    )
    name: str = Field(..., description="Name of the index/collection/table.")


class Model(ImmutableModel):
    """Describes a generative model configuration, including provider and model ID."""

    id: str = Field(..., description="Unique ID for the model.")
    auth: (
        APIKeyAuthProvider
        | BearerTokenAuthProvider
        | AWSAuthProvider
        | OAuth2AuthProvider
        | None
    ) = Field(None, description="AuthorizationProvider used for model access.")
    inference_params: dict[str, Any] = Field(
        {},
        description="Optional inference parameters like temperature or max_tokens.",
    )
    model_id: str | None = Field(
        None,
        description="The specific model name or ID for the provider. If None, id is used",
    )
    provider: str = Field(
        ..., description="Name of the provider, e.g., openai or anthropic."
    )


class Memory(ImmutableModel):
    """Session or persistent memory used to store relevant conversation or state data across steps or turns."""

    id: str = Field(..., description="Unique ID of the memory block.")
    token_limit: int = Field(
        100000, description="Maximum number of tokens to store in memory."
    )
    chat_history_token_ratio: float = Field(
        0.7, description="Ratio of chat history tokens to total memory tokens."
    )
    token_flush_size: int = Field(
        3000,
        description="Size of memory to flush when it exceeds the token limit.",
    )


class TelemetrySink(BaseModel):
    """Defines an observability endpoint for collecting telemetry data from the QType runtime."""

    id: str = Field(
        ..., description="Unique ID of the telemetry sink configuration."
    )
    auth: (
        APIKeyAuthProvider
        | BearerTokenAuthProvider
        | AWSAuthProvider
        | OAuth2AuthProvider
        | None
    ) = Field(
        None,
        description="AuthorizationProvider used to authenticate telemetry data transmission.",
    )
    endpoint: str = Field(
        ..., description="URL endpoint where telemetry data will be sent."
    )


class APIKeyAuthProvider(AuthorizationProvider):
    """API key-based authentication provider."""

    type: Literal["api_key"] = Field("api_key")
    api_key: str = Field(..., description="API key for authentication.")
    host: str | None = Field(
        None, description="Base URL or domain of the provider."
    )


class AWSAuthProvider(AuthorizationProvider):
    """AWS authentication provider supporting multiple credential methods."""

    type: Literal["aws"] = Field("aws")
    access_key_id: str | None = Field(None, description="AWS access key ID.")
    secret_access_key: str | None = Field(
        None, description="AWS secret access key."
    )
    session_token: str | None = Field(
        None, description="AWS session token for temporary credentials."
    )
    profile_name: str | None = Field(
        None, description="AWS profile name from credentials file."
    )
    role_arn: str | None = Field(
        None, description="ARN of the role to assume."
    )
    role_session_name: str | None = Field(
        None, description="Session name for role assumption."
    )
    external_id: str | None = Field(
        None, description="External ID for role assumption."
    )
    region: str | None = Field(None, description="AWS region.")


class BearerTokenAuthProvider(AuthorizationProvider):
    """Bearer token authentication provider."""

    type: Literal["bearer_token"] = Field("bearer_token")
    token: str = Field(..., description="Bearer token for authentication.")


class OAuth2AuthProvider(AuthorizationProvider):
    """OAuth2 authentication provider."""

    type: Literal["oauth2"] = Field("oauth2")
    client_id: str = Field(..., description="OAuth2 client ID.")
    client_secret: str = Field(..., description="OAuth2 client secret.")
    token_url: str = Field(..., description="Token endpoint URL.")
    scopes: list[str] = Field([], description="OAuth2 scopes required.")


class APITool(Tool):
    """Tool that invokes an API endpoint."""

    endpoint: str = Field(..., description="API endpoint URL to call.")
    method: str = Field(
        "GET", description="HTTP method to use (GET, POST, PUT, DELETE, etc.)."
    )
    auth: (
        APIKeyAuthProvider
        | BearerTokenAuthProvider
        | AWSAuthProvider
        | OAuth2AuthProvider
        | None
    ) = Field(
        None,
        description="Optional AuthorizationProvider for API authentication.",
    )
    headers: dict[str, str] = Field(
        {}, description="Optional HTTP headers to include in the request."
    )
    parameters: dict[str, ToolParameter] = Field(
        {}, description="Output parameters produced by this tool."
    )


class PythonFunctionTool(Tool):
    """Tool that calls a Python function."""

    function_name: str = Field(
        ..., description="Name of the Python function to call."
    )
    module_path: str = Field(
        ..., description="Optional module path where the function is defined."
    )


class Condition(Step):
    """Conditional logic gate within a flow. Supports branching logic for execution based on variable values."""

    type: Literal["Condition"] = Field("Condition")
    else_: Step | str | None = Field(
        None,
        description="Optional step to run if condition fails.",
        alias="else",
    )
    equals: Variable | None = Field(
        None, description="Match condition for equality check."
    )
    then: Step | str = Field(
        ..., description="Step to run if condition matches."
    )


class Decoder(Step):
    """Defines a step that decodes string data into structured outputs.

    If parsing fails, the step will raise an error and halt execution.
    Use conditional logic in your flow to handle potential parsing errors."""

    type: Literal["Decoder"] = Field("Decoder")
    format: DecoderFormat = Field(
        DecoderFormat.json,
        description="Format in which the decoder processes data. Defaults to JSON.",
    )


class Invoke(Step):
    """Invokes a tool with input and output bindings."""

    type: Literal["Invoke"] = Field("Invoke")
    tool: Tool = Field(..., description="Tool to invoke.")
    input_bindings: dict[str, str] = Field(
        ...,
        description="Mapping from step input IDs to tool input parameter names.",
    )
    output_bindings: dict[str, str] = Field(
        ...,
        description="Mapping from tool output parameter names to step output IDs.",
    )


class LLMInference(Step):
    """Defines a step that performs inference using a language model.
    It can take input variables and produce output variables based on the model's response."""

    type: Literal["LLMInference"] = Field("LLMInference")
    memory: Memory | None = Field(
        None,
        description="Memory object to retain context across interactions.",
    )
    model: Model = Field(..., description="The model to use for inference.")
    system_message: str | None = Field(
        None,
        description="Optional system message to set the context for the model.",
    )


class PromptTemplate(Step):
    """Defines a prompt template with a string format and variable bindings.
    This is used to generate prompts dynamically based on input variables."""

    type: Literal["PromptTemplate"] = Field("PromptTemplate")
    template: str = Field(
        ...,
        description="String template for the prompt with variable placeholders.",
    )


class Search(Step):
    """Base class for search operations against indexes."""

    filters: dict[str, Any] = Field(
        {}, description="Optional filters to apply during search."
    )
    index: Index = Field(
        ..., description="Index to search against (object or ID reference)."
    )


class Sink(Step):
    """Base class for data sinks"""

    id: str = Field(..., description="Unique ID of the data sink.")
    cardinality: Literal["one"] = Field(
        StepCardinality.one,
        description="Flows always emit exactly one instance of the outputs.",
    )


class Source(Step):
    """Base class for data sources"""

    id: str = Field(..., description="Unique ID of the data source.")
    cardinality: Literal["many"] = Field(
        StepCardinality.many,
        description="Sources always emit 0...N instances of the outputs.",
    )


class DocumentIndex(Index):
    """Document search index for text-based search (e.g., Elasticsearch, OpenSearch)."""

    pass


class VectorIndex(Index):
    """Vector database index for similarity search using embeddings."""

    embedding_model: EmbeddingModel = Field(
        ...,
        description="Embedding model used to vectorize queries and documents.",
    )


class EmbeddingModel(Model):
    """Describes an embedding model configuration, extending the base Model class."""

    dimensions: int = Field(
        ...,
        description="Dimensionality of the embedding vectors produced by this model.",
    )


class Agent(LLMInference):
    """Defines an agent that can perform tasks and make decisions based on user input and context."""

    type: Literal["Agent"] = Field("Agent")
    tools: list[Tool] = Field(
        ..., description="List of tools available to the agent."
    )


class DocumentSearch(Search):
    """Performs document search against a document index."""

    type: Literal["DocumentSearch"] = Field("DocumentSearch")


class VectorSearch(Search):
    """Performs vector similarity search against a vector index."""

    type: Literal["VectorSearch"] = Field("VectorSearch")
    default_top_k: int | None = Field(
        50,
        description="Number of top results to retrieve if not provided in the inputs.",
    )


class FileSink(Sink):
    """File sink that writes data to a file using fsspec-compatible URIs."""

    type: Literal["FileSink"] = Field("FileSink")
    path: str | None = Field(
        None,
        description="fsspec-compatible URI to write to. If None, expects 'path' input variable.",
    )


class IndexUpsert(Sink):
    """Semantic version of IndexUpsert."""

    type: Literal["IndexUpsert"] = Field("IndexUpsert")
    index: Index = Field(
        ..., description="Index to upsert into (object or ID reference)."
    )


class FileSource(Source):
    """File source that reads data from a file using fsspec-compatible URIs."""

    type: Literal["FileSource"] = Field("FileSource")
    path: str | None = Field(
        None,
        description="fsspec-compatible URI to read from. If None, expects 'path' input variable.",
    )


class SQLSource(Source):
    """SQL database source that executes queries and emits rows."""

    type: Literal["SQLSource"] = Field("SQLSource")
    query: str = Field(
        ..., description="SQL query to execute. Inputs are injected as params."
    )
    connection: str = Field(
        ...,
        description="Database connection string or reference to auth provider. Typically in SQLAlchemy format.",
    )
    auth: (
        APIKeyAuthProvider
        | BearerTokenAuthProvider
        | AWSAuthProvider
        | OAuth2AuthProvider
        | None
    ) = Field(
        None,
        description="Optional AuthorizationProvider for database authentication.",
    )


class Flow(Step):
    """Defines a flow of steps that can be executed in sequence or parallel.
    If input or output variables are not specified, they are inferred from
    the first and last step, respectively.
    """

    description: str | None = Field(
        None, description="Optional description of the flow."
    )
    cardinality: StepCardinality = Field(
        StepCardinality.auto,
        description="The cardinality of the flow, inferred from its steps when set to 'auto'.",
    )
    mode: Literal["Complete", "Chat"] = Field("Complete")
    steps: list[Step] = Field(..., description="List of steps or step IDs.")

    @model_validator(mode="after")
    def infer_cardinality(self) -> "Flow":
        if self.cardinality == StepCardinality.auto:
            self.cardinality = StepCardinality.one
            for step in self.steps:
                if step.cardinality == StepCardinality.many:
                    self.cardinality = StepCardinality.many
                    break
        return self
