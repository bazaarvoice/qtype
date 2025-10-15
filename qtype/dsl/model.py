from __future__ import annotations

import inspect
from abc import ABC
from enum import Enum
from typing import Annotated, Any, Literal, Type, Union

from pydantic import (
    BaseModel,
    Field,
    RootModel,
    ValidationInfo,
    model_validator,
)

import qtype.dsl.domain_types as domain_types
from qtype.base.types import (
    PrimitiveTypeEnum,
    Reference,
    StepCardinality,
    StrictBaseModel,
)
from qtype.dsl.domain_types import (
    ChatContent,
    ChatMessage,
    Embedding,
    RAGChunk,
    RAGDocument,
)

DOMAIN_CLASSES = {
    name: obj
    for name, obj in inspect.getmembers(domain_types)
    if inspect.isclass(obj) and obj.__module__ == domain_types.__name__
}


def _resolve_variable_type(
    parsed_type: Any, custom_type_registry: dict[str, Type[BaseModel]]
) -> Any:
    """Resolve a type string to its corresponding PrimitiveTypeEnum or return as is."""
    # If the type is already resolved or is a structured definition, pass it through.
    if not isinstance(parsed_type, str):
        return parsed_type

    # --- Case 1: The type is a string ---
    # Check if it's a list type (e.g., "list[text]")
    if parsed_type.startswith("list[") and parsed_type.endswith("]"):
        # Extract the element type from "list[element_type]"
        element_type_str = parsed_type[5:-1]  # Remove "list[" and "]"

        # Recursively resolve the element type
        element_type = _resolve_variable_type(
            element_type_str, custom_type_registry
        )

        # Allow both primitive types and custom types (but no nested lists)
        if isinstance(element_type, PrimitiveTypeEnum):
            return ListType(element_type=element_type)
        elif isinstance(element_type, str):
            # This is a custom type reference - store as string for later resolution
            return ListType(element_type=element_type)
        elif element_type in DOMAIN_CLASSES.values():
            # Domain class - store its name as string reference
            for name, cls in DOMAIN_CLASSES.items():
                if cls == element_type:
                    return ListType(element_type=name)
            return ListType(element_type=str(element_type))
        else:
            raise ValueError(
                f"List element type must be a primitive type or custom type reference, got: {element_type}"
            )

    # Try to resolve it as a primitive type first.
    try:
        return PrimitiveTypeEnum(parsed_type)
    except ValueError:
        pass  # Not a primitive, continue to the next check.

    # Try to resolve it as a built-in Domain Entity class.
    # (Assuming domain_types and inspect are defined elsewhere)
    if parsed_type in DOMAIN_CLASSES:
        return DOMAIN_CLASSES[parsed_type]

    # Check the registry of dynamically created custom types
    if parsed_type in custom_type_registry:
        return custom_type_registry[parsed_type]

    # If it's not a primitive or a known domain entity, return it as a string.
    # This assumes it might be another custom type.
    return parsed_type


class Variable(StrictBaseModel):
    """Schema for a variable that can serve as input, output, or parameter within the DSL."""

    id: str = Field(
        ...,
        description="Unique ID of the variable. Referenced in prompts or steps.",
    )
    type: VariableType | str = Field(
        ...,
        description=(
            "Type of data expected or produced. Either a CustomType or domain specific type."
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def resolve_type(cls, data: Any, info: ValidationInfo) -> Any:
        """
        This validator runs during the main validation pass. It uses the
        context to resolve string-based type references.
        """
        if (
            isinstance(data, dict)
            and "type" in data
            and isinstance(data["type"], str)
        ):
            # Get the registry of custom types from the validation context.
            custom_types = (info.context or {}).get("custom_types", {})
            resolved = _resolve_variable_type(data["type"], custom_types)
            # {'id': 'user_message', 'type': 'ChatMessage'}
            data["type"] = resolved
        return data


class CustomType(StrictBaseModel):
    """A simple declaration of a custom data type by the user."""

    id: str
    description: str | None = None
    properties: dict[str, str]


class ToolParameter(BaseModel):
    """Defines a tool input or output parameter with type and optional flag."""

    type: VariableType | str
    optional: bool = Field(
        default=False, description="Whether this parameter is optional"
    )

    @model_validator(mode="before")
    @classmethod
    def resolve_type(cls, data: Any, info: ValidationInfo) -> Any:
        """
        This validator runs during the main validation pass. It uses the
        context to resolve string-based type references.
        """
        if (
            isinstance(data, dict)
            and "type" in data
            and isinstance(data["type"], str)
        ):
            # Get the registry of custom types from the validation context.
            custom_types = (info.context or {}).get("custom_types", {})
            resolved = _resolve_variable_type(data["type"], custom_types)
            data["type"] = resolved
        return data


class ListType(BaseModel):
    """Represents a list type with a specific element type."""

    element_type: PrimitiveTypeEnum | str = Field(
        ...,
        description="Type of elements in the list (primitive type or custom type reference)",
    )

    def __str__(self) -> str:
        """String representation for list type."""
        if isinstance(self.element_type, PrimitiveTypeEnum):
            return f"list[{self.element_type.value}]"
        else:
            return f"list[{self.element_type}]"


VariableType = (
    PrimitiveTypeEnum
    | Type[Embedding]
    | Type[ChatMessage]
    | Type[ChatContent]
    | Type[BaseModel]
    | Type[RAGDocument]
    | Type[RAGChunk]
    | ListType
)


class Model(StrictBaseModel):
    """Describes a generative model configuration, including provider and model ID."""

    type: Literal["Model"] = "Model"
    id: str = Field(..., description="Unique ID for the model.")
    auth: Reference[AuthProviderType] | str | None = Field(
        default=None,
        description="AuthorizationProvider used for model access.",
    )
    inference_params: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional inference parameters like temperature or max_tokens.",
    )
    model_id: str | None = Field(
        default=None,
        description="The specific model name or ID for the provider. If None, id is used",
    )
    # TODO(maybe): Make this an enum?
    provider: str = Field(
        ..., description="Name of the provider, e.g., openai or anthropic."
    )


class EmbeddingModel(Model):
    """Describes an embedding model configuration, extending the base Model class."""

    type: Literal["EmbeddingModel"] = "EmbeddingModel"
    dimensions: int = Field(
        ...,
        description="Dimensionality of the embedding vectors produced by this model.",
    )


class Memory(StrictBaseModel):
    """Session or persistent memory used to store relevant conversation or state data across steps or turns."""

    id: str = Field(..., description="Unique ID of the memory block.")

    token_limit: int = Field(
        default=100000,
        description="Maximum number of tokens to store in memory.",
    )
    chat_history_token_ratio: float = Field(
        default=0.7,
        description="Ratio of chat history tokens to total memory tokens.",
    )
    token_flush_size: int = Field(
        default=3000,
        description="Size of memory to flush when it exceeds the token limit.",
    )
    # TODO: Add support for vectorstores and sql chat stores


#
# ---------------- Core Steps and Flow Components ----------------
#


class Step(StrictBaseModel, ABC):
    """Base class for components that take inputs and produce outputs."""

    id: str = Field(..., description="Unique ID of this component.")
    type: str = Field(..., description="Type of the step component.")
    cardinality: StepCardinality = Field(
        default=StepCardinality.one,
        description="Does this step emit 1 (one) or 0...N (many) instances of the outputs?",
    )
    inputs: list[Reference[Variable] | str] = Field(
        default_factory=list,
        description="References to the variables required by this step.",
    )
    outputs: list[Reference[Variable] | str] = Field(
        default_factory=list,
        description="References to the variables where output is stored.",
    )


class PromptTemplate(Step):
    """Defines a prompt template with a string format and variable bindings.
    This is used to generate prompts dynamically based on input variables."""

    type: Literal["PromptTemplate"] = "PromptTemplate"
    template: str = Field(
        ...,
        description="String template for the prompt with variable placeholders.",
    )


class Tool(StrictBaseModel, ABC):
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


class PythonFunctionTool(Tool):
    """Tool that calls a Python function."""

    type: Literal["PythonFunctionTool"] = "PythonFunctionTool"
    function_name: str = Field(
        ..., description="Name of the Python function to call."
    )
    module_path: str = Field(
        ...,
        description="Optional module path where the function is defined.",
    )


class APITool(Tool):
    """Tool that invokes an API endpoint."""

    type: Literal["APITool"] = "APITool"
    endpoint: str = Field(..., description="API endpoint URL to call.")
    method: str = Field(
        default="GET",
        description="HTTP method to use (GET, POST, PUT, DELETE, etc.).",
    )
    auth: Reference[AuthProviderType] | str | None = Field(
        default=None,
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


class LLMInference(Step):
    """Defines a step that performs inference using a language model.
    It can take input variables and produce output variables based on the model's response."""

    type: Literal["LLMInference"] = "LLMInference"
    memory: Reference[Memory] | str | None = Field(
        default=None,
        description="A reference to a Memory object to retain context across interactions.",
    )
    model: Reference[ModelType] | str = Field(
        ..., description="The model to use for inference."
    )
    system_message: str | None = Field(
        default=None,
        description="Optional system message to set the context for the model.",
    )


class Agent(LLMInference):
    """Defines an agent that can perform tasks and make decisions based on user input and context."""

    type: Literal["Agent"] = "Agent"

    tools: list[Reference[ToolType] | str] = Field(
        default_factory=list,
        description="List of tools available to the agent.",
    )


class Flow(StrictBaseModel):
    """Defines a flow of steps that can be executed in sequence or parallel.
    If input or output variables are not specified, they are inferred from
    the first and last step, respectively."""

    id: str = Field(..., description="Unique ID of the flow.")
    type: Literal["Flow"] = "Flow"
    description: str | None = Field(
        default=None, description="Optional description of the flow."
    )
    steps: list[StepType | Reference[StepType]] = Field(
        default_factory=list,
        description="List of steps or references to steps",
    )

    interface: FlowInterface | None = Field(default=None)
    inputs: list[Variable] = Field(
        default_factory=list,
        description="Input variables required by this step.",
    )
    outputs: list[Variable] = Field(
        default_factory=list, description="Resulting variables"
    )


class FlowInterface(StrictBaseModel):
    """
    Defines the public-facing contract for a Flow, guiding the UI
    and session management.
    """

    # 1. Tells the UI how to render this flow
    type: Literal["Complete", "Conversational"] = "Complete"

    # 2. Declares which inputs are "sticky" and persisted in the session
    session_inputs: list[Reference[Variable] | str] = Field(
        default_factory=list,
        description="A list of input variable IDs that are set once and then persisted across a session.",
    )


class DecoderFormat(str, Enum):
    """Defines the format in which the decoder step processes data."""

    json = "json"
    xml = "xml"


class Decoder(Step):
    """Defines a step that decodes string data into structured outputs.

    If parsing fails, the step will raise an error and halt execution.
    Use conditional logic in your flow to handle potential parsing errors."""

    type: Literal["Decoder"] = "Decoder"

    format: DecoderFormat = Field(
        DecoderFormat.json,
        description="Format in which the decoder processes data. Defaults to JSON.",
    )


class InvokeTool(Step):
    """Invokes a tool with input and output bindings."""

    type: Literal["InvokeTool"] = "InvokeTool"

    tool: Reference[ToolType] | str = Field(
        ...,
        description="Tool to invoke.",
    )
    input_bindings: dict[str, str] = Field(
        ...,
        description="Mapping from variable references to tool input parameter names.",
    )
    output_bindings: dict[str, str] = Field(
        ...,
        description="Mapping from variable references to tool output parameter names.",
    )


class InvokeFlow(Step):
    """Invokes a flow with input and output bindings."""

    type: Literal["InvokeFlow"] = "InvokeFlow"

    flow: Reference[Flow] | str = Field(
        ...,
        description="Flow to invoke.",
    )
    input_bindings: dict[str, str] = Field(
        ...,
        description="Mapping from variable references to flow input variable IDs.",
    )
    output_bindings: dict[str, str] = Field(
        ...,
        description="Mapping from variable references to flow output variable IDs.",
    )


#
# ---------------- Observability and Authentication Components ----------------
#


class AuthorizationProvider(StrictBaseModel, ABC):
    """Base class for authentication providers."""

    id: str = Field(
        ..., description="Unique ID of the authorization configuration."
    )
    type: str = Field(..., description="Authorization method type.")


class APIKeyAuthProvider(AuthorizationProvider):
    """API key-based authentication provider."""

    type: Literal["api_key"] = "api_key"
    api_key: str = Field(..., description="API key for authentication.")
    host: str | None = Field(
        default=None, description="Base URL or domain of the provider."
    )


class BearerTokenAuthProvider(AuthorizationProvider):
    """Bearer token authentication provider."""

    type: Literal["bearer_token"] = "bearer_token"
    token: str = Field(..., description="Bearer token for authentication.")


class OAuth2AuthProvider(AuthorizationProvider):
    """OAuth2 authentication provider."""

    type: Literal["oauth2"] = "oauth2"
    client_id: str = Field(..., description="OAuth2 client ID.")
    client_secret: str = Field(..., description="OAuth2 client secret.")
    token_url: str = Field(..., description="Token endpoint URL.")
    scopes: list[str] = Field(
        default_factory=list, description="OAuth2 scopes required."
    )


class AWSAuthProvider(AuthorizationProvider):
    """AWS authentication provider supporting multiple credential methods."""

    type: Literal["aws"] = "aws"

    # Method 1: Access key/secret/session
    access_key_id: str | None = Field(
        default=None, description="AWS access key ID."
    )
    secret_access_key: str | None = Field(
        default=None, description="AWS secret access key."
    )
    session_token: str | None = Field(
        default=None,
        description="AWS session token for temporary credentials.",
    )

    # Method 2: Profile
    profile_name: str | None = Field(
        default=None, description="AWS profile name from credentials file."
    )

    # Method 3: Role assumption
    role_arn: str | None = Field(
        default=None, description="ARN of the role to assume."
    )
    role_session_name: str | None = Field(
        default=None, description="Session name for role assumption."
    )
    external_id: str | None = Field(
        default=None, description="External ID for role assumption."
    )

    # Common AWS settings
    region: str | None = Field(default=None, description="AWS region.")

    @model_validator(mode="after")
    def validate_aws_auth(self) -> AWSAuthProvider:
        """Validate AWS authentication configuration."""
        # At least one auth method must be specified
        has_keys = self.access_key_id and self.secret_access_key
        has_profile = self.profile_name
        has_role = self.role_arn

        if not (has_keys or has_profile or has_role):
            raise ValueError(
                "AWSAuthProvider must specify at least one authentication method: "
                "access keys, profile name, or role ARN."
            )

        # If assuming a role, need either keys or profile for base credentials
        if has_role and not (has_keys or has_profile):
            raise ValueError(
                "Role assumption requires base credentials (access keys or profile)."
            )

        return self


class TelemetrySink(StrictBaseModel):
    """Defines an observability endpoint for collecting telemetry data from the QType runtime."""

    id: str = Field(
        ..., description="Unique ID of the telemetry sink configuration."
    )
    auth: Reference[AuthorizationProvider] | str | None = Field(
        default=None,
        description="AuthorizationProvider used to authenticate telemetry data transmission.",
    )
    endpoint: str = Field(
        ..., description="URL endpoint where telemetry data will be sent."
    )


#
# ---------------- Application Definition ----------------
#


class Application(StrictBaseModel):
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
        default=None, description="Optional description of the application."
    )

    # Core components
    memories: list[Memory] = Field(
        default_factory=list,
        description="List of memory definitions used in this application.",
    )
    models: list[ModelType] = Field(
        default_factory=list,
        description="List of models used in this application.",
    )
    types: list[CustomType] = Field(
        default_factory=list,
        description="List of custom types defined in this application.",
    )
    variables: list[Variable] = Field(
        default_factory=list,
        description="List of variables available at the application scope.",
    )

    # Orchestration
    flows: list[Flow] = Field(
        default_factory=list,
        description="List of flows defined in this application.",
    )

    # External integrations
    auths: list[AuthProviderType] = Field(
        default_factory=list,
        description="List of authorization providers used for API access.",
    )
    tools: list[ToolType] = Field(
        default_factory=list,
        description="List of tools available in this application.",
    )
    indexes: list[IndexType] = Field(
        default_factory=list,
        description="List of indexes available for search operations.",
    )

    # Observability
    telemetry: TelemetrySink | None = Field(
        default=None, description="Optional telemetry sink for observability."
    )

    # Extensibility
    references: list[Document] = Field(
        default_factory=list,
        description="List of other q-type documents you may use. This allows modular composition and reuse of components across applications.",
    )


#
# ---------------- Data Pipeline Components ----------------
#


class ConstantPath(StrictBaseModel):
    uri: str = Field(..., description="A constant Fsspec URI.")


# Let's the user use a constant path or reference a variable
PathType = ConstantPath | Reference[Variable] | str


class Source(Step):
    """Base class for data sources"""

    id: str = Field(..., description="Unique ID of the data source.")
    cardinality: Literal[StepCardinality.many] = Field(
        default=StepCardinality.many,
        description="Sources always emit 0...N instances of the outputs.",
    )


class SQLSource(Source):
    """SQL database source that executes queries and emits rows."""

    type: Literal["SQLSource"] = "SQLSource"
    query: str = Field(
        ..., description="SQL query to execute. Inputs are injected as params."
    )
    connection: str = Field(
        ...,
        description="Database connection string or reference to auth provider. Typically in SQLAlchemy format.",
    )
    auth: Reference[AuthProviderType] | str | None = Field(
        default=None,
        description="Optional AuthorizationProvider for database authentication.",
    )


class FileSource(Source):
    """File source that reads data from a file using fsspec-compatible URIs."""

    type: Literal["FileSource"] = "FileSource"
    path: PathType = Field(
        default=...,
        description="Reference to a variable with an fsspec-compatible URI to read from, or the uri itself.",
    )


class Sink(Step):
    """Base class for data sinks"""

    id: str = Field(..., description="Unique ID of the data sink.")
    cardinality: Literal[StepCardinality.one] = Field(
        default=StepCardinality.one,
        description="Flows always emit exactly one instance of the outputs.",
    )


class FileSink(Sink):
    """File sink that writes data to a file using fsspec-compatible URIs."""

    type: Literal["FileSink"] = "FileSink"
    path: PathType = Field(
        default=...,
        description="Reference to a variable with an fsspec-compatible URI to read from, or the uri itself.",
    )


#
# ---------------- Retrieval Augmented Generation Components ----------------
#


class DocumentSource(Source):
    """A source of documents that will be used in retrieval augmented generation.
    It uses LlamaIndex readers to load one or more raw Documents
    from a specified path or system (e.g., Google Drive, web page).
    See https://github.com/run-llama/llama_index/tree/main/llama-index-integrations/readers
    """

    type: Literal["DocumentSource"] = "DocumentSource"
    cardinality: Literal[StepCardinality.many] = Field(
        default=StepCardinality.many,
        description="A DocumentSource always emits 0...N instances of documents.",
    )

    reader_module: str = Field(
        ...,
        description="Module path of the LlamaIndex Reader without 'llama_index.readers' (e.g., 'google.GoogleDriveReader', 'file.IPYNBReader').",
    )
    args: dict[str, Any] = Field(
        default_factory=dict,
        description="Reader-specific arguments to pass to the LlamaIndex constructor.",
    )
    auth: Reference[AuthProviderType] | str | None = Field(
        default=None,
        description="AuthorizationProvider for accessing the source.",
    )


class DocToTextConverter(Step):
    """Defines a step to convert raw documents (e.g., PDF, DOCX) loaded by a DocumentSource into plain text
    using an external tool like Docling or LlamaParse for pre-processing before chunking.
    The input and output are both RAGDocument, but the output after processing with have content of type markdown.
    """

    type: Literal["DocToTextConverter"] = "DocToTextConverter"
    cardinality: Literal[StepCardinality.one] = Field(
        default=StepCardinality.one,
        description="Consumes one document and produces one processed text output.",
    )


class DocumentSplitter(Step):
    """Configuration for chunking/splitting documents into embeddable nodes/chunks."""

    type: Literal["DocumentSplitter"] = "DocumentSplitter"
    cardinality: Literal[StepCardinality.many] = Field(
        default=StepCardinality.many,
        description="Consumes one document and emits 0...N nodes/chunks.",
    )

    splitter_name: str = Field(
        default="SentenceSplitter",
        description="Name of the LlamaIndex TextSplitter class.",
    )
    chunk_size: int = Field(default=1024, description="Size of each chunk.")
    chunk_overlap: int = Field(
        default=20, description="Overlap between consecutive chunks."
    )
    args: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional arguments specific to the chosen splitter class.",
    )


class DocumentEmbedder(Step):
    """Embeds document chunks using a specified embedding model."""

    type: Literal["DocumentEmbedder"] = "DocumentEmbedder"
    cardinality: Literal[StepCardinality.many] = Field(
        default=StepCardinality.many,
        description="Consumes one chunk and emits one embedded chunk.",
    )
    model: Reference[EmbeddingModel] | str = Field(
        ..., description="Embedding model to use for vectorization."
    )


class Index(StrictBaseModel, ABC):
    """Base class for searchable indexes that can be queried by search steps."""

    id: str = Field(..., description="Unique ID of the index.")
    args: dict[str, Any] = Field(
        default_factory=dict,
        description="Index-specific configuration and connection parameters.",
    )
    auth: Reference[AuthProviderType] | str | None = Field(
        default=None,
        description="AuthorizationProvider for accessing the index.",
    )
    name: str = Field(..., description="Name of the index/collection/table.")


class IndexUpsert(Sink):
    type: Literal["IndexUpsert"] = "IndexUpsert"
    index: Reference[IndexType] | str = Field(
        ..., description="Index to upsert into (object or ID reference)."
    )


class VectorIndex(Index):
    """Vector database index for similarity search using embeddings."""

    type: Literal["VectorIndex"] = "VectorIndex"
    embedding_model: Reference[EmbeddingModel] | str = Field(
        ...,
        description="Embedding model used to vectorize queries and documents.",
    )


class DocumentIndex(Index):
    """Document search index for text-based search (e.g., Elasticsearch, OpenSearch)."""

    type: Literal["DocumentIndex"] = "DocumentIndex"
    # TODO: add anything that is needed for document search indexes
    pass


class Search(Step, ABC):
    """Base class for search operations against indexes."""

    filters: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional filters to apply during search.",
    )
    index: Reference[IndexType] | str = Field(
        ..., description="Index to search against (object or ID reference)."
    )


class VectorSearch(Search):
    """Performs vector similarity search against a vector index."""

    type: Literal["VectorSearch"] = "VectorSearch"
    default_top_k: int | None = Field(
        default=50,
        description="Number of top results to retrieve if not provided in the inputs.",
    )


class DocumentSearch(Search):
    """Performs document search against a document index."""

    type: Literal["DocumentSearch"] = "DocumentSearch"


# Create a union type for all tool types
ToolType = Annotated[
    Union[
        APITool,
        PythonFunctionTool,
    ],
    Field(discriminator="type"),
]

# Create a union type for all source types
SourceType = Union[
    DocumentSource,
    FileSource,
    SQLSource,
]

# Create a union type for all authorization provider types
AuthProviderType = Union[
    APIKeyAuthProvider,
    BearerTokenAuthProvider,
    AWSAuthProvider,
    OAuth2AuthProvider,
]

# Create a union type for all step types
StepType = Annotated[
    Union[
        Agent,
        Decoder,
        DocToTextConverter,
        DocumentEmbedder,
        DocumentSearch,
        DocumentSplitter,
        DocumentSource,
        FileSink,
        FileSource,
        Flow,
        IndexUpsert,
        InvokeFlow,
        InvokeTool,
        LLMInference,
        PromptTemplate,
        SQLSource,
        VectorSearch,
    ],
    Field(discriminator="type"),
]

# Create a union type for all index types
IndexType = Annotated[
    Union[
        DocumentIndex,
        VectorIndex,
    ],
    Field(discriminator="type"),
]

# Create a union type for all model types
ModelType = Annotated[
    Union[
        EmbeddingModel,
        Model,
    ],
    Field(discriminator="type"),
]

#
# ---------------- Document Flexibility Shapes ----------------
# The following shapes let users define a set of flexible document structures
#


class AuthorizationProviderList(RootModel[list[AuthProviderType]]):
    """Schema for a standalone list of authorization providers."""

    root: list[AuthProviderType]


class IndexList(RootModel[list[IndexType]]):
    """Schema for a standalone list of indexes."""

    root: list[IndexType]


class ModelList(RootModel[list[ModelType]]):
    """Schema for a standalone list of models."""

    root: list[ModelType]


class ToolList(RootModel[list[ToolType]]):
    """Schema for a standalone list of tools."""

    root: list[ToolType]


class TypeList(RootModel[list[CustomType]]):
    """Schema for a standalone list of type definitions."""

    root: list[CustomType]


class VariableList(RootModel[list[Variable]]):
    """Schema for a standalone list of variables."""

    root: list[Variable]


DocumentType = Union[
    Agent,
    Application,
    AuthorizationProviderList,
    Flow,
    IndexList,
    ModelList,
    ToolList,
    TypeList,
    VariableList,
]


class Document(RootModel[DocumentType]):
    """Schema for any valid QType document structure.

    This allows validation of standalone lists of components, individual components,
    or full QType application specs. Supports modular composition and reuse.
    """

    root: DocumentType
