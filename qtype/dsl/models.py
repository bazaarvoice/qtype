
from enum import Enum
from typing import List, Optional, Dict, Union
from pydantic import BaseModel, Field


# Shared Enums and Types
class InputType(str, Enum):
    text = "text"
    number = "number"
    file = "file"
    image = "image"
    date = "date"
    time = "time"
    datetime = "datetime"
    multiselect = "multiselect"


class ModelProvider(str, Enum):
    openai = "openai"
    anthropic = "anthropic"
    huggingface = "huggingface"
    azure = "azure"
    google = "google"
    other = "other"


class RetrieverType(str, Enum):
    elastic = "elastic"
    vector = "vector"


class FlowMode(str, Enum):
    chat = "chat"
    complete = "complete"
    api = "api"


class ConditionalOperator(str, Enum):
    equals = "equals"
    not_equals = "not_equals"
    in_ = "in"
    not_in = "not_in"
    exists = "exists"
    not_exists = "not_exists"


# Core DSL Models
class Model(BaseModel):
    id: str
    provider: ModelProvider
    name: str
    inference_params: Optional[Dict[str, Union[str, int, float]]] = None


class Input(BaseModel):
    id: str
    type: InputType
    required: bool = False
    display_type: Optional[str] = None


class Prompt(BaseModel):
    id: str
    file: str
    input_vars: List[str]
    output_vars: Optional[List[str]] = None


class Index(BaseModel):
    id: str
    type: str
    embedding_model: str


class Retriever(BaseModel):
    id: str
    type: RetrieverType
    source: str


class Tool(BaseModel):
    id: str
    name: str
    description: str
    input_schema: Dict[str, str]
    output_schema: Dict[str, str]


class ToolProvider(BaseModel):
    id: str
    auth: Optional[Dict[str, str]] = None
    openapi_spec: Optional[str] = None
    include_tags: Optional[List[str]] = None
    exclude_paths: Optional[List[str]] = None
    tools: List[Tool]


class Feedback(BaseModel):
    id: str
    type: str
    inputs: Optional[List[Input]] = None


class Memory(BaseModel):
    id: str
    type: str
    store: Optional[str] = None


class Condition(BaseModel):
    if_var: str
    operator: ConditionalOperator
    value: Union[str, int, float, bool]
    then: str
    else_: Optional[str] = Field(None, alias="else")


class Step(BaseModel):
    id: str
    prompt: Optional[str] = None
    retriever: Optional[str] = None
    tool: Optional[str] = None
    input_map: Optional[Dict[str, str]] = None
    output_map: Optional[Dict[str, str]] = None
    condition: Optional[Condition] = None


class Flow(BaseModel):
    id: str
    steps: List[Step]
    inputs: Optional[List[str]] = None
    mode: FlowMode = FlowMode.chat


class AuthProvider(BaseModel):
    id: str
    type: str
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    scopes: Optional[List[str]] = None
    token_url: Optional[str] = None


class QTypeSpec(BaseModel):
    version: str
    models: Optional[List[Model]] = None
    inputs: Optional[List[Input]] = None
    prompts: Optional[List[Prompt]] = None
    retrievers: Optional[List[Retriever]] = None
    indexes: Optional[List[Index]] = None
    tools: Optional[List[ToolProvider]] = None
    flows: Optional[List[Flow]] = None
    feedback: Optional[List[Feedback]] = None
    memory: Optional[List[Memory]] = None
    auth: Optional[List[AuthProvider]] = None
