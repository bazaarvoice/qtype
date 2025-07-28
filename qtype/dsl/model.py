from __future__ import annotations

import inspect
from abc import ABC
from enum import Enum
from typing import Any, Type, Union

from pydantic import Field, RootModel, model_validator

import qtype.dsl.domain_types as domain_types
from qtype.dsl.base_types import PrimitiveTypeEnum, StrictBaseModel
from qtype.dsl.domain_types import ChatContent, ChatMessage, Embedding


class StructuralTypeEnum(str, Enum):
    """Represents a structured type that can be used in the DSL."""

    object = "object"
    array = "array"


DOMAIN_CLASSES = {
    name: obj
    for name, obj in inspect.getmembers(domain_types)
    if inspect.isclass(obj) and obj.__module__ == domain_types.__name__
}


def _resolve_variable_type(parsed_type: Any) -> Any:
    """Resolve a type string to its corresponding PrimitiveTypeEnum or return as is."""
    # If the type is already resolved or is a structured definition, pass it through.
    if not isinstance(parsed_type, str):
        return parsed_type

    # --- Case 1: The type is a string ---
    # Try to resolve it as a primitive type first.
    try:
        return PrimitiveTypeEnum(parsed_type)
    except ValueError:
        pass  # Not a primitive, continue to the next check.

    # Try to resolve it as a built-in Domain Entity class.
    # (Assuming domain_types and inspect are defined elsewhere)
    if parsed_type in DOMAIN_CLASSES:
        return DOMAIN_CLASSES[parsed_type]

    # If it's not a primitive or a known domain entity, return it as a string.
    # This assumes it might be a reference ID to another custom type.
    return parsed_type


class Variable(StrictBaseModel):
    """Schema for a variable that can serve as input, output, or parameter within the DSL."""

    id: str = Field(
        ...,
        description="Unique ID of the variable. Referenced in prompts or steps.",
    )
    type: VariableType | str = Field(
        ...,
        description=("Type of data expected or produced."),
    )

    @model_validator(mode="before")
    @classmethod
    def resolve_type(cls, data: Any) -> Any:
        if isinstance(data, dict) and "type" in data:
            data["type"] = _resolve_variable_type(data["type"])  # type: ignore
        return data


class TypeDefinitionBase(StrictBaseModel, ABC):
    id: str = Field(description="The unique identifier for this custom type.")
    kind: StructuralTypeEnum = Field(
        ...,
        description="The kind of structure this type represents (object/array).",
    )
    description: str | None = Field(
        None, description="A description of what this type represents."
    )


class ObjectTypeDefinition(TypeDefinitionBase):
    kind: StructuralTypeEnum = StructuralTypeEnum.object
    properties: dict[str, VariableType | str] | None = Field(
        None, description="Defines the nested properties."
    )

    @model_validator(mode="after")
    def resolve_type(self) -> "ObjectTypeDefinition":
        """Resolve the type string to its corresponding PrimitiveTypeEnum."""
        # Pydantic doesn't properly handle enums as strings in model validation,
        if self.properties:
            for key, value in self.properties.items():
                if isinstance(value, str):
                    self.properties[key] = _resolve_variable_type(value)
        return self


class ArrayTypeDefinition(TypeDefinitionBase):
    kind: StructuralTypeEnum = StructuralTypeEnum.array
    type: VariableType | str = Field(
        ..., description="The type of items in the array."
    )

    @model_validator(mode="before")
    @classmethod
    def resolve_type(cls, data: Any) -> Any:
        if isinstance(data, dict) and "type" in data:
            # If the type is a string, resolve it to PrimitiveTypeEnum or Domain Entity class.
            data["type"] = _resolve_variable_type(data["type"])  # type: ignore
        return data


TypeDefinition = ObjectTypeDefinition | ArrayTypeDefinition
VariableType = (
    PrimitiveTypeEnum
    | TypeDefinition
    | Type[Embedding]
    | Type[ChatMessage]
    | Type[ChatContent]
)


class Model(StrictBaseModel):
    """Describes a generative model configuration, including provider and model ID."""

    id: str = Field(..., description="Unique ID for the model.")
    auth: AuthorizationProvider | str | None = Field(
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


class Tool(Step, ABC):
    """
    Base class for callable functions or external operations available to the model or as a step in a flow.
    """

    name: str = Field(..., description="Name of the tool function.")
    description: str = Field(
        ..., description="Description of what the tool does."
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
    auth: AuthorizationProvider | str | None = Field(
        default=None,
        description="Optional AuthorizationProvider for API authentication.",
    )
    headers: dict[str, str] | None = Field(
        default=None,
        description="Optional HTTP headers to include in the request.",
    )


class LLMInference(Step):
    """Defines a step that performs inference using a language model.
    It can take input variables and produce output variables based on the model's response."""

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

    tools: list[ToolType | str] = Field(
        ..., description="List of tools available to the agent."
    )


class Flow(Step):
    """Defines a flow of steps that can be executed in sequence or parallel.
    If input or output variables are not specified, they are inferred from
    the first and last step, respectively.
    """

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
    Use conditional logic in your flow to handle potential parsing errors.
    """

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


#
# ---------------- Observability and Authentication Components ----------------
#


class AuthorizationProvider(StrictBaseModel):
    """Defines how tools or providers authenticate with APIs, such as OAuth2 or API keys."""

    id: str = Field(
        ..., description="Unique ID of the authorization configuration."
    )
    api_key: str | None = Field(
        default=None, description="API key if using token-based auth."
    )
    client_id: str | None = Field(
        default=None, description="OAuth2 client ID."
    )
    client_secret: str | None = Field(
        default=None, description="OAuth2 client secret."
    )
    host: str | None = Field(
        default=None, description="Base URL or domain of the provider."
    )
    scopes: list[str] | None = Field(
        default=None, description="OAuth2 scopes required."
    )
    token_url: str | None = Field(
        default=None, description="Token endpoint URL."
    )
    type: str = Field(
        ..., description="Authorization method, e.g., 'oauth2' or 'api_key'."
    )


class TelemetrySink(StrictBaseModel):
    """Defines an observability endpoint for collecting telemetry data from the QType runtime."""

    id: str = Field(
        ..., description="Unique ID of the telemetry sink configuration."
    )
    auth: AuthorizationProvider | str | None = Field(
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
    """Defines a QType application that can include models, variables, and other components."""

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
    types: list[TypeDefinition] | None = Field(
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
    auths: list[AuthorizationProvider] | None = Field(
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
# ---------------- Retrieval Augmented Generation Components ----------------
#


class Index(StrictBaseModel, ABC):
    """Base class for searchable indexes that can be queried by search steps."""

    id: str = Field(..., description="Unique ID of the index.")
    args: dict[str, Any] | None = Field(
        default=None,
        description="Index-specific configuration and connection parameters.",
    )
    auth: AuthorizationProvider | str | None = Field(
        default=None,
        description="AuthorizationProvider for accessing the index.",
    )
    name: str = Field(..., description="Name of the index/collection/table.")


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

    default_top_k: int | None = Field(
        description="Number of top results to retrieve if not provided in the inputs.",
    )

    @model_validator(mode="after")
    def set_default_inputs_outputs(self) -> "VectorSearch":
        """Set default input and output variables if none provided."""
        if self.inputs is None:
            self.inputs = [
                Variable(id="top_k", type=PrimitiveTypeEnum.number),
                Variable(id="query", type=PrimitiveTypeEnum.text),
            ]

        if self.outputs is None:
            self.outputs = [
                Variable(
                    id=f"{self.id}.results",
                    type=ArrayTypeDefinition(
                        id=f"{self.id}.SearchResult",
                        type=ObjectTypeDefinition(
                            id="SearchResult",
                            description="Result of a search operation.",
                            properties={
                                "score": PrimitiveTypeEnum.number,
                                "id": PrimitiveTypeEnum.text,
                                "document": PrimitiveTypeEnum.text,
                            },
                        ),
                        description=None,
                    ),
                )
            ]
        return self


class DocumentSearch(Search):
    """Performs document search against a document index."""

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

# Create a union type for all step types
StepType = Union[
    Agent,
    APITool,
    Condition,
    Decoder,
    DocumentSearch,
    Flow,
    LLMInference,
    PromptTemplate,
    PythonFunctionTool,
    VectorSearch,
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


class AuthorizationProviderList(RootModel[list[AuthorizationProvider]]):
    """Schema for a standalone list of authorization providers."""

    root: list[AuthorizationProvider]


class IndexList(RootModel[list[IndexType]]):
    """Schema for a standalone list of indexes."""

    root: list[IndexType]


class ModelList(RootModel[list[ModelType]]):
    """Schema for a standalone list of models."""

    root: list[ModelType]


class ToolList(RootModel[list[ToolType]]):
    """Schema for a standalone list of tools."""

    root: list[ToolType]


class TypeList(RootModel[list[TypeDefinition]]):
    """Schema for a standalone list of type definitions."""

    root: list[TypeDefinition]


class VariableList(RootModel[list[Variable]]):
    """Schema for a standalone list of variables."""

    root: list[Variable]


class Document(
    RootModel[
        Union[
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
    ]
):
    """Schema for any valid QType document structure.

    This allows validation of standalone lists of components, individual components,
    or full QType application specs. Supports modular composition and reuse.
    """

    root: Union[
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
