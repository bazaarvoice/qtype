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

from functools import partial
from typing import Any, Literal, Union

from pydantic import BaseModel, Field

# Import enums, mixins, and type aliases
from qtype.base.types import (  # noqa: F401
    BatchableStepMixin,
    BatchConfig,
    CachedStepMixin,
    ConcurrencyConfig,
    ConcurrentStepMixin,
)
from qtype.dsl.model import VariableType  # noqa: F401
from qtype.dsl.model import (  # noqa: F401
    CustomType,
    DecoderFormat,
    ListType,
    PrimitiveTypeEnum,
    StepCardinality,
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
        default_factory=dict,
        description="Input parameters required by this tool.",
    )
    outputs: dict[str, ToolParameter] = Field(
        default_factory=dict,
        description="Output parameters produced by this tool.",
    )


class SecretManager(BaseModel):
    """Base class for secret manager configurations."""

    id: str = Field(
        ..., description="Unique ID for this secret manager configuration."
    )
    type: str = Field(..., description="The type of secret manager.")
    auth: AuthorizationProvider = Field(
        ...,
        description="AuthorizationProvider used to access this secret manager.",
    )


class Step(CachedStepMixin, BaseModel):
    """Base class for components that take inputs and produce outputs."""

    id: str = Field(..., description="Unique ID of this component.")
    type: str = Field(..., description="Type of the step component.")
    cardinality: StepCardinality = Field(
        StepCardinality.one,
        description="Does this step emit 1 (one) or 0...N (many) instances of the outputs?",
    )
    inputs: list[Variable] = Field(
        default_factory=list,
        description="References to the variables required by this step.",
    )
    outputs: list[Variable] = Field(
        default_factory=list,
        description="References to the variables where output is stored.",
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
        default_factory=list,
        description="List of memory definitions used in this application.",
    )
    models: list[Model] = Field(
        default_factory=list,
        description="List of models used in this application.",
    )
    types: list[CustomType] = Field(
        default_factory=list,
        description="List of custom types defined in this application.",
    )
    flows: list[Flow] = Field(
        default_factory=list,
        description="List of flows defined in this application.",
    )
    auths: list[AuthorizationProvider] = Field(
        default_factory=list,
        description="List of authorization providers used for API access.",
    )
    tools: list[Tool] = Field(
        default_factory=list,
        description="List of tools available in this application.",
    )
    indexes: list[Index] = Field(
        default_factory=list,
        description="List of indexes available for search operations.",
    )
    secret_manager: AWSSecretManager | None = Field(
        None,
        description="Optional secret manager configuration for the application.",
    )
    telemetry: TelemetrySink | None = Field(
        None, description="Optional telemetry sink for observability."
    )


class AuthorizationProviderList(BaseModel):
    """Schema for a standalone list of authorization providers."""

    root: list[AuthorizationProvider] = Field(...)


class ConstantPath(BaseModel):
    """Semantic version of ConstantPath."""

    uri: str = Field(..., description="A constant Fsspec URI.")


class Index(ImmutableModel):
    """Base class for searchable indexes that can be queried by search steps."""

    id: str = Field(..., description="Unique ID of the index.")
    args: dict[str, Any] = Field(
        default_factory=dict,
        description="Index-specific configuration and connection parameters.",
    )
    auth: AuthorizationProvider | None = Field(
        None, description="AuthorizationProvider for accessing the index."
    )
    name: str = Field(..., description="Name of the index/collection/table.")


class Model(ImmutableModel):
    """Describes a generative model configuration, including provider and model ID."""

    type: Literal["Model"] = Field("Model")
    id: str = Field(..., description="Unique ID for the model.")
    auth: AuthorizationProvider | None = Field(
        None, description="AuthorizationProvider used for model access."
    )
    inference_params: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional inference parameters like temperature or max_tokens.",
    )
    model_id: str | None = Field(
        None,
        description="The specific model name or ID for the provider. If None, id is used",
    )
    provider: Literal["openai", "anthropic", "aws-bedrock", "gcp-vertex"] = (
        Field(
            ..., description="Name of the provider, e.g., openai or anthropic."
        )
    )


class Flow(BaseModel):
    """Defines a flow of steps that can be executed in sequence or parallel.
    If input or output variables are not specified, they are inferred from
    the first and last step, respectively."""

    id: str = Field(..., description="Unique ID of the flow.")
    type: Literal["Flow"] = Field("Flow")
    description: str | None = Field(
        None, description="Optional description of the flow."
    )
    steps: list[Step | Step] = Field(
        default_factory=list,
        description="List of steps or references to steps",
    )
    interface: FlowInterface | None = Field(None)
    variables: list[Variable] = Field(
        default_factory=list,
        description="List of variables available at the application scope.",
    )
    inputs: list[Variable] = Field(
        default_factory=list,
        description="Input variables required by this step.",
    )
    outputs: list[Variable] = Field(
        default_factory=list, description="Resulting variables"
    )


class FlowInterface(BaseModel):
    """
    Defines the public-facing contract for a Flow, guiding the UI
    and session management.
    """

    type: Literal["Complete", "Conversational"] = Field("Complete")
    session_inputs: list[Variable] = Field(
        default_factory=list,
        description="A list of input variable IDs that are set once and then persisted across a session.",
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


class ModelList(BaseModel):
    """Schema for a standalone list of models."""

    root: list[Model] = Field(...)


class SecretReference(BaseModel):
    """
    A reference to a secret in the application's configured SecretManager.
    This value is resolved at runtime by the interpreter.
    """

    secret_name: str = Field(
        ...,
        description="The name, ID, or ARN of the secret to fetch (e.g., 'my-project/db-password').",
    )
    key: str | None = Field(
        None,
        description="Optional key if the secret is a JSON blob or map (e.g., a specific key in a K8s secret).",
    )


class TelemetrySink(BaseModel):
    """Defines an observability endpoint for collecting telemetry data from the QType runtime."""

    id: str = Field(
        ..., description="Unique ID of the telemetry sink configuration."
    )
    provider: Literal["Phoenix", "Langfuse"] = Field("Phoenix")
    auth: AuthorizationProvider | None = Field(
        None,
        description="AuthorizationProvider used to authenticate telemetry data transmission.",
    )
    endpoint: str | SecretReference = Field(
        ..., description="URL endpoint where telemetry data will be sent."
    )
    args: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional configuration arguments specific to the telemetry sink type.",
    )


class ToolList(BaseModel):
    """Schema for a standalone list of tools."""

    root: list[Tool] = Field(...)


class TypeList(BaseModel):
    """Schema for a standalone list of type definitions."""

    root: list[CustomType] = Field(...)


class VariableList(BaseModel):
    """Schema for a standalone list of variables."""

    root: list[Variable] = Field(...)


class APIKeyAuthProvider(AuthorizationProvider):
    """API key-based authentication provider."""

    type: Literal["api_key"] = Field("api_key")
    api_key: str | SecretReference = Field(
        ..., description="API key for authentication."
    )
    host: str | None = Field(
        None, description="Base URL or domain of the provider."
    )


class AWSAuthProvider(AuthorizationProvider):
    """AWS authentication provider supporting multiple credential methods."""

    type: Literal["aws"] = Field("aws")
    access_key_id: str | SecretReference | None = Field(
        None, description="AWS access key ID."
    )
    secret_access_key: str | SecretReference | None = Field(
        None, description="AWS secret access key."
    )
    session_token: str | SecretReference | None = Field(
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
    token: str | SecretReference = Field(
        ..., description="Bearer token for authentication."
    )


class OAuth2AuthProvider(AuthorizationProvider):
    """OAuth2 authentication provider."""

    type: Literal["oauth2"] = Field("oauth2")
    client_id: str = Field(..., description="OAuth2 client ID.")
    client_secret: str | SecretReference = Field(
        ..., description="OAuth2 client secret."
    )
    token_url: str = Field(..., description="Token endpoint URL.")
    scopes: list[str] = Field(
        default_factory=list, description="OAuth2 scopes required."
    )


class VertexAuthProvider(AuthorizationProvider):
    """Google Vertex authentication provider supporting gcloud profile or service account."""

    type: Literal["vertex"] = Field("vertex")
    profile_name: str | None = Field(
        None,
        description="Local gcloud profile name (if using existing CLI credentials).",
    )
    project_id: str | None = Field(
        None,
        description="Explicit GCP project ID override (if different from profile).",
    )
    service_account_file: str | None = Field(
        None, description="Path to a service account JSON key file."
    )
    region: str | None = Field(
        None, description="Vertex region (e.g., us-central1)."
    )


class APITool(Tool):
    """Tool that invokes an API endpoint."""

    type: Literal["APITool"] = Field("APITool")
    endpoint: str = Field(..., description="API endpoint URL to call.")
    method: str = Field(
        "GET", description="HTTP method to use (GET, POST, PUT, DELETE, etc.)."
    )
    auth: AuthorizationProvider | None = Field(
        None,
        description="Optional AuthorizationProvider for API authentication.",
    )
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Optional HTTP headers to include in the request.",
    )
    parameters: dict[str, ToolParameter] = Field(
        default_factory=dict,
        description="Output parameters produced by this tool.",
    )


class PythonFunctionTool(Tool):
    """Tool that calls a Python function."""

    type: Literal["PythonFunctionTool"] = Field("PythonFunctionTool")
    function_name: str = Field(
        ..., description="Name of the Python function to call."
    )
    module_path: str = Field(
        ..., description="Optional module path where the function is defined."
    )


class AWSSecretManager(SecretManager):
    """Configuration for AWS Secrets Manager."""

    type: Literal["aws_secret_manager"] = Field("aws_secret_manager")


class Aggregate(Step):
    """
    A terminal step that consumes an entire input stream and produces a single
    summary message with success/error counts.
    """

    type: Literal["Aggregate"] = Field("Aggregate")
    cardinality: Literal[StepCardinality.one] = Field(StepCardinality.one)
    outputs: list[Variable] = Field(
        default_factory=list,
        description="References to the variables for the output. There should be one and only one output with type AggregateStats",
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


class DocToTextConverter(Step, ConcurrentStepMixin):
    """Defines a step to convert raw documents (e.g., PDF, DOCX) loaded by a DocumentSource into plain text
    using an external tool like Docling or LlamaParse for pre-processing before chunking.
    The input and output are both RAGDocument, but the output after processing with have content of type markdown.
    """

    type: Literal["DocToTextConverter"] = Field("DocToTextConverter")


class DocumentEmbedder(Step, ConcurrentStepMixin):
    """Embeds document chunks using a specified embedding model."""

    type: Literal["DocumentEmbedder"] = Field("DocumentEmbedder")
    cardinality: Literal[StepCardinality.many] = Field(
        StepCardinality.many,
        description="Consumes one chunk and emits one embedded chunk.",
    )
    model: EmbeddingModel = Field(
        ..., description="Embedding model to use for vectorization."
    )


class DocumentSplitter(Step, ConcurrentStepMixin):
    """Configuration for chunking/splitting documents into embeddable nodes/chunks."""

    type: Literal["DocumentSplitter"] = Field("DocumentSplitter")
    cardinality: Literal[StepCardinality.many] = Field(
        StepCardinality.many,
        description="Consumes one document and emits 0...N nodes/chunks.",
    )
    splitter_name: str = Field(
        "SentenceSplitter",
        description="Name of the LlamaIndex TextSplitter class.",
    )
    chunk_size: int = Field(1024, description="Size of each chunk.")
    chunk_overlap: int = Field(
        20, description="Overlap between consecutive chunks."
    )
    args: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional arguments specific to the chosen splitter class.",
    )


class Echo(Step):
    """Defines a step that echoes its inputs as outputs.

    Useful for debugging flows by inspecting variable values at a specific
    point in the execution pipeline. The step simply passes through all input
    variables as outputs without modification.
    """

    type: Literal["Echo"] = Field("Echo")


class FieldExtractor(Step):
    """Extracts specific fields from input data using JSONPath expressions.

    This step uses JSONPath syntax to extract data from structured inputs
    (Pydantic models, dicts, lists). The input is first converted to a dict
    using model_dump() if it's a Pydantic model, then the JSONPath expression
    is evaluated.

    If the JSONPath matches multiple values, the step yields multiple output
    messages (1-to-many cardinality). If it matches a single value, it yields
    one output message. If it matches nothing, it raises an error.

    The extracted data is used to construct the output variable by passing it
    as keyword arguments to the output type's constructor.

    Example JSONPath expressions:
    - `$.field_name` - Extract a single field
    - `$.items[*]` - Extract all items from a list
    - `$.items[?(@.price > 10)]` - Filter items by condition
    """

    type: Literal["FieldExtractor"] = Field("FieldExtractor")
    json_path: str = Field(
        ...,
        description="JSONPath expression to extract data from the input. Uses jsonpath-ng syntax.",
    )


class InvokeEmbedding(Step, ConcurrentStepMixin):
    """Defines a step that generates embeddings using an embedding model.
    It takes input variables and produces output variables containing the embeddings."""

    type: Literal["InvokeEmbedding"] = Field("InvokeEmbedding")
    model: EmbeddingModel = Field(
        ..., description="The embedding model to use."
    )


class InvokeFlow(Step):
    """Invokes a flow with input and output bindings."""

    type: Literal["InvokeFlow"] = Field("InvokeFlow")
    flow: Flow = Field(..., description="Flow to invoke.")
    input_bindings: dict[Variable, str] = Field(
        ...,
        description="Mapping from variable references to flow input variable IDs.",
    )
    output_bindings: dict[Variable, str] = Field(
        ...,
        description="Mapping from variable references to flow output variable IDs.",
    )


class InvokeTool(Step, ConcurrentStepMixin):
    """Invokes a tool with input and output bindings."""

    type: Literal["InvokeTool"] = Field("InvokeTool")
    tool: Tool = Field(..., description="Tool to invoke.")
    input_bindings: dict[str, str] = Field(
        ...,
        description="Mapping from variable references to tool input parameter names.",
    )
    output_bindings: dict[str, str] = Field(
        ...,
        description="Mapping from variable references to tool output parameter names.",
    )


class LLMInference(Step, ConcurrentStepMixin):
    """Defines a step that performs inference using a language model.
    It can take input variables and produce output variables based on the model's response."""

    type: Literal["LLMInference"] = Field("LLMInference")
    memory: Memory | None = Field(
        None,
        description="A reference to a Memory object to retain context across interactions.",
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
        default_factory=dict,
        description="Optional filters to apply during search.",
    )
    index: Index = Field(
        ..., description="Index to search against (object or ID reference)."
    )


class Source(Step):
    """Base class for data sources"""

    id: str = Field(..., description="Unique ID of the data source.")
    cardinality: Literal[StepCardinality.many] = Field(
        StepCardinality.many,
        description="Sources always emit 0...N instances of the outputs.",
    )


class Writer(Step, BatchableStepMixin):
    """Base class for things that write data in batches."""

    id: str = Field(..., description="Unique ID of the data writer.")


class DocumentIndex(Index):
    """Document search index for text-based search (e.g., Elasticsearch, OpenSearch)."""

    type: Literal["DocumentIndex"] = Field("DocumentIndex")
    endpoint: str = Field(
        ...,
        description="URL endpoint for the search cluster (e.g., https://my-cluster.es.amazonaws.com).",
    )


class VectorIndex(Index):
    """Vector database index for similarity search using embeddings."""

    type: Literal["VectorIndex"] = Field("VectorIndex")
    module: str = Field(
        ...,
        description="Python module path for the vector store implementation (e.g., 'llama_index.vector_stores.qdrant.QdrantVectorStore').",
    )
    embedding_model: EmbeddingModel = Field(
        ...,
        description="Embedding model used to vectorize queries and documents.",
    )


class EmbeddingModel(Model):
    """Describes an embedding model configuration, extending the base Model class."""

    type: Literal["EmbeddingModel"] = Field("EmbeddingModel")
    dimensions: int = Field(
        ...,
        description="Dimensionality of the embedding vectors produced by this model.",
    )


class Agent(LLMInference):
    """Defines an agent that can perform tasks and make decisions based on user input and context."""

    type: Literal["Agent"] = Field("Agent")
    tools: list[Tool] = Field(
        default_factory=list,
        description="List of tools available to the agent.",
    )


class DocumentSearch(Search, ConcurrentStepMixin):
    """Performs document search against a document index."""

    type: Literal["DocumentSearch"] = Field("DocumentSearch")


class VectorSearch(Search, BatchableStepMixin):
    """Performs vector similarity search against a vector index."""

    type: Literal["VectorSearch"] = Field("VectorSearch")
    default_top_k: int | None = Field(
        50,
        description="Number of top results to retrieve if not provided in the inputs.",
    )


class DocumentSource(Source):
    """A source of documents that will be used in retrieval augmented generation.
    It uses LlamaIndex readers to load one or more raw Documents
    from a specified path or system (e.g., Google Drive, web page).
    See https://github.com/run-llama/llama_index/tree/main/llama-index-integrations/readers
    """

    type: Literal["DocumentSource"] = Field("DocumentSource")
    reader_module: str = Field(
        ..., description="Module path of the LlamaIndex Reader)."
    )
    args: dict[str, Any] = Field(
        default_factory=dict,
        description="Reader-specific arguments to pass to the Reader constructor.",
    )
    loader_args: dict[str, Any] = Field(
        default_factory=dict,
        description="Loader-specific arguments to pass to the load_data method.",
    )
    auth: AuthorizationProvider | None = Field(
        None, description="AuthorizationProvider for accessing the source."
    )


class FileSource(Source):
    """File source that reads data from a file using fsspec-compatible URIs."""

    type: Literal["FileSource"] = Field("FileSource")
    path: ConstantPath | Variable = Field(
        ...,
        description="Reference to a variable with an fsspec-compatible URI to read from, or the uri itself.",
    )


class SQLSource(Source):
    """SQL database source that executes queries and emits rows."""

    type: Literal["SQLSource"] = Field("SQLSource")
    query: str = Field(
        ..., description="SQL query to execute. Inputs are injected as params."
    )
    connection: str | SecretReference = Field(
        ...,
        description="Database connection string or reference to auth provider. Typically in SQLAlchemy format.",
    )
    auth: AuthorizationProvider | None = Field(
        None,
        description="Optional AuthorizationProvider for database authentication.",
    )


class FileWriter(Writer, BatchableStepMixin):
    """File writer that writes data to a file using fsspec-compatible URIs."""

    type: Literal["FileWriter"] = Field("FileWriter")
    path: ConstantPath | Variable = Field(
        ...,
        description="Reference to a variable with an fsspec-compatible URI to read from, or the uri itself.",
    )
    batch_config: BatchConfig = Field(
        default_factory=partial(BatchConfig, batch_size=9223372036854775807),
        description="Configuration for processing the input stream in batches. If omitted, the step processes items one by one.",
    )


class IndexUpsert(Writer):
    """Semantic version of IndexUpsert."""

    type: Literal["IndexUpsert"] = Field("IndexUpsert")
    index: Index = Field(
        ..., description="Index to upsert into (object or ID reference)."
    )


DocumentType = Union[
    Application,
    AuthorizationProviderList,
    ModelList,
    ToolList,
    TypeList,
    VariableList,
]
