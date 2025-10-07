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
from qtype.dsl.base_types import (
    PrimitiveTypeEnum,
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


class StructuralTypeEnum(str, Enum):
    """Represents a structured type that can be used in the DSL."""

    object = "object"
    array = "array"


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
    # This assumes it might be a reference ID to another custom type.
    return parsed_type


class Variable(BaseModel):
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

    id: str = Field(..., description="Unique ID for the model.")
    auth: AuthProviderType | str | None = Field(
        default=None,
        description="AuthorizationProvider used for model access.",
    )
    inference_params: dict[str, Any] | None = Field(
        default=None,
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
    inputs: list[Variable | str] | None = Field(
        default=None,
        description="Input variables required by this step.",
    )
    outputs: list[Variable | str] | None = Field(
        default=None, description="Variable where output is stored."
    )


class PromptTemplate(Step):
    """Defines a prompt template with a string format and variable bindings.
    This is used to generate prompts dynamically based on input variables."""

    type: Literal["PromptTemplate"] = "PromptTemplate"
    template: str = Field(
        ...,
        description="String template for the prompt with variable placeholders.",
    )

    @model_validator(mode="after")
    def set_default_outputs(self) -> "PromptTemplate":
        """Set default output variable if none provided."""
        if self.outputs is None:
            self.outputs = [
                Variable(id=f"{self.id}.prompt", type=PrimitiveTypeEnum.text)
            ]
        if len(self.outputs) != 1:
            raise ValueError(
                "PromptTemplate steps must have exactly one output variable -- the result of applying the template."
            )
        return self


class Condition(Step):
    """Conditional logic gate within a flow. Supports branching logic for execution based on variable values."""

    type: Literal["Condition"] = "Condition"
    # TODO: Add support for more complex conditions
    else_: StepType | str | None = Field(
        default=None,
        alias="else",
        description="Optional step to run if condition fails.",
    )
    equals: Variable | str | None = Field(
        default=None, description="Match condition for equality check."
    )
    then: StepType | str = Field(
        ..., description="Step to run if condition matches."
    )

    @model_validator(mode="after")
    def set_default_outputs(self) -> "Condition":
        """Set default output variable if none provided."""
        if not self.inputs or len(self.inputs) != 1:
            raise ValueError(
                "Condition steps must have exactly one input variable."
            )
        return self


class Tool(StrictBaseModel, ABC):
    """
    Base class for callable functions or external operations available to the model or as a step in a flow.
    """

    id: str = Field(..., description="Unique ID of this component.")
    name: str = Field(..., description="Name of the tool function.")
    description: str = Field(
        ..., description="Description of what the tool does."
    )
    inputs: dict[str, ToolParameter] | None = Field(
        default=None,
        description="Input parameters required by this tool.",
    )
    outputs: dict[str, ToolParameter] | None = Field(
        default=None,
        description="Output parameters produced by this tool.",
    )


class PythonFunctionTool(Tool):
    """Tool that calls a Python function."""

    function_name: str = Field(
        ..., description="Name of the Python function to call."
    )
    module_path: str = Field(
        ...,
        description="Optional module path where the function is defined.",
    )


class APITool(Tool):
    """Tool that invokes an API endpoint."""

    endpoint: str = Field(..., description="API endpoint URL to call.")
    method: str = Field(
        default="GET",
        description="HTTP method to use (GET, POST, PUT, DELETE, etc.).",
    )
    auth: AuthProviderType | str | None = Field(
        default=None,
        description="Optional AuthorizationProvider for API authentication.",
    )
    headers: dict[str, str] | None = Field(
        default=None,
        description="Optional HTTP headers to include in the request.",
    )
    parameters: dict[str, ToolParameter] | None = Field(
        default=None,
        description="Output parameters produced by this tool.",
    )


class LLMInference(Step):
    """Defines a step that performs inference using a language model.
    It can take input variables and produce output variables based on the model's response."""

    type: Literal["LLMInference"] = "LLMInference"
    memory: Memory | str | None = Field(
        default=None,
        description="Memory object to retain context across interactions.",
    )
    model: ModelType | str = Field(
        ..., description="The model to use for inference."
    )
    system_message: str | None = Field(
        default=None,
        description="Optional system message to set the context for the model.",
    )

    @model_validator(mode="after")
    def set_default_outputs(self) -> "LLMInference":
        """Set default output variable if none provided."""
        if self.outputs is None:
            self.outputs = [
                Variable(id=f"{self.id}.response", type=PrimitiveTypeEnum.text)
            ]
        return self


class Agent(LLMInference):
    """Defines an agent that can perform tasks and make decisions based on user input and context."""

    type: Literal["Agent"] = "Agent"
    """Defines an agent that can perform tasks and make decisions based on user input and context."""

    tools: list[ToolType | str] = Field(
        ..., description="List of tools available to the agent."
    )


class Flow(Step):
    """Defines a flow of steps that can be executed in sequence or parallel.
    If input or output variables are not specified, they are inferred from
    the first and last step, respectively."""

    type: Literal["Flow"] = "Flow"
    description: str | None = Field(
        default=None, description="Optional description of the flow."
    )

    cardinality: StepCardinality = Field(
        default=StepCardinality.auto,
        description="The cardinality of the flow, inferred from its steps when set to 'auto'.",
    )

    mode: Literal["Complete", "Chat"] = "Complete"

    steps: list[StepType | str] = Field(
        default_factory=list, description="List of steps or step IDs."
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

    @model_validator(mode="after")
    def set_default_outputs(self) -> "Decoder":
        """Set default output variable if none provided."""

        if (
            self.inputs is None
            or len(self.inputs) != 1
            or (
                isinstance(self.inputs[0], Variable)
                and self.inputs[0].type != PrimitiveTypeEnum.text
            )
        ):
            raise ValueError(
                f"Decoder steps must have exactly one input variable of type 'text'. Found: {self.inputs}"
            )
        if self.outputs is None:
            raise ValueError(
                "Decoder steps must have at least one output variable defined."
            )
        return self


class Invoke(Step):
    """Invokes a tool with input and output bindings."""

    type: Literal["Invoke"] = "Invoke"

    tool: ToolType | str = Field(
        ...,
        description="Tool to invoke.",
    )
    input_bindings: dict[str, str] = Field(
        ...,
        description="Mapping from step input IDs to tool input parameter names.",
    )
    output_bindings: dict[str, str] = Field(
        ...,
        description="Mapping from tool output parameter names to step output IDs.",
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
    scopes: list[str] | None = Field(
        default=None, description="OAuth2 scopes required."
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
    def validate_aws_auth(self) -> "AWSAuthProvider":
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
    auth: AuthProviderType | str | None = Field(
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
    memories: list[Memory] | None = Field(
        default=None,
        description="List of memory definitions used in this application.",
    )
    models: list[ModelType] | None = Field(
        default=None, description="List of models used in this application."
    )
    types: list[CustomType] | None = Field(
        default=None,
        description="List of custom types defined in this application.",
    )
    variables: list[Variable] | None = Field(
        default=None, description="List of variables used in this application."
    )

    # Orchestration
    flows: list[Flow] | None = Field(
        default=None, description="List of flows defined in this application."
    )

    # External integrations
    auths: list[AuthProviderType] | None = Field(
        default=None,
        description="List of authorization providers used for API access.",
    )
    tools: list[ToolType] | None = Field(
        default=None,
        description="List of tools available in this application.",
    )
    indexes: list[IndexType] | None = Field(
        default=None,
        description="List of indexes available for search operations.",
    )

    # Observability
    telemetry: TelemetrySink | None = Field(
        default=None, description="Optional telemetry sink for observability."
    )

    # Extensibility
    references: list[Document] | None = Field(
        default=None,
        description="List of other q-type documents you may use. This allows modular composition and reuse of components across applications.",
    )


#
# ---------------- Data Pipeline Components ----------------
#


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
    auth: AuthProviderType | str | None = Field(
        default=None,
        description="Optional AuthorizationProvider for database authentication.",
    )

    @model_validator(mode="after")
    def validate_sql_source(self) -> "SQLSource":
        """Validate SQL source configuration."""
        if self.outputs is None:
            raise ValueError(
                "SQLSource must define output variables that match the result columns."
            )
        return self


class FileSource(Source):
    """File source that reads data from a file using fsspec-compatible URIs."""

    type: Literal["FileSource"] = "FileSource"
    path: str | None = Field(
        default=None,
        description="fsspec-compatible URI to read from. If None, expects 'path' input variable.",
    )

    @model_validator(mode="after")
    def validate_file_source(self) -> "FileSource":
        """Validate that either path is specified or 'path' input variable exists."""
        if self.path is None:
            # Check if 'path' input variable exists
            if self.inputs is None:
                raise ValueError(
                    "FileSource must either specify 'path' field or have a 'path' input variable."
                )

            path_input_exists = any(
                (isinstance(inp, Variable) and inp.id == "path")
                or (isinstance(inp, str) and inp == "path")
                for inp in self.inputs
            )

            if not path_input_exists:
                raise ValueError(
                    "FileSource must either specify 'path' field or have a 'path' input variable."
                )

        return self


class Sink(Step):
    """Base class for data sinks"""

    id: str = Field(..., description="Unique ID of the data sink.")
    # Remove cardinality field - it's always one for sinks
    # ...existing code...
    cardinality: Literal[StepCardinality.one] = Field(
        default=StepCardinality.one,
        description="Flows always emit exactly one instance of the outputs.",
    )


class FileSink(Sink):
    """File sink that writes data to a file using fsspec-compatible URIs."""

    type: Literal["FileSink"] = "FileSink"
    path: str | None = Field(
        default=None,
        description="fsspec-compatible URI to write to. If None, expects 'path' input variable.",
    )

    @model_validator(mode="after")
    def validate_file_sink(self) -> "FileSink":
        """Validate that either path is specified or 'path' input variable exists."""
        # Ensure user does not set any output variables
        if self.outputs is not None and len(self.outputs) > 0:
            raise ValueError(
                "FileSink outputs are automatically generated. Do not specify outputs."
            )

        # Automatically set the output variable
        self.outputs = [Variable(id=f"{self.id}-file-uri", type="text")]

        if self.path is None:
            # Check if 'path' input variable exists
            if self.inputs is None:
                raise ValueError(
                    "FileSink must either specify 'path' field or have a 'path' input variable."
                )

            path_input_exists = any(
                (isinstance(inp, Variable) and inp.id == "path")
                or (isinstance(inp, str) and inp == "path")
                for inp in self.inputs
            )

            if not path_input_exists:
                raise ValueError(
                    "FileSink must either specify 'path' field or have a 'path' input variable."
                )

        return self


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
    args: dict[str, Any] | None = Field(
        default=None,
        description="Reader-specific arguments to pass to the LlamaIndex constructor.",
    )
    auth: AuthProviderType | str | None = Field(
        default=None,
        description="AuthorizationProvider for accessing the source.",
    )

    @model_validator(mode="after")
    def set_default_outputs(self) -> "DocumentSource":
        """Set default output variable."""
        if self.outputs is None or not len(self.outputs):
            # Outputting a domain object representing the raw document (metadata + text)
            self.outputs = [
                Variable(id=f"{self.id}.output_document", type=RAGDocument)
            ]

        # Ensure there is exactly one output variable and it's RAGDocument type
        if len(self.outputs) != 1 or (
            isinstance(self.outputs[0], Variable)
            and self.outputs[0].type != RAGDocument
        ):
            raise ValueError(
                "DocumentSource steps must have exactly one output variable of type 'RAGDocument'."
            )
        return self


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

    @model_validator(mode="after")
    def set_default_inputs_outputs(self) -> "DocToTextConverter":
        """Set default input/output variables."""
        if self.inputs is None or not len(self.inputs):
            self.inputs = [
                Variable(id=f"{self.id}.input_document", type=RAGDocument)
            ]
        # Ensure there is exactly one input variable and it's RAGDocument type
        if len(self.inputs) != 1 or (
            isinstance(self.inputs[0], Variable)
            and self.inputs[0].type != RAGDocument
        ):
            raise ValueError(
                "DocToTextConverter steps must have exactly one input variable of type 'RAGDocument'."
            )

        if self.outputs is None or not len(self.outputs):
            self.outputs = [
                Variable(
                    id=f"{self.id}.output_document",
                    type=RAGDocument,
                )
            ]

        # Ensure there is exactly one output variable and it's RAGDocument type
        if len(self.outputs) != 1 or (
            isinstance(self.outputs[0], Variable)
            and self.outputs[0].type != RAGDocument
        ):
            raise ValueError(
                "DocumentSource steps must have exactly one output variable of type 'RAGDocument'."
            )
        return self


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
    args: dict[str, Any] | None = Field(
        default=None,
        description="Additional arguments specific to the chosen splitter class.",
    )

    @model_validator(mode="after")
    def set_default_inputs_outputs(self) -> "DocumentSplitter":
        if not self.inputs or not len(self.inputs):
            self.inputs = [
                Variable(id=f"{self.id}.input_doc", type=RAGDocument)
            ]
        # Ensure there is exactly one input variable and it's RAGDocument type
        if len(self.inputs) != 1 or (
            isinstance(self.inputs[0], Variable)
            and self.inputs[0].type != RAGDocument
        ):
            raise ValueError(
                "DocumentSplitter steps must have exactly one input variable of type 'RAGDocument'."
            )

        if self.outputs is None or not len(self.outputs):
            # Output uses the domain-level `Embedding` type, which represents a vectorizable chunk.
            self.outputs = [
                Variable(id=f"{self.id}.output_chunk", type=RAGChunk)
            ]

        # Ensure there is exactly one output variable and it's RAGChunk type
        if len(self.outputs) != 1 or (
            isinstance(self.outputs[0], Variable)
            and self.outputs[0].type != RAGChunk
        ):
            raise ValueError(
                "DocumentSplitter steps must have exactly one output variable of type 'RAGChunk'."
            )

        return self


class Index(StrictBaseModel, ABC):
    """Base class for searchable indexes that can be queried by search steps."""

    id: str = Field(..., description="Unique ID of the index.")
    args: dict[str, Any] | None = Field(
        default=None,
        description="Index-specific configuration and connection parameters.",
    )
    auth: AuthProviderType | str | None = Field(
        default=None,
        description="AuthorizationProvider for accessing the index.",
    )
    name: str = Field(..., description="Name of the index/collection/table.")


class IndexUpsert(Sink):
    type: Literal["IndexUpsert"] = "IndexUpsert"
    index: IndexType | str = Field(
        ..., description="Index to upsert into (object or ID reference)."
    )

    @model_validator(mode="after")
    def set_default_outputs(self) -> "IndexUpsert":
        # Ensure there is only one input variable and it's either a RAGChunk (for vector indexes) or a RAGDocument (for document indexes)
        if not self.inputs or len(self.inputs) != 1:
            raise ValueError(
                "IndexUpsert must have exactly one input variable."
            )
        if isinstance(self.index, VectorIndex):
            if not (
                isinstance(self.inputs[0], Variable)
                and self.inputs[0].type == RAGChunk
            ):
                raise ValueError(
                    "IndexUpsert input variable must be of type 'RAGChunk' for vector indexes."
                )
        elif isinstance(self.index, DocumentIndex):
            if not (
                isinstance(self.inputs[0], Variable)
                and self.inputs[0].type == RAGDocument
            ):
                raise ValueError(
                    "IndexUpsert input variable must be of type 'RAGDocument' for document indexes."
                )
        return self


class VectorIndex(Index):
    """Vector database index for similarity search using embeddings."""

    embedding_model: EmbeddingModel | str = Field(
        ...,
        description="Embedding model used to vectorize queries and documents.",
    )


class DocumentIndex(Index):
    """Document search index for text-based search (e.g., Elasticsearch, OpenSearch)."""

    # TODO: add anything that is needed for document search indexes
    pass


class Search(Step, ABC):
    """Base class for search operations against indexes."""

    filters: dict[str, Any] | None = Field(
        default=None, description="Optional filters to apply during search."
    )
    index: IndexType | str = Field(
        ..., description="Index to search against (object or ID reference)."
    )


class VectorSearch(Search):
    """Performs vector similarity search against a vector index."""

    type: Literal["VectorSearch"] = "VectorSearch"
    default_top_k: int | None = Field(
        default=50,
        description="Number of top results to retrieve if not provided in the inputs.",
    )

    @model_validator(mode="after")
    def set_default_inputs_outputs(self) -> "VectorSearch":
        """Set default input and output variables if none provided."""
        if self.inputs is None:
            self.inputs = [
                Variable(id="top_k", type=PrimitiveTypeEnum.int),
                Variable(id="query", type=PrimitiveTypeEnum.text),
            ]

        if self.outputs is None:
            self.outputs = [Variable(id=f"{self.id}.results", type=Embedding)]
        return self


class DocumentSearch(Search):
    """Performs document search against a document index."""

    type: Literal["DocumentSearch"] = "DocumentSearch"

    @model_validator(mode="after")
    def set_default_inputs_outputs(self) -> "DocumentSearch":
        """Set default input and output variables if none provided."""
        if self.inputs is None:
            self.inputs = [Variable(id="query", type=PrimitiveTypeEnum.text)]

        if self.outputs is None:
            self.outputs = [
                Variable(id=f"{self.id}.results", type=PrimitiveTypeEnum.text)
            ]
        return self


# Create a union type for all tool types
ToolType = Union[
    APITool,
    PythonFunctionTool,
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
        Condition,
        Decoder,
        DocToTextConverter,
        DocumentSearch,
        DocumentSplitter,
        DocumentSource,
        FileSink,
        FileSource,
        Flow,
        IndexUpsert,
        Invoke,
        LLMInference,
        PromptTemplate,
        SQLSource,
        VectorSearch,
    ],
    Field(discriminator="type"),
]

# Create a union type for all index types
IndexType = Union[
    DocumentIndex,
    VectorIndex,
]

# Create a union type for all model types
ModelType = Union[
    EmbeddingModel,
    Model,
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
