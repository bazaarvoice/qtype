# Flow

A flow defines a sequence of [Steps](Steps/index.md) that work together to accomplish a specific task or workflow. Flows are the primary orchestration mechanism in QType, allowing you to chain multiple operations such as LLM inference, tool calls, and data processing into coherent, reusable workflows.

Flows can be invoked from other flows using the [InvokeFlow](../components/InvokeFlow.md) step, enabling composability where common patterns can be extracted into reusable flow components.

## Key Principles

### Explicit Variable Declarations

All variables used within a flow **must be declared** in the `variables` section of the flow. This creates a clear "data contract" for the flow, making it easier to understand what data flows through each step.

```yaml
flows:
  - type: Flow
    id: my_flow
    variables:
      - id: user_query
        type: text
      - id: response
        type: text
    # ... steps reference these variables
```

### Reference by ID

Steps reference variables by their ID (as strings). The variable must be declared in the flow's `variables` section.

```yaml
steps:
  - id: my_step
    type: LLMInference
    inputs:
      - user_query  # References the variable declared above
    outputs:
      - response
```

## Rules and Behaviors

- **Unique IDs**: Each flow must have a unique `id` within the application. Duplicate flow IDs will result in a validation error.
- **Required Steps**: Flows must contain at least one step. Empty flows will result in a validation error.
- **Required Variables**: All variables used in step inputs/outputs must be declared in the flow's `variables` section.
- **Input Specification**: The `inputs` field lists which variables serve as the flow's inputs (by referencing their IDs).
- **Output Specification**: The `outputs` field lists which variables serve as the flow's outputs (by referencing their IDs).
- **Step References**: Steps can be referenced by ID (string) or embedded as inline objects within the flow definition.
- **Sequential Execution**: Steps within a flow are executed in the order they appear in the `steps` list.

--8<-- "components/Flow.md"

## Flow Interface

Flows define their interaction pattern using the `interface` field, which specifies how the flow should be hosted and what kind of user experience it provides.

### Complete Flows

Complete flows (`type: Complete`) are stateless executions that accept input values and produce output values. Think of them like data pipelines or functions.

```yaml
flows:
  - type: Flow
    id: my_flow
    interface:
      type: Complete
    variables:
      - id: input_data
        type: text
      - id: output_data
        type: text
    inputs:
      - input_data
    outputs:
      - output_data
```

**Interpreter Behavior**: The interpreter hosts each complete flow as an HTTP endpoint where you can POST the input values and receive the output values.

### Conversational Flows

Conversational flows (`type: Conversational`) enable interactive, multi-turn conversations. They have specific requirements:

**Requirements:**
* Must have at least one input variable of type `ChatMessage`
* Must have exactly one output variable of type `ChatMessage`

**Session Management**: The `interface.session_inputs` field allows you to specify which variables should persist across conversation turns:

```yaml
flows:
  - type: Flow
    id: doc_chat_flow
    interface:
      type: Conversational
      session_inputs:
        - document_content  # This variable persists across turns
    variables:
      - id: document_content
        type: text
      - id: user_message
        type: ChatMessage
      - id: ai_response
        type: ChatMessage
```

**Interpreter Behavior**: 
- The interpreter hosts conversational flows as endpoints ending in `/chat`
- Supports Vercel's [ai-sdk](https://ai-sdk.dev/)
- The UI automatically detects conversational flows and provides a chat interface
- Conversational flows can be stateful or stateless depending on whether LLM inference steps use [Memory](memory.md)