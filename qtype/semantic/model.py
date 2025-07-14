"""
Semantic Intermediate Representation models.

This module contains the semantic models that represent a resolved QType
specification where all ID references have been replaced with actual object
references.

Generated automatically with command:
qtype generate semantic-model
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# Import enums and type aliases from DSL
from qtype.dsl.model import VariableTypeEnum, DecoderFormat

class SemanticApplication(BaseModel):
    """Defines a QType application that can include models, variables, and other components."""

    id: str = Field(..., description="Unique ID of the application.")
    description: str | None = Field(None, description="Optional description of the application.")
    memories: list[SemanticMemory] = Field([], description="List of memory definitions used in this application.")
    models: list[SemanticEmbeddingModel | SemanticModel] = Field([], description="List of models used in this application.")
    variables: list[SemanticVariable] = Field([], description="List of variables used in this application.")
    flows: list[SemanticFlow] = Field([], description="List of flows defined in this application.")
    auths: list[SemanticAuthorizationProvider] = Field([], description="List of authorization providers used for API access.")
    tools: list[SemanticAPITool | SemanticPythonFunctionTool] = Field([], description="List of tools available in this application.")
    indexes: list[SemanticDocumentIndex | SemanticVectorIndex] = Field([], description="List of indexes available for search operations.")
    telemetry: SemanticTelemetrySink | None = Field(None, description="Optional telemetry sink for observability.")

class SemanticAuthorizationProvider(BaseModel):
    """Defines how tools or providers authenticate with APIs, such as OAuth2 or API keys."""

    id: str = Field(..., description="Unique ID of the authorization configuration.")
    api_key: str | None = Field(None, description="API key if using token-based auth.")
    client_id: str | None = Field(None, description="OAuth2 client ID.")
    client_secret: str | None = Field(None, description="OAuth2 client secret.")
    host: str | None = Field(None, description="Base URL or domain of the provider.")
    scopes: list[str] = Field([], description="OAuth2 scopes required.")
    token_url: str | None = Field(None, description="Token endpoint URL.")
    type: str = Field(..., description="Authorization method, e.g., 'oauth2' or 'api_key'.")

class SemanticStep(BaseModel):
    """Base class for components that take inputs and produce outputs."""

    id: str = Field(..., description="Unique ID of this component.")
    inputs: list[SemanticVariable] = Field([], description="Input variables required by this step.")
    outputs: list[SemanticVariable] = Field([], description="Variable where output is stored.")

class SemanticIndex(BaseModel):
    """Base class for searchable indexes that can be queried by search steps."""

    id: str = Field(..., description="Unique ID of the index.")
    args: dict[str, Any] = Field({}, description="Index-specific configuration and connection parameters.")
    auth: SemanticAuthorizationProvider | None = Field(None, description="AuthorizationProvider for accessing the index.")
    name: str = Field(..., description="Name of the index/collection/table.")

class SemanticModel(BaseModel):
    """Describes a generative model configuration, including provider and model ID."""

    id: str = Field(..., description="Unique ID for the model.")
    auth: SemanticAuthorizationProvider | None = Field(None, description="AuthorizationProvider used for model access.")
    inference_params: dict[str, Any] = Field({}, description="Optional inference parameters like temperature or max_tokens.")
    model_id: str | None = Field(None, description="The specific model name or ID for the provider. If None, id is used")
    provider: str = Field(..., description="Name of the provider, e.g., openai or anthropic.")

class SemanticMemory(BaseModel):
    """Session or persistent memory used to store relevant conversation or state data across steps or turns."""

    id: str = Field(..., description="Unique ID of the memory block.")

class SemanticTelemetrySink(BaseModel):
    """Defines an observability endpoint for collecting telemetry data from the QType runtime."""

    id: str = Field(..., description="Unique ID of the telemetry sink configuration.")
    auth: SemanticAuthorizationProvider | None = Field(None, description="AuthorizationProvider used to authenticate telemetry data transmission.")
    endpoint: str = Field(..., description="URL endpoint where telemetry data will be sent.")

class SemanticVariable(BaseModel):
    """Schema for a variable that can serve as input, output, or parameter within the DSL."""

    id: str = Field(..., description="Unique ID of the variable. Referenced in prompts or steps.")
    type: VariableTypeEnum | dict | list = Field(..., description="Type of data expected or produced. Can be:\n- A simple type from VariableType enum (e.g., 'text', 'number')\n- A dict defining object structure with property names as keys\n- For arrays: use [type] syntax (e.g., [text] for array of strings)\n- For nested objects: use nested dict structure\n- For tuples: use [type1, type2] syntax")

class SemanticCondition(SemanticStep):
    """Conditional logic gate within a flow. Supports branching logic for execution based on variable values."""

    else_: SemanticAgent | SemanticAPITool | SemanticCondition | SemanticDocumentSearch | SemanticFlow | SemanticLLMInference | SemanticPromptTemplate | SemanticPythonFunctionTool | SemanticVectorSearch | None = Field(None, description="Optional step to run if condition fails.", alias="else")
    equals: SemanticVariable | None = Field(None, description="Match condition for equality check.")
    then: SemanticAgent | SemanticAPITool | SemanticCondition | SemanticDocumentSearch | SemanticFlow | SemanticLLMInference | SemanticPromptTemplate | SemanticPythonFunctionTool | SemanticVectorSearch = Field(..., description="Step to run if condition matches.")

class SemanticDecoder(SemanticStep):
    """Defines a step that decodes string data into structured outputs.

    If parsing fails, the step will raise an error and halt execution.
    Use conditional logic in your flow to handle potential parsing errors.
    """

    format: DecoderFormat = Field("json", description="Format in which the decoder processes data. Defaults to JSON.")

class SemanticFlow(SemanticStep):
    """Defines a flow of steps that can be executed in sequence or parallel.
    Flows can include conditions and memory for state management.
    If input or output variables are not specified, they are inferred from
    the first and last step, respectively.
    """

    steps: list[SemanticAgent | SemanticAPITool | SemanticCondition | SemanticDocumentSearch | SemanticFlow | SemanticLLMInference | SemanticPromptTemplate | SemanticPythonFunctionTool | SemanticVectorSearch] = Field(..., description="List of steps or step IDs.")

class SemanticLLMInference(SemanticStep):
    """Defines a step that performs inference using a language model.
    It can take input variables and produce output variables based on the model's response."""

    memory: SemanticMemory | None = Field(None, description="Memory object to retain context across interactions.")
    model: SemanticEmbeddingModel | SemanticModel = Field(..., description="The model to use for inference.")
    system_message: str | None = Field(None, description="Optional system message to set the context for the model.")

class SemanticPromptTemplate(SemanticStep):
    """Defines a prompt template with a string format and variable bindings.
    This is used to generate prompts dynamically based on input variables."""

    template: str = Field(..., description="String template for the prompt with variable placeholders.")

class SemanticSearch(SemanticStep):
    """Base class for search operations against indexes."""

    filters: dict[str, Any] = Field({}, description="Optional filters to apply during search.")
    index: SemanticDocumentIndex | SemanticVectorIndex = Field(..., description="Index to search against (object or ID reference).")

class SemanticTool(SemanticStep):
    """
    Base class for callable functions or external operations available to the model or as a step in a flow.
    """

    name: str = Field(..., description="Name of the tool function.")
    description: str = Field(..., description="Description of what the tool does.")

class SemanticDocumentIndex(SemanticIndex):
    """Document search index for text-based search (e.g., Elasticsearch, OpenSearch)."""

    pass

class SemanticVectorIndex(SemanticIndex):
    """Vector database index for similarity search using embeddings."""

    embedding_model: SemanticEmbeddingModel = Field(..., description="Embedding model used to vectorize queries and documents.")

class SemanticEmbeddingModel(SemanticModel):
    """Describes an embedding model configuration, extending the base Model class."""

    dimensions: int = Field(..., description="Dimensionality of the embedding vectors produced by this model.")

class SemanticAgent(SemanticLLMInference):
    """Defines an agent that can perform tasks and make decisions based on user input and context."""

    tools: list[SemanticAPITool | SemanticPythonFunctionTool] = Field(..., description="List of tools available to the agent.")

class SemanticDocumentSearch(SemanticSearch):
    """Performs document search against a document index."""

    pass

class SemanticVectorSearch(SemanticSearch):
    """Performs vector similarity search against a vector index."""

    default_top_k: int | None = Field(..., description="Number of top results to retrieve if not provided in the inputs.")

class SemanticAPITool(SemanticTool):
    """Tool that invokes an API endpoint."""

    endpoint: str = Field(..., description="API endpoint URL to call.")
    method: str = Field("GET", description="HTTP method to use (GET, POST, PUT, DELETE, etc.).")
    auth: SemanticAuthorizationProvider | None = Field(None, description="Optional AuthorizationProvider for API authentication.")
    headers: dict[str, str] = Field({}, description="Optional HTTP headers to include in the request.")

class SemanticPythonFunctionTool(SemanticTool):
    """Tool that calls a Python function."""

    function_name: str = Field(..., description="Name of the Python function to call.")
    module_path: str = Field(..., description="Optional module path where the function is defined.")

# Union types for semantic models
SemanticToolType = SemanticAPITool | SemanticPythonFunctionTool

SemanticStepType = (
    SemanticAgent |
    SemanticAPITool |
    SemanticCondition |
    SemanticDecoder |
    SemanticDocumentSearch |
    SemanticFlow |
    SemanticLLMInference |
    SemanticPromptTemplate |
    SemanticPythonFunctionTool |
    SemanticVectorSearch
)

SemanticIndexType = SemanticDocumentIndex | SemanticVectorIndex

SemanticModelType = SemanticEmbeddingModel | SemanticModel
