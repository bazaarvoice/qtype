from __future__ import annotations

from enum import Enum
from typing import Any, Union

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator

#
# ---------------- Base Components ----------------
#


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
    type: VariableType | dict | list = Field(
        ..., description="Type of data expected or produced."
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
    auth: AuthorizationProvider | str | None = Field(
        default=None,
        description="AuthorizationProvider ID used to authenticate model access.",
    )


class EmbeddingModel(Model):
    """Describes an embedding model configuration, extending the base Model class."""

    dimensions: int | None = Field(
        default=None,
        description="Dimensionality of the embedding vectors produced by this model if an embedding model.",
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
        default=None, description="Variable IDs where output is stored."
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
                Variable(id=f"{self.id}.prompt", type=VariableType.text)
            ]
        return self


class Condition(Step):
    """Conditional logic gate within a flow. Supports branching logic for execution based on variable values."""

    # TODO: Add support for more complex conditions
    equals: Variable | str | None = Field(
        default=None, description="Match condition for equality check."
    )
    then: Step | str = Field(
        ..., description="Step to run if condition matches."
    )
    else_: Step | str | None = Field(
        default=None,
        alias="else",
        description="Optional step to run if condition fails.",
    )

    @model_validator(mode="after")
    def set_default_outputs(self) -> "Condition":
        """Set default output variable if none provided."""
        if not self.inputs or len(self.inputs) != 1:
            raise ValueError(
                "Condition steps must have exactly one input variable."
            )
        return self


class Tool(Step):
    """
    Callable function or external operation available to the model or as a step in a flow.
    """

    id: str = Field(..., description="Unique ID of the tool.")
    name: str = Field(..., description="Name of the tool function.")
    description: str = Field(
        ..., description="Description of what the tool does."
    )


class LLMInference(Step):
    """Defines a step that performs inference using a language model.
    It can take input variables and produce output variables based on the model's response."""

    model: Model = Field(..., description="The model to use for inference.")
    memory: Memory | None = Field(
        default=None,
        description="Memory object to retain context across interactions.",
    )
    system_message: str | None = Field(
        default=None,
        description="Optional system message to set the context for the model.",
    )
    outputs: list[Variable | str] | None = Field(
        default=None,
        description="Output variables produced by the inference. If not provided, defaults to <id>.response variable.",
    )

    @model_validator(mode="after")
    def set_default_outputs(self) -> "LLMInference":
        """Set default output variable if none provided."""
        if self.outputs is None:
            self.outputs = [
                Variable(id=f"{self.id}.response", type=VariableType.text)
            ]
        return self


class Agent(LLMInference):
    """Defines an agent that can perform tasks and make decisions based on user input and context."""

    tools: list[Tool] | None = Field(
        default=None, description="List of tools available to the agent."
    )


class Flow(Step):
    """Defines a flow of steps that can be executed in sequence or parallel.
    Flows can include conditions and memory for state management.
    If input or output variables are not specified, they are inferred from
    the first and last step, respectively.
    """

    steps: list[Step | str] = Field(
        default_factory=list, description="List of steps or step IDs."
    )

#
# ---------------- Observability and Provider Components ----------------
#


class ToolProvider(StrictBaseModel):
    """Logical grouping of tools, often backed by an API or 
    OpenAPI spec, and optionally authenticated."""

    id: str = Field(..., description="Unique ID of the tool provider.")
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
    auth: AuthorizationProvider | str | None = Field(
        default=None,
        description="AuthorizationProvider ID used to authenticate tool access.",
    )


class AuthorizationProvider(StrictBaseModel):
    """Defines how tools or providers authenticate with APIs, such as OAuth2 or API keys."""
    # TODO: think through this more and decide if it's the right shape...

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
    auth: AuthorizationProvider | str | None = Field(
        default=None,
        description="AuthorizationProvider used to authenticate telemetry data transmission.",
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
        description="List of memory definitions used in this application."
    )
    models: list[Model | EmbeddingModel] | None = Field(
        default=None, description="List of models used in this application."
    )
    variables: list[Variable] | None = Field(
        default=None, description="List of variables used in this application."
    )

    # Step components (can be referenced by ID in flows)
    agents: list[Agent] | None = Field(
        default=None,
        description="List of agents defined in this application."
    )
    conditions: list[Condition] | None = Field(
        default=None,
        description="List of reusable condition steps."
    )
    prompt_templates: list[PromptTemplate] | None = Field(
        default=None,
        description="List of reusable prompt templates."
    )
    steps: list[Step] | None = Field(
        default=None,
        description="List of individual steps that can be referenced by flows."
    )

    # Orchestration
    flows: list[Flow] | None = Field(
        default=None, description="List of flows defined in this application."
    )

    # External integrations
    auths: list[AuthorizationProvider] | None = Field(
        default=None,
        description="List of authorization providers used for API access."
    )
    tool_providers: list[ToolProvider] | None = Field(
        default=None,
        description="List of tool providers that can auto-generate tools from OpenAPI specs."
    )
    tools: list[Tool] | None = Field(
        default=None, description="List of tools available in this application."
    )

    # Observability
    telemetry: TelemetrySink | None = Field(
        default=None,
        description="Optional telemetry sink for observability."
    )

    # Extensibility
    references: list[Document] | None = Field(
        default=None,
        description="List of other q-type documents you may use. This allows modular composition and reuse of components across applications.",
    )


#
# ---------------- Document Flexibility Shapes ----------------
# The following shapes let users define a set of flexible document structures
#


class ModelList(RootModel[list[Model | EmbeddingModel]]):
    """Schema for a standalone list of models."""

    root: list[Model | EmbeddingModel]


class VariableList(RootModel[list[Variable]]):
    """Schema for a standalone list of variables."""

    root: list[Variable]


class AuthorizationProviderList(RootModel[list[AuthorizationProvider]]):
    """Schema for a standalone list of authorization providers."""

    root: list[AuthorizationProvider]


class ToolProviderList(RootModel[list[ToolProvider]]):
    """Schema for a standalone list of tool providers."""

    root: list[ToolProvider]


class Document(
    RootModel[
        Union[
            Application,
            Agent,
            Flow,
            ModelList,
            VariableList,
            AuthorizationProviderList,
            ToolProviderList,
        ]
    ]
):
    """Schema for any valid QType document structure.

    This allows validation of standalone lists of components, individual components,
    or full QType application specs. Supports modular composition and reuse.
    """

    root: Union[
        Application,
        Agent,
        Flow,
        ModelList,
        VariableList,
        AuthorizationProviderList,
        ToolProviderList,
    ]


#
# ---------------- Shapes we've disabled for now but will need soon ----------------
#



# class VectorDBRetriever(StrictBaseModel):
#     """Retriever that fetches top-K documents using a vector database and embedding-based similarity search."""

#     type: Literal["vector_retrieve"] = "vector_retrieve"
#     id: str = Field(..., description="Unique ID of the retriever.")
#     index: str = Field(..., description="ID of the index this retriever uses.")
#     embedding_model: str = Field(
#         ...,
#         description="ID of the embedding model used to vectorize the query.",
#     )
#     top_k: int = Field(5, description="Number of top documents to retrieve.")
#     args: dict[str, Any] | None = Field(
#         default=None,
#         description="Arbitrary arguments as JSON/YAML for custom retriever configuration.",
#     )
#     inputs: list[str] | None = Field(
#         default=None,
#         description="Input variable IDs required by this retriever.",
#     )
#     outputs: list[str] | None = Field(
#         default=None,
#         description="Optional list of output variable IDs this prompt generates.",
#     )


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
