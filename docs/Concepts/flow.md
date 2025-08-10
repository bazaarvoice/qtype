# Flow

A flow defines a sequence of [Steps](Steps/index.md) that work together to accomplish a specific task or workflow. Flows are the primary orchestration mechanism in QType, allowing you to chain multiple operations such as LLM inference, tool calls, data processing, and conditional logic into coherent, reusable workflows.

Flows themselves are steps, meaning they can be nested within other flows to create complex, hierarchical workflows. This composability allows you to build modular applications where common patterns can be extracted into reusable flow components.

## Rules and Behaviors

- **Unique IDs**: Each flow must have a unique `id` within the application. Duplicate flow IDs will result in a validation error.
- **Required Steps**: Flows must contain at least one step. Empty flows will result in a `FlowHasNoStepsError` validation error.
- **Input Inference**: If `inputs` are not explicitly defined, they are automatically inferred from the inputs of the first step in the flow.
- **Output Inference**: If `outputs` are not explicitly defined, they are automatically inferred from the outputs of the last step in the flow.
- **Step References**: Steps can be referenced by ID (string) or embedded as inline objects within the flow definition.
- **Sequential Execution**: Steps within a flow are executed in the order they appear in the `steps` list.

--8<-- "components/Flow.md"

## Related Concepts

Flows orchestrate [Step](Steps/index.md) components to create workflows. Any step type can be included in a flow, including other flows for nested workflows.

# Flow Modes

## Complete Flows

The default mode for a flow is 'Complete'. These are stateless executions -- think of them like data pipelines. They will accept input values and produce output values.


### Intepreter Behavior

The interpreter hosts each complete flow as an endpoint where you can post the input values and it returns the output values of your declared output variables.

## Chat Flows

Chat flows are a more restrictive, but defining one enables unique behavior in the interpreter.

### Restrictions:
* Chat flows must have at least one input variable of type `ChatMessage`.
* Chat flows may only have one output variable and it must be of type `ChatMessage`.

`qtype validate` will check for these conditions.

### Intepreter Behavior
The interpreter hosts each chat flow as an endpoint that ends in `/chat`.

The endpoint supports Vercel's [ai-sdk](https://ai-sdk.dev/).

The UI will detect the chat flows, and surface a conversation experience.

Chat flows can be _stateful_ or _stateless_. If the llm inference step in the chat flow has [Memory](memory.md), then it is stateful. Otherwise, it is stateless. In both casses the UI sends the entire conversation to the api with each new message, but the stateful behavior will truncate it based on the memory settings.