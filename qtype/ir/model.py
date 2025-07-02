"""
Semantic Intermediate Representation (IR) models.

This module contains the semantic IR models that represent a resolved QType
specification where all ID references have been replaced with actual object
references.
"""

from abc import ABC
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

# Import enums and simple classes from DSL that don't need IR-specific
# modifications
from qtype.dsl.model import (
    AuthorizationProvider,
    FeedbackType,
    FlowMode,
    MemoryType,
)
from qtype.dsl.model import Variable as DSLVariable

class Variable(DSLVariable):
    """IR Variable that extends DSL Variable with a value field."""

    value: Optional[Any] = Field(None, description="The value of this variable if defined.")

    # A copy constructor from DSLVariable
    def __init__(self, f: DSLVariable):
        super().__init__(id=f.id, type=f.type, display_name=f.display_name)

    def is_set(self) -> bool:
        return self.value is not None


class Prompt(BaseModel):
    """Points to a prompt template used for generation."""

    id: str = Field(..., description="Unique ID for the prompt.")
    path: Optional[str] = Field(
        None, description="File path to the prompt template."
    )
    template: Optional[str] = Field(
        None, description="Inline template string for the prompt."
    )
    inputs: List[Variable] = Field(
        ..., description="List of input objects this prompt expects."
    )
    outputs: Optional[List[Variable]] = Field(
        None,
        description="Optional list of output objects this prompt generates.",
    )


class Model(BaseModel):
    """Represents a generative model configuration."""

    id: str = Field(..., description="Unique ID for the model.")
    provider: str = Field(
        ..., description="Name of the provider, e.g., openai or anthropic."
    )
    model_id: Optional[str] = Field(
        None,
        description=(
            "The specific model name or ID for the provider. "
            "If None, id is used"
        ),
    )
    inference_params: Optional[Dict[str, Any]] = Field(
        ...,
        description="Optional inference parameters like temperature or max_tokens.",
    )


class EmbeddingModel(Model):
    """Describes a model used for embedding text for vector search or memory."""

    dimensions: int = Field(
        ...,
        description="Dimensionality of the embedding vectors produced by this model.",
    )



class Memory(BaseModel):
    """Persistent or session-level memory context for a user or flow."""

    id: str = Field(..., description="Unique ID of the memory block.")
    type: MemoryType = Field(
        ..., description="The type of memory to store context."
    )
    embedding_model: EmbeddingModel = Field(
        ..., description="Embedding model object used for storage."
    )
    persist: bool = Field(
        default=False, description="Whether memory persists across sessions."
    )
    ttl_minutes: Optional[int] = Field(
        None, description="Optional TTL for temporary memory."
    )
    use_for_context: bool = Field(
        default=True,
        description="Whether this memory should be injected as context.",
    )


class ToolProvider(BaseModel):
    """Wraps and authenticates access to a set of tools (often from a single API or OpenAPI spec)."""

    id: str = Field(..., description="Unique ID of the tool provider.")
    name: str = Field(..., description="Name of the tool provider.")
    tools: List["Tool"] = Field(
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
    auth: Optional["AuthorizationProvider"] = Field(
        None,
        description="AuthorizationProvider object used to authenticate tool access.",
    )


class TelemetrySink(BaseModel):
    """Defines an observability endpoint for collecting telemetry data from the QType runtime."""

    id: str = Field(
        ..., description="Unique ID of the telemetry sink configuration."
    )
    endpoint: str = Field(
        ..., description="URL endpoint where telemetry data will be sent."
    )
    auth: Optional[AuthorizationProvider] = Field(
        None,
        description="AuthorizationProvider object used to authenticate telemetry data transmission.",
    )


class Feedback(BaseModel):
    """Describes how and where to collect >feedback on generated responses."""

    id: str = Field(..., description="Unique ID of the feedback config.")
    type: FeedbackType = Field(
        ..., description="Feedback mechanism type (e.g., thumbs, star, text)."
    )
    question: Optional[str] = Field(
        None, description="Question to show user for qualitative feedback."
    )
    prompt: Optional[Prompt] = Field(
        None,
        description="Prompt object used to generate a follow-up based on feedback.",
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
    then: List["Step"] = Field(
        ..., description="List of step objects to run if condition matches."
    )
    else_: Optional[List["Step"]] = Field(
        None,
        alias="else",
        description="Optional list of step objects to run if condition fails.",
    )


class Step(BaseModel, ABC):
    """Abstract base class for execution steps within a flow."""

    id: str = Field(..., description="Unique ID of the step.")
    inputs: Optional[List[Variable]] = Field(
        None, description="Input objects required by this step."
    )
    outputs: Optional[List[Variable]] = Field(
        None, description="Output objects where results are stored."
    )


class VectorDBRetriever(Step):
    """Retriever that queries a vector database using an embedding-based search."""

    id: str = Field(..., description="Unique ID of the retriever.")
    index: str = Field(..., description="ID of the index this retriever uses.")
    embedding_model: EmbeddingModel = Field(
        ..., description="Embedding model object used to vectorize the query."
    )
    top_k: int = Field(5, description="Number of top documents to retrieve.")
    args: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Optional additional arguments for the vector search, "
            "e.g., filtering or scoring parameters."
        )
    )

class Tool(Step):
    """Callable function or external operation available to the model."""

    name: str = Field(..., description="Name of the tool function.")
    description: str = Field(
        ..., description="Description of what the tool does."
    )

class Agent(Step):
    """An AI agent with a specific model, prompt, and tools for autonomous task execution."""

    model: Model = Field(..., description="The model object for this agent to use.")
    prompt: Prompt = Field(..., description="The prompt object for this agent to use.")
    tools: Optional[List[Tool]] = Field(
        default=None,
        description="Tool objects that this agent has access to.",
    )


class Flow(Step):
    """A flow represents the full composition of steps a user or system interacts with."""

    mode: FlowMode = Field(..., description="Interaction mode for the flow.")
    steps: List[Union[Step, "Flow"]] = Field(
        ..., description="List of step objects or nested flow objects."
    )
    conditions: Optional[List[Condition]] = Field(
        None, description="Optional conditional logic within the flow."
    )
    memory: Optional[List[Memory]] = Field(
        None, description="List of memory objects to include (chat mode only)."
    )


class QTypeSpec(BaseModel):
    """
    The top-level definition of a resolved QType specification.

    This class represents the full configuration of a generative AI application,
    including models, inputs, prompts, tools, flows, and supporting infrastructure,
    with all ID references resolved to actual object references.

    Only one `QTypeSpec` should exist per resolved specification.
    """

    version: str = Field(
        ...,
        description="Version of the QType specification schema used.",
    )
    models: Optional[List[Model]] = Field(
        None,
        description="List of generative model objects available for use, including their providers and inference parameters.",
    )
    variables: Optional[List[Variable]] = Field(
        None,
        description="Variables used around this thing",
    )
    prompts: Optional[List[Prompt]] = Field(
        None,
        description="Prompt template objects used in generation steps or tools, with resolved input and output references.",
    )
    tools_provider: Optional[List[ToolProvider]] = Field(
        None,
        description="Tool provider objects with optional OpenAPI specs, exposing callable tools for the model.",
    )
    flows: Optional[List[Flow]] = Field(
        None,
        description="Entry point flow objects to application logic. Each flow defines an executable composition of steps.",
    )
    agents: Optional[List[Agent]] = Field(
        None,
        description="AI agent objects with specific models, prompts, and tools for autonomous task execution.",
    )
    feedback: Optional[List[Feedback]] = Field(
        None,
        description="Feedback configuration objects for collecting structured or unstructured user reactions to outputs.",
    )
    memory: Optional[List[Memory]] = Field(
        None,
        description="Session-level memory context objects, only used in chat-mode flows to persist state across turns.",
    )
    auth: Optional[List[AuthorizationProvider]] = Field(
        None,
        description="Authorization provider objects and credentials used to access external APIs or cloud services.",
    )
    telemetry: Optional[List[TelemetrySink]] = Field(
        None,
        description="Telemetry sink objects for collecting observability data from the QType runtime.",
    )
