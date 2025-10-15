# **QType DSL Evolution: A Guide to the New Design**

This document outlines the planned changes to the QType DSL. The goal of this evolution is to create a more robust, expressive, and maintainable language by improving clarity, modularity, and the separation of concerns.

### **1\. Centralized Variable Declaration**

**Change:** Inline variable definitions within a step's inputs or outputs will be removed. All variables must be declared in a variables block, scoped to either the Flow (for local variables) or the Application (for global constants).

**Rationale:** This enforces the "separation of declaration and usage," a core principle of robust language design. It eliminates ambiguity, simplifies parsing, and enables static analysis (e.g., checking if a referenced variable exists). It establishes a clear "data contract" for each component.

**Example:**

**Before (Ambiguous):**

steps:  
  \- id: my\_llm  
    type: LLMInference  
    inputs:  
      \- user\_query \# Is this a reference or a string literal?  
    outputs:  
      \- id: ai\_response \# Inline declaration  
        type: text

**After (Explicit & Clear):**

flows:  
  \- id: my\_flow  
    variables:  
      \- id: user\_query  
        type: text  
      \- id: ai\_response  
        type: text  
    steps:  
      \- id: my\_llm  
        type: LLMInference  
        inputs:  
          \- user\_query \# Unambiguously a reference to the declared variable  
        outputs:  
          \- ai\_response \# Also a reference

### **2\. Two-Tier Variable Scoping**

**Change:** The DSL will support two distinct variable scopes: Application and Flow.

1. **Application Variables:** Defined at the root of the Application. They are global, read-only constants (e.g., a company name, a shared prompt template).  
2. **Flow Variables:** Defined within a Flow. They are local to that flow and represent the ephemeral data passed between steps.

**Rationale:** This provides proper encapsulation, making flows self-contained and reusable like functions. Application variables provide a clean mechanism for shared, immutable configuration without polluting the local scope of flows or relying on text-substitution tricks like YAML anchors.

**Example:**

id: my\_app  
\# Application-level variables are global constants  
variables:  
  \- id: company\_name  
    type: text  
    value: "Starlight Innovations"

flows:  
  \- id: my\_flow  
    \# Flow-level variables are for local data passing  
    variables:  
      \- id: welcome\_message  
        type: text  
    steps:  
      \- id: create\_welcome  
        type: PromptTemplate  
        \# This step can cleanly reference the global constant  
        template: "Welcome to {company\_name}\!"  
        outputs:  
          \- welcome\_message

### **2\. Always use descriminators**

**Change** All uniuon types in `model.py` now require a descriminator in the schema for ease of readability by humans.
e.g.:
```

models:
  - type: EmbeddingModel
    id: test_embedding_model
```

### **4\. Centralized Memory Configuration**

**Change:** The Memory object definition will be moved from an inline property on steps (like LLMInference) to a top-level memories list on the Application model. Steps will reference a memory configuration by its string ID.

**Rationale:** This follows the DRY (Don't Repeat Yourself) principle. It allows a single, consistent memory configuration to be defined once and shared across multiple steps and flows. This aligns Memory with other first-class, reusable components like models and tools, making the language more consistent.

**Example:**

**Before (Repetitive):**

steps:  
  \- id: step\_one  
    type: Agent  
    memory:  
      id: chat\_mem  
      token\_limit: 4000

**After (Reusable & Centralized):**

id: my\_app  
memories:  
  \- id: main\_chat\_mem  
    token\_limit: 4000

flows:  
  \- id: my\_flow  
    steps:  
      \- id: step\_one  
        type: Agent  
        memory: main\_chat\_mem \# Reference by ID

### **5\. Explicit Flow.interface for UI & Session Logic**

**Change:** The imperative Flow.mode field will be removed. It will be replaced by a declarative Flow.interface object, which contains type: "Conversational" | "Complete" and session\_inputs: list\[str\].

**Rationale:** This decouples a flow's core logic from its interaction pattern. The interface acts as a contract for external systems (like a UI or a SessionManager), telling them how to host the flow and what state to persist across runs. This is a more flexible and powerful model that enables complex, multi-input conversational applications (e.g., "upload a doc, then chat about it").

**Example:**

flows:  
  \- id: doc\_chat\_flow  
    interface:  
      type: Conversational  
      \# Tells the SessionManager to persist 'doc\_content' between runs  
      session\_inputs:  
        \- doc\_content  
    variables:  
      \- id: uploaded\_file  
        type: text  
      \- id: doc\_content  
        type: text  
      \- id: user\_question  
        type: ChatMessage  
    \# ... steps to process the file and then chat ...

### **6\. Composable Flows with InvokeFlow**

**Change:** Flow will no longer inherit from Step. A new InvokeFlow step will be introduced, allowing one flow to call another with explicit input\_bindings and output\_bindings.

**Rationale:** This establishes a proper function-call mechanism for flows, turning them into truly reusable and composable building blocks. It promotes the creation of smaller, single-responsibility flows that can be combined to build large, maintainable applications, while ensuring each flow's scope is properly encapsulated.

**Example:**

flows:  
  \- id: main\_flow  
    variables:  
      \- id: my\_text  
        type: text  
      \- id: my\_summary  
        type: text  
    steps:  
      \- id: call\_summarizer  
        type: InvokeFlow  
        flow: reusable\_summarize\_flow \# ID of the flow to call  
        input\_bindings:  
          \# Map callee's input 'text\_to\_summarize' to our 'my\_text'  
          text\_to\_summarize: my\_text  
        output\_bindings:  
          \# Map callee's output 'summary' to our 'my\_summary'  
          summary: my\_summary  


### **7\. Use References for Everything**

The `Reference` Type Approach (Explicit and Robust)

Now, let's introduce a dedicated type. This type acts as a **marker** for your resolver.

#### 1\. Define the `Reference` Type

First, you define a generic `Reference` type. Using a standard like `$ref` for the field name (via a Pydantic alias) is good practice.

**File:** `qtype/dsl/base_types.py` (or a new `references.py`)

```python
from pydantic import BaseModel, Field
from typing import Generic, TypeVar

T = TypeVar("T")

class Reference(BaseModel, Generic[T]):
    """Represents a reference to another component by its ID."""
    ref: str = Field(..., alias="$ref")
```

#### 2\. Update Your Pydantic Models

Now, your models declare their dependencies explicitly.

**File:** `qtype/dsl/model.py`

```python
from .base_types import Reference
from typing import Union

# In your old model you had:
# model: Union[Model, str]

# In the new model, it becomes:
class LLMInference(Step):
    # ...
    # This field IS the resolved model object.
    model: Model 
    # The Union type is now handled by Pydantic during initial loading.

# During initial parsing from YAML, Pydantic will see either the string ID or the Ref object.
# To handle this, you can define a type alias for the loader.
ReferenceableModel = Union[Reference["Model"], str] 

# Then, in your DSL model (before resolution):
class PreResolutionLLMInference(Step):
    #...
    model: ReferenceableModel
```

Even simpler, you can use a validator to automatically convert a plain string into a `Reference` object during parsing.

#### 3\. The Resolver Becomes Simple and Generic

Your semantic resolver no longer needs to know the specific structure of every step. Its job is simply to find all instances of `Reference` and replace them.

**Conceptual Resolver Logic (The Easy Way):**

```python
def resolve_all_references(model: BaseModel, app_context: Application):
    """Walks a Pydantic model tree and resolves all Reference objects."""
    for field_name, field_value in model.__iter__():
        if isinstance(field_value, Reference):
            # We found a reference! Let's resolve it.
            resolved_obj = find_component_by_id(app_context, field_value.ref)
            setattr(model, field_name, resolved_obj)
        
        elif isinstance(field_value, BaseModel):
            # Recurse into nested models
            resolve_all_references(field_value, app_context)
            
        elif isinstance(field_value, list):
            # Recurse into lists
            for item in field_value:
                if isinstance(item, BaseModel):
                    resolve_all_references(item, app_context)

# You would call this on your top-level Application model after loading.
```

This resolver is **generic**. It doesn't care if it's resolving a `Model`, an `AuthProvider`, or a `Tool`. It just finds the `Reference` marker and does its job. If you add a new referenceable component tomorrow, you don't have to change the resolver at all.





#### **How to Implement This "Magic" with Pydantic**

This is where the power of Pydantic's validation system comes in. You can define your models to accept either the simple string *or* the full object, and then use a validator to normalize the input into the `Reference` object your generic resolver expects.

Here’s the complete Python code to make this happen:

**. The Pydantic Model with a Normalizing Validator:**

You define the field to accept `Union[Reference, str]`, and then use a `model_validator` in `before` mode to transform the simple string into the full `Reference` object before any other validation runs.

```python
from pydantic import model_validator, BaseModel
from typing import Any, Union

class Model(BaseModel):
    id: str
    provider: str
    # This field can accept a string or a Reference object from the YAML
    auth: Union[Reference["AuthProvider"], str] # Use a forward reference for AuthProvider

    @model_validator(mode='before')
    @classmethod
    def normalize_string_references(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Check if the 'auth' field is a simple string
            if 'auth' in data and isinstance(data['auth'], str):
                # If it is, transform it into the explicit $ref object
                data['auth'] = {'$ref': data['auth']}
        return data

# Do the same for LLMInference
class LLMInference(Step):
    # ...
    model: Union[Reference[Model], str]

    @model_validator(mode='before')
    @classmethod
    def normalize_string_references(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if 'model' in data and isinstance(data['model'], str):
                data['model'] = {'$ref': data['model']}
        return data

```

#### **The Result: The Perfect System**

This design is the best of all worlds:

1.  **Great User Experience:** The YAML is incredibly clean and intuitive for the 99% case.
2.  **Robust Backend:** Your parser automatically transforms the clean shorthand into the structured `Reference` object.
3.  **Generic Resolver:** Your generic, tree-walking resolver remains simple and powerful because, by the time it runs, it **only ever sees `Reference` objects**. It doesn't need to handle the `Union[Reference, str]` complexity at all.

You've successfully created a powerful abstraction. The user gets a simple, beautiful language, and you get a robust, maintainable, and standards-compliant internal representation. This is the hallmark of excellent language design.


### **8\. Remove Conditional Branching**

It doesn't work well right now and causes complexity we should sort out later





### **Future: Path Expressions for Accessing Complex Types**

**Change:** Variable references in a step's inputs can now use dot-notation to access nested properties of complex types (like ChatMessage or RAGDocument).

**Rationale:** This makes the rich domain types in the language truly useful. It provides a seamless, intuitive way to "look inside" a structured variable to get a specific piece of data, without needing to "flatten" the types or write a custom tool for simple data extraction. This greatly enhances the language's expressiveness.

**Example:**

flows:  
  \- id: my\_flow  
    variables:  
      \- id: user\_msg  
        type: ChatMessage  
      \- id: user\_text  
        type: text  
    steps:  
      \- id: extract\_text \# A hypothetical step to demonstrate the concept  
        type: Assign  
        \# Use dot-notation to access a nested field  
        from: user\_msg.content.content  
        to: user\_text
