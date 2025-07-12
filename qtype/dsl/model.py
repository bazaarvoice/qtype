from __future__ import annotations

from abc import ABC
from enum import Enum
from typing import Any, Union

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator
#
# ---------------- Base Components ----------------
#


class StrictBaseModel(BaseModel):
    """Base model with extra fields forbidden."""

    model_config = ConfigDict(extra="forbid")


class VariableTypeEnum(str, Enum):
    """Represents the type of data a user or system input can accept within the DSL."""

    audio = "audio"
    boolean = "boolean"
    bytes = "bytes"
    date = "date"
    datetime = "datetime"
    embedding = "embedding"
    int = "int"
    file = "file"
    float = "float"
    image = "image"
    number = "number"
    text = "text"
    time = "time"
    video = "video"

VariableType = Union[
    VariableTypeEnum,
    dict,
    list
]


class Variable(StrictBaseModel):
    """Schema for a variable that can serve as input, output, or parameter within the DSL."""

    id: str = Field(
        ...,
        description="Unique ID of the variable. Referenced in prompts or steps.",
    )
    type: VariableType = Field(
        ...,
        description=(
            "Type of data expected or produced. Can be:\n"
            + "- A simple type from VariableType enum (e.g., 'text', 'number')\n"
            + "- A dict defining object structure with property names as keys\n"
            + "- For arrays: use [type] syntax (e.g., [text] for array of strings)\n"
            + "- For nested objects: use nested dict structure\n"
            + "- For tuples: use [type1, type2] syntax"
        ),
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
    # TODO: flush this out with options for vector memory, etc.


#
# ---------------- Core Steps and Flow Components ----------------
#


class Step(StrictBaseModel):
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
    outputs: list[Variable | str] | None = Field(
        default=None,
        description="The result of applying this template to the input variables. If not provided, defaults to a single text output variable called <id>.prompt",
    )

    @model_validator(mode="after")
    def set_default_outputs(self) -> "PromptTemplate":
        """Set default output variable if none provided."""
        if self.outputs is None:
            self.outputs = [
                Variable(id=f"{self.id}.prompt", type=VariableTypeEnum.text)
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
        default="GET", description="HTTP method to use (GET, POST, PUT, DELETE, etc.)."
    )
    auth: AuthorizationProvider | str | None = Field(
        default=None,
        description="Optional AuthorizationProvider for API authentication.",
    )
    headers: dict[str, str] | None = Field(
        default=None, description="Optional HTTP headers to include in the request."
    )


class LLMInference(Step):
    """Defines a step that performs inference using a language model.
    It can take input variables and produce output variables based on the model's response."""

    memory: Memory | None = Field(
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
                Variable(id=f"{self.id}.response", type=VariableTypeEnum.text)
            ]
        return self


class Agent(LLMInference):
    """Defines an agent that can perform tasks and make decisions based on user input and context."""

    tools: list[ToolType] = Field(
        ..., description="List of tools available to the agent."
    )


class Flow(Step):
    """Defines a flow of steps that can be executed in sequence or parallel.
    Flows can include conditions and memory for state management.
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

        if self.inputs is None or len(self.inputs) != 1 or \
           (isinstance(self.inputs[0], Variable) and self.inputs[0].type != VariableTypeEnum.text):
            raise ValueError(
                f"Decoder steps must have exactly one input variable of type 'text'. Found: {self.inputs}"
            )
        if self.outputs is None:
            raise ValueError(
                "Decoder steps must have at least one output variable defined."
            )
        return self


#
# ---------------- Observability and Provider Components ----------------
#


class ToolProvider(StrictBaseModel, ABC):
    """Base class for tool providers that can generate tools from various sources."""

    id: str = Field(..., description="Unique ID of the tool provider.")

class OpenAPIToolProvider(ToolProvider):
    """Tool provider that generates tools from OpenAPI specifications."""

    exclude_paths: list[str] | None = Field(
        default=None, description="Exclude specific endpoints by path."
    )
    include_tags: list[str] | None = Field(
        default=None,
        description="Limit tool generation to specific OpenAPI tags.",
    )
    openapi_spec: str | None = Field(
        default=None,
        description="Optional path or URL to an OpenAPI spec to auto-generate tools.",
    )
    auth: AuthorizationProvider | str | None = Field(
        default=None,
        description="AuthorizationProvider ID used to authenticate tool access.",
    )


class PythonModuleToolProvider(ToolProvider):
    """Tool provider that generates tools from Python module functions."""

    module_path: str = Field(
        ...,
        description="Python module path (e.g., 'com.org.my_module.my_tools')"
    )


class AuthorizationProvider(StrictBaseModel):
    """Defines how tools or providers authenticate with APIs, such as OAuth2 or API keys."""

    # TODO: think through this more and decide if it's the right shape...

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
    tool_providers: list[ToolProviderType] | None = Field(
        default=None,
        description="List of tool providers that can auto-generate tools from OpenAPI specs.",
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
                Variable(id="top_k", type=VariableTypeEnum.number),
                Variable(id="query", type=VariableTypeEnum.text),
            ]

        if self.outputs is None:
            self.outputs = [
                Variable(id=f"{self.id}.results", type={"results": ["dict"]})
            ]
        return self


class DocumentSearch(Search):
    """Performs document search against a document index."""

    @model_validator(mode="after")
    def set_default_inputs_outputs(self) -> "DocumentSearch":
        """Set default input and output variables if none provided."""
        if self.inputs is None:
            self.inputs = [Variable(id="query", type=VariableTypeEnum.text)]

        if self.outputs is None:
            self.outputs = [
                # If not specified, use a generic results variable and let the user normalize it later.
                Variable(id=f"{self.id}.results", type={"results": [dict]})
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

# Create a union type for all tool provider types
ToolProviderType = Union[
    OpenAPIToolProvider,
    PythonModuleToolProvider,
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


class ToolProviderList(RootModel[list[ToolProviderType]]):
    """Schema for a standalone list of tool providers."""

    root: list[ToolProviderType]


class ToolList(RootModel[list[ToolType]]):
    """Schema for a standalone list of tools."""

    root: list[ToolType]



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
            ToolProviderList,
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
        ToolProviderList,
        ToolList,
        VariableList,
    ]


#
# ---------------- Shapes we've disabled for now but will need soon ----------------
#

# class FeedbackType(str, Enum):
#     """Enum of supported feedback mechanisms such as thumbs, stars, or text responses."""

#     THUMBS = "thumbs"
#     STAR = "star"
#     TEXT = "text"
#     RATING = "rating"
#     CHOICE = "choice"
#     BOOLEAN = "boolean"


# class Feedback(StrictBaseModel):
#     """Schema to define how user feedback is collected, structured, and optionally used to guide future prompts."""

#     id: str = Field(..., description="Unique ID of the feedback config.")
#     type: FeedbackType = Field(..., description="Feedback mechanism type.")
#     question: str | None = Field(
#         default=None,
#         description="Question to show user for qualitative feedback.",
#     )
#     prompt: str | None = Field(
#         default=None,
#         description="ID of prompt used to generate a follow-up based on feedback.",
#     )
